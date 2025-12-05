# Instalação Rápida

Guia rápido para instalar as dependências necessárias.

## ⚠️ IMPORTANTE: Diferença entre Pacotes Python e Programas do Sistema

### Pacotes Python (instalar com `pip`)
- `yt-dlp`
- `ffmpeg-python`
- `python-dotenv`
- `openai-whisper`
- `torch`

### Programas do Sistema (NÃO usar `pip`)
- **FFmpeg** - instalar com `brew` (macOS) ou `apt-get` (Ubuntu)
- **Homebrew** - gerenciador de pacotes do macOS

## Instalação Completa (macOS)

### Passo 1: Instalar Homebrew (se não tiver)

```bash
# Verificar se já está instalado
which brew

# Se não estiver, instalar:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Passo 2: Instalar FFmpeg (programa do sistema)

```bash
# Usar brew (NÃO usar pip!)
brew install ffmpeg

# Verificar
ffmpeg -version
```

### Passo 3: Instalar Pacotes Python

```bash
# Agora sim, usar pip para pacotes Python
pip install yt-dlp ffmpeg-python python-dotenv openai-whisper torch
```

## Instalação Completa (Ubuntu/Debian)

```bash
# Passo 1: Instalar FFmpeg (programa do sistema)
sudo apt-get update
sudo apt-get install ffmpeg

# Passo 2: Instalar pacotes Python
pip install yt-dlp ffmpeg-python python-dotenv openai-whisper torch
```

## Instalação Apenas para Legendas (sem FFmpeg)

Se você só precisa baixar legendas e não precisa processar vídeos:

```bash
# Apenas yt-dlp
pip install yt-dlp
```

Você poderá usar:
- `cli_subtitle.py` - Download de legendas
- `cli_subtitle_clipper.py` - Geração de legendas para clipes (requer momentos)

## Verificar Instalação

```bash
# Programas do sistema
ffmpeg -version
yt-dlp --version

# Python packages
python -c "import whisper; print('Whisper OK')"
python -c "from dotenv import load_dotenv; print('dotenv OK')"
```

## Comandos Comuns (Corretos vs Incorretos)

### ❌ INCORRETO

```bash
# NÃO FAZER ISSO!
pip install brew                    # brew NÃO é pacote Python
pip install ffmpeg                  # ffmpeg NÃO é pacote Python
pip install brew install ffmpeg     # Sintaxe completamente errada
```

### ✅ CORRETO

```bash
# Instalar FFmpeg (macOS)
brew install ffmpeg

# Instalar FFmpeg (Ubuntu)
sudo apt-get install ffmpeg

# Instalar pacotes Python
pip install yt-dlp
pip install ffmpeg-python
pip install python-dotenv
pip install openai-whisper torch
```

## Problemas Comuns

### Erro: "brew: command not found"

**Solução:** Instale o Homebrew primeiro (veja Passo 1 acima)

### Erro: "ffmpeg not found"

**Solução:**
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt-get install ffmpeg
```

### Erro: "yt-dlp not found"

**Solução:**
```bash
pip install yt-dlp
```

## Resumo dos Comandos

```bash
# ============================================
# macOS - Instalação Completa
# ============================================

# 1. Homebrew (se necessário)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. FFmpeg (sistema)
brew install ffmpeg

# 3. Pacotes Python
pip install yt-dlp ffmpeg-python python-dotenv openai-whisper torch

# ============================================
# Ubuntu/Debian - Instalação Completa
# ============================================

# 1. FFmpeg (sistema)
sudo apt-get update
sudo apt-get install ffmpeg

# 2. Pacotes Python
pip install yt-dlp ffmpeg-python python-dotenv openai-whisper torch

# ============================================
# Apenas Legendas (qualquer OS)
# ============================================

pip install yt-dlp
```

## Próximos Passos

Após instalar as dependências:

1. Teste a instalação:
   ```bash
   ffmpeg -version
   yt-dlp --version
   ```

2. Use os serviços:
   ```bash
   # Listar legendas disponíveis
   python cli_subtitle.py list "VIDEO_ID"

   # Baixar legenda
   python cli_subtitle.py download "VIDEO_ID" -l en
   ```

3. Consulte a documentação completa:
   - **INSTALLATION.md** - Guia detalhado
   - **SUBTITLE_SERVICE.md** - Serviço de legendas
   - **README.md** - Visão geral

## Ajuda

Se tiver problemas, verifique:
1. Que você está usando `brew install` para FFmpeg, não `pip install`
2. Que você está usando `pip install` apenas para pacotes Python
3. A documentação em INSTALLATION.md para troubleshooting detalhado