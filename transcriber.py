import os

import torch
import whisper


class WhisperTranscriber:
    def __init__(self, model_size="base"):
        """Initialize a Whisper model.

        Model sizes: tiny, base, small, medium, large

        Two backends are supported, selected with the WHISPER_BACKEND env var:
          * "openai"  (default) - the reference openai-whisper package.
          * "faster"            - faster-whisper (CTranslate2), typically several
                                  times faster and lighter on memory, especially
                                  on CPU. Requires `pip install faster-whisper`.
        """
        self.model_size = model_size
        self.backend = os.getenv("WHISPER_BACKEND", "openai").lower()

        default_language = os.getenv("DEFAULT_LANGUAGE", "en")
        self.language = None if default_language.lower() == "none" else default_language
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

        use_gpu = os.getenv("USE_GPU", "true").lower() == "true"
        self.device = "cuda" if (torch.cuda.is_available() and use_gpu) else "cpu"

        print(f"Loading Whisper {model_size} model ({self.backend} backend)...")
        if self.backend == "faster":
            self._load_faster_model()
        else:
            self.model = whisper.load_model(model_size, device=self.device)
        print(f"Model loaded on {self.device}")

    def _load_faster_model(self):
        """Load a faster-whisper model, mapping the device to its conventions."""
        try:
            from faster_whisper import WhisperModel
        except ImportError as error:
            raise RuntimeError(
                "WHISPER_BACKEND=faster requires the faster-whisper package. "
                "Install it with: pip install faster-whisper"
            ) from error

        compute_type = "float16" if self.device == "cuda" else "int8"
        self.model = WhisperModel(
            self.model_size, device=self.device, compute_type=compute_type
        )

    def transcribe(self, audio_file_path):
        """Transcribe an audio file, returning a normalized result dict.

        The returned dict always has the shape::

            {"text": str, "segments": [{"start", "end", "text"}, ...], "language": str}

        regardless of which backend produced it.
        """
        print("Transcribing audio...")
        if self.backend == "faster":
            return self._transcribe_faster(audio_file_path)
        return self._transcribe_openai(audio_file_path)

    def _transcribe_openai(self, audio_file_path):
        return self.model.transcribe(
            audio_file_path,
            fp16=self.device != "cpu",
            language=self.language,
            verbose=self.debug_mode,
        )

    def _transcribe_faster(self, audio_file_path):
        segments_iter, info = self.model.transcribe(
            audio_file_path, language=self.language
        )

        segments = []
        text_parts = []
        for segment in segments_iter:
            segments.append(
                {"start": segment.start, "end": segment.end, "text": segment.text}
            )
            text_parts.append(segment.text)
            if self.debug_mode:
                print(f"[{segment.start:.2f} - {segment.end:.2f}] {segment.text}")

        return {
            "text": "".join(text_parts),
            "segments": segments,
            "language": getattr(info, "language", "unknown"),
        }

    def format_transcript(self, result, include_timestamps=True):
        """Format the transcript result into readable text."""
        transcript = result["text"].strip()

        if include_timestamps and result.get("segments"):
            formatted_segments = []
            for segment in result["segments"]:
                start = self._format_timestamp(segment["start"])
                end = self._format_timestamp(segment["end"])
                text = segment["text"].strip()
                formatted_segments.append(f"[{start} - {end}] {text}")
        else:
            formatted_segments = []

        return {
            "full_text": transcript,
            "segments": formatted_segments,
            "language": result.get("language", "unknown"),
        }

    def _format_timestamp(self, seconds):
        """Convert seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
