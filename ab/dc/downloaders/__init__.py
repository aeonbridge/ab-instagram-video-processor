"""
Video Clipper Service Package
Downloads YouTube videos and creates clips based on popular moments
"""

from .video_clipper_service import process_video_moments
from .config_manager import get_config, Config
from .storage_manager import (
    create_video_directory,
    get_clip_path,
    get_video_path,
    is_video_downloaded
)
from .video_downloader import download_video, DownloadError
from .video_cutter import cut_video_segment, batch_cut_videos, CuttingError

__all__ = [
    # Main service
    'process_video_moments',

    # Configuration
    'get_config',
    'Config',

    # Storage
    'create_video_directory',
    'get_clip_path',
    'get_video_path',
    'is_video_downloaded',

    # Download
    'download_video',
    'DownloadError',

    # Cutting
    'cut_video_segment',
    'batch_cut_videos',
    'CuttingError',
]

__version__ = '1.0.0'