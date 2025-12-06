#!/usr/bin/env python3
"""
Example Usage of YouTube Publisher
Demonstrates how to use the YouTube publisher programmatically
"""

from pathlib import Path
from youtube_publisher import YouTubePublisher
from base_publisher import VideoMetadata
from publisher_config import get_config
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_simple_upload():
    """Simple video upload example"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Simple Video Upload")
    print("="*70)

    # Load configuration
    config = get_config()

    # Initialize publisher
    publisher = YouTubePublisher({
        'client_id': config.youtube_client_id,
        'client_secret': config.youtube_client_secret,
        'redirect_uri': config.youtube_redirect_uri,
        'token_file': config.token_storage_path,
        'ffprobe_path': config.ffprobe_path,
    })

    # Authenticate
    logger.info("Authenticating...")
    if not publisher.authenticate():
        logger.error("Authentication failed")
        return

    # Prepare metadata
    metadata = VideoMetadata(
        title="Test Upload - Simple Example",
        description="This is a test upload using the YouTube publisher",
        tags=["test", "youtube", "api"],
        privacy="private"  # Use private for testing
    )

    # Upload video
    video_path = Path("test_video.mp4")  # Replace with your video
    if not video_path.exists():
        logger.error(f"Video not found: {video_path}")
        logger.info("Please create a test_video.mp4 or update the path")
        return

    logger.info(f"Uploading: {video_path}")
    result = publisher.upload_video(
        video_path=video_path,
        metadata=metadata
    )

    if result.success:
        logger.info("Upload successful!")
        logger.info(f"Video ID: {result.video_id}")
        logger.info(f"Video URL: {result.video_url}")
    else:
        logger.error(f"Upload failed: {result.error}")


def example_upload_with_progress():
    """Upload with progress tracking"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Upload with Progress Bar")
    print("="*70)

    config = get_config()
    publisher = YouTubePublisher(config.get_youtube_credentials())

    if not publisher.authenticate():
        logger.error("Authentication failed")
        return

    metadata = VideoMetadata(
        title="Test Upload - With Progress",
        description="Upload with progress tracking",
        tags=["test", "progress"],
        privacy="private"
    )

    # Progress callback
    def progress_callback(progress: float):
        percent = progress * 100
        bar_length = 50
        filled = int(bar_length * progress)
        bar = '=' * filled + '-' * (bar_length - filled)
        print(f"\rProgress: [{bar}] {percent:.1f}%", end='', flush=True)

    video_path = Path("test_video.mp4")
    if not video_path.exists():
        logger.info("Skipping: test_video.mp4 not found")
        return

    result = publisher.upload_video(
        video_path=video_path,
        metadata=metadata,
        progress_callback=progress_callback
    )

    print()  # New line after progress bar

    if result.success:
        logger.info(f"Uploaded: {result.video_url}")


def example_upload_youtube_short():
    """Upload YouTube Short"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Upload YouTube Short")
    print("="*70)

    config = get_config()
    publisher = YouTubePublisher(config.get_youtube_credentials())

    if not publisher.authenticate():
        return

    # YouTube Shorts metadata
    metadata = VideoMetadata(
        title="Epic Moment #Shorts",
        description="Quick gaming clip\n\n#shorts #gaming #viral",
        tags=["shorts", "gaming", "viral", "epic"],
        privacy="private",
        category="gaming"
    )

    # Short video (< 60s, vertical)
    short_path = Path("short_clip.mp4")
    if not short_path.exists():
        logger.info("Skipping: short_clip.mp4 not found")
        logger.info("Create a <60s vertical video for testing Shorts")
        return

    # Validate if it's a Short
    is_short = publisher.validator.is_youtube_short(short_path)
    logger.info(f"Is YouTube Short: {is_short}")

    result = publisher.upload_video(
        video_path=short_path,
        metadata=metadata
    )

    if result.success:
        logger.info(f"Short uploaded: {result.video_url}")
        if result.metadata.get('is_short'):
            logger.info("Confirmed as YouTube Short!")


def example_upload_with_thumbnail():
    """Upload with custom thumbnail"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Upload with Custom Thumbnail")
    print("="*70)

    config = get_config()
    publisher = YouTubePublisher(config.get_youtube_credentials())

    if not publisher.authenticate():
        return

    metadata = VideoMetadata(
        title="Video with Custom Thumbnail",
        description="This video has a custom thumbnail",
        tags=["thumbnail", "custom"],
        privacy="private",
        thumbnail_path=Path("custom_thumbnail.jpg")
    )

    video_path = Path("test_video.mp4")
    if not video_path.exists():
        logger.info("Skipping: test_video.mp4 not found")
        return

    if not metadata.thumbnail_path.exists():
        logger.warning("Thumbnail not found, uploading without it")
        metadata.thumbnail_path = None

    result = publisher.upload_video(
        video_path=video_path,
        metadata=metadata
    )

    if result.success:
        logger.info(f"Uploaded with thumbnail: {result.video_url}")


