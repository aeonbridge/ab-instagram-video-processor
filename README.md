# AB Video Processor 📹

Suite completa de ferramentas Python para processamento de vídeos e áudio: download, extração, transcrição, busca e monitoramento de tendências.

> **Open Source Project** sponsored by [AeonBridge Co.](https://aeonbridge.co)

## Ferramentas Disponíveis

- **Download de Vídeos** - Instagram, YouTube e 1000+ plataformas
- **Extração de Áudio** - Conversão para MP3, M4A, WAV, FLAC, OGG
- **Transcrição de Áudio** - Transcrição automática com OpenAI Whisper
- **Busca no YouTube** - Busca avançada com filtros e exportação para CSV
- **Monitoramento de Tendências** - Agente agnóstico para múltiplas plataformas (YouTube, Twitter/X, Google Search)

## 🚀 Instalação

### 1. Instalar Python
Certifique-se de ter Python 3.7+ instalado:
```bash
python --version
```

### 2. Instalar Dependências

#### Opção A: Instalação automática
Os scripts instalam automaticamente o `yt-dlp` quando executados pela primeira vez.

#### Opção B: Usando pip
```bash
# Dependências básicas (download e extração de áudio)
pip install -r requirements.txt

# Com suporte a transcrição de áudio (Whisper)
pip install -r requirements.txt openai-whisper torch
```

#### Opção C: Usando uv (recomendado - mais rápido)
```bash
# Instalar uv (se ainda não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Dependências básicas
uv pip install -r requirements.txt

# Ou usando pyproject.toml
uv sync

# Com suporte a transcrição
uv sync --extra transcription

# Todas as dependências
uv sync --extra all
```

## 📖 Como Usar

### 1. Download de Vídeos

#### Script Completo (`instagram_video_downloader.py`)

```bash
# Uso interativo
python instagram_video_downloader.py

# Ou passar a URL diretamente
python instagram_video_downloader.py https://www.instagram.com/p/DRfm-7diW8-/
```

**Recursos:**
- Interface interativa amigável
- Progresso do download em tempo real
- Escolha de diretório de saída
- Informações detalhadas do vídeo

#### Script Rápido (`instagram_quick_download.py`)

```bash
python instagram_quick_download.py https://www.instagram.com/p/DRfm-7diW8-/
```

### 2. Extração de Áudio

#### Extrator Completo (`audio_extractor.py`)

```bash
# De uma URL
python audio_extractor.py https://www.youtube.com/watch?v=VIDEO_ID

# De um arquivo local
python audio_extractor.py video.mp4
```

**Formatos suportados:** MP3, M4A, WAV, FLAC, OGG

#### Extrator Rápido (`quick_audio_extract.py`)

```bash
# Extração rápida para MP3
python quick_audio_extract.py video.mp4

# Com formato específico
python quick_audio_extract.py video.mp4 wav
```

#### Extração em Lote (`batch_audio_extract.py`)

```bash
# Processa múltiplos vídeos em paralelo
python batch_audio_extract.py
```

### 3. Transcrição de Áudio

```bash
# Transcrição automática
python transcribe_audio.py audio.mp3

# Com modelo específico
python transcribe_audio.py audio.mp3 medium

# Com idioma específico
python transcribe_audio.py audio.mp3 medium pt
```

**Modelos disponíveis:** tiny, base, small, medium, large

**Saída:** Arquivo Markdown em `transcriptions/`

### 4. Busca no YouTube

```bash
# Configurar chave da API no .env
cp .env.example .env
# Edite .env e adicione YOUTUBE_API_KEY

# Executar busca
python youtube_video_search.py
```

**Resultados:**
- `youtube_jogos_dataset.csv` - Dataset completo (60+ campos)
- `youtube_jogos_results.txt` - Resumo legível

### 5. Monitoramento de Tendências

#### Configuração

```bash
# Adicionar chaves de API no .env
YOUTUBE_API_KEY=sua_chave
TWITTER_BEARER_TOKEN=seu_token
GOOGLE_API_KEY=sua_chave
GOOGLE_SEARCH_ENGINE_ID=seu_id
```

#### Execução Única

```bash
# Monitorar games
python trend_monitor_agent.py --config config_games.json

# Monitorar tech
python trend_monitor_agent.py --config config_tech.json

# Tópico customizado
python trend_monitor_agent.py --topic "inteligência artificial"
```

#### Monitoramento Contínuo

```bash
# Executar a cada 6 horas
python trend_monitor_scheduler.py --config config_games.json --interval 6
```

**Fontes de dados:**
- YouTube (vídeos, canais, estatísticas)
- Twitter/X (tweets, engajamento, perfis)
- Google Search (notícias, artigos, eventos)

**Saída:** CSV unificado em `trend_data/` com schema padronizado

Ver [README_TREND_MONITOR.md](README_TREND_MONITOR.md) para documentação completa.

## 📝 Plataformas e URLs Suportadas

### Instagram
- Posts: `https://www.instagram.com/p/XXXXX/`
- Reels: `https://www.instagram.com/reel/XXXXX/`
- IGTV: `https://www.instagram.com/tv/XXXXX/`

### YouTube
- Vídeos: `https://www.youtube.com/watch?v=XXXXX`
- Shorts: `https://www.youtube.com/shorts/XXXXX`
- Playlists: `https://www.youtube.com/playlist?list=XXXXX`

### Outras Plataformas
O projeto utiliza `yt-dlp`, que suporta [1000+ sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md), incluindo:
- TikTok, Twitter/X, Facebook, Vimeo, Twitch, Reddit, e muitos outros

## 📂 Estrutura de Arquivos

```
.
├── instagram_video_downloader.py  # Download completo de vídeos
├── instagram_quick_download.py    # Download rápido
├── audio_extractor.py             # Extração de áudio completa
├── quick_audio_extract.py         # Extração rápida
├── batch_audio_extract.py         # Extração em lote
├── transcribe_audio.py            # Transcrição com Whisper
├── youtube_video_search.py        # Busca avançada no YouTube
├── trend_monitor_agent.py         # Agente de monitoramento
├── trend_monitor_scheduler.py     # Agendador de monitoramento
├── config_games.json              # Configuração para games
├── config_tech.json               # Configuração para tech
├── requirements.txt               # Dependências
├── .env.example                   # Template de configuração
├── README.md                      # Este arquivo
├── README_TREND_MONITOR.md        # Documentação do agente
├── downloads/                     # Vídeos baixados
├── audio_downloads/               # Áudios extraídos
├── transcriptions/                # Transcrições
└── trend_data/                    # Datasets de tendências
```

## ⚙️ Configurações e APIs

### Chaves de API Necessárias

Para usar todas as funcionalidades, configure o arquivo `.env`:

```bash
cp .env.example .env
```

Adicione suas chaves:

```env
# YouTube Data API v3 (busca e monitoramento)
YOUTUBE_API_KEY=sua_chave_aqui

# Twitter API v2 (monitoramento de tendências)
TWITTER_BEARER_TOKEN=seu_bearer_token

# Google Custom Search API (busca de notícias)
GOOGLE_API_KEY=sua_chave_google
GOOGLE_SEARCH_ENGINE_ID=seu_search_engine_id
```

**Como obter:**
- **YouTube API:** [Google Cloud Console](https://console.developers.google.com/) → Ativar YouTube Data API v3
- **Twitter API:** [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard) → Criar App → Gerar Bearer Token
- **Google Search API:** [Google Cloud Console](https://console.developers.google.com/) → Custom Search API + [Custom Search Engine](https://programmablesearchengine.google.com/)

### Configurações Customizadas

#### Diretórios de Saída

```python
# Download de vídeos
download_instagram_video(url, output_dir="meus_videos")

# Extração de áudio
extract_audio(video, output_dir="meus_audios")
```

#### Formatos de Áudio

Suportados: MP3, M4A, WAV, FLAC, OGG

#### Monitoramento de Tendências

Crie arquivos JSON personalizados baseados em `config_games.json` ou `config_tech.json` para qualquer tópico.

## 🔧 Solução de Problemas

### Erro: "URL inválida"
- Verifique se a URL está completa e correta
- Certifique-se de que é uma URL do Instagram

### Erro: "Download failed"
- O post pode ser privado (requer login)
- Tente novamente após alguns minutos
- Verifique sua conexão com a internet

### Erro: "yt-dlp not found"
Execute:
```bash
pip install --upgrade yt-dlp
```

### Erro: "Unknown encoder 'libmp3lame'" (macOS)
Este erro ocorre quando o ffmpeg foi compilado sem suporte a MP3.

**Solução:** Reinstale o ffmpeg via Homebrew:
```bash
brew uninstall ffmpeg
brew install ffmpeg
```

Se você tiver múltiplas versões do ffmpeg instaladas, adicione ao seu `~/.zshrc`:
```bash
export PATH="/opt/homebrew/bin:$PATH"
```

### Erro: "ffmpeg error (see stderr output for detail)"
Possíveis causas:
1. **Codec não suportado** - Reinstale o ffmpeg: `brew install ffmpeg`
2. **Versão antiga do ffmpeg** - Atualize: `brew upgrade ffmpeg`
3. **Múltiplas instalações do ffmpeg** - Verifique qual está sendo usada: `which ffmpeg`

### Erro: "ffmpeg não está instalado"
Instale o ffmpeg:
```bash
# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg

# Linux (Fedora)
sudo dnf install ffmpeg
```

## 📊 Casos de Uso

### Análise de Mercado
- Monitorar lançamentos de produtos
- Acompanhar concorrentes
- Identificar tendências emergentes

### Pesquisa de Conteúdo
- Coletar dados de vídeos para análise
- Extrair áudio para processamento
- Transcrever conteúdo automaticamente

### Social Media Intelligence
- Monitorar menções de marca
- Analisar engajamento de conteúdo
- Identificar influenciadores

### Gaming & Esports
- Acompanhar lançamentos de jogos
- Monitorar streamers e torneios
- Analisar tendências do setor

## 🔒 Limitações

### Downloads
- **Posts Privados**: Requer autenticação
- **Stories**: Não suportado por privacidade
- **Lives**: Não podem ser baixadas durante transmissão

### APIs (Quotas Gratuitas)
- **YouTube:** 10.000 unidades/dia
- **Twitter Essential:** 500.000 tweets/mês
- **Google Search:** 100 consultas/dia

## 📋 Requisitos do Sistema

- Python 3.7 ou superior
- ffmpeg (para extração de áudio)
- Conexão com a internet
- Espaço em disco adequado

## 🤝 Uso Responsável

Este script é fornecido apenas para fins educacionais. Por favor:
- ✅ Respeite os direitos autorais
- ✅ Baixe apenas conteúdo que você tem permissão para baixar
- ✅ Use de acordo com os Termos de Serviço das plataformas
- ❌ Não use para distribuição não autorizada de conteúdo

## 📄 Licença

Este projeto é licenciado sob a [MIT License](LICENSE) - a licença open source mais permissiva, permitindo uso comercial, modificação, distribuição e uso privado sem restrições.

Copyright (c) 2024 AeonBridge Co.

## 📚 Documentação Adicional

- [README_TREND_MONITOR.md](README_TREND_MONITOR.md) - Documentação completa do Agente de Monitoramento
- [CLAUDE.md](CLAUDE.md) - Guia de referência para desenvolvimento

## 🆘 Suporte

Se encontrar problemas:
1. Verifique se tem a versão mais recente: `pip install --upgrade yt-dlp`
2. Consulte as instruções de solução de problemas acima
3. Verifique se as chaves de API estão configuradas corretamente no `.env`
4. Para o agente de monitoramento, veja [README_TREND_MONITOR.md](README_TREND_MONITOR.md)

## 🚀 Roadmap

### Próximas Funcionalidades
- [ ] Suporte para Reddit API
- [ ] Suporte para TikTok API
- [ ] Análise de sentimentos em comentários
- [ ] Dashboard web para visualização
- [ ] Detecção automática de trending topics
- [ ] Alertas em tempo real
- [ ] Exportação para bancos de dados
- [ ] API REST para integração

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se livre para:
- Reportar bugs
- Sugerir novas funcionalidades
- Enviar pull requests
- Melhorar a documentação

---

**Nota**: As plataformas podem alterar sua estrutura a qualquer momento. Mantenha as dependências atualizadas para melhores resultados.
