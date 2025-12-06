# Quick Start: Metadata Generator

Guia rápido para começar a gerar metadados virais com IA.

## Instalação Rápida

```bash
# 1. Instalar dependências
pip install agno openai

# 2. Configurar chave API
export OPENAI_API_KEY="sk-..."
```

## Uso Básico

### 1. Gerar Metadados de uma Transcrição

```bash
cd ab/dc/publishers/agents

python cli_metadata_agent.py generate \
  ../../../../processed_videos/VIDEO_ID/VIDEO_ID_0000_40s_score_095_original_en.md \
  --preview
```

**Resultado**: JSON com título, descrição, tags, ideias de thumbnails, hooks, etc.

### 2. Apenas Gerar (Sem Preview)

```bash
python cli_metadata_agent.py generate transcript.md
```

**Resultado**: `transcript_metadata.json` no mesmo diretório

### 3. Processar Pasta Inteira

```bash
python cli_metadata_agent.py batch \
  ../../../../processed_videos/VIDEO_ID/ \
  --platform youtube
```

**Resultado**: `*_metadata.json` para cada arquivo `.md`

## Casos de Uso

### YouTube (Horizontal)

```bash
python cli_metadata_agent.py generate transcript.md \
  --platform youtube \
  --preview
```

Otimizado para:
- Títulos SEO-friendly
- Descrições longas com timestamps
- Tags abrangentes
- Thumbnails 16:9

### TikTok (Vertical)

```bash
python cli_metadata_agent.py generate transcript.md \
  --platform tiktok \
  --temperature 0.9
```

Otimizado para:
- Títulos curtos e impactantes
- Hashtags trending
- Alto engajamento
- Thumbnails 9:16

### Instagram Reels

```bash
python cli_metadata_agent.py generate transcript.md \
  --platform instagram \
  --temperature 0.8
```

Otimizado para:
- Captions storytelling
- Hashtags estratégicos
- Visual appeal
- Thumbnails 1:1 ou 4:5

### YouTube Shorts

```bash
python cli_metadata_agent.py generate transcript.md \
  --platform shorts \
  --temperature 0.9
```

Otimizado para:
- Títulos ultra-curtos
- Formato vertical
- Trending topics
- Thumbnails 9:16

## Exemplo de Saída

### Comando

```bash
python cli_metadata_agent.py generate transcript.md --preview
```

### Resultado

```
======================================================================
METADATA PREVIEW
======================================================================
Title: Pro Video Setup on a Budget: Sony ZVE10 & Sigma 16mm!
Category: Howto & Style
Tags: Sony ZVE10, Sigma 16mm, budget filmmaking, video setup tips, content creation

Description:
Unlock the secrets to a professional video setup without spending a fortune! 🎥 Dive into our budget-friendly guide featuring the Sony ZVE10 and the Sigma 16mm lens...
======================================================================
```

### Arquivo JSON Gerado

```json
{
  "title": "Pro Video Setup on a Budget: Sony ZVE10 & Sigma 16mm!",
  "description": "Unlock the secrets to a professional video setup...",
  "tags": [
    "Sony ZVE10",
    "Sigma 16mm",
    "budget filmmaking",
    "video setup tips",
    "content creation"
  ],
  "category": "Howto & Style",
  "thumbnail_ideas": [
    {
      "concept": "Sony ZVE10 with price tag overlay",
      "text_overlay": "Pro Setup, Tiny Budget!",
      "color_scheme": "Blue and white"
    }
  ],
  "target_audience": "Aspiring YouTubers, budget filmmakers",
  "video_hook": "Audio makes up 50% of your video! Let's fix yours on a budget!",
  "call_to_action": "Subscribe for more budget filmmaking secrets!"
}
```

## Workflow Pipeline

### Pipeline Completo (Download → Clips → Metadados)

```bash
#!/bin/bash
VIDEO_ID="RusBe_8arLQ"

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
  --platform youtube \
  --preview

echo "Metadados gerados em: processed_videos/$VIDEO_ID/"
```

## Validar Metadados

```bash
python cli_metadata_agent.py validate metadata.json
```

**Resultado**:
```
======================================================================
✓ METADATA IS VALID
======================================================================
Title: Pro Video Setup on a Budget: Sony ZVE10 & Sigma 16mm!
Category: Howto & Style
Tags: 5 tags
Thumbnail Ideas: 3
======================================================================
```

## Opções Avançadas

### Escolher Modelo

```bash
# GPT-4 Turbo (padrão, melhor qualidade)
python cli_metadata_agent.py generate transcript.md \
  --model gpt-4-turbo-preview

# GPT-3.5 Turbo (mais rápido e barato)
python cli_metadata_agent.py generate transcript.md \
  --model gpt-3.5-turbo
```

### Ajustar Criatividade (Temperature)

