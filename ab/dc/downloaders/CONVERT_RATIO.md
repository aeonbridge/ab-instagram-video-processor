# Video Aspect Ratio Converter

Serviço para converter vídeos para diferentes aspect ratios, organizando a saída em pastas por ratio.

## Características

- Suporta conversão de arquivos individuais ou pastas inteiras
- Organiza automaticamente os vídeos convertidos em pastas nomeadas pelo ratio
- Verifica arquivos existentes para evitar reconversões
- Padrão de nomenclatura consistente com cli_clipper.py
- Suporte a múltiplos codecs e opções de qualidade

## Aspect Ratios Suportados

| Ratio | Dimensões | Uso |
|-------|-----------|-----|
| 9:16 | 1080x1920 | Instagram Reels, TikTok, YouTube Shorts (Vertical) |
| 16:9 | 1920x1080 | YouTube, Vídeos widescreen padrão (Horizontal) |
| 1:1 | 1080x1080 | Instagram Feed (Quadrado) |
| 4:5 | 1080x1350 | Instagram Portrait |

## Instalação

Requer FFmpeg instalado no sistema:

```bash
# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg
```

## Uso

### Sintaxe Básica

```bash
python convert_ratio.py <arquivo_ou_pasta> --ratio <ratio>
```

### Exemplos

#### Converter um vídeo para 9:16 (Reels/TikTok)
```bash
python convert_ratio.py video.mp4 --ratio 9:16
```

#### Converter todos vídeos de uma pasta para 16:9
```bash
python convert_ratio.py videos/ --ratio 16:9
```

#### Converter com qualidade alta (CRF baixo = melhor qualidade)
```bash
python convert_ratio.py video.mp4 --ratio 1:1 --crf 18
```

#### Forçar re-conversão mesmo se o arquivo já existir
```bash
python convert_ratio.py video.mp4 --ratio 4:5 --force
```

#### Especificar pasta de saída customizada
```bash
python convert_ratio.py videos/ --ratio 9:16 --output ./reels
```

#### Usar codec H.265 (melhor compressão)
```bash
python convert_ratio.py video.mp4 --ratio 9:16 --codec libx265
```

#### Conversão rápida com preset ultrafast
```bash
python convert_ratio.py video.mp4 --ratio 16:9 --preset ultrafast
```

## Opções

### Obrigatórias

- `input`: Arquivo de vídeo ou pasta com vídeos
- `--ratio`, `-r`: Aspect ratio de saída (9:16, 16:9, 1:1, 4:5)

### Opcionais

- `--output`, `-o`: Pasta de saída (padrão: pasta com nome do ratio)
- `--codec`: Codec de vídeo - libx264 (padrão), libx265
- `--crf`: Qualidade CRF (18-28, menor=melhor, padrão: 23)
- `--preset`: Preset de encoding (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow, padrão: medium)
- `--force`, `-f`: Sobrescrever arquivos existentes
- `--verbose`, `-v`: Log detalhado

## Padrão de Nomenclatura

Os arquivos convertidos seguem o padrão:

```
{nome_original}_{ratio}.mp4
```

Exemplos:
- `video_9x16.mp4` - Vídeo convertido para 9:16
- `RusBe_8arLQ_0000_30s_score_095_16x9.mp4` - Clip convertido para 16:9

## Estrutura de Saída

```
pasta_origem/
├── video1.mp4
├── video2.mp4
└── 9x16/                    # Pasta criada automaticamente
    ├── video1_9x16.mp4
    └── video2_9x16.mp4
```

Ou com output customizado:

```bash
python convert_ratio.py videos/ --ratio 9:16 --output ./reels
```

```
reels/
├── video1_9x16.mp4
└── video2_9x16.mp4
```

## Comportamento

### Detecção de Duplicatas
- Por padrão, o script **não** reconverte vídeos que já existem na pasta de saída
- Use `--force` para forçar reconversão

### Processamento de Pastas
- Suporta extensões: .mp4, .mov, .avi, .mkv, .flv, .webm, .m4v
- Case-insensitive (.MP4, .Mp4, etc.)
- Processa apenas na pasta especificada (não recursivo em subpastas)

### Conversão de Aspect Ratio
A conversão funciona da seguinte forma:
1. **Crop**: Recorta o vídeo para o aspect ratio desejado (centralizado)
2. **Scale**: Redimensiona para as dimensões alvo

Exemplo 9:16 em vídeo 16:9:
- Recorta laterais (mantém centro)
- Escala para 1080x1920

## Qualidade e Performance

### CRF (Constant Rate Factor)
- **18**: Qualidade altíssima (arquivos grandes)
- **23**: Qualidade boa (padrão, balanceado)
- **28**: Qualidade aceitável (arquivos menores)

### Presets
Velocidade vs Compressão:
- **ultrafast**: Muito rápido, arquivos maiores
- **medium**: Balanceado (padrão)
- **veryslow**: Muito lento, melhor compressão

### Codecs
- **libx264** (H.264): Padrão, compatibilidade máxima
- **libx265** (H.265/HEVC): Melhor compressão, arquivos 30-50% menores

## Resumo da Conversão

Ao final, o script exibe um resumo:

```
============================================================
RESUMO DA CONVERSÃO
============================================================
Total de vídeos: 5
Convertidos com sucesso: 4
Já existiam (pulados): 1
Falharam: 0
Pasta de saída: /path/to/9x16
============================================================
```

## Códigos de Saída

- `0`: Todos os vídeos convertidos com sucesso
- `1`: Todos os vídeos falharam
- `2`: Alguns vídeos falharam (conversão parcial)

## Limitações

- Vídeos corrompidos ou sem moov atom podem falhar
- Timeout de 10 minutos por vídeo
- Requer espaço em disco para os arquivos convertidos
- Não processa subpastas recursivamente

## Integração com Outros Serviços

O script pode ser usado em pipelines com outros serviços:

```bash
# Baixar vídeo, extrair clips e converter para Reels
python cli.py VIDEO_ID --format json | \
python cli_clipper.py | \
python convert_ratio.py processed_videos/VIDEO_ID/ --ratio 9:16
```

## Troubleshooting

### Erro "moov atom not found"
Vídeo está corrompido ou incompleto. Tente baixar novamente.

### Erro "Invalid data found when processing input"
Arquivo não é um vídeo válido ou está corrompido.

### FFmpeg não encontrado
Instale o FFmpeg: `brew install ffmpeg` (macOS) ou `apt-get install ffmpeg` (Linux)

### Conversão muito lenta
Use preset mais rápido: `--preset faster` ou `--preset ultrafast`

### Arquivos muito grandes
Use CRF maior (menor qualidade): `--crf 28` ou codec H.265: `--codec libx265`