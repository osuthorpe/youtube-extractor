#!/usr/bin/env python3

import os
import sys
import tempfile
import re
from dotenv import load_dotenv

from youtube_downloader import YouTubeDownloader
from transcriber import WhisperTranscriber
from transcript_manager import TranscriptManager
from ui import TerminalUI

# Load environment variables
load_dotenv()


class YouTubeTranscriptExtractor:
    def __init__(self):
        self.ui = TerminalUI()

        # Load config from environment variables
        temp_dir = os.getenv("TEMP_DIR", tempfile.gettempdir())
        self.downloader = YouTubeDownloader(temp_dir=temp_dir)

        transcripts_dir = os.getenv("TRANSCRIPTS_DIR", "transcripts")
        self.transcript_manager = TranscriptManager(output_dir=transcripts_dir)

        self.whisper_model = os.getenv("WHISPER_MODEL", "base")
        self.max_duration = int(os.getenv("MAX_VIDEO_DURATION", "10800"))
        self.include_timestamps = (
            os.getenv("INCLUDE_TIMESTAMPS", "true").lower() == "true"
        )
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

        self.transcriber = None
        self._init_transcriber()

    def _init_transcriber(self):
        """Initialize Whisper transcriber."""
        try:
            self.ui.print_info(f"Initializing Whisper {self.whisper_model} model...")
            self.transcriber = WhisperTranscriber(self.whisper_model)
            self.ui.print_success("Model loaded successfully!")
        except Exception as e:
            self.ui.print_error(f"Failed to load Whisper model: {e}")
            sys.exit(1)

    def is_youtube_url(self, url):
        """Check if the provided string is a valid YouTube URL."""
        youtube_patterns = [
            r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/",
            r"(https?://)?(www\.)?(m\.youtube\.com)/",
        ]
        return any(re.match(pattern, url) for pattern in youtube_patterns)

    def process_url(self, url):
        """Process a YouTube URL: download, transcribe, and save."""
        try:
            # Get video info
            self.ui.print_progress("Fetching video information...")
            video_info = self.downloader.get_video_info(url)
            self.ui.print_video_info(video_info)

            # Check duration
            if video_info["duration"] > self.max_duration:
                hours = self.max_duration // 3600
                self.ui.print_warning(
                    f"Video is longer than {hours} hours. This may take a while..."
                )

            # Download audio
            self.ui.print_progress("Downloading audio from YouTube...")
            audio_file, safe_title, full_info = self.downloader.download_audio(url)
            self.ui.print_success("Audio downloaded successfully!")

            # Transcribe
            self.ui.print_progress("Transcribing audio with Whisper...")
            self.ui.print_info(
                "This may take several minutes depending on video length..."
            )

            result = self.transcriber.transcribe(audio_file)
            formatted_transcript = self.transcriber.format_transcript(
                result,
                include_timestamps=self.include_timestamps,
            )
            self.ui.print_success("Transcription completed!")

            # Save transcript
            self.ui.print_progress("Saving transcript...")
            txt_path, json_path, video_folder = self.transcript_manager.save_transcript(
                video_info, formatted_transcript, url
            )

            self.ui.print_success(f"Transcript saved to folder: {video_folder}")

            # Clean up temp audio file
            try:
                os.remove(audio_file)
            except OSError:
                if self.debug_mode:
                    self.ui.print_warning(
                        "Temporary audio file could not be removed; continuing."
                    )

            # Show preview
            print("\n" + "=" * 60)
            print("TRANSCRIPT PREVIEW (first 500 characters):")
            print("=" * 60)
            preview = formatted_transcript["full_text"][:500]
            print(
                preview + "..."
                if len(formatted_transcript["full_text"]) > 500
                else preview
            )
            print("=" * 60 + "\n")

        except Exception as e:
            self.ui.print_error(f"Error processing URL: {e}")

    def show_settings(self):
        """Show and handle settings menu."""
        self.ui.print_settings_menu(self.whisper_model)
        choice = self.ui.get_settings_choice()

        model_map = {
            "1": "tiny",
            "2": "base",
            "3": "small",
            "4": "medium",
            "5": "large",
        }

        if choice in model_map:
            new_model = model_map[choice]
            if new_model != self.whisper_model:
                self.whisper_model = new_model
                self.ui.print_info(f"Switching to {new_model} model...")
                self._init_transcriber()
            else:
                self.ui.print_info("Model unchanged.")
        elif choice != "0":
            self.ui.print_error("Invalid choice.")

    def list_transcripts(self):
        """List all saved transcripts."""
        transcripts = self.transcript_manager.list_transcripts()

        if not transcripts:
            self.ui.print_info("No transcripts saved yet.")
            return

        print("\n" + "=" * 80)
        print("SAVED TRANSCRIPTS:")
        print("=" * 80)

        for i, transcript in enumerate(transcripts, 1):
            print(f"\n{i}. {transcript['title']}")
            print(f"   URL: {transcript['url']}")
            print(f"   File: {transcript['file']}")
            print(f"   Date: {transcript['date']}")

        print("=" * 80 + "\n")

    def run(self):
        """Main application loop."""
        self.ui.print_header()
        self.ui.print_menu()

        while True:
            try:
                user_input = self.ui.get_input()

                if not user_input:
                    continue

                # Handle commands
                if user_input.lower() in ["quit", "exit", "q"]:
                    self.ui.print_info("Goodbye!")
                    break

                elif user_input.lower() == "settings":
                    self.show_settings()

                elif user_input.lower() == "list":
                    self.list_transcripts()

                elif user_input.lower() == "clear":
                    self.ui.clear_screen()
                    self.ui.print_header()
                    self.ui.print_menu()

                elif user_input.lower() == "help":
                    self.ui.print_menu()

                # Handle YouTube URL
                elif self.is_youtube_url(user_input):
                    self.process_url(user_input)

                else:
                    self.ui.print_error(
                        "Invalid input. Please enter a valid YouTube URL or command."
                    )
                    self.ui.print_info("Type 'help' to see available commands.")

            except KeyboardInterrupt:
                print("\n")
                self.ui.print_info("Use 'quit' to exit properly.")
            except Exception as e:
                self.ui.print_error(f"Unexpected error: {e}")


def main():
    """Entry point."""
    # Check dependencies
    try:
        import importlib

        for dependency in ("yt_dlp", "whisper", "torch"):
            importlib.import_module(dependency)
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("\nPlease install requirements:")
        print("  pip install -r requirements.txt")
        print("\nNote: You may also need to install ffmpeg:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu: sudo apt install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org")
        sys.exit(1)

    app = YouTubeTranscriptExtractor()
    app.run()


if __name__ == "__main__":
    main()
