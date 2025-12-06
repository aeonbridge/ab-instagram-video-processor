#!/usr/bin/env python3
"""
CLI Publisher
Command-line interface for publishing videos to YouTube and other platforms
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional, List

from publisher_config import get_config
from youtube_publisher import YouTubePublisher
from base_publisher import VideoMetadata


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def publish_to_youtube(args):
    """Publish video to YouTube"""
    config = get_config()

    # Validate YouTube configuration
    is_valid, error = config.validate_youtube()
    if not is_valid:
        logger.error(f"YouTube configuration invalid: {error}")
        logger.info("\nPlease set up YouTube credentials in .env file:")
        logger.info("  YOUTUBE_CLIENT_ID=your_client_id")
        logger.info("  YOUTUBE_CLIENT_SECRET=your_client_secret")
        logger.info("\nSee YOUTUBE_SETUP.md for detailed instructions.")
        return 1

    # Initialize publisher
    publisher = YouTubePublisher({
        'client_id': config.youtube_client_id,
        'client_secret': config.youtube_client_secret,
        'redirect_uri': config.youtube_redirect_uri,
        'token_file': config.token_storage_path,
        'ffprobe_path': config.ffprobe_path,
        'max_retries': config.max_retries,
        'chunk_size': config.upload_chunk_size,
    })

    # Authenticate
    logger.info("Authenticating with YouTube...")
    if not publisher.authenticate():
        logger.error("Authentication failed")
        return 1

    logger.info("Authentication successful!")

    # Prepare video path
    video_path = Path(args.video)
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return 1

    # Validate video
    logger.info(f"Validating video: {video_path.name}")
    validation = publisher.validate_video(video_path)

    if not validation.valid:
        logger.error("Video validation failed:")
        for error in validation.errors:
            logger.error(f"  - {error}")
        return 1

    if validation.warnings:
        logger.warning("Video validation warnings:")
        for warning in validation.warnings:
            logger.warning(f"  - {warning}")

    logger.info(f"Video info:")
    logger.info(f"  Duration: {validation.duration:.1f}s")
    logger.info(f"  Resolution: {validation.resolution[0]}x{validation.resolution[1]}")
    logger.info(f"  Format: {validation.format}")
    logger.info(f"  Codec: {validation.codec}")
    logger.info(f"  Size: {validation.file_size / (1024**2):.1f} MB")

    # Prepare metadata
    tags = args.tags.split(',') if args.tags else []

    metadata = VideoMetadata(
        title=args.title,
        description=args.description or "",
        tags=tags,
        category=args.category,
        privacy=args.privacy,
        language=args.language,
        thumbnail_path=Path(args.thumbnail) if args.thumbnail else None
    )

    # Upload video
    logger.info(f"\nUploading video to YouTube...")
    logger.info(f"Title: {metadata.title}")
    logger.info(f"Privacy: {metadata.privacy}")

    def progress_callback(progress: float):
        """Display upload progress"""
        percent = progress * 100
        bar_length = 40
        filled = int(bar_length * progress)
        bar = '=' * filled + '-' * (bar_length - filled)
        print(f"\rUpload Progress: [{bar}] {percent:.1f}%", end='', flush=True)

    result = publisher.upload_video(
        video_path=video_path,
        metadata=metadata,
        progress_callback=progress_callback if not args.no_progress else None
    )

    print()  # New line after progress bar

    if result.success:
        logger.info("\n" + "="*70)
        logger.info("UPLOAD SUCCESSFUL!")
        logger.info("="*70)
        logger.info(f"Video ID: {result.video_id}")
        logger.info(f"Video URL: {result.video_url}")
        logger.info(f"Status: {result.status}")

        if result.metadata.get('is_short'):
            logger.info("\nThis video qualifies as a YouTube Short!")

        logger.info("\nNote: Video processing may take a few minutes.")
        logger.info("Check the video status on YouTube Studio.")
        logger.info("="*70)
        return 0
    else:
        logger.error(f"\nUpload failed: {result.error}")
        return 1


def authenticate_youtube(args):
    """Authenticate with YouTube"""
    config = get_config()

    is_valid, error = config.validate_youtube()
    if not is_valid:
        logger.error(f"Configuration invalid: {error}")
        return 1

    publisher = YouTubePublisher({
        'client_id': config.youtube_client_id,
        'client_secret': config.youtube_client_secret,
        'redirect_uri': config.youtube_redirect_uri,
        'token_file': config.token_storage_path,
    })

    logger.info("Starting YouTube authentication...")
    if publisher.authenticate():
        logger.info("Authentication successful!")
        logger.info(f"Tokens saved to: {config.token_storage_path}")
        return 0
    else:
        logger.error("Authentication failed")
        return 1


def check_status(args):
    """Check video upload status"""
    config = get_config()

    publisher = YouTubePublisher({
        'client_id': config.youtube_client_id,
        'client_secret': config.youtube_client_secret,
        'token_file': config.token_storage_path,
    })

    if not publisher.authenticate():
        logger.error("Authentication failed")
        return 1

    status = publisher.get_upload_status(args.video_id)

    if 'error' in status:
        logger.error(f"Error: {status['error']}")
        return 1

    logger.info("\nVideo Status:")
    logger.info(f"  Upload Status: {status.get('status', {}).get('uploadStatus', 'unknown')}")
    logger.info(f"  Privacy Status: {status.get('status', {}).get('privacyStatus', 'unknown')}")
    logger.info(f"  Embeddable: {status.get('status', {}).get('embeddable', 'unknown')}")

    if 'processingDetails' in status:
        processing = status['processingDetails']
        logger.info(f"  Processing Status: {processing.get('processingStatus', 'unknown')}")

    return 0


def delete_video(args):
    """Delete video from YouTube"""
    config = get_config()

    publisher = YouTubePublisher({
        'client_id': config.youtube_client_id,
        'client_secret': config.youtube_client_secret,
        'token_file': config.token_storage_path,
    })

    if not publisher.authenticate():
        logger.error("Authentication failed")
        return 1

    if not args.confirm:
        response = input(f"Are you sure you want to delete video {args.video_id}? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Deletion cancelled")
            return 0

    if publisher.delete_video(args.video_id):
        logger.info(f"Video {args.video_id} deleted successfully")
        return 0
    else:
        logger.error("Deletion failed")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Publish videos to YouTube and other platforms',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Authenticate with YouTube
  python cli_publisher.py auth

  # Publish video to YouTube
  python cli_publisher.py upload my_video.mp4 \\
    --title "My Amazing Video" \\
    --description "Check out this cool video!" \\
    --tags "gaming,tutorial,youtube" \\
    --category gaming \\
    --privacy public

  # Check video status
  python cli_publisher.py status VIDEO_ID

  # Delete video
  python cli_publisher.py delete VIDEO_ID
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Auth command
    auth_parser = subparsers.add_parser('auth', help='Authenticate with YouTube')
    auth_parser.set_defaults(func=authenticate_youtube)

    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload video to YouTube')
    upload_parser.add_argument('video', help='Path to video file')
    upload_parser.add_argument('--title', required=True, help='Video title')
    upload_parser.add_argument('--description', default='', help='Video description')
    upload_parser.add_argument('--tags', help='Comma-separated tags')
    upload_parser.add_argument('--category', default='entertainment',
                              help='Video category (default: entertainment)')
    upload_parser.add_argument('--privacy', choices=['public', 'private', 'unlisted'],
                              default='public', help='Privacy status')
    upload_parser.add_argument('--language', default='en', help='Video language code')
    upload_parser.add_argument('--thumbnail', help='Path to custom thumbnail image')
    upload_parser.add_argument('--no-progress', action='store_true',
                              help='Disable progress bar')
    upload_parser.set_defaults(func=publish_to_youtube)

    # Status command
    status_parser = subparsers.add_parser('status', help='Check video status')
    status_parser.add_argument('video_id', help='YouTube video ID')
    status_parser.set_defaults(func=check_status)

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete video')
    delete_parser.add_argument('video_id', help='YouTube video ID')
    delete_parser.add_argument('--confirm', action='store_true',
                              help='Skip confirmation prompt')
    delete_parser.set_defaults(func=delete_video)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
