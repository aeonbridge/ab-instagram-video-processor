#!/usr/bin/env python3
"""
Command-line interface for YouTube Popular Moments extraction.

Usage:
    python cli.py <youtube_url_or_video_id> [options]

Examples:
    python cli.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    python cli.py dQw4w9WgXcQ --max-duration 60 --min-duration 15
    python cli.py "https://youtu.be/dQw4w9WgXcQ" --output moments.json
"""

import argparse
import json
import sys
from pathlib import Path

from replay_heatmap import get_popular_moments


def main():
    parser = argparse.ArgumentParser(
        description="Extract popular moments from YouTube videos using heatmap data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://www.youtube.com/watch?v=RusBe_8arLQ"
  %(prog)s RusBe_8arLQ --max-duration 60 --min-duration 15
  %(prog)s "https://youtu.be/RusBe_8arLQ" --output moments.json --format json
        """
    )

    parser.add_argument(
        "url",
        help="YouTube URL or video ID"
    )

    parser.add_argument(
        "--max-duration",
        type=int,
        default=40,
        help="Maximum moment duration in seconds (default: 40)"
    )

    parser.add_argument(
        "--min-duration",
        type=int,
        default=10,
        help="Minimum moment duration in seconds (default: 10)"
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.45,
        help="Peak detection threshold, 0.1-0.9 (default: 0.45, lower = more moments)"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path (default: print to stdout)"
    )

    parser.add_argument(
        "--format", "-f",
        choices=["json", "pretty", "csv"],
        default="pretty",
        help="Output format (default: pretty)"
    )

    args = parser.parse_args()

    # Call the service
    print(f"Extracting popular moments from: {args.url}", file=sys.stderr)
    result = get_popular_moments(
        url_or_video_id=args.url,
        max_duration=args.max_duration,
        min_duration=args.min_duration,
        threshold=args.threshold
    )

    # Format output
    if args.format == "json":
        output = json.dumps(result, indent=2)
    elif args.format == "csv":
        output = format_csv(result)
    else:  # pretty
        output = format_pretty(result)

    # Write output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(output)
        print(f"\n✓ Results saved to: {output_path}", file=sys.stderr)
    else:
        print(output)

    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


def format_pretty(result: dict) -> str:
    """Format result in human-readable format"""
    lines = []
    lines.append("="*60)

    if result['success']:
        lines.append(f"✓ Successfully extracted {result['total_moments']} popular moments")
        lines.append(f"Video ID: {result['video_id']}")
        lines.append("="*60)

        if result['moments']:
            lines.append("\nPopular Moments:")
            for i, moment in enumerate(result['moments'], 1):
                lines.append(
                    f"{i:2d}. [{moment['timestamp']}] "
                    f"{moment['start_time']:.1f}s - {moment['end_time']:.1f}s "
                    f"(duration: {moment['duration']:.1f}s, score: {moment['score']:.2f})"
                )
        else:
            lines.append("\nNo moments found.")
    else:
        lines.append(f"✗ Error: {result['error']}")
        if result['video_id']:
            lines.append(f"Video ID: {result['video_id']}")

    lines.append("="*60)
    return "\n".join(lines)


def format_csv(result: dict) -> str:
    """Format result as CSV"""
    if not result['success']:
        return f"error,{result['error']}\n"

    lines = ["timestamp,start_time,end_time,duration,score"]

    for moment in result['moments']:
        lines.append(
            f"{moment['timestamp']},{moment['start_time']},"
            f"{moment['end_time']},{moment['duration']},{moment['score']}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    main()