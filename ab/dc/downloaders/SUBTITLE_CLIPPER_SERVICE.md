# Subtitle Clipper Service

Serviço para gerar arquivos de legenda para cada clipe/corte de vídeo baseado nos momentos populares extraídos do replay heatmap do YouTube.

## Visão Geral

Este serviço automatiza a criação de arquivos de legenda segmentados para cada clipe de vídeo:

1. Extrai momentos populares do vídeo usando o replay heatmap (via `get_popular_moments`)
2. Baixa a legenda completa do vídeo do YouTube
3. Segmenta a legenda em arquivos individuais para cada clipe
4. Ajusta os timestamps relativos ao início de cada clipe
5. Usa a mesma convenção de nomenclatura dos clipes de vídeo

## Features

- Geração automática de legendas para cada clipe
- Suporte a múltiplos idiomas
- Ajuste automático de timestamps
- Formatos VTT e SRT
- Convenção de nomenclatura consistente com clipes de vídeo
- Filtragem inteligente de segmentos
- Integração com o serviço de extração de momentos

## Instalação

```bash
pip install yt-dlp
```

## Uso Rápido

### CLI

```bash
# Extrair momentos e gerar legendas (inglês)
python cli_subtitle_clipper.py --video-id "dQw4w9WgXcQ"

# Múltiplos idiomas
python cli_subtitle_clipper.py --video-id "dQw4w9WgXcQ" -l en -l pt -l es

# A partir de arquivo JSON de momentos
python cli_subtitle_clipper.py --input moments.json -l en

# Formato SRT
python cli_subtitle_clipper.py --video-id "dQw4w9WgXcQ" -l en -f srt

# Com aspect ratio para nomenclatura
python cli_subtitle_clipper.py --video-id "dQw4w9WgXcQ" -l en --aspect-ratio 9:16
```

### Python API

```python
from pathlib import Path
from subtitle_clipper_service import extract_and_generate_subtitles

# Workflow completo
result = extract_and_generate_subtitles(
    video_url_or_id="dQw4w9WgXcQ",
    languages=["en", "pt"],
    format="vtt",
    aspect_ratio="9:16"
)

print(f"Created {result['clip_subtitles_created']} subtitle files")
```

## Convenção de Nomenclatura

Os arquivos de legenda seguem a mesma convenção dos clipes de vídeo:

```
{video_id}_{clip_number:04d}_{duration}s_score_{score}_{ratio}_{lang}.{ext}
```

### Exemplos

```
processed_videos/
└── dQw4w9WgXcQ/
    ├── dQw4w9WgXcQ_0000_30s_score_095_9x16_en.vtt
    ├── dQw4w9WgXcQ_0000_30s_score_095_9x16_pt.vtt
    ├── dQw4w9WgXcQ_0001_25s_score_087_9x16_en.vtt
    └── dQw4w9WgXcQ_0001_25s_score_087_9x16_pt.vtt
```

### Componentes do Nome

- `video_id`: ID do vídeo no YouTube (11 caracteres)
- `clip_number`: Número sequencial do clipe (0000, 0001, ...)
- `duration`: Duração do clipe em segundos (30s, 25.5s)
- `score`: Score de engajamento × 100 (095 = 0.95, 087 = 0.87)
- `ratio`: Aspect ratio (9x16, 16x9, original)
- `lang`: Código do idioma (en, pt, es)
- `ext`: Extensão do formato (vtt, srt)

## API Reference

### `extract_and_generate_subtitles()`

Workflow completo: extrai momentos e gera legendas dos clipes.

```python
def extract_and_generate_subtitles(
    video_url_or_id: str,
    languages: Optional[List[str]] = None,
    max_duration: int = 40,
    min_duration: int = 10,
    threshold: float = 0.45,
    format: str = 'vtt',
    aspect_ratio: str = 'original',
    subtitles_download_path: Path = Path("./subtitles"),
    clips_output_path: Path = Path("./processed_videos")
) -> Dict
```

**Parâmetros:**
- `video_url_or_id`: URL ou ID do vídeo no YouTube
- `languages`: Lista de códigos de idioma (padrão: ['en'])
- `max_duration`: Duração máxima do momento em segundos
- `min_duration`: Duração mínima do momento em segundos
- `threshold`: Valor mínimo relativo para detecção de picos
- `format`: Formato da legenda ('vtt' ou 'srt')
- `aspect_ratio`: Aspect ratio para nomenclatura
- `subtitles_download_path`: Diretório para baixar legendas completas
- `clips_output_path`: Diretório para salvar legendas dos clipes

