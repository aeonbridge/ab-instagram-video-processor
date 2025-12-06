#!/usr/bin/env python3
"""
CLI for Auto Publisher
Automated video publishing with AI-generated metadata and thumbnails
"""

import argparse
import sys
import logging
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try to load .env from project root
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    # Also try loading from publisher directory
    publisher_env = Path(__file__).parent / '.env'
    if publisher_env.exists():
        load_dotenv(publisher_env)
except ImportError:
    pass  # python-dotenv not installed, will rely on system env vars

try:
    from auto_publisher import AutoPublisher
except ImportError:
    from .auto_publisher import AutoPublisher

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def scan_command(args):
    """Scan directory for publishable videos"""
    directory = Path(args.directory)

    publisher = AutoPublisher(
        platform=args.platform,
        scan_only=True
    )

    videos = publisher.find_publishable_videos(
        directory=directory,
        require_metadata=args.require_metadata,
        require_thumbnail=args.require_thumbnail
    )

    if not videos:
        print("\nNo publishable videos found.")
        return 1

    print(f"\n{'='*70}")
    print(f"PUBLISHABLE VIDEOS IN: {directory}")
    print(f"{'='*70}")

    for i, video in enumerate(videos, 1):
        print(f"\n{i}. {video['video_file'].name}")
        print(f"   Location: {video['video_file'].parent}")

        if video['metadata_file']:
            metadata = publisher.load_metadata(video['metadata_file'])
            print(f"   Metadata: ✓")
            print(f"   Title: {metadata.get('title', 'N/A')}")
            print(f"   Category: {metadata.get('category', 'N/A')}")
            print(f"   Tags: {len(metadata.get('tags', []))}")
        else:
            print(f"   Metadata: ✗")

        print(f"   Thumbnails: {len(video['thumbnail_files'])}")
        if video['thumbnail_files']:
            for j, thumb in enumerate(video['thumbnail_files'][:3], 1):
                print(f"     {j}. {thumb.name}")

    print(f"\n{'='*70}")
    print(f"Total: {len(videos)} video(s)")
    print(f"{'='*70}")

    return 0


def publish_command(args):
    """Publish single video"""
    video_file = Path(args.video)

    if not video_file.exists():
        logger.error(f"Video file not found: {video_file}")
        return 1

    publisher = AutoPublisher(
        platform=args.platform,
        dry_run=args.dry_run
    )

    # Find the video
    videos = publisher.find_publishable_videos(
        directory=video_file.parent,
        require_metadata=False,
        require_thumbnail=False
    )

    # Find matching video
    video_info = None
    for v in videos:
        if v['video_file'] == video_file:
            video_info = v
            break

    if not video_info:
        logger.error(f"Could not find video: {video_file}")
        return 1

    # Publish
    result = publisher.publish_video(
        video_info=video_info,
        thumbnail_index=args.thumbnail_index,
        privacy_status=args.privacy
    )

    if result and result.success:
        print(f"\n{'='*70}")
        print("VIDEO PUBLISHED SUCCESSFULLY!")
        print(f"{'='*70}")
        print(f"Video ID: {result.video_id}")
        print(f"URL: {result.video_url}")
        print(f"Status: {result.status}")
        print(f"{'='*70}")
        return 0
    else:
        logger.error("Publishing failed")
        if result:
            logger.error(f"Error: {result.error}")
        return 1


