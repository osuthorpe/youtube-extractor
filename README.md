# YouTube Transcript Extractor

A terminal-based YouTube video transcription tool powered by OpenAI Whisper.

## Features

- Download audio from YouTube videos
- Transcribe using OpenAI Whisper (multiple model sizes)
- Save transcripts with timestamps
- Terminal-based interface
- Transcript management system

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg (required for audio processing):

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Usage

### Interactive mode

Run the application with no arguments to start an interactive session:
```bash
python main.py
```

Once running, you can:
- Paste a YouTube URL to transcribe it
- Type `settings` to change Whisper model size
- Type `list` to view saved transcripts
- Type `view <n>` to print a saved transcript
- Type `quit` to exit

### Non-interactive / batch mode

Pass one or more URLs as arguments to transcribe them and exit — handy for
scripting and pipelines:

```bash
python main.py "https://youtu.be/VIDEO_ID"
python main.py URL1 URL2 URL3 --model small --no-timestamps
```

| Flag | Description |
| --- | --- |
| `-m`, `--model` | Whisper model to use (overrides `WHISPER_MODEL`) |
| `--no-timestamps` | Skip the timestamped transcript output |
| `--force` | Transcribe even if a video exceeds `MAX_VIDEO_DURATION` |

In batch mode, videos longer than `MAX_VIDEO_DURATION` are skipped unless
`--force` is given; in interactive mode you'll be prompted to confirm.

### Configuration

The app reads environment variables from a `.env` file if present. Useful options include:

| Variable | Default | Description |
| --- | --- | --- |
| `TEMP_DIR` | System temp | Directory for intermediate audio files |
| `TRANSCRIPTS_DIR` | `transcripts` | Destination folder for transcript archives |
| `WHISPER_MODEL` | `base` | Default Whisper model loaded on startup |
| `INCLUDE_TIMESTAMPS` | `true` | Set to `false` to skip timestamped transcript output |
| `DEFAULT_LANGUAGE` | `en` | Force a transcription language (set to `none` for auto-detect) |
| `USE_GPU` | `true` | Disable to force CPU inference even if CUDA is available |
| `WHISPER_BACKEND` | `openai` | Set to `faster` to use [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (often several times faster, especially on CPU) |
| `MAX_VIDEO_DURATION` | `10800` | Duration limit in seconds; longer videos prompt for confirmation (interactive) or are skipped (batch) |
| `AUDIO_QUALITY` | `192` | Target audio bitrate (kbps) for the extracted MP3 |

### Faster transcription with faster-whisper

For a significant speedup (especially on CPU), install the optional backend and
enable it:

```bash
pip install faster-whisper
export WHISPER_BACKEND=faster
```

## Whisper Models

- **tiny**: Fastest, lowest quality (39M)
- **base**: Good balance (74M) - Default
- **small**: Better quality (244M)
- **medium**: High quality (769M)
- **large**: Best quality, slowest (1550M)

## Output

Transcripts are saved in the `transcripts/` folder as:
- `.txt` files with full transcript and timestamps
- `.json` files with structured data
- `.txt` files without timestamps when `INCLUDE_TIMESTAMPS=false`

## Requirements

- Python 3.8+
- FFmpeg
- ~2GB disk space for Whisper models
- GPU recommended for faster transcription (but works on CPU)

## Notes

- First run will download the Whisper model (~74MB for base model)
- Transcription speed depends on video length and hardware
- Longer videos (>1 hour) may take significant time on CPU

## Development

Create a virtual environment and install dependencies:

```bash
make setup
```

Run quality checks:

```bash
make format
make lint
make test
```

Tests are written with `pytest` and rely on lightweight stubs so no Whisper model download is required.
