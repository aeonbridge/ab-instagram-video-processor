#!/usr/bin/env python3
"""
CLI Metadata Agent
Command-line interface for AI-powered metadata generation
"""

import argparse
import sys
import json
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

try:
    from metadata_generator_agent import MetadataGeneratorAgent
except ImportError:
    from .metadata_generator_agent import MetadataGeneratorAgent


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def generate_single(args):
    """Generate metadata for single transcript"""
    transcript_path = Path(args.input)

    if not transcript_path.exists():
        logger.error(f"File not found: {transcript_path}")
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = transcript_path.parent / f"{transcript_path.stem}_metadata.json"

    # Check if output exists
    if output_path.exists() and not args.force:
        logger.error(f"Output file already exists: {output_path}")
        logger.info("Use --force to overwrite")
        return 1

    try:
        # Initialize agent
        logger.info("Initializing AI agent...")
        agent = MetadataGeneratorAgent(
            api_key=args.api_key,
            model=args.model,
            temperature=args.temperature
        )

        logger.info(f"Processing: {transcript_path.name}")
        logger.info(f"Platform: {args.platform}")
        logger.info(f"Model: {args.model}")

        # Generate metadata
        metadata = agent.generate_metadata(
            transcript_path=transcript_path,
            platform=args.platform
        )

        # Validate
        is_valid, errors = agent.validate_metadata(metadata)
        if not is_valid:
            logger.warning("Generated metadata has validation errors:")
            for error in errors:
                logger.warning(f"  - {error}")

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Metadata saved to: {output_path}")

        # Show cost information
        if '_usage' in metadata:
            usage = metadata['_usage']
            logger.info(f"Tokens: {usage['total_tokens']} (input: {usage['input_tokens']}, output: {usage['output_tokens']})")
            logger.info(f"Cost: ${usage['cost_usd']:.6f} USD")
            if 'duration_seconds' in usage:
                logger.info(f"Duration: {usage['duration_seconds']}s")

        # Show preview
        if args.preview:
            print("\n" + "="*70)
            print("METADATA PREVIEW")
            print("="*70)
            print(f"Title: {metadata.get('title', 'N/A')}")
            print(f"Category: {metadata.get('category', 'N/A')}")
            print(f"Tags: {', '.join(metadata.get('tags', []))}")
            print(f"\nDescription:\n{metadata.get('description', 'N/A')[:200]}...")
            print("="*70)

        return 0

    except ImportError as e:
        logger.error(f"Missing dependencies: {e}")
        logger.info("\nInstall required packages:")
        logger.info("  pip install agno openai")
        return 1

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("\nMake sure OPENAI_API_KEY is set:")
        logger.info("  export OPENAI_API_KEY='your-api-key'")
        logger.info("Or pass it via --api-key parameter")
        return 1

    except Exception as e:
        logger.error(f"Failed to generate metadata: {e}", exc_info=args.debug)
        return 1


def generate_batch(args):
    """Generate metadata for all transcripts in directory"""
    directory = Path(args.directory)

    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return 1

    if not directory.is_dir():
        logger.error(f"Not a directory: {directory}")
        return 1

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = directory

    try:
        # Initialize agent
        logger.info("Initializing AI agent...")
        agent = MetadataGeneratorAgent(
            api_key=args.api_key,
            model=args.model,
            temperature=args.temperature
        )

        logger.info(f"Scanning directory: {directory}")
        logger.info(f"Pattern: {args.pattern}")
        logger.info(f"Platform: {args.platform}")

        # Generate batch
        created_files = agent.generate_batch(
            transcript_dir=directory,
            output_dir=output_dir,
            pattern=args.pattern,
            platform=args.platform,
            overwrite=args.force
        )

        if created_files:
            print("\n" + "="*70)
            print(f"SUCCESSFULLY GENERATED {len(created_files)} METADATA FILES")
            print("="*70)

            total_cost = 0.0
            total_tokens = 0
            for json_file in created_files:
                print(f"  ✓ {json_file.name}")
                # Calculate total cost from all generated files
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        if '_usage' in metadata:
                            total_cost += metadata['_usage']['cost_usd']
                            total_tokens += metadata['_usage']['total_tokens']
                except Exception:
                    pass

            print("="*70)
            if total_cost > 0:
                print(f"Total Cost: ${total_cost:.6f} USD")
                print(f"Total Tokens: {total_tokens:,}")
                print(f"Average Cost per File: ${total_cost/len(created_files):.6f} USD")
                print("="*70)
        else:
            logger.warning("No metadata files were generated")

        return 0

    except ImportError as e:
        logger.error(f"Missing dependencies: {e}")
        logger.info("\nInstall required packages:")
        logger.info("  pip install agno openai")
        return 1

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("\nMake sure OPENAI_API_KEY is set:")
        logger.info("  export OPENAI_API_KEY='your-api-key'")
        return 1

    except Exception as e:
        logger.error(f"Batch generation failed: {e}", exc_info=args.debug)
        return 1


