# Video Processing Pipeline - Complete Automation

Orquestrador completo que automatiza todo o processo desde uma URL do YouTube até clips publicados.

## Visão Geral

O Pipeline processa automaticamente vídeos do YouTube através de 7 etapas:

1. **Extração de Momentos Populares** - Usa heatmap do YouTube (algoritmo de Goodman)
2. **Download do Vídeo** - Download em alta qualidade
3. **Download de Legendas** - Legendas em inglês (auto-geradas ou manuais)
4. **Criação de Clips** - Extrai clips de cada momento popular
5. **Geração de Metadata AI** - Cria títulos, descrições e tags usando GPT-4
6. **Geração de Thumbnails AI** - Cria thumbnails virais usando DALL-E 3
7. **Publicação (Opcional)** - Publica clips no YouTube

## Estrutura de Saída

```
output/
└── youtube/
    └── VIDEO_ID/
        ├── video_metadata.json        # Informações completas do vídeo
        ├── moments.json                # Momentos populares detectados
        ├── VIDEO_ID.mp4               # Vídeo completo baixado
        ├── VIDEO_ID_full_subtitle.vtt # Legenda completa
        │
        ├── VIDEO_ID_0000/             # Primeiro momento popular
        │   ├── VIDEO_ID_0000_40s_score_095_original.mp4
        │   ├── VIDEO_ID_0000_40s_score_095_original_en.vtt
        │   ├── VIDEO_ID_0000_40s_score_095_original_en_metadata.json
        │   └── thumbnails/
        │       └── dalle/
        │           ├── VIDEO_ID_0000_..._thumbnail_1.png
        │           ├── VIDEO_ID_0000_..._thumbnail_2.png
        │           └── VIDEO_ID_0000_..._thumbnail_3.png
        │
        ├── VIDEO_ID_0001/             # Segundo momento popular
        │   └── ...
        └── ...
```

## Instalação

### Dependências

```bash
# Python packages
pip install python-dotenv requests agno openai

# System tools
brew install ffmpeg        # macOS
apt install ffmpeg         # Linux
pip install yt-dlp         # YouTube downloader
```

### Configuração

Configure as credenciais no arquivo `.env`:

```bash
# YouTube API (para publicação)
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_REDIRECT_URI=http://localhost:8088/callback

# OpenAI (para metadata e thumbnails)
OPENAI_API_KEY=sk-...

# Codec de vídeo (para clips)
VIDEO_CODEC=libx264
AUDIO_CODEC=aac
```

## Uso

### Comando Básico

```bash
# Processar vídeo e gerar clips (sem publicar)
python ab/dc/cli_pipeline.py https://www.youtube.com/watch?v=VIDEO_ID
```

### Processar e Publicar

```bash
# Publicar como privado
python ab/dc/cli_pipeline.py VIDEO_ID --publish --privacy private

# Publicar como público (dry-run primeiro)
python ab/dc/cli_pipeline.py VIDEO_ID --publish --privacy public --dry-run

# Depois publicar de verdade
python ab/dc/cli_pipeline.py VIDEO_ID --publish --privacy public
```

### Opções Avançadas

```bash
# Diretório de saída customizado
python ab/dc/cli_pipeline.py VIDEO_ID --output my_videos/

# Duração de clips personalizada
python ab/dc/cli_pipeline.py VIDEO_ID --max-duration 60 --min-duration 20

# Modo verbose (debug)
python ab/dc/cli_pipeline.py VIDEO_ID --verbose
```

## Exemplos Práticos

### Exemplo 1: Processar Vídeo Sem Publicar

```bash
python ab/dc/cli_pipeline.py RusBe_8arLQ
```

**Saída:**
```
======================================================================
VIDEO PROCESSING PIPELINE
======================================================================
Video: RusBe_8arLQ
Output: output
Clip Duration: 10s - 40s
Publishing: DISABLED
======================================================================

2025-12-06 - INFO: Step 1: Extracting popular moments...
2025-12-06 - INFO: Found 6 popular moments
2025-12-06 - INFO: Step 2: Downloading video...
2025-12-06 - INFO: Downloaded video to: output/youtube/RusBe_8arLQ/RusBe_8arLQ.mp4
2025-12-06 - INFO: Step 3: Downloading subtitles...
2025-12-06 - INFO: Step 4: Creating clips...
2025-12-06 - INFO: Created clip 1/6: RusBe_8arLQ_0000_40s_score_095_original.mp4
...
2025-12-06 - INFO: Step 5: Generating AI metadata...
2025-12-06 - INFO: Generated metadata for 6/6 clips
2025-12-06 - INFO: Step 6: Generating AI thumbnails...
2025-12-06 - INFO: Generated thumbnails for 6/6 clips

======================================================================
PIPELINE COMPLETED SUCCESSFULLY
======================================================================

Video ID: RusBe_8arLQ
Output Directory: output/youtube/RusBe_8arLQ

Popular Moments Found: 6
Clips Created: 6
Metadata Generated: 6
Thumbnails Generated: 6

======================================================================

Next Steps:
  1. Review clips in: output/youtube/RusBe_8arLQ
  2. Publish clips:
     python ab/dc/cli_pipeline.py RusBe_8arLQ --publish --privacy private
```