**Retorna:**
```python
{
    "success": bool,
    "video_id": str,
    "video_url": str,
    "moments_extracted": int,
    "languages_processed": List[str],
    "total_clips": int,
    "clip_subtitles_created": int,
    "clip_subtitles": [
        {
            "clip_id": int,
            "language": str,
            "path": str,
            "filename": str,
            "segments_count": int,
            "start_time": float,
            "end_time": float,
            "duration": float
        },
        ...
    ],
    "processing_time": float,
    "error": str (se success=False)
}
```

### `process_moments_subtitles()`

Gera legendas de clipes a partir de dados de momentos existentes.

```python
def process_moments_subtitles(
    moments_data: Dict,
    subtitles_download_path: Path = Path("./subtitles"),
    clips_output_path: Path = Path("./processed_videos"),
    languages: Optional[List[str]] = None,
    format: str = 'vtt',
    aspect_ratio: str = 'original',
    force_redownload: bool = False
) -> Dict
```

**Parâmetros:**
- `moments_data`: Dicionário retornado por `get_popular_moments()`
- `subtitles_download_path`: Diretório para baixar legendas completas
- `clips_output_path`: Diretório para salvar legendas dos clipes
- `languages`: Lista de códigos de idioma
- `format`: Formato da legenda ('vtt' ou 'srt')
- `aspect_ratio`: Aspect ratio para nomenclatura
- `force_redownload`: Forçar re-download da legenda

### `create_clip_subtitle()`

Cria arquivo de legenda para um único clipe.

```python
def create_clip_subtitle(
    video_id: str,
    full_subtitle_path: Path,
    clip_number: int,
    start_time: float,
    end_time: float,
    score: float,
    output_dir: Path,
    language: str = 'en',
    aspect_ratio: str = 'original',
    format: str = 'vtt'
) -> Path
```

### `filter_subtitle_segments()`

Filtra segmentos de legenda dentro de um intervalo de tempo.

```python
def filter_subtitle_segments(
    segments: List[Dict],
    start_time: float,
    end_time: float
) -> List[Dict]
```

## Exemplos de Uso

### Exemplo 1: Workflow Completo

```python
from subtitle_clipper_service import extract_and_generate_subtitles

# Extrair momentos e gerar legendas
result = extract_and_generate_subtitles(
    video_url_or_id="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    languages=["en", "pt", "es"],
    max_duration=30,
    min_duration=15,
    format="vtt",
    aspect_ratio="9:16"
)

if result['success']:
    print(f"Momentos extraídos: {result['moments_extracted']}")
    print(f"Idiomas processados: {', '.join(result['languages_processed'])}")
    print(f"Legendas criadas: {result['clip_subtitles_created']}")

    for subtitle in result['clip_subtitles']:
        print(f"  {subtitle['filename']} - {subtitle['segments_count']} segmentos")
else:
    print(f"Erro: {result['error']}")
```

### Exemplo 2: A Partir de Momentos Existentes

```python
from pathlib import Path
from subtitle_clipper_service import process_moments_subtitles
from replay_heatmap import get_popular_moments

# Primeiro, extrair momentos
moments = get_popular_moments("dQw4w9WgXcQ")

# Depois, gerar legendas
result = process_moments_subtitles(
    moments_data=moments,
    languages=["en", "pt"],
    format="srt",
    clips_output_path=Path("./my_clips")
)

print(f"Legendas criadas: {result['clip_subtitles_created']}")
```

### Exemplo 3: Integração com Pipeline de Clipes

```python
from pathlib import Path
from replay_heatmap import get_popular_moments
from video_clipper_service import process_video_moments
from subtitle_clipper_service import process_moments_subtitles

# 1. Extrair momentos populares
moments = get_popular_moments("dQw4w9WgXcQ", max_duration=30)

# 2. Criar clipes de vídeo
video_result = process_video_moments(
    moments,
    aspect_ratio="9:16"
)

# 3. Criar legendas dos clipes
subtitle_result = process_moments_subtitles(
    moments_data=moments,
    languages=["en", "pt"],
    aspect_ratio="9:16"  # Mesmo aspect ratio dos vídeos
)

print(f"Clipes de vídeo: {video_result['clips_created']}")
print(f"Legendas criadas: {subtitle_result['clip_subtitles_created']}")
```

