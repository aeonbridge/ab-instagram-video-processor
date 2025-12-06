#!/usr/bin/env python3
"""
CLI Subtitle Cleaner
Command-line interface for cleaning subtitle files to Markdown
"""

import argparse
import sys
import logging
from pathlib import Path

from subtitle_cleaner import SubtitleCleaner


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def clean_single_file(args):
    """Clean a single subtitle file"""
    subtitle_path = Path(args.input)

    if not subtitle_path.exists():
        logger.error(f"File not found: {subtitle_path}")
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = subtitle_path.with_suffix('.md')

    # Check if output exists
    if output_path.exists() and not args.force:
        logger.error(f"Output file already exists: {output_path}")
        logger.info("Use --force to overwrite")
        return 1

    try:
        cleaner = SubtitleCleaner()

        logger.info(f"Processing: {subtitle_path}")
        logger.info(f"Output: {output_path}")

        md_path = cleaner.process_subtitle_file(
            subtitle_path=subtitle_path,
            output_path=output_path,
            include_llm_instructions=not args.text_only
        )

        logger.info(f"✓ Successfully created: {md_path}")

        # Show preview
        if args.preview:
            print("\n" + "="*70)
            print("PREVIEW (first 500 characters)")
            print("="*70)
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content[:500])
                if len(content) > 500:
                    print("\n... (truncated)")
            print("="*70)

        return 0

    except Exception as e:
        logger.error(f"Failed to process file: {e}")
        return 1


def clean_directory(args):
    """Clean all subtitle files in directory"""
    directory = Path(args.directory)

    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return 1

    if not directory.is_dir():
        logger.error(f"Not a directory: {directory}")
        return 1

    try:
        cleaner = SubtitleCleaner()

        logger.info(f"Scanning directory: {directory}")
        logger.info(f"Pattern: {args.pattern}")

        created_files = cleaner.process_directory(
            directory=directory,
            pattern=args.pattern,
            include_llm_instructions=not args.text_only,
            overwrite=args.force
        )

        if created_files:
            print("\n" + "="*70)
            print(f"SUCCESSFULLY PROCESSED {len(created_files)} FILES")
            print("="*70)
            for md_file in created_files:
                print(f"  ✓ {md_file.name}")
            print("="*70)
        else:
            logger.warning("No files were processed")

        return 0

    except Exception as e:
        logger.error(f"Failed to process directory: {e}")
        return 1


def show_example(args):
    """Show usage examples"""
    examples = """
SUBTITLE CLEANER - USAGE EXAMPLES
==================================

1. Clean a single VTT file:
   python cli_subtitle_cleaner.py clean subtitle.vtt

2. Clean with custom output path:
   python cli_subtitle_cleaner.py clean subtitle.vtt -o output.md

3. Clean without LLM instructions (text only):
   python cli_subtitle_cleaner.py clean subtitle.vtt --text-only

4. Clean and preview result:
   python cli_subtitle_cleaner.py clean subtitle.vtt --preview

5. Clean all VTT files in a directory:
   python cli_subtitle_cleaner.py batch processed_videos/VIDEO_ID/

6. Clean all SRT files in a directory:
   python cli_subtitle_cleaner.py batch subtitles/ --pattern "*.srt"

7. Force overwrite existing files:
   python cli_subtitle_cleaner.py batch videos/ --force

8. Process specific clip subtitles:
   python cli_subtitle_cleaner.py batch processed_videos/RusBe_8arLQ/

INTEGRATION WITH VIDEO CLIPPER
================================

Complete workflow:

# 1. Extract popular moments
cd ab/dc/analysers
python cli.py VIDEO_ID --format json > moments.json

# 2. Create clips with subtitles
cd ../downloaders
python cli_clipper.py --input ../analysers/moments.json --aspect-ratio 9:16
python cli_subtitle_clipper.py --video-id VIDEO_ID -l en

# 3. Clean subtitles to Markdown
python cli_subtitle_cleaner.py batch processed_videos/VIDEO_ID/

# 4. Use Markdown files with LLM to generate metadata
# Feed .md files to ChatGPT, Claude, or other LLM

# 5. Upload to YouTube with generated metadata
cd ../publishers
python cli_publisher.py upload processed_videos/VIDEO_ID/clip.mp4 \\
  --title "Generated Title" \\
  --description "Generated Description" \\
  --tags "tag1,tag2,tag3"

OUTPUT FORMAT
=============

The generated Markdown files include:

1. Video Information (extracted from filename)
2. Instructions for LLM metadata generation
3. Clean transcript text (no timestamps, no tags)
4. Output format template

Example output structure:

```
# Video Transcript for Metadata Generation

## Video Information
- Video ID: RusBe_8arLQ
- Duration: 0m 40s

## Instructions
[Detailed instructions for generating:]
- Title (engaging, max 100 chars)
- Description (200-500 words with hashtags)
- Tags (10-15 relevant tags)
- Category selection
- Thumbnail ideas

## Video Transcript
[Clean text without timestamps]

## Output Format
[Template for LLM response]
```

TIPS
====

1. Use --preview to check output before processing many files
2. Use --text-only for simple transcript extraction
3. Process entire directories for batch operations
4. Generated .md files are ready for LLM input
5. Keep original .vtt/.srt files for reference

"""
    print(examples)
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Clean subtitle files (VTT/SRT) to Markdown for LLM metadata generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Use "python cli_subtitle_cleaner.py examples" for usage examples'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Clean command (single file)
    clean_parser = subparsers.add_parser(
        'clean',
        help='Clean a single subtitle file'
    )
    clean_parser.add_argument(
        'input',
        help='Path to VTT or SRT subtitle file'
    )
    clean_parser.add_argument(
        '-o', '--output',
        help='Output Markdown file path (default: same name with .md extension)'
    )
    clean_parser.add_argument(
        '--text-only',
        action='store_true',
        help='Output only clean text without LLM instructions'
    )
    clean_parser.add_argument(
        '--preview',
        action='store_true',
        help='Show preview of generated content'
    )
    clean_parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing output file'
    )
    clean_parser.set_defaults(func=clean_single_file)

    # Batch command (directory)
    batch_parser = subparsers.add_parser(
        'batch',
        help='Clean all subtitle files in a directory'
    )
    batch_parser.add_argument(
        'directory',
        help='Directory containing subtitle files'
    )
    batch_parser.add_argument(
        '--pattern',
        default='*.vtt',
        help='File pattern to match (default: *.vtt)'
    )
    batch_parser.add_argument(
        '--text-only',
        action='store_true',
        help='Output only clean text without LLM instructions'
    )
    batch_parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing .md files'
    )
    batch_parser.set_defaults(func=clean_directory)

    # Examples command
    examples_parser = subparsers.add_parser(
        'examples',
        help='Show usage examples'
    )
    examples_parser.set_defaults(func=show_example)

    # Parse arguments
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
