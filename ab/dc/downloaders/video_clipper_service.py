"""
Video Clipper Service - Main Orchestrator
Downloads YouTube videos and creates clips based on popular moments
"""

import time
import logging
from pathlib import Path
from typing import Dict, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import get_config, Config
from storage_manager import (
    create_video_directory,
    is_video_downloaded,
    get_video_path,
    calculate_directory_size,
    cleanup_old_clips,
    check_disk_space,
    sanitize_video_id
)
from video_downloader import (
    download_video,
    get_video_info,
    validate_video_file,
    check_video_availability,
    DownloadError
)
from video_cutter import (
    batch_cut_videos,
    CuttingError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_moments_data(data: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate input moments data

    Args:
        data: Input dictionary with video_id, video_url, moments

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    if 'video_id' not in data:
        return False, "Missing required field: video_id"

    if 'video_url' not in data:
        return False, "Missing required field: video_url"

    if 'moments' not in data:
        return False, "Missing required field: moments"

    # Validate video_id format
    video_id = data['video_id']
    try:
        sanitize_video_id(video_id)
    except ValueError as e:
        return False, str(e)

    # Validate video_url
    video_url = data['video_url']
    if not isinstance(video_url, str):
        return False, "video_url must be a string"

    if not ('youtube.com' in video_url or 'youtu.be' in video_url):
        return False, "video_url must be a YouTube URL"

    # Validate moments
    moments = data['moments']
    if not isinstance(moments, list):
        return False, "moments must be a list"

    if len(moments) == 0:
        return False, "moments list cannot be empty"

    # Validate each moment
    for i, moment in enumerate(moments):
        if not isinstance(moment, dict):
            return False, f"Moment {i} must be a dictionary"

        required_fields = ['start_time', 'end_time', 'duration']
        for field in required_fields:
            if field not in moment:
                return False, f"Moment {i} missing required field: {field}"

        start = moment['start_time']
        end = moment['end_time']

        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            return False, f"Moment {i} timestamps must be numbers"

        if start < 0 or end < 0:
            return False, f"Moment {i} timestamps cannot be negative"

        if start >= end:
            return False, f"Moment {i} start_time must be less than end_time"

    return True, None


def process_video_moments(
    moments_data: Dict,
    downloads_path: Optional[Path] = None,
    storage_path: Optional[Path] = None,
    force_redownload: bool = False,
    force_reprocess: bool = False,
    **ffmpeg_options
) -> Dict:
    """
    Main service function to process video moments and create clips

    Args:
        moments_data: Dictionary with video_id, video_url, moments
        downloads_path: Override downloads directory (uses config if None)
        storage_path: Override storage directory (uses config if None)
        force_redownload: Re-download video even if exists
        force_reprocess: Re-cut clips even if they exist
        **ffmpeg_options: Override FFmpeg options (video_codec, audio_codec, etc.)

    Returns:
        Dictionary with processing results
    """
    start_time = time.time()

    try:
        # Load configuration
        config = get_config()

        # Use provided paths or defaults from config
        downloads_path = downloads_path or config.downloads_path
        storage_path = storage_path or config.stored_processed_videos

        # Validate input
        logger.info("Validating input data...")
        is_valid, error = validate_moments_data(moments_data)
        if not is_valid:
            return {
                'success': False,
                'error': f"Invalid input: {error}",
                'video_id': moments_data.get('video_id'),
                'video_url': moments_data.get('video_url')
            }

        video_id = moments_data['video_id']
        video_url = moments_data['video_url']
        moments = moments_data['moments']

        logger.info(f"Processing video: {video_id} ({len(moments)} moments)")

        # Check video availability
        logger.info("Checking video availability...")
        available, availability_msg = check_video_availability(video_url)
        if not available:
            return {
                'success': False,
                'error': availability_msg,
                'video_id': video_id,
                'video_url': video_url
            }

        # Check if video is already downloaded
        video_exists = is_video_downloaded(video_id, downloads_path)
        video_path = get_video_path(video_id, downloads_path)

        if video_exists and not force_redownload:
            logger.info(f"Video already downloaded: {video_path}")
            video_downloaded = False  # Not downloaded in this run
        else:
            # Download video
            if force_redownload and video_exists:
                logger.info("Force re-download enabled, downloading video...")

            logger.info(f"Downloading video from: {video_url}")

            try:
                video_path = download_video(
                    video_url=video_url,
                    video_id=video_id,
                    downloads_path=downloads_path,
                    quality=config.download_quality,
                    timeout=config.download_timeout
                )
                video_downloaded = True
                logger.info(f"Video downloaded successfully: {video_path}")

            except DownloadError as e:
                return {
                    'success': False,
                    'error': f"Download failed: {str(e)}",
                    'video_id': video_id,
                    'video_url': video_url
                }

        # Validate video file
        logger.info("Validating video file...")
        is_valid, validation_msg = validate_video_file(
            video_path,
            max_duration=config.max_video_duration
        )

        if not is_valid:
            return {
                'success': False,
                'error': f"Video validation failed: {validation_msg}",
                'video_id': video_id,
                'video_url': video_url,
                'video_path': str(video_path)
            }

        # Get video info
        video_info = get_video_info(video_path)
        if not video_info:
            logger.warning("Could not extract video metadata")

        # Check disk space (estimate: video size × 0.5 for clips)
        video_size_mb = video_info.get('size_mb', 0) if video_info else 0
        estimated_clips_size = video_size_mb * 0.5
        has_space, space_msg = check_disk_space(storage_path, estimated_clips_size)

        if not has_space:
            return {
                'success': False,
                'error': space_msg,
                'video_id': video_id,
                'video_url': video_url,
                'video_path': str(video_path)
            }

        logger.info(space_msg)

        # Create output directory
        logger.info(f"Creating output directory for clips...")
        try:
            output_dir = create_video_directory(video_id, storage_path)
        except OSError as e:
            return {
                'success': False,
                'error': f"Failed to create output directory: {str(e)}",
                'video_id': video_id,
                'video_url': video_url,
                'video_path': str(video_path)
            }

        # Cleanup old clips if force reprocess
        if force_reprocess:
            logger.info("Force reprocess enabled, cleaning up old clips...")
            cleanup_old_clips(video_id, storage_path)

        # Prepare FFmpeg options
        ffmpeg_opts = config.get_ffmpeg_options()
        ffmpeg_opts.update(ffmpeg_options)  # Override with provided options
        ffmpeg_opts['ffmpeg_path'] = config.ffmpeg_path
        ffmpeg_opts['timeout'] = config.clip_timeout

        logger.info(f"FFmpeg options: codec={ffmpeg_opts['video_codec']}, "
                   f"crf={ffmpeg_opts['crf']}, preset={ffmpeg_opts.get('preset', 'medium')}")

        # Cut clips
        logger.info(f"Creating {len(moments)} clips...")
        clips = batch_cut_videos(
            input_path=video_path,
            output_dir=output_dir,
            moments=moments,
            video_id=video_id,
            parallel=config.enable_parallel_processing,
            max_workers=config.max_concurrent_clips,
            **ffmpeg_opts
        )

        # Count successful clips
        successful_clips = [c for c in clips if c.get('success', False)]
        failed_clips = [c for c in clips if not c.get('success', True)]

        if failed_clips:
            logger.warning(f"{len(failed_clips)} clips failed to process")
            for clip in failed_clips:
                logger.warning(f"  Clip {clip['clip_id']}: {clip.get('error', 'Unknown error')}")

        # Calculate total size
        total_size_mb = calculate_directory_size(output_dir)

        # Calculate processing time
        processing_time = time.time() - start_time

        logger.info(f"Processing complete: {len(successful_clips)}/{len(moments)} clips created "
                   f"in {processing_time:.1f}s")

        # Build response
        return {
            'success': len(successful_clips) > 0,
            'video_id': video_id,
            'video_url': video_url,
            'video_downloaded': video_downloaded,
            'video_path': str(video_path),
            'video_info': video_info,
            'clips_created': len(successful_clips),
            'clips_failed': len(failed_clips),
            'clips': successful_clips,
            'failed_clips': failed_clips if failed_clips else None,
            'total_size_mb': total_size_mb,
            'processing_time_seconds': round(processing_time, 2),
            'error': None if successful_clips else 'All clips failed to process'
        }

    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}", exc_info=True)
        processing_time = time.time() - start_time

        return {
            'success': False,
            'error': f"Unexpected error: {str(e)}",
            'video_id': moments_data.get('video_id'),
            'video_url': moments_data.get('video_url'),
            'processing_time_seconds': round(processing_time, 2)
        }


def main():
    """Example usage"""
    import json

    # Example: Load moments from JSON file or use directly
    example_moments = {
        "video_id": "RusBe_8arLQ",
        "video_url": "https://www.youtube.com/watch?v=RusBe_8arLQ",
        "moments": [
            {
                "start_time": 15.06,
                "end_time": 45.06,
                "duration": 30.0,
                "score": 0.952,
                "timestamp": "0:15"
            },
            {
                "start_time": 75.3,
                "end_time": 105.3,
                "duration": 30.0,
                "score": 1.374,
                "timestamp": "1:15"
            }
        ]
    }

    print("=" * 60)
    print("Video Clipper Service - Test Run")
    print("=" * 60)

    result = process_video_moments(example_moments)

    print("\nResult:")
    print(json.dumps(result, indent=2))

    if result['success']:
        print(f"\n✓ Successfully created {result['clips_created']} clips")
        print(f"  Total size: {result['total_size_mb']}MB")
        print(f"  Processing time: {result['processing_time_seconds']}s")
        print(f"\nClips:")
        for clip in result['clips']:
            print(f"  - {clip['filename']} ({clip['file_size_mb']}MB)")
    else:
        print(f"\n✗ Error: {result['error']}")


if __name__ == "__main__":
    main()