### Exemplo 4: Criar Legenda para Clipe Específico

```python
from pathlib import Path
from subtitle_clipper_service import create_clip_subtitle

# Criar legenda para um clipe específico
subtitle_path = create_clip_subtitle(
    video_id="dQw4w9WgXcQ",
    full_subtitle_path=Path("./subtitles/dQw4w9WgXcQ_en.vtt"),
    clip_number=0,
    start_time=15.5,
    end_time=45.5,
    score=0.95,
    output_dir=Path("./processed_videos"),
    language="en",
    aspect_ratio="9:16",
    format="vtt"
)

print(f"Legenda criada: {subtitle_path}")
```

### Exemplo 5: Batch Processing

```python
from pathlib import Path
from subtitle_clipper_service import extract_and_generate_subtitles

video_ids = ["VIDEO_ID_1", "VIDEO_ID_2", "VIDEO_ID_3"]
languages = ["en", "pt"]

results = []
for video_id in video_ids:
    result = extract_and_generate_subtitles(
        video_url_or_id=video_id,
        languages=languages,
        format="vtt"
    )
    results.append(result)

    if result['success']:
        print(f"{video_id}: {result['clip_subtitles_created']} legendas")
    else:
        print(f"{video_id}: Erro - {result['error']}")

# Estatísticas
total_subtitles = sum(r['clip_subtitles_created'] for r in results if r['success'])
print(f"\nTotal de legendas criadas: {total_subtitles}")
```

## CLI - Exemplos Completos

### Extrair Momentos e Gerar Legendas

```bash
# Inglês (padrão)
python cli_subtitle_clipper.py --video-id "dQw4w9WgXcQ"

# Múltiplos idiomas
python cli_subtitle_clipper.py --video-id "dQw4w9WgXcQ" \
  -l en -l pt -l es -l fr

# Com configurações personalizadas
python cli_subtitle_clipper.py --video-id "dQw4w9WgXcQ" \
  -l en \
  --max-duration 25 \
  --min-duration 15 \
  --threshold 0.5 \
  --aspect-ratio 9:16
```

### A Partir de Arquivo de Momentos

```bash
# Gerar legendas de arquivo JSON
python cli_subtitle_clipper.py --input moments.json -l en -l pt

# Com diretórios personalizados
python cli_subtitle_clipper.py --input moments.json \
  -l en \
  --output-dir ./my_clips \
  --subtitles-dir ./my_subtitles
```

### Formato e Saída

```bash
# Formato SRT
python cli_subtitle_clipper.py --video-id "dQw4w9WgXcQ" -l en -f srt

# Salvar resultado em JSON
python cli_subtitle_clipper.py --video-id "dQw4w9WgXcQ" \
  -l en \
  --json-output result.json

# Forçar re-download de legendas
python cli_subtitle_clipper.py --video-id "dQw4w9WgXcQ" \
  -l en \
  --force-redownload
```

### Pipeline Completo

```bash
# 1. Extrair momentos e salvar
python ../analysers/replay_heatmap.py "dQw4w9WgXcQ" > moments.json

# 2. Criar clipes de vídeo
python cli_clipper.py --input moments.json --aspect-ratio 9:16

# 3. Criar legendas dos clipes
python cli_subtitle_clipper.py --input moments.json \
  -l en -l pt \
  --aspect-ratio 9:16
```

## Estrutura de Diretórios

```
projeto/
├── subtitles/                    # Legendas completas dos vídeos
│   ├── dQw4w9WgXcQ_en.vtt
│   ├── dQw4w9WgXcQ_pt.vtt
│   └── dQw4w9WgXcQ_es.vtt
│
└── processed_videos/             # Clipes e legendas
    └── dQw4w9WgXcQ/
        ├── dQw4w9WgXcQ_0000_30s_score_095_9x16.mp4
        ├── dQw4w9WgXcQ_0000_30s_score_095_9x16_en.vtt
        ├── dQw4w9WgXcQ_0000_30s_score_095_9x16_pt.vtt
        ├── dQw4w9WgXcQ_0001_25s_score_087_9x16.mp4
        ├── dQw4w9WgXcQ_0001_25s_score_087_9x16_en.vtt
        └── dQw4w9WgXcQ_0001_25s_score_087_9x16_pt.vtt
```

## Formatos de Legenda

### VTT (WebVTT)

Formato padrão, otimizado para web:

