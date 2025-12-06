#!/usr/bin/env python3
"""
CLI for Video Pipeline Orchestrator
Complete automation from YouTube URL to published clips
"""

import argparse
import sys
import logging
from pathlib import Path

from video_pipeline_orchestrator import VideoPipelineOrchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Automated Video Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process video and generate clips (no publishing)
  %(prog)s https://www.youtube.com/watch?v=VIDEO_ID

  # Process and publish as private
  %(prog)s VIDEO_ID --publish --privacy private

  # Process and publish as public (dry-run)
  %(prog)s VIDEO_ID --publish --privacy public --dry-run

  # Custom output directory
  %(prog)s VIDEO_ID --output my_videos/

  # Custom clip duration limits
  %(prog)s VIDEO_ID --max-duration 60 --min-duration 20

Complete Workflow:
  The pipeline automatically:
  1. Extracts popular moments using YouTube heatmap data
  2. Downloads the video and subtitles
  3. Creates clips for each popular moment
  4. Generates AI metadata for each clip (title, description, tags)
  5. Generates AI thumbnails from the metadata
  6. Optionally publishes clips to YouTube

Output Structure:
  output/
  └── youtube/
      └── VIDEO_ID/
          ├── video_metadata.json        # Full video information
          ├── moments.json                # Popular moments detected
          ├── VIDEO_ID.mp4               # Downloaded video
          ├── VIDEO_ID_full_subtitle.vtt # Full subtitle
          ├── VIDEO_ID_0000/             # First moment clip
          │   ├── VIDEO_ID_0000_40s_score_095_original.mp4
          │   ├── VIDEO_ID_0000_40s_score_095_original_en.vtt
          │   ├── VIDEO_ID_0000_40s_score_095_original_en_metadata.json
          │   └── thumbnails/
          │       └── dalle/
          │           ├── *_thumbnail_1.png
          │           ├── *_thumbnail_2.png
          │           └── *_thumbnail_3.png
          ├── VIDEO_ID_0001/             # Second moment clip
          └── ...

Requirements:
  - YouTube Data API credentials (for publishing)
  - OpenAI API key (for metadata and thumbnails)
  - ffmpeg installed
  - yt-dlp installed
        """
    )

    # Required argument
    parser.add_argument(
        'url',
        help='YouTube URL or video ID'
    )

    # Output options
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='Base output directory (default: output)'
    )

    # Clip duration options
    parser.add_argument(
        '--max-duration',
        type=int,
        default=40,
        help='Maximum clip duration in seconds (default: 40)'
    )
    parser.add_argument(
        '--min-duration',
        type=int,
        default=10,
        help='Minimum clip duration in seconds (default: 10)'
    )

    # Publishing options
    publish_group = parser.add_argument_group('Publishing Options')
    publish_group.add_argument(
        '--publish',
        action='store_true',
        help='Publish clips to YouTube after processing'
    )
    publish_group.add_argument(
        '--privacy',
        choices=['public', 'private', 'unlisted'],
        default='public',
        help='Privacy status for published videos (default: public)'
    )
    publish_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Test publishing without actually uploading (requires --publish)'
    )

    # Processing options
    proc_group = parser.add_argument_group('Processing Options')
    proc_group.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip video download if already exists'
    )
    proc_group.add_argument(
        '--skip-metadata',
        action='store_true',
        help='Skip AI metadata generation'
    )
    proc_group.add_argument(
        '--skip-thumbnails',
        action='store_true',
        help='Skip AI thumbnail generation'
    )

    # Advanced options
    adv_group = parser.add_argument_group('Advanced Options')
    adv_group.add_argument(
        '--provider',
        default='youtube',
        help='Platform provider (default: youtube)'
    )
    adv_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose logging (DEBUG level)'
    )

    args = parser.parse_args()

    # Adjust logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validation
    if args.dry_run and not args.publish:
        parser.error("--dry-run requires --publish flag")

    # Show configuration
    print("="*70)
    print("VIDEO PROCESSING PIPELINE")
    print("="*70)
    print(f"Video: {args.url}")
    print(f"Output: {args.output}")
    print(f"Clip Duration: {args.min_duration}s - {args.max_duration}s")
    if args.publish:
        print(f"Publishing: {'DRY RUN' if args.dry_run else 'ENABLED'} (privacy: {args.privacy})")
    else:
        print("Publishing: DISABLED")
    print("="*70)
    print()

    # Create orchestrator
    orchestrator = VideoPipelineOrchestrator(
        provider=args.provider,
        output_base=args.output,
        max_clip_duration=args.max_duration,
        min_clip_duration=args.min_duration
    )

    # Process video
    result = orchestrator.process_video(
        url_or_id=args.url,
        publish=args.publish,
        privacy=args.privacy,
        dry_run=args.dry_run
    )

    # Display results
    if result["success"]:
        print("\n" + "="*70)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("="*70)
        
        summary = result.get("summary", {})
        print(f"\nVideo ID: {summary.get('video_id')}")
        print(f"Output Directory: {summary.get('video_dir')}")
        print()
        print(f"Popular Moments Found: {summary.get('moments_found', 0)}")
        print(f"Clips Created: {summary.get('clips_created', 0)}")
        print(f"Metadata Generated: {summary.get('metadata_generated', 0)}")
        print(f"Thumbnails Generated: {summary.get('thumbnails_generated', 0)}")
        
        if 'published' in summary:
            print(f"Clips Published: {summary.get('published', 0)}")
        
        print()
        print("="*70)
        print()
        
        # Show next steps
        if not args.publish:
            print("Next Steps:")
            print(f"  1. Review clips in: {summary.get('video_dir')}")
            print(f"  2. Publish clips:")
            print(f"     python {sys.argv[0]} {args.url} --publish --privacy private")
            print()
        
        return 0
    else:
        print("\n" + "="*70)
        print("PIPELINE FAILED")
        print("="*70)
        print(f"Error: {result.get('error', 'Unknown error')}")
        print("="*70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
