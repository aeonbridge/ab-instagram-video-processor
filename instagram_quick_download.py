#!/usr/bin/env python3
"""
Script simplificado para download rápido de vídeos do Instagram
"""

import os
import sys

# Instala yt-dlp se necessário
try:
    import yt_dlp
except ImportError:
    print("Instalando yt-dlp...")
    os.system(f"{sys.executable} -m pip install yt-dlp")
    import yt_dlp

def download_quick(url):
    """Download rápido e simples"""
    
    # Configuração básica
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        print(f"Baixando: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✅ Download concluído!")
        print("📁 Salvo em: downloads/")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Cole a URL do Instagram: ")
    
    download_quick(url)
