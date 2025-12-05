# Guia de Instalação

Guia completo de instalação e configuração dos serviços de processamento de vídeo.

## Dependências do Sistema

### FFmpeg (Obrigatório para clipes de vídeo)

FFmpeg é necessário para:
- Cortar vídeos (video clipper)
- Processar vídeos
- Extrair áudio para transcrição

**IMPORTANTE:** FFmpeg é um programa do sistema, NÃO é um pacote Python. NÃO use `pip install`.

**macOS (usando Homebrew):**

Primeiro, certifique-se de que o Homebrew está instalado:
```bash
# Verificar se brew está instalado
which brew

# Se não estiver instalado, instalar Homebrew:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Depois instale o FFmpeg:
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows:**
1. Baixe o FFmpeg de: https://ffmpeg.org/download.html
2. Extraia para `C:\ffmpeg`
3. Adicione `C:\ffmpeg\bin` ao PATH do sistema

**Verificar instalação:**
```bash
ffmpeg -version
```

Deve mostrar a versão do FFmpeg instalada.

### yt-dlp (Obrigatório para download)

Ferramenta para baixar vídeos do YouTube.

**Instalar via pip:**
```bash
pip install yt-dlp
```

**Verificar instalação:**
```bash
yt-dlp --version
```

## Dependências Python

### Instalação Básica

Para serviços de legendas apenas:
```bash
pip install yt-dlp
```

### Instalação Completa

Para todos os serviços (vídeo + legendas + transcrição):
```bash
pip install yt-dlp ffmpeg-python python-dotenv openai-whisper torch
```

### Instalação por Componente

**Video Clipper Service:**
```bash
pip install yt-dlp ffmpeg-python python-dotenv
```

**Subtitle Services:**
```bash
pip install yt-dlp
```

**Transcription Service:**
```bash
pip install openai-whisper torch
```

## Configuração

### Arquivo .env (Opcional)

Crie um arquivo `.env` na raiz do projeto:

```bash
# Paths
DOWNLOADS_PATH=downloads/
STORED_PROCESSED_VIDEOS=processed_videos/
TRANSCRIPTIONS_PATH=transcriptions/

# Download settings
DOWNLOAD_QUALITY=best
DOWNLOAD_TIMEOUT=600

# FFmpeg settings (se FFmpeg estiver instalado)
FFMPEG_PATH=ffmpeg
VIDEO_CODEC=libx264
AUDIO_CODEC=aac
CRF_QUALITY=23
FFMPEG_PRESET=medium
INCLUDE_AUDIO=true

# Aspect ratio (original, 9:16, 16:9, 1:1, 4:5)
ASPECT_RATIO=original

# Processing
MAX_CONCURRENT_CLIPS=4
ENABLE_PARALLEL_PROCESSING=true
CLIP_TIMEOUT=120

# Limits
MAX_VIDEO_DURATION=7200
MAX_CLIP_DURATION=300
MAX_CLIPS_PER_VIDEO=50

# Transcription
WHISPER_MODEL=base
TRANSCRIPTION_LANGUAGE=
INCLUDE_TIMESTAMPS=true

# Logging
LOG_LEVEL=INFO
```

### Diretórios

Os diretórios serão criados automaticamente:
- `downloads/` - Vídeos baixados
- `processed_videos/` - Clipes processados
- `subtitles/` - Legendas baixadas
- `transcriptions/` - Transcrições

## Verificação da Instalação

### Script de Teste

Crie um arquivo `test_installation.py`:

```python
import subprocess
import sys

