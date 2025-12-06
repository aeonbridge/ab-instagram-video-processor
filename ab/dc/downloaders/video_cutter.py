"""
Video Cutter for Video Clipper Service
Handles cutting video segments using FFmpeg
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)


class CuttingError(Exception):
    """Custom exception for video cutting failures"""
    pass


def _get_aspect_ratio_filter(aspect_ratio: str) -> Optional[str]:
    """
    Get FFmpeg filter for aspect ratio conversion

    Args:
        aspect_ratio: Target aspect ratio (original, 9:16, 16:9, 1:1, 4:5)

    Returns:
        FFmpeg video filter string or None for original

    Supported ratios:
        - original: No conversion, keep source aspect ratio
        - 9:16: Vertical (Instagram Reels, TikTok, YouTube Shorts) 1080x1920
        - 16:9: Horizontal (YouTube, standard widescreen) 1920x1080
        - 1:1: Square (Instagram feed) 1080x1080
        - 4:5: Portrait (Instagram portrait) 1080x1350
    """
    if aspect_ratio == 'original':
        return None

    # Map aspect ratios to dimensions and filter logic
    aspect_configs = {
        '9:16': {
            'width': 1080,
            'height': 1920,
            'crop': 'crop=ih*9/16:ih'  # Crop to 9:16, center horizontally
        },
        '16:9': {
            'width': 1920,
            'height': 1080,
            'crop': 'crop=iw:iw*9/16'  # Crop to 16:9, center vertically
        },
        '1:1': {
            'width': 1080,
            'height': 1080,
            'crop': 'crop=min(iw\\,ih):min(iw\\,ih)'  # Crop to square, centered
        },
        '4:5': {
            'width': 1080,
            'height': 1350,
            'crop': 'crop=ih*4/5:ih'  # Crop to 4:5, center horizontally
        }
    }

    if aspect_ratio not in aspect_configs:
        logger.warning(f"Unknown aspect ratio '{aspect_ratio}', using original")
        return None

    config = aspect_configs[aspect_ratio]

    # Build filter: crop first, then scale to target dimensions
    vf = f"{config['crop']},scale={config['width']}:{config['height']}"

    return vf


def cut_video_segment(
    input_path: Path,
    output_path: Path,
    start_time: float,
    end_time: float,
    video_codec: str = 'libx264',
    audio_codec: str = 'aac',
    crf: int = 23,
    preset: str = 'medium',
    include_audio: bool = True,
    aspect_ratio: str = 'original',
    ffmpeg_path: str = 'ffmpeg',
    timeout: int = 600
) -> bool:
    """
    Cut a single video segment using FFmpeg

    Args:
        input_path: Path to input video
        output_path: Path for output clip
        start_time: Start time in seconds
        end_time: End time in seconds
        video_codec: Video codec (libx264, libx265, copy)
        audio_codec: Audio codec (aac, mp3, copy)
        crf: Constant Rate Factor for quality (18-28)
        preset: Encoding preset (ultrafast to veryslow)
        include_audio: Whether to include audio
        ffmpeg_path: Path to ffmpeg binary
        timeout: Timeout in seconds

    Returns:
        True if successful, False otherwise

    Raises:
        CuttingError: If cutting fails
    """
    if not input_path.exists():
        raise CuttingError(f"Input video not found: {input_path}")

    if start_time < 0 or end_time < 0:
        raise CuttingError(f"Invalid timestamps: start={start_time}, end={end_time}")

    if start_time >= end_time:
        raise CuttingError(f"Start time ({start_time}) must be less than end time ({end_time})")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    duration = end_time - start_time

    # Check if aspect ratio conversion is needed
    needs_conversion = aspect_ratio != 'original'

    # Build FFmpeg command based on codec settings
    if video_codec == 'copy' and audio_codec == 'copy' and not needs_conversion:
        # Fast stream copy (no re-encoding, no conversion)
        command = _build_stream_copy_command(
            ffmpeg_path, input_path, output_path, start_time, duration
        )
    else:
        # Re-encode with specified codecs (or if aspect ratio conversion needed)
        if video_codec == 'copy' and needs_conversion:
            # Force re-encoding for aspect ratio conversion
            logger.info(f"Forcing re-encoding for aspect ratio conversion: {aspect_ratio}")
            # Try hardware encoder first (macOS VideoToolbox), fallback to libx264
            import platform
            if platform.system() == 'Darwin':
                video_codec = 'h264_videotoolbox'  # macOS hardware encoder
            else:
                video_codec = 'libx264'  # Software encoder

        command = _build_encode_command(
            ffmpeg_path, input_path, output_path,
            start_time, end_time, duration,
            video_codec, audio_codec, crf, preset, include_audio, aspect_ratio
        )

    logger.debug(f"FFmpeg command: {' '.join(command)}")
    logger.info(f"Cutting clip: {start_time:.2f}s - {end_time:.2f}s -> {output_path.name}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )

        # Verify output file was created
        if not output_path.exists():
            raise CuttingError(f"Output file not created: {output_path}")

        file_size = output_path.stat().st_size
        if file_size == 0:
            raise CuttingError("Output file is empty")

        logger.info(f"Clip created: {output_path.name} ({file_size / 1024 / 1024:.1f}MB)")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"FFmpeg timeout after {timeout}s")
        raise CuttingError(f"Cutting timeout after {timeout}s")

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        logger.error(f"FFmpeg error: {error_msg}")
        raise CuttingError(f"FFmpeg failed: {error_msg}")

    except Exception as e:
        logger.error(f"Unexpected error during cutting: {e}")
        raise CuttingError(f"Cutting failed: {e}")


def _build_stream_copy_command(
    ffmpeg_path: str,
    input_path: Path,
    output_path: Path,
    start_time: float,
    duration: float
) -> List[str]:
    """
    Build FFmpeg command for fast stream copy (no re-encoding)

    Args:
        ffmpeg_path: Path to ffmpeg binary
        input_path: Input video path
        output_path: Output clip path
        start_time: Start time in seconds
        duration: Duration in seconds

    Returns:
        FFmpeg command as list of strings
    """
    return [
        ffmpeg_path,
        '-ss', str(start_time),           # Seek to start time
        '-i', str(input_path),            # Input file
        '-t', str(duration),              # Duration
        '-c', 'copy',                     # Copy codecs (no re-encode)
        '-avoid_negative_ts', 'make_zero',  # Handle timestamp issues
        '-y',                              # Overwrite output
        str(output_path)
    ]


def _build_encode_command(
    ffmpeg_path: str,
    input_path: Path,
    output_path: Path,
    start_time: float,
    end_time: float,
    duration: float,
    video_codec: str,
    audio_codec: str,
    crf: int,
    preset: str,
    include_audio: bool,
    aspect_ratio: str = 'original'
) -> List[str]:
    """
    Build FFmpeg command for re-encoding with specified codecs

    Args:
        ffmpeg_path: Path to ffmpeg binary
        input_path: Input video path
        output_path: Output clip path
        start_time: Start time in seconds
        end_time: End time in seconds
        duration: Duration in seconds
        video_codec: Video codec
        audio_codec: Audio codec
        crf: Quality setting
        preset: Encoding preset
        include_audio: Whether to include audio
        aspect_ratio: Target aspect ratio (original, 9:16, 16:9, 1:1, 4:5)

    Returns:
        FFmpeg command as list of strings
    """
    command = [
        ffmpeg_path,
        '-i', str(input_path),            # Input file
        '-ss', str(start_time),           # Start time
        '-to', str(end_time),             # End time
    ]

    # Video codec settings
    if video_codec == 'copy':
        command.extend(['-c:v', 'copy'])
    else:
        command.extend(['-c:v', video_codec])   # Video codec

        # Add CRF only for codecs that support it (libx264, libx265, libvpx, etc.)
        if video_codec in ['libx264', 'libx265', 'libvpx', 'libvpx-vp9']:
            command.extend(['-crf', str(crf)])  # Quality

        # Add preset only for codecs that support it
        if video_codec in ['libx264', 'libx265']:
            command.extend(['-preset', preset])  # Encoding speed

    # Add aspect ratio filter if needed
    aspect_filter = _get_aspect_ratio_filter(aspect_ratio)
    if aspect_filter:
        command.extend(['-vf', aspect_filter])
        logger.info(f"Applying aspect ratio filter: {aspect_ratio} -> {aspect_filter}")

    # Audio codec settings
    if include_audio:
        if audio_codec == 'copy':
            command.extend(['-c:a', 'copy'])
        elif audio_codec == 'aac':
            command.extend([
                '-c:a', 'aac',
                '-b:a', '128k'              # Audio bitrate
            ])
        elif audio_codec == 'mp3':
            command.extend([
                '-c:a', 'libmp3lame',
                '-b:a', '128k'
            ])
        else:
            command.extend(['-c:a', audio_codec])
    else:
        command.extend(['-an'])            # No audio

    # Additional settings
    command.extend([
        '-movflags', '+faststart',         # Enable progressive streaming
        '-y',                               # Overwrite output
        str(output_path)
    ])

    return command


def batch_cut_videos(
    input_path: Path,
    output_dir: Path,
    moments: List[Dict],
    video_id: str,
    parallel: bool = True,
    max_workers: int = 4,
    **ffmpeg_options
) -> List[Dict]:
    """
    Cut multiple video segments (with optional parallel processing)

    Args:
        input_path: Path to input video
        output_dir: Directory for output clips
        moments: List of moment dicts with start_time, end_time, duration
        video_id: Video ID for clip naming
        parallel: Whether to process clips in parallel
        max_workers: Maximum concurrent workers
        **ffmpeg_options: Options to pass to cut_video_segment

    Returns:
        List of clip information dicts

    Each clip dict contains:
        - clip_id: Clip number
        - filename: Clip filename
        - path: Full path to clip
        - start_time: Start time
        - end_time: End time
        - duration: Duration
        - score: Engagement score (from moment)
        - file_size_mb: File size in MB
        - success: Whether cutting succeeded
        - error: Error message if failed
    """
    from storage_manager import get_clip_path, calculate_file_size_mb

    clips_info = []

    if parallel and len(moments) > 1:
        # Parallel processing
        logger.info(f"Processing {len(moments)} clips in parallel (max {max_workers} workers)")
        clips_info = _process_clips_parallel(
            input_path, output_dir, moments, video_id, max_workers, ffmpeg_options
        )
    else:
        # Sequential processing
        logger.info(f"Processing {len(moments)} clips sequentially")
        clips_info = _process_clips_sequential(
            input_path, output_dir, moments, video_id, ffmpeg_options
        )

    return clips_info


def _process_clips_sequential(
    input_path: Path,
    output_dir: Path,
    moments: List[Dict],
    video_id: str,
    ffmpeg_options: Dict
) -> List[Dict]:
    """Process clips sequentially"""
    from storage_manager import get_clip_path, calculate_file_size_mb

    clips_info = []

    for clip_id, moment in enumerate(moments):
        clip_info = _process_single_clip(
            clip_id, moment, input_path, output_dir, video_id, ffmpeg_options
        )
        clips_info.append(clip_info)

    return clips_info


def _process_clips_parallel(
    input_path: Path,
    output_dir: Path,
    moments: List[Dict],
    video_id: str,
    max_workers: int,
    ffmpeg_options: Dict
) -> List[Dict]:
    """Process clips in parallel using ThreadPoolExecutor"""
    clips_info = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                _process_single_clip,
                clip_id, moment, input_path, output_dir, video_id, ffmpeg_options
            ): clip_id
            for clip_id, moment in enumerate(moments)
        }

        # Collect results as they complete
        for future in as_completed(futures):
            clip_id = futures[future]
            try:
                clip_info = future.result()
                clips_info.append(clip_info)
            except Exception as e:
                logger.error(f"Clip {clip_id} processing failed with exception: {e}")
                # Add failed clip info
                clips_info.append({
                    'clip_id': clip_id,
                    'success': False,
                    'error': str(e)
                })

    # Sort by clip_id to maintain order
    clips_info.sort(key=lambda x: x['clip_id'])

    return clips_info


def _process_single_clip(
    clip_id: int,
    moment: Dict,
    input_path: Path,
    output_dir: Path,
    video_id: str,
    ffmpeg_options: Dict
) -> Dict:
    """Process a single clip and return info"""
    from storage_manager import get_clip_path, calculate_file_size_mb

    start_time = moment['start_time']
    end_time = moment['end_time']
    duration = moment['duration']
    score = moment.get('score', 0)
    aspect_ratio = ffmpeg_options.get('aspect_ratio', 'original')

    clip_path = get_clip_path(video_id, clip_id, duration, output_dir, score, aspect_ratio)

    try:
        # Cut the clip
        success = cut_video_segment(
            input_path=input_path,
            output_path=clip_path,
            start_time=start_time,
            end_time=end_time,
            **ffmpeg_options
        )

        file_size_mb = calculate_file_size_mb(clip_path) if success else 0

        return {
            'clip_id': clip_id,
            'filename': clip_path.name,
            'path': str(clip_path),
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'score': score,
            'file_size_mb': file_size_mb,
            'success': True,
            'error': None
        }

    except CuttingError as e:
        logger.error(f"Failed to cut clip {clip_id}: {e}")
        return {
            'clip_id': clip_id,
            'filename': clip_path.name if clip_path else f"clip_{clip_id}.mp4",
            'path': str(clip_path) if clip_path else None,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'score': score,
            'file_size_mb': 0,
            'success': False,
            'error': str(e)
        }


def validate_clip_output(clip_path: Path, min_duration: float = 1.0) -> tuple[bool, str]:
    """
    Validate generated clip

    Args:
        clip_path: Path to clip file
        min_duration: Minimum expected duration in seconds

    Returns:
        Tuple of (is_valid, message)
    """
    if not clip_path.exists():
        return False, "Clip file does not exist"

    file_size = clip_path.stat().st_size
    if file_size == 0:
        return False, "Clip file is empty"

    if file_size < 1024:  # Less than 1KB
        return False, f"Clip file too small: {file_size} bytes"

    # Optionally check duration with ffprobe
    try:
        command = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(clip_path)
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )

        duration = float(result.stdout.strip())
        if duration < min_duration:
            return False, f"Clip duration ({duration}s) too short"

        return True, f"Clip is valid ({duration:.1f}s, {file_size / 1024 / 1024:.1f}MB)"

    except Exception as e:
        # If ffprobe check fails, accept if file exists and has size
        logger.warning(f"Could not validate clip duration: {e}")
        return True, f"Clip file exists ({file_size / 1024 / 1024:.1f}MB)"