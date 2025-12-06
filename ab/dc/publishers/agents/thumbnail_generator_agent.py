"""
Thumbnail Generator Agent
Uses Agno framework with OpenAI API and nanobanana to generate viral video thumbnails from transcripts
"""

import json
import os
import logging
import base64
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import requests

try:
    from agno.agent import Agent, RunOutput
    from agno.models.openai import OpenAIChat
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    Agent = None
    RunOutput = None
    OpenAIChat = None

logger = logging.getLogger(__name__)


class ThumbnailGeneratorAgent:
    """
    Agent that generates viral video thumbnails using Agno, OpenAI, and nanobanana
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        nanobanana_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.8,
        max_tokens: int = 1500,
        image_size: str = "1920x1080",
        image_provider: str = "dalle"  # 'dalle' (recommended), 'gemini' (experimental), or 'nanobanana'
    ):
        """
        Initialize thumbnail generator agent

        Args:
            openai_api_key: OpenAI API key (reads from OPENAI_API_KEY env if not provided)
            nanobanana_api_key: nanobanana API key (reads from NANOBANANA_API_KEY env if not provided)
            model: OpenAI model to use for prompt generation
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum tokens in response
            image_size: Output image size (1920x1080, 1280x720, 1080x1920 for vertical)
        """
        if not AGNO_AVAILABLE:
            raise ImportError(
                "Agno package not installed. Install with: pip install agno openai"
            )

        # Get API keys
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass openai_api_key parameter"
            )

        self.nanobanana_api_key = nanobanana_api_key or os.getenv('NANOBANANA_API_KEY')

        self.gemini_api_key = gemini_api_key or os.getenv('GOOGLE_GEMINI_API_KEY')
        if not self.gemini_api_key and image_provider == 'gemini':
            logger.warning(
                "Gemini API key not found. Set GOOGLE_GEMINI_API_KEY environment variable."
            )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.image_size = image_size
        self.image_provider = image_provider

        # API endpoints
        self.nanobanana_url = "https://api.nanobanana.com/v1/generate"
        self.dalle_url = "https://api.openai.com/v1/images/generations"
        # Use Gemini's text generation with image response
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

        # Initialize Agno agent
        self.agent = self._create_agent()

        # Track last API usage
        self._last_usage = None

        logger.info(f"Initialized ThumbnailGeneratorAgent with model: {model}, image provider: {image_provider}")

    def _create_agent(self) -> Agent:
        """Create and configure Agno agent for thumbnail prompt generation"""

        # System instructions for the agent
        instructions = """You are an expert in creating viral YouTube and social media thumbnails.

Your task is to analyze video transcripts and generate highly effective thumbnail concepts that:
1. **Stop the scroll** - Eye-catching, bold, and attention-grabbing
2. **Communicate value** - Instantly convey what viewers will get
3. **Create curiosity** - Make people NEED to click
4. **Use proven patterns** - Leverage what works in viral content
5. **Match the platform** - Optimize for YouTube, TikTok, or Instagram

For each thumbnail concept, provide:
- **Main Visual**: Specific description of the dominant visual element
- **Text Overlay**: Short, punchy text (3-7 words max)
- **Color Scheme**: Strategic colors that pop and convert
- **Composition**: Layout and positioning details
- **Emotion/Vibe**: The feeling/reaction it should evoke
- **Image Generation Prompt**: Detailed prompt for AI image generation (nanobanana/DALL-E style)

Key principles for text overlays:
- Use ALL CAPS for impact
- Include numbers when relevant ("3 SECRETS", "$1000/DAY")
- Use emoji strategically (🔥💰✅❌)
- Create contrast (what NOT to do, before/after)
- Invoke emotions (SHOCKED, INSANE, GENIUS)

Key principles for visuals:
- High contrast (light text on dark bg or vice versa)
- Faces with exaggerated expressions (shocked, excited, confused)
- Before/After split screens
- Red circles/arrows pointing to key elements
- Green checkmarks ✅ and red X marks ❌
- Money/success symbols for financial content
- Tech/gaming visuals for tech content

