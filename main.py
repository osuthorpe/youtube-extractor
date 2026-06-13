#!/usr/bin/env python3

import argparse
import os
import sys
import tempfile

from dotenv import load_dotenv

from youtube_downloader import YouTubeDownloader, extract_video_id
from transcriber import WhisperTranscriber
from transcript_manager import TranscriptManager
from summarizer import TranscriptSummarizer, has_credentials
from ui import TerminalUI

# Load environment variables once, at startup.
load_dotenv()


class YouTubeTranscriptExtractor:
    def __init__(self, interactive=True):
        self.interactive = interactive
        self.ui = TerminalUI(clear=interactive)

        # Load config from environment variables
        temp_dir = os.getenv("TEMP_DIR", tempfile.gettempdir())
        self.downloader = YouTubeDownloader(temp_dir=temp_dir)

        transcripts_dir = os.getenv("TRANSCRIPTS_DIR", "transcripts")
        self.transcript_manager = TranscriptManager(output_dir=transcripts_dir)

        self.whisper_model = os.getenv("WHISPER_MODEL", "small")
        self.max_duration = int(os.getenv("MAX_VIDEO_DURATION", "10800"))
        self.include_timestamps = (
            os.getenv("INCLUDE_TIMESTAMPS", "true").lower() == "true"
        )
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

        # Summarization (actionable bullet points via Claude) is opt-out, but only
        # actually runs when Anthropic credentials are present.
        self.summarize = os.getenv("SUMMARIZE", "true").lower() == "true"
        self.summarizer = TranscriptSummarizer()

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
        """Check if the provided string is a valid YouTube video URL."""
        return extract_video_id(url) is not None

    def _allow_long_video(self, duration):
        """Decide whether to proceed when a video exceeds the duration limit."""
        if duration <= self.max_duration:
            return True

        hours = self.max_duration / 3600
        self.ui.print_warning(
            f"Video is longer than the {hours:.1f}h limit "
            f"(MAX_VIDEO_DURATION={self.max_duration}s)."
        )
        if not self.interactive:
            self.ui.print_warning(
                "Skipping. Use --force or raise MAX_VIDEO_DURATION to transcribe it."
            )
            return False
        return self.ui.confirm("Transcribe it anyway?")

    def process_url(self, url, force=False):
        """Process a YouTube URL: download, transcribe, and save."""
        audio_file = None
        try:
            # Get video info (single metadata fetch used for display + limit check)
            self.ui.print_progress("Fetching video information...")
            video_info = self.downloader.get_video_info(url)
            self.ui.print_video_info(video_info)

            # Enforce the duration limit before spending time on a download.
            if not force and not self._allow_long_video(video_info["duration"]):
                return

            # Download audio (this is the second and final metadata fetch).
            self.ui.print_progress("Downloading audio from YouTube...")
            audio_file, video_info = self.downloader.download_audio(url)
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
            _, _, video_folder = self.transcript_manager.save_transcript(
                video_info, formatted_transcript, url
            )

            self.ui.print_success(f"Transcript saved to folder: {video_folder}")

            # Distill the transcript into actionable bullet points.
            if self.summarize:
                self._summarize_to_folder(
                    formatted_transcript["full_text"],
                    video_folder,
                    title=video_info.get("title"),
                )

            # Show preview
            self._print_preview(formatted_transcript["full_text"])

        except Exception as e:
            self.ui.print_error(f"Error processing URL: {e}")
            if self.debug_mode:
                raise
        finally:
            # Always clean up the temp audio file, even on failure.
            if audio_file and os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                except OSError:
                    if self.debug_mode:
                        self.ui.print_warning(
                            "Temporary audio file could not be removed; continuing."
                        )

    def _summarize_to_folder(self, transcript_text, video_folder, title=None):
        """Generate actionable bullet points and save them as summary.md."""
        if not has_credentials():
            self.ui.print_info(
                "Skipping summary: set ANTHROPIC_API_KEY to get actionable bullet "
                "points (or SUMMARIZE=false to silence this)."
            )
            return None

        self.ui.print_progress("Summarizing transcript into actionable points...")
        print("\n" + "=" * 60)
        print("ACTIONABLE POINTS:")
        print("=" * 60)
        try:
            summary = self.summarizer.summarize(
                transcript_text,
                title=title,
                on_text=lambda chunk: print(chunk, end="", flush=True),
            )
            print("\n" + "=" * 60 + "\n")
        except Exception as e:
            print()
            self.ui.print_error(f"Could not summarize transcript: {e}")
            if self.debug_mode:
                raise
            return None

        summary_path = self.transcript_manager.save_summary(video_folder, summary)
        self.ui.print_success(f"Summary saved to: {summary_path}")
        return summary_path

    def _print_preview(self, full_text, limit=500):
        """Print a short preview of the transcript text."""
        print("\n" + "=" * 60)
        print(f"TRANSCRIPT PREVIEW (first {limit} characters):")
        print("=" * 60)
        preview = full_text[:limit]
        print(preview + "..." if len(full_text) > limit else preview)
        print("=" * 60 + "\n")

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

    def view_transcript(self, index):
        """Print the full text of a saved transcript by its list position."""
        transcripts = self.transcript_manager.list_transcripts()
        if not transcripts:
            self.ui.print_info("No transcripts saved yet.")
            return

        if index < 1 or index > len(transcripts):
            self.ui.print_error(
                f"No transcript #{index}. Use 'list' to see valid numbers (1-"
                f"{len(transcripts)})."
            )
            return

        entry = transcripts[index - 1]
        path = self.transcript_manager.get_transcript_path(entry["id"])
        if not path or not path.exists():
            self.ui.print_error(f"Transcript file not found: {path}")
            return

        print("\n" + "=" * 80)
        print(f"{entry['title']}")
        print("=" * 80)
        print(path.read_text(encoding="utf-8"))
        print("=" * 80 + "\n")

    def summarize_transcript(self, index):
        """Generate (or regenerate) a summary for a saved transcript by position."""
        transcripts = self.transcript_manager.list_transcripts()
        if not transcripts:
            self.ui.print_info("No transcripts saved yet.")
            return

        if index < 1 or index > len(transcripts):
            self.ui.print_error(
                f"No transcript #{index}. Use 'list' to see valid numbers (1-"
                f"{len(transcripts)})."
            )
            return

        entry = transcripts[index - 1]
        path = self.transcript_manager.get_transcript_path(entry["id"])
        folder = self.transcript_manager.get_video_folder(entry["id"])
        if not path or not path.exists():
            self.ui.print_error(f"Transcript file not found: {path}")
            return

        self._summarize_to_folder(
            path.read_text(encoding="utf-8"), folder, title=entry["title"]
        )

    def _handle_command(self, user_input):
        """Dispatch a single line of REPL input. Returns False to quit."""
        command = user_input.lower()

        if command in ("quit", "exit", "q"):
            self.ui.print_info("Goodbye!")
            return False
        elif command == "settings":
            self.show_settings()
        elif command == "list":
            self.list_transcripts()
        elif command.startswith("view"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2 and parts[1].strip().isdigit():
                self.view_transcript(int(parts[1].strip()))
            else:
                self.ui.print_error("Usage: view <number> (see 'list').")
        elif command.startswith("summarize"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2 and parts[1].strip().isdigit():
                self.summarize_transcript(int(parts[1].strip()))
            else:
                self.ui.print_error("Usage: summarize <number> (see 'list').")
        elif command == "clear":
            self.ui.clear_screen()
            self.ui.print_header()
            self.ui.print_menu()
        elif command == "help":
            self.ui.print_menu()
        elif self.is_youtube_url(user_input):
            self.process_url(user_input)
        else:
            self.ui.print_error(
                "Invalid input. Please enter a valid YouTube URL or command."
            )
            self.ui.print_info("Type 'help' to see available commands.")
        return True

    def run(self):
        """Main interactive application loop."""
        self.ui.print_header()
        self.ui.print_menu()

        while True:
            try:
                user_input = self.ui.get_input()
                if not user_input:
                    continue
                if not self._handle_command(user_input):
                    break
            except KeyboardInterrupt:
                print("\n")
                self.ui.print_info("Use 'quit' to exit properly.")
            except Exception as e:
                self.ui.print_error(f"Unexpected error: {e}")
                if self.debug_mode:
                    raise

    def run_batch(self, urls, force=False):
        """Transcribe one or more URLs non-interactively. Returns exit code."""
        failures = 0
        for url in urls:
            if not self.is_youtube_url(url):
                self.ui.print_error(f"Not a valid YouTube URL: {url}")
                failures += 1
                continue
            self.process_url(url, force=force)
        return 1 if failures else 0


def _check_dependencies():
    """Ensure required third-party packages are importable."""
    import importlib

    try:
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


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Download and transcribe YouTube videos with OpenAI Whisper.",
    )
    parser.add_argument(
        "urls",
        nargs="*",
        help="One or more YouTube URLs to transcribe. If omitted, an interactive "
        "session starts.",
    )
    parser.add_argument(
        "-m",
        "--model",
        help="Whisper model to use (tiny, base, small, medium, large). "
        "Overrides WHISPER_MODEL.",
    )
    parser.add_argument(
        "--no-timestamps",
        action="store_true",
        help="Skip the timestamped transcript output.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Transcribe even if a video exceeds MAX_VIDEO_DURATION.",
    )
    summary_group = parser.add_mutually_exclusive_group()
    summary_group.add_argument(
        "--summarize",
        dest="summarize",
        action="store_true",
        default=None,
        help="Summarize transcripts into actionable bullet points (needs "
        "ANTHROPIC_API_KEY).",
    )
    summary_group.add_argument(
        "--no-summarize",
        dest="summarize",
        action="store_false",
        help="Skip the actionable-points summary.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Entry point."""
    _check_dependencies()
    args = _parse_args(argv)

    # CLI flags take precedence over environment defaults.
    if args.model:
        os.environ["WHISPER_MODEL"] = args.model
    if args.no_timestamps:
        os.environ["INCLUDE_TIMESTAMPS"] = "false"
    if args.summarize is not None:
        os.environ["SUMMARIZE"] = "true" if args.summarize else "false"

    interactive = not args.urls
    app = YouTubeTranscriptExtractor(interactive=interactive)

    if interactive:
        app.run()
        return 0
    return app.run_batch(args.urls, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
