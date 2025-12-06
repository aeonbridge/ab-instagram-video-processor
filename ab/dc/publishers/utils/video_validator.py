"""
Video Validator Utility
Validates video files against platform requirements
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class VideoRequirements:
    """Platform video requirements"""
    max_file_size: int  # bytes
    max_duration: float  # seconds
    min_duration: float  # seconds
    min_resolution: Tuple[int, int]  # (width, height)
    max_resolution: Tuple[int, int]  # (width, height)
    supported_formats: List[str]
    supported_codecs: List[str]
    supported_aspect_ratios: List[str]
    max_bitrate: Optional[int] = None  # kbps
    min_bitrate: Optional[int] = None  # kbps


class VideoValidator:
    """Validates video files using FFprobe"""

    # Platform-specific requirements
    YOUTUBE_REQUIREMENTS = VideoRequirements(
        max_file_size=256 * 1024 * 1024 * 1024,  # 256GB
        max_duration=12 * 60 * 60,  # 12 hours
        min_duration=1,  # 1 second
        min_resolution=(426, 240),
        max_resolution=(7680, 4320),  # 8K
        supported_formats=['mp4', 'mov', 'avi', 'wmv', 'flv', '3gp', 'webm', 'mkv'],
        supported_codecs=['h264', 'h265', 'hevc', 'mpeg2', 'mpeg4', 'vp8', 'vp9'],
        supported_aspect_ratios=['16:9', '9:16', '4:3', '1:1', '21:9'],
    )

    TIKTOK_REQUIREMENTS = VideoRequirements(
        max_file_size=4 * 1024 * 1024 * 1024,  # 4GB
        max_duration=10 * 60,  # 10 minutes
        min_duration=3,  # 3 seconds
        min_resolution=(360, 640),  # 360p vertical
        max_resolution=(4096, 2160),  # 4K
        supported_formats=['mp4', 'webm', 'mov'],
        supported_codecs=['h264', 'h265', 'hevc'],
        supported_aspect_ratios=['9:16', '16:9', '1:1'],
    )

    def __init__(self, ffprobe_path: str = 'ffprobe'):
        """
        Initialize validator

        Args:
            ffprobe_path: Path to ffprobe binary
        """
        self.ffprobe_path = ffprobe_path

    def get_video_info(self, video_path: Path) -> Dict:
        """
        Extract video information using ffprobe

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video information

        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If ffprobe fails
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cmd = [
            self.ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"ffprobe failed: {result.stderr}")

            data = json.loads(result.stdout)

            # Find video stream
            video_stream = None
            audio_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream

            if not video_stream:
                raise RuntimeError("No video stream found in file")

            format_info = data.get('format', {})

            # Calculate aspect ratio
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            aspect_ratio = self._calculate_aspect_ratio(width, height)

            return {
                'file_size': int(format_info.get('size', 0)),
                'duration': float(format_info.get('duration', 0)),
                'format': format_info.get('format_name', '').split(',')[0],
                'bitrate': int(format_info.get('bit_rate', 0)) // 1000,  # kbps
                'video': {
                    'codec': video_stream.get('codec_name', ''),
                    'width': width,
                    'height': height,
                    'aspect_ratio': aspect_ratio,
                    'fps': self._get_fps(video_stream),
                    'bitrate': int(video_stream.get('bit_rate', 0)) // 1000,  # kbps
                },
                'audio': {
                    'codec': audio_stream.get('codec_name', '') if audio_stream else None,
                    'channels': audio_stream.get('channels', 0) if audio_stream else 0,
                    'sample_rate': audio_stream.get('sample_rate', 0) if audio_stream else 0,
                } if audio_stream else None
            }

        except subprocess.TimeoutExpired:
            raise RuntimeError("ffprobe timed out")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse ffprobe output: {e}")

    def validate(
        self,
        video_path: Path,
        requirements: VideoRequirements
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate video against requirements

        Args:
            video_path: Path to video file
            requirements: Platform requirements

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        try:
            info = self.get_video_info(video_path)
        except Exception as e:
            errors.append(f"Failed to read video info: {str(e)}")
            return False, errors, warnings

        # Check file size
        if info['file_size'] > requirements.max_file_size:
            errors.append(
                f"File size {info['file_size'] / (1024**3):.2f}GB exceeds "
                f"maximum {requirements.max_file_size / (1024**3):.2f}GB"
            )

        # Check duration
        if info['duration'] > requirements.max_duration:
            errors.append(
                f"Duration {info['duration']:.1f}s exceeds maximum {requirements.max_duration:.1f}s"
            )
        elif info['duration'] < requirements.min_duration:
            errors.append(
                f"Duration {info['duration']:.1f}s is below minimum {requirements.min_duration:.1f}s"
            )

        # Check resolution
        width = info['video']['width']
        height = info['video']['height']
        min_w, min_h = requirements.min_resolution
        max_w, max_h = requirements.max_resolution

        if width < min_w or height < min_h:
            errors.append(
                f"Resolution {width}x{height} is below minimum {min_w}x{min_h}"
            )
        if width > max_w or height > max_h:
            errors.append(
                f"Resolution {width}x{height} exceeds maximum {max_w}x{max_h}"
            )

        # Check format
        video_format = info['format'].lower()
        if video_format not in requirements.supported_formats:
            errors.append(
                f"Format '{video_format}' not supported. "
                f"Supported: {', '.join(requirements.supported_formats)}"
            )

        # Check codec
        codec = info['video']['codec'].lower()
        if codec not in requirements.supported_codecs:
            errors.append(
                f"Codec '{codec}' not supported. "
                f"Supported: {', '.join(requirements.supported_codecs)}"
            )

        # Check aspect ratio
        aspect_ratio = info['video']['aspect_ratio']
        if aspect_ratio not in requirements.supported_aspect_ratios:
            warnings.append(
                f"Aspect ratio {aspect_ratio} may not be optimal. "
                f"Recommended: {', '.join(requirements.supported_aspect_ratios)}"
            )

        # Check bitrate
        if requirements.max_bitrate and info['bitrate'] > requirements.max_bitrate:
            warnings.append(
                f"Bitrate {info['bitrate']}kbps exceeds recommended {requirements.max_bitrate}kbps"
            )
        if requirements.min_bitrate and info['bitrate'] < requirements.min_bitrate:
            warnings.append(
                f"Bitrate {info['bitrate']}kbps is below recommended {requirements.min_bitrate}kbps"
            )

        # Check audio
        if not info['audio']:
            warnings.append("No audio track found")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def validate_youtube(self, video_path: Path) -> Tuple[bool, List[str], List[str]]:
        """Validate video for YouTube"""
        return self.validate(video_path, self.YOUTUBE_REQUIREMENTS)

    def validate_tiktok(self, video_path: Path) -> Tuple[bool, List[str], List[str]]:
        """Validate video for TikTok"""
        return self.validate(video_path, self.TIKTOK_REQUIREMENTS)

    def is_youtube_short(self, video_path: Path) -> bool:
        """
        Check if video qualifies as YouTube Short

        Args:
            video_path: Path to video file

        Returns:
            True if video is a YouTube Short (< 60s, vertical)
        """
        try:
            info = self.get_video_info(video_path)
            is_vertical = info['video']['height'] > info['video']['width']
            is_short_duration = info['duration'] <= 60
            return is_vertical and is_short_duration
        except Exception:
            return False

    def _calculate_aspect_ratio(self, width: int, height: int) -> str:
        """Calculate aspect ratio string"""
        if width == 0 or height == 0:
            return "unknown"

        # Common aspect ratios
        ratio = width / height
        if 0.99 < ratio < 1.01:
            return "1:1"
        elif 1.76 < ratio < 1.79:
            return "16:9"
        elif 0.56 < ratio < 0.57:
            return "9:16"
        elif 1.32 < ratio < 1.34:
            return "4:3"
        elif 2.33 < ratio < 2.40:
            return "21:9"
        else:
            return f"{width}:{height}"

    def _get_fps(self, video_stream: Dict) -> float:
        """Extract FPS from video stream"""
        fps_str = video_stream.get('r_frame_rate', '0/1')
        try:
            num, den = fps_str.split('/')
            return float(num) / float(den) if float(den) != 0 else 0
        except (ValueError, ZeroDivisionError):
            return 0.0
