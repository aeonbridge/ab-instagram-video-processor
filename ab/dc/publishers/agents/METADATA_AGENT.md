# Metadata Generator Agent

Agente Agno que gera metadados virais (título, descrição, tags, thumbnails, etc.) para vídeos baseado nas transcrições de legendas.

## Visão Geral

O Metadata Generator Agent usa o framework Agno com a API OpenAI para analisar transcrições de vídeos e gerar metadados otimizados para diferentes plataformas (YouTube, TikTok, Instagram, Shorts).

## Características

- Geração de títulos otimizados para SEO e engajamento
- Descrições completas com hashtags e call-to-action
- Tags estratégicas para descoberta
- Ideias de thumbnails com conceitos visuais
- Hooks para os primeiros 5 segundos
- Análise de público-alvo
- Suporte a múltiplas plataformas
- Processamento em batch

## Instalação

```bash
# Instalar dependências
pip install agno openai

# Configurar API key
export OPENAI_API_KEY="sk-..."
# ou adicionar no .env:
echo 'OPENAI_API_KEY=sk-...' >> ab/dc/publishers/.env
```

## Uso Básico

### 1. Gerar Metadados de um Arquivo

```bash
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  processed_videos/VIDEO_ID/VIDEO_ID_0000_40s_score_095_original_en.md
```

**Saída**: `VIDEO_ID_0000_40s_score_095_original_en_metadata.json`

### 2. Gerar com Preview

```bash
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  transcript.md \
  --preview
```

Mostra preview dos metadados gerados no terminal.

### 3. Especificar Plataforma

```bash
# YouTube (padrão)
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  transcript.md \
  --platform youtube

# TikTok
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  transcript.md \
  --platform tiktok

# Instagram
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  transcript.md \
  --platform instagram

# YouTube Shorts
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  transcript.md \
  --platform shorts
```

### 4. Processamento em Batch

```bash
# Processar todos os .md de uma pasta
python ab/dc/publishers/agents/cli_metadata_agent.py batch \
  processed_videos/VIDEO_ID/

# Com padrão customizado
python ab/dc/publishers/agents/cli_metadata_agent.py batch \
  processed_videos/VIDEO_ID/ \
  --pattern "*_en.md"

# Com diretório de saída customizado
python ab/dc/publishers/agents/cli_metadata_agent.py batch \
  processed_videos/VIDEO_ID/ \
  --output-dir metadata_output/

# Forçar sobrescrever arquivos existentes
python ab/dc/publishers/agents/cli_metadata_agent.py batch \
  processed_videos/VIDEO_ID/ \
  --force
```

### 5. Validar Metadados

```bash
python ab/dc/publishers/agents/cli_metadata_agent.py validate \
  metadata.json
```

## Formato de Entrada

O agente aceita arquivos Markdown gerados pelo `cli_subtitle_cleaner.py`:

### Formato Completo
```markdown
# Video Transcript for Metadata Generation

## Video Information
- **Video ID**: RusBe
- **Duration**: 0m 40s

## Video Transcript
[transcrição do vídeo aqui]
```

### Formato Text Only
```markdown
# Video Transcript

[transcrição do vídeo aqui]
```

## Formato de Saída

O agente gera um arquivo JSON com a seguinte estrutura:

```json
{
  "title": "Título otimizado (max 100 caracteres)",
  "description": "Descrição completa com hashtags e CTA",
  "tags": [
    "tag1",
    "tag2",
    "tag3",
    "tag4",
    "tag5"
  ],
  "category": "Howto & Style",
  "thumbnail_ideas": [
    {
      "concept": "Descrição visual do conceito",
      "text_overlay": "Texto sugerido para thumbnail",
      "color_scheme": "Esquema de cores"
    },
    {
      "concept": "Conceito alternativo",
      "text_overlay": "Texto alternativo",
      "color_scheme": "Cores alternativas"
    },
    {
      "concept": "Terceiro conceito",
      "text_overlay": "Terceiro texto",
      "color_scheme": "Terceiro esquema"
    }
  ],
  "target_audience": "Descrição do público-alvo",
  "video_hook": "Hook para os primeiros 5 segundos",
  "call_to_action": "CTA específico",
  "_generated_at": "2025-12-05T21:30:59.471435",
  "_model": "gpt-4-turbo-preview",
  "_source_file": "caminho/para/transcript.md",
  "_platform": "youtube"
}
```

## Opções Avançadas

### Modelos OpenAI

```bash
# GPT-4 Turbo (padrão, melhor qualidade)
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  transcript.md \
  --model gpt-4-turbo-preview

# GPT-4 (alta qualidade)
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  transcript.md \
  --model gpt-4

# GPT-3.5 Turbo (rápido e econômico)
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  transcript.md \
  --model gpt-3.5-turbo
```

### Temperature (Criatividade)

```bash
# Mais conservador (0.0 - 0.5)
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  transcript.md \
  --temperature 0.5

# Balanceado (0.6 - 0.8, padrão 0.7)
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  transcript.md \
  --temperature 0.7

# Mais criativo (0.9 - 1.0)
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  transcript.md \
  --temperature 0.9
```

### API Key

```bash
# Passar API key diretamente
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  transcript.md \
  --api-key sk-...
```

### Debug

```bash
# Ativar modo debug
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  transcript.md \
  --debug
```

## Pipeline Completo

### Workflow: Vídeo → Clips → Legendas → Metadados

