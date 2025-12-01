#!/usr/bin/env python3
"""
Audio Extractor - Extrai áudio de vídeos do Instagram ou arquivos locais
Suporta múltiplos formatos de saída: MP3, M4A, WAV, FLAC, OGG
"""

import os
import sys
import re
from pathlib import Path
import subprocess

# Garante que o ffmpeg do Homebrew seja usado primeiro (macOS)
if sys.platform == 'darwin' and os.path.exists('/opt/homebrew/bin'):
    os.environ['PATH'] = '/opt/homebrew/bin:' + os.environ.get('PATH', '')

# Verifica e instala dependências
def install_dependencies():
    """Instala as dependências necessárias"""
    dependencies = ['yt-dlp', 'ffmpeg-python']

    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            print(f"📦 Instalando {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

    # Verifica ffmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("\n⚠️ ATENÇÃO: ffmpeg não está instalado!")
        print("📥 Por favor, instale o ffmpeg:")
        print("  • Windows: baixe de https://ffmpeg.org/download.html")
        print("  • Mac: brew install ffmpeg")
        print("  • Linux: sudo apt-get install ffmpeg")
        return False
    return True

# Instala dependências
if not install_dependencies():
    sys.exit(1)

import yt_dlp
import ffmpeg

class AudioExtractor:
    """Classe para extrair áudio de vídeos"""
    
    # Formatos de áudio suportados
    AUDIO_FORMATS = {
        'mp3': {
            'codec': 'libmp3lame',
            'ext': 'mp3',
            'quality': {'low': '128k', 'medium': '192k', 'high': '320k', 'best': '320k'}
        },
        'm4a': {
            'codec': 'aac',
            'ext': 'm4a',
            'quality': {'low': '128k', 'medium': '192k', 'high': '256k', 'best': '256k'}
        },
        'wav': {
            'codec': 'pcm_s16le',
            'ext': 'wav',
            'quality': None  # WAV não usa compressão
        },
        'flac': {
            'codec': 'flac',
            'ext': 'flac',
            'quality': None  # FLAC usa compressão sem perdas
        },
        'ogg': {
            'codec': 'libvorbis',
            'ext': 'ogg',
            'quality': {'low': '4', 'medium': '6', 'high': '8', 'best': '10'}
        }
    }
    
    def __init__(self, output_dir="audio_downloads"):
        """
        Inicializa o extrator
        
        Args:
            output_dir: Diretório para salvar os arquivos de áudio
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def is_url(self, source):
        """Verifica se a fonte é uma URL"""
        url_patterns = [
            r'https?://',
            r'www\.',
        ]
        return any(re.match(pattern, source) for pattern in url_patterns)
    
    def is_instagram_url(self, url):
        """Verifica se é uma URL do Instagram"""
        patterns = [
            r'https?://(?:www\.)?instagram\.com/p/[\w-]+',
            r'https?://(?:www\.)?instagram\.com/reel/[\w-]+',
            r'https?://(?:www\.)?instagram\.com/tv/[\w-]+',
        ]
        return any(re.match(pattern, url) for pattern in patterns)
    
    def download_video(self, url, temp_file="temp_video"):
        """
        Baixa vídeo da URL
        
        Args:
            url: URL do vídeo
            temp_file: Nome do arquivo temporário
            
        Returns:
            Path do arquivo baixado ou None se falhar
        """
        print(f"📥 Baixando vídeo de: {url}")
        
        output_template = str(self.output_dir / f"{temp_file}.%(ext)s")
        
        ydl_opts = {
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'format': 'best[ext=mp4]/best',
            'progress_hooks': [self.download_progress_hook],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Encontra o arquivo baixado
                ext = info.get('ext', 'mp4')
                downloaded_file = self.output_dir / f"{temp_file}.{ext}"
                
                if downloaded_file.exists():
                    return downloaded_file
                
                # Procura por outros possíveis arquivos
                for file in self.output_dir.glob(f"{temp_file}.*"):
                    if file.suffix in ['.mp4', '.webm', '.mkv', '.avi']:
                        return file
                
                return None
                
        except Exception as e:
            print(f"❌ Erro ao baixar vídeo: {e}")
            return None
    
    def download_progress_hook(self, d):
        """Hook para mostrar progresso do download"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            sys.stdout.write(f"\r⏳ Download: {percent} | Velocidade: {speed}    ")
            sys.stdout.flush()
        elif d['status'] == 'finished':
            print("\n✅ Download concluído!")
    
    def extract_audio(self, video_path, output_format='mp3', quality='high', 
                     output_name=None, keep_video=False):
        """
        Extrai áudio do vídeo
        
        Args:
            video_path: Caminho do vídeo ou URL
            output_format: Formato de saída (mp3, m4a, wav, flac, ogg)
            quality: Qualidade do áudio (low, medium, high, best)
            output_name: Nome personalizado para o arquivo de saída
            keep_video: Se deve manter o arquivo de vídeo após extração
            
        Returns:
            Path do arquivo de áudio ou None se falhar
        """
        
        # Valida formato
        if output_format not in self.AUDIO_FORMATS:
            print(f"❌ Formato '{output_format}' não suportado!")
            print(f"📝 Formatos disponíveis: {', '.join(self.AUDIO_FORMATS.keys())}")
            return None
        
        format_config = self.AUDIO_FORMATS[output_format]
        
        # Se for URL, baixa primeiro
        temp_video = None
        if self.is_url(video_path):
            temp_video = self.download_video(video_path, "temp_video")
            if not temp_video:
                return None
            video_path = temp_video
        else:
            video_path = Path(video_path)
            if not video_path.exists():
                print(f"❌ Arquivo não encontrado: {video_path}")
                return None
        
        # Define nome de saída
        if output_name:
            output_file = self.output_dir / f"{output_name}.{format_config['ext']}"
        else:
            base_name = Path(video_path).stem
            output_file = self.output_dir / f"{base_name}_audio.{format_config['ext']}"
        
        print(f"\n🎵 Extraindo áudio...")
        print(f"📁 Formato: {output_format.upper()}")
        print(f"⚡ Qualidade: {quality}")
        
        try:
            # Configura stream de entrada
            stream = ffmpeg.input(str(video_path))
            
            # Configura parâmetros de áudio baseado no formato
            audio_params = {
                'acodec': format_config['codec'],
            }
            
            # Adiciona bitrate/qualidade se aplicável
            if format_config['quality']:
                if output_format == 'ogg':
                    # OGG usa escala de qualidade (0-10)
                    audio_params['audio_bitrate'] = format_config['quality'].get(quality, '6')
                else:
                    # Outros formatos usam bitrate
                    audio_params['audio_bitrate'] = format_config['quality'].get(quality, '192k')
            
            # Se for WAV, configura para melhor qualidade
            if output_format == 'wav':
                audio_params['ar'] = '44100'  # Sample rate
                audio_params['ac'] = '2'       # Stereo
            
            # Extrai o áudio
            stream = stream.output(str(output_file), **audio_params)
            
            # Executa a conversão
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            print(f"✅ Áudio extraído com sucesso!")
            
            # Mostra informações do arquivo
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)
                print(f"📊 Tamanho: {size_mb:.2f} MB")
                print(f"💾 Salvo em: {output_file}")
                
                # Remove vídeo temporário se necessário
                if temp_video and not keep_video:
                    temp_video.unlink()
                    print("🗑️ Vídeo temporário removido")
                elif temp_video and keep_video:
                    print(f"📹 Vídeo mantido em: {temp_video}")
                
                return output_file
            else:
                print("❌ Erro: arquivo de áudio não foi criado")
                return None
                
        except ffmpeg.Error as e:
            print(f"❌ Erro ao extrair áudio: {e}")
            if temp_video and temp_video.exists():
                temp_video.unlink()
            return None
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            if temp_video and temp_video.exists():
                temp_video.unlink()
            return None
    
    def batch_extract(self, sources, output_format='mp3', quality='high'):
        """
        Extrai áudio de múltiplas fontes
        
        Args:
            sources: Lista de URLs ou caminhos de arquivo
            output_format: Formato de saída
            quality: Qualidade do áudio
            
        Returns:
            Lista de arquivos extraídos com sucesso
        """
        results = []
        total = len(sources)
        
        print(f"\n🎬 Processando {total} arquivo(s)...")
        print("=" * 50)
        
        for i, source in enumerate(sources, 1):
            print(f"\n[{i}/{total}] Processando: {source}")
            
            result = self.extract_audio(source, output_format, quality)
            if result:
                results.append(result)
            
            print("-" * 50)
        
        print(f"\n📊 Resumo: {len(results)}/{total} extrações bem-sucedidas")
        return results

