# Video Transcription Service

Serviço para transcrição de vídeos usando OpenAI Whisper. Suporta transcrição de URLs (YouTube, Instagram, etc.) ou arquivos de vídeo locais.

## Características

- Transcrição automática usando OpenAI Whisper
- Suporte para múltiplos idiomas (detecção automática ou manual)
- 5 tamanhos de modelo (tiny a large) para balancear velocidade e precisão
- Timestamps opcionais para navegação temporal
- Download automático de vídeos se necessário
- Saída em Markdown e JSON
- Interface CLI fácil de usar

## Arquivos do Serviço

```
ab/dc/downloaders/
├── video_transcriber.py      # Serviço principal de transcrição
├── cli_transcriber.py         # Interface de linha de comando
├── config_manager.py          # Configuração (atualizado)
└── TRANSCRIPTION_SERVICE.md   # Esta documentação
```

## Dependências

O serviço instala automaticamente as dependências necessárias:
- `openai-whisper` - Modelo de transcrição Whisper da OpenAI
- `torch` - PyTorch para execução do modelo

**Pré-requisitos do sistema:**
- FFmpeg (para extração de áudio)
- Python 3.8+

## Instalação

### 1. Instalar FFmpeg (se não tiver)

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download de https://ffmpeg.org

### 2. Configurar variáveis de ambiente

Copie o arquivo `.env.example` e configure:

```bash
# Diretório de saída das transcrições
TRANSCRIPTIONS_PATH=transcriptions/

# Modelo Whisper (tiny, base, small, medium, large)
WHISPER_MODEL=base

# Código do idioma (pt, en, es, fr, etc.)
# Deixe vazio para detecção automática
TRANSCRIPTION_LANGUAGE=

# Incluir timestamps na transcrição (true/false)
INCLUDE_TIMESTAMPS=true
```

## Uso

### CLI Tool (Recomendado)

#### 1. Transcrever de URL

```bash
# YouTube
python ab/dc/downloaders/cli_transcriber.py --url "https://youtube.com/watch?v=VIDEO_ID"

# Com modelo específico
python ab/dc/downloaders/cli_transcriber.py --url "URL" --model medium

# Com idioma específico
python ab/dc/downloaders/cli_transcriber.py --url "URL" --language pt
```

#### 2. Transcrever vídeo já baixado

```bash
python ab/dc/downloaders/cli_transcriber.py --video-id "VIDEO_ID"
```

#### 3. Transcrever arquivo local

```bash
python ab/dc/downloaders/cli_transcriber.py --file "/path/to/video.mp4"
```

#### 4. Opções avançadas

```bash
# Sem timestamps
python ab/dc/downloaders/cli_transcriber.py --url "URL" --no-timestamps

# Diretório de saída customizado
python ab/dc/downloaders/cli_transcriber.py --url "URL" --output-dir "./my_transcriptions"

# Salvar JSON também
python ab/dc/downloaders/cli_transcriber.py --url "URL" --format both

# Modo verbose
python ab/dc/downloaders/cli_transcriber.py --url "URL" -v
```

### Uso Programático

#### Transcrever de URL

```python
from pathlib import Path
from ab.dc.downloaders.video_transcriber import transcribe_from_url
from ab.dc.downloaders.config_manager import get_config

config = get_config()

result = transcribe_from_url(
    video_url="https://youtube.com/watch?v=VIDEO_ID",
    video_id="VIDEO_ID",
    downloads_path=config.downloads_path,
    transcriptions_path=config.transcriptions_path,
    model_size="base",
    language="pt",  # ou None para detecção automática
    include_timestamps=True,
    download_if_needed=True
)

print(f"Language: {result['detected_language']}")
print(f"Full text: {result['full_text']}")
print(f"Markdown file: {result['markdown_file']}")
```

#### Transcrever arquivo local

```python
from pathlib import Path
from ab.dc.downloaders.video_transcriber import transcribe_video

result = transcribe_video(
    video_path=Path("path/to/video.mp4"),
    model_size="base",
    language=None,  # Detecção automática
    include_timestamps=True,
    output_dir=Path("transcriptions/")
)

# Acessar segmentos com timestamps
for segment in result.get('segments', []):
    print(f"[{segment['start_formatted']} - {segment['end_formatted']}]")
    print(segment['text'])
```

#### Transcrição em lote

```python
from pathlib import Path
from ab.dc.downloaders.video_transcriber import batch_transcribe_videos

video_files = [
    Path("video1.mp4"),
    Path("video2.mp4"),
    Path("video3.mp4")
]

results = batch_transcribe_videos(
    video_paths=video_files,
    output_dir=Path("transcriptions/"),
    model_size="base",
    language="pt",
    include_timestamps=True
)

print(f"Successful: {results['successful']}")
print(f"Failed: {results['failed']}")
print(f"Total time: {results['total_time']:.1f}s")
```

