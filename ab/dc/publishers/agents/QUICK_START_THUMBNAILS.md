# Quick Start: Thumbnail Generator

Guia rápido para começar a gerar thumbnails virais com IA.

## Instalação Rápida

```bash
# 1. Instalar dependências
pip install agno openai requests

# 2. Configurar chaves API
export OPENAI_API_KEY="sk-..."
export NANOBANANA_API_KEY="nb-..."  # Opcional, apenas para gerar imagens
```

## Uso Básico

### 1. Gerar Thumbnails de uma Transcrição

```bash
cd ab/dc/publishers/agents

python cli_thumbnail.py generate \
  ../../../../processed_videos/RusBe_8arLQ/RusBe_8arLQ_0000_40s_score_095_original_en.md
```

**Resultado**: 3 thumbnails em `processed_videos/RusBe_8arLQ/thumbnails/`

### 2. Apenas Conceitos (Sem Imagens)

```bash
python cli_thumbnail.py concepts \
  ../../../../processed_videos/RusBe_8arLQ/RusBe_8arLQ_0000_40s_score_095_original_en.md \
  --num 5
```

**Resultado**: JSON com 5 conceitos de thumbnails

### 3. Processar Pasta Inteira

```bash
python cli_thumbnail.py generate \
  ../../../../processed_videos/RusBe_8arLQ/ \
  --platform youtube \
  --ratio 16:9
```

**Resultado**: Thumbnails para todos os `.md` na pasta

## Casos de Uso

### YouTube (Horizontal 16:9)

```bash
python cli_thumbnail.py generate transcript.md \
  --platform youtube \
  --ratio 16:9 \
  --num 3 \
  --output youtube_thumbnails/
```

### TikTok/Reels (Vertical 9:16)

```bash
python cli_thumbnail.py generate transcript.md \
  --platform tiktok \
  --ratio 9:16 \
  --size 1080x1920
```

### Instagram Feed (Quadrado 1:1)

```bash
python cli_thumbnail.py generate transcript.md \
  --platform instagram \
  --ratio 1:1 \
  --size 1080x1080
```

## Workflow Pipeline

### Pipeline Completo (Download → Clips → Thumbnails)

```bash
#!/bin/bash
VIDEO_ID="RusBe_8arLQ"

# 1. Extrair momentos do vídeo
cd ab/dc/analysers
python cli.py $VIDEO_ID --format json > moments.json

# 2. Criar clips dos momentos
cd ../downloaders
python cli_clipper.py < ../analysers/moments.json

# 3. Gerar thumbnails para cada clip
cd ../publishers/agents
python cli_thumbnail.py generate \
  ../../../../processed_videos/$VIDEO_ID/ \
  --platform youtube \
  --ratio 16:9 \
  --num 3

echo "Thumbnails gerados em: processed_videos/$VIDEO_ID/thumbnails/"
```

## Sem API do nanobanana?

Se você não tem chave API do nanobanana, ainda pode:

### 1. Gerar Apenas Conceitos

```bash
python cli_thumbnail.py concepts transcript.md --num 5
```

Isso retorna:
- Conceitos visuais
- Texto sugerido
- Esquema de cores
- **Prompts para geração de imagens**

### 2. Usar os Prompts em Outras Ferramentas

Copie os `image_prompt` do JSON e use em:
- DALL-E (https://labs.openai.com/)
- Midjourney
- Stable Diffusion
- Leonardo AI
- Outras ferramentas de geração de imagens

## Exemplo de Saída

### Conceito Gerado

```json
{
  "main_visual": "YouTuber chocado olhando para câmera com microfone",
  "text_overlay": "MELHOR MIC POR $40! 😱",
  "color_scheme": ["#FF0000", "#FFFF00", "#000000"],
  "composition": "Rosto à esquerda, mic gigante à direita, texto no topo",
  "emotion": "shocked",
  "image_prompt": "Professional YouTube thumbnail, photorealistic, 8K quality, YouTuber with shocked expression looking at camera, holding Deity D4 mini microphone, dramatic lighting, vibrant red and yellow color scheme, bold text overlay 'MELHOR MIC POR $40!' in all caps, high contrast black background, cinematic feel, eye-catching, viral thumbnail style"
}
```

### Thumbnail Gerado

![Exemplo](exemplo_thumbnail.png)

Arquivo salvo em: `thumbnails/transcript_thumbnail_1.png`

## Dicas para Melhores Resultados

### 1. Transcrições Claras
- Quanto mais detalhada a transcrição, melhores os conceitos
- Inclua momentos-chave e emoções

### 2. Plataforma Correta
- YouTube: Use `--platform youtube --ratio 16:9`
- TikTok/Reels: Use `--platform tiktok --ratio 9:16`
- Instagram: Use `--platform instagram --ratio 1:1`

### 3. Quantidade de Conceitos
- 3-5 conceitos é ideal para ter variedade
- Teste diferentes para ver qual performa melhor

### 4. Ajuste de Temperatura
- `--temperature 0.7`: Mais conservador, seguro
- `--temperature 0.9`: Mais criativo, arriscado
- Padrão 0.8 é balanceado

### 5. Modelos OpenAI
- `gpt-4-turbo-preview`: Melhor qualidade (recomendado)
- `gpt-3.5-turbo`: Mais rápido e barato (para testes)

## Troubleshooting Rápido

### "Agno package not installed"
```bash
pip install agno openai
```

### "OpenAI API key not found"
```bash
export OPENAI_API_KEY="sk-sua-chave-aqui"
```

### "Transcript not found"
- Verifique o caminho do arquivo .md
- Use caminho absoluto se necessário

### Resultado não é JSON válido
- GPT às vezes adiciona texto extra
- Use `--temperature 0.7` para respostas mais consistentes

## Próximos Passos

1. **Leia a documentação completa**: `THUMBNAIL_GENERATOR.md`
2. **Explore opções do CLI**: `python cli_thumbnail.py --help`
3. **Integre no seu pipeline**: Combine com downloaders e publishers
4. **Teste e ajuste**: Experimente diferentes configurações

## Suporte

- Issues: https://github.com/your-repo/issues
- Docs do Agno: https://docs.agno.com
- OpenAI: https://platform.openai.com/docs

Divirta-se gerando thumbnails virais! 🚀