### Exemplo 2: Publicar Como Privado

```bash
python ab/dc/cli_pipeline.py RusBe_8arLQ --publish --privacy private
```

**Resultado:**
- Clips publicados no YouTube
- Status: Privado
- URLs dos vídeos retornadas

### Exemplo 3: Teste de Publicação (Dry Run)

```bash
python ab/dc/cli_pipeline.py RusBe_8arLQ --publish --privacy public --dry-run
```

**Resultado:**
- Simula publicação sem fazer upload real
- Valida autenticação e metadados
- Mostra o que seria publicado

## Componentes Utilizados

O orquestrador integra os seguintes serviços já implementados:

### 1. Replay Heatmap (`ab/dc/analysers/replay_heatmap.py`)
- Função: `get_moments_with_metadata()`
- Detecta momentos populares usando dados do YouTube
- Retorna metadados completos do vídeo

### 2. Metadata Generator Agent (`ab/dc/publishers/agents/metadata_generator_agent.py`)
- Função: `generate_metadata_from_transcript()`
- Usa GPT-4 para gerar título, descrição, tags
- Otimizado para YouTube

### 3. Thumbnail Generator Agent (`ab/dc/publishers/agents/thumbnail_generator_agent.py`)
- Função: `generate_thumbnails_from_metadata()`
- Usa DALL-E 3 para criar thumbnails virais
- Gera 3 variações por clip

### 4. Auto Publisher (`ab/dc/publishers/auto_publisher.py`)
- Função: `publish_video()`
- Upload para YouTube via OAuth
- Transcodifica automaticamente se necessário
- Upload de thumbnails

## Detecção de Momentos Populares

O pipeline usa o algoritmo de Goodman para detectar momentos populares:

### Como Funciona

1. **Heatmap do YouTube**: Dados de replay dos usuários
2. **Suavização**: Algoritmo de Goodman (média ponderada)
3. **Detecção de Picos**: Encontra máximos locais acima do threshold
4. **Agrupamento**: Une picos próximos
5. **Extração**: Cria clips dos momentos detectados

### Requisitos

- Vídeo precisa ter 50,000+ views para ter heatmap
- Duração mínima: 10 segundos
- Duração máxima: 40 segundos (configurável)

### Exemplo de Momento Detectado

```json
{
  "start_time": 45.5,
  "end_time": 85.2,
  "duration": 39.7,
  "score": 0.856,
  "timestamp": "0:45"
}
```

## Geração de Metadata AI

Cada clip recebe metadata otimizada para YouTube:

### Campos Gerados

```json
{
  "title": "Transform Your Videos: Manfrotto Tripod & Amaran 60D Review!",
  "description": "Discover the ultimate secrets to cinematic quality...",
  "tags": ["Manfrotto", "Amaran 60D", "Video Gear", "Videography Tips"],
  "category": "Tech & Gear",
  "thumbnail_ideas": [
    {
      "concept": "Manfrotto tripod and Amaran light...",
      "text_overlay": "Upgrade Your Video Quality!",
      "color_scheme": "Warm tones"
    }
  ],
  "target_audience": "Aspiring videographers...",
  "video_hook": "Ever wondered how to make your videos look professional?",
  "call_to_action": "Hit Subscribe for more tips!"
}
```

### Custos

- GPT-4 Turbo: ~$0.02 por clip
- DALL-E 3: ~$0.12 por thumbnail (3 por clip)
- **Total**: ~$0.38 por clip

## Geração de Thumbnails AI

### Processo

1. Lê `thumbnail_ideas` do metadata
2. Cria prompts detalhados para DALL-E 3
3. Gera 3 variações de thumbnail
4. Salva em `thumbnails/dalle/`

### Características

- Resolução: 1024x1024 (padrão DALL-E 3)
- Formato: PNG
- Tamanho: ~2-3 MB cada
- Estilo: Otimizado para YouTube

## Publicação no YouTube

### Autenticação

Na primeira execução com `--publish`:

