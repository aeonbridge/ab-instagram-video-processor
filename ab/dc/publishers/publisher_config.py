"""
Publisher Configuration Manager
Handles loading and validating configuration from environment variables
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class PublisherConfig:
    """Configuration container for publisher service"""

    def __init__(self):
        """Load configuration from environment variables"""
        # Try to load .env from multiple locations
        # 1. Local publishers directory
        local_env = Path(__file__).parent / '.env'
        # 2. Project root
        root_env = Path(__file__).parent.parent.parent.parent / '.env'

        if local_env.exists():
            load_dotenv(dotenv_path=local_env)
        elif root_env.exists():
            load_dotenv(dotenv_path=root_env)
        else:
            # Load from current directory as fallback
            load_dotenv()

        # YouTube Configuration
        self.youtube_client_id = os.getenv('YOUTUBE_CLIENT_ID', '')
        self.youtube_client_secret = os.getenv('YOUTUBE_CLIENT_SECRET', '')
        self.youtube_redirect_uri = os.getenv('YOUTUBE_REDIRECT_URI', 'http://localhost:8080')
        self.youtube_access_token = os.getenv('YOUTUBE_ACCESS_TOKEN', '')
        self.youtube_refresh_token = os.getenv('YOUTUBE_REFRESH_TOKEN', '')

        # TikTok Configuration
        self.tiktok_client_key = os.getenv('TIKTOK_CLIENT_KEY', '')
        self.tiktok_client_secret = os.getenv('TIKTOK_CLIENT_SECRET', '')
        self.tiktok_redirect_uri = os.getenv('TIKTOK_REDIRECT_URI', 'http://localhost:8080')
        self.tiktok_access_token = os.getenv('TIKTOK_ACCESS_TOKEN', '')
        self.tiktok_refresh_token = os.getenv('TIKTOK_REFRESH_TOKEN', '')

        # General Publisher Settings
        self.default_platform = os.getenv('DEFAULT_PLATFORM', 'youtube')
        self.upload_chunk_size = int(os.getenv('UPLOAD_CHUNK_SIZE', str(10 * 1024 * 1024)))  # 10MB
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('RETRY_DELAY', '5'))
        self.enable_auto_retry = self._str_to_bool(os.getenv('ENABLE_AUTO_RETRY', 'true'))
        self.enable_queue_processing = self._str_to_bool(os.getenv('ENABLE_QUEUE_PROCESSING', 'true'))
        self.max_concurrent_uploads = int(os.getenv('MAX_CONCURRENT_UPLOADS', '2'))

        # Token storage
        self.token_storage_path = Path(os.getenv(
            'TOKEN_STORAGE_PATH',
            str(Path.home() / '.ab_publisher_tokens.json')
        ))

        # Video processing paths
        self.processed_videos_path = Path(os.getenv('STORED_PROCESSED_VIDEOS', 'processed_videos/'))
        self.thumbnails_path = Path(os.getenv('THUMBNAILS_PATH', 'thumbnails/'))

        # FFprobe path for video validation
        self.ffprobe_path = os.getenv('FFPROBE_PATH', 'ffprobe')

        # Logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', 'logs/publisher.log')

        # Ensure directories exist
        self._create_directories()

    def _str_to_bool(self, value: str) -> bool:
        """Convert string to boolean"""
        return value.lower() in ('true', '1', 'yes', 'on')

    def _create_directories(self):
        """Create necessary directories if they don't exist"""
        self.processed_videos_path.mkdir(parents=True, exist_ok=True)
        self.thumbnails_path.mkdir(parents=True, exist_ok=True)
        self.token_storage_path.parent.mkdir(parents=True, exist_ok=True)

        if self.log_file:
            log_dir = Path(self.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)

    def validate_youtube(self) -> tuple[bool, Optional[str]]:
        """
        Validate YouTube configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.youtube_client_id:
            return False, "YOUTUBE_CLIENT_ID not set in .env"

        if not self.youtube_client_secret:
            return False, "YOUTUBE_CLIENT_SECRET not set in .env"

        return True, None

    def validate_tiktok(self) -> tuple[bool, Optional[str]]:
        """
        Validate TikTok configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.tiktok_client_key:
            return False, "TIKTOK_CLIENT_KEY not set in .env"

        if not self.tiktok_client_secret:
            return False, "TIKTOK_CLIENT_SECRET not set in .env"

        return True, None

    def get_youtube_credentials(self) -> dict:
        """Get YouTube OAuth credentials"""
        return {
            'client_id': self.youtube_client_id,
            'client_secret': self.youtube_client_secret,
            'redirect_uri': self.youtube_redirect_uri,
            'access_token': self.youtube_access_token,
            'refresh_token': self.youtube_refresh_token,
        }

    def get_tiktok_credentials(self) -> dict:
        """Get TikTok OAuth credentials"""
        return {
            'client_key': self.tiktok_client_key,
            'client_secret': self.tiktok_client_secret,
            'redirect_uri': self.tiktok_redirect_uri,
            'access_token': self.tiktok_access_token,
            'refresh_token': self.tiktok_refresh_token,
        }

    def __repr__(self) -> str:
        return (
            f"PublisherConfig("
            f"youtube_configured={bool(self.youtube_client_id)}, "
            f"tiktok_configured={bool(self.tiktok_client_key)}, "
            f"default_platform={self.default_platform})"
        )


# Global config instance
_config: Optional[PublisherConfig] = None


def load_config() -> PublisherConfig:
    """
    Load or return cached configuration

    Returns:
        PublisherConfig object with all settings
    """
    global _config
    if _config is None:
        _config = PublisherConfig()
    return _config


def get_config() -> PublisherConfig:
    """
    Get current configuration (load if not loaded)

    Returns:
        PublisherConfig object
    """
    return load_config()


def reload_config() -> PublisherConfig:
    """
    Force reload configuration from .env

    Returns:
        New PublisherConfig object
    """
    global _config
    _config = None
    return load_config()