```
WEBVTT

00:00:00.000 --> 00:00:03.500
Primeira linha da legenda

00:00:03.500 --> 00:00:07.000
Segunda linha da legenda
```

### SRT (SubRip)

Formato alternativo, compatível com editores:

```
1
00:00:00,000 --> 00:00:03,500
Primeira linha da legenda

2
00:00:03,500 --> 00:00:07,000
Segunda linha da legenda
```

## Ajuste de Timestamps

O serviço ajusta automaticamente os timestamps relativos ao início do clipe:

**Vídeo original (00:15 - 00:45):**
```
00:00:15.000 --> 00:00:18.000
Texto no vídeo original
```

**Clipe (00:00 - 00:30):**
```
00:00:00.000 --> 00:00:03.000
Texto no vídeo original
```

Os timestamps são recalculados subtraindo o tempo de início do clipe.

## Códigos de Idioma

Códigos comuns suportados pelo YouTube:

| Código | Idioma |
|--------|--------|
| en | Inglês |
| pt | Português |
| es | Espanhol |
| fr | Francês |
| de | Alemão |
| it | Italiano |
| ja | Japonês |
| ko | Coreano |
| zh | Chinês |
| ru | Russo |
| ar | Árabe |
| hi | Hindi |

## Integração com Outros Serviços

### Com Video Clipper Service

```python
from replay_heatmap import get_popular_moments
from video_clipper_service import process_video_moments
from subtitle_clipper_service import process_moments_subtitles

# Extrair momentos
moments = get_popular_moments("VIDEO_ID")

# Criar vídeos E legendas
video_result = process_video_moments(moments, aspect_ratio="9:16")
subtitle_result = process_moments_subtitles(
    moments,
    languages=["en", "pt"],
    aspect_ratio="9:16"
)
```

### Com FastAPI

```python
from fastapi import FastAPI
from subtitle_clipper_service import extract_and_generate_subtitles

app = FastAPI()

@app.post("/api/v1/generate-clip-subtitles")
async def generate_subtitles(video_id: str, languages: list[str]):
    result = extract_and_generate_subtitles(
        video_url_or_id=video_id,
        languages=languages,
        format="vtt"
    )
    return result
```

## Tratamento de Erros

Todos os erros são capturados e retornados no resultado:

```python
result = extract_and_generate_subtitles("INVALID_ID")

if not result['success']:
    print(f"Erro: {result['error']}")
    # Possíveis erros:
    # - "Failed to extract moments: ..."
    # - "No moments found in input data"
    # - "Failed to process subtitles for any language"
    # - "Failed to download {language} subtitle: ..."
```

## Performance

### Tempos de Processamento (Estimados)

- Extração de momentos: 3-8 segundos
- Download de legenda: 2-5 segundos por idioma
- Processamento de 6 clipes: 1-2 segundos
- **Total**: 6-15 segundos por vídeo (1 idioma)

### Uso de Recursos

- CPU: ~10-20%
- Memória: ~100-200MB
- Disco: ~5-50KB por arquivo de legenda
- Network: Apenas durante download das legendas

## Notas Importantes

1. **Legendas Disponíveis**: Nem todos os vídeos do YouTube possuem legendas em todos os idiomas
2. **Legendas Auto-geradas**: O serviço aceita legendas auto-geradas se legendas manuais não estiverem disponíveis
3. **Timestamps**: Os timestamps são ajustados automaticamente para serem relativos ao início de cada clipe
4. **Nomenclatura**: Os nomes dos arquivos seguem exatamente a mesma convenção dos clipes de vídeo
5. **Segmentos Vazios**: Se não houver legendas no período do clipe, um arquivo vazio é criado

## Troubleshooting

### Nenhuma legenda disponível

```
Error: Failed to download en subtitle
```

**Solução**: Use o comando `list` do `cli_subtitle.py` para ver idiomas disponíveis.

### Momentos não encontrados

```
Error: No moments found in input data
```

**Solução**: Verifique se o vídeo tem replay heatmap disponível (geralmente precisa de 50.000+ visualizações).

### Arquivo de momentos inválido

```
Error: Invalid JSON in file
```

**Solução**: Verifique se o arquivo JSON está no formato correto retornado por `get_popular_moments()`.

## Ver Também

- **SUBTITLE_SERVICE.md** - Serviço de download de legendas
- **video_clipper_service.md** - Serviço de criação de clipes
- **replay_heatmap.py** - Extração de momentos populares
- **SUBTITLE_QUICKSTART.md** - Guia rápido de legendas