from colorama import init, Fore, Style
import os


class TerminalUI:
    def __init__(self):
        init(autoreset=True)
        self.clear_screen()

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system("cls" if os.name == "nt" else "clear")

    def print_header(self):
        """Print application header."""
        print(
            Fore.CYAN
            + Style.BRIGHT
            + """
╔══════════════════════════════════════════════════════════════╗
║             YouTube Transcript Extractor                     ║
║                Powered by OpenAI Whisper                     ║
╚══════════════════════════════════════════════════════════════╝
        """
            + Style.RESET_ALL
        )

    def print_menu(self):
        """Print main menu."""
        print(Fore.YELLOW + "\nOptions:" + Style.RESET_ALL)
        print("  • Paste a YouTube URL to transcribe")
        print("  • Type 'settings' to change Whisper model")
        print("  • Type 'list' to view saved transcripts")
        print("  • Type 'quit' or 'exit' to close")
        print()

    def get_input(self):
        """Get user input with prompt."""
        return input(
            Fore.GREEN + "Enter YouTube URL or command: " + Style.RESET_ALL
        ).strip()

    def print_info(self, message):
        """Print info message."""
        print(Fore.BLUE + f"ℹ {message}" + Style.RESET_ALL)

    def print_success(self, message):
        """Print success message."""
        print(Fore.GREEN + f"✓ {message}" + Style.RESET_ALL)

    def print_error(self, message):
        """Print error message."""
        print(Fore.RED + f"✗ {message}" + Style.RESET_ALL)

    def print_warning(self, message):
        """Print warning message."""
        print(Fore.YELLOW + f"⚠ {message}" + Style.RESET_ALL)

    def print_video_info(self, info):
        """Print video information."""
        print(Fore.CYAN + "\nVideo Information:" + Style.RESET_ALL)
        print(f"  Title: {info['title']}")
        print(f"  Uploader: {info['uploader']}")
        print(f"  Duration: {self._format_duration(info['duration'])}")
        print()

    def print_progress(self, message):
        """Print progress message."""
        print(Fore.MAGENTA + f"⟳ {message}" + Style.RESET_ALL)

    def _format_duration(self, seconds):
        """Format duration from seconds to readable format."""
        if seconds == 0:
            return "Unknown"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def print_settings_menu(self, current_model):
        """Print settings menu."""
        print(Fore.CYAN + "\nWhisper Model Settings" + Style.RESET_ALL)
        print(f"Current model: {Fore.YELLOW}{current_model}{Style.RESET_ALL}")
        print("\nAvailable models:")
        print("  1. tiny    (39M, fastest, lower quality)")
        print("  2. base    (74M, good balance)")
        print("  3. small   (244M, better quality)")
        print("  4. medium  (769M, high quality)")
        print("  5. large   (1550M, best quality, slowest)")
        print("  0. Cancel")
        print()

    def get_settings_choice(self):
        """Get settings choice from user."""
        return input(Fore.GREEN + "Select model (0-5): " + Style.RESET_ALL).strip()
