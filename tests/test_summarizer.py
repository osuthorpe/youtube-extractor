import pytest

import summarizer
from summarizer import TranscriptSummarizer, build_messages, has_credentials


def test_build_messages_includes_title_and_transcript():
    messages = build_messages("hello world", title="My Episode")

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "actionable" in messages[0]["content"].lower()
    assert "sponsor" in messages[0]["content"].lower()
    assert messages[1]["role"] == "user"
    assert "My Episode" in messages[1]["content"]
    assert "hello world" in messages[1]["content"]


def test_build_messages_without_title():
    messages = build_messages("just a transcript")

    assert "Title:" not in messages[1]["content"]
    assert "just a transcript" in messages[1]["content"]


def test_has_credentials_reflects_env(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert has_credentials() is False

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert has_credentials() is True


def test_summarize_rejects_empty_transcript():
    with pytest.raises(ValueError):
        TranscriptSummarizer().summarize("   ")


def test_summary_model_defaults(monkeypatch):
    monkeypatch.delenv("SUMMARY_MODEL", raising=False)
    assert TranscriptSummarizer().model == summarizer.DEFAULT_SUMMARY_MODEL

    monkeypatch.setenv("SUMMARY_MODEL", "gpt-4o")
    assert TranscriptSummarizer().model == "gpt-4o"


def _make_chunk(text):
    delta = type("Delta", (), {"content": text})()
    choice = type("Choice", (), {"delta": delta})()
    return type("Chunk", (), {"choices": [choice]})()


def test_summarize_streams_and_returns_text():
    """Exercise the streaming path with a fake OpenAI client."""

    class FakeCompletions:
        def create(self, **kwargs):
            assert kwargs["stream"] is True
            assert kwargs["model"]
            return iter([_make_chunk("- point one\n"), _make_chunk("- point two\n")])

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    captured = []
    s = TranscriptSummarizer()
    s._client = FakeClient()

    result = s.summarize("a transcript", on_text=captured.append)

    assert result == "- point one\n- point two"
    assert captured == ["- point one\n", "- point two\n"]
