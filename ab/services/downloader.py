# services/downloader.py
import yt_dlp
from pathlib import Path


class VideoDownloader:
    def __init__(self, output_dir: str, s3_client):
        self.output_dir = Path(output_dir)
        self.s3 = s3_client

    def download(self, video_id: str) -> dict:
        """
        Baixa vídeo em melhor qualidade até 1080p
        Retorna metadados e caminho local
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        output_template = str(self.output_dir / f"{video_id}.%(ext)s")

        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['pt', 'en'],
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        local_path = self.output_dir / f"{video_id}.mp4"

        # Upload para S3
        s3_key = f"raw_videos/{video_id}.mp4"
        self.s3.upload_file(str(local_path), s3_key)

        return {
            'video_id': video_id,
            'local_path': str(local_path),
            's3_key': s3_key,
            'duration': info['duration'],
            'title': info['title'],
            'description': info.get('description', ''),
            'subtitles_path': self._get_subtitles_path(video_id)
        }