import yt_dlp
import pytest

from youtube_downloader import YouTubeDownloader, DEFAULT_PLAYER_CLIENTS


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