def batch_command(args):
    """Publish batch of videos"""
    directory = Path(args.directory)

    publisher = AutoPublisher(
        platform=args.platform,
        dry_run=args.dry_run
    )

    results = publisher.publish_batch(
        directory=directory,
        require_metadata=args.require_metadata,
        require_thumbnail=args.require_thumbnail,
        thumbnail_index=args.thumbnail_index,
        privacy_status=args.privacy,
        max_videos=args.max_videos
    )

    if not results:
        logger.warning("No videos published")
        return 1

    # Show results
    print(f"\n{'='*70}")
    print("PUBLISHING RESULTS")
    print(f"{'='*70}")

    for i, result in enumerate(results, 1):
        status = "✓" if result.success else "✗"
        print(f"{i}. {status} Video ID: {result.video_id or 'Failed'}")
        if result.video_url:
            print(f"   URL: {result.video_url}")
        if result.error:
            print(f"   Error: {result.error}")

    successful = sum(1 for r in results if r.success)
    print(f"\n{'='*70}")
    print(f"Success Rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
    print(f"{'='*70}")

    return 0 if successful > 0 else 1


def main():
    parser = argparse.ArgumentParser(
        description="Automated video publishing with AI-generated metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan directory for publishable videos
  %(prog)s scan processed_videos/VIDEO_ID/

  # Publish single video (dry run)
  %(prog)s publish video.mp4 --dry-run

  # Publish single video to YouTube
  %(prog)s publish video.mp4 --privacy private

  # Batch publish all videos with metadata
  %(prog)s batch processed_videos/VIDEO_ID/ --require-metadata

  # Batch publish first 5 videos as private
  %(prog)s batch processed_videos/VIDEO_ID/ --max-videos 5 --privacy private

  # Use second thumbnail for all videos
  %(prog)s batch processed_videos/VIDEO_ID/ --thumbnail-index 1

Workflow:
  1. Generate metadata:
     python ab/dc/publishers/agents/cli_metadata_agent.py batch processed_videos/VIDEO_ID/

  2. Generate thumbnails:
     python ab/dc/publishers/agents/cli_thumbnail.py from-metadata processed_videos/VIDEO_ID/

  3. Scan for publishable videos:
     %(prog)s scan processed_videos/VIDEO_ID/

  4. Publish videos:
     %(prog)s batch processed_videos/VIDEO_ID/ --privacy private
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Scan command
    scan_parser = subparsers.add_parser(
        'scan',
        help='Scan directory for publishable videos'
    )
    scan_parser.add_argument(
        'directory',
        type=Path,
        help='Directory to scan'
    )
    scan_parser.add_argument(
        '--platform',
        default='youtube',
        choices=['youtube'],
        help='Publishing platform (default: youtube)'
    )
    scan_parser.add_argument(
        '--require-metadata',
        action='store_true',
        help='Only show videos with metadata'
    )
    scan_parser.add_argument(
        '--require-thumbnail',
        action='store_true',
        help='Only show videos with thumbnails'
    )
    scan_parser.set_defaults(func=scan_command)

    # Publish command
    publish_parser = subparsers.add_parser(
        'publish',
        help='Publish single video'
    )
    publish_parser.add_argument(
        'video',
        type=Path,
        help='Video file to publish'
    )
    publish_parser.add_argument(
        '--platform',
        default='youtube',
        choices=['youtube'],
        help='Publishing platform (default: youtube)'
    )
    publish_parser.add_argument(
        '--privacy',
        choices=['public', 'private', 'unlisted'],
        help='Privacy status (overrides metadata)'
    )
    publish_parser.add_argument(
        '--thumbnail-index',
        type=int,
        default=0,
        help='Thumbnail index to use (default: 0 = first)'
    )
    publish_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run - don\'t actually publish'
    )
    publish_parser.set_defaults(func=publish_command)

    # Batch command
    batch_parser = subparsers.add_parser(
        'batch',
        help='Publish multiple videos'
    )
    batch_parser.add_argument(
        'directory',
        type=Path,
        help='Directory with videos'
    )
    batch_parser.add_argument(
        '--platform',
        default='youtube',
        choices=['youtube'],
        help='Publishing platform (default: youtube)'
    )
    batch_parser.add_argument(
        '--require-metadata',
        action='store_true',
        help='Only publish videos with metadata'
    )
    batch_parser.add_argument(
        '--require-thumbnail',
        action='store_true',
        help='Only publish videos with thumbnails'
    )
    batch_parser.add_argument(
        '--privacy',
        choices=['public', 'private', 'unlisted'],
        default='private',
        help='Privacy status for all videos (default: private)'
    )
    batch_parser.add_argument(
        '--thumbnail-index',
        type=int,
        default=0,
        help='Thumbnail index to use (default: 0 = first)'
    )
    batch_parser.add_argument(
        '--max-videos',
        type=int,
        help='Maximum number of videos to publish'
    )
    batch_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run - don\'t actually publish'
    )
    batch_parser.set_defaults(func=batch_command)

    # Parse args
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Run command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
