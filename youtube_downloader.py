import yt_dlp
import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

# Default YouTube player clients used for extraction.
#
# YouTube aggressively bot-gates its default "web" client, which makes public
# videos fail with misleading "Private video" / "Sign in to confirm you're not
# a bot" errors. Preferring the clients below avoids that gate without needing
# cookies. Override with the YOUTUBE_PLAYER_CLIENTS env var (comma-separated),
# or set it to "default" to fall back to yt-dlp's built-in selection.
DEFAULT_PLAYER_CLIENTS = "tv,web_safari,mweb,android_vr"


class YouTubeDownloader:
    def __init__(self, temp_dir=None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.cookies_from_browser = os.getenv("COOKIES_FROM_BROWSER")
        self.cookies_file = os.getenv("COOKIES_FILE")
        self.player_clients = os.getenv(
            "YOUTUBE_PLAYER_CLIENTS", DEFAULT_PLAYER_CLIENTS
        )

    def _base_opts(self, **overrides):
        """Build common yt-dlp options (cookies, player clients) plus overrides."""
        debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

        opts = {
            "quiet": not debug_mode,
            "no_warnings": not debug_mode,
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

    def _extract(self, url, download):
        """Extract info, translating YouTube's misleading errors into clear ones."""
        try:
            with yt_dlp.YoutubeDL(self._base_opts()) as ydl:
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

    def download_audio(self, url):
        """Download audio from YouTube URL and return the path to the audio file."""
        # First extract info to get the title
        info = self._extract(url, download=False)
        title = info.get("title", "video")
        # Clean filename for safety
        safe_title = "".join(
            c for c in title if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()

        # Now download with the sanitized filename
        output_path = os.path.join(self.temp_dir, f"{safe_title}.%(ext)s")
        audio_quality = os.getenv("AUDIO_QUALITY", "192")

        ydl_opts = self._base_opts(
            format="bestaudio/best",
            postprocessors=[
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": audio_quality,
                }
            ],
            outtmpl=output_path,
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_file = os.path.join(self.temp_dir, f"{safe_title}.mp3")

            return audio_file, safe_title, info

    def get_video_info(self, url):
        """Get video metadata without downloading."""
        info = self._extract(url, download=False)
        return {
            "title": info.get("title", "Unknown"),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", "Unknown"),
            "upload_date": info.get("upload_date", "Unknown"),
        }
