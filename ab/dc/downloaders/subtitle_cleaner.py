"""
Subtitle Cleaner Service
Cleans VTT/SRT subtitle files by extracting only text content
and saving as Markdown for LLM metadata generation
"""

import re
from pathlib import Path
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SubtitleCleaner:
    """Cleans subtitle files for LLM processing"""

    def __init__(self):
        """Initialize subtitle cleaner"""
        pass

    def clean_vtt(self, vtt_path: Path) -> str:
        """
        Clean VTT subtitle file and extract text

        Args:
            vtt_path: Path to VTT file

        Returns:
            Cleaned text content
        """
        if not vtt_path.exists():
            raise FileNotFoundError(f"VTT file not found: {vtt_path}")

        with open(vtt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove WEBVTT header
        content = re.sub(r'^WEBVTT.*?\n\n?', '', content, flags=re.MULTILINE)

        # Split into lines
        lines = content.split('\n')

        # Process line by line, tracking what we've already added
        result_words = []
        result_text = ""

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip timestamp lines (format: 00:00:00.000 --> 00:00:00.769)
            if '-->' in line:
                continue

            # Skip lines that are just numbers (cue identifiers)
            if line.isdigit():
                continue

            # Clean VTT tags like <00:00:14.719><c> text </c>
            # Remove all <timestamp><c> tags
            cleaned = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}><c>', '', line)
            cleaned = re.sub(r'</c>', '', cleaned)

            # Remove other VTT tags
            cleaned = re.sub(r'<[^>]+>', '', cleaned)

            # Clean up extra spaces
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()

            # Skip if empty after cleaning
            if not cleaned:
                continue

            # Check if this line adds new content
            # VTT lines often repeat previous content and add new words
            # We want to extract only the NEW words

            # If current line contains all of result_text, extract the new part
            if result_text and cleaned.startswith(result_text):
                # Extract new words
                new_part = cleaned[len(result_text):].strip()
                if new_part:
                    result_text = cleaned
            elif not result_text:
                # First line
                result_text = cleaned
            else:
                # Line doesn't start with previous text, might be new section
                # Check if there's any overlap
                words = cleaned.split()
                overlap_found = False

                # Try to find where the overlap starts
                for i in range(len(result_words)):
                    # Check if current line starts where result ends
                    tail = ' '.join(result_words[i:])
                    if cleaned.startswith(tail):
                        # Found overlap, add new part
                        new_part = cleaned[len(tail):].strip()
                        if new_part:
                            result_text += ' ' + new_part
                            result_words = result_text.split()
                        overlap_found = True
                        break

                if not overlap_found:
                    # No overlap, this is completely new text
                    result_text += ' ' + cleaned

            result_words = result_text.split()

        # Final cleanup
        text = re.sub(r'\s+', ' ', result_text).strip()

        return text

    def clean_srt(self, srt_path: Path) -> str:
        """
        Clean SRT subtitle file and extract text

        Args:
            srt_path: Path to SRT file

        Returns:
            Cleaned text content
        """
        if not srt_path.exists():
            raise FileNotFoundError(f"SRT file not found: {srt_path}")

        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into subtitle blocks
        blocks = content.split('\n\n')

        text_lines = []
        for block in blocks:
            lines = block.strip().split('\n')

            for line in lines:
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Skip sequence numbers (just digits)
                if line.isdigit():
                    continue

                # Skip timestamp lines
                if '-->' in line:
                    continue

                # Remove SRT tags
                cleaned = re.sub(r'<[^>]+>', '', line)
                cleaned = re.sub(r'\{[^}]+\}', '', cleaned)

                # Clean up spaces
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()

                if cleaned:
                    text_lines.append(cleaned)

        # Join and clean
        text = ' '.join(text_lines)
        text = self._remove_consecutive_duplicates(text)
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _remove_consecutive_duplicates(self, text: str) -> str:
        """
        Remove consecutive duplicate words and phrases

        Args:
            text: Input text

        Returns:
            Text with duplicates removed
        """
        words = text.split()
        if not words:
            return text

        # First pass: remove immediate word duplicates
        deduplicated = []
        prev_word = None

        for word in words:
            if word != prev_word:
                deduplicated.append(word)
                prev_word = word

        # Second pass: remove phrase duplicates
        words = deduplicated
        result = []
        i = 0

        while i < len(words):
            # Check for repeating sequences of different lengths
            max_check = min(20, len(words) - i)
            found_duplicate = False

            for seq_len in range(max_check, 1, -1):  # Start from 2 words minimum
                if i + seq_len * 2 <= len(words):
                    # Get two sequences
                    seq1 = words[i:i + seq_len]
                    seq2 = words[i + seq_len:i + seq_len * 2]

                    if seq1 == seq2:
                        # Add the sequence once and skip the duplicate
                        result.extend(seq1)
                        i += seq_len * 2
                        found_duplicate = True
                        break

            if not found_duplicate:
                result.append(words[i])
                i += 1

        return ' '.join(result)

    def create_llm_markdown(
        self,
        text: str,
        video_id: Optional[str] = None,
        duration: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create Markdown formatted for LLM metadata generation

        Args:
            text: Cleaned subtitle text
            video_id: Optional video identifier
            duration: Optional video duration in seconds
            metadata: Optional additional metadata

        Returns:
            Markdown formatted content
        """
        md_lines = []

        # Header
        md_lines.append("# Video Transcript for Metadata Generation")
        md_lines.append("")

        # Add context if available
        if video_id or duration or metadata:
            md_lines.append("## Video Information")
            md_lines.append("")

            if video_id:
                md_lines.append(f"- **Video ID**: {video_id}")

            if duration:
                minutes = duration // 60
                seconds = duration % 60
                md_lines.append(f"- **Duration**: {minutes}m {seconds}s")

            if metadata:
                for key, value in metadata.items():
                    md_lines.append(f"- **{key.title()}**: {value}")

            md_lines.append("")

        # Instructions for LLM
        md_lines.append("## Instructions")
        md_lines.append("")
        md_lines.append("Based on the transcript below, generate viral video metadata:")
        md_lines.append("")
        md_lines.append("1. **Title** (max 100 characters):")
        md_lines.append("   - Engaging and clickable")
        md_lines.append("   - Include main topic/benefit")
        md_lines.append("   - Use power words")
        md_lines.append("")
        md_lines.append("2. **Description** (engaging, 200-500 words):")
        md_lines.append("   - Hook in first line")
        md_lines.append("   - Key points from video")
        md_lines.append("   - Call to action")
        md_lines.append("   - Relevant hashtags")
        md_lines.append("")
        md_lines.append("3. **Tags** (10-15 relevant tags):")
        md_lines.append("   - Mix of broad and specific")
        md_lines.append("   - Include trending topics")
        md_lines.append("   - Target audience keywords")
        md_lines.append("")
        md_lines.append("4. **Category** (select most relevant):")
        md_lines.append("   - Film, Music, Gaming, Sports, Education, etc.")
        md_lines.append("")
        md_lines.append("5. **Thumbnail Ideas** (3 concepts):")
        md_lines.append("   - Eye-catching visuals")
        md_lines.append("   - Text overlay suggestions")
        md_lines.append("   - Color schemes")
        md_lines.append("")

        # Transcript section
        md_lines.append("## Video Transcript")
        md_lines.append("")

        # Split text into paragraphs for readability
        sentences = self._split_into_sentences(text)
        paragraph = []

        for i, sentence in enumerate(sentences):
            paragraph.append(sentence)

            # Create new paragraph every 3-4 sentences
            if (i + 1) % 4 == 0 or i == len(sentences) - 1:
                md_lines.append(' '.join(paragraph))
                md_lines.append("")
                paragraph = []

        # Footer
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("## Output Format")
        md_lines.append("")
        md_lines.append("Please provide the metadata as a JSON object in the following format:")
        md_lines.append("")
        md_lines.append("```json")
        md_lines.append("{")
        md_lines.append('  "title": "Your engaging title here (max 100 characters)",')
        md_lines.append('  "description": "Your compelling description with hashtags and call-to-action",')
        md_lines.append('  "tags": [')
        md_lines.append('    "tag1",')
        md_lines.append('    "tag2",')
        md_lines.append('    "tag3",')
        md_lines.append('    "tag4",')
        md_lines.append('    "tag5"')
        md_lines.append('  ],')
        md_lines.append('  "category": "selected_category",')
        md_lines.append('  "thumbnail_ideas": [')
        md_lines.append('    {')
        md_lines.append('      "concept": "Concept 1 description",')
        md_lines.append('      "text_overlay": "Suggested text for thumbnail",')
        md_lines.append('      "color_scheme": "Color palette suggestion"')
        md_lines.append('    },')
        md_lines.append('    {')
        md_lines.append('      "concept": "Concept 2 description",')
        md_lines.append('      "text_overlay": "Suggested text for thumbnail",')
        md_lines.append('      "color_scheme": "Color palette suggestion"')
        md_lines.append('    },')
        md_lines.append('    {')
        md_lines.append('      "concept": "Concept 3 description",')
        md_lines.append('      "text_overlay": "Suggested text for thumbnail",')
        md_lines.append('      "color_scheme": "Color palette suggestion"')
        md_lines.append('    }')
        md_lines.append('  ],')
        md_lines.append('  "target_audience": "Description of target demographic",')
        md_lines.append('  "video_hook": "First 5 seconds hook to capture attention",')
        md_lines.append('  "call_to_action": "Specific CTA for end of video/description"')
        md_lines.append("}")
        md_lines.append("```")

        return '\n'.join(md_lines)

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def process_subtitle_file(
        self,
        subtitle_path: Path,
        output_path: Optional[Path] = None,
        include_llm_instructions: bool = True,
        metadata: Optional[Dict] = None
    ) -> Path:
        """
        Process subtitle file and save as Markdown

        Args:
            subtitle_path: Path to VTT or SRT file
            output_path: Optional output path (default: same name with .md extension)
            include_llm_instructions: Include LLM generation instructions
            metadata: Optional video metadata

        Returns:
            Path to created Markdown file
        """
        # Determine file type
        if subtitle_path.suffix.lower() == '.vtt':
            text = self.clean_vtt(subtitle_path)
        elif subtitle_path.suffix.lower() == '.srt':
            text = self.clean_srt(subtitle_path)
        else:
            raise ValueError(f"Unsupported subtitle format: {subtitle_path.suffix}")

        # Determine output path
        if output_path is None:
            output_path = subtitle_path.with_suffix('.md')

        # Extract video info from filename if available
        # Format: VIDEO_ID_0000_40s_score_095_original_en.vtt
        filename = subtitle_path.stem
        parts = filename.split('_')

        video_id = None
        duration = None

        if len(parts) >= 3:
            # Try to extract video ID (first part)
            video_id = parts[0]

            # Try to extract duration
            for part in parts:
                if part.endswith('s') and part[:-1].isdigit():
                    duration = int(part[:-1])
                    break

        # Create markdown content
        if include_llm_instructions:
            content = self.create_llm_markdown(
                text=text,
                video_id=video_id,
                duration=duration,
                metadata=metadata
            )
        else:
            # Simple clean text output
            content = f"# Video Transcript\n\n{text}\n"

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Created Markdown file: {output_path}")
        return output_path

    def process_directory(
        self,
        directory: Path,
        pattern: str = "*.vtt",
        include_llm_instructions: bool = True,
        overwrite: bool = False
    ) -> List[Path]:
        """
        Process all subtitle files in directory

        Args:
            directory: Directory containing subtitle files
            pattern: File pattern to match (e.g., "*.vtt", "*.srt")
            include_llm_instructions: Include LLM instructions
            overwrite: Overwrite existing .md files

        Returns:
            List of created Markdown files
        """
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        subtitle_files = list(directory.glob(pattern))
        logger.info(f"Found {len(subtitle_files)} subtitle files matching '{pattern}'")

        created_files = []

        for subtitle_file in subtitle_files:
            output_path = subtitle_file.with_suffix('.md')

            # Skip if file exists and not overwriting
            if output_path.exists() and not overwrite:
                logger.info(f"Skipping (already exists): {output_path}")
                continue

            try:
                md_path = self.process_subtitle_file(
                    subtitle_path=subtitle_file,
                    include_llm_instructions=include_llm_instructions
                )
                created_files.append(md_path)
                logger.info(f"Processed: {subtitle_file.name} -> {md_path.name}")

            except Exception as e:
                logger.error(f"Failed to process {subtitle_file}: {e}")

        logger.info(f"Successfully processed {len(created_files)}/{len(subtitle_files)} files")
        return created_files


def clean_subtitle_to_markdown(
    subtitle_path: Path,
    output_path: Optional[Path] = None,
    include_llm_instructions: bool = True
) -> Path:
    """
    Convenience function to clean subtitle file to Markdown

    Args:
        subtitle_path: Path to VTT or SRT file
        output_path: Optional output path
        include_llm_instructions: Include LLM instructions

    Returns:
        Path to created Markdown file
    """
    cleaner = SubtitleCleaner()
    return cleaner.process_subtitle_file(
        subtitle_path=subtitle_path,
        output_path=output_path,
        include_llm_instructions=include_llm_instructions
    )
