# Instagram Video Downloader 📹

Scripts Python para baixar vídeos do Instagram de forma simples e eficiente.

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

#### Opção B: Instalação manual
```bash
pip install -r requirements.txt
```

ou simplesmente:
```bash
pip install yt-dlp
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

## 📝 Exemplos de URLs Suportadas

- Posts: `https://www.instagram.com/p/XXXXX/`
- Reels: `https://www.instagram.com/reel/XXXXX/`
- IGTV: `https://www.instagram.com/tv/XXXXX/`

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
- ✅ Use de acordo com os Termos de Serviço do Instagram
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

**Nota**: O Instagram pode alterar sua estrutura a qualquer momento, o que pode afetar o funcionamento destes scripts. Mantenha o yt-dlp atualizado para melhores resultados.
