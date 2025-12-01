#!/usr/bin/env python3
"""
Batch Audio Extractor - Extrai áudio de múltiplos vídeos
Suporta URLs e arquivos locais em lote
"""

import os
import sys
import json
from pathlib import Path
import subprocess
import concurrent.futures
from datetime import datetime

# Instala dependências
try:
    import yt_dlp
except ImportError:
    print("📦 Instalando yt-dlp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp

class BatchAudioExtractor:
    """Extrator de áudio em lote"""
    
    def __init__(self, output_dir="batch_audio", max_workers=3):
        """
        Inicializa o extrator em lote
        
        Args:
            output_dir: Diretório de saída
            max_workers: Número máximo de downloads simultâneos
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        self.results = []
        
    def extract_single(self, source, format='mp3', quality='320'):
        """
        Extrai áudio de uma única fonte
        
        Args:
            source: URL ou arquivo
            format: Formato de áudio
            quality: Qualidade/bitrate
            
        Returns:
            Dict com resultado da extração
        """
        result = {
            'source': source,
            'status': 'pending',
            'output': None,
            'error': None,
            'start_time': datetime.now()
        }
        
        try:
            # Determina o nome base
            if os.path.exists(source):
                base_name = Path(source).stem
            else:
                base_name = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            output_file = self.output_dir / f"{base_name}.{format}"
            
            # Configuração do yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format,
                    'preferredquality': quality,
                }],
            }
            
            print(f"🎵 Processando: {source}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if os.path.exists(source):
                    # Arquivo local - usa ffmpeg diretamente
                    self.extract_local(source, output_file, format, quality)
                    result['output'] = str(output_file)
                else:
                    # URL - usa yt-dlp
                    info = ydl.extract_info(source, download=True)
                    title = info.get('title', base_name)
                    # Procura o arquivo de saída
                    for file in self.output_dir.glob(f"*{title}*.{format}"):
                        result['output'] = str(file)
                        break
                
                result['status'] = 'success'
                result['end_time'] = datetime.now()
                duration = (result['end_time'] - result['start_time']).total_seconds()
                result['duration'] = f"{duration:.1f}s"
                
                print(f"✅ Concluído: {source}")
                
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            result['end_time'] = datetime.now()
            print(f"❌ Falhou: {source} - {e}")
        
        return result
    
    def extract_local(self, input_file, output_file, format='mp3', quality='320'):
        """
        Extrai áudio de arquivo local usando ffmpeg
        
        Args:
            input_file: Arquivo de entrada
            output_file: Arquivo de saída
            format: Formato de áudio
            quality: Qualidade/bitrate
        """
        codec_map = {
            'mp3': 'libmp3lame',
            'm4a': 'aac',
            'wav': 'pcm_s16le',
            'flac': 'flac',
            'ogg': 'libvorbis'
        }
        
        cmd = [
            'ffmpeg', '-i', str(input_file),
            '-vn',  # Sem vídeo
            '-acodec', codec_map.get(format, 'libmp3lame'),
            '-ab', f'{quality}k',
            '-ar', '44100',
            '-y',  # Sobrescrever
            str(output_file)
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
    
    def extract_batch(self, sources, format='mp3', quality='320', parallel=True):
        """
        Extrai áudio de múltiplas fontes
        
        Args:
            sources: Lista de URLs ou arquivos
            format: Formato de áudio
            quality: Qualidade/bitrate
            parallel: Se deve processar em paralelo
            
        Returns:
            Lista de resultados
        """
        print(f"\n📊 Iniciando extração em lote")
        print(f"📁 Total de arquivos: {len(sources)}")
        print(f"🎵 Formato: {format.upper()}")
        print(f"⚡ Qualidade: {quality}k")
        print(f"🔄 Modo: {'Paralelo' if parallel else 'Sequencial'}")
        print("=" * 50)
        
        start_time = datetime.now()
        
        if parallel and len(sources) > 1:
            # Processamento paralelo
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                for source in sources:
                    future = executor.submit(self.extract_single, source, format, quality)
                    futures.append(future)
                
                # Coleta resultados conforme completam
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    self.results.append(result)
        else:
            # Processamento sequencial
            for i, source in enumerate(sources, 1):
                print(f"\n[{i}/{len(sources)}] ", end="")
                result = self.extract_single(source, format, quality)
                self.results.append(result)
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        # Estatísticas
        successful = sum(1 for r in self.results if r['status'] == 'success')
        failed = sum(1 for r in self.results if r['status'] == 'failed')
        
        print("\n" + "=" * 50)
        print("📊 RESUMO DA EXTRAÇÃO")
        print(f"✅ Bem-sucedidas: {successful}/{len(sources)}")
        if failed > 0:
            print(f"❌ Falhadas: {failed}")
        print(f"⏱️ Tempo total: {total_duration:.1f} segundos")
        print(f"📁 Arquivos salvos em: {self.output_dir.absolute()}")
        
        return self.results
    
    def save_report(self, filename="extraction_report.json"):
        """
        Salva relatório da extração em JSON
        
        Args:
            filename: Nome do arquivo de relatório
        """
        report_file = self.output_dir / filename
        
        # Prepara dados serializáveis
        report_data = []
        for result in self.results:
            data = {
                'source': result['source'],
                'status': result['status'],
                'output': result.get('output'),
                'error': result.get('error'),
                'duration': result.get('duration')
            }
            report_data.append(data)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Relatório salvo em: {report_file}")

def load_sources_from_file(filename):
    """
    Carrega lista de URLs/arquivos de um arquivo texto
    
    Args:
        filename: Nome do arquivo com as fontes
        
    Returns:
        Lista de fontes
    """
    sources = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    sources.append(line)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {filename}")
        return []
    
    return sources

def main():
    """Função principal"""
    print("=" * 60)
    print("🎵 BATCH AUDIO EXTRACTOR")
    print("Extrai áudio de múltiplos vídeos simultaneamente")
    print("=" * 60)
    
    # Opções de entrada
    print("\n📝 Como fornecer as fontes?")
    print("  1. Digitar URLs/arquivos manualmente")
    print("  2. Carregar de arquivo texto")
    print("  3. Processar todos os vídeos de uma pasta")
    
    opcao = input("\nOpção [1]: ").strip() or "1"
    
    sources = []
    
    if opcao == "1":
        # Entrada manual
        print("\n📎 Digite as URLs ou arquivos (um por linha)")
        print("Digite 'fim' quando terminar:")
        
        while True:
            source = input("> ").strip()
            if source.lower() in ['fim', 'done', 'exit']:
                break
            if source:
                sources.append(source)
    
    elif opcao == "2":
        # Carregar de arquivo
        filename = input("\n📄 Nome do arquivo com as URLs: ").strip()
        sources = load_sources_from_file(filename)
    
    elif opcao == "3":
        # Processar pasta
        folder = input("\n📁 Caminho da pasta: ").strip()
        folder_path = Path(folder)
        
        if folder_path.exists():
            # Procura por vídeos comuns
            video_extensions = ['.mp4', '.avi', '.mkv', '.webm', '.mov', '.flv']
            for ext in video_extensions:
                sources.extend([str(f) for f in folder_path.glob(f"*{ext}")])
        else:
            print(f"❌ Pasta não encontrada: {folder}")
            return 1
    
    if not sources:
        print("❌ Nenhuma fonte fornecida!")
        return 1
    
    print(f"\n📊 {len(sources)} fonte(s) encontrada(s)")
    
    # Configurações
    print("\n⚙️ Configurações:")
    
    # Formato
    format_input = input("Formato de áudio (mp3/m4a/wav/flac) [mp3]: ").strip() or "mp3"
    
    # Qualidade
    quality_options = {
        'mp3': ['128', '192', '256', '320'],
        'm4a': ['128', '192', '256'],
        'wav': ['44100'],
        'flac': ['44100'],
    }
    
    if format_input in quality_options:
        print(f"Qualidade disponível: {', '.join(quality_options[format_input])}")
        quality = input(f"Qualidade [{quality_options[format_input][-1]}]: ").strip()
        quality = quality or quality_options[format_input][-1]
    else:
        quality = '320'
    
    # Modo de processamento
    parallel = True
    if len(sources) > 1:
        mode = input("Processar em paralelo? (S/n): ").strip().lower()
        parallel = mode != 'n'
    
    # Diretório de saída
    output_dir = input("Diretório de saída [batch_audio]: ").strip() or "batch_audio"
    
    # Cria extrator e processa
    extractor = BatchAudioExtractor(output_dir=output_dir)
    
    print("\n🚀 Iniciando extração...")
    results = extractor.extract_batch(
        sources,
        format=format_input,
        quality=quality,
        parallel=parallel
    )
    
    # Salva relatório
    save_report = input("\n💾 Salvar relatório? (s/N): ").strip().lower()
    if save_report in ['s', 'sim', 'yes', 'y']:
        extractor.save_report()
    
    print("\n🎉 Processo concluído!")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Operação cancelada pelo usuário.")
        sys.exit(1)