## Modelos Whisper

| Modelo | Tamanho | VRAM | Velocidade | Precisão | Uso recomendado |
|--------|---------|------|------------|----------|------------------|
| tiny   | ~39M    | ~1GB | Muito rápido | Básica | Testes rápidos |
| base   | ~74M    | ~1GB | Rápido | Boa | Uso geral (padrão) |
| small  | ~244M   | ~2GB | Moderado | Muito boa | Conteúdo importante |
| medium | ~769M   | ~5GB | Lento | Excelente | Alta qualidade |
| large  | ~1550M  | ~10GB | Muito lento | Máxima | Produção profissional |

## Idiomas Suportados

Whisper suporta 99 idiomas. Principais:

- `pt` - Português
- `en` - Inglês
- `es` - Espanhol
- `fr` - Francês
- `de` - Alemão
- `it` - Italiano
- `ja` - Japonês
- `zh` - Chinês
- `ko` - Coreano
- `ru` - Russo
- `ar` - Árabe
- `hi` - Hindi

Deixe vazio para detecção automática.

## Formato de Saída

### Markdown (padrão)

```markdown
# Transcription: video.mp4

## Metadata

- **Source file:** video.mp4
- **Detected language:** pt
- **Model used:** base
- **Transcription date:** 2025-01-15 10:30:00
- **Processing time:** 45.2s

## Transcription

**[00:00 - 00:15]**
Olá, bem-vindo ao nosso vídeo sobre...

**[00:15 - 00:30]**
Hoje vamos falar sobre...

---

## Full Text

Olá, bem-vindo ao nosso vídeo sobre... Hoje vamos falar sobre...
```

### JSON

```json
{
  "success": true,
  "video_path": "/path/to/video.mp4",
  "video_name": "video.mp4",
  "detected_language": "pt",
  "full_text": "Texto completo da transcrição...",
  "model_used": "base",
  "processing_time": 45.2,
  "segments": [
    {
      "start": 0.0,
      "end": 15.5,
      "start_formatted": "00:00",
      "end_formatted": "00:15",
      "text": "Olá, bem-vindo ao nosso vídeo sobre..."
    }
  ],
  "markdown_file": "/path/to/transcriptions/video_transcription.md"
}
```

## API Reference

### transcribe_from_url()

Transcreve vídeo de URL (baixa se necessário).

**Parâmetros:**
- `video_url` (str): URL do vídeo
- `video_id` (str): ID do vídeo para nome do arquivo
- `downloads_path` (Path): Diretório de downloads
- `transcriptions_path` (Path): Diretório de saída
- `model_size` (str): Tamanho do modelo Whisper
- `language` (str, opcional): Código do idioma
- `include_timestamps` (bool): Incluir timestamps
- `download_if_needed` (bool): Baixar se não existir

**Retorna:** Dict com resultado da transcrição

### transcribe_video()

Transcreve arquivo de vídeo local.

**Parâmetros:**
- `video_path` (Path): Caminho do vídeo
- `model_size` (str): Tamanho do modelo
- `language` (str, opcional): Código do idioma
- `include_timestamps` (bool): Incluir timestamps
- `output_dir` (Path, opcional): Diretório de saída

**Retorna:** Dict com resultado da transcrição

### batch_transcribe_videos()

Transcreve múltiplos vídeos em lote.

**Parâmetros:**
- `video_paths` (List[Path]): Lista de caminhos de vídeo
- `output_dir` (Path): Diretório de saída
- `model_size` (str): Tamanho do modelo
- `language` (str, opcional): Código do idioma
- `include_timestamps` (bool): Incluir timestamps

**Retorna:** Dict com resultados do lote

## Performance

### Tempos de Processamento Estimados

Vídeo de 10 minutos (Core i7, GPU NVIDIA):

| Modelo | Tempo | Precisão |
|--------|-------|----------|
| tiny   | ~30s  | 70-80%   |
| base   | ~1min | 80-85%   |
| small  | ~2min | 85-90%   |
| medium | ~5min | 90-95%   |
| large  | ~10min| 95-98%   |

### Otimizações

1. **Use GPU se disponível:** Instale `torch` com suporte CUDA
2. **Escolha o modelo adequado:** base é suficiente para maioria dos casos
3. **Processe em lote:** Use `batch_transcribe_videos()` para múltiplos vídeos
4. **Extraia áudio primeiro:** Para vídeos grandes, extraia áudio separadamente