def main():
    """Função principal com interface interativa"""
    print("=" * 60)
    print("🎵 AUDIO EXTRACTOR")
    print("Extrai áudio de vídeos do Instagram ou arquivos locais")
    print("=" * 60)
    
    # Cria extrator
    extractor = AudioExtractor()
    
    # Obtém fonte (URL ou arquivo)
    if len(sys.argv) > 1:
        source = sys.argv[1]
    else:
        print("\n📎 Digite a URL ou caminho do vídeo")
        print("Exemplos:")
        print("  • https://www.instagram.com/p/XXXXX/")
        print("  • /caminho/para/video.mp4")
        print("  • video.mp4 (arquivo local)")
        source = input("\nFonte: ").strip()
    
    if not source:
        print("❌ Nenhuma fonte fornecida!")
        return 1
    
    # Escolhe formato de saída
    print("\n🎵 Escolha o formato de áudio:")
    print("  1. MP3  (mais compatível)")
    print("  2. M4A  (boa qualidade, tamanho menor)")
    print("  3. WAV  (sem compressão, máxima qualidade)")
    print("  4. FLAC (compressão sem perdas)")
    print("  5. OGG  (formato livre)")
    
    formato_opcao = input("\nOpção [1]: ").strip() or "1"
    
    formatos = {
        '1': 'mp3',
        '2': 'm4a',
        '3': 'wav',
        '4': 'flac',
        '5': 'ogg'
    }
    
    output_format = formatos.get(formato_opcao, 'mp3')
    
    # Escolhe qualidade (se aplicável)
    quality = 'high'
    if output_format in ['mp3', 'm4a', 'ogg']:
        print("\n⚡ Escolha a qualidade:")
        print("  1. Baixa   (menor tamanho)")
        print("  2. Média   (balanceado)")
        print("  3. Alta    (melhor qualidade)")
        print("  4. Máxima  (qualidade máxima)")
        
        qualidade_opcao = input("\nOpção [3]: ").strip() or "3"
        
        qualidades = {
            '1': 'low',
            '2': 'medium',
            '3': 'high',
            '4': 'best'
        }
        
        quality = qualidades.get(qualidade_opcao, 'high')
    
    # Pergunta se deve manter o vídeo
    keep_video = False
    if extractor.is_url(source):
        keep = input("\n💾 Manter arquivo de vídeo após extração? (s/N): ").strip().lower()
        keep_video = keep in ['s', 'sim', 'yes', 'y']
    
    # Nome personalizado
    print("\n📝 Nome para o arquivo de áudio (Enter para usar padrão):")
    custom_name = input("Nome: ").strip() or None
    
    # Extrai o áudio
    print("\n" + "=" * 50)
    result = extractor.extract_audio(
        source, 
        output_format=output_format,
        quality=quality,
        output_name=custom_name,
        keep_video=keep_video
    )
    
    if result:
        print("\n🎉 Processo concluído com sucesso!")
        print(f"🎵 Seu arquivo de áudio está em: {result}")
    else:
        print("\n😔 Não foi possível extrair o áudio.")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Operação cancelada pelo usuário.")
        sys.exit(1)