```bash
# Mais conservador (0.5)
python cli_metadata_agent.py generate transcript.md \
  --temperature 0.5

# Balanceado (0.7, padrão)
python cli_metadata_agent.py generate transcript.md \
  --temperature 0.7

# Mais criativo (0.9)
python cli_metadata_agent.py generate transcript.md \
  --temperature 0.9
```

### Forçar Sobrescrever

```bash
# Sobrescrever arquivo existente
python cli_metadata_agent.py generate transcript.md --force

# Sobrescrever batch
python cli_metadata_agent.py batch processed_videos/VIDEO_ID/ --force
```

### Output Customizado

```bash
# Especificar arquivo de saída
python cli_metadata_agent.py generate transcript.md \
  -o custom_metadata.json
```

## Integração com Publicação

### Usar Metadados para Upload

```bash
VIDEO="processed_videos/VIDEO_ID/clip.mp4"
METADATA="processed_videos/VIDEO_ID/clip_metadata.json"

# Extrair campos do JSON com jq
python ab/dc/publishers/cli_publisher.py upload "$VIDEO" \
  --title "$(jq -r .title $METADATA)" \
  --description "$(jq -r .description $METADATA)" \
  --tags "$(jq -r '.tags | join(",")' $METADATA)" \
  --category "$(jq -r .category $METADATA)"
```

### Loop para Múltiplos Vídeos

```bash
cd ab/dc/publishers

for metadata in ../../processed_videos/VIDEO_ID/*_metadata.json; do
    video="${metadata%_metadata.json}.mp4"

    python cli_publisher.py upload "$video" \
        --title "$(jq -r .title $metadata)" \
        --description "$(jq -r .description $metadata)" \
        --tags "$(jq -r '.tags | join(",")' $metadata)" \
        --category "$(jq -r .category $metadata)"
done
```

## Dicas para Melhores Resultados

### 1. Transcrições Claras
- Quanto mais detalhada a transcrição, melhores os metadados
- Inclua contexto e momentos-chave
- Evite transcrições muito curtas (< 50 palavras)

### 2. Plataforma Correta
- YouTube: `--platform youtube` (SEO, descrições longas)
- TikTok: `--platform tiktok` (viral, hashtags)
- Instagram: `--platform instagram` (visual, storytelling)
- Shorts: `--platform shorts` (curto, trending)

### 3. Modelo GPT
- GPT-4 Turbo: Melhor para conteúdo de alto valor
- GPT-3.5 Turbo: Bom para testes e volume alto

### 4. Temperature
- 0.5-0.6: Mais seguro, consistente
- 0.7-0.8: Balanceado (recomendado)
- 0.9-1.0: Mais criativo, arriscado

### 5. Batch Processing
- Use batch para processar múltiplos vídeos de uma vez
- Adicione `--force` para reprocessar todos
- Verifique os resultados antes de publicar

## Troubleshooting Rápido

### "Agno package not installed"
```bash
pip install agno openai
```

### "OpenAI API key not found"
```bash
export OPENAI_API_KEY="sk-sua-chave-aqui"
# ou
echo 'OPENAI_API_KEY=sk-...' >> ab/dc/publishers/.env
```

### "Transcript not found"
- Verifique o caminho do arquivo .md
- Use caminho absoluto se necessário
- Certifique-se que o arquivo foi gerado pelo `cli_subtitle_cleaner.py`

### "Invalid JSON response"
- GPT às vezes adiciona texto extra
- Use `--temperature 0.7` ou menor
- Use `--model gpt-4-turbo-preview`
- Adicione `--debug` para ver resposta completa

### Metadados de baixa qualidade
- Use GPT-4 ao invés de GPT-3.5
- Ajuste temperature para 0.7-0.9
- Melhore a qualidade da transcrição
- Forneça transcrições mais completas (> 100 palavras)

## Estimativa de Custos

### GPT-4 Turbo Preview
- Por vídeo: ~$0.01 - $0.03
- Batch de 10 vídeos: ~$0.10 - $0.30
- Batch de 100 vídeos: ~$1.00 - $3.00

### GPT-3.5 Turbo
- Por vídeo: ~$0.001 - $0.005
- Batch de 10 vídeos: ~$0.01 - $0.05
- Batch de 100 vídeos: ~$0.10 - $0.50

**Recomendação**: Use GPT-4 Turbo para conteúdo premium, GPT-3.5 Turbo para volume alto.

## Próximos Passos

1. **Leia a documentação completa**: `METADATA_AGENT.md`
2. **Explore opções do CLI**: `python cli_metadata_agent.py --help`
3. **Veja exemplos**: `python cli_metadata_agent.py examples`
4. **Integre no seu pipeline**: Combine com downloaders e publishers
5. **Teste e ajuste**: Experimente diferentes configurações

## Ver Mais Exemplos

```bash
python cli_metadata_agent.py examples
```

## Suporte

- GitHub Issues: https://github.com/your-repo/issues
- Docs do Agno: https://docs.agno.com
- OpenAI: https://platform.openai.com/docs

Divirta-se gerando metadados virais!
