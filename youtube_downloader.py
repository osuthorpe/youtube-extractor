import yt_dlp
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class YouTubeDownloader:
    def __init__(self, temp_dir=None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
    def download_audio(self, url):
        """Download audio from YouTube URL and return the path to the audio file."""
        # First extract info to get the title
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            # Clean filename for safety
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        # Now download with the sanitized filename
        output_path = os.path.join(self.temp_dir, f"{safe_title}.%(ext)s")
        audio_quality = os.getenv('AUDIO_QUALITY', '192')
        debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': audio_quality,
            }],
            'outtmpl': output_path,
            'quiet': not debug_mode,
            'no_warnings': not debug_mode,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_file = os.path.join(self.temp_dir, f"{safe_title}.mp3")
            
            return audio_file, safe_title, info
    
    def get_video_info(self, url):
        """Get video metadata without downloading."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'upload_date': info.get('upload_date', 'Unknown'),
            }