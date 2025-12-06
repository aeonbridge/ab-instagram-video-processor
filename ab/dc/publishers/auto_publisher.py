"""
Auto Publisher Service
Automated video publishing using metadata and thumbnails from AI agents
"""

import os
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try to load .env from project root
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    # Also try loading from publisher directory
    publisher_env = Path(__file__).parent / '.env'
    if publisher_env.exists():
        load_dotenv(publisher_env)
except ImportError:
    pass  # python-dotenv not installed, will rely on system env vars

try:
    from .youtube_publisher import YouTubePublisher
    from .base_publisher import VideoMetadata, UploadResult
except ImportError:
    from youtube_publisher import YouTubePublisher
    from base_publisher import VideoMetadata, UploadResult

logger = logging.getLogger(__name__)


class AutoPublisher:
    """
    Automated video publisher that uses AI-generated metadata and thumbnails
    """

    def __init__(
        self,
        platform: str = "youtube",
        dry_run: bool = False,
        config: Optional[Dict] = None,
        scan_only: bool = False
    ):
        """
        Initialize auto publisher

        Args:
            platform: Publishing platform (currently only 'youtube')
            dry_run: If True, don't actually publish, just validate
            config: Optional platform configuration (if None, loads from environment)
            scan_only: If True, skip publisher initialization (for scanning only)
        """
        self.platform = platform
        self.dry_run = dry_run
        self.publisher = None

        # Skip publisher initialization if scan_only mode
        if scan_only:
            logger.info(f"Initialized AutoPublisher in scan-only mode")
            return

        # Initialize platform publisher
        if platform == "youtube":
            # Build config from environment if not provided
            if config is None:
                config = self._build_youtube_config()

            self.publisher = YouTubePublisher(config)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

        logger.info(f"Initialized AutoPublisher for {platform} (dry_run={dry_run})")

    def _build_youtube_config(self) -> Dict:
        """
        Build YouTube publisher configuration from environment variables

        Returns:
            Configuration dictionary for YouTubePublisher

        Environment Variables:
            YOUTUBE_CLIENT_ID: OAuth client ID
            YOUTUBE_CLIENT_SECRET: OAuth client secret
            YOUTUBE_REDIRECT_URI: OAuth redirect URI (default: http://localhost:8080)
            YOUTUBE_TOKEN_FILE: Path to token storage file (default: .youtube_tokens.json)
        """
        # Get credentials from environment
        client_id = os.getenv('YOUTUBE_CLIENT_ID')
        client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')

        if not client_id or not client_secret:
            raise ValueError(
                "YouTube credentials not found in environment. "
                "Please set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET"
            )

        config = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': os.getenv('YOUTUBE_REDIRECT_URI', 'http://localhost:8080'),
            'token_file': Path(os.getenv('YOUTUBE_TOKEN_FILE', '.youtube_tokens.json')),
            'max_retries': 3,
            'chunk_size': 10 * 1024 * 1024  # 10MB chunks
        }

        logger.debug("Built YouTube configuration from environment")
        return config

    def find_publishable_videos(
        self,
        directory: Path,
        require_metadata: bool = True,
        require_thumbnail: bool = False
    ) -> List[Dict]:
        """
        Find all videos ready for publishing in a directory

        Args:
            directory: Directory to search
            require_metadata: Require metadata JSON file
            require_thumbnail: Require thumbnail image

        Returns:
            List of publishable video dictionaries
        """
        directory = Path(directory)
        if not directory.exists():
            raise ValueError(f"Directory not found: {directory}")

        publishable = []

        # Find all video files
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        video_files = []
        for ext in video_extensions:
            video_files.extend(directory.glob(f'*{ext}'))

        logger.info(f"Found {len(video_files)} video file(s) in {directory}")

        for video_file in video_files:
            # Look for corresponding metadata - try multiple patterns
            metadata_file = None

            # Try exact match first
            exact_match = video_file.parent / f"{video_file.stem}_metadata.json"
            if exact_match.exists():
                metadata_file = exact_match
            else:
                # Try with wildcard for language suffix (e.g., _en_metadata.json)
                metadata_pattern = video_file.parent / f"{video_file.stem}_*_metadata.json"
                matches = list(video_file.parent.glob(f"{video_file.stem}_*_metadata.json"))
                if matches:
                    metadata_file = matches[0]  # Use first match
                else:
                    # Try searching in parent directory
                    parent_exact = video_file.parent.parent / f"{video_file.stem}_metadata.json"
                    if parent_exact.exists():
                        metadata_file = parent_exact
                    else:
                        parent_matches = list(video_file.parent.parent.glob(f"{video_file.stem}_*_metadata.json"))
                        if parent_matches:
                            metadata_file = parent_matches[0]

            # Look for thumbnails - check both video directory and parent directory
            thumbnail_files = []

            def find_thumbnails_in_dir(base_dir: Path) -> List[Path]:
                """Find thumbnails matching video stem in directory"""
                found = []

                # Check for direct thumbnails
                for i in range(1, 10):
                    # Try exact match
                    thumb_file = base_dir / f"{video_file.stem}_thumbnail_{i}.png"
                    if thumb_file.exists():
                        found.append(thumb_file)
                    else:
                        # Try with wildcard (e.g., _en_thumbnail_1.png)
                        matches = list(base_dir.glob(f"{video_file.stem}_*_thumbnail_{i}.png"))
                        if matches:
                            found.append(matches[0])

                # Also check subdirectories (dalle, gemini, etc.)
                if not found and base_dir.exists():
                    for subdir in base_dir.iterdir():
                        if subdir.is_dir():
                            for i in range(1, 10):
                                # Try exact match
                                thumb_file = subdir / f"{video_file.stem}_thumbnail_{i}.png"
                                if thumb_file.exists():
                                    found.append(thumb_file)
                                else:
                                    # Try with wildcard
                                    matches = list(subdir.glob(f"{video_file.stem}_*_thumbnail_{i}.png"))
                                    if matches:
                                        found.append(matches[0])

                            # If we found thumbnails in this subdir, use them
                            if found:
                                break

                return found

            # First check thumbnails subdirectory next to video
            thumbnail_dir = video_file.parent / 'thumbnails'
            if thumbnail_dir.exists():
                thumbnail_files = find_thumbnails_in_dir(thumbnail_dir)

            # Also check parent directory's thumbnails subdirectory
            if not thumbnail_files:
                parent_thumbnail_dir = video_file.parent.parent / 'thumbnails'
                if parent_thumbnail_dir.exists():
                    thumbnail_files = find_thumbnails_in_dir(parent_thumbnail_dir)

            # Check requirements
            has_metadata = metadata_file is not None and metadata_file.exists()
            has_thumbnail = len(thumbnail_files) > 0

            if require_metadata and not has_metadata:
                logger.debug(f"Skipping {video_file.name}: no metadata")
                continue

            if require_thumbnail and not has_thumbnail:
                logger.debug(f"Skipping {video_file.name}: no thumbnail")
                continue

            # Add to publishable list
            publishable.append({
                'video_file': video_file,
                'metadata_file': metadata_file if has_metadata else None,
                'thumbnail_files': thumbnail_files,
                'has_metadata': has_metadata,
                'has_thumbnail': has_thumbnail
            })

        logger.info(f"Found {len(publishable)} publishable video(s)")
        return publishable

    def load_metadata(self, metadata_file: Path) -> Dict:
        """
        Load metadata from JSON file

        Args:
            metadata_file: Path to metadata JSON

        Returns:
            Metadata dictionary
        """
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            logger.debug(f"Loaded metadata from {metadata_file.name}")
            return metadata

        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return {}

    def metadata_to_video_metadata(
        self,
        metadata: Dict,
        video_file: Path
    ) -> VideoMetadata:
        """
        Convert AI-generated metadata to VideoMetadata object

        Args:
            metadata: Metadata dictionary from AI
            video_file: Path to video file

        Returns:
            VideoMetadata object
        """
        # Extract tags (handle both list and comma-separated string)
        tags = metadata.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]

        # Build VideoMetadata
        video_metadata = VideoMetadata(
            title=metadata.get('title', video_file.stem)[:100],  # YouTube limit
            description=metadata.get('description', '')[:5000],  # YouTube limit
            tags=tags[:500],  # YouTube limit
            category=self._category_to_name(metadata.get('category', 'Entertainment')),
            privacy=metadata.get('privacy_status', 'private'),
            language=metadata.get('language', 'en')
        )

        return video_metadata

    def _category_to_name(self, category: str) -> str:
        """
        Normalize category name for YouTube

        Args:
            category: Category name from metadata

        Returns:
            Normalized category name
        """
        # Map common category names to YouTube categories
        category_map = {
            'Tech & Gear': 'Science & Technology',
            'Technology': 'Science & Technology',
            'Tech': 'Science & Technology',
            'Games': 'Gaming',
            'Game': 'Gaming',
            'Music': 'Music',
            'Sports': 'Sports',
            'Education': 'Education',
            'Comedy': 'Comedy',
            'Entertainment': 'Entertainment',
            'News': 'News & Politics',
            'Politics': 'News & Politics',
            'How-to': 'Howto & Style',
            'Howto': 'Howto & Style',
            'Travel': 'Travel & Events',
            'Autos': 'Autos & Vehicles',
            'Vehicles': 'Autos & Vehicles',
            'Pets': 'Pets & Animals',
            'Animals': 'Pets & Animals',
            'Film': 'Film & Animation',
            'Animation': 'Film & Animation',
            'People': 'People & Blogs',
            'Blogs': 'People & Blogs',
            'Nonprofits': 'Nonprofits & Activism',
            'Activism': 'Nonprofits & Activism'
        }

        return category_map.get(category, 'Entertainment')  # Default: Entertainment

    def _transcode_video(self, video_path: Path, output_codec: str = 'h264') -> Optional[Path]:
        """
        Transcode video to a YouTube-compatible codec

        Args:
            video_path: Path to input video
            output_codec: Target codec (default: h264)

        Returns:
            Path to transcoded video or None if failed
        """
        # Create output path
        output_path = video_path.parent / f"{video_path.stem}_transcoded{video_path.suffix}"

        logger.info(f"Transcoding video to {output_codec}...")
        logger.info(f"Input: {video_path.name}")
        logger.info(f"Output: {output_path.name}")

        try:
            # Build ffmpeg command
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-c:v', 'libx264',  # H.264 codec
                '-preset', 'medium',  # Encoding speed
                '-crf', '23',  # Quality (18-28, lower = better)
                '-c:a', 'aac',  # AAC audio
                '-b:a', '192k',  # Audio bitrate
                '-movflags', '+faststart',  # Optimize for web streaming
                '-y',  # Overwrite output file
                str(output_path)
            ]

            # Run ffmpeg
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Transcoding failed: {result.stderr}")
                return None

            logger.info(f"Transcoding successful!")
            logger.info(f"Original size: {video_path.stat().st_size / 1024 / 1024:.2f} MB")
            logger.info(f"Transcoded size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

            return output_path

        except Exception as e:
            logger.error(f"Transcoding error: {e}")
            return None

    def publish_video(
        self,
        video_info: Dict,
        thumbnail_index: int = 0,
        privacy_status: Optional[str] = None
    ) -> Optional[UploadResult]:
        """
        Publish a single video with metadata and thumbnail

        Args:
            video_info: Video information dictionary from find_publishable_videos
            thumbnail_index: Which thumbnail to use (0-based)
            privacy_status: Override privacy status

        Returns:
            UploadResult or None if failed
        """
        video_file = video_info['video_file']
        metadata_file = video_info['metadata_file']
        thumbnail_files = video_info['thumbnail_files']

        logger.info(f"\n{'='*60}")
        logger.info(f"Publishing: {video_file.name}")
        logger.info(f"{'='*60}")

        # Load metadata if available
        if metadata_file:
            ai_metadata = self.load_metadata(metadata_file)
            video_metadata = self.metadata_to_video_metadata(ai_metadata, video_file)
        else:
            # Create basic metadata
            video_metadata = VideoMetadata(
                title=video_file.stem[:100],
                description=f"Uploaded via AutoPublisher at {datetime.now().isoformat()}",
                tags=[],
                category='Entertainment',
                privacy='private'
            )

        # Override privacy if specified
        if privacy_status:
            video_metadata.privacy = privacy_status

        logger.info(f"Title: {video_metadata.title}")
        logger.info(f"Category: {video_metadata.category}")
        logger.info(f"Privacy: {video_metadata.privacy}")
        logger.info(f"Tags: {len(video_metadata.tags)}")

        if self.dry_run:
            logger.info("DRY RUN - Would publish video")
            return UploadResult(
                success=True,
                video_id="DRY_RUN",
                video_url="https://dry.run/test",
                status="published"
            )

        # Ensure authenticated before publishing
        if not self.publisher._authenticated:
            logger.info("Authenticating with YouTube...")
            if not self.publisher.authenticate():
                return UploadResult(
                    success=False,
                    error="Authentication failed",
                    status="failed"
                )
            logger.info("Authentication successful!")

        # Publish video
        transcoded_file = None
        try:
            # First, try to validate the video
            validation = self.publisher.validate_video(video_file)

            # Check if video needs transcoding
            needs_transcoding = False
            if not validation.valid:
                # Check if it's a codec issue
                for error in validation.errors:
                    if 'Codec' in error and 'not supported' in error:
                        needs_transcoding = True
                        logger.warning(f"Video codec not supported, transcoding required")
                        break

            # Transcode if needed
            video_to_upload = video_file
            if needs_transcoding:
                transcoded_file = self._transcode_video(video_file)
                if not transcoded_file:
                    return UploadResult(
                        success=False,
                        error="Video transcoding failed",
                        status="failed"
                    )
                video_to_upload = transcoded_file
                logger.info(f"Using transcoded video: {transcoded_file.name}")

            # Upload the video
            result = self.publisher.upload_video(
                video_path=video_to_upload,
                metadata=video_metadata
            )

            if not result.success:
                logger.error(f"Failed to publish video: {result.error}")
                return result

            logger.info(f"Video published! ID: {result.video_id}")
            logger.info(f"URL: {result.video_url}")

            # Upload thumbnail if available
            if thumbnail_files and thumbnail_index < len(thumbnail_files):
                thumbnail_file = thumbnail_files[thumbnail_index]
                logger.info(f"Uploading thumbnail: {thumbnail_file.name}")

                try:
                    thumb_result = self.publisher.set_thumbnail(
                        video_id=result.video_id,
                        thumbnail_path=thumbnail_file
                    )

                    if thumb_result:
                        logger.info("Thumbnail uploaded successfully")
                    else:
                        logger.warning("Thumbnail upload failed")

                except Exception as e:
                    logger.error(f"Thumbnail upload error: {e}")

            # Cleanup transcoded file if it was created
            if transcoded_file and transcoded_file.exists():
                logger.info(f"Cleaning up transcoded file: {transcoded_file.name}")
                transcoded_file.unlink()

            return result

        except Exception as e:
            logger.error(f"Publishing error: {e}")
            # Cleanup transcoded file on error
            if transcoded_file and transcoded_file.exists():
                transcoded_file.unlink()
            return UploadResult(
                success=False,
                video_id=None,
                error=str(e),
                status="failed"
            )

    def publish_batch(
        self,
        directory: Path,
        require_metadata: bool = True,
        require_thumbnail: bool = False,
        thumbnail_index: int = 0,
        privacy_status: Optional[str] = None,
        max_videos: Optional[int] = None
    ) -> List[UploadResult]:
        """
        Publish all videos in a directory

        Args:
            directory: Directory with videos
            require_metadata: Only publish videos with metadata
            require_thumbnail: Only publish videos with thumbnails
            thumbnail_index: Which thumbnail to use
            privacy_status: Privacy status for all videos
            max_videos: Maximum number of videos to publish

        Returns:
            List of UploadResults
        """
        # Find publishable videos
        publishable = self.find_publishable_videos(
            directory=directory,
            require_metadata=require_metadata,
            require_thumbnail=require_thumbnail
        )

        if not publishable:
            logger.warning("No publishable videos found")
            return []

        # Limit if specified
        if max_videos:
            publishable = publishable[:max_videos]
            logger.info(f"Publishing first {max_videos} video(s)")

        # Publish each video
        results = []
        for i, video_info in enumerate(publishable, 1):
            logger.info(f"\n--- Video {i}/{len(publishable)} ---")

            result = self.publish_video(
                video_info=video_info,
                thumbnail_index=thumbnail_index,
                privacy_status=privacy_status
            )

            results.append(result)

        # Summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        logger.info(f"\n{'='*60}")
        logger.info(f"BATCH PUBLISHING COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total: {len(results)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"{'='*60}")

        return results


def main():
    """Example usage"""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    if len(sys.argv) < 2:
        print("Usage: python auto_publisher.py <video_directory>")
        return 1

    directory = Path(sys.argv[1])

    # Create publisher
    publisher = AutoPublisher(
        platform='youtube',
        dry_run=False  # Set to False for actual publishing
    )

    # Find publishable videos
    videos = publisher.find_publishable_videos(
        directory=directory,
        require_metadata=True,
        require_thumbnail=False
    )

    print(f"\nFound {len(videos)} publishable video(s):")
    for video in videos:
        print(f"  - {video['video_file'].name}")
        print(f"    Metadata: {'✓' if video['has_metadata'] else '✗'}")
        print(f"    Thumbnails: {len(video['thumbnail_files'])}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