## Tratamento de Erros

```python
from ab.dc.downloaders.video_transcriber import (
    transcribe_from_url,
    TranscriptionError
)

try:
    result = transcribe_from_url(...)
except FileNotFoundError as e:
    print(f"Arquivo não encontrado: {e}")
except TranscriptionError as e:
    print(f"Erro na transcrição: {e}")
except Exception as e:
    print(f"Erro inesperado: {e}")
```

## Integração com outros serviços

### Com Video Clipper Service

```python
from ab.dc.downloaders.video_clipper_service import process_video_moments
from ab.dc.downloaders.video_transcriber import transcribe_from_url

# 1. Criar clips de momentos populares
clips_result = process_video_moments(moments_data)

# 2. Transcrever o vídeo original
transcription = transcribe_from_url(
    video_url=moments_data['video_url'],
    video_id=moments_data['video_id'],
    ...
)

# 3. Combinar dados
combined = {
    'clips': clips_result,
    'transcription': transcription
}
```

### Com API FastAPI

```python
from fastapi import FastAPI, HTTPException
from ab.dc.downloaders.video_transcriber import transcribe_from_url

app = FastAPI()

@app.post("/api/v1/transcribe")
async def transcribe_endpoint(
    video_url: str,
    model_size: str = "base",
    language: str = None
):
    try:
        result = transcribe_from_url(
            video_url=video_url,
            video_id=extract_video_id(video_url),
            model_size=model_size,
            language=language,
            ...
        )
        return result
    except Exception as e:
        raise HTTPException(500, str(e))
```

## Troubleshooting

### "FFmpeg not found"

```bash
# Instale o FFmpeg
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Linux
```

### "Model download failed"

O Whisper baixa modelos automaticamente na primeira execução. Se falhar:

```bash
# Baixe manualmente
python -c "import whisper; whisper.load_model('base')"
```

### "CUDA out of memory"

Use modelo menor ou modo CPU:

```python
# Forçar uso de CPU
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
```

### "Audio extraction failed"

Verifique se o vídeo tem áudio:

```bash
ffprobe video.mp4
```

## Exemplos de Uso Avançado

### Transcrever apenas um trecho

```python
import subprocess
from pathlib import Path
from ab.dc.downloaders.video_transcriber import transcribe_video

# Extrair trecho com ffmpeg
subprocess.run([
    'ffmpeg', '-i', 'video.mp4',
    '-ss', '00:01:30',  # Start
    '-t', '00:05:00',   # Duration
    'excerpt.mp4'
])

# Transcrever trecho
result = transcribe_video(Path('excerpt.mp4'))
```

### Transcrever com callback de progresso

```python
from ab.dc.downloaders.video_transcriber import transcribe_video
import logging

# Habilitar logs detalhados
logging.basicConfig(level=logging.INFO)

result = transcribe_video(
    video_path=Path('video.mp4'),
    model_size='base'
)
```

### Salvar em múltiplos formatos

```python
import json
from ab.dc.downloaders.video_transcriber import transcribe_video

result = transcribe_video(...)

# Markdown (automático)
# JSON
with open('transcription.json', 'w') as f:
    json.dump(result, f, indent=2)

# TXT (apenas texto)
with open('transcription.txt', 'w') as f:
    f.write(result['full_text'])

# SRT (legendas)
with open('transcription.srt', 'w') as f:
    for i, seg in enumerate(result['segments'], 1):
        f.write(f"{i}\n")
        f.write(f"{format_srt_time(seg['start'])} --> {format_srt_time(seg['end'])}\n")
        f.write(f"{seg['text']}\n\n")
```

## Roadmap

Funcionalidades futuras planejadas:
- [ ] Suporte para múltiplos speakers (diarização)
- [ ] Exportação para SRT/VTT (legendas)
- [ ] Transcrição em tempo real (streaming)
- [ ] Suporte para áudio de múltiplas faixas
- [ ] Cache de transcrições
- [ ] API REST completa
- [ ] Dashboard web para visualização

## Contribuindo

Para adicionar novas funcionalidades ao serviço de transcrição, siga o padrão estabelecido:

1. Adicione funções em `video_transcriber.py`
2. Atualize CLI em `cli_transcriber.py` se necessário
3. Adicione configurações em `config_manager.py`
4. Atualize `.env.example`
5. Documente neste arquivo

## Licença

Este serviço faz parte do projeto download-ig-videos e segue a mesma licença.

## Suporte

Para problemas ou dúvidas:
1. Verifique a seção Troubleshooting
2. Consulte a documentação do Whisper: https://github.com/openai/whisper
3. Abra uma issue no repositório