#!/usr/bin/env python3
"""
Audio Transcription Script - Transcrição de áudio para Markdown
Transcreve arquivos de áudio ou vídeo usando OpenAI Whisper e salva em formato Markdown
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# Install dependencies if needed
def install_dependencies():
    """Install required dependencies"""
    dependencies = [
        ("openai-whisper", "whisper"),
        ("torch", "torch"),
    ]

    for package, import_name in dependencies:
        try:
            __import__(import_name)
        except ImportError:
            print(f"📦 Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_dependencies()

import whisper


# Supported file formats
AUDIO_FORMATS = {'.mp3', '.m4a', '.wav', '.flac', '.ogg', '.aac', '.wma'}
VIDEO_FORMATS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv'}
SUPPORTED_FORMATS = AUDIO_FORMATS | VIDEO_FORMATS


def extract_audio_from_video(video_path: Path, temp_dir: str) -> Path:
    """
    Extract audio from video file using ffmpeg

    Args:
        video_path: Path to video file
        temp_dir: Temporary directory for extracted audio

    Returns:
        Path to extracted audio file
    """
    audio_path = Path(temp_dir) / f"{video_path.stem}_audio.wav"

    cmd = [
        'ffmpeg', '-i', str(video_path),
        '-vn',  # No video
        '-acodec', 'pcm_s16le',  # PCM format for best compatibility
        '-ar', '16000',  # 16kHz sample rate (optimal for Whisper)
        '-ac', '1',  # Mono
        '-y',  # Overwrite
        str(audio_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Failed to extract audio: {result.stderr}")

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


def transcribe_audio(
    source_path: str,
    model_size: str = "base",
    language: str = None,
    include_timestamps: bool = True,
    output_dir: str = None
) -> Path:
    """
    Transcribe audio/video file to Markdown

    Args:
        source_path: Path to audio or video file
        model_size: Whisper model size (tiny, base, small, medium, large)
        language: Language code (e.g., 'pt', 'en') or None for auto-detection
        include_timestamps: Whether to include timestamps in output
        output_dir: Output directory for markdown file

    Returns:
        Path to generated markdown file
    """
    source = Path(source_path)

    # Validate file
    if not source.exists():
        raise FileNotFoundError(f"File not found: {source_path}")

    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {suffix}. Supported: {', '.join(SUPPORTED_FORMATS)}")

    # Setup output directory
    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = Path("transcriptions")
    out_dir.mkdir(exist_ok=True)

    # Load Whisper model
    print(f"🤖 Loading Whisper model '{model_size}'...")
    model = whisper.load_model(model_size)

    # Handle video files - extract audio first
    audio_path = source
    temp_dir = None

    try:
        if suffix in VIDEO_FORMATS:
            print(f"🎬 Extracting audio from video...")
            temp_dir = tempfile.mkdtemp()
            audio_path = extract_audio_from_video(source, temp_dir)

        # Transcribe
        print(f"🎤 Transcribing audio...")
        transcribe_options = {
            "verbose": False,
        }

        if language:
            transcribe_options["language"] = language

        result = model.transcribe(str(audio_path), **transcribe_options)

        # Detected language
        detected_lang = result.get("language", "unknown")
        print(f"🌐 Detected language: {detected_lang}")

        # Generate markdown content
        md_content = generate_markdown(
            source_name=source.name,
            transcription=result,
            include_timestamps=include_timestamps,
            detected_language=detected_lang
        )

        # Save markdown file
        output_file = out_dir / f"{source.stem}_transcription.md"
        output_file.write_text(md_content, encoding='utf-8')

        print(f"✅ Transcription complete!")
        print(f"💾 Saved to: {output_file}")

        return output_file

    finally:
        # Cleanup temp files
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)


def generate_markdown(
    source_name: str,
    transcription: dict,
    include_timestamps: bool,
    detected_language: str
) -> str:
    """
    Generate markdown content from transcription

    Args:
        source_name: Name of source file
        transcription: Whisper transcription result
        include_timestamps: Whether to include timestamps
        detected_language: Detected language code

    Returns:
        Markdown formatted string
    """
    lines = []

    # Header
    lines.append(f"# Transcription: {source_name}")
    lines.append("")

    # Metadata
    lines.append("## Metadata")
    lines.append("")
    lines.append(f"- **Source file:** {source_name}")
    lines.append(f"- **Detected language:** {detected_language}")
    lines.append(f"- **Transcription date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Transcription content
    lines.append("## Transcription")
    lines.append("")

    if include_timestamps and transcription.get("segments"):
        # With timestamps - segment by segment
        for segment in transcription["segments"]:
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip()

            lines.append(f"**[{start} - {end}]**")
            lines.append(f"{text}")
            lines.append("")
    else:
        # Without timestamps - full text
        full_text = transcription.get("text", "").strip()
        lines.append(full_text)
        lines.append("")

    # Full text section (for timestamped versions)
    if include_timestamps and transcription.get("segments"):
        lines.append("---")
        lines.append("")
        lines.append("## Full Text")
        lines.append("")
        full_text = transcription.get("text", "").strip()
        lines.append(full_text)
        lines.append("")

    return "\n".join(lines)


def main():
    """Main function"""
    print("🎤 AUDIO TRANSCRIPTION TO MARKDOWN")
    print("-" * 40)

    # Parse arguments
    if len(sys.argv) > 1:
        source = sys.argv[1]
        model_size = sys.argv[2] if len(sys.argv) > 2 else "base"
        language = sys.argv[3] if len(sys.argv) > 3 else None
    else:
        # Interactive mode
        source = input("Audio/Video file path: ").strip()
        if not source:
            print("❌ No file provided!")
            print("💡 Usage: python transcribe_audio.py <file> [model] [language]")
            print("")
            print("Models: tiny, base, small, medium, large")
            print("Languages: pt, en, es, fr, de, etc. (or leave empty for auto)")
            return

        print("")
        print("Available models (larger = more accurate but slower):")
        print("  • tiny   - Fastest, least accurate")
        print("  • base   - Good balance (default)")
        print("  • small  - Better accuracy")
        print("  • medium - High accuracy")
        print("  • large  - Best accuracy, requires more VRAM")
        print("")
        model_size = input("Model [base]: ").strip() or "base"

        print("")
        language = input("Language (pt/en/es/etc or empty for auto): ").strip() or None

    # Validate model size
    valid_models = ["tiny", "base", "small", "medium", "large"]
    if model_size not in valid_models:
        print(f"❌ Invalid model: {model_size}")
        print(f"💡 Valid models: {', '.join(valid_models)}")
        return

    try:
        transcribe_audio(
            source_path=source,
            model_size=model_size,
            language=language,
            include_timestamps=True
        )
    except FileNotFoundError as e:
        print(f"❌ {e}")
    except ValueError as e:
        print(f"❌ {e}")
    except RuntimeError as e:
        print(f"❌ {e}")
        print("💡 Make sure ffmpeg is installed:")
        print("  • Mac: brew install ffmpeg")
        print("  • Linux: sudo apt-get install ffmpeg")
        print("  • Windows: download from https://ffmpeg.org")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()