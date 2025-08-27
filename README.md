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

## Requirements

- Python 3.8+
- FFmpeg
- ~2GB disk space for Whisper models
- GPU recommended for faster transcription (but works on CPU)

## Notes

- First run will download the Whisper model (~74MB for base model)
- Transcription speed depends on video length and hardware
- Longer videos (>1 hour) may take significant time on CPU