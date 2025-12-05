#!/usr/bin/env python3
"""
Video Aspect Ratio Converter
Converts videos to specified aspect ratio, organizing output by ratio
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_aspect_ratio_filter(aspect_ratio: str) -> Optional[str]:
    """
    Get FFmpeg filter for aspect ratio conversion

    Args:
        aspect_ratio: Target aspect ratio (9:16, 16:9, 1:1, 4:5)

    Returns:
        FFmpeg video filter string or None
    """
    aspect_configs = {
        '9:16': {
            'width': 1080,
            'height': 1920,
            'crop': 'crop=ih*9/16:ih'
        },
        '16:9': {
            'width': 1920,
            'height': 1080,
            'crop': 'crop=iw:iw*9/16'
        },
        '1:1': {
            'width': 1080,
            'height': 1080,
            'crop': 'crop=min(iw\\,ih):min(iw\\,ih)'
        },
        '4:5': {
            'width': 1080,
            'height': 1350,
            'crop': 'crop=ih*4/5:ih'
        }
    }

    if aspect_ratio not in aspect_configs:
        logger.error(f"Aspect ratio inválido: {aspect_ratio}")
        logger.error(f"Ratios suportados: {', '.join(aspect_configs.keys())}")
        return None

    config = aspect_configs[aspect_ratio]
    vf = f"{config['crop']},scale={config['width']}:{config['height']}"

    return vf


def get_video_info(video_path: Path) -> Optional[Dict]:
    """
    Get video information using ffprobe

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with video info or None if failed
    """
    try:
        command = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration,codec_name',
            '-show_entries', 'format=duration,size',
            '-of', 'default=noprint_wrappers=1',
            str(video_path)
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )

        info = {}
        for line in result.stdout.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                info[key] = value

        return info

    except Exception as e:
        logger.warning(f"Não foi possível extrair info do vídeo: {e}")
        return None


def generate_output_filename(input_path: Path, aspect_ratio: str) -> str:
    """
    Generate output filename following the pattern from cli_clipper.py

    Args:
        input_path: Input video path
        aspect_ratio: Target aspect ratio

    Returns:
        Output filename

    Format: {basename}_{ratio}.mp4
    Example: video_0000_30s_score_095_9x16.mp4
    """
    basename = input_path.stem
    ratio_str = aspect_ratio.replace(':', 'x')

    return f"{basename}_{ratio_str}.mp4"


def convert_video(
    input_path: Path,
    output_path: Path,
    aspect_ratio: str,
    codec: str = 'libx264',
    crf: int = 23,
    preset: str = 'medium',
    force: bool = False
) -> bool:
    """
    Convert video to specified aspect ratio

    Args:
        input_path: Path to input video
        output_path: Path for output video
        aspect_ratio: Target aspect ratio
        codec: Video codec
        crf: Quality (18-28, lower=better)
        preset: Encoding preset
        force: Overwrite if exists

    Returns:
        True if successful, False otherwise
    """
    # Check if output exists
    if output_path.exists() and not force:
        logger.info(f"Arquivo já existe (use --force para recriar): {output_path.name}")
        return True

    # Get aspect ratio filter
    vf = get_aspect_ratio_filter(aspect_ratio)
    if not vf:
        return False

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build FFmpeg command
    command = [
        'ffmpeg',
        '-i', str(input_path),
        '-vf', vf,
        '-c:v', codec,
        '-crf', str(crf),
        '-preset', preset,
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
    ]

    if force:
        command.append('-y')

    command.append(str(output_path))

    logger.info(f"Convertendo: {input_path.name} -> {aspect_ratio}")
    logger.debug(f"FFmpeg command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes max
            check=True
        )

        # Verify output
        if not output_path.exists():
            logger.error(f"Arquivo de saída não foi criado: {output_path}")
            return False

        file_size = output_path.stat().st_size
        if file_size == 0:
            logger.error("Arquivo de saída está vazio")
            return False

        logger.info(f"Convertido com sucesso: {output_path.name} ({file_size / 1024 / 1024:.1f}MB)")
        return True

    except subprocess.TimeoutExpired:
        logger.error("Timeout durante conversão")
        return False

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        logger.error(f"Erro FFmpeg: {error_msg}")
        return False

    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return False


def find_video_files(path: Path) -> List[Path]:
    """
    Find all video files in path (file or directory)

    Args:
        path: File or directory path

    Returns:
        List of video file paths
    """
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.webm', '.m4v'}

    if path.is_file():
        if path.suffix.lower() in video_extensions:
            return [path]
        else:
            logger.error(f"Arquivo não é um vídeo suportado: {path}")
            return []

    elif path.is_dir():
        videos = []
        for ext in video_extensions:
            videos.extend(path.glob(f'*{ext}'))
            videos.extend(path.glob(f'*{ext.upper()}'))

        videos = sorted(set(videos))  # Remove duplicates and sort

        if not videos:
            logger.warning(f"Nenhum vídeo encontrado em: {path}")

        return videos

    else:
        logger.error(f"Path não existe: {path}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Converte vídeos para aspect ratio especificado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Converter um vídeo para 9:16 (Reels/TikTok)
  %(prog)s video.mp4 --ratio 9:16

  # Converter todos vídeos de uma pasta para 16:9
  %(prog)s videos/ --ratio 16:9

  # Converter com qualidade alta (CRF baixo)
  %(prog)s video.mp4 --ratio 1:1 --crf 18

  # Forçar re-conversão mesmo se existir
  %(prog)s video.mp4 --ratio 4:5 --force

Aspect ratios suportados:
  9:16  - Vertical (Reels, TikTok, Shorts) 1080x1920
  16:9  - Horizontal (YouTube) 1920x1080
  1:1   - Quadrado (Instagram feed) 1080x1080
  4:5   - Portrait (Instagram) 1080x1350
        """
    )

    parser.add_argument(
        'input',
        type=str,
        help='Arquivo de vídeo ou pasta com vídeos'
    )

    parser.add_argument(
        '--ratio', '-r',
        required=True,
        choices=['9:16', '16:9', '1:1', '4:5'],
        help='Aspect ratio de saída'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Pasta de saída (padrão: pasta com nome do ratio)'
    )

    parser.add_argument(
        '--codec',
        choices=['libx264', 'libx265'],
        default='libx264',
        help='Codec de vídeo (padrão: libx264)'
    )

    parser.add_argument(
        '--crf',
        type=int,
        default=23,
        help='Qualidade CRF: 18-28, menor=melhor (padrão: 23)'
    )

    parser.add_argument(
        '--preset',
        choices=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast',
                 'medium', 'slow', 'slower', 'veryslow'],
        default='medium',
        help='Preset de encoding (padrão: medium)'
    )

    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Sobrescrever arquivos existentes'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Log detalhado'
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse input path
    input_path = Path(args.input).resolve()

    if not input_path.exists():
        logger.error(f"Path não existe: {input_path}")
        sys.exit(1)

    # Find video files
    video_files = find_video_files(input_path)

    if not video_files:
        logger.error("Nenhum vídeo encontrado para processar")
        sys.exit(1)

    logger.info(f"Encontrados {len(video_files)} vídeo(s) para processar")

    # Determine output directory
    if args.output:
        output_dir = Path(args.output).resolve()
    else:
        # Create folder named with ratio next to input
        ratio_folder = args.ratio.replace(':', 'x')
        if input_path.is_file():
            output_dir = input_path.parent / ratio_folder
        else:
            output_dir = input_path / ratio_folder

    logger.info(f"Pasta de saída: {output_dir}")

    # Process videos
    successful = 0
    failed = 0
    skipped = 0

    for i, video_path in enumerate(video_files, 1):
        logger.info(f"\n[{i}/{len(video_files)}] Processando: {video_path.name}")

        # Generate output filename
        output_filename = generate_output_filename(video_path, args.ratio)
        output_path = output_dir / output_filename

        # Check if already exists
        if output_path.exists() and not args.force:
            logger.info(f"Já existe (pulando): {output_filename}")
            skipped += 1
            continue

        # Convert video
        success = convert_video(
            input_path=video_path,
            output_path=output_path,
            aspect_ratio=args.ratio,
            codec=args.codec,
            crf=args.crf,
            preset=args.preset,
            force=args.force
        )

        if success:
            successful += 1
        else:
            failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("RESUMO DA CONVERSÃO")
    print("=" * 60)
    print(f"Total de vídeos: {len(video_files)}")
    print(f"Convertidos com sucesso: {successful}")
    print(f"Já existiam (pulados): {skipped}")
    print(f"Falharam: {failed}")
    print(f"Pasta de saída: {output_dir}")
    print("=" * 60)

    # Exit code
    if failed == len(video_files):
        sys.exit(1)  # All failed
    elif failed > 0:
        sys.exit(2)  # Some failed
    else:
        sys.exit(0)  # All success


if __name__ == "__main__":
    main()