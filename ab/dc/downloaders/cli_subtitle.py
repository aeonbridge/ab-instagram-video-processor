#!/usr/bin/env python3
"""
CLI tool for downloading YouTube subtitles
"""

import sys
import argparse
import logging
from pathlib import Path

from subtitle_downloader import (
    list_available_subtitles,
    download_subtitle,
    download_all_subtitles,
    export_subtitle_to_text,
    export_subtitle_to_markdown,
    get_subtitle_metadata,
    SubtitleDownloadError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def extract_video_id(url_or_id: str) -> str:
    """
    Extract video ID from URL or return as-is if already an ID

    Args:
        url_or_id: YouTube URL or video ID

    Returns:
        Video ID
    """
    # If it's already an 11-character ID, return it
    if len(url_or_id) == 11 and url_or_id.replace('-', '').replace('_', '').isalnum():
        return url_or_id

    # Extract from URL
    if 'youtube.com/watch?v=' in url_or_id:
        return url_or_id.split('watch?v=')[1].split('&')[0]
    elif 'youtu.be/' in url_or_id:
        return url_or_id.split('youtu.be/')[1].split('?')[0]

    # Assume it's an ID
    return url_or_id


def list_command(args):
    """List available subtitles for a video"""
    try:
        video_id = extract_video_id(args.url)
        logger.info(f"Listing subtitles for video: {video_id}")

        subtitles = list_available_subtitles(video_id)

        print("\n" + "="*60)
        print("AVAILABLE SUBTITLES")
        print("="*60)

        if subtitles['manual']:
            print("\nManual Subtitles:")
            for sub in subtitles['manual']:
                print(f"  - {sub['lang']:5s} {sub['name']}")

        if subtitles['auto']:
            print("\nAuto-generated Subtitles:")
            for sub in subtitles['auto']:
                print(f"  - {sub['lang']:5s} {sub['name']}")

        if not subtitles['manual'] and not subtitles['auto']:
            print("\nNo subtitles available for this video.")

        print("="*60 + "\n")

    except SubtitleDownloadError as e:
        logger.error(f"Failed to list subtitles: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


def download_command(args):
    """Download subtitle(s) for a video"""
    try:
        video_id = extract_video_id(args.url)
        output_dir = Path(args.output_dir)

        logger.info(f"Downloading subtitles for video: {video_id}")

        if args.all_languages:
            # Download all available subtitles
            logger.info("Downloading all available subtitles...")

            downloaded = download_all_subtitles(
                video_url=video_id,
                video_id=video_id,
                subtitles_path=output_dir,
                format=args.format,
                auto_generated=not args.no_auto,
                timeout=args.timeout
            )

            print(f"\nDownloaded {len(downloaded)} subtitle(s):")
            for lang, path in downloaded.items():
                print(f"  - {lang}: {path}")

        else:
            # Download specific language
            language = args.language

            subtitle_path = download_subtitle(
                video_url=video_id,
                video_id=video_id,
                language=language,
                subtitles_path=output_dir,
                format=args.format,
                auto_generated=not args.no_auto,
                timeout=args.timeout
            )

            print(f"\nSubtitle downloaded: {subtitle_path}")

            # Export to text if requested
            if args.export_text:
                text_path = export_subtitle_to_text(
                    subtitle_path,
                    include_timestamps=args.timestamps
                )
                print(f"Text export: {text_path}")

            # Export to markdown if requested
            if args.export_markdown:
                markdown_path = export_subtitle_to_markdown(
                    video_id=video_id,
                    subtitle_path=subtitle_path,
                    language=language
                )
                print(f"Markdown export: {markdown_path}")

            # Show metadata
            if args.show_metadata:
                metadata = get_subtitle_metadata(subtitle_path)
                print("\nMetadata:")
                print(f"  - File size: {metadata['file_size_kb']} KB")
                print(f"  - Segments: {metadata['segment_count']}")
                print(f"  - Duration: {metadata['duration_formatted']}")
                print(f"  - Language: {metadata['language']}")

    except SubtitleDownloadError as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Download YouTube subtitles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available subtitles
  python cli_subtitle.py list "https://www.youtube.com/watch?v=VIDEO_ID"

  # Download English subtitle
  python cli_subtitle.py download "VIDEO_ID" -l en

  # Download Portuguese subtitle with text export
  python cli_subtitle.py download "VIDEO_ID" -l pt --export-text

  # Download all available subtitles
  python cli_subtitle.py download "VIDEO_ID" --all

  # Download subtitle in SRT format
  python cli_subtitle.py download "VIDEO_ID" -l en -f srt

  # Download with markdown export and metadata
  python cli_subtitle.py download "VIDEO_ID" -l en --export-markdown --metadata
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List command
    list_parser = subparsers.add_parser('list', help='List available subtitles')
    list_parser.add_argument('url', help='YouTube URL or video ID')
    list_parser.set_defaults(func=list_command)

    # Download command
    download_parser = subparsers.add_parser('download', help='Download subtitle(s)')
    download_parser.add_argument('url', help='YouTube URL or video ID')
    download_parser.add_argument(
        '-l', '--language',
        default='en',
        help='Subtitle language code (default: en)'
    )
    download_parser.add_argument(
        '-o', '--output-dir',
        default='./subtitles',
        help='Output directory (default: ./subtitles)'
    )
    download_parser.add_argument(
        '-f', '--format',
        choices=['vtt', 'srt'],
        default='vtt',
        help='Subtitle format (default: vtt)'
    )
    download_parser.add_argument(
        '--all', '--all-languages',
        dest='all_languages',
        action='store_true',
        help='Download all available subtitles'
    )
    download_parser.add_argument(
        '--no-auto',
        action='store_true',
        help='Disable auto-generated subtitles (manual only)'
    )
    download_parser.add_argument(
        '--export-text',
        action='store_true',
        help='Export subtitle to plain text file'
    )
    download_parser.add_argument(
        '--export-markdown',
        action='store_true',
        help='Export subtitle to markdown file'
    )
    download_parser.add_argument(
        '--timestamps',
        action='store_true',
        help='Include timestamps in text export'
    )
    download_parser.add_argument(
        '--metadata',
        dest='show_metadata',
        action='store_true',
        help='Show subtitle metadata after download'
    )
    download_parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Download timeout in seconds (default: 60)'
    )
    download_parser.set_defaults(func=download_command)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    args.func(args)


if __name__ == '__main__':
    main()