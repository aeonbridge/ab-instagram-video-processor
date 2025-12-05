#!/usr/bin/env python3
"""
CLI Tool for Video Transcription Service
Transcribe videos from URLs (YouTube, Instagram) or local video IDs
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import get_config
from video_transcriber import (
    transcribe_from_url,
    transcribe_video,
    get_available_models,
    validate_model_size,
    TranscriptionError
)
from storage_manager import get_video_path
from video_downloader import check_video_availability


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Transcribe videos from URLs or local video files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transcribe from YouTube URL
  python cli_transcriber.py --url "https://youtube.com/watch?v=VIDEO_ID"

  # Transcribe from video ID (must be downloaded)
  python cli_transcriber.py --video-id "VIDEO_ID"

  # Use different Whisper model
  python cli_transcriber.py --url "URL" --model medium

  # Specify language
  python cli_transcriber.py --url "URL" --language pt

  # Transcribe local video file
  python cli_transcriber.py --file "/path/to/video.mp4"

  # Output to specific directory
  python cli_transcriber.py --url "URL" --output-dir "./my_transcriptions"

  # Disable timestamps
  python cli_transcriber.py --url "URL" --no-timestamps

Available Whisper models (larger = more accurate but slower):
  • tiny   - Fastest, least accurate (~1GB VRAM)
  • base   - Good balance (default) (~1GB VRAM)
  • small  - Better accuracy (~2GB VRAM)
  • medium - High accuracy (~5GB VRAM)
  • large  - Best accuracy (~10GB VRAM)

Common language codes:
  pt (Portuguese), en (English), es (Spanish), fr (French), de (German),
  it (Italian), ja (Japanese), zh (Chinese), ko (Korean), etc.
  Leave empty for automatic detection.
        """
    )

    # Input source (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        '--url',
        type=str,
        help='Video URL (YouTube, Instagram, etc)'
    )
    source_group.add_argument(
        '--video-id',
        type=str,
        help='Video ID (for already downloaded videos)'
    )
    source_group.add_argument(
        '--file',
        type=str,
        help='Path to local video file'
    )

    # Transcription options
    parser.add_argument(
        '--model',
        type=str,
        default='base',
        choices=get_available_models(),
        help='Whisper model size (default: base)'
    )
    parser.add_argument(
        '--language',
        type=str,
        default=None,
        help='Language code (e.g., pt, en, es). Leave empty for auto-detection'
    )
    parser.add_argument(
        '--no-timestamps',
        action='store_true',
        help='Disable timestamps in transcription'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for transcription files (default: from config)'
    )

    # Download options (for --url)
    parser.add_argument(
        '--no-download',
        action='store_true',
        help='Do not download video if not found locally (only for --url)'
    )

    # Output format
    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'markdown', 'both'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    parser.add_argument(
        '--json-output',
        type=str,
        default=None,
        help='Save JSON output to specified file'
    )

    # Verbose
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    return parser.parse_args()


def print_banner():
    """Print CLI banner"""
    print("=" * 60)
    print("VIDEO TRANSCRIPTION CLI")
    print("Powered by OpenAI Whisper")
    print("=" * 60)
    print()


def print_result_summary(result: dict):
    """Print transcription result summary"""
    print()
    print("-" * 60)
    print("TRANSCRIPTION COMPLETE")
    print("-" * 60)
    print(f"Video: {result['video_name']}")
    print(f"Detected language: {result['detected_language']}")
    print(f"Model used: {result['model_used']}")
    print(f"Processing time: {result['processing_time']:.1f}s")

    if 'markdown_file' in result:
        print(f"Markdown saved to: {result['markdown_file']}")

    if 'segments' in result:
        print(f"Total segments: {len(result['segments'])}")

    print()
    print("Full text preview:")
    print("-" * 60)
    preview = result['full_text'][:500]
    if len(result['full_text']) > 500:
        preview += "..."
    print(preview)
    print("-" * 60)


def main():
    """Main CLI function"""
    args = parse_arguments()

    if not args.verbose:
        # Suppress info logs if not verbose
        import logging
        logging.getLogger().setLevel(logging.WARNING)

    print_banner()

    # Load configuration
    try:
        config = get_config()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nMake sure ffmpeg and yt-dlp are installed:")
        print("  • Mac: brew install ffmpeg yt-dlp")
        print("  • Linux: apt-get install ffmpeg && pip install yt-dlp")
        sys.exit(1)

    # Set output directory
    output_dir = Path(args.output_dir) if args.output_dir else config.transcriptions_path

    # Determine include_timestamps
    include_timestamps = not args.no_timestamps

    try:
        # Process based on input source
        if args.url:
            # Extract video ID from URL
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(args.url)

            # Try to extract video ID for YouTube
            video_id = None
            if 'youtube.com' in args.url or 'youtu.be' in args.url:
                if 'youtu.be' in args.url:
                    video_id = parsed.path.split('/')[-1]
                else:
                    video_id = parse_qs(parsed.query).get('v', [None])[0]

            if not video_id:
                video_id = Path(parsed.path).stem or "video"

            print(f"Video URL: {args.url}")
            print(f"Video ID: {video_id}")
            print()

            # Check availability
            print("Checking video availability...")
            is_available, msg = check_video_availability(args.url)
            if not is_available:
                print(f"Error: {msg}")
                sys.exit(1)
            print(f"✓ {msg}")
            print()

            # Transcribe from URL
            print("Starting transcription...")
            result = transcribe_from_url(
                video_url=args.url,
                video_id=video_id,
                downloads_path=config.downloads_path,
                transcriptions_path=output_dir,
                model_size=args.model,
                language=args.language,
                include_timestamps=include_timestamps,
                download_if_needed=not args.no_download
            )

        elif args.video_id:
            # Transcribe from video ID
            video_path = get_video_path(args.video_id, config.downloads_path)

            if not video_path.exists():
                print(f"Error: Video not found at: {video_path}")
                print("Use --url to download the video first")
                sys.exit(1)

            print(f"Video ID: {args.video_id}")
            print(f"Video path: {video_path}")
            print()

            print("Starting transcription...")
            result = transcribe_video(
                video_path=video_path,
                model_size=args.model,
                language=args.language,
                include_timestamps=include_timestamps,
                output_dir=output_dir
            )

        elif args.file:
            # Transcribe local file
            video_path = Path(args.file)

            if not video_path.exists():
                print(f"Error: File not found: {video_path}")
                sys.exit(1)

            print(f"Video file: {video_path}")
            print()

            print("Starting transcription...")
            result = transcribe_video(
                video_path=video_path,
                model_size=args.model,
                language=args.language,
                include_timestamps=include_timestamps,
                output_dir=output_dir
            )

        # Print result summary
        print_result_summary(result)

        # Save JSON if requested
        if args.json_output or args.format in ['json', 'both']:
            json_file = args.json_output or (output_dir / f"{Path(result['video_path']).stem}_transcription.json")
            json_file = Path(json_file)
            json_file.parent.mkdir(parents=True, exist_ok=True)

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"\nJSON saved to: {json_file}")

        print("\n✓ Transcription completed successfully!")

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except TranscriptionError as e:
        print(f"\nTranscription error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTranscription cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()