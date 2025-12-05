#!/usr/bin/env python3
"""
Command-line interface for Video Clipper Service
Allows creating clips from moments JSON or by extracting moments from video URL
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directories to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent / 'analysers'))

from video_clipper_service import process_video_moments


def load_moments_from_file(file_path: str) -> dict:
    """Load moments data from JSON file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file: {e}", file=sys.stderr)
        sys.exit(1)


def load_moments_from_stdin() -> dict:
    """Load moments data from stdin (pipe)"""
    try:
        data = json.load(sys.stdin)
        return data
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON from stdin: {e}", file=sys.stderr)
        sys.exit(1)


def extract_and_create_clips(video_url_or_id: str, **kwargs) -> dict:
    """Extract moments from video and create clips"""
    try:
        from replay_heatmap import get_popular_moments

        print(f"Extracting popular moments from: {video_url_or_id}", file=sys.stderr)

        # Extract moments
        moments_result = get_popular_moments(video_url_or_id)

        if not moments_result['success']:
            print(f"Error extracting moments: {moments_result['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"Found {moments_result['total_moments']} popular moments", file=sys.stderr)

        # Create clips
        return process_video_moments(moments_result, **kwargs)

    except ImportError:
        print("Error: replay_heatmap module not found. "
              "Make sure it's in the ab/dc/analysers directory.", file=sys.stderr)
        sys.exit(1)


def format_pretty_output(result: dict) -> str:
    """Format result in human-readable format"""
    lines = []
    lines.append("=" * 60)

    if result['success']:
        lines.append(f"✓ Video Clips Created Successfully")
        lines.append("=" * 60)
        lines.append(f"Video ID: {result['video_id']}")
        lines.append(f"Video URL: {result['video_url']}")
        lines.append(f"Video Path: {result['video_path']}")

        if result.get('video_downloaded'):
            lines.append("Video: Downloaded in this run")
        else:
            lines.append("Video: Already downloaded")

        lines.append(f"\nClips Created: {result['clips_created']}")
        if result.get('clips_failed', 0) > 0:
            lines.append(f"Clips Failed: {result['clips_failed']}")

        lines.append(f"Total Size: {result['total_size_mb']}MB")
        lines.append(f"Processing Time: {result['processing_time_seconds']}s")

        if result['clips']:
            lines.append("\nClips:")
            for clip in result['clips']:
                lines.append(
                    f"  {clip['clip_id']:2d}. {clip['filename']:<40} "
                    f"{clip['file_size_mb']:>6.1f}MB  "
                    f"[{clip['start_time']:.1f}s - {clip['end_time']:.1f}s]"
                )

        if result.get('failed_clips'):
            lines.append("\nFailed Clips:")
            for clip in result['failed_clips']:
                lines.append(
                    f"  {clip['clip_id']:2d}. Error: {clip.get('error', 'Unknown')}"
                )
    else:
        lines.append(f"✗ Processing Failed")
        lines.append("=" * 60)
        lines.append(f"Error: {result.get('error', 'Unknown error')}")
        if result.get('video_id'):
            lines.append(f"Video ID: {result['video_id']}")
        if result.get('video_url'):
            lines.append(f"Video URL: {result['video_url']}")

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Create video clips from popular moments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From moments JSON file
  %(prog)s --input moments.json

  # Pipe from replay_heatmap service
  python ../analysers/cli.py VIDEO_ID --format json | %(prog)s

  # Extract moments and create clips in one command
  %(prog)s --video-id RusBe_8arLQ

  # With custom options
  %(prog)s --input moments.json --quality 720p --codec libx264 --parallel

  # Save output to file
  %(prog)s --input moments.json --output result.json --format json
        """
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument(
        '--input', '-i',
        type=str,
        help='Input JSON file with moments data'
    )
    input_group.add_argument(
        '--video-id', '--url',
        type=str,
        dest='video_id',
        help='YouTube video ID or URL (will extract moments automatically)'
    )

    # Output options
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file for results (default: stdout)'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'pretty'],
        default='pretty',
        help='Output format (default: pretty)'
    )

    # Processing options
    parser.add_argument(
        '--quality', '-q',
        choices=['best', '1080p', '720p', '480p', '360p', 'worst'],
        help='Video download quality (overrides config)'
    )
    parser.add_argument(
        '--codec',
        choices=['libx264', 'libx265', 'copy'],
        help='Video codec for clips (overrides config)'
    )
    parser.add_argument(
        '--audio-codec',
        choices=['aac', 'mp3', 'copy'],
        help='Audio codec for clips (overrides config)'
    )
    parser.add_argument(
        '--crf',
        type=int,
        help='CRF quality (18-28, lower=better)'
    )
    parser.add_argument(
        '--preset',
        choices=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast',
                 'medium', 'slow', 'slower', 'veryslow'],
        help='FFmpeg encoding preset'
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Enable parallel clip processing'
    )
    parser.add_argument(
        '--no-parallel',
        action='store_true',
        help='Disable parallel clip processing'
    )
    parser.add_argument(
        '--max-workers',
        type=int,
        help='Maximum concurrent workers for parallel processing'
    )
    parser.add_argument(
        '--aspect-ratio',
        choices=['original', '9:16', '16:9', '1:1', '4:5'],
        help='Output aspect ratio (original=keep source, 9:16=vertical/Reels, 16:9=horizontal, 1:1=square, 4:5=portrait)'
    )

    # Force options
    parser.add_argument(
        '--force-redownload',
        action='store_true',
        help='Re-download video even if it exists'
    )
    parser.add_argument(
        '--force-reprocess',
        action='store_true',
        help='Re-create clips even if they exist'
    )

    args = parser.parse_args()

    # Determine input source
    if args.video_id:
        # Extract moments and create clips
        print(f"Mode: Extract moments and create clips", file=sys.stderr)

        # Build kwargs for processing
        kwargs = {}
        if args.force_redownload:
            kwargs['force_redownload'] = True
        if args.force_reprocess:
            kwargs['force_reprocess'] = True

        # FFmpeg options
        ffmpeg_options = {}
        if args.codec:
            ffmpeg_options['video_codec'] = args.codec
        if args.audio_codec:
            ffmpeg_options['audio_codec'] = args.audio_codec
        if args.crf:
            ffmpeg_options['crf'] = args.crf
        if args.preset:
            ffmpeg_options['preset'] = args.preset
        if args.aspect_ratio:
            ffmpeg_options['aspect_ratio'] = args.aspect_ratio

        if ffmpeg_options:
            kwargs.update(ffmpeg_options)

        result = extract_and_create_clips(args.video_id, **kwargs)

    elif args.input:
        # Load from file
        print(f"Loading moments from: {args.input}", file=sys.stderr)
        moments_data = load_moments_from_file(args.input)

        # Build FFmpeg options
        ffmpeg_options = {}
        if args.codec:
            ffmpeg_options['video_codec'] = args.codec
        if args.audio_codec:
            ffmpeg_options['audio_codec'] = args.audio_codec
        if args.crf:
            ffmpeg_options['crf'] = args.crf
        if args.preset:
            ffmpeg_options['preset'] = args.preset
        if args.aspect_ratio:
            ffmpeg_options['aspect_ratio'] = args.aspect_ratio

        result = process_video_moments(moments_data, **ffmpeg_options)

    elif not sys.stdin.isatty():
        # Load from stdin (pipe)
        print(f"Reading moments from stdin...", file=sys.stderr)
        moments_data = load_moments_from_stdin()

        # Build FFmpeg options
        ffmpeg_options = {}
        if args.codec:
            ffmpeg_options['video_codec'] = args.codec
        if args.audio_codec:
            ffmpeg_options['audio_codec'] = args.audio_codec
        if args.crf:
            ffmpeg_options['crf'] = args.crf
        if args.preset:
            ffmpeg_options['preset'] = args.preset
        if args.aspect_ratio:
            ffmpeg_options['aspect_ratio'] = args.aspect_ratio

        result = process_video_moments(moments_data, **ffmpeg_options)

    else:
        parser.print_help()
        print("\nError: No input provided. Use --input, --video-id, or pipe JSON to stdin.",
              file=sys.stderr)
        sys.exit(1)

    # Format output
    if args.format == 'json':
        output = json.dumps(result, indent=2)
    else:
        output = format_pretty_output(result)

    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"\nResults saved to: {args.output}", file=sys.stderr)
    else:
        print(output)

    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()