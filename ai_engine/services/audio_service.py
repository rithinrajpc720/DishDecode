import os, subprocess, tempfile
import yt_dlp
from django.conf import settings

class AudioExtractor:
    @staticmethod
    def extract_audio(video_url):
        """Extract audio from a video URL and save it to a temporary file."""
        temp_dir = tempfile.gettempdir()
        output_file_base = os.path.join(temp_dir, 'dishdecode_audio_%(id)s')
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'outtmpl': output_file_base,
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                audio_file = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                return audio_file
        except Exception as e:
            print(f"Error extracting audio: {str(e)}")
            return None

    @staticmethod
    def cleanup(file_path):
        """Remove a temporary file."""
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
