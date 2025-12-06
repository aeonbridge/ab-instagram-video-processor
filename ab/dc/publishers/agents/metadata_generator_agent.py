"""
Metadata Generator Agent
Uses Agno framework with OpenAI API to generate viral video metadata from transcripts
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

try:
    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    Agent = None
    OpenAIChat = None

logger = logging.getLogger(__name__)


class MetadataGeneratorAgent:
    """
    Agent that generates viral video metadata using Agno and OpenAI
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        Initialize metadata generator agent

        Args:
            api_key: OpenAI API key (reads from OPENAI_API_KEY env if not provided)
            model: OpenAI model to use
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum tokens in response
        """
        if not AGNO_AVAILABLE:
            raise ImportError(
                "Agno package not installed. Install with: pip install agno openai"
            )

        # Get API key
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter"
            )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize Agno agent
        self.agent = self._create_agent()

        logger.info(f"Initialized MetadataGeneratorAgent with model: {model}")

    def _create_agent(self) -> Agent:
        """Create and configure Agno agent"""

        # System instructions for the agent
        instructions = """You are a viral video metadata expert specializing in YouTube, TikTok, and social media optimization.

Your task is to analyze video transcripts and generate highly optimized metadata that maximizes engagement, click-through rates, and virality.

Key principles:
1. **Titles**: Create attention-grabbing, curiosity-inducing titles under 100 characters
2. **Descriptions**: Write compelling descriptions with strategic hashtags and clear CTAs
3. **Tags**: Select a mix of broad reach and niche-specific tags for discoverability
4. **Thumbnails**: Suggest visually striking concepts that stop scrollers
5. **Hooks**: Craft irresistible opening lines that prevent viewers from scrolling
6. **Target Audience**: Define specific demographics for precise targeting

Always analyze the transcript content, identify the main value proposition, and optimize for maximum viral potential.

IMPORTANT: Always respond with valid JSON only. Do not include any text before or after the JSON object."""

        # Create OpenAI chat model
        openai_model = OpenAIChat(
            id=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        # Create Agno agent
        agent = Agent(
            model=openai_model,
            instructions=instructions,
            markdown=False  # Ensure clean JSON output
        )

        return agent

    def generate_metadata(
        self,
        transcript_path: Path,
        video_duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        platform: str = "youtube"
    ) -> Dict:
        """
        Generate metadata from transcript file

        Args:
            transcript_path: Path to markdown transcript file
            video_duration: Optional video duration in seconds
            aspect_ratio: Optional aspect ratio (e.g., "9:16", "16:9")
            platform: Target platform (youtube, tiktok, instagram)

        Returns:
            Dictionary with generated metadata

        Raises:
            FileNotFoundError: If transcript file doesn't exist
            ValueError: If generation fails
        """
        if not transcript_path.exists():
            raise FileNotFoundError(f"Transcript file not found: {transcript_path}")

        # Read transcript
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_content = f.read()

        # Extract video info from filename
        video_info = self._extract_video_info(transcript_path, video_duration, aspect_ratio)

        # Build prompt
        prompt = self._build_prompt(transcript_content, video_info, platform)

        logger.info(f"Generating metadata for: {transcript_path.name}")
        logger.debug(f"Using platform: {platform}, aspect_ratio: {aspect_ratio}")

        try:
            # Run agent
            response = self.agent.run(prompt)

            # Extract JSON from response
            metadata = self._parse_response(response.content)

            # Add generation metadata
            metadata['_generated_at'] = datetime.now().isoformat()
            metadata['_model'] = self.model
            metadata['_source_file'] = str(transcript_path)
            metadata['_platform'] = platform

            # Add cost and token usage information
            if response.metrics:
                cost_info = self._calculate_cost(response.metrics)
                metadata['_usage'] = {
                    'input_tokens': response.metrics.input_tokens,
                    'output_tokens': response.metrics.output_tokens,
                    'total_tokens': response.metrics.total_tokens,
                    'cost_usd': cost_info['total_cost'],
                    'cost_breakdown': {
                        'input_cost_usd': cost_info['input_cost'],
                        'output_cost_usd': cost_info['output_cost']
                    }
                }
                if response.metrics.duration:
                    metadata['_usage']['duration_seconds'] = round(response.metrics.duration, 2)

            logger.info("Metadata generated successfully")
            return metadata

        except Exception as e:
            logger.error(f"Failed to generate metadata: {e}")
            raise ValueError(f"Metadata generation failed: {str(e)}")

    def _extract_video_info(
        self,
        transcript_path: Path,
        video_duration: Optional[int],
        aspect_ratio: Optional[str]
    ) -> Dict:
        """Extract video information from filename and parameters"""

        filename = transcript_path.stem
        parts = filename.split('_')

        info = {
            'filename': filename,
            'video_id': None,
            'clip_number': None,
            'duration': video_duration,
            'score': None,
            'aspect_ratio': aspect_ratio or 'original',
            'language': 'en'
        }

        # Try to parse filename format: VIDEO_ID_0000_40s_score_095_original_en
        if len(parts) >= 3:
            info['video_id'] = parts[0]

            # Extract clip number
            if parts[1].isdigit():
                info['clip_number'] = int(parts[1])

            # Extract duration
            for part in parts:
                if part.endswith('s') and part[:-1].isdigit():
                    info['duration'] = int(part[:-1])
                    break

            # Extract score
            for i, part in enumerate(parts):
                if part == 'score' and i + 1 < len(parts):
                    try:
                        info['score'] = float(parts[i + 1]) / 100
                    except ValueError:
                        pass

            # Extract aspect ratio
            for part in parts:
                if 'x' in part or ':' in part:
                    info['aspect_ratio'] = part

            # Extract language (usually last part before extension)
            if len(parts) > 0 and len(parts[-1]) == 2:
                info['language'] = parts[-1]

        return info

    def _build_prompt(
        self,
        transcript_content: str,
        video_info: Dict,
        platform: str
    ) -> str:
        """Build prompt for agent"""

        # Extract just the transcript text from markdown
        transcript_text = self._extract_transcript_text(transcript_content)

        prompt_parts = []

        # Add context
        prompt_parts.append(f"Platform: {platform.upper()}")

        if video_info.get('duration'):
            prompt_parts.append(f"Video Duration: {video_info['duration']} seconds")

        if video_info.get('aspect_ratio'):
            prompt_parts.append(f"Aspect Ratio: {video_info['aspect_ratio']}")

        if video_info.get('score'):
            prompt_parts.append(f"Engagement Score: {video_info['score']:.2f}")

        # Platform-specific guidance
        platform_guidance = {
            'youtube': "Focus on SEO-optimized titles and comprehensive descriptions with timestamps.",
            'tiktok': "Create punchy, trend-focused titles and hashtag-heavy descriptions.",
            'instagram': "Emphasize visual appeal and story-driven captions.",
            'shorts': "Optimize for YouTube Shorts: vertical format, under 60 seconds, trending topics."
        }

        if platform.lower() in platform_guidance:
            prompt_parts.append(f"\nGuidance: {platform_guidance[platform.lower()]}")

        # Add transcript
        prompt_parts.append(f"\n## Video Transcript\n\n{transcript_text}")

        # Add output format instruction
        prompt_parts.append("""