def check_command(cmd, name):
    """Check if command is available"""
    try:
        result = subprocess.run(
            [cmd, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ {name} installed")
            return True
        else:
            print(f"✗ {name} not working properly")
            return False
    except FileNotFoundError:
        print(f"✗ {name} not found")
        return False
    except Exception as e:
        print(f"✗ {name} error: {e}")
        return False

def check_python_package(package, import_name=None):
    """Check if Python package is installed"""
    if import_name is None:
        import_name = package

    try:
        __import__(import_name)
        print(f"✓ Python package '{package}' installed")
        return True
    except ImportError:
        print(f"✗ Python package '{package}' not found")
        return False

print("Checking installation...\n")

print("System Dependencies:")
ffmpeg_ok = check_command('ffmpeg', 'FFmpeg')
ytdlp_ok = check_command('yt-dlp', 'yt-dlp')

print("\nPython Packages:")
whisper_ok = check_python_package('openai-whisper', 'whisper')
dotenv_ok = check_python_package('python-dotenv', 'dotenv')

print("\n" + "="*50)
if ffmpeg_ok and ytdlp_ok:
    print("✓ All required dependencies installed!")
    print("\nYou can use:")
    print("  - Video Clipper Service")
    print("  - Subtitle Download Service")
    print("  - Subtitle Clipper Service")
    if whisper_ok:
        print("  - Video Transcription Service")
elif ytdlp_ok:
    print("✓ Partial installation complete!")
    print("\nYou can use:")
    print("  - Subtitle Download Service")
    print("\nTo enable video processing, install FFmpeg:")
    print("  macOS:  brew install ffmpeg")
    print("  Ubuntu: sudo apt-get install ffmpeg")
else:
    print("✗ Missing required dependencies")
    print("\nInstall missing dependencies:")
    if not ytdlp_ok:
        print("  pip install yt-dlp")
    if not ffmpeg_ok:
        print("  macOS:  brew install ffmpeg")
        print("  Ubuntu: sudo apt-get install ffmpeg")

print("="*50)
```

Execute:
```bash
python test_installation.py
```

### Teste Rápido de Cada Serviço

**Subtitle Download:**
```bash
python cli_subtitle.py list "dQw4w9WgXcQ"
```

**Subtitle Clipper (requer yt-dlp):**
```bash
python cli_subtitle_clipper.py --help
```

**Video Clipper (requer FFmpeg + yt-dlp):**
```bash
python cli_clipper.py --help
```

## Troubleshooting

### FFmpeg não encontrado

**Erro:**
```
Invalid configuration: FFmpeg not found at: ffmpeg
```

**Solução:**

1. Instalar FFmpeg:
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```

2. Verificar instalação:
   ```bash
   which ffmpeg
   ffmpeg -version
   ```

3. Se instalado em local customizado, configurar no `.env`:
   ```
   FFMPEG_PATH=/caminho/customizado/ffmpeg
   ```

### yt-dlp não encontrado

**Erro:**
```
yt-dlp not found. Install with: pip install yt-dlp
```

**Solução:**
```bash
pip install yt-dlp

# Verificar
yt-dlp --version
```

### Erro de permissão ao criar diretórios

**Erro:**
```
No write permission for: processed_videos/
```

**Solução:**
```bash
# Dar permissões ao diretório
chmod -R 755 processed_videos/

# Ou criar manualmente com permissões corretas
mkdir -p processed_videos downloads subtitles transcriptions
```

### Whisper não encontrado

**Erro:**
```
ModuleNotFoundError: No module named 'whisper'
```

**Solução:**
```bash
pip install openai-whisper torch
```

### Erro ao baixar legenda

**Erro:**
```
Failed to download en subtitle: Language 'en' may not be available
```

**Solução:**
1. Verificar legendas disponíveis:
   ```bash
   python cli_subtitle.py list "VIDEO_ID"
   ```

2. Usar idioma disponível ou habilitar auto-geradas:
   ```bash
   python cli_subtitle.py download "VIDEO_ID" -l pt
   ```

### Video sem heatmap

**Erro:**
```
No heatmap data available. Video may need 50,000+ views.
```

**Solução:**
- O replay heatmap do YouTube só está disponível para vídeos populares (geralmente 50.000+ visualizações)
- Use outro vídeo com mais visualizações

## Uso Sem FFmpeg

Se você não precisa processar vídeos, pode usar apenas os serviços de legenda:

```python
# Isso funciona sem FFmpeg
from subtitle_downloader import download_subtitle
from pathlib import Path

subtitle_path = download_subtitle(
    video_url="VIDEO_ID",
    video_id="VIDEO_ID",
    language="en",
    subtitles_path=Path("./subtitles")
)
```

## Instalação em Diferentes Ambientes

### Docker (Exemplo)

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install yt-dlp ffmpeg-python python-dotenv openai-whisper torch

# Copy application
COPY . /app
WORKDIR /app

CMD ["bash"]
```

### Virtual Environment

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependências
pip install yt-dlp ffmpeg-python python-dotenv openai-whisper torch
```

### Conda

```bash
# Criar ambiente
conda create -n video-processor python=3.10

# Ativar
conda activate video-processor

# Instalar FFmpeg via conda
conda install -c conda-forge ffmpeg

# Instalar Python packages
pip install yt-dlp ffmpeg-python python-dotenv openai-whisper torch
```

## Recursos do Sistema

### Requisitos Mínimos

- **CPU**: 2+ cores
- **RAM**: 4GB (8GB recomendado para Whisper)
- **Disk**: 10GB+ livre para downloads e processamento
- **Network**: Conexão estável para downloads

### Requisitos por Serviço

**Subtitle Download:**
- RAM: 100MB
- Disk: ~50KB por legenda
- Network: Necessário

**Video Clipper:**
- RAM: 500MB-1GB
- CPU: 2+ cores (4+ para parallel)
- Disk: ~100MB por 10min de vídeo

**Transcription (Whisper):**
- RAM: 1-8GB (depende do modelo)
- CPU: Multicore recomendado
- GPU: Opcional (muito mais rápido)

## Suporte

Para problemas de instalação:

1. Verifique as versões:
   ```bash
   python --version  # 3.8+
   ffmpeg -version
   yt-dlp --version
   ```

2. Revise os logs de erro

3. Consulte a documentação específica:
   - SUBTITLE_SERVICE.md
   - SUBTITLE_CLIPPER_SERVICE.md
   - video_clipper_service.md
   - TRANSCRIPTION_SERVICE.md

4. Reporte issues com:
   - Sistema operacional e versão
   - Versões das dependências
   - Comando completo executado
   - Mensagem de erro completa