def example_batch_upload():
    """Batch upload multiple videos"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Batch Upload Multiple Videos")
    print("="*70)

    config = get_config()
    publisher = YouTubePublisher(config.get_youtube_credentials())

    if not publisher.authenticate():
        return

    # Directory with videos to upload
    video_dir = Path("processed_videos")
    if not video_dir.exists():
        logger.info("Skipping: processed_videos/ directory not found")
        return

    videos = list(video_dir.glob("*.mp4"))
    if not videos:
        logger.info("No videos found in processed_videos/")
        return

    logger.info(f"Found {len(videos)} videos to upload")

    for i, video_path in enumerate(videos[:3], 1):  # Limit to 3 for example
        logger.info(f"\nUploading {i}/{min(3, len(videos))}: {video_path.name}")

        metadata = VideoMetadata(
            title=f"Batch Upload - {video_path.stem}",
            description=f"Automatically uploaded from batch process",
            tags=["batch", "automated"],
            privacy="private"
        )

        result = publisher.upload_video(
            video_path=video_path,
            metadata=metadata
        )

        if result.success:
            logger.info(f"✓ Uploaded: {result.video_url}")
        else:
            logger.error(f"✗ Failed: {result.error}")


def example_check_status():
    """Check video status"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Check Video Status")
    print("="*70)

    config = get_config()
    publisher = YouTubePublisher(config.get_youtube_credentials())

    if not publisher.authenticate():
        return

    # Replace with actual video ID
    video_id = "dQw4w9WgXcQ"  # Example ID
    logger.info(f"Checking status for: {video_id}")

    status = publisher.get_upload_status(video_id)

    if 'error' in status:
        logger.error(f"Error: {status['error']}")
    else:
        logger.info("Video Status:")
        logger.info(f"  Upload Status: {status.get('status', {}).get('uploadStatus')}")
        logger.info(f"  Privacy: {status.get('status', {}).get('privacyStatus')}")
        logger.info(f"  Embeddable: {status.get('status', {}).get('embeddable')}")


def example_validate_video():
    """Validate video before upload"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Validate Video Before Upload")
    print("="*70)

    config = get_config()
    publisher = YouTubePublisher(config.get_youtube_credentials())

    video_path = Path("test_video.mp4")
    if not video_path.exists():
        logger.info("Skipping: test_video.mp4 not found")
        return

    logger.info(f"Validating: {video_path}")
    validation = publisher.validate_video(video_path)

    logger.info(f"\nValidation Result: {'✓ VALID' if validation.valid else '✗ INVALID'}")
    logger.info(f"Duration: {validation.duration:.1f}s")
    logger.info(f"Resolution: {validation.resolution[0]}x{validation.resolution[1]}")
    logger.info(f"Format: {validation.format}")
    logger.info(f"Codec: {validation.codec}")
    logger.info(f"Size: {validation.file_size / (1024**2):.1f} MB")

    if validation.errors:
        logger.error("\nErrors:")
        for error in validation.errors:
            logger.error(f"  - {error}")

    if validation.warnings:
        logger.warning("\nWarnings:")
        for warning in validation.warnings:
            logger.warning(f"  - {warning}")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("YOUTUBE PUBLISHER - USAGE EXAMPLES")
    print("="*70)
    print("\nThese examples demonstrate various features of the YouTube publisher.")
    print("Make sure you have:")
    print("  1. Configured YouTube credentials in .env")
    print("  2. Run 'python cli_publisher.py auth' first")
    print("  3. Have test video files ready")
    print("\n" + "="*70)

    # Run examples
    try:
        # Example 1: Simple upload
        # example_simple_upload()

        # Example 2: Upload with progress
        # example_upload_with_progress()

        # Example 3: YouTube Short
        # example_upload_youtube_short()

        # Example 4: Custom thumbnail
        # example_upload_with_thumbnail()

        # Example 5: Batch upload
        # example_batch_upload()

        # Example 6: Check status
        # example_check_status()

        # Example 7: Validate video
        example_validate_video()

        print("\n" + "="*70)
        print("Examples completed!")
        print("="*70)
        print("\nUncomment the examples you want to run in main()")

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)


if __name__ == '__main__':
    main()
