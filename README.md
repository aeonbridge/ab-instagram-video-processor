# Video Downloader 📹

Scripts Python para baixar vídeos do Instagram, YouTube e outras plataformas de forma simples e eficiente.

> **Open Source Project** sponsored by [AeonBridge Co.](https://aeonbridge.co)

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

### Script Completo (`instagram_video_downloader.py`)

Este script oferece mais opções e feedback detalhado:

```bash
# Uso interativo
python instagram_video_downloader.py

# Ou passar a URL diretamente
python instagram_video_downloader.py https://www.instagram.com/p/DRfm-7diW8-/
```

**Recursos:**
- ✅ Interface interativa amigável
- 📊 Mostra progresso do download
- 📁 Permite escolher diretório de saída
- 🔍 Exibe informações do vídeo antes de baixar
- ⚡ Tratamento de erros detalhado

### Script Rápido (`instagram_quick_download.py`)

Para downloads rápidos sem muitas opções:

```bash
# Uso interativo
python instagram_quick_download.py

# Ou passar a URL diretamente
python instagram_quick_download.py https://www.instagram.com/p/DRfm-7diW8-/
```

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
├── instagram_video_downloader.py  # Script principal completo
├── instagram_quick_download.py    # Script simplificado
├── requirements.txt               # Dependências
├── README.md                      # Este arquivo
└── downloads/                     # Pasta onde os vídeos são salvos (criada automaticamente)
```

## ⚙️ Configurações Avançadas

### Mudar o Diretório de Download

No script completo, você pode especificar onde salvar:
```python
download_instagram_video(url, output_dir="meus_videos")
```

### Formato de Saída

Por padrão, o script baixa no melhor formato disponível (geralmente MP4).

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

## 🔒 Limitações

- **Posts Privados**: Não é possível baixar posts de contas privadas sem autenticação
- **Stories**: Stories não são suportados por questões de privacidade
- **Lives**: Transmissões ao vivo não podem ser baixadas enquanto estão acontecendo

## 📋 Requisitos do Sistema

- Python 3.7 ou superior
- Conexão com a internet
- Espaço em disco suficiente para os vídeos

## 🤝 Uso Responsável

Este script é fornecido apenas para fins educacionais. Por favor:
- ✅ Respeite os direitos autorais
- ✅ Baixe apenas conteúdo que você tem permissão para baixar
- ✅ Use de acordo com os Termos de Serviço das plataformas
- ❌ Não use para distribuição não autorizada de conteúdo

## 📄 Licença

Este projeto é licenciado sob a [MIT License](LICENSE) - a licença open source mais permissiva, permitindo uso comercial, modificação, distribuição e uso privado sem restrições.

Copyright (c) 2024 AeonBridge Co.

## 🆘 Suporte

Se encontrar problemas:
1. Verifique se tem a versão mais recente do yt-dlp: `pip install --upgrade yt-dlp`
2. Tente o script simplificado primeiro
3. Verifique se a URL está acessível no navegador

---

**Nota**: As plataformas podem alterar sua estrutura a qualquer momento, o que pode afetar o funcionamento destes scripts. Mantenha o yt-dlp atualizado para melhores resultados.
