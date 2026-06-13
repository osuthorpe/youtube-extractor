import os

import torch
import whisper


class WhisperTranscriber:
    def __init__(self, model_size="small"):
        """Initialize a Whisper model.

        Model sizes: tiny, base, small, medium, large

        Uses the full openai-whisper implementation. The default is "small",
        a good quality/footprint balance; bump to "medium" or "large" for
        higher accuracy on long videos.
        """
        self.model_size = model_size

        default_language = os.getenv("DEFAULT_LANGUAGE", "en")
        self.language = None if default_language.lower() == "none" else default_language
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

        use_gpu = os.getenv("USE_GPU", "true").lower() == "true"
        self.device = "cuda" if (torch.cuda.is_available() and use_gpu) else "cpu"

        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size, device=self.device)
        print(f"Model loaded on {self.device}")

    def transcribe(self, audio_file_path):
        """Transcribe an audio file, returning Whisper's result dict.

        The result has the shape::

            {"text": str, "segments": [{"start", "end", "text"}, ...], "language": str}
        """
        print("Transcribing audio...")
        return self.model.transcribe(
            audio_file_path,
            fp16=self.device != "cpu",
            language=self.language,
            verbose=self.debug_mode,
        )

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
