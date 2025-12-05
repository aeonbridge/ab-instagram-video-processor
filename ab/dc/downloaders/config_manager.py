"""
Configuration Manager for Video Clipper Service
Handles loading and validating environment variables from .env file
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Configuration container for video clipper service"""

    def __init__(self):
        """Load configuration from environment variables"""
        # Load .env file from project root
        env_path = Path(__file__).parent.parent.parent.parent / '.env'
        load_dotenv(dotenv_path=env_path)

        # Paths
        self.downloads_path = Path(os.getenv('DOWNLOADS_PATH', 'downloads/'))
        self.stored_processed_videos = Path(os.getenv('STORED_PROCESSED_VIDEOS', 'processed_videos/'))
        self.temp_path = Path(os.getenv('TEMP_PATH', 'temp/'))
        self.log_file = os.getenv('LOG_FILE', '')

        # Download settings
        self.download_quality = os.getenv('DOWNLOAD_QUALITY', 'best')
        self.download_timeout = int(os.getenv('DOWNLOAD_TIMEOUT', '600'))

        # FFmpeg settings
        self.ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')
        self.video_codec = os.getenv('VIDEO_CODEC', 'libx264')
        self.audio_codec = os.getenv('AUDIO_CODEC', 'aac')
        self.crf_quality = int(os.getenv('CRF_QUALITY', '23'))
        self.ffmpeg_preset = os.getenv('FFMPEG_PRESET', 'medium')
        self.include_audio = self._str_to_bool(os.getenv('INCLUDE_AUDIO', 'true'))

        # Aspect ratio (original, 9:16, 16:9, 1:1, 4:5)
        self.aspect_ratio = os.getenv('ASPECT_RATIO', 'original')

        # Processing settings
        self.max_concurrent_clips = int(os.getenv('MAX_CONCURRENT_CLIPS', '4'))
        self.enable_parallel_processing = self._str_to_bool(
            os.getenv('ENABLE_PARALLEL_PROCESSING', 'true')
        )
        self.clip_timeout = int(os.getenv('CLIP_TIMEOUT', '120'))

        # Limits
        self.max_video_duration = int(os.getenv('MAX_VIDEO_DURATION', '7200'))
        self.max_clip_duration = int(os.getenv('MAX_CLIP_DURATION', '300'))
        self.max_clips_per_video = int(os.getenv('MAX_CLIPS_PER_VIDEO', '50'))

        # Cleanup
        self.cleanup_source_video = self._str_to_bool(
            os.getenv('CLEANUP_SOURCE_VIDEO', 'false')
        )

        # Logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

        # Ensure directories exist
        self._create_directories()

    def _str_to_bool(self, value: str) -> bool:
        """Convert string to boolean"""
        return value.lower() in ('true', '1', 'yes', 'on')

    def _create_directories(self):
        """Create necessary directories if they don't exist"""
        self.downloads_path.mkdir(parents=True, exist_ok=True)
        self.stored_processed_videos.mkdir(parents=True, exist_ok=True)
        if self.temp_path:
            self.temp_path.mkdir(parents=True, exist_ok=True)
        if self.log_file:
            log_dir = Path(self.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check FFmpeg availability
        import shutil
        if not shutil.which(self.ffmpeg_path):
            return False, f"FFmpeg not found at: {self.ffmpeg_path}"

        # Check yt-dlp availability
        if not shutil.which('yt-dlp'):
            return False, "yt-dlp not found. Install with: pip install yt-dlp"

        # Validate numeric ranges
        if self.crf_quality < 0 or self.crf_quality > 51:
            return False, f"CRF quality must be 0-51, got: {self.crf_quality}"

        if self.max_concurrent_clips < 1:
            return False, f"max_concurrent_clips must be >= 1, got: {self.max_concurrent_clips}"

        # Check write permissions
        if not os.access(self.stored_processed_videos, os.W_OK):
            return False, f"No write permission for: {self.stored_processed_videos}"

        return True, None

    def get_ffmpeg_options(self) -> dict:
        """Get FFmpeg encoding options as dictionary"""
        return {
            'video_codec': self.video_codec,
            'audio_codec': self.audio_codec,
            'crf': self.crf_quality,
            'preset': self.ffmpeg_preset,
            'include_audio': self.include_audio,
            'aspect_ratio': self.aspect_ratio
        }

    def __repr__(self) -> str:
        return (
            f"Config("
            f"downloads={self.downloads_path}, "
            f"processed={self.stored_processed_videos}, "
            f"quality={self.download_quality}, "
            f"codec={self.video_codec}, "
            f"parallel={self.enable_parallel_processing})"
        )


# Global config instance
_config: Optional[Config] = None


def load_config() -> Config:
    """
    Load or return cached configuration

    Returns:
        Config object with all settings
    """
    global _config
    if _config is None:
        _config = Config()
        is_valid, error = _config.validate()
        if not is_valid:
            raise ValueError(f"Invalid configuration: {error}")
    return _config


def get_config() -> Config:
    """
    Get current configuration (load if not loaded)

    Returns:
        Config object
    """
    return load_config()


def reload_config() -> Config:
    """
    Force reload configuration from .env

    Returns:
        New Config object
    """
    global _config
    _config = None
    return load_config()