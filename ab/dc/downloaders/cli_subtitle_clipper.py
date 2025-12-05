#!/usr/bin/env python3
"""
CLI tool for generating subtitle files for video clips
"""

import sys
import argparse
import json
import logging
from pathlib import Path

from subtitle_clipper_service import (
    process_moments_subtitles,
    extract_and_generate_subtitles,
    SubtitleClipperError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def load_moments_from_file(file_path: str) -> dict:
    """Load moments data from JSON file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file: {e}")
        sys.exit(1)


def format_pretty_output(result: dict) -> str:
    """Format result in human-readable format"""
    lines = []
    lines.append("=" * 70)

    if result['success']:
        lines.append("Clip Subtitles Generated Successfully")
        lines.append("=" * 70)
        lines.append(f"Video ID: {result['video_id']}")
        lines.append(f"Video URL: {result['video_url']}")
        lines.append(f"Languages: {', '.join(result['languages_processed'])}")
        lines.append(f"Total Clips: {result['total_clips']}")
        lines.append(f"Subtitles Created: {result['clip_subtitles_created']}")
        lines.append(f"Processing Time: {result['processing_time']:.1f}s")

        if result.get('moments_extracted'):
            lines.append(f"Moments Extracted: {result['moments_extracted']}")

        if result['clip_subtitles']:
            lines.append(f"\nClip Subtitles:")

            # Group by clip_id
            clips_by_id = {}
            for sub in result['clip_subtitles']:
                clip_id = sub['clip_id']
                if clip_id not in clips_by_id:
                    clips_by_id[clip_id] = []
                clips_by_id[clip_id].append(sub)

            for clip_id in sorted(clips_by_id.keys()):
                clip_subs = clips_by_id[clip_id]
                first_sub = clip_subs[0]

                lines.append(
                    f"  Clip {clip_id:2d}: "
                    f"[{first_sub['start_time']:.1f}s - {first_sub['end_time']:.1f}s] "
                    f"({first_sub['duration']:.1f}s)"
                )

                for sub in clip_subs:
                    lines.append(
                        f"    - {sub['language']}: {sub['filename']} "
                        f"({sub['segments_count']} segments)"
                    )
    else:
        lines.append("Subtitle Generation Failed")
        lines.append("=" * 70)
        lines.append(f"Error: {result.get('error', 'Unknown error')}")
        if result.get('video_id'):
            lines.append(f"Video ID: {result['video_id']}")
        if result.get('video_url'):
            lines.append(f"Video URL: {result['video_url']}")

    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Generate subtitle files for video clips based on popular moments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract moments and generate subtitles (English)
  %(prog)s --video-id "dQw4w9WgXcQ"

  # Extract moments and generate subtitles (multiple languages)
  %(prog)s --video-id "dQw4w9WgXcQ" -l en -l pt -l es

  # From moments JSON file
  %(prog)s --input moments.json -l en

  # With custom output directory
  %(prog)s --video-id "dQw4w9WgXcQ" -l en --output-dir ./my_clips

  # Generate SRT format instead of VTT
  %(prog)s --video-id "dQw4w9WgXcQ" -l en -f srt

  # With aspect ratio for clip naming
  %(prog)s --video-id "dQw4w9WgXcQ" -l en --aspect-ratio 9:16

  # Save output to JSON file
  %(prog)s --video-id "dQw4w9WgXcQ" -l en --json-output result.json
        """
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--video-id', '--url',
        type=str,
        dest='video_id',
        help='YouTube video ID or URL (will extract moments automatically)'
    )
    input_group.add_argument(
        '--input', '-i',
        type=str,
        help='Input JSON file with moments data (from get_popular_moments)'
    )

    # Language options
    parser.add_argument(
        '-l', '--language',
        action='append',
        dest='languages',
        help='Language code (e.g., en, pt, es). Can be specified multiple times. Default: en'
    )

    # Output options
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='./processed_videos',
        help='Output directory for clip subtitles (default: ./processed_videos)'
    )
    parser.add_argument(
        '--subtitles-dir',
        type=str,
        default='./subtitles',
        help='Directory to download full video subtitles (default: ./subtitles)'
    )
    parser.add_argument(
        '--json-output',
        type=str,
        help='Save result as JSON to file'
    )

    # Format options
    parser.add_argument(
        '-f', '--format',
        choices=['vtt', 'srt'],
        default='vtt',
        help='Subtitle format (default: vtt)'
    )

    # Clip naming options
    parser.add_argument(
        '--aspect-ratio',
        choices=['original', '9:16', '16:9', '1:1', '4:5'],
        default='original',
        help='Aspect ratio for clip naming (default: original)'
    )

    # Moments extraction options (only used with --video-id)
    parser.add_argument(
        '--max-duration',
        type=int,
        default=40,
        help='Maximum moment duration in seconds (default: 40)'
    )
    parser.add_argument(
        '--min-duration',
        type=int,
        default=10,
        help='Minimum moment duration in seconds (default: 10)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.45,
        help='Minimum relative value for peak detection (default: 0.45)'
    )

    # Other options
    parser.add_argument(
        '--force-redownload',
        action='store_true',
        help='Force re-download of subtitle even if it exists'
    )

    args = parser.parse_args()

    # Default to English if no languages specified
    languages = args.languages if args.languages else ['en']

    # Process based on input mode
    if args.video_id:
        # Extract moments and generate subtitles
        logger.info(f"Mode: Extract moments and generate subtitles")
        logger.info(f"Video: {args.video_id}")
        logger.info(f"Languages: {', '.join(languages)}")

        result = extract_and_generate_subtitles(
            video_url_or_id=args.video_id,
            languages=languages,
            max_duration=args.max_duration,
            min_duration=args.min_duration,
            threshold=args.threshold,
            format=args.format,
            aspect_ratio=args.aspect_ratio,
            subtitles_download_path=Path(args.subtitles_dir),
            clips_output_path=Path(args.output_dir)
        )

    else:
        # Load from moments JSON file
        logger.info(f"Mode: Generate subtitles from moments file")
        logger.info(f"Input: {args.input}")
        logger.info(f"Languages: {', '.join(languages)}")

        moments_data = load_moments_from_file(args.input)

        result = process_moments_subtitles(
            moments_data=moments_data,
            subtitles_download_path=Path(args.subtitles_dir),
            clips_output_path=Path(args.output_dir),
            languages=languages,
            format=args.format,
            aspect_ratio=args.aspect_ratio,
            force_redownload=args.force_redownload
        )

    # Output results
    print("\n" + format_pretty_output(result))

    # Save JSON output if requested
    if args.json_output:
        with open(args.json_output, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"\nJSON output saved to: {args.json_output}")

    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()