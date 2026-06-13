import os
import re
import sys
import tempfile

import yt_dlp

# Default YouTube player clients used for extraction.
#
# YouTube aggressively bot-gates its default "web" client, which makes public
# videos fail with misleading "Private video" / "Sign in to confirm you're not
# a bot" errors. Preferring the clients below avoids that gate without needing
# cookies. Override with the YOUTUBE_PLAYER_CLIENTS env var (comma-separated),
# or set it to "default" to fall back to yt-dlp's built-in selection.
DEFAULT_PLAYER_CLIENTS = "tv,web_safari,mweb,android_vr"

# Matches the common YouTube URL shapes and captures the 11-character video id.
_YOUTUBE_URL_RE = re.compile(r"""(?x)
    ^(?:https?://)?
    (?:www\.|m\.)?
    (?:
        youtu\.be/(?P<short>[A-Za-z0-9_-]{11})
      | youtube\.com/
        (?:
            watch\?(?:\S*&)?v=(?P<v>[A-Za-z0-9_-]{11})
          | (?:embed|shorts|live|v)/(?P<path>[A-Za-z0-9_-]{11})
        )
    )
    """)


def extract_video_id(url):
    """Return the 11-character video id for a YouTube URL, or None if invalid."""
    if not url:
        return None
    match = _YOUTUBE_URL_RE.match(url.strip())
    if not match:
        return None
    return match.group("short") or match.group("v") or match.group("path")


class YouTubeDownloader:
    def __init__(self, temp_dir=None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.cookies_from_browser = os.getenv("COOKIES_FROM_BROWSER")
        self.cookies_file = os.getenv("COOKIES_FILE")
        self.player_clients = os.getenv(
            "YOUTUBE_PLAYER_CLIENTS", DEFAULT_PLAYER_CLIENTS
        )
        self.audio_quality = os.getenv("AUDIO_QUALITY", "192")
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

    def _base_opts(self, **overrides):
        """Build common yt-dlp options (cookies, player clients) plus overrides."""
        opts = {
            "quiet": not self.debug_mode,
            "no_warnings": not self.debug_mode,
        }

        # Prefer player clients that aren't bot-gated, unless explicitly disabled.
        if self.player_clients and self.player_clients.lower() != "default":
            clients = [c.strip() for c in self.player_clients.split(",") if c.strip()]
            if clients:
                opts["extractor_args"] = {"youtube": {"player_client": clients}}

        # Add cookie support (browser extraction takes precedence over a file).
        if self.cookies_from_browser:
            opts["cookiesfrombrowser"] = (self.cookies_from_browser, None, None, None)
        elif self.cookies_file:
            opts["cookiefile"] = self.cookies_file

        opts.update(overrides)
        return opts

    def _extract(self, url, download=False, opts=None):
        """Extract info, translating YouTube's misleading errors into clear ones."""
        opts = opts if opts is not None else self._base_opts()
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=download)
        except yt_dlp.utils.DownloadError as error:
            message = str(error).lower()
            bot_gated = (
                "sign in to confirm" in message
                or "private video" in message
                or "this video is private" in message
            )
            if bot_gated and not (self.cookies_from_browser or self.cookies_file):
                raise RuntimeError(
                    "YouTube refused the request and reported the video as private "
                    "or bot-protected. Public videos can trigger this when no "
                    "authentication is present. Try setting COOKIES_FROM_BROWSER or "
                    "COOKIES_FILE (see COOKIES_SETUP.md), and make sure yt-dlp is up "
                    "to date (pip install -U yt-dlp)."
                ) from error
            raise

    def _progress_hook(self, status):
        """Render a single-line download progress indicator."""
        if self.debug_mode:
            return  # yt-dlp prints its own verbose progress in debug mode.
        if status.get("status") == "downloading":
            percent = (status.get("_percent_str") or "").strip()
            speed = (status.get("_speed_str") or "").strip()
            sys.stdout.write(f"\r  Downloading: {percent} {speed}   ")
            sys.stdout.flush()
        elif status.get("status") == "finished":
            sys.stdout.write("\r  Download complete; converting audio...      \n")
            sys.stdout.flush()

    def download_audio(self, url):
        """Download audio from a YouTube URL.

        Returns a tuple of (audio_file_path, video_info). Files are named by the
        unique video id so concurrent or repeated downloads never collide, and
        the real output path is read back from yt-dlp rather than guessed.
        """
        output_template = os.path.join(self.temp_dir, "%(id)s.%(ext)s")
        ydl_opts = self._base_opts(
            format="bestaudio/best",
            postprocessors=[
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": self.audio_quality,
                }
            ],
            outtmpl=output_template,
            progress_hooks=[self._progress_hook],
        )

        info = self._extract(url, download=True, opts=ydl_opts)

        audio_file = None
        downloads = info.get("requested_downloads")
        if downloads:
            audio_file = downloads[0].get("filepath")
        if not audio_file:
            audio_file = os.path.join(self.temp_dir, f"{info['id']}.mp3")

        return audio_file, self._video_info(info)

    def get_video_info(self, url):
        """Get video metadata without downloading."""
        return self._video_info(self._extract(url, download=False))

    @staticmethod
    def _video_info(info):
        """Normalize a yt-dlp info dict to the fields the app uses."""
        return {
            "id": info.get("id"),
            "title": info.get("title", "Unknown"),
            "duration": info.get("duration", 0) or 0,
            "uploader": info.get("uploader", "Unknown"),
            "upload_date": info.get("upload_date", "Unknown"),
        }
