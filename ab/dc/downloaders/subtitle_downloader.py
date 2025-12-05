"""
Subtitle Downloader Service
Downloads subtitles from YouTube videos using yt-dlp
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from storage_manager import sanitize_video_id

logger = logging.getLogger(__name__)


class SubtitleDownloadError(Exception):
    """Custom exception for subtitle download failures"""
    pass


def get_subtitle_path(
    video_id: str,
    language: str,
    base_path: Path,
    extension: str = '.vtt'
) -> Path:
    """
    Get path for subtitle file

    Args:
        video_id: YouTube video ID
        language: Language code (e.g., 'en', 'pt', 'es')
        base_path: Base path for subtitles directory
        extension: File extension (default: .vtt, also supports .srt)

    Returns:
        Path to subtitle file
    """
    video_id = sanitize_video_id(video_id)
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path / f"{video_id}_{language}{extension}"


def list_available_subtitles(video_url: str) -> Dict[str, List[Dict]]:
    """
    List all available subtitles for a YouTube video

    Args:
        video_url: YouTube video URL or video ID

    Returns:
        Dictionary with subtitle information:
        {
            'manual': [{'lang': 'en', 'name': 'English'}, ...],
            'auto': [{'lang': 'pt', 'name': 'Portuguese (auto-generated)'}, ...]
        }

    Raises:
        SubtitleDownloadError: If listing fails
    """
    try:
        # Ensure it's a full URL
        if not video_url.startswith('http'):
            video_url = f"https://www.youtube.com/watch?v={video_url}"

        command = [
            'yt-dlp',
            '--list-subs',
            '--skip-download',
            '--no-warnings',
            video_url
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )

        # Parse output to extract subtitle information
        subtitles = {'manual': [], 'auto': []}

        output_lines = result.stdout.split('\n')
        current_section = None

        for line in output_lines:
            line = line.strip()

            # Detect subtitle sections
            if 'Available subtitles' in line or 'manual' in line.lower():
                current_section = 'manual'
            elif 'auto-generated' in line.lower() or 'automatic captions' in line.lower():
                current_section = 'auto'

            # Parse subtitle entries (format: "en    English")
            if current_section and line and not line.startswith('[') and not 'Available' in line:
                # Split by whitespace, first part is language code
                parts = line.split()
                if len(parts) >= 2 and len(parts[0]) <= 5:  # Language codes are short
                    lang_code = parts[0]
                    lang_name = ' '.join(parts[1:])

                    subtitles[current_section].append({
                        'lang': lang_code,
                        'name': lang_name
                    })

        logger.info(f"Found {len(subtitles['manual'])} manual and {len(subtitles['auto'])} auto-generated subtitles")
        return subtitles

    except subprocess.TimeoutExpired:
        raise SubtitleDownloadError("Timeout listing available subtitles")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise SubtitleDownloadError(f"Failed to list subtitles: {error_msg}")
    except Exception as e:
        raise SubtitleDownloadError(f"Error listing subtitles: {e}")


def download_subtitle(
    video_url: str,
    video_id: str,
    language: str,
    subtitles_path: Path,
    format: str = 'vtt',
    auto_generated: bool = True,
    timeout: int = 60
) -> Path:
    """
    Download subtitle for a YouTube video

    Args:
        video_url: YouTube video URL or video ID
        video_id: Video ID (for filename)
        language: Language code (e.g., 'en', 'pt', 'es')
        subtitles_path: Directory to save subtitles
        format: Subtitle format ('vtt' or 'srt')
        auto_generated: Allow auto-generated subtitles if manual not available
        timeout: Download timeout in seconds

    Returns:
        Path to downloaded subtitle file

    Raises:
        SubtitleDownloadError: If download fails
    """
    video_id = sanitize_video_id(video_id)

    # Ensure it's a full URL
    if not video_url.startswith('http'):
        video_url = f"https://www.youtube.com/watch?v={video_url}"

    # Determine file extension
    extension = f'.{format}'
    output_path = get_subtitle_path(video_id, language, subtitles_path, extension)

    # Build yt-dlp command
    command = [
        'yt-dlp',
        '--write-sub',
        '--sub-lang', language,
        '--sub-format', format,
        '--skip-download',
        '--output', str(subtitles_path / f"{video_id}"),
        '--no-warnings',
        video_url
    ]

    # Add auto-generated flag if enabled
    if auto_generated:
        command.insert(2, '--write-auto-sub')

    logger.info(f"Downloading {language} subtitle: {video_url} -> {output_path}")

    try:
        result = subprocess.run(
            command,
            timeout=timeout,
            capture_output=True,
            text=True,
            check=True
        )

        # yt-dlp saves with format: {video_id}.{lang}.{format}
        actual_path = subtitles_path / f"{video_id}.{language}.{format}"

        # Check if file was created
        if not actual_path.exists():
            raise SubtitleDownloadError(
                f"Subtitle file not created. Language '{language}' may not be available."
            )

        # Rename to our standard format if different
        if actual_path != output_path:
            actual_path.rename(output_path)

        file_size = output_path.stat().st_size
        logger.info(f"Subtitle downloaded: {output_path} ({file_size / 1024:.1f}KB)")

        return output_path

    except subprocess.TimeoutExpired:
        raise SubtitleDownloadError(f"Subtitle download timeout after {timeout} seconds")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise SubtitleDownloadError(f"Subtitle download failed: {error_msg}")
    except Exception as e:
        raise SubtitleDownloadError(f"Error downloading subtitle: {e}")


def download_all_subtitles(
    video_url: str,
    video_id: str,
    subtitles_path: Path,
    format: str = 'vtt',
    languages: Optional[List[str]] = None,
    auto_generated: bool = True,
    timeout: int = 120
) -> Dict[str, Path]:
    """
    Download multiple subtitles for a video

    Args:
        video_url: YouTube video URL or video ID
        video_id: Video ID (for filename)
        subtitles_path: Directory to save subtitles
        format: Subtitle format ('vtt' or 'srt')
        languages: List of language codes to download (None = all available)
        auto_generated: Allow auto-generated subtitles
        timeout: Download timeout in seconds

    Returns:
        Dictionary mapping language codes to downloaded file paths
        Example: {'en': Path('/path/to/video_en.vtt'), 'pt': Path('/path/to/video_pt.vtt')}

    Raises:
        SubtitleDownloadError: If download fails
    """
    video_id = sanitize_video_id(video_id)

    # Ensure it's a full URL
    if not video_url.startswith('http'):
        video_url = f"https://www.youtube.com/watch?v={video_url}"

    # List available subtitles first
    available = list_available_subtitles(video_url)
    all_available = available['manual'] + (available['auto'] if auto_generated else [])

    if not all_available:
        raise SubtitleDownloadError("No subtitles available for this video")

    # Determine which languages to download
    if languages:
        # Filter to requested languages
        available_langs = {sub['lang'] for sub in all_available}
        languages_to_download = [lang for lang in languages if lang in available_langs]

        if not languages_to_download:
            raise SubtitleDownloadError(
                f"None of the requested languages {languages} are available. "
                f"Available: {list(available_langs)}"
            )
    else:
        # Download all available
        languages_to_download = [sub['lang'] for sub in all_available]

    logger.info(f"Downloading subtitles for languages: {languages_to_download}")

    # Download each subtitle
    downloaded = {}
    errors = []

    for lang in languages_to_download:
        try:
            subtitle_path = download_subtitle(
                video_url=video_url,
                video_id=video_id,
                language=lang,
                subtitles_path=subtitles_path,
                format=format,
                auto_generated=auto_generated,
                timeout=timeout
            )
            downloaded[lang] = subtitle_path
        except SubtitleDownloadError as e:
            logger.warning(f"Failed to download {lang} subtitle: {e}")
            errors.append({'lang': lang, 'error': str(e)})

    if not downloaded:
        raise SubtitleDownloadError(
            f"Failed to download any subtitles. Errors: {errors}"
        )

    logger.info(f"Successfully downloaded {len(downloaded)} subtitle(s)")
    return downloaded


def parse_vtt_subtitle(subtitle_path: Path) -> List[Dict]:
    """
    Parse VTT subtitle file into structured data

    Args:
        subtitle_path: Path to VTT subtitle file

    Returns:
        List of subtitle segments:
        [
            {
                'index': 0,
                'start': '00:00:00.000',
                'end': '00:00:03.000',
                'start_seconds': 0.0,
                'end_seconds': 3.0,
                'text': 'Subtitle text'
            },
            ...
        ]

    Raises:
        SubtitleDownloadError: If parsing fails
    """
    if not subtitle_path.exists():
        raise SubtitleDownloadError(f"Subtitle file not found: {subtitle_path}")

    try:
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            content = f.read()

        segments = []
        lines = content.split('\n')

        i = 0
        segment_index = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip WEBVTT header and empty lines
            if not line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
                i += 1
                continue

            # Look for timestamp line (format: 00:00:00.000 --> 00:00:03.000)
            if '-->' in line:
                try:
                    # Parse timestamps
                    parts = line.split('-->')
                    start_time = parts[0].strip()
                    end_time = parts[1].strip().split()[0]  # Remove any additional metadata

                    # Collect text lines until next timestamp or empty line
                    text_lines = []
                    i += 1
                    while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                        text_lines.append(lines[i].strip())
                        i += 1

                    text = ' '.join(text_lines)

                    # Convert timestamps to seconds
                    start_seconds = _timestamp_to_seconds(start_time)
                    end_seconds = _timestamp_to_seconds(end_time)

                    segments.append({
                        'index': segment_index,
                        'start': start_time,
                        'end': end_time,
                        'start_seconds': start_seconds,
                        'end_seconds': end_seconds,
                        'text': text
                    })

                    segment_index += 1
                except Exception as e:
                    logger.warning(f"Failed to parse subtitle segment: {e}")
                    i += 1
            else:
                i += 1

        logger.info(f"Parsed {len(segments)} subtitle segments from {subtitle_path}")
        return segments

    except Exception as e:
        raise SubtitleDownloadError(f"Error parsing VTT file: {e}")


def _timestamp_to_seconds(timestamp: str) -> float:
    """
    Convert VTT timestamp to seconds

    Args:
        timestamp: Timestamp string (HH:MM:SS.mmm or MM:SS.mmm)

    Returns:
        Time in seconds
    """
    parts = timestamp.split(':')

    if len(parts) == 3:
        # HH:MM:SS.mmm
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:
        # MM:SS.mmm
        minutes = float(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    else:
        return 0.0


def export_subtitle_to_text(
    subtitle_path: Path,
    output_path: Optional[Path] = None,
    include_timestamps: bool = False
) -> Path:
    """
    Export subtitle to plain text format

    Args:
        subtitle_path: Path to subtitle file (VTT)
        output_path: Output text file path (optional)
        include_timestamps: Whether to include timestamps in output

    Returns:
        Path to exported text file
    """
    if output_path is None:
        output_path = subtitle_path.with_suffix('.txt')

    segments = parse_vtt_subtitle(subtitle_path)

    lines = []
    for segment in segments:
        if include_timestamps:
            lines.append(f"[{segment['start']} --> {segment['end']}]")
        lines.append(segment['text'])
        lines.append('')  # Empty line between segments

    text_content = '\n'.join(lines)
    output_path.write_text(text_content, encoding='utf-8')

    logger.info(f"Exported subtitle to text: {output_path}")
    return output_path


def export_subtitle_to_markdown(
    video_id: str,
    subtitle_path: Path,
    output_path: Optional[Path] = None,
    video_title: Optional[str] = None,
    language: Optional[str] = None
) -> Path:
    """
    Export subtitle to markdown format with metadata

    Args:
        video_id: YouTube video ID
        subtitle_path: Path to subtitle file (VTT)
        output_path: Output markdown file path (optional)
        video_title: Video title for header (optional)
        language: Language name (optional)

    Returns:
        Path to exported markdown file
    """
    if output_path is None:
        output_path = subtitle_path.with_suffix('.md')

    segments = parse_vtt_subtitle(subtitle_path)

    lines = []

    # Header
    title = video_title or f"Video {video_id}"
    lines.append(f"# Subtitle: {title}")
    lines.append("")

    # Metadata
    lines.append("## Metadata")
    lines.append("")
    lines.append(f"- **Video ID:** {video_id}")
    lines.append(f"- **Video URL:** https://www.youtube.com/watch?v={video_id}")
    if language:
        lines.append(f"- **Language:** {language}")
    lines.append(f"- **Total segments:** {len(segments)}")
    if segments:
        duration = segments[-1]['end_seconds']
        lines.append(f"- **Duration:** {_format_duration(duration)}")
    lines.append(f"- **Downloaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Content
    lines.append("## Subtitle Text")
    lines.append("")

    for segment in segments:
        lines.append(f"**[{segment['start']} - {segment['end']}]**")
        lines.append(segment['text'])
        lines.append("")

    # Full text
    lines.append("---")
    lines.append("")
    lines.append("## Full Text")
    lines.append("")
    full_text = ' '.join(seg['text'] for seg in segments)
    lines.append(full_text)
    lines.append("")

    markdown_content = '\n'.join(lines)
    output_path.write_text(markdown_content, encoding='utf-8')

    logger.info(f"Exported subtitle to markdown: {output_path}")
    return output_path


def _format_duration(seconds: float) -> str:
    """
    Format duration in seconds to HH:MM:SS

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def get_subtitle_metadata(subtitle_path: Path) -> Dict:
    """
    Get metadata about a subtitle file

    Args:
        subtitle_path: Path to subtitle file

    Returns:
        Dictionary with metadata:
        {
            'file_size_kb': float,
            'segment_count': int,
            'duration_seconds': float,
            'duration_formatted': str,
            'language': str (from filename)
        }
    """
    if not subtitle_path.exists():
        raise SubtitleDownloadError(f"Subtitle file not found: {subtitle_path}")

    segments = parse_vtt_subtitle(subtitle_path)

    # Extract language from filename (format: videoId_lang.vtt)
    filename = subtitle_path.stem
    parts = filename.split('_')
    language = parts[-1] if len(parts) > 1 else 'unknown'

    duration = segments[-1]['end_seconds'] if segments else 0.0

    return {
        'file_size_kb': round(subtitle_path.stat().st_size / 1024, 2),
        'segment_count': len(segments),
        'duration_seconds': duration,
        'duration_formatted': _format_duration(duration),
        'language': language
    }