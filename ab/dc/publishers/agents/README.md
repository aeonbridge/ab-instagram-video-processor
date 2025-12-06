# AI Agents for Video Publishing

Agentes de IA baseados no framework Agno para automação de tarefas de publicação de vídeos.

## Agentes Disponíveis

### 1. Metadata Generator Agent
Gera metadados virais (título, descrição, tags, thumbnails, hooks) baseado em transcrições de vídeos.

**Arquivo**: `metadata_generator_agent.py`
**CLI**: `cli_metadata_agent.py`
**Docs**: `METADATA_AGENT.md`

**Uso Básico**:
```bash
# Gerar metadados de um arquivo
python cli_metadata_agent.py generate transcript.md --preview

# Processar pasta inteira
python cli_metadata_agent.py batch processed_videos/VIDEO_ID/ --platform youtube

# Validar metadados gerados
python cli_metadata_agent.py validate metadata.json
```

### 2. Thumbnail Generator Agent
Gera thumbnails virais usando IA, com conceitos criativos e imagens.

**Arquivo**: `thumbnail_generator_agent.py`
**CLI**: `cli_thumbnail.py`
**Docs**: `THUMBNAIL_GENERATOR.md`
**Quick Start**: `QUICK_START_THUMBNAILS.md`

**Uso Básico**:
```bash
# Gerar thumbnails
python cli_thumbnail.py generate transcript.md --platform youtube --ratio 16:9

# Apenas conceitos (sem gerar imagens)
python cli_thumbnail.py concepts transcript.md --num 5
```

## Instalação

```bash
# Instalar dependências
pip install agno openai requests

# Configurar API keys
export OPENAI_API_KEY="sk-..."
export NANOBANANA_API_KEY="nb-..."  # Opcional, apenas para thumbnails

# Ou adicionar ao .env
echo 'OPENAI_API_KEY=sk-...' >> ab/dc/publishers/.env
```

## Cost Tracking

Os agentes incluem rastreamento automático de custos de API:

**Metadados gerados incluem informações de custo:**
```json
{
  "title": "Seu título viral...",
  "description": "Descrição...",
  "_usage": {
    "input_tokens": 654,
    "output_tokens": 342,
    "total_tokens": 996,
    "cost_usd": 0.00084,
    "cost_breakdown": {
      "input_cost_usd": 0.000327,
      "output_cost_usd": 0.000513
    },
    "duration_seconds": 5.37
  }
}
```

**Batch processing mostra custo total:**
```bash
python cli_metadata_agent.py batch videos/ --model gpt-3.5-turbo

# Output:
# ======================================================================
# SUCCESSFULLY GENERATED 10 METADATA FILES
# ======================================================================
# Total Cost: $0.008400 USD
# Total Tokens: 9,960
# Average Cost per File: $0.000840 USD
# ======================================================================
```

**Custos estimados (GPT-3.5-turbo):**
- Por vídeo: $0.0008 - $0.0015 USD
- 100 vídeos: ~$0.10 USD
- 1000 vídeos: ~$1.00 USD

**Custos estimados (GPT-4-turbo):**
- Por vídeo: $0.01 - $0.03 USD
- 100 vídeos: ~$2.00 USD
- 1000 vídeos: ~$20.00 USD

## Quick Start

### Pipeline Completo

```bash
#!/bin/bash
VIDEO_ID="seu_video_id"

# 1. Extrair momentos do vídeo
cd ab/dc/analysers
python cli.py $VIDEO_ID --format json > moments.json

# 2. Criar clips
cd ../downloaders
python cli_clipper.py --input ../analysers/moments.json --aspect-ratio 9:16

# 3. Gerar legendas
python cli_subtitle_clipper.py --video-id $VIDEO_ID -l en

# 4. Limpar legendas para markdown
python cli_subtitle_cleaner.py batch processed_videos/$VIDEO_ID/

# 5. Gerar metadados com IA
cd ../publishers/agents
python cli_metadata_agent.py batch \
  ../../../../processed_videos/$VIDEO_ID/ \
  --platform youtube

# 6. Gerar thumbnails
python cli_thumbnail.py generate \
  ../../../../processed_videos/$VIDEO_ID/ \
  --platform youtube \
  --ratio 16:9

echo "Pipeline concluído!"
echo "Metadados: processed_videos/$VIDEO_ID/*_metadata.json"
echo "Thumbnails: processed_videos/$VIDEO_ID/thumbnails/"
```

## Documentação Completa

### Metadata Generator
- **Documentação**: `METADATA_AGENT.md`
- **Exemplos**: `python cli_metadata_agent.py examples`

### Thumbnail Generator
- **Documentação**: `THUMBNAIL_GENERATOR.md`
- **Quick Start**: `QUICK_START_THUMBNAILS.md`

## Plataformas Suportadas

Ambos os agentes suportam otimização para:
- YouTube (16:9, horizontal)
- TikTok (9:16, vertical)
- Instagram (1:1, quadrado ou 4:5)
- YouTube Shorts (9:16, vertical)

## Uso Programático

### Python

```python
from pathlib import Path
from ab.dc.publishers.agents import MetadataGeneratorAgent, ThumbnailGeneratorAgent

# Metadata Agent
metadata_agent = MetadataGeneratorAgent(
    api_key="sk-...",
    model="gpt-4-turbo-preview"
)

metadata = metadata_agent.generate_metadata(
    transcript_path=Path("transcript.md"),
    platform="youtube"
)

print(f"Título: {metadata['title']}")

# Thumbnail Agent
thumbnail_agent = ThumbnailGeneratorAgent(
    openai_api_key="sk-...",
    nanobanana_api_key="nb-..."
)

thumbnails = thumbnail_agent.generate_thumbnails_from_transcript(
    transcript_path=Path("transcript.md"),
    output_dir=Path("thumbnails/"),
    num_thumbnails=3
)

print(f"Gerados {len(thumbnails)} thumbnails")
```

## Estimativa de Custos

### Metadata Generator
- GPT-4 Turbo: ~$0.01-$0.03 por vídeo
- GPT-3.5 Turbo: ~$0.001-$0.005 por vídeo

### Thumbnail Generator
- Conceitos (GPT-4): ~$0.01-$0.02 por conjunto
- Imagens (nanobanana): ~$0.05-$0.10 por imagem

## Referências

- [Agno Framework](https://docs.agno.com/)
- [OpenAI API](https://platform.openai.com/docs)
- [nanobanana API](https://nanobanana.com/docs)
