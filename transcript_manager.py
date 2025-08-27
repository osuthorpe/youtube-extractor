import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class TranscriptManager:
    def __init__(self, output_dir='transcripts'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.metadata_file = self.output_dir / 'metadata.json'
        self.metadata = self._load_metadata()
    
    def _load_metadata(self):
        """Load metadata from file."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save metadata to file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def save_transcript(self, video_info, transcript_data, url):
        """Save transcript to file and update metadata."""
        # Generate folder name for this video
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = "".join(c for c in video_info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:100]  # Limit filename length
        
        # Create folder for this video
        video_folder_name = f"{timestamp}_{safe_title}"
        video_folder = self.output_dir / video_folder_name
        video_folder.mkdir(exist_ok=True)
        
        # Create filenames within the folder
        txt_filename = "transcript.txt"
        timestamped_filename = "transcript_timestamped.txt"
        json_filename = "transcript.json"
        metadata_filename = "metadata.json"
        
        txt_path = video_folder / txt_filename
        timestamped_path = video_folder / timestamped_filename
        json_path = video_folder / json_filename
        video_metadata_path = video_folder / metadata_filename
        
        # Save plain text transcript (just the text, ready to copy/paste)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(transcript_data['full_text'])
        
        # Save timestamped version if segments are available
        if transcript_data.get('segments'):
            with open(timestamped_path, 'w', encoding='utf-8') as f:
                for segment in transcript_data['segments']:
                    f.write(segment + "\n")
        
        # Save JSON version with full transcript data
        json_data = {
            'video_info': video_info,
            'url': url,
            'transcribed_at': datetime.now().isoformat(),
            'transcript': transcript_data
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Save video metadata separately for easier access
        video_metadata = {
            'title': video_info['title'],
            'url': url,
            'uploader': video_info['uploader'],
            'duration': video_info['duration'],
            'transcribed_at': datetime.now().isoformat(),
            'language': transcript_data.get('language', 'unknown'),
            'files': {
                'transcript_txt': txt_filename,
                'transcript_timestamped': timestamped_filename if transcript_data.get('segments') else None,
                'transcript_json': json_filename
            }
        }
        
        with open(video_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(video_metadata, f, indent=2, ensure_ascii=False)
        
        # Update global metadata
        metadata_entry = {
            'title': video_info['title'],
            'url': url,
            'folder': video_folder_name,
            'txt_file': str(video_folder / txt_filename),
            'json_file': str(video_folder / json_filename),
            'metadata_file': str(video_folder / metadata_filename),
            'transcribed_at': datetime.now().isoformat(),
            'duration': video_info['duration']
        }
        
        self.metadata[timestamp] = metadata_entry
        self._save_metadata()
        
        return txt_path, json_path, video_folder
    
    def list_transcripts(self):
        """List all saved transcripts."""
        if not self.metadata:
            return []
        
        transcripts = []
        for key, value in sorted(self.metadata.items(), reverse=True):
            transcripts.append({
                'id': key,
                'title': value['title'],
                'url': value['url'],
                'file': value['txt_file'],
                'date': value['transcribed_at']
            })
        
        return transcripts
    
    def get_transcript_path(self, transcript_id):
        """Get the path to a transcript file."""
        if transcript_id in self.metadata:
            return Path(self.metadata[transcript_id]['txt_file'])
        return None
    
    def get_video_folder(self, transcript_id):
        """Get the folder path for a specific video transcript."""
        if transcript_id in self.metadata:
            return self.output_dir / self.metadata[transcript_id]['folder']
        return None