```bash
#!/bin/bash
VIDEO_ID="RusBe_8arLQ"

# 1. Extrair momentos do vídeo
cd ab/dc/analysers
python cli.py $VIDEO_ID --format json > moments.json

# 2. Criar clips
cd ../downloaders
python cli_clipper.py --input ../analysers/moments.json --aspect-ratio 9:16

# 3. Gerar arquivos de legendas
python cli_subtitle_clipper.py --video-id $VIDEO_ID -l en

# 4. Limpar legendas para markdown
python cli_subtitle_cleaner.py batch processed_videos/$VIDEO_ID/

# 5. Gerar metadados com IA
cd ../publishers/agents
python cli_metadata_agent.py batch \
  ../../../../processed_videos/$VIDEO_ID/ \
  --platform youtube \
  --preview

echo "Metadados gerados em: processed_videos/$VIDEO_ID/"
```

## Otimização por Plataforma

### YouTube
- Títulos SEO-friendly
- Descrições longas com timestamps
- Tags abrangentes
- Thumbnails 16:9

```bash
python cli_metadata_agent.py generate transcript.md \
  --platform youtube \
  --temperature 0.7
```

### TikTok
- Títulos curtos e impactantes
- Hashtags trending
- Foco em viralidade
- Thumbnails 9:16

```bash
python cli_metadata_agent.py generate transcript.md \
  --platform tiktok \
  --temperature 0.9
```

### Instagram
- Captions storytelling
- Hashtags estratégicos
- Visual appeal
- Thumbnails 1:1 ou 4:5

```bash
python cli_metadata_agent.py generate transcript.md \
  --platform instagram \
  --temperature 0.8
```

### YouTube Shorts
- Títulos ultra-curtos
- Vertical format
- Trending topics
- Thumbnails 9:16

```bash
python cli_metadata_agent.py generate transcript.md \
  --platform shorts \
  --temperature 0.9
```

## Uso Programático

### Python

```python
from pathlib import Path
from ab.dc.publishers.agents import MetadataGeneratorAgent

# Inicializar agente
agent = MetadataGeneratorAgent(
    api_key="sk-...",  # ou None para usar OPENAI_API_KEY
    model="gpt-4-turbo-preview",
    temperature=0.7
)

# Gerar metadados
metadata = agent.generate_metadata(
    transcript_path=Path("transcript.md"),
    platform="youtube"
)

print(f"Título: {metadata['title']}")
print(f"Tags: {', '.join(metadata['tags'])}")

# Validar
is_valid, errors = agent.validate_metadata(metadata)
if not is_valid:
    print("Erros:", errors)

# Batch
created_files = agent.generate_batch(
    transcript_dir=Path("processed_videos/VIDEO_ID/"),
    platform="youtube",
    overwrite=False
)
print(f"Criados {len(created_files)} arquivos")
```

## Estimativa de Custos

### GPT-4 Turbo Preview
- Por geração: ~$0.01 - $0.03
- Batch de 10 vídeos: ~$0.10 - $0.30

### GPT-3.5 Turbo
- Por geração: ~$0.001 - $0.005
- Batch de 10 vídeos: ~$0.01 - $0.05

**Recomendação**: Use GPT-4 Turbo para conteúdo de alto valor, GPT-3.5 Turbo para processamento em larga escala.

## Troubleshooting

### "Agno package not installed"

```bash
pip install agno openai
```

### "OpenAI API key not found"

```bash
export OPENAI_API_KEY="sk-..."
# ou
echo 'OPENAI_API_KEY=sk-...' >> ab/dc/publishers/.env
```

### "Invalid JSON response from agent"

O GPT às vezes adiciona texto extra. Soluções:
- Usar `--temperature 0.7` ou menor
- Usar modelo mais recente (`gpt-4-turbo-preview`)
- Adicionar `--debug` para ver resposta completa

### "Transcript file not found"

Verifique:
- Caminho absoluto ou relativo correto
- Arquivo foi gerado pelo `cli_subtitle_cleaner.py`
- Extensão `.md`

### Metadados de baixa qualidade

Ajustes:
- Usar GPT-4 ao invés de GPT-3.5
- Ajustar temperature (0.7-0.9)
- Melhorar qualidade da transcrição
- Fornecer transcrições mais completas

## Exemplos

### Ver Exemplos Completos

```bash
python ab/dc/publishers/agents/cli_metadata_agent.py examples
```

## Integração com Publisher

Usar metadados gerados para upload:

```bash
# Gerar metadados
python ab/dc/publishers/agents/cli_metadata_agent.py generate \
  processed_videos/VIDEO_ID/clip.md

# Extrair campos do JSON e usar no upload
VIDEO="processed_videos/VIDEO_ID/clip.mp4"
METADATA="processed_videos/VIDEO_ID/clip_metadata.json"

python ab/dc/publishers/cli_publisher.py upload "$VIDEO" \
  --title "$(jq -r .title $METADATA)" \
  --description "$(jq -r .description $METADATA)" \
  --tags "$(jq -r '.tags | join(",")' $METADATA)" \
  --category "$(jq -r .category $METADATA)"
```

## Referências

- [Agno Framework](https://docs.agno.com/)
- [OpenAI API](https://platform.openai.com/docs)
- [YouTube Best Practices](https://www.youtube.com/creators/)
- [TikTok Creator Portal](https://www.tiktok.com/creators/)

## Suporte

- GitHub Issues: https://github.com/your-repo/issues
- Documentação Agno: https://docs.agno.com
- OpenAI Support: https://platform.openai.com/support
