"""
Subtitle Clipper Service
Generates subtitle files for each clip/moment based on popular moments extraction
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import timedelta

# Add parent directories to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent / 'analysers'))

from subtitle_downloader import (
    download_subtitle,
    download_all_subtitles,
    parse_vtt_subtitle,
    SubtitleDownloadError
)
from storage_manager import sanitize_video_id, create_video_directory

logger = logging.getLogger(__name__)


class SubtitleClipperError(Exception):
    """Custom exception for subtitle clipper failures"""
    pass


def get_clip_subtitle_path(
    video_id: str,
    clip_number: int,
    duration: float,
    base_path: Path,
    score: float = 0.0,
    aspect_ratio: str = 'original',
    language: str = 'en',
    extension: str = '.vtt'
) -> Path:
    """
    Generate file path for a clip subtitle file (same naming as video clips)

    Args:
        video_id: YouTube video ID
        clip_number: Clip index (0-based)
        duration: Clip duration in seconds
        base_path: Base path for processed videos
        score: Engagement score for the clip (optional)
        aspect_ratio: Aspect ratio of the clip (optional)
        language: Language code (e.g., 'en', 'pt')
        extension: File extension (default: .vtt)

    Returns:
        Full path to clip subtitle file

    Format: {video_id}/{video_id}_{clip_number:04d}_{duration}s_score_{score}_{ratio}_{lang}.vtt
    Example: RusBe_8arLQ/RusBe_8arLQ_0000_30s_score_095_9x16_en.vtt
    """
    video_id = sanitize_video_id(video_id)
    video_dir = base_path / video_id

    # Format duration as integer if whole number, else one decimal
    if duration == int(duration):
        duration_str = f"{int(duration)}s"
    else:
        duration_str = f"{duration:.1f}s"

    # Format score as integer by multiplying by 100 (0.95 -> 095, 1.06 -> 106)
    score_int = int(score * 100)
    score_str = f"score_{score_int:03d}"

    # Format aspect ratio (9:16 -> 9x16, original -> original)
    if aspect_ratio == 'original':
        ratio_str = 'original'
    else:
        ratio_str = aspect_ratio.replace(':', 'x')

    filename = f"{video_id}_{clip_number:04d}_{duration_str}_{score_str}_{ratio_str}_{language}{extension}"
    return video_dir / filename


def filter_subtitle_segments(
    segments: List[Dict],
    start_time: float,
    end_time: float
) -> List[Dict]:
    """
    Filter subtitle segments to only include those within time range

    Args:
        segments: List of subtitle segments from parse_vtt_subtitle()
        start_time: Start time in seconds
        end_time: End time in seconds

    Returns:
        List of segments within the time range, with adjusted timestamps
    """
    filtered = []

    for segment in segments:
        seg_start = segment['start_seconds']
        seg_end = segment['end_seconds']

        # Skip segments completely outside the range
        if seg_end <= start_time or seg_start >= end_time:
            continue

        # Adjust timestamps relative to clip start
        adjusted_start = max(0, seg_start - start_time)
        adjusted_end = min(end_time - start_time, seg_end - start_time)

        # Create adjusted segment
        filtered.append({
            'index': len(filtered),
            'start': _seconds_to_vtt_timestamp(adjusted_start),
            'end': _seconds_to_vtt_timestamp(adjusted_end),
            'start_seconds': adjusted_start,
            'end_seconds': adjusted_end,
            'text': segment['text']
        })

    return filtered


def _seconds_to_vtt_timestamp(seconds: float) -> str:
    """
    Convert seconds to VTT timestamp format (HH:MM:SS.mmm)

    Args:
        seconds: Time in seconds

    Returns:
        VTT formatted timestamp
    """
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"


def generate_vtt_content(segments: List[Dict]) -> str:
    """
    Generate VTT file content from segments

    Args:
        segments: List of subtitle segments with adjusted timestamps

    Returns:
        VTT file content as string
    """
    lines = ["WEBVTT", ""]

    for segment in segments:
        lines.append(f"{segment['start']} --> {segment['end']}")
        lines.append(segment['text'])
        lines.append("")

    return "\n".join(lines)


def generate_srt_content(segments: List[Dict]) -> str:
    """
    Generate SRT file content from segments

    Args:
        segments: List of subtitle segments with adjusted timestamps

    Returns:
        SRT file content as string
    """
    lines = []

    for i, segment in enumerate(segments, 1):
        # SRT uses comma instead of dot for milliseconds
        start = segment['start'].replace('.', ',')
        end = segment['end'].replace('.', ',')

        lines.append(str(i))
        lines.append(f"{start} --> {end}")
        lines.append(segment['text'])
        lines.append("")

    return "\n".join(lines)


def create_clip_subtitle(
    video_id: str,
    full_subtitle_path: Path,
    clip_number: int,
    start_time: float,
    end_time: float,
    score: float,
    output_dir: Path,
    language: str = 'en',
    aspect_ratio: str = 'original',
    format: str = 'vtt'
) -> Path:
    """
    Create subtitle file for a single clip

    Args:
        video_id: YouTube video ID
        full_subtitle_path: Path to full video subtitle file
        clip_number: Clip index (0-based)
        start_time: Clip start time in seconds
        end_time: Clip end time in seconds
        score: Engagement score for the clip
        output_dir: Output directory for clip subtitles
        language: Language code (e.g., 'en', 'pt')
        aspect_ratio: Aspect ratio of the clip
        format: Subtitle format ('vtt' or 'srt')

    Returns:
        Path to created clip subtitle file

    Raises:
        SubtitleClipperError: If subtitle creation fails
    """
    try:
        # Parse full subtitle
        segments = parse_vtt_subtitle(full_subtitle_path)

        # Filter segments for this clip
        clip_segments = filter_subtitle_segments(segments, start_time, end_time)

        if not clip_segments:
            logger.warning(
                f"No subtitle segments found for clip {clip_number} "
                f"({start_time:.1f}s - {end_time:.1f}s)"
            )
            # Return empty subtitle file
            clip_segments = []

        # Generate subtitle content
        duration = end_time - start_time
        extension = f'.{format}'

        if format == 'srt':
            content = generate_srt_content(clip_segments)
        else:
            content = generate_vtt_content(clip_segments)

        # Get output path
        clip_subtitle_path = get_clip_subtitle_path(
            video_id=video_id,
            clip_number=clip_number,
            duration=duration,
            base_path=output_dir,
            score=score,
            aspect_ratio=aspect_ratio,
            language=language,
            extension=extension
        )

        # Ensure directory exists
        clip_subtitle_path.parent.mkdir(parents=True, exist_ok=True)

        # Write subtitle file
        clip_subtitle_path.write_text(content, encoding='utf-8')

        logger.info(
            f"Created clip subtitle: {clip_subtitle_path} "
            f"({len(clip_segments)} segments)"
        )

        return clip_subtitle_path

    except Exception as e:
        raise SubtitleClipperError(f"Failed to create clip subtitle: {e}")


def process_moments_subtitles(
    moments_data: Dict,
    subtitles_download_path: Path = Path("./subtitles"),
    clips_output_path: Path = Path("./processed_videos"),
    languages: Optional[List[str]] = None,
    format: str = 'vtt',
    aspect_ratio: str = 'original',
    force_redownload: bool = False
) -> Dict:
    """
    Main service function to generate subtitle files for all clips/moments

    Args:
        moments_data: Dictionary from get_popular_moments() containing:
            - video_id: YouTube video ID
            - video_url: YouTube video URL
            - moments: List of moments with start_time, end_time, score
        subtitles_download_path: Directory to download full video subtitles
        clips_output_path: Directory to save clip subtitle files
        languages: List of language codes to process (default: ['en'])
        format: Subtitle format ('vtt' or 'srt')
        aspect_ratio: Aspect ratio used for clip naming
        force_redownload: Force re-download of subtitle even if exists

    Returns:
        Dictionary with structure:
        {
            "success": bool,
            "video_id": str,
            "video_url": str,
            "languages_processed": List[str],
            "total_clips": int,
            "clip_subtitles": [
                {
                    "clip_id": int,
                    "language": str,
                    "path": str,
                    "segments_count": int,
                    "start_time": float,
                    "end_time": float,
                    "duration": float
                },
                ...
            ],
            "processing_time": float,
            "error": str (only if success=False)
        }
    """
    import time
    start_time = time.time()

    try:
        # Validate input
        if not moments_data.get('success'):
            return {
                "success": False,
                "error": f"Moments extraction failed: {moments_data.get('error')}",
                "video_id": moments_data.get('video_id'),
                "video_url": moments_data.get('video_url'),
                "languages_processed": [],
                "total_clips": 0,
                "clip_subtitles": [],
                "processing_time": 0
            }

        video_id = moments_data['video_id']
        video_url = moments_data['video_url']
        moments = moments_data['moments']

        if not moments:
            return {
                "success": False,
                "error": "No moments found in input data",
                "video_id": video_id,
                "video_url": video_url,
                "languages_processed": [],
                "total_clips": 0,
                "clip_subtitles": [],
                "processing_time": time.time() - start_time
            }

        # Default to English if no languages specified
        if languages is None:
            languages = ['en']

        logger.info(
            f"Processing subtitles for {len(moments)} clips in {len(languages)} language(s)"
        )

        # Create output directory
        create_video_directory(video_id, clips_output_path)

        # Process each language
        all_clip_subtitles = []
        languages_processed = []

        for language in languages:
            try:
                # Download full video subtitle
                subtitle_path = subtitles_download_path / f"{video_id}_{language}.{format}"

                if force_redownload or not subtitle_path.exists():
                    logger.info(f"Downloading {language} subtitle for video {video_id}")
                    subtitle_path = download_subtitle(
                        video_url=video_url,
                        video_id=video_id,
                        language=language,
                        subtitles_path=subtitles_download_path,
                        format=format,
                        auto_generated=True
                    )
                else:
                    logger.info(f"Using existing {language} subtitle: {subtitle_path}")

                # Create clip subtitles for each moment
                for i, moment in enumerate(moments):
                    try:
                        clip_subtitle_path = create_clip_subtitle(
                            video_id=video_id,
                            full_subtitle_path=subtitle_path,
                            clip_number=i,
                            start_time=moment['start_time'],
                            end_time=moment['end_time'],
                            score=moment['score'],
                            output_dir=clips_output_path,
                            language=language,
                            aspect_ratio=aspect_ratio,
                            format=format
                        )

                        # Parse to get segment count
                        segments = parse_vtt_subtitle(clip_subtitle_path) if format == 'vtt' else []

                        all_clip_subtitles.append({
                            "clip_id": i,
                            "language": language,
                            "path": str(clip_subtitle_path),
                            "filename": clip_subtitle_path.name,
                            "segments_count": len(segments),
                            "start_time": moment['start_time'],
                            "end_time": moment['end_time'],
                            "duration": moment['duration']
                        })

                    except SubtitleClipperError as e:
                        logger.error(f"Failed to create subtitle for clip {i} ({language}): {e}")
                        continue

                languages_processed.append(language)

            except SubtitleDownloadError as e:
                logger.error(f"Failed to download {language} subtitle: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing {language} subtitles: {e}")
                continue

        if not languages_processed:
            return {
                "success": False,
                "error": "Failed to process subtitles for any language",
                "video_id": video_id,
                "video_url": video_url,
                "languages_processed": [],
                "total_clips": 0,
                "clip_subtitles": [],
                "processing_time": time.time() - start_time
            }

        return {
            "success": True,
            "video_id": video_id,
            "video_url": video_url,
            "languages_processed": languages_processed,
            "total_clips": len(moments),
            "clip_subtitles_created": len(all_clip_subtitles),
            "clip_subtitles": all_clip_subtitles,
            "processing_time": round(time.time() - start_time, 2),
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "video_id": moments_data.get('video_id') if moments_data else None,
            "video_url": moments_data.get('video_url') if moments_data else None,
            "languages_processed": [],
            "total_clips": 0,
            "clip_subtitles": [],
            "processing_time": time.time() - start_time if 'start_time' in locals() else 0
        }


def extract_and_generate_subtitles(
    video_url_or_id: str,
    languages: Optional[List[str]] = None,
    max_duration: int = 40,
    min_duration: int = 10,
    threshold: float = 0.45,
    format: str = 'vtt',
    aspect_ratio: str = 'original',
    subtitles_download_path: Path = Path("./subtitles"),
    clips_output_path: Path = Path("./processed_videos")
) -> Dict:
    """
    Complete workflow: extract moments and generate clip subtitles

    Args:
        video_url_or_id: YouTube URL or video ID
        languages: List of language codes (default: ['en'])
        max_duration: Maximum moment duration in seconds
        min_duration: Minimum moment duration in seconds
        threshold: Minimum relative value for peak detection
        format: Subtitle format ('vtt' or 'srt')
        aspect_ratio: Aspect ratio for clip naming
        subtitles_download_path: Directory to download full video subtitles
        clips_output_path: Directory to save clip subtitle files

    Returns:
        Dictionary with complete results
    """
    try:
        from replay_heatmap import get_popular_moments

        logger.info(f"Extracting popular moments from: {video_url_or_id}")

        # Extract moments
        moments_result = get_popular_moments(
            url_or_video_id=video_url_or_id,
            max_duration=max_duration,
            min_duration=min_duration,
            threshold=threshold
        )

        if not moments_result['success']:
            return {
                "success": False,
                "error": f"Failed to extract moments: {moments_result['error']}",
                "video_id": moments_result.get('video_id'),
                "video_url": moments_result.get('video_url'),
                "moments_extracted": 0,
                "languages_processed": [],
                "total_clips": 0,
                "clip_subtitles": []
            }

        logger.info(f"Found {moments_result['total_moments']} popular moments")

        # Generate clip subtitles
        result = process_moments_subtitles(
            moments_data=moments_result,
            subtitles_download_path=subtitles_download_path,
            clips_output_path=clips_output_path,
            languages=languages,
            format=format,
            aspect_ratio=aspect_ratio
        )

        # Add moments extraction info
        result['moments_extracted'] = moments_result['total_moments']
        result['moments'] = moments_result['moments']

        return result

    except ImportError:
        return {
            "success": False,
            "error": "replay_heatmap module not found",
            "video_id": None,
            "video_url": None,
            "moments_extracted": 0,
            "languages_processed": [],
            "total_clips": 0,
            "clip_subtitles": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "video_id": None,
            "video_url": None,
            "moments_extracted": 0,
            "languages_processed": [],
            "total_clips": 0,
            "clip_subtitles": []
        }