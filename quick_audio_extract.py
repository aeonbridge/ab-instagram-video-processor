#!/usr/bin/env python3
"""
Quick Audio Extractor - Extração rápida de áudio
Extrai áudio em MP3 de alta qualidade com um comando
"""

import os
import sys
import subprocess
from pathlib import Path

# Instala dependências
try:
    import yt_dlp
except ImportError:
    print("📦 Instalando yt-dlp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp

def quick_extract(source, format='mp3'):
    """
    Extração rápida de áudio
    
    Args:
        source: URL ou arquivo de vídeo
        format: Formato de saída (mp3, m4a, wav, flac)
    """
    
    # Cria pasta de saída
    output_dir = Path("audio_downloads")
    output_dir.mkdir(exist_ok=True)
    
    # Configura yt-dlp para extrair áudio
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format,
            'preferredquality': '320' if format == 'mp3' else '256',
        }],
        'postprocessor_args': [
            '-ar', '44100',  # Sample rate
        ],
    }
    
    try:
        print(f"🎵 Extraindo áudio em {format.upper()}...")
        print(f"📥 Fonte: {source}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Se for arquivo local
            if os.path.exists(source):
                # Para arquivos locais, usa ffmpeg diretamente
                output_file = output_dir / f"{Path(source).stem}.{format}"
                
                cmd = [
                    'ffmpeg', '-i', source,
                    '-vn',  # Sem vídeo
                    '-acodec', 'libmp3lame' if format == 'mp3' else 'aac',
                    '-ab', '320k' if format == 'mp3' else '256k',
                    '-ar', '44100',
                    '-y',  # Sobrescrever
                    str(output_file)
                ]
                
                subprocess.run(cmd, capture_output=True)
                
                if output_file.exists():
                    print(f"✅ Áudio extraído com sucesso!")
                    print(f"💾 Salvo em: {output_file}")
                    size_mb = output_file.stat().st_size / (1024 * 1024)
                    print(f"📊 Tamanho: {size_mb:.2f} MB")
                else:
                    print("❌ Erro ao extrair áudio")
            else:
                # Para URLs, usa yt-dlp
                ydl.download([source])
                print(f"✅ Áudio extraído com sucesso!")
                print(f"📁 Salvo em: {output_dir}/")
        
    except subprocess.CalledProcessError:
        print("❌ Erro: ffmpeg não está instalado!")
        print("📥 Instale o ffmpeg:")
        print("  • Windows: baixe de https://ffmpeg.org")
        print("  • Mac: brew install ffmpeg")
        print("  • Linux: sudo apt-get install ffmpeg")
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("💡 Dica: Verifique se a URL está correta ou se o arquivo existe")

def main():
    """Função principal"""
    if len(sys.argv) > 1:
        source = sys.argv[1]
        format = sys.argv[2] if len(sys.argv) > 2 else 'mp3'
    else:
        print("🎵 QUICK AUDIO EXTRACTOR")
        print("-" * 30)
        source = input("URL ou arquivo: ").strip()
        format = input("Formato (mp3/m4a/wav) [mp3]: ").strip() or 'mp3'
    
    if source:
        quick_extract(source, format)
    else:
        print("❌ Nenhuma fonte fornecida!")
        print("💡 Uso: python quick_audio_extract.py [URL/arquivo] [formato]")

if __name__ == "__main__":
    main()
