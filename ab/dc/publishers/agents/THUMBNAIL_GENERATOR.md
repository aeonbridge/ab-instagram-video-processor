# Thumbnail Generator Agent

Agente Agno para gerar thumbnails virais de vídeos usando IA, baseado em transcrições.

## Visão Geral

O Thumbnail Generator Agent usa:
- **Agno Framework** - Orquestração de agentes IA
- **OpenAI GPT-4** - Geração de conceitos criativos
- **nanobanana API** - Geração de imagens via IA

## Características

- Gera múltiplos conceitos de thumbnail por vídeo
- Analisa transcrições para extrair elementos virais
- Cria prompts detalhados para geração de imagens
- Suporta múltiplas plataformas (YouTube, TikTok, Instagram)
- Aspect ratios configuráveis (16:9, 9:16, 1:1, 4:5)
- Modo concepts-only (sem gerar imagens)
- Processamento em lote de múltiplos vídeos

## Instalação

### Dependências

```bash
pip install agno openai requests
```

### Variáveis de Ambiente

```bash
# Obrigatório
export OPENAI_API_KEY="sk-..."

# Obrigatório para geração de imagens
export NANOBANANA_API_KEY="nb-..."
```

## Uso

### CLI Básico

```bash
# Gerar 3 thumbnails de uma transcrição
python cli_thumbnail.py generate transcript.md

# Gerar 5 thumbnails para TikTok (vertical)
python cli_thumbnail.py generate transcript.md --num 5 --platform tiktok --ratio 9:16

# Processar todos os .md em uma pasta
python cli_thumbnail.py generate processed_videos/RusBe_8arLQ/

# Apenas conceitos (sem imagens)
python cli_thumbnail.py concepts transcript.md --num 5
```

### Exemplos Avançados

#### Gerar para YouTube (horizontal)
```bash
python cli_thumbnail.py generate \
  processed_videos/RusBe_8arLQ/RusBe_8arLQ_0000_40s_score_095_original_en.md \
  --platform youtube \
  --ratio 16:9 \
  --num 3 \
  --output thumbnails/youtube/
```

#### Gerar para Instagram Reels (vertical)
```bash
python cli_thumbnail.py generate \
  transcript.md \
  --platform instagram \
  --ratio 9:16 \
  --size 1080x1920
```

#### Gerar apenas conceitos (sem imagens) e salvar JSON
```bash
python cli_thumbnail.py concepts \
  transcript.md \
  --num 5 \
  --json-output concepts.json
```

#### Usar GPT-3.5 (mais rápido e barato)
```bash
python cli_thumbnail.py generate \
  transcript.md \
  --model gpt-3.5-turbo \
  --temperature 0.9
```

### Uso Programático

```python
from pathlib import Path
from thumbnail_generator_agent import ThumbnailGeneratorAgent

# Inicializar agente
agent = ThumbnailGeneratorAgent(
    model="gpt-4-turbo-preview",
    temperature=0.8
)

# Gerar thumbnails
result = agent.generate_thumbnails_from_transcript(
    transcript_path=Path("transcript.md"),
    output_dir=Path("thumbnails"),
    num_thumbnails=3,
    platform="youtube",
    aspect_ratio="16:9",
    generate_images=True
)

# Resultados
print(f"Gerados: {result['images_generated']} thumbnails")
for thumb in result['thumbnails']:
    if thumb['success']:
        print(f"  - {thumb['image_path']}")
```

## Estrutura de Saída

### Conceitos Gerados

Cada conceito de thumbnail contém:

```json
{
  "main_visual": "Close-up do rosto chocado com olhos arregalados",
  "text_overlay": "VOCÊ NÃO VAI ACREDITAR! 😱",
  "color_scheme": ["#FF0000", "#FFFF00", "#000000"],
  "composition": "Rosto no lado esquerdo, texto grande no lado direito",
  "emotion": "shocked",
  "image_prompt": "Professional YouTube thumbnail, ultra realistic, 8K quality..."
}
```

### Resultado Completo

```json
{
  "success": true,
  "transcript_path": "transcript.md",
  "concepts_generated": 3,
  "images_generated": 3,
  "thumbnails": [
    {
      "success": true,
      "image_path": "thumbnails/transcript_thumbnail_1.png",
      "concept": { ... },
      "size": "1920x1080",
      "file_size_mb": 2.3
    }
  ],
  "output_dir": "thumbnails"
}
```

## Formatos de Transcrição Suportados

O agente extrai automaticamente o texto da transcrição de arquivos markdown com:

### Formato Completo
```markdown
# Video Transcript for Metadata Generation

## Video Information
- **Video ID**: RusBe
- **Duration**: 0m 40s

## Video Transcript

your transcript text here...
```

### Formato Simplificado
```markdown
# Video Transcript

your transcript text here...
```

## Otimizações por Plataforma

### YouTube (16:9)
- Texto grande e legível
- Faces com expressões exageradas
- Cores de alto contraste
- Setas e círculos vermelhos
- Elementos de click-bait

