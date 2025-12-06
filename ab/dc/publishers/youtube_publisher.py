"""
YouTube Publisher
Implements YouTube Data API v3 for video publishing with resumable uploads
"""

import os
import requests
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlencode

try:
    from .base_publisher import (
        BasePublisher,
        VideoMetadata,
        UploadResult,
        VideoValidation
    )
    from .oauth_manager import OAuthManager
    from .utils.video_validator import VideoValidator
    from .utils.rate_limiter import YouTubeRateLimiter
    from .utils.retry_handler import RetryHandler
    from .utils.metadata_builder import MetadataBuilder
except ImportError:
    from base_publisher import (
        BasePublisher,
        VideoMetadata,
        UploadResult,
        VideoValidation
    )
    from oauth_manager import OAuthManager
    from utils.video_validator import VideoValidator
    from utils.rate_limiter import YouTubeRateLimiter
    from utils.retry_handler import RetryHandler
    from utils.metadata_builder import MetadataBuilder

logger = logging.getLogger(__name__)


class YouTubePublisher(BasePublisher):
    """YouTube video publisher using Data API v3"""

    # API endpoints
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
    VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
    THUMBNAIL_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"

    # OAuth scopes
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube',
    ]

    def __init__(self, config: Dict):
        """
        Initialize YouTube publisher

        Args:
            config: Configuration dictionary with credentials
        """
        super().__init__(config)

        # Initialize components
        self.oauth = OAuthManager(
            client_id=config.get('client_id'),
            client_secret=config.get('client_secret'),
            redirect_uri=config.get('redirect_uri', 'http://localhost:8080'),
            token_file=config.get('token_file')
        )

        self.validator = VideoValidator(
            ffprobe_path=config.get('ffprobe_path', 'ffprobe')
        )

        self.rate_limiter = YouTubeRateLimiter()
        self.retry_handler = RetryHandler(
            max_retries=config.get('max_retries', 3)
        )
        self.metadata_builder = MetadataBuilder('youtube')

        # Load existing tokens
        if self.oauth.load_tokens('youtube'):
            self._authenticated = True
            self._access_token = self.oauth.access_token

    def authenticate(self, credentials: Optional[Dict] = None) -> bool:
        """
        Authenticate with YouTube using OAuth 2.0

        Args:
            credentials: Optional credentials dict (not used, reads from config)

        Returns:
            True if authentication successful
        """
        # Check if we already have valid tokens
        if self.oauth.is_token_valid():
            self._authenticated = True
            self._access_token = self.oauth.access_token
            logger.info("Using existing valid tokens")
            return True

        # Try to refresh token if we have a refresh token
        if self.oauth.refresh_token:
            logger.info("Attempting to refresh access token...")
            if self.oauth.refresh_access_token(self.TOKEN_URL):
                self._authenticated = True
                self._access_token = self.oauth.access_token
                return True

        # Perform full OAuth flow
        logger.info("Starting OAuth authorization flow...")
        success = self.oauth.authorize(
            auth_url=self.AUTH_URL,
            token_url=self.TOKEN_URL,
            scopes=self.SCOPES
        )

        if success:
            self._authenticated = True
            self._access_token = self.oauth.access_token
            self.oauth.save_tokens('youtube')

        return success

    def refresh_access_token(self) -> bool:
        """Refresh expired access token"""
        if self.oauth.refresh_access_token(self.TOKEN_URL):
            self._access_token = self.oauth.access_token
            self.oauth.save_tokens('youtube')
            return True
        return False

    def validate_video(self, video_path: Path) -> VideoValidation:
        """
        Validate video for YouTube requirements

        Args:
            video_path: Path to video file

        Returns:
            VideoValidation object
        """
        try:
            is_valid, errors, warnings = self.validator.validate_youtube(video_path)
            info = self.validator.get_video_info(video_path)

            return VideoValidation(
                valid=is_valid,
                errors=errors,
                warnings=warnings,
                file_size=info['file_size'],
                duration=info['duration'],
                resolution=(info['video']['width'], info['video']['height']),
                format=info['format'],
                codec=info['video']['codec']
            )

        except Exception as e:
            return VideoValidation(
                valid=False,
                errors=[f"Validation failed: {str(e)}"]
            )

    def upload_video(
        self,
        video_path: Path,
        metadata: VideoMetadata,
        progress_callback: Optional[callable] = None
    ) -> UploadResult:
        """
        Upload video to YouTube using resumable upload

        Args:
            video_path: Path to video file
            metadata: Video metadata
            progress_callback: Optional callback for upload progress (0.0 to 1.0)

        Returns:
            UploadResult object
        """
        self._ensure_authenticated()

        # Validate video first
        validation = self.validate_video(video_path)
        if not validation.valid:
            return UploadResult(
                success=False,
                error=f"Video validation failed: {', '.join(validation.errors)}"
            )

        # Check rate limit and quota
        if not self.rate_limiter.acquire('video_upload'):
            return UploadResult(
                success=False,
                error="YouTube quota exceeded or rate limited"
            )

        try:
            # Build YouTube metadata
            youtube_metadata = self._build_metadata(metadata, video_path)

            # Initialize resumable upload
            logger.info(f"Initializing upload for: {video_path.name}")
            session_uri = self._initialize_resumable_upload(
                youtube_metadata,
                video_path.stat().st_size
            )

            if not session_uri:
                return UploadResult(
                    success=False,
                    error="Failed to initialize resumable upload"
                )

            # Upload video file
            logger.info("Uploading video file...")
            video_data = self._upload_video_file(
                session_uri,
                video_path,
                progress_callback
            )

            if not video_data:
                return UploadResult(
                    success=False,
                    error="Video upload failed"
                )

            video_id = video_data.get('id')
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            logger.info(f"Upload successful! Video ID: {video_id}")
            logger.info(f"Video URL: {video_url}")

            # Upload thumbnail if provided
            if metadata.thumbnail_path and metadata.thumbnail_path.exists():
                logger.info("Uploading custom thumbnail...")
                self._upload_thumbnail(video_id, metadata.thumbnail_path)

            return UploadResult(
                success=True,
                video_id=video_id,
                video_url=video_url,
                status="uploaded",
                metadata={
                    'title': metadata.title,
                    'is_short': self.validator.is_youtube_short(video_path),
                    'duration': validation.duration,
                    'resolution': f"{validation.resolution[0]}x{validation.resolution[1]}"
                }
            )

        except Exception as e:
            logger.error(f"Upload failed: {str(e)}", exc_info=True)
            return UploadResult(
                success=False,
                error=f"Upload failed: {str(e)}"
            )

    def _initialize_resumable_upload(
        self,
        metadata: Dict,
        file_size: int
    ) -> Optional[str]:
        """
        Initialize resumable upload session

        Args:
            metadata: Video metadata
            file_size: Video file size in bytes

        Returns:
            Session URI for upload or None
        """
        self._ensure_token_valid()

        url = f"{self.UPLOAD_URL}?uploadType=resumable&part=snippet,status"

        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json',
            'X-Upload-Content-Length': str(file_size),
            'X-Upload-Content-Type': 'video/*'
        }

        logger.debug(f"Using access token: {self._access_token[:50]}...")

        try:
            response = requests.post(
                url,
                headers=headers,
                json=metadata,
                timeout=30
            )
            response.raise_for_status()

            session_uri = response.headers.get('Location')
            return session_uri

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to initialize upload: {e}")
            return None

    def _upload_video_file(
        self,
        session_uri: str,
        video_path: Path,
        progress_callback: Optional[callable] = None
    ) -> Optional[Dict]:
        """
        Upload video file to session URI

        Args:
            session_uri: Resumable upload session URI
            video_path: Path to video file
            progress_callback: Optional progress callback

        Returns:
            Video data dict or None
        """
        file_size = video_path.stat().st_size
        chunk_size = self.config.get('chunk_size', 10 * 1024 * 1024)  # 10MB default

        with open(video_path, 'rb') as video_file:
            uploaded = 0

            while uploaded < file_size:
                chunk_end = min(uploaded + chunk_size, file_size)
                chunk = video_file.read(chunk_end - uploaded)

                headers = {
                    'Content-Length': str(len(chunk)),
                    'Content-Range': f'bytes {uploaded}-{chunk_end - 1}/{file_size}'
                }

                try:
                    response = requests.put(
                        session_uri,
                        headers=headers,
                        data=chunk,
                        timeout=300
                    )

                    if response.status_code in (200, 201):
                        # Upload complete
                        if progress_callback:
                            progress_callback(1.0)
                        return response.json()

                    elif response.status_code == 308:
                        # Resume incomplete
                        uploaded = chunk_end
                        if progress_callback:
                            progress_callback(uploaded / file_size)
                    else:
                        response.raise_for_status()

                except requests.exceptions.RequestException as e:
                    logger.error(f"Upload failed at byte {uploaded}: {e}")
                    return None

        return None

    def _upload_thumbnail(self, video_id: str, thumbnail_path: Path) -> bool:
        """Upload custom thumbnail"""
        self._ensure_token_valid()

        url = f"{self.THUMBNAIL_URL}?videoId={video_id}"

        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'image/jpeg'
        }

        try:
            with open(thumbnail_path, 'rb') as thumbnail:
                response = requests.post(
                    url,
                    headers=headers,
                    data=thumbnail,
                    timeout=60
                )
                response.raise_for_status()
                logger.info("Thumbnail uploaded successfully")
                return True

        except Exception as e:
            logger.error(f"Thumbnail upload failed: {e}")
            return False

    def get_upload_status(self, upload_id: str) -> Dict:
        """Get video processing status"""
        self._ensure_authenticated()
        self._ensure_token_valid()

        url = f"{self.VIDEO_URL}?part=status,processingDetails&id={upload_id}"

        headers = {
            'Authorization': f'Bearer {self._access_token}'
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                return data['items'][0]

            return {'error': 'Video not found'}

        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {'error': str(e)}

    def delete_video(self, video_id: str) -> bool:
        """Delete video from YouTube"""
        self._ensure_authenticated()
        self._ensure_token_valid()

        url = f"{self.VIDEO_URL}?id={video_id}"

        headers = {
            'Authorization': f'Bearer {self._access_token}'
        }

        try:
            response = requests.delete(url, headers=headers, timeout=30)
            response.raise_for_status()
            logger.info(f"Video {video_id} deleted")
            return True

        except Exception as e:
            logger.error(f"Failed to delete video: {e}")
            return False

    def get_video_analytics(self, video_id: str, days: int = 7) -> Dict:
        """Get video analytics (requires YouTube Analytics API)"""
        logger.warning("Analytics require YouTube Analytics API - not implemented")
        return {'error': 'Analytics API not implemented'}

    def update_video_metadata(
        self,
        video_id: str,
        metadata: VideoMetadata
    ) -> bool:
        """Update video metadata"""
        self._ensure_authenticated()
        self._ensure_token_valid()

        url = f"{self.VIDEO_URL}?part=snippet,status"

        youtube_metadata = self._build_metadata(metadata)
        youtube_metadata['id'] = video_id

        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.put(
                url,
                headers=headers,
                json=youtube_metadata,
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Video {video_id} metadata updated")
            return True

        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            return False

    def set_thumbnail(self, video_id: str, thumbnail_path: Path) -> bool:
        """Set custom thumbnail"""
        return self._upload_thumbnail(video_id, thumbnail_path)

    def _build_metadata(self, metadata: VideoMetadata, video_path: Optional[Path] = None) -> Dict:
        """Build YouTube API metadata from VideoMetadata"""
        youtube_meta = self.metadata_builder.build_youtube_metadata(
            title=metadata.title,
            description=metadata.description,
            tags=metadata.tags,
            category=metadata.category or 'entertainment',
            privacy=metadata.privacy,
            language=metadata.language,
            made_for_kids=False,
            embeddable=True,
            public_stats=True
        )

        # Detect if video is a Short
        if video_path and self.validator.is_youtube_short(video_path):
            # Add #Shorts to title if not present
            if '#shorts' not in youtube_meta['snippet']['title'].lower():
                youtube_meta['snippet']['title'] += ' #Shorts'
            logger.info("Video detected as YouTube Short")

        return youtube_meta

    def _ensure_token_valid(self):
        """Ensure access token is valid, refresh if needed"""
        if not self.oauth.is_token_valid():
            logger.info("Access token expired, refreshing...")
            if not self.refresh_access_token():
                raise RuntimeError("Failed to refresh access token")
