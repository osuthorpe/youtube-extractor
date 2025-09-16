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

Run the application:
```bash
python main.py
```

Once running, you can:
- Paste a YouTube URL to transcribe it
- Type `settings` to change Whisper model size
- Type `list` to view saved transcripts
- Type `quit` to exit

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
