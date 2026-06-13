import pytest

import summarizer
from summarizer import TranscriptSummarizer, build_messages, has_credentials


def test_build_messages_includes_title_and_transcript():
    system, messages = build_messages("hello world", title="My Episode")

    assert "actionable" in system.lower()
    assert "sponsor" in system.lower()
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert "My Episode" in messages[0]["content"]
    assert "hello world" in messages[0]["content"]


def test_build_messages_without_title():
    _, messages = build_messages("just a transcript")

    assert "Title:" not in messages[0]["content"]
    assert "just a transcript" in messages[0]["content"]


def test_has_credentials_reflects_env(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    assert has_credentials() is False

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert has_credentials() is True


def test_summarize_rejects_empty_transcript():
    with pytest.raises(ValueError):
        TranscriptSummarizer().summarize("   ")


def test_summary_model_defaults(monkeypatch):
    monkeypatch.delenv("SUMMARY_MODEL", raising=False)
    assert TranscriptSummarizer().model == summarizer.DEFAULT_SUMMARY_MODEL

    monkeypatch.setenv("SUMMARY_MODEL", "claude-sonnet-4-6")
    assert TranscriptSummarizer().model == "claude-sonnet-4-6"


def test_summarize_streams_and_returns_text(monkeypatch):
    """Exercise the streaming path with a fake Anthropic client."""

    class FakeStream:
        text_stream = ["- point one\n", "- point two\n"]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get_final_message(self):
            return type("Msg", (), {"stop_reason": "end_turn", "content": []})()

    class FakeMessages:
        def stream(self, **kwargs):
            assert kwargs["model"]
            assert kwargs["thinking"] == {"type": "adaptive"}
            return FakeStream()

    class FakeClient:
        messages = FakeMessages()

    captured = []
    s = TranscriptSummarizer()
    s._client = FakeClient()

    result = s.summarize("a transcript", on_text=captured.append)

    assert result == "- point one\n- point two"
    assert captured == ["- point one\n", "- point two\n"]