def validate_metadata(args):
    """Validate metadata JSON file"""
    metadata_path = Path(args.metadata_file)

    if not metadata_path.exists():
        logger.error(f"File not found: {metadata_path}")
        return 1

    try:
        # Load metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Initialize agent just for validation
        agent = MetadataGeneratorAgent()

        # Validate
        is_valid, errors = agent.validate_metadata(metadata)

        print("\n" + "="*70)
        if is_valid:
            print("✓ METADATA IS VALID")
            print("="*70)
            print(f"Title: {metadata['title']}")
            print(f"Category: {metadata['category']}")
            print(f"Tags: {len(metadata.get('tags', []))} tags")
            print(f"Thumbnail Ideas: {len(metadata.get('thumbnail_ideas', []))}")
        else:
            print("✗ METADATA HAS ERRORS")
            print("="*70)
            for error in errors:
                print(f"  - {error}")
        print("="*70)

        return 0 if is_valid else 1

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON file: {e}")
        return 1

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return 1


def show_examples(args):
    """Show usage examples"""
    examples = """
METADATA AGENT - USAGE EXAMPLES
================================

SETUP
-----

1. Install dependencies:
   pip install agno openai

2. Set OpenAI API key:
   export OPENAI_API_KEY='sk-...'

   Or add to .env file:
   OPENAI_API_KEY=sk-...

BASIC USAGE
-----------

1. Generate metadata for single transcript:
   python cli_metadata_agent.py generate transcript.md

2. Generate with custom output:
   python cli_metadata_agent.py generate transcript.md -o metadata.json

3. Generate with preview:
   python cli_metadata_agent.py generate transcript.md --preview

4. Specify platform:
   python cli_metadata_agent.py generate transcript.md --platform tiktok

5. Use different model:
   python cli_metadata_agent.py generate transcript.md --model gpt-3.5-turbo

BATCH PROCESSING
----------------

1. Generate for all transcripts in directory:
   python cli_metadata_agent.py batch processed_videos/VIDEO_ID/

2. Batch with custom output directory:
   python cli_metadata_agent.py batch transcripts/ --output-dir metadata/

3. Batch with specific pattern:
   python cli_metadata_agent.py batch videos/ --pattern "*_en.md"

4. Force overwrite existing files:
   python cli_metadata_agent.py batch videos/ --force

PLATFORM-SPECIFIC
-----------------

1. YouTube optimization:
   python cli_metadata_agent.py generate transcript.md --platform youtube

2. TikTok optimization:
   python cli_metadata_agent.py generate transcript.md --platform tiktok

3. YouTube Shorts:
   python cli_metadata_agent.py generate transcript.md --platform shorts

4. Instagram Reels:
   python cli_metadata_agent.py generate transcript.md --platform instagram

VALIDATION
----------

1. Validate generated metadata:
   python cli_metadata_agent.py validate metadata.json

COMPLETE WORKFLOW
-----------------

# 1. Extract moments from video
cd ab/dc/analysers
python cli.py VIDEO_ID --format json > moments.json

# 2. Create clips
cd ../downloaders
python cli_clipper.py --input ../analysers/moments.json --aspect-ratio 9:16

# 3. Generate subtitle files
python cli_subtitle_clipper.py --video-id VIDEO_ID -l en

# 4. Clean subtitles to markdown
python cli_subtitle_cleaner.py batch processed_videos/VIDEO_ID/

# 5. Generate AI metadata
cd ../publishers/agents
python cli_metadata_agent.py batch ../../processed_videos/VIDEO_ID/ --platform youtube

# 6. Publish videos with AI-generated metadata
cd ..
for metadata in ../../processed_videos/VIDEO_ID/*_metadata.json; do
    video="${metadata%_metadata.json}.mp4"
    python cli_publisher.py upload "$video" \\
        --title "$(jq -r .title $metadata)" \\
        --description "$(jq -r .description $metadata)" \\
        --tags "$(jq -r '.tags | join(",")' $metadata)" \\
        --category "$(jq -r .category $metadata)"
done

ADVANCED OPTIONS
----------------

1. Custom temperature (creativity):
   python cli_metadata_agent.py generate transcript.md --temperature 0.9

2. Debug mode:
   python cli_metadata_agent.py generate transcript.md --debug

3. Pass API key directly:
   python cli_metadata_agent.py generate transcript.md --api-key sk-...

MODELS AVAILABLE
----------------

- gpt-4-turbo-preview (best quality, slower)
- gpt-4 (high quality)
- gpt-3.5-turbo (fast, cost-effective)

COST ESTIMATES
--------------

Per video (with gpt-4-turbo-preview):
- ~$0.01 - $0.03 per metadata generation
- Batch of 10 videos: ~$0.10 - $0.30

With gpt-3.5-turbo:
- ~$0.001 - $0.005 per generation
- Much cheaper for large batches

TIPS
----

1. Use gpt-4-turbo-preview for high-value content
2. Use gpt-3.5-turbo for batch processing
3. Validate metadata before publishing
4. Test different temperatures for creativity
5. Keep transcripts under 3000 words for best results

"""
    print(examples)
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='AI-powered metadata generation using Agno and OpenAI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Use "python cli_metadata_agent.py examples" for detailed usage examples'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Generate command (single file)
    generate_parser = subparsers.add_parser(
        'generate',
        help='Generate metadata for single transcript'
    )
    generate_parser.add_argument(
        'input',
        help='Path to transcript markdown file'
    )
    generate_parser.add_argument(
        '-o', '--output',
        help='Output JSON file path (default: input_metadata.json)'
    )
    generate_parser.add_argument(
        '--platform',
        default='youtube',
        choices=['youtube', 'tiktok', 'instagram', 'shorts'],
        help='Target platform (default: youtube)'
    )
    generate_parser.add_argument(
        '--model',
        default='gpt-4-turbo-preview',
        help='OpenAI model to use (default: gpt-4-turbo-preview)'
    )
    generate_parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='Temperature for generation 0.0-1.0 (default: 0.7)'
    )
    generate_parser.add_argument(
        '--api-key',
        help='OpenAI API key (or set OPENAI_API_KEY env var)'
    )
    generate_parser.add_argument(
        '--preview',
        action='store_true',
        help='Show preview of generated metadata'
    )
    generate_parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing output file'
    )
    generate_parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    generate_parser.set_defaults(func=generate_single)

    # Batch command
    batch_parser = subparsers.add_parser(
        'batch',
        help='Generate metadata for all transcripts in directory'
    )
    batch_parser.add_argument(
        'directory',
        help='Directory containing transcript files'
    )
    batch_parser.add_argument(
        '--output-dir',
        help='Output directory for JSON files (default: same as input)'
    )
    batch_parser.add_argument(
        '--pattern',
        default='*.md',
        help='File pattern to match (default: *.md)'
    )
    batch_parser.add_argument(
        '--platform',
        default='youtube',
        choices=['youtube', 'tiktok', 'instagram', 'shorts'],
        help='Target platform (default: youtube)'
    )
    batch_parser.add_argument(
        '--model',
        default='gpt-4-turbo-preview',
        help='OpenAI model to use'
    )
    batch_parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='Temperature for generation'
    )
    batch_parser.add_argument(
        '--api-key',
        help='OpenAI API key'
    )
    batch_parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing JSON files'
    )
    batch_parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    batch_parser.set_defaults(func=generate_batch)

    # Validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate metadata JSON file'
    )
    validate_parser.add_argument(
        'metadata_file',
        help='Path to metadata JSON file'
    )
    validate_parser.set_defaults(func=validate_metadata)

    # Examples command
    examples_parser = subparsers.add_parser(
        'examples',
        help='Show detailed usage examples'
    )
    examples_parser.set_defaults(func=show_examples)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Set logging level
    if hasattr(args, 'debug') and args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        return args.func(args)
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=hasattr(args, 'debug') and args.debug)
        return 1


if __name__ == '__main__':
    sys.exit(main())
