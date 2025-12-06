"""
Base Publisher Abstract Class
Defines interface for all social media publishers
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime


@dataclass
class VideoMetadata:
    """Video metadata for publishing"""
    title: str
    description: str = ""
    tags: List[str] = None
    category: Optional[str] = None
    privacy: str = "public"  # public, private, unlisted
    language: str = "en"
    thumbnail_path: Optional[Path] = None
    scheduled_time: Optional[datetime] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class UploadResult:
    """Result of video upload operation"""
    success: bool
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    upload_id: Optional[str] = None
    status: str = "pending"  # pending, processing, published, failed
    error: Optional[str] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class VideoValidation:
    """Video validation result"""
    valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    file_size: int = 0
    duration: float = 0.0
    resolution: tuple = (0, 0)
    format: str = ""
    codec: str = ""

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class BasePublisher(ABC):
    """Abstract base class for social media publishers"""

    def __init__(self, config: Dict):
        """
        Initialize publisher with configuration

        Args:
            config: Configuration dictionary with credentials and settings
        """
        self.config = config
        self._authenticated = False
        self._access_token = None
        self._refresh_token = None

    @property
    def platform_name(self) -> str:
        """Platform name (e.g., 'YouTube', 'TikTok')"""
        return self.__class__.__name__.replace('Publisher', '')

    @property
    def is_authenticated(self) -> bool:
        """Check if publisher is authenticated"""
        return self._authenticated

    # Abstract methods that must be implemented by subclasses

    @abstractmethod
    def authenticate(self, credentials: Optional[Dict] = None) -> bool:
        """
        Authenticate with OAuth 2.0

        Args:
            credentials: Optional credentials dict (client_id, client_secret, etc.)

        Returns:
            True if authentication successful
        """
        pass

    @abstractmethod
    def refresh_access_token(self) -> bool:
        """
        Refresh expired access token using refresh token

        Returns:
            True if token refreshed successfully
        """
        pass

    @abstractmethod
    def validate_video(self, video_path: Path) -> VideoValidation:
        """
        Validate video meets platform requirements

        Args:
            video_path: Path to video file

        Returns:
            VideoValidation object with validation results
        """
        pass

    @abstractmethod
    def upload_video(
        self,
        video_path: Path,
        metadata: VideoMetadata,
        progress_callback: Optional[callable] = None
    ) -> UploadResult:
        """
        Upload video to platform

        Args:
            video_path: Path to video file
            metadata: Video metadata (title, description, tags, etc.)
            progress_callback: Optional callback for upload progress (0.0 to 1.0)

        Returns:
            UploadResult object with upload results
        """
        pass

    @abstractmethod
    def get_upload_status(self, upload_id: str) -> Dict:
        """
        Check upload/processing status

        Args:
            upload_id: Upload/video identifier

        Returns:
            Status dictionary with current state
        """
        pass

    @abstractmethod
    def delete_video(self, video_id: str) -> bool:
        """
        Delete published video

        Args:
            video_id: Video identifier

        Returns:
            True if deletion successful
        """
        pass

    @abstractmethod
    def get_video_analytics(self, video_id: str, days: int = 7) -> Dict:
        """
        Get video performance metrics

        Args:
            video_id: Video identifier
            days: Number of days of analytics to retrieve

        Returns:
            Analytics dictionary with metrics
        """
        pass

    @abstractmethod
    def update_video_metadata(
        self,
        video_id: str,
        metadata: VideoMetadata
    ) -> bool:
        """
        Update video metadata after publishing

        Args:
            video_id: Video identifier
            metadata: Updated metadata

        Returns:
            True if update successful
        """
        pass

    # Optional methods with default implementations

    def set_thumbnail(self, video_id: str, thumbnail_path: Path) -> bool:
        """
        Set custom thumbnail for video

        Args:
            video_id: Video identifier
            thumbnail_path: Path to thumbnail image

        Returns:
            True if thumbnail set successfully
        """
        raise NotImplementedError(f"{self.platform_name} does not support custom thumbnails")

    def get_upload_quota(self) -> Dict:
        """
        Get remaining upload quota for the day

        Returns:
            Dictionary with quota information
        """
        return {
            "available": True,
            "remaining": "unknown",
            "reset_time": None
        }

    def _ensure_authenticated(self):
        """Raise exception if not authenticated"""
        if not self._authenticated:
            raise RuntimeError(f"Not authenticated with {self.platform_name}. Call authenticate() first.")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(authenticated={self._authenticated})"
