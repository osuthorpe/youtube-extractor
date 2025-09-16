import whisper
import os
import torch
from dotenv import load_dotenv

load_dotenv()


class WhisperTranscriber:
    def __init__(self, model_size="base"):
        """Initialize Whisper model.

        Model sizes: tiny, base, small, medium, large
        """
        print(f"Loading Whisper {model_size} model...")
        use_gpu = os.getenv("USE_GPU", "true").lower() == "true"
        self.device = "cuda" if (torch.cuda.is_available() and use_gpu) else "cpu"
        self.model = whisper.load_model(model_size, device=self.device)
        print(f"Model loaded on {self.device}")

    def transcribe(self, audio_file_path):
        """Transcribe audio file using Whisper."""
        print("Transcribing audio...")

        default_language = os.getenv("DEFAULT_LANGUAGE", "en")
        if default_language.lower() == "none":
            default_language = None

        debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

        # Transcribe with progress indication
        result = self.model.transcribe(
            audio_file_path,
            fp16=False if self.device == "cpu" else True,
            language=default_language,
            verbose=debug_mode,
        )

        return result

    def format_transcript(self, result, include_timestamps=True):
        """Format the transcript result into readable text."""
        transcript = result["text"].strip()

        if include_timestamps and "segments" in result:
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