## Task

Generate viral video metadata in the following JSON format:

```json
{
  "title": "Engaging title (max 100 characters)",
  "description": "Compelling description with hashtags and CTA",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "category": "category_name",
  "thumbnail_ideas": [
    {
      "concept": "Visual concept description",
      "text_overlay": "Text for thumbnail",
      "color_scheme": "Color palette"
    },
    {
      "concept": "Alternative concept",
      "text_overlay": "Alternative text",
      "color_scheme": "Alternative colors"
    },
    {
      "concept": "Third concept",
      "text_overlay": "Third text option",
      "color_scheme": "Third color scheme"
    }
  ],
  "target_audience": "Demographic description",
  "video_hook": "First 5 seconds hook",
  "call_to_action": "Specific CTA"
}
```

Respond with ONLY the JSON object, no additional text.""")

        return '\n'.join(prompt_parts)

    def _extract_transcript_text(self, markdown_content: str) -> str:
        """Extract just the transcript text from markdown"""

        # If it's a simple text file (text_only mode)
        if not markdown_content.startswith('#'):
            return markdown_content.strip()

        # Extract from markdown format
        lines = markdown_content.split('\n')
        in_transcript = False
        transcript_lines = []

        for line in lines:
            if line.startswith('## Video Transcript'):
                in_transcript = True
                continue
            elif line.startswith('---') or line.startswith('##'):
                in_transcript = False
                continue

            if in_transcript and line.strip():
                transcript_lines.append(line.strip())

        return ' '.join(transcript_lines)

    def _parse_response(self, response_content: str) -> Dict:
        """Parse JSON response from agent"""

        # Clean response
        content = response_content.strip()

        # Remove markdown code blocks if present
        if content.startswith('```'):
            # Find the actual JSON content
            lines = content.split('\n')
            json_lines = []
            in_json = False

            for line in lines:
                if line.startswith('```'):
                    in_json = not in_json
                    continue
                if in_json:
                    json_lines.append(line)

            content = '\n'.join(json_lines)

        # Try to parse JSON
        try:
            metadata = json.loads(content)
            return metadata
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {content}")
            raise ValueError(f"Invalid JSON response from agent: {str(e)}")

    def generate_batch(
        self,
        transcript_dir: Path,
        output_dir: Optional[Path] = None,
        pattern: str = "*.md",
        platform: str = "youtube",
        overwrite: bool = False
    ) -> List[Path]:
        """
        Generate metadata for all transcripts in directory

        Args:
            transcript_dir: Directory containing transcript markdown files
            output_dir: Output directory for JSON files (default: same as transcripts)
            pattern: File pattern to match
            platform: Target platform
            overwrite: Overwrite existing JSON files

        Returns:
            List of created JSON file paths
        """
        if not transcript_dir.exists():
            raise FileNotFoundError(f"Directory not found: {transcript_dir}")

        output_dir = output_dir or transcript_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        transcript_files = list(transcript_dir.glob(pattern))
        logger.info(f"Found {len(transcript_files)} transcript files")

        created_files = []

        for transcript_file in transcript_files:
            # Skip text_only files if there's a full version
            if 'text_only' in transcript_file.stem:
                full_version = transcript_file.parent / transcript_file.name.replace('_text_only', '')
                if full_version.exists():
                    logger.info(f"Skipping {transcript_file.name} (full version exists)")
                    continue

            # Determine output path
            output_file = output_dir / f"{transcript_file.stem}_metadata.json"

            if output_file.exists() and not overwrite:
                logger.info(f"Skipping {transcript_file.name} (metadata exists)")
                continue

            try:
                # Generate metadata
                metadata = self.generate_metadata(
                    transcript_path=transcript_file,
                    platform=platform
                )

                # Save to JSON
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)

                created_files.append(output_file)
                logger.info(f"Created: {output_file.name}")

            except Exception as e:
                logger.error(f"Failed to process {transcript_file.name}: {e}")

        logger.info(f"Successfully processed {len(created_files)}/{len(transcript_files)} files")
        return created_files

    def _calculate_cost(self, metrics) -> Dict[str, float]:
        """
        Calculate API cost based on token usage and model

        Pricing as of 2024 (per 1M tokens):
        - GPT-4 Turbo: $10/1M input, $30/1M output
        - GPT-4: $30/1M input, $60/1M output
        - GPT-3.5 Turbo: $0.50/1M input, $1.50/1M output
        - GPT-4o: $2.50/1M input, $10/1M output
        - GPT-4o-mini: $0.15/1M input, $0.60/1M output

        Args:
            metrics: Agno Metrics object with token counts

        Returns:
            Dictionary with input_cost, output_cost, and total_cost in USD
        """
        # Pricing per 1M tokens (input, output)
        model_pricing = {
            'gpt-4-turbo-preview': (10.00, 30.00),
            'gpt-4-turbo': (10.00, 30.00),
            'gpt-4': (30.00, 60.00),
            'gpt-4-0613': (30.00, 60.00),
            'gpt-3.5-turbo': (0.50, 1.50),
            'gpt-3.5-turbo-0125': (0.50, 1.50),
            'gpt-4o': (2.50, 10.00),
            'gpt-4o-mini': (0.15, 0.60),
            'gpt-4o-2024-11-20': (2.50, 10.00),
        }

        # Get pricing for current model (default to GPT-4 Turbo if unknown)
        input_price_per_million, output_price_per_million = model_pricing.get(
            self.model,
            (10.00, 30.00)
        )

        # Calculate costs
        input_tokens = metrics.input_tokens or 0
        output_tokens = metrics.output_tokens or 0

        input_cost = (input_tokens / 1_000_000) * input_price_per_million
        output_cost = (output_tokens / 1_000_000) * output_price_per_million
        total_cost = input_cost + output_cost

        return {
            'input_cost': round(input_cost, 6),
            'output_cost': round(output_cost, 6),
            'total_cost': round(total_cost, 6)
        }

    def validate_metadata(self, metadata: Dict) -> tuple[bool, List[str]]:
        """
        Validate generated metadata

        Args:
            metadata: Metadata dictionary

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []

        # Required fields
        required_fields = ['title', 'description', 'tags', 'category']
        for field in required_fields:
            if field not in metadata:
                errors.append(f"Missing required field: {field}")

        # Title length
        if 'title' in metadata and len(metadata['title']) > 100:
            errors.append(f"Title exceeds 100 characters: {len(metadata['title'])}")

        # Tags format
        if 'tags' in metadata:
            if not isinstance(metadata['tags'], list):
                errors.append("Tags must be a list")
            elif len(metadata['tags']) < 3:
                errors.append("At least 3 tags required")

        # Thumbnail ideas
        if 'thumbnail_ideas' in metadata:
            if not isinstance(metadata['thumbnail_ideas'], list):
                errors.append("thumbnail_ideas must be a list")
            else:
                for i, thumb in enumerate(metadata['thumbnail_ideas']):
                    if not isinstance(thumb, dict):
                        errors.append(f"thumbnail_ideas[{i}] must be an object")
                    else:
                        required_thumb_fields = ['concept', 'text_overlay', 'color_scheme']
                        for field in required_thumb_fields:
                            if field not in thumb:
                                errors.append(f"thumbnail_ideas[{i}] missing field: {field}")

        is_valid = len(errors) == 0
        return is_valid, errors


def generate_metadata_from_transcript(
    transcript_path: Path,
    api_key: Optional[str] = None,
    platform: str = "youtube",
    model: str = "gpt-4-turbo-preview"
) -> Dict:
    """
    Convenience function to generate metadata from transcript

    Args:
        transcript_path: Path to transcript markdown file
        api_key: Optional OpenAI API key
        platform: Target platform
        model: OpenAI model to use

    Returns:
        Generated metadata dictionary
    """
    agent = MetadataGeneratorAgent(api_key=api_key, model=model)
    return agent.generate_metadata(transcript_path, platform=platform)
