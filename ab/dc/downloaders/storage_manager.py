"""
Storage Manager for Video Clipper Service
Handles file paths, directory creation, and storage operations
"""

import os
import re
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def sanitize_video_id(video_id: str) -> str:
    """
    Sanitize video ID to prevent directory traversal attacks

    Args:
        video_id: YouTube video ID

    Returns:
        Sanitized video ID (alphanumeric, dash, underscore only)

    Raises:
        ValueError: If video_id is invalid
    """
    if not video_id:
        raise ValueError("video_id cannot be empty")

    # YouTube video IDs are 11 characters: alphanumeric, dash, underscore
    if not re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
        raise ValueError(f"Invalid video ID format: {video_id}")

    return video_id


def create_video_directory(video_id: str, base_path: Path) -> Path:
    """
    Create directory for storing video clips

    Args:
        video_id: YouTube video ID
        base_path: Base path for processed videos

    Returns:
        Path to created directory

    Raises:
        ValueError: If video_id is invalid
        OSError: If directory cannot be created
    """
    video_id = sanitize_video_id(video_id)
    video_dir = base_path / video_id

    try:
        video_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {video_dir}")
        return video_dir
    except OSError as e:
        logger.error(f"Failed to create directory {video_dir}: {e}")
        raise


def get_video_path(video_id: str, base_path: Path, extension: str = '.mp4') -> Path:
    """
    Get path for downloaded video file

    Args:
        video_id: YouTube video ID
        base_path: Base path for downloads
        extension: File extension (default: .mp4)

    Returns:
        Path to video file
    """
    video_id = sanitize_video_id(video_id)
    return base_path / f"{video_id}{extension}"


def get_clip_path(
    video_id: str,
    clip_number: int,
    duration: float,
    base_path: Path,
    score: float = 0.0,
    aspect_ratio: str = 'original'
) -> Path:
    """
    Generate file path for a clip

    Args:
        video_id: YouTube video ID
        clip_number: Clip index (0-based)
        duration: Clip duration in seconds
        base_path: Base path for processed videos
        score: Engagement score for the clip (optional)
        aspect_ratio: Aspect ratio of the clip (optional)

    Returns:
        Full path to clip file

    Format: {video_id}/{video_id}_{clip_number:04d}_{duration}s_score_{score}_{ratio}.mp4
    Example: RusBe_8arLQ/RusBe_8arLQ_0000_30s_score_095_9x16.mp4
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

    filename = f"{video_id}_{clip_number:04d}_{duration_str}_{score_str}_{ratio_str}.mp4"
    return video_dir / filename


def is_video_downloaded(video_id: str, downloads_path: Path) -> bool:
    """
    Check if video file already exists

    Args:
        video_id: YouTube video ID
        downloads_path: Path to downloads directory

    Returns:
        True if video exists, False otherwise
    """
    try:
        video_path = get_video_path(video_id, downloads_path)
        exists = video_path.exists() and video_path.is_file()

        if exists:
            # Check if file is not empty
            file_size = video_path.stat().st_size
            if file_size == 0:
                logger.warning(f"Video file exists but is empty: {video_path}")
                return False

            logger.info(f"Video already downloaded: {video_path} ({file_size / 1024 / 1024:.1f}MB)")
            return True

        return False
    except Exception as e:
        logger.error(f"Error checking if video downloaded: {e}")
        return False


def calculate_file_size_mb(file_path: Path) -> float:
    """
    Calculate file size in megabytes

    Args:
        file_path: Path to file

    Returns:
        File size in MB (rounded to 2 decimals)
    """
    try:
        if not file_path.exists():
            return 0.0
        size_bytes = file_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    except Exception as e:
        logger.error(f"Error calculating file size for {file_path}: {e}")
        return 0.0


def calculate_directory_size(directory: Path) -> float:
    """
    Calculate total size of all files in directory

    Args:
        directory: Directory path

    Returns:
        Total size in MB (rounded to 2 decimals)
    """
    total_size = 0
    try:
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        size_mb = total_size / (1024 * 1024)
        return round(size_mb, 2)
    except Exception as e:
        logger.error(f"Error calculating directory size for {directory}: {e}")
        return 0.0


def cleanup_old_clips(video_id: str, base_path: Path) -> bool:
    """
    Remove all existing clips for a video (for re-processing)

    Args:
        video_id: YouTube video ID
        base_path: Base path for processed videos

    Returns:
        True if successful, False otherwise
    """
    try:
        video_id = sanitize_video_id(video_id)
        video_dir = base_path / video_id

        if not video_dir.exists():
            logger.info(f"No existing clips to clean up for {video_id}")
            return True

        # Count and remove clip files
        clip_count = 0
        for clip_file in video_dir.glob(f"{video_id}_*.mp4"):
            try:
                clip_file.unlink()
                clip_count += 1
            except Exception as e:
                logger.error(f"Failed to delete clip {clip_file}: {e}")
                return False

        logger.info(f"Cleaned up {clip_count} existing clips for {video_id}")
        return True

    except Exception as e:
        logger.error(f"Error during cleanup for {video_id}: {e}")
        return False


def get_available_disk_space(path: Path) -> float:
    """
    Get available disk space for a path

    Args:
        path: Directory path to check

    Returns:
        Available space in MB
    """
    try:
        stat = os.statvfs(path)
        available_bytes = stat.f_bavail * stat.f_frsize
        available_mb = available_bytes / (1024 * 1024)
        return round(available_mb, 2)
    except Exception as e:
        logger.error(f"Error getting disk space for {path}: {e}")
        return 0.0


def check_disk_space(
    path: Path,
    required_mb: float,
    buffer_mb: float = 1024
) -> tuple[bool, str]:
    """
    Check if there's enough disk space

    Args:
        path: Path to check
        required_mb: Required space in MB
        buffer_mb: Extra buffer space to keep free (default: 1GB)

    Returns:
        Tuple of (has_space, message)
    """
    try:
        available = get_available_disk_space(path)
        needed = required_mb + buffer_mb

        if available >= needed:
            return True, f"Sufficient disk space: {available:.1f}MB available"
        else:
            return False, (
                f"Insufficient disk space: {available:.1f}MB available, "
                f"{needed:.1f}MB needed (including {buffer_mb}MB buffer)"
            )
    except Exception as e:
        return False, f"Error checking disk space: {e}"


def list_video_clips(video_id: str, base_path: Path) -> list[Path]:
    """
    List all clip files for a video

    Args:
        video_id: YouTube video ID
        base_path: Base path for processed videos

    Returns:
        List of clip file paths
    """
    try:
        video_id = sanitize_video_id(video_id)
        video_dir = base_path / video_id

        if not video_dir.exists():
            return []

        clips = sorted(video_dir.glob(f"{video_id}_*.mp4"))
        return clips
    except Exception as e:
        logger.error(f"Error listing clips for {video_id}: {e}")
        return []


def validate_path_safety(path: Path, allowed_base: Path) -> bool:
    """
    Validate that a path is within allowed base directory (prevent traversal)

    Args:
        path: Path to validate
        allowed_base: Allowed base directory

    Returns:
        True if path is safe, False otherwise
    """
    try:
        # Resolve to absolute paths
        path_resolved = path.resolve()
        base_resolved = allowed_base.resolve()

        # Check if path is within base
        return str(path_resolved).startswith(str(base_resolved))
    except Exception as e:
        logger.error(f"Error validating path safety: {e}")
        return False