IMPORTANT: Always respond with valid JSON only. Do not include any text before or after the JSON object."""

        # Create OpenAI chat model
        openai_model = OpenAIChat(
            id=self.model,
            api_key=self.openai_api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        # Create Agno agent
        agent = Agent(
            model=openai_model,
            instructions=instructions,
            markdown=False  # Ensure JSON output
        )

        return agent

    def generate_thumbnail_concepts(
        self,
        transcript: str,
        video_title: Optional[str] = None,
        num_concepts: int = 3,
        platform: str = "youtube"
    ) -> List[Dict]:
        """
        Generate thumbnail concepts based on video transcript

        Args:
            transcript: Video transcript text
            video_title: Optional video title for context
            num_concepts: Number of thumbnail concepts to generate (1-5)
            platform: Target platform (youtube, tiktok, instagram, generic)

        Returns:
            List of thumbnail concept dictionaries
        """
        # Build prompt
        prompt = self._build_prompt(transcript, video_title, num_concepts, platform)

        # Run agent
        logger.info("Generating thumbnail concepts with Agno agent...")
        response = self.agent.run(prompt)

        # Parse response
        try:
            # Extract JSON from response
            content = response.content

            # Try to find JSON in the response
            if isinstance(content, str):
                # Remove markdown code blocks if present
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()

                concepts_data = json.loads(content)
            else:
                concepts_data = content

            # Validate and extract concepts
            if isinstance(concepts_data, dict):
                concepts = concepts_data.get('thumbnail_concepts', concepts_data.get('concepts', []))
            elif isinstance(concepts, list):
                concepts = concepts_data
            else:
                raise ValueError("Invalid response format")

            # Add cost tracking
            usage_info = None
            if hasattr(response, 'metrics') and response.metrics:
                cost_info = self._calculate_cost(response.metrics)
                usage_info = {
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
                    usage_info['duration_seconds'] = round(response.metrics.duration, 2)

            logger.info(f"Generated {len(concepts)} thumbnail concepts")

            # Store usage info for later retrieval
            self._last_usage = usage_info

            return concepts

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse agent response: {e}")
            logger.debug(f"Response content: {response.content}")
            raise

    def generate_thumbnail_image(
        self,
        concept: Dict,
        output_path: Path,
        aspect_ratio: Optional[str] = None
    ) -> Dict:
        """
        Generate actual thumbnail image using nanobanana

        Args:
            concept: Thumbnail concept dictionary with 'image_prompt'
            output_path: Path to save generated image
            aspect_ratio: Override aspect ratio (16:9, 9:16, 1:1, 4:5)

        Returns:
            Dictionary with generation results
        """
        if not self.nanobanana_api_key:
            logger.warning("nanobanana API key not configured. Skipping image generation.")
            return {
                'success': False,
                'error': 'nanobanana API key not configured',
                'concept': concept
            }

        # Get image prompt
        image_prompt = concept.get('image_prompt', concept.get('prompt', ''))
        if not image_prompt:
            return {
                'success': False,
                'error': 'No image_prompt in concept',
                'concept': concept
            }

        # Determine image size based on aspect ratio
        if aspect_ratio:
            size_map = {
                '16:9': '1920x1080',
                '9:16': '1080x1920',
                '1:1': '1080x1080',
                '4:5': '1080x1350'
            }
            image_size = size_map.get(aspect_ratio, self.image_size)
        else:
            image_size = self.image_size

        # Use appropriate provider
        if self.image_provider == 'dalle':
            return self._generate_with_dalle(image_prompt, output_path, image_size, concept)
        elif self.image_provider == 'gemini':
            return self._generate_with_gemini(image_prompt, output_path, image_size, concept)
        else:
            return self._generate_with_nanobanana(image_prompt, output_path, image_size, concept)

    def _generate_with_dalle(
        self,
        prompt: str,
        output_path: Path,
        image_size: str,
        concept: Dict
    ) -> Dict:
        """Generate image using OpenAI DALL-E 3"""
        logger.info(f"Generating thumbnail image with DALL-E 3 ({image_size})...")
        logger.debug(f"Prompt: {prompt}")

        # DALL-E 3 only supports specific sizes
        dalle_size = "1024x1024"  # Default square
        if "1920" in image_size or "16:9" in str(image_size):
            dalle_size = "1792x1024"  # Landscape
        elif "1080x1920" in image_size or "9:16" in str(image_size):
            dalle_size = "1024x1792"  # Portrait

        try:
            # Call OpenAI DALL-E API
            response = requests.post(
                self.dalle_url,
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'dall-e-3',
                    'prompt': prompt[:4000],  # DALL-E limit
                    'size': dalle_size,
                    'quality': 'hd',
                    'style': 'vivid',
                    'n': 1
                },
                timeout=120  # DALL-E can take longer
            )
            response.raise_for_status()

            result = response.json()

            # Get image URL
            if 'data' in result and len(result['data']) > 0:
                image_url = result['data'][0].get('url')
                if image_url:
                    # Download image
                    img_response = requests.get(image_url, timeout=30)
                    img_response.raise_for_status()
                    image_bytes = img_response.content

                    # Ensure output directory exists
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    # Save image
                    with open(output_path, 'wb') as f:
                        f.write(image_bytes)

                    logger.info(f"Thumbnail saved to: {output_path}")

                    return {
                        'success': True,
                        'image_path': str(output_path),
                        'image_size': dalle_size,
                        'provider': 'dalle',
                        'concept': concept
                    }

            return {
                'success': False,
                'error': 'No image URL in DALL-E response',
                'concept': concept
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"DALL-E API error: {e}")
            return {
                'success': False,
                'error': f'DALL-E API error: {str(e)}',
                'concept': concept
            }

        except Exception as e:
            logger.error(f"Unexpected error generating thumbnail: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'concept': concept
            }

    def _generate_with_gemini(
        self,
        prompt: str,
        output_path: Path,
        image_size: str,
        concept: Dict
    ) -> Dict:
        """Generate image using Google Gemini (Imagen 3)"""
        logger.info(f"Generating thumbnail image with Gemini/Imagen 3 ({image_size})...")
        logger.debug(f"Prompt: {prompt}")

        if not self.gemini_api_key:
            return {
                'success': False,
                'error': 'Gemini API key not configured',
                'concept': concept
            }

        # Determine aspect ratio and resolution
        aspect_ratio = "16:9"  # Default
        resolution = "2K"  # Default

        if "1920" in image_size or "16:9" in str(image_size):
            aspect_ratio = "16:9"
            resolution = "2K"
        elif "1080x1920" in image_size or "9:16" in str(image_size):
            aspect_ratio = "9:16"
            resolution = "2K"
        elif "1080x1080" in image_size or "1:1" in str(image_size):
            aspect_ratio = "1:1"
            resolution = "2K"
        elif "1080x1350" in image_size or "4:5" in str(image_size):
            aspect_ratio = "4:5"
            resolution = "2K"

        try:
            # Call Gemini API with generateContent endpoint
            url = f"{self.gemini_url}?key={self.gemini_api_key}"

            response = requests.post(
                url,
                headers={
                    'Content-Type': 'application/json'
                },
                json={
                    "contents": [{
                        "parts": [{
                            "text": prompt[:5000]  # Gemini limit
                        }]
                    }],
                    "generationConfig": {
                        "responseModalities": ["IMAGE"],
                        "imageConfig": {
                            "aspectRatio": aspect_ratio
                        }
                    }
                },
                timeout=120
            )
            response.raise_for_status()

            result = response.json()

            # Get image from response
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'inlineData' in part:
                            import base64
                            image_data = part['inlineData'].get('data', '')
                            image_bytes = base64.b64decode(image_data)

                            # Ensure output directory exists
                            output_path.parent.mkdir(parents=True, exist_ok=True)

                            # Save image
                            with open(output_path, 'wb') as f:
                                f.write(image_bytes)

                            logger.info(f"Thumbnail saved to: {output_path}")

                            return {
                                'success': True,
                                'image_path': str(output_path),
                                'image_size': f"{resolution} {aspect_ratio}",
                                'provider': 'gemini',
                                'concept': concept
                            }

            return {
                'success': False,
                'error': 'No image data in Gemini response',
                'concept': concept
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API error: {e}")
            return {
                'success': False,
                'error': f'Gemini API error: {str(e)}',
                'concept': concept
            }

        except Exception as e:
            logger.error(f"Unexpected error generating thumbnail: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'concept': concept
            }

    def _generate_with_nanobanana(
        self,
        prompt: str,
        output_path: Path,
        image_size: str,
        concept: Dict
    ) -> Dict:
        """Generate image using nanobanana API"""
        logger.info(f"Generating thumbnail image with nanobanana ({image_size})...")
        logger.debug(f"Prompt: {prompt}")

        try:
            # Call nanobanana API
            response = requests.post(
                self.nanobanana_url,
                headers={
                    'Authorization': f'Bearer {self.nanobanana_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'prompt': image_prompt,
                    'size': image_size,
                    'quality': 'hd',
                    'style': 'vivid',  # More dramatic/eye-catching
                    'n': 1
                },
                timeout=60
            )
            response.raise_for_status()

            result = response.json()

            # Get image URL or base64 data
            if 'data' in result and len(result['data']) > 0:
                image_data = result['data'][0]

                # Download and save image
                if 'url' in image_data:
                    img_response = requests.get(image_data['url'], timeout=30)
                    img_response.raise_for_status()
                    image_bytes = img_response.content
                elif 'b64_json' in image_data:
                    image_bytes = base64.b64decode(image_data['b64_json'])
                else:
                    raise ValueError("No image data in response")

                # Save to file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(image_bytes)

                logger.info(f"Thumbnail saved to: {output_path}")

                return {
                    'success': True,
                    'image_path': str(output_path),
                    'concept': concept,
                    'size': image_size,
                    'file_size_mb': len(image_bytes) / (1024 * 1024)
                }
            else:
                raise ValueError("No image data in API response")

        except requests.exceptions.RequestException as e:
            logger.error(f"nanobanana API error: {e}")
            return {
                'success': False,
                'error': f"API error: {str(e)}",
                'concept': concept
            }
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            return {
                'success': False,
                'error': str(e),
                'concept': concept
            }

    def generate_thumbnails_from_transcript(
        self,
        transcript_path: Path,
        output_dir: Path,
        num_thumbnails: int = 3,
        platform: str = "youtube",
        aspect_ratio: Optional[str] = None,
        generate_images: bool = True
    ) -> Dict:
        """
        Complete workflow: generate concepts and images from transcript file

        Args:
            transcript_path: Path to transcript markdown file
            output_dir: Directory to save thumbnail images
            num_thumbnails: Number of thumbnails to generate
            platform: Target platform
            aspect_ratio: Aspect ratio for images (16:9, 9:16, 1:1, 4:5)
            generate_images: Whether to generate actual images (requires nanobanana API)

        Returns:
            Dictionary with all generated thumbnails
        """
        # Read transcript
        logger.info(f"Reading transcript from: {transcript_path}")
        transcript = self._read_transcript(transcript_path)

        # Extract video title from transcript if available
        video_title = self._extract_title_from_transcript(transcript)

        # Generate concepts
        concepts = self.generate_thumbnail_concepts(
            transcript=transcript,
            video_title=video_title,
            num_concepts=num_thumbnails,
            platform=platform
        )

        # Generate images if requested
        results = []
        for i, concept in enumerate(concepts):
            result = {'concept': concept}

            if generate_images:
                # Generate filename
                base_name = transcript_path.stem
                output_filename = f"{base_name}_thumbnail_{i+1}.png"
                output_path = output_dir / output_filename

                # Generate image
                image_result = self.generate_thumbnail_image(
                    concept=concept,
                    output_path=output_path,
                    aspect_ratio=aspect_ratio
                )
                result.update(image_result)
            else:
                result['success'] = True
                result['message'] = 'Concept only (image generation skipped)'

            results.append(result)

        # Summary
        successful = sum(1 for r in results if r.get('success', False))

        result = {
            'success': successful > 0,
            'transcript_path': str(transcript_path),
            'concepts_generated': len(concepts),
            'images_generated': successful,
            'thumbnails': results,
            'output_dir': str(output_dir)
        }

        # Add usage info if available
        if self._last_usage:
            result['_usage'] = self._last_usage

        return result

    def generate_thumbnails_from_metadata(
        self,
        metadata_path: Path,
        output_dir: Path,
        aspect_ratio: Optional[str] = None,
        generate_images: bool = True
    ) -> Dict:
        """
        Generate thumbnails from metadata JSON file (from metadata generator)

        Args:
            metadata_path: Path to metadata JSON file
            output_dir: Directory to save thumbnail images
            aspect_ratio: Aspect ratio for images (16:9, 9:16, 1:1, 4:5)
            generate_images: Whether to generate actual images (requires nanobanana API)

        Returns:
            Dictionary with all generated thumbnails
        """
        # Read metadata JSON
        logger.info(f"Reading metadata from: {metadata_path}")

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to read metadata file: {e}")

        # Extract thumbnail ideas
        thumbnail_ideas = metadata.get('thumbnail_ideas', [])
        if not thumbnail_ideas:
            raise ValueError("No thumbnail_ideas found in metadata JSON")

        logger.info(f"Found {len(thumbnail_ideas)} thumbnail ideas in metadata")

        # Convert metadata thumbnail_ideas to thumbnail concepts format
        concepts = []
        for i, idea in enumerate(thumbnail_ideas):
            # Build a detailed prompt from the metadata idea
            concept = {
                'main_visual': idea.get('concept', f'Thumbnail concept {i+1}'),
                'text_overlay': idea.get('text_overlay', ''),
                'color_scheme': self._parse_color_scheme(idea.get('color_scheme', '')),
                'composition': f"Based on: {idea.get('concept', '')}",
                'emotion': 'engaging',
                'image_prompt': self._build_image_prompt_from_metadata(
                    idea,
                    metadata.get('title', ''),
                    metadata.get('description', '')
                )
            }
            concepts.append(concept)

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate images if requested
        results = []
        for i, concept in enumerate(concepts):
            result = {'concept': concept}

            if generate_images:
                # Generate filename
                base_name = metadata_path.stem.replace('_metadata', '')
                output_filename = f"{base_name}_thumbnail_{i+1}.png"
                output_path = output_dir / output_filename

                # Generate image
                image_result = self.generate_thumbnail_image(
                    concept=concept,
                    output_path=output_path,
                    aspect_ratio=aspect_ratio
                )
                result.update(image_result)
            else:
                result['success'] = True
                result['message'] = 'Concept only (image generation skipped)'

            results.append(result)

        # Summary
        successful = sum(1 for r in results if r.get('success', False))

        return {
            'success': successful > 0,
            'metadata_path': str(metadata_path),
            'concepts_generated': len(concepts),
            'images_generated': successful,
            'thumbnails': results,
            'output_dir': str(output_dir),
            'source': 'metadata'
        }

    def _parse_color_scheme(self, color_scheme: str) -> List[str]:
        """Parse color scheme from metadata format"""
        if isinstance(color_scheme, list):
            return color_scheme

        # Parse from string like "Blue and white" or "Black, yellow, red"
        if isinstance(color_scheme, str):
            # Simple color mapping
            color_map = {
                'blue': '#2196F3',
                'red': '#F44336',
                'green': '#4CAF50',
                'yellow': '#FFEB3B',
                'orange': '#FF9800',
                'purple': '#9C27B0',
                'pink': '#E91E63',
                'black': '#000000',
                'white': '#FFFFFF',
                'gray': '#9E9E9E',
                'grey': '#9E9E9E'
            }

            colors = []
            color_scheme_lower = color_scheme.lower()
            for color_name, hex_code in color_map.items():
                if color_name in color_scheme_lower:
                    colors.append(hex_code)

            return colors if colors else ['#2196F3', '#FFFFFF']

        return ['#2196F3', '#FFFFFF']

    def _build_image_prompt_from_metadata(
        self,
        idea: Dict,
        title: str,
        description: str
    ) -> str:
        """Build detailed image prompt from metadata thumbnail idea"""
        concept = idea.get('concept', '')
        text_overlay = idea.get('text_overlay', '')
        color_scheme = idea.get('color_scheme', '')

        prompt = f"""Create a professional, eye-catching YouTube thumbnail image.

Visual Concept: {concept}

Text Overlay: {text_overlay}
(The text should be bold, highly visible, and professionally integrated into the image)

Color Scheme: {color_scheme}
(Use these colors strategically to create visual impact and brand consistency)

Context from video:
Title: {title}
Description: {description[:200]}

Style Requirements:
- Professional and polished look
- High contrast for readability
- Eye-catching and click-worthy
- Clear focal point
- Optimized for small preview sizes
- No generic stock photos
- Authentic and engaging

The image should instantly communicate the video's value and make viewers want to click."""

        return prompt

    def _build_prompt(
        self,
        transcript: str,
        video_title: Optional[str],
        num_concepts: int,
        platform: str
    ) -> str:
        """Build prompt for agent"""

        title_context = f"\n\n**Video Title**: {video_title}" if video_title else ""

        prompt = f"""Analyze this video transcript and generate {num_concepts} viral thumbnail concepts for {platform.upper()}.

{title_context}

**Transcript**:
{transcript[:2000]}  # Limit to avoid token limits

Generate {num_concepts} different thumbnail concepts, each optimized for maximum click-through rate.

For each concept, provide:
1. **main_visual**: Specific visual description (person, object, scene, emotion)
2. **text_overlay**: Short punchy text for the thumbnail (3-7 words, use CAPS and emoji)
3. **color_scheme**: Strategic color palette (list 2-3 main colors)
4. **composition**: Layout details (positioning, split screen, framing)
5. **emotion**: Target emotion/vibe (shocked, excited, curious, etc.)
6. **image_prompt**: Detailed prompt for AI image generation (200+ words, very specific, photorealistic style)

Return ONLY a JSON object with this structure:
{{
  "thumbnail_concepts": [
    {{
      "main_visual": "description",
      "text_overlay": "TEXT HERE",
      "color_scheme": ["#FF0000", "#FFFF00"],
      "composition": "composition details",
      "emotion": "emotion",
      "image_prompt": "Detailed prompt for image generation: ..."
    }}
  ]
}}"""

        return prompt

    def _read_transcript(self, transcript_path: Path) -> str:
        """Read transcript from markdown file"""
        if not transcript_path.exists():
            raise FileNotFoundError(f"Transcript not found: {transcript_path}")

        content = transcript_path.read_text(encoding='utf-8')

        # Try to extract just the transcript text
        # Look for "## Video Transcript" or similar
        if '## Video Transcript' in content:
            parts = content.split('## Video Transcript', 1)
            if len(parts) > 1:
                transcript = parts[1].strip()
                # Remove everything after "---" or "## Output Format"
                if '---' in transcript:
                    transcript = transcript.split('---')[0].strip()
                if '## Output Format' in transcript:
                    transcript = transcript.split('## Output Format')[0].strip()
                return transcript

        # Fallback: return full content
        return content

    def _extract_title_from_transcript(self, content: str) -> Optional[str]:
        """Try to extract video title from transcript content"""
        # Look for patterns like "**Video ID**: something"
        lines = content.split('\n')
        for line in lines:
            if 'Video ID' in line and ':' in line:
                return line.split(':', 1)[1].strip().strip('*').strip()
        return None

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


def main():
    """Example usage"""
    import sys

    # Example transcript path
    if len(sys.argv) > 1:
        transcript_path = Path(sys.argv[1])
    else:
        transcript_path = Path("processed_videos/RusBe_8arLQ/RusBe_8arLQ_0000_40s_score_095_original_en.md")

    # Initialize agent
    agent = ThumbnailGeneratorAgent()

    # Generate thumbnails
    result = agent.generate_thumbnails_from_transcript(
        transcript_path=transcript_path,
        output_dir=Path("thumbnails"),
        num_thumbnails=3,
        platform="youtube",
        aspect_ratio="16:9",
        generate_images=True  # Set to False to only generate concepts
    )

    # Print results
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
