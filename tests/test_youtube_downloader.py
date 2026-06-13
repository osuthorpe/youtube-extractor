import yt_dlp
import pytest

from youtube_downloader import (
    YouTubeDownloader,
    DEFAULT_PLAYER_CLIENTS,
    extract_video_id,
)


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "http://youtube.com/watch?v=dQw4w9WgXcQ&t=10s",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "youtu.be/dQw4w9WgXcQ",
    ],
)
def test_extract_video_id_accepts_valid_urls(url):
    assert extract_video_id(url) == "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "url",
    [
        "",
        None,
        "https://www.youtube.com/",
        "https://example.com/watch?v=dQw4w9WgXcQ",
        "not a url",
        "https://youtu.be/short",
    ],
)
def test_extract_video_id_rejects_invalid_urls(url):
    assert extract_video_id(url) is None


def test_download_audio_uses_reported_filepath(monkeypatch, tmp_path):
    downloader = YouTubeDownloader(temp_dir=str(tmp_path))
    expected = str(tmp_path / "abc123.mp3")

    def fake_extract(self, url, download=False, opts=None):
        assert download is True
        return {
            "id": "abc123",
            "title": "Example",
            "duration": 10,
            "uploader": "Chan",
            "requested_downloads": [{"filepath": expected}],
        }

    monkeypatch.setattr(YouTubeDownloader, "_extract", fake_extract)

    audio_file, info = downloader.download_audio("https://youtu.be/abc12345678")

    assert audio_file == expected
    assert info["id"] == "abc123"


def test_download_audio_falls_back_to_id(monkeypatch, tmp_path):
    downloader = YouTubeDownloader(temp_dir=str(tmp_path))

    def fake_extract(self, url, download=False, opts=None):
        return {"id": "xyz789", "title": "Example", "duration": 10}

    monkeypatch.setattr(YouTubeDownloader, "_extract", fake_extract)

    audio_file, _ = downloader.download_audio("https://youtu.be/xyz789aaaaa")

    assert audio_file == str(tmp_path / "xyz789.mp3")


def test_base_opts_sets_default_player_clients(monkeypatch):
    monkeypatch.delenv("YOUTUBE_PLAYER_CLIENTS", raising=False)
    monkeypatch.delenv("COOKIES_FROM_BROWSER", raising=False)
    monkeypatch.delenv("COOKIES_FILE", raising=False)

    opts = YouTubeDownloader()._base_opts()

    expected = [c.strip() for c in DEFAULT_PLAYER_CLIENTS.split(",")]
    assert opts["extractor_args"]["youtube"]["player_client"] == expected


def test_base_opts_default_keyword_uses_yt_dlp_selection(monkeypatch):
    monkeypatch.setenv("YOUTUBE_PLAYER_CLIENTS", "default")

    opts = YouTubeDownloader()._base_opts()

    assert "extractor_args" not in opts


def test_base_opts_merges_overrides(monkeypatch):
    monkeypatch.delenv("YOUTUBE_PLAYER_CLIENTS", raising=False)

    opts = YouTubeDownloader()._base_opts(format="bestaudio/best")

    assert opts["format"] == "bestaudio/best"


def test_private_error_without_cookies_is_translated(monkeypatch):
    monkeypatch.delenv("COOKIES_FROM_BROWSER", raising=False)
    monkeypatch.delenv("COOKIES_FILE", raising=False)

    downloader = YouTubeDownloader()

    def boom(self, url, download):
        raise yt_dlp.utils.DownloadError("ERROR: Private video. Sign in if you...")

    monkeypatch.setattr(yt_dlp.YoutubeDL, "extract_info", boom)

    with pytest.raises(RuntimeError, match="bot-protected"):
        downloader._extract("https://youtu.be/abc", download=False)


def test_genuine_error_is_not_swallowed(monkeypatch):
    downloader = YouTubeDownloader()

    def boom(self, url, download):
        raise yt_dlp.utils.DownloadError("ERROR: Unsupported URL")

    monkeypatch.setattr(yt_dlp.YoutubeDL, "extract_info", boom)

    with pytest.raises(yt_dlp.utils.DownloadError):
        downloader._extract("https://example.com", download=False)