1. Abre navegador para autorização OAuth
2. Login com conta Google
3. Autoriza upload de vídeos
4. Salva tokens em `.youtube_tokens.json`

Execuções subsequentes usam tokens salvos.

### Recursos Automáticos

- **Transcodificação**: AV1 → H.264 se necessário
- **Validação**: Verifica codec, duração, tamanho
- **Upload Resumível**: Suporta uploads grandes
- **Thumbnails**: Upload automático
- **Metadata**: Título, descrição, tags, categoria

### Limites do YouTube

- **Quota Diária**: 10,000 unidades
- **Upload**: ~1,600 unidades por vídeo
- **Limite**: ~6 vídeos/dia
- **Tamanho Máximo**: 256 GB ou 12 horas

## Troubleshooting

### "No heatmap data available"

**Causa**: Vídeo tem menos de 50,000 views  
**Solução**: Use vídeos mais populares

### "YouTube credentials not found"

**Causa**: Credenciais não configuradas no `.env`  
**Solução**: Configure `YOUTUBE_CLIENT_ID` e `YOUTUBE_CLIENT_SECRET`

### "OpenAI API key not found"

**Causa**: Chave OpenAI não configurada  
**Solução**: Configure `OPENAI_API_KEY` no `.env`

### "Codec not supported"

**Causa**: Vídeo usa codec AV1  
**Solução**: Automático - o pipeline transcodifica para H.264

### "Thumbnail upload failed: 413"

**Causa**: Thumbnail maior que 2 MB  
**Solução**: Em desenvolvimento - compressão automática

## Programação (Python)

Você também pode usar o orquestrador em código Python:

```python
from ab.dc.video_pipeline_orchestrator import VideoPipelineOrchestrator

# Criar orquestrador
orchestrator = VideoPipelineOrchestrator(
    provider='youtube',
    output_base='my_output',
    max_clip_duration=60,
    min_clip_duration=20
)

# Processar vídeo
result = orchestrator.process_video(
    url_or_id='RusBe_8arLQ',
    publish=True,
    privacy='private',
    dry_run=False
)

# Verificar resultado
if result['success']:
    print(f"Processado: {result['summary']['clips_created']} clips")
    print(f"Publicado: {result['summary']['published']} clips")
else:
    print(f"Erro: {result['error']}")
```

## Performance

### Tempo Estimado

Para um vídeo com 6 momentos populares:

- **Extração de momentos**: ~5s
- **Download do vídeo**: ~30s (depende da conexão)
- **Download de legendas**: ~5s
- **Criação de clips**: ~60s (6 clips × 10s cada)
- **Geração de metadata**: ~120s (6 clips × 20s cada)
- **Geração de thumbnails**: ~180s (6 clips × 30s cada)
- **Publicação**: ~300s (6 clips × 50s cada)

**Total**: ~12 minutos para processar e publicar 6 clips

### Otimizações

- Downloads paralelos (implementável)
- Geração de metadata em lote
- Cache de autenticação OAuth
- Reuso de vídeo baixado

## Custos Estimados

Para processar 1 vídeo com 6 clips:

| Item | Custo Unitário | Quantidade | Total |
|------|---------------|------------|-------|
| GPT-4 Metadata | $0.02 | 6 | $0.12 |
| DALL-E 3 Thumbnails | $0.04 | 18 (3×6) | $0.72 |
| **Total** | | | **$0.84** |

YouTube API: Gratuito (dentro da quota)

## Requisitos de Sistema

- **Python**: 3.8+
- **RAM**: 2 GB mínimo
- **Disco**: 10 GB por vídeo (temporário)
- **Internet**: Banda larga (download e upload)
- **OS**: macOS, Linux, Windows (com WSL)

## Limitações

1. **YouTube Heatmap**: Vídeos precisam ter 50k+ views
2. **Quota API**: ~6 vídeos/dia no YouTube
3. **OpenAI**: Limite de rate (TPM/RPM)
4. **Codec**: Apenas vídeos em MP4/WebM suportados

## Roadmap

- [ ] Suporte para TikTok
- [ ] Suporte para Instagram
- [ ] Compressão automática de thumbnails
- [ ] Processamento paralelo
- [ ] Interface web
- [ ] Agendamento de publicação
- [ ] Analytics de performance

## Suporte

Para problemas ou dúvidas:

1. Verifique os logs com `--verbose`
2. Revise os arquivos gerados em `output/`
3. Teste com `--dry-run` antes de publicar
4. Consulte a documentação dos componentes individuais

## Licença

Parte do projeto AEON-BRIDGE ab-video-processor.
