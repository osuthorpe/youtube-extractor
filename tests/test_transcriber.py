import transcriber as transcriber_module


class _DummyModel:
    def transcribe(self, *args, **kwargs):
        return {
            "text": "Hello world",
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Hello"},
                {"start": 5.0, "end": 8.0, "text": "world"},
            ],
            "language": "en",
        }


def _make_transcriber(monkeypatch):
    dummy_model = _DummyModel()
    monkeypatch.setenv("USE_GPU", "false")
    monkeypatch.setattr(
        transcriber_module.whisper, "load_model", lambda *args, **kwargs: dummy_model
    )
    return transcriber_module.WhisperTranscriber("base")


def test_format_transcript_with_timestamps(monkeypatch):
    transcriber = _make_transcriber(monkeypatch)

    result = transcriber.model.transcribe(None)
    formatted = transcriber.format_transcript(result, include_timestamps=True)

    assert formatted["segments"]
    assert formatted["segments"][0].startswith("[")


def test_format_transcript_without_timestamps(monkeypatch):
    transcriber = _make_transcriber(monkeypatch)

    result = transcriber.model.transcribe(None)
    formatted = transcriber.format_transcript(result, include_timestamps=False)

    assert formatted["segments"] == []