### TikTok/Reels (9:16)
- Texto vertical centrado
- Emoji estratégicos
- Estilo trendy/moderno
- Menos texto, mais visual
- Foco na emoção

### Instagram Feed (1:1)
- Composição equilibrada
- Estética limpa
- Paleta de cores coesa
- Texto mínimo
- Visual aspiracional

## Prompts de Geração de Imagem

O agente gera prompts detalhados para nanobanana/DALL-E:

```
Professional YouTube thumbnail, photorealistic, 8K quality, dramatic lighting,
[main visual description],
vibrant [color scheme],
bold text overlay "[text]",
[composition details],
emotion: [emotion],
cinematic feel, high contrast, eye-catching
```

## Melhores Práticas

### Texto em Thumbnails

- **Use CAPS** para impacto
- **Máximo 7 palavras** - seja conciso
- **Números** funcionam (3 SECRETS, $1000/DAY)
- **Emoji** estratégicos (🔥💰✅❌)
- **Contraste** emocional (ANTES vs DEPOIS)

### Elementos Visuais

- **Faces humanas** aumentam CTR em 30%
- **Expressões exageradas** (chocado, excitado)
- **Alto contraste** (texto claro em fundo escuro)
- **Cores primárias** (vermelho, amarelo, azul)
- **Setas/círculos** apontando elementos-chave

### Composição

- **Regra dos terços** para equilíbrio
- **Foco central** no elemento principal
- **Espaço negativo** para texto
- **Split screen** para comparações
- **Close-ups** de rostos

## Configuração API

### OpenAI

1. Obtenha chave em: https://platform.openai.com/api-keys
2. Configure: `export OPENAI_API_KEY="sk-..."`
3. Modelos recomendados:
   - `gpt-4-turbo-preview` - Melhor qualidade
   - `gpt-3.5-turbo` - Mais rápido/barato

### nanobanana

1. Cadastre-se em: https://nanobanana.com
2. Gere API key no dashboard
3. Configure: `export NANOBANANA_API_KEY="nb-..."`
4. Preços típicos: $0.02-0.10 por imagem

## Troubleshooting

### Erro: "Agno package not installed"
```bash
pip install agno openai
```

### Erro: "OpenAI API key not found"
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### Erro: "nanobanana API key not configured"
```bash
# Para apenas gerar conceitos (sem imagens):
python cli_thumbnail.py concepts transcript.md

# Ou configure a chave:
export NANOBANANA_API_KEY="nb-your-key-here"
```

### Resposta inválida do GPT
- Aumente `--temperature` para mais criatividade
- Ou diminua para respostas mais conservadoras
- Verifique se a transcrição está bem formatada

### Imagens de baixa qualidade
- Use `--size 1920x1080` ou maior
- Revise os prompts gerados (concepts-only)
- Ajuste descrições no conceito

## Performance

### Tempo de Geração

- **Conceitos**: ~5-15 segundos (GPT-4)
- **Imagens**: ~10-30 segundos cada (nanobanana)
- **Total (3 thumbnails)**: ~2-3 minutos

### Custos Estimados

- **GPT-4**: ~$0.01-0.05 por conceito
- **GPT-3.5**: ~$0.001-0.005 por conceito
- **nanobanana**: ~$0.02-0.10 por imagem

### Otimizações

- Use `gpt-3.5-turbo` para testes rápidos
- Gere conceitos primeiro, revise, depois gere imagens
- Processe em lote múltiplas transcrições

## Integração com Pipeline

### Workflow Completo

```bash
# 1. Extrair momentos populares
python cli.py VIDEO_ID --format json > moments.json

# 2. Criar clips
python cli_clipper.py < moments.json

# 3. Gerar thumbnails para os clips
python cli_thumbnail.py generate processed_videos/VIDEO_ID/ \
  --platform youtube \
  --num 3

# 4. Upload com thumbnail
python cli_publisher.py upload \
  video.mp4 \
  --title "Title" \
  --thumbnail thumbnails/video_thumbnail_1.png
```

### Script Automatizado

```bash
#!/bin/bash
VIDEO_ID=$1

# Processar vídeo completo
python cli.py $VIDEO_ID --format json | python cli_clipper.py

# Gerar thumbnails para todos os clips
python cli_thumbnail.py generate processed_videos/$VIDEO_ID/ \
  --platform youtube \
  --ratio 16:9 \
  --num 3

echo "Pipeline concluído! Thumbnails em processed_videos/$VIDEO_ID/thumbnails/"
```

## Referências

- [Agno Documentation](https://docs.agno.com/reference/agents/agent)
- [OpenAI API](https://platform.openai.com/docs)
- [nanobanana](https://nanobanana.com/docs)
- [YouTube Thumbnail Best Practices](https://creatoracademy.youtube.com/page/lesson/thumbnails)
- [TikTok Creative Best Practices](https://www.tiktok.com/business/en/blog/tiktok-creative-best-practices)

## Licença

Este agente faz parte do ab-video-processor e segue a mesma licença do projeto.
