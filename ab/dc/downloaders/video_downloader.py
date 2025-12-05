"""
Video Downloader for Video Clipper Service
Handles downloading YouTube videos using yt-dlp
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Optional, Dict
import logging

from storage_manager import get_video_path, sanitize_video_id

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Custom exception for download failures"""
    pass


def download_video(
    video_url: str,
    video_id: str,
    downloads_path: Path,
    quality: str = 'best',
    timeout: int = 600,
    max_retries: int = 3
) -> Path:
    """
    Download YouTube video using yt-dlp

    Args:
        video_url: YouTube video URL
        video_id: Video ID (for filename)
        downloads_path: Directory to save video
        quality: Quality setting (best, 1080p, 720p, 480p, worst)
        timeout: Download timeout in seconds
        max_retries: Maximum number of retry attempts

    Returns:
        Path to downloaded video file

    Raises:
        DownloadError: If download fails after all retries
    """
    video_id = sanitize_video_id(video_id)
    output_path = get_video_path(video_id, downloads_path)

    # Build format string based on quality
    format_str = _build_format_string(quality)

    # yt-dlp command
    command = [
        'yt-dlp',
        '-f', format_str,
        '-o', str(output_path),
        '--merge-output-format', 'mp4',
        '--no-playlist',
        '--no-warnings',
        '--quiet',
        video_url
    ]

    logger.info(f"Downloading video: {video_url} -> {output_path}")

    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                command,
                timeout=timeout,
                capture_output=True,
                text=True,
                check=True
            )

            # Verify file was created and is not empty
            if not output_path.exists():
                raise DownloadError(f"Download completed but file not found: {output_path}")

            file_size = output_path.stat().st_size
            if file_size == 0:
                raise DownloadError("Downloaded file is empty")

            logger.info(f"Download successful: {output_path} ({file_size / 1024 / 1024:.1f}MB)")
            return output_path

        except subprocess.TimeoutExpired:
            logger.warning(f"Download timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise DownloadError(f"Download timeout after {max_retries} attempts")

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"yt-dlp error (attempt {attempt + 1}/{max_retries}): {error_msg}")

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise DownloadError(f"Download failed after {max_retries} attempts: {error_msg}")

        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            raise DownloadError(f"Download failed: {e}")

    raise DownloadError("Download failed: max retries exceeded")


def _build_format_string(quality: str) -> str:
    """
    Build yt-dlp format string based on quality setting

    Args:
        quality: Quality setting (best, 1080p, 720p, 480p, 360p, worst)

    Returns:
        Format string for yt-dlp
    """
    quality_map = {
        'best': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]',
        '720p': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
        '480p': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]',
        '360p': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]',
        'worst': 'worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst'
    }

    return quality_map.get(quality, quality_map['best'])


def get_video_info(video_path: Path) -> Optional[Dict]:
    """
    Get video metadata using ffprobe

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with video metadata or None if failed
        Keys: duration, width, height, codec, fps, bitrate
    """
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return None

    try:
        # Use ffprobe to get video information
        command = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

        data = json.loads(result.stdout)

        # Extract video stream info
        video_stream = next(
            (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
            None
        )

        if not video_stream:
            logger.error("No video stream found in file")
            return None

        # Extract relevant metadata
        format_info = data.get('format', {})

        metadata = {
            'duration': float(format_info.get('duration', 0)),
            'width': int(video_stream.get('width', 0)),
            'height': int(video_stream.get('height', 0)),
            'codec': video_stream.get('codec_name', 'unknown'),
            'fps': eval(video_stream.get('r_frame_rate', '0/1')),  # Evaluates fraction
            'bitrate': int(format_info.get('bit_rate', 0)),
            'size_mb': round(int(format_info.get('size', 0)) / (1024 * 1024), 2)
        }

        logger.info(f"Video info: {metadata['width']}x{metadata['height']}, "
                   f"{metadata['duration']:.1f}s, {metadata['codec']}")

        return metadata

    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe error: {e.stderr if e.stderr else str(e)}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ffprobe output: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return None


def validate_video_file(video_path: Path, max_duration: Optional[int] = None) -> tuple[bool, str]:
    """
    Validate downloaded video file

    Args:
        video_path: Path to video file
        max_duration: Maximum allowed duration in seconds (optional)

    Returns:
        Tuple of (is_valid, message)
    """
    if not video_path.exists():
        return False, f"Video file does not exist: {video_path}"

    if not video_path.is_file():
        return False, f"Path is not a file: {video_path}"

    # Check file size
    file_size = video_path.stat().st_size
    if file_size == 0:
        return False, "Video file is empty"

    if file_size < 1024:  # Less than 1KB
        return False, f"Video file too small: {file_size} bytes"

    # Get video metadata
    metadata = get_video_info(video_path)
    if not metadata:
        return False, "Could not read video metadata"

    # Check duration
    duration = metadata.get('duration', 0)
    if duration == 0:
        return False, "Video has zero duration"

    if max_duration and duration > max_duration:
        return False, f"Video duration ({duration}s) exceeds maximum ({max_duration}s)"

    # Check dimensions
    width = metadata.get('width', 0)
    height = metadata.get('height', 0)
    if width == 0 or height == 0:
        return False, f"Invalid video dimensions: {width}x{height}"

    return True, "Video file is valid"


def estimate_download_size(video_url: str, quality: str = 'best') -> Optional[float]:
    """
    Estimate download size without downloading

    Args:
        video_url: YouTube video URL
        quality: Quality setting

    Returns:
        Estimated size in MB or None if cannot estimate
    """
    try:
        format_str = _build_format_string(quality)

        command = [
            'yt-dlp',
            '-f', format_str,
            '--print', '%(filesize,filesize_approx)s',
            '--no-warnings',
            '--quiet',
            video_url
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

        size_bytes = int(result.stdout.strip())
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)

    except Exception as e:
        logger.warning(f"Could not estimate download size: {e}")
        return None


def check_video_availability(video_url: str) -> tuple[bool, str]:
    """
    Check if video is available for download

    Args:
        video_url: YouTube video URL

    Returns:
        Tuple of (is_available, message)
    """
    try:
        command = [
            'yt-dlp',
            '--simulate',
            '--no-warnings',
            '--quiet',
            video_url
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return True, "Video is available"
        else:
            error = result.stderr.strip() if result.stderr else "Unknown error"
            return False, f"Video not available: {error}"

    except subprocess.TimeoutExpired:
        return False, "Timeout checking video availability"
    except Exception as e:
        return False, f"Error checking availability: {e}"