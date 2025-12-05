"""
Video Transcriber Service
Transcribes videos from Instagram/YouTube URLs or local video files using OpenAI Whisper
"""

import os
import sys
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

# Install dependencies if needed
def _install_dependencies():
    """Install required dependencies for transcription"""
    dependencies = [
        ("openai-whisper", "whisper"),
        ("torch", "torch"),
    ]

    for package, import_name in dependencies:
        try:
            __import__(import_name)
        except ImportError:
            logger.info(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Configure logging
logger = logging.getLogger(__name__)

# Lazy import whisper after dependencies are checked
whisper = None


class TranscriptionError(Exception):
    """Custom exception for transcription failures"""
    pass


# Supported file formats
AUDIO_FORMATS = {'.mp3', '.m4a', '.wav', '.flac', '.ogg', '.aac', '.wma'}
VIDEO_FORMATS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv'}
SUPPORTED_FORMATS = AUDIO_FORMATS | VIDEO_FORMATS


def _ensure_whisper_loaded():
    """Ensure whisper is loaded and dependencies are installed"""
    global whisper
    if whisper is None:
        _install_dependencies()
        import whisper as whisper_module
        whisper = whisper_module


def extract_audio_from_video(video_path: Path, temp_dir: str) -> Path:
    """
    Extract audio from video file using ffmpeg

    Args:
        video_path: Path to video file
        temp_dir: Temporary directory for extracted audio

    Returns:
        Path to extracted audio file

    Raises:
        TranscriptionError: If audio extraction fails
    """
    audio_path = Path(temp_dir) / f"{video_path.stem}_audio.wav"

    cmd = [
        'ffmpeg', '-i', str(video_path),
        '-vn',  # No video
        '-acodec', 'pcm_s16le',  # PCM format for best compatibility
        '-ar', '16000',  # 16kHz sample rate (optimal for Whisper)
        '-ac', '1',  # Mono
        '-y',  # Overwrite
        '-loglevel', 'error',  # Only show errors
        str(audio_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise TranscriptionError(f"Failed to extract audio: {result.stderr}")

    if not audio_path.exists() or audio_path.stat().st_size == 0:
        raise TranscriptionError("Audio extraction produced empty file")

    logger.info(f"Audio extracted: {audio_path} ({audio_path.stat().st_size / 1024 / 1024:.1f}MB)")
    return audio_path


def format_timestamp(seconds: float) -> str:
    """
    Format seconds to HH:MM:SS timestamp

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def transcribe_video(
    video_path: Path,
    model_size: str = "base",
    language: Optional[str] = None,
    include_timestamps: bool = True,
    output_dir: Optional[Path] = None
) -> Dict:
    """
    Transcribe video file to text with metadata

    Args:
        video_path: Path to video file
        model_size: Whisper model size (tiny, base, small, medium, large)
        language: Language code (e.g., 'pt', 'en') or None for auto-detection
        include_timestamps: Whether to include timestamps in segments
        output_dir: Output directory for transcription files (optional)

    Returns:
        Dictionary with transcription data:
        {
            'success': bool,
            'video_path': str,
            'detected_language': str,
            'full_text': str,
            'segments': List[Dict],  # Only if include_timestamps
            'markdown_file': str,  # Path to saved markdown file (if output_dir provided)
            'processing_time': float
        }

    Raises:
        TranscriptionError: If transcription fails
        FileNotFoundError: If video file not found
    """
    start_time = datetime.now()

    # Ensure whisper is loaded
    _ensure_whisper_loaded()

    # Validate file
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    suffix = video_path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise TranscriptionError(
            f"Unsupported format: {suffix}. Supported: {', '.join(SUPPORTED_FORMATS)}"
        )

    logger.info(f"Starting transcription for: {video_path.name}")
    logger.info(f"Model: {model_size}, Language: {language or 'auto'}")

    # Load Whisper model
    try:
        logger.info(f"Loading Whisper model '{model_size}'...")
        model = whisper.load_model(model_size)
    except Exception as e:
        raise TranscriptionError(f"Failed to load Whisper model: {e}")

    # Handle video files - extract audio first
    audio_path = video_path
    temp_dir = None

    try:
        if suffix in VIDEO_FORMATS:
            logger.info("Extracting audio from video...")
            temp_dir = tempfile.mkdtemp()
            audio_path = extract_audio_from_video(video_path, temp_dir)

        # Transcribe
        logger.info("Transcribing audio (this may take a while)...")
        transcribe_options = {
            "verbose": False,
        }

        if language:
            transcribe_options["language"] = language

        result = whisper.transcribe(str(audio_path), **transcribe_options)

        # Detected language
        detected_lang = result.get("language", "unknown")
        logger.info(f"Detected language: {detected_lang}")

        # Build response
        response = {
            'success': True,
            'video_path': str(video_path),
            'video_name': video_path.name,
            'detected_language': detected_lang,
            'full_text': result.get("text", "").strip(),
            'model_used': model_size
        }

        # Add segments with timestamps if requested
        if include_timestamps and result.get("segments"):
            response['segments'] = [
                {
                    'start': seg['start'],
                    'end': seg['end'],
                    'start_formatted': format_timestamp(seg['start']),
                    'end_formatted': format_timestamp(seg['end']),
                    'text': seg['text'].strip()
                }
                for seg in result['segments']
            ]

        # Save to markdown file if output directory provided
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            markdown_content = _generate_markdown(
                video_name=video_path.name,
                transcription_data=response,
                include_timestamps=include_timestamps
            )

            markdown_file = output_dir / f"{video_path.stem}_transcription.md"
            markdown_file.write_text(markdown_content, encoding='utf-8')

            response['markdown_file'] = str(markdown_file)
            logger.info(f"Transcription saved to: {markdown_file}")

        # Calculate processing time
        end_time = datetime.now()
        response['processing_time'] = (end_time - start_time).total_seconds()

        logger.info(f"Transcription complete in {response['processing_time']:.1f}s")
        return response

    finally:
        # Cleanup temp files
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)


def transcribe_from_url(
    video_url: str,
    video_id: str,
    downloads_path: Path,
    transcriptions_path: Path,
    model_size: str = "base",
    language: Optional[str] = None,
    include_timestamps: bool = True,
    download_if_needed: bool = True
) -> Dict:
    """
    Transcribe video from URL (downloads if needed)

    Args:
        video_url: Video URL (YouTube, Instagram, etc)
        video_id: Video identifier for filename
        downloads_path: Directory where videos are stored
        transcriptions_path: Directory to save transcriptions
        model_size: Whisper model size
        language: Language code or None for auto-detection
        include_timestamps: Whether to include timestamps
        download_if_needed: Download video if not already downloaded

    Returns:
        Dictionary with transcription data (same as transcribe_video)

    Raises:
        TranscriptionError: If transcription fails
        FileNotFoundError: If video not found and download_if_needed=False
    """
    from storage_manager import sanitize_video_id, get_video_path
    from video_downloader import download_video as download_video_ytdlp

    # Sanitize video ID
    video_id = sanitize_video_id(video_id)
    video_path = get_video_path(video_id, downloads_path)

    # Download if needed
    if not video_path.exists():
        if not download_if_needed:
            raise FileNotFoundError(
                f"Video not found: {video_path}. Set download_if_needed=True to download."
            )

        logger.info(f"Video not found locally. Downloading from: {video_url}")
        try:
            video_path = download_video_ytdlp(
                video_url=video_url,
                video_id=video_id,
                downloads_path=downloads_path
            )
        except Exception as e:
            raise TranscriptionError(f"Failed to download video: {e}")
    else:
        logger.info(f"Using existing video: {video_path}")

    # Transcribe
    return transcribe_video(
        video_path=video_path,
        model_size=model_size,
        language=language,
        include_timestamps=include_timestamps,
        output_dir=transcriptions_path
    )


def _generate_markdown(
    video_name: str,
    transcription_data: Dict,
    include_timestamps: bool
) -> str:
    """
    Generate markdown content from transcription data

    Args:
        video_name: Name of video file
        transcription_data: Transcription result dictionary
        include_timestamps: Whether to include timestamps

    Returns:
        Markdown formatted string
    """
    lines = []

    # Header
    lines.append(f"# Transcription: {video_name}")
    lines.append("")

    # Metadata
    lines.append("## Metadata")
    lines.append("")
    lines.append(f"- **Source file:** {video_name}")
    lines.append(f"- **Detected language:** {transcription_data['detected_language']}")
    lines.append(f"- **Model used:** {transcription_data['model_used']}")
    lines.append(f"- **Transcription date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **Processing time:** {transcription_data.get('processing_time', 0):.1f}s")
    lines.append("")

    # Transcription content
    lines.append("## Transcription")
    lines.append("")

    if include_timestamps and 'segments' in transcription_data:
        # With timestamps - segment by segment
        for segment in transcription_data['segments']:
            start = segment['start_formatted']
            end = segment['end_formatted']
            text = segment['text']

            lines.append(f"**[{start} - {end}]**")
            lines.append(f"{text}")
            lines.append("")
    else:
        # Without timestamps - full text
        lines.append(transcription_data['full_text'])
        lines.append("")

    # Full text section (for timestamped versions)
    if include_timestamps and 'segments' in transcription_data:
        lines.append("---")
        lines.append("")
        lines.append("## Full Text")
        lines.append("")
        lines.append(transcription_data['full_text'])
        lines.append("")

    return "\n".join(lines)


def batch_transcribe_videos(
    video_paths: List[Path],
    output_dir: Path,
    model_size: str = "base",
    language: Optional[str] = None,
    include_timestamps: bool = True
) -> Dict:
    """
    Transcribe multiple videos in batch

    Args:
        video_paths: List of video file paths
        output_dir: Directory to save transcriptions
        model_size: Whisper model size
        language: Language code or None for auto-detection
        include_timestamps: Whether to include timestamps

    Returns:
        Dictionary with batch results:
        {
            'total_videos': int,
            'successful': int,
            'failed': int,
            'results': List[Dict],  # Individual transcription results
            'total_time': float
        }
    """
    start_time = datetime.now()

    results = {
        'total_videos': len(video_paths),
        'successful': 0,
        'failed': 0,
        'results': [],
        'errors': []
    }

    for i, video_path in enumerate(video_paths, 1):
        logger.info(f"Processing video {i}/{len(video_paths)}: {video_path.name}")

        try:
            result = transcribe_video(
                video_path=video_path,
                model_size=model_size,
                language=language,
                include_timestamps=include_timestamps,
                output_dir=output_dir
            )
            results['successful'] += 1
            results['results'].append(result)

        except Exception as e:
            logger.error(f"Failed to transcribe {video_path.name}: {e}")
            results['failed'] += 1
            results['errors'].append({
                'video': str(video_path),
                'error': str(e)
            })

    end_time = datetime.now()
    results['total_time'] = (end_time - start_time).total_seconds()

    logger.info(f"Batch complete: {results['successful']} successful, {results['failed']} failed")
    return results


def get_available_models() -> List[str]:
    """
    Get list of available Whisper model sizes

    Returns:
        List of model names
    """
    return ["tiny", "base", "small", "medium", "large"]


def validate_model_size(model_size: str) -> tuple[bool, Optional[str]]:
    """
    Validate Whisper model size

    Args:
        model_size: Model size to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_models = get_available_models()
    if model_size not in valid_models:
        return False, f"Invalid model size: {model_size}. Valid models: {', '.join(valid_models)}"
    return True, None


def validate_language_code(language: str) -> tuple[bool, Optional[str]]:
    """
    Validate language code for Whisper

    Args:
        language: Language code to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Common language codes supported by Whisper
    common_languages = {
        'en', 'zh', 'de', 'es', 'ru', 'ko', 'fr', 'ja', 'pt', 'tr', 'pl', 'ca', 'nl',
        'ar', 'sv', 'it', 'id', 'hi', 'fi', 'vi', 'he', 'uk', 'el', 'ms', 'cs', 'ro',
        'da', 'hu', 'ta', 'no', 'th', 'ur', 'hr', 'bg', 'lt', 'la', 'mi', 'ml', 'cy',
        'sk', 'te', 'fa', 'lv', 'bn', 'sr', 'az', 'sl', 'kn', 'et', 'mk', 'br', 'eu',
        'is', 'hy', 'ne', 'mn', 'bs', 'kk', 'sq', 'sw', 'gl', 'mr', 'pa', 'si', 'km',
        'sn', 'yo', 'so', 'af', 'oc', 'ka', 'be', 'tg', 'sd', 'gu', 'am', 'yi', 'lo',
        'uz', 'fo', 'ht', 'ps', 'tk', 'nn', 'mt', 'sa', 'lb', 'my', 'bo', 'tl', 'mg',
        'as', 'tt', 'haw', 'ln', 'ha', 'ba', 'jw', 'su'
    }

    if language.lower() not in common_languages:
        return False, f"Language code '{language}' may not be supported by Whisper"

    return True, None