#!/usr/bin/env python3
"""
CLI for Thumbnail Generator Agent
Generate viral thumbnails from video transcripts using AI
"""

import argparse
import json
import sys
import logging
import os
from pathlib import Path

# Load environment variables from parent directory's .env file
try:
    from dotenv import load_dotenv
    # Try to load .env from parent directory (ab/dc/publishers/)
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, will rely on env vars

from thumbnail_generator_agent import ThumbnailGeneratorAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_thumbnails(args):
    """Generate thumbnails from transcript"""
    try:
        # Initialize agent
        logger.info("Initializing Thumbnail Generator Agent...")
        agent = ThumbnailGeneratorAgent(
            model=args.model,
            temperature=args.temperature,
            image_size=args.size
        )

        # Process single file or directory
        if args.transcript.is_file():
            transcripts = [args.transcript]
        elif args.transcript.is_dir():
            # Find all .md files
            transcripts = list(args.transcript.glob('*.md'))
            if not transcripts:
                transcripts = list(args.transcript.glob('**/*.md'))
            logger.info(f"Found {len(transcripts)} transcript file(s)")
        else:
            logger.error(f"Path not found: {args.transcript}")
            return 1

        # Process each transcript
        results = []
        for transcript_path in transcripts:
            logger.info(f"\nProcessing: {transcript_path.name}")

            # Determine output directory
            if args.output:
                output_dir = args.output
            else:
                # Create thumbnails/ subdirectory next to transcript
                output_dir = transcript_path.parent / 'thumbnails'

            # Generate thumbnails
            result = agent.generate_thumbnails_from_transcript(
                transcript_path=transcript_path,
                output_dir=output_dir,
                num_thumbnails=args.num,
                platform=args.platform,
                aspect_ratio=args.ratio,
                generate_images=not args.concepts_only
            )

            results.append(result)

            # Print summary
            if result['success']:
                logger.info(f"  Generated {result['images_generated']}/{result['concepts_generated']} thumbnail(s)")
                logger.info(f"  Output: {result['output_dir']}")

                # Show cost information if available
                if '_usage' in result:
                    usage = result['_usage']
                    logger.info(f"  Tokens: {usage['total_tokens']} (input: {usage['input_tokens']}, output: {usage['output_tokens']})")
                    logger.info(f"  Cost: ${usage['cost_usd']:.6f} USD")
                    if 'duration_seconds' in usage:
                        logger.info(f"  Duration: {usage['duration_seconds']}s")
            else:
                logger.error(f"  Failed to generate thumbnails")

        # Save combined results if JSON output requested
        if args.format == 'json':
            output_data = {
                'total_transcripts': len(transcripts),
                'total_concepts': sum(r.get('concepts_generated', 0) for r in results),
                'total_images': sum(r.get('images_generated', 0) for r in results),
                'results': results
            }

            if args.json_output:
                with open(args.json_output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                logger.info(f"\nResults saved to: {args.json_output}")
            else:
                print(json.dumps(output_data, indent=2))

        # Print summary
        total_success = sum(1 for r in results if r.get('success', False))
        total_cost = sum(r.get('_usage', {}).get('cost_usd', 0) for r in results)
        total_tokens = sum(r.get('_usage', {}).get('total_tokens', 0) for r in results)

        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Transcripts processed: {len(transcripts)}")
        print(f"Successful: {total_success}")
        print(f"Failed: {len(transcripts) - total_success}")

        if total_cost > 0:
            print(f"Total Cost: ${total_cost:.6f} USD")
            print(f"Total Tokens: {total_tokens:,}")
            if total_success > 0:
                print(f"Average Cost per Transcript: ${total_cost/total_success:.6f} USD")

        print(f"{'='*60}")

        return 0 if total_success > 0 else 1

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


def list_concepts(args):
    """List thumbnail concepts without generating images"""
    args.concepts_only = True
    args.format = 'json'
    return generate_thumbnails(args)


def generate_from_metadata(args):
    """Generate thumbnails from metadata JSON file or directory"""
    try:
        # Validate metadata file/directory
        metadata_path = args.metadata
        if not metadata_path.exists():
            logger.error(f"Path not found: {metadata_path}")
            return 1

        # Get list of metadata files
        metadata_files = []
        if metadata_path.is_file():
            if not metadata_path.name.endswith('.json'):
                logger.error(f"Metadata file must be a JSON file: {metadata_path}")
                return 1
            metadata_files = [metadata_path]
        elif metadata_path.is_dir():
            # Find all *_metadata.json files in directory
            metadata_files = list(metadata_path.glob('*_metadata.json'))
            if not metadata_files:
                logger.error(f"No *_metadata.json files found in: {metadata_path}")
                return 1
            logger.info(f"Found {len(metadata_files)} metadata file(s)")
        else:
            logger.error(f"Invalid path: {metadata_path}")
            return 1

        # Initialize agent (no need for OpenAI API for this operation)
        logger.info("Initializing Thumbnail Generator Agent...")
        agent = ThumbnailGeneratorAgent(
            model='gpt-3.5-turbo',  # Not used for metadata-based generation
            image_size=args.size,
            image_provider=getattr(args, 'provider', 'dalle')
        )

        # Process each metadata file
        results = []
        for metadata_file in metadata_files:
            # Determine output directory
            if args.output:
                output_dir = args.output
            else:
                # Create thumbnails/ subdirectory next to metadata file
                output_dir = metadata_file.parent / 'thumbnails'

            logger.info(f"\nProcessing metadata: {metadata_file.name}")

            # Generate thumbnails from metadata
            try:
                result = agent.generate_thumbnails_from_metadata(
                    metadata_path=metadata_file,
                    output_dir=output_dir,
                    aspect_ratio=args.ratio,
                    generate_images=not args.concepts_only
                )

                results.append(result)

                # Print summary
                if result['success']:
                    logger.info(f"  Generated {result['images_generated']}/{result['concepts_generated']} thumbnail(s)")
                    logger.info(f"  Output: {result['output_dir']}")
                else:
                    logger.error(f"  Failed to generate thumbnails")

            except Exception as e:
                logger.error(f"  Error processing {metadata_file.name}: {e}")
                results.append({'success': False, 'error': str(e)})

        # Save results if JSON output requested
        if args.format == 'json':
            output_data = {
                'total_files': len(metadata_files),
                'total_concepts': sum(r.get('concepts_generated', 0) for r in results),
                'total_images': sum(r.get('images_generated', 0) for r in results),
                'results': results
            }

            if args.json_output:
                with open(args.json_output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                logger.info(f"\nResults saved to: {args.json_output}")
            else:
                print(json.dumps(output_data, indent=2))

        # Print summary
        total_success = sum(1 for r in results if r.get('success', False))
        total_concepts = sum(r.get('concepts_generated', 0) for r in results)
        total_images = sum(r.get('images_generated', 0) for r in results)

        print(f"\n{'='*60}")
        print(f"SUMMARY - FROM METADATA")
        print(f"{'='*60}")
        print(f"Metadata files: {len(metadata_files)}")
        print(f"Successful: {total_success}")
        print(f"Failed: {len(metadata_files) - total_success}")
        print(f"Total concepts: {total_concepts}")
        print(f"Total images: {total_images}")
        print(f"{'='*60}")

        return 0 if total_success > 0 else 1

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Generate viral video thumbnails from transcripts using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 3 thumbnails from a transcript
  %(prog)s generate transcript.md

  # Generate 5 thumbnails for TikTok (vertical)
  %(prog)s generate transcript.md --num 5 --platform tiktok --ratio 9:16

  # Process all transcripts in a directory
  %(prog)s generate processed_videos/RusBe_8arLQ/

  # Only generate concepts (no images)
  %(prog)s generate transcript.md --concepts-only

  # List concepts as JSON
  %(prog)s concepts transcript.md --num 5

  # Custom output directory
  %(prog)s generate transcript.md --output my_thumbnails/

  # Use GPT-3.5 for faster/cheaper generation
  %(prog)s generate transcript.md --model gpt-3.5-turbo

  # Generate from metadata JSON (already has thumbnail ideas)
  %(prog)s from-metadata video_metadata.json

  # Generate from metadata with custom output
  %(prog)s from-metadata video_metadata.json --output custom_thumbnails/

  # Show concepts from metadata only (no image generation)
  %(prog)s meta video_metadata.json --concepts-only

  # Generate with DALL-E 3 (OpenAI - default, high quality, reliable)
  %(prog)s from-metadata video_metadata.json

  # Or explicitly specify provider
  %(prog)s from-metadata video_metadata.json --provider dalle

  # Gemini support (experimental)
  %(prog)s from-metadata video_metadata.json --provider gemini

Environment Variables:
  OPENAI_API_KEY         - OpenAI API key (required for all operations)
  GOOGLE_GEMINI_API_KEY  - Google Gemini API key (optional, experimental)
  NANOBANANA_API_KEY     - nanobanana API key (optional, legacy)
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Generate command
    gen_parser = subparsers.add_parser(
        'generate',
        help='Generate thumbnail images',
        aliases=['gen']
    )
    gen_parser.add_argument(
        'transcript',
        type=Path,
        help='Path to transcript file (.md) or directory'
    )
    gen_parser.add_argument(
        '--num', '-n',
        type=int,
        default=3,
        help='Number of thumbnails to generate (default: 3)'
    )
    gen_parser.add_argument(
        '--platform', '-p',
        choices=['youtube', 'tiktok', 'instagram', 'generic'],
        default='youtube',
        help='Target platform (default: youtube)'
    )
    gen_parser.add_argument(
        '--ratio', '-r',
        choices=['16:9', '9:16', '1:1', '4:5'],
        help='Aspect ratio (auto-detected from platform if not specified)'
    )
    gen_parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output directory (default: thumbnails/ next to transcript)'
    )
    gen_parser.add_argument(
        '--model', '-m',
        default='gpt-4-turbo-preview',
        help='OpenAI model (default: gpt-4-turbo-preview)'
    )
    gen_parser.add_argument(
        '--temperature', '-t',
        type=float,
        default=0.8,
        help='Generation temperature 0.0-1.0 (default: 0.8)'
    )
    gen_parser.add_argument(
        '--size', '-s',
        default='1920x1080',
        help='Image size (default: 1920x1080)'
    )
    gen_parser.add_argument(
        '--concepts-only',
        action='store_true',
        help='Only generate concepts, skip image generation'
    )
    gen_parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    gen_parser.add_argument(
        '--json-output',
        type=Path,
        help='Save JSON output to file'
    )
    gen_parser.set_defaults(func=generate_thumbnails)

    # Concepts command (alias for concepts-only)
    concepts_parser = subparsers.add_parser(
        'concepts',
        help='Generate concepts only (no images)',
        aliases=['con']
    )
    concepts_parser.add_argument(
        'transcript',
        type=Path,
        help='Path to transcript file (.md)'
    )
    concepts_parser.add_argument(
        '--num', '-n',
        type=int,
        default=3,
        help='Number of concepts (default: 3)'
    )
    concepts_parser.add_argument(
        '--platform', '-p',
        choices=['youtube', 'tiktok', 'instagram', 'generic'],
        default='youtube',
        help='Target platform (default: youtube)'
    )
    concepts_parser.add_argument(
        '--model', '-m',
        default='gpt-4-turbo-preview',
        help='OpenAI model'
    )
    concepts_parser.add_argument(
        '--temperature', '-t',
        type=float,
        default=0.8,
        help='Generation temperature'
    )
    concepts_parser.add_argument(
        '--json-output',
        type=Path,
        help='Save JSON output to file'
    )
    concepts_parser.set_defaults(
        func=list_concepts,
        ratio=None,
        output=None,
        size='1920x1080'
    )

    # From-metadata command (generate from metadata JSON)
    metadata_parser = subparsers.add_parser(
        'from-metadata',
        help='Generate thumbnails from metadata JSON file',
        aliases=['meta']
    )
    metadata_parser.add_argument(
        'metadata',
        type=Path,
        help='Path to metadata JSON file (*_metadata.json) or directory with metadata files'
    )
    metadata_parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output directory (default: thumbnails/ next to metadata file)'
    )
    metadata_parser.add_argument(
        '--ratio', '-r',
        choices=['16:9', '9:16', '1:1', '4:5'],
        help='Aspect ratio (auto-detected from platform if not specified)'
    )
    metadata_parser.add_argument(
        '--size', '-s',
        default='1920x1080',
        help='Image size (default: 1920x1080)'
    )
    metadata_parser.add_argument(
        '--concepts-only',
        action='store_true',
        help='Only show concepts, skip image generation'
    )
    metadata_parser.add_argument(
        '--provider',
        choices=['dalle', 'gemini', 'nanobanana'],
        default='dalle',
        help='Image generation provider (default: dalle - recommended)'
    )
    metadata_parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    metadata_parser.add_argument(
        '--json-output',
        type=Path,
        help='Save JSON output to file'
    )
    metadata_parser.set_defaults(func=generate_from_metadata)

    # Parse args
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Run command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
