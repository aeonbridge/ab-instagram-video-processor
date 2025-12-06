# Subtitle Cleaner Service

Serviço para limpar arquivos de legenda (VTT/SRT), removendo timestamps e tags, e gerando arquivos Markdown otimizados para LLMs criarem metadados virais.

## Visão Geral

O Subtitle Cleaner processa arquivos de legenda extraindo apenas o texto limpo e criando documentos Markdown formatados com instruções para que LLMs (ChatGPT, Claude, etc.) gerem metadados otimizados para plataformas de vídeo.

## Características

- Remove timestamps, tags VTT/SRT e formatação
- Elimina duplicações de texto (comum em VTT do YouTube)
- Mantém ordem cronológica do conteúdo
- Gera Markdown com instruções detalhadas para LLMs
- Extrai metadados do nome do arquivo (video_id, duração)
- Suporta processamento em lote
- Formatos suportados: VTT, SRT

## Instalação

Não requer dependências adicionais - usa apenas bibliotecas padrão do Python.

## Uso

### CLI - Arquivo Único

```bash
# Limpar um arquivo de legenda
python cli_subtitle_cleaner.py clean subtitle.vtt

# Com saída customizada
python cli_subtitle_cleaner.py clean subtitle.vtt -o output.md

# Apenas texto limpo (sem instruções LLM)
python cli_subtitle_cleaner.py clean subtitle.vtt --text-only

# Com preview do resultado
python cli_subtitle_cleaner.py clean subtitle.vtt --preview

# Forçar sobrescrever arquivo existente
python cli_subtitle_cleaner.py clean subtitle.vtt --force
```

### CLI - Processamento em Lote

```bash
# Processar todos os arquivos VTT de um diretório
python cli_subtitle_cleaner.py batch processed_videos/VIDEO_ID/

# Processar arquivos SRT
python cli_subtitle_cleaner.py batch subtitles/ --pattern "*.srt"

# Forçar sobrescrever arquivos existentes
python cli_subtitle_cleaner.py batch videos/ --force

# Apenas texto (sem instruções)
python cli_subtitle_cleaner.py batch videos/ --text-only
```

### Python API

```python
from pathlib import Path
from subtitle_cleaner import SubtitleCleaner

# Inicializar
cleaner = SubtitleCleaner()

# Processar arquivo único
md_path = cleaner.process_subtitle_file(
    subtitle_path=Path("video.vtt"),
    include_llm_instructions=True
)

# Processar diretório
created_files = cleaner.process_directory(
    directory=Path("processed_videos/VIDEO_ID/"),
    pattern="*.vtt",
    overwrite=False
)

# Limpar apenas o texto
text = cleaner.clean_vtt(Path("video.vtt"))
print(text)
```

## Formato de Saída

O arquivo Markdown gerado inclui:

### 1. Informações do Vídeo
Extraídas automaticamente do nome do arquivo:
- **Video ID**: Identificador do vídeo
- **Duration**: Duração em minutos e segundos

### 2. Instruções para LLM
Diretrizes detalhadas para gerar:
- **Título**: Máx 100 caracteres, engajante e viral
- **Descrição**: 200-500 palavras com hook e hashtags
- **Tags**: 10-15 tags relevantes e otimizadas
- **Categoria**: Seleção da categoria apropriada
- **Ideias de Thumbnail**: 3 conceitos visuais

### 3. Transcrição Limpa
Texto extraído sem timestamps, sem tags, sem duplicações

### 4. Template de Saída JSON
Formato JSON estruturado para resposta do LLM, facilitando integração e automação

## Exemplo de Saída

```markdown
# Video Transcript for Metadata Generation

## Video Information

- **Video ID**: RusBe_8arLQ
- **Duration**: 0m 40s

## Instructions

Based on the transcript below, generate viral video metadata:

1. **Title** (max 100 characters):
   - Engaging and clickable
   - Include main topic/benefit
   - Use power words

[... instruções completas ...]

## Video Transcript

this year let's go you gotta just press record hey what's up it's omar's corey
with think media and this channel is all about helping you build your influence
with online video and so if you're interested in that be sure to hit that
subscribe button...

---

## Output Format

Please provide the metadata as a JSON object in the following format:

```json
{
  "title": "Your engaging title here (max 100 characters)",
  "description": "Your compelling description with hashtags and call-to-action",
  "tags": [
    "tag1",
    "tag2",
    "tag3",
    "tag4",
    "tag5"
  ],
  "category": "selected_category",
  "thumbnail_ideas": [
    {
      "concept": "Concept 1 description",
      "text_overlay": "Suggested text for thumbnail",
      "color_scheme": "Color palette suggestion"
    },
    {
      "concept": "Concept 2 description",
      "text_overlay": "Suggested text for thumbnail",
      "color_scheme": "Color palette suggestion"
    },
    {
      "concept": "Concept 3 description",
      "text_overlay": "Suggested text for thumbnail",
      "color_scheme": "Color palette suggestion"
    }
  ],
  "target_audience": "Description of target demographic",
  "video_hook": "First 5 seconds hook to capture attention",
  "call_to_action": "Specific CTA for end of video/description"
}
```
```

## Vantagens do Formato JSON

O template de saída em JSON oferece múltiplos benefícios:

### 1. Automação Completa
```python
import json

# LLM retorna JSON
llm_response = get_llm_response(markdown_content)
metadata = json.loads(llm_response)

# Usar diretamente na publicação
publisher.upload_video(
    video_path=video,
    title=metadata['title'],
    description=metadata['description'],
    tags=metadata['tags'],
    category=metadata['category']
)
```

### 2. Validação Estruturada
```python
# Validar campos obrigatórios
required_fields = ['title', 'description', 'tags', 'category']
if all(field in metadata for field in required_fields):
    # Proceder com publicação
    pass
```

### 3. Processamento em Lote
```python
# Gerar metadados para múltiplos vídeos
for md_file in Path('processed_videos/VIDEO_ID/').glob('*.md'):
    with open(md_file) as f:
        content = f.read()

    # Enviar para LLM e obter JSON
    metadata = get_llm_metadata(content)

    # Salvar para uso posterior
    json_file = md_file.with_suffix('.json')
    with open(json_file, 'w') as f:
        json.dump(metadata, f, indent=2)
```

### 4. Integração com Ferramentas
- **APIs**: Fácil integração com APIs de publicação
- **Databases**: Armazenar metadados estruturados
- **Analytics**: Análise de performance por categoria/tags
- **A/B Testing**: Testar diferentes títulos/descrições

## Workflow Completo

### Pipeline de Produção de Conteúdo

```bash
# 1. Extrair momentos populares
cd ab/dc/analysers
python cli.py VIDEO_ID --format json > moments.json

# 2. Criar clipes de vídeo
cd ../downloaders
python cli_clipper.py --input ../analysers/moments.json --aspect-ratio 9:16

# 3. Gerar arquivos de legenda para cada clipe
python cli_subtitle_clipper.py --video-id VIDEO_ID -l en

# 4. Limpar legendas para formato LLM
python cli_subtitle_cleaner.py batch processed_videos/VIDEO_ID/

# 5. Usar Markdown com LLM para gerar metadados
# Copiar conteúdo do .md e colar no ChatGPT/Claude

# 6. Publicar no YouTube com metadados gerados
cd ../publishers
python cli_publisher.py upload processed_videos/VIDEO_ID/clip.mp4 \
  --title "Título Gerado pelo LLM" \
  --description "Descrição gerada..." \
  --tags "tag1,tag2,tag3"
```

## Estrutura de Arquivos

```
processed_videos/
└── VIDEO_ID/
    ├── VIDEO_ID_0000_40s_score_095_original_en.mp4    # Vídeo
    ├── VIDEO_ID_0000_40s_score_095_original_en.vtt    # Legenda original
    └── VIDEO_ID_0000_40s_score_095_original_en.md     # Markdown limpo (LLM-ready)
```

## Detalhes Técnicos

### Limpeza de VTT

O formato VTT do YouTube tem estrutura peculiar onde o texto acumula:
```
Linha 1: "hello"
Linha 2: "hello world"
Linha 3: "hello world how"
```

O serviço detecta isso e extrai apenas o texto novo, mantendo ordem cronológica.

### Algoritmo de Deduplicação

1. Remove tags VTT: `<00:00:14.719><c>`, `</c>`
2. Remove timestamps: `00:00:00.000 --> 00:00:00.769`
3. Processa linha por linha incrementalmente
4. Detecta sobreposições entre linhas consecutivas
5. Adiciona apenas conteúdo novo
6. Mantém ordem cronológica

### Tratamento de SRT

Arquivos SRT são processados de forma similar:
- Remove números de sequência
- Remove timestamps
- Remove tags `<...>` e `{...}`
- Junta texto por blocos

## Casos de Uso

### 1. Geração de Metadados para YouTube

Usar o Markdown gerado com ChatGPT/Claude para criar:
- Títulos otimizados para SEO
- Descrições com hashtags virais
- Tags estratégicas
- Ideias de thumbnail chamativas

### 2. Criação de Conteúdo Multi-Plataforma

Gerar metadados diferentes para cada plataforma:
- YouTube: Títulos descritivos, descrições longas
- TikTok: Títulos curtos, hashtags trending
- Instagram: Captions engajantes

### 3. Análise de Conteúdo

Extrair texto limpo para:
- Análise de sentimento
- Extração de palavras-chave
- Identificação de tópicos
- Geração de resumos

### 4. Acessibilidade

Converter legendas em texto puro para:
- Leitores de tela
- Documentação
- Transcrições de áudio

## Exemplos de Uso com LLMs

### Com ChatGPT

```
1. Processar legenda:
   python cli_subtitle_cleaner.py clean video.vtt

2. Copiar conteúdo do .md gerado

3. Colar no ChatGPT com prompt:
   "Use as instruções no documento para gerar metadados virais"

4. ChatGPT retorna metadados no formato especificado

5. Usar metadados para publicar vídeo
```

### Com Claude

```
1. Mesmo processo de limpeza

2. Enviar .md para Claude Code ou Claude.ai

3. Claude gera metadados seguindo template

4. Copiar e usar na publicação
```

### Prompts Customizados

Você pode editar o arquivo Markdown para adicionar:
- Instruções específicas para seu nicho
- Exemplos de títulos bem-sucedidos
- Guidelines de tom de voz
- Palavras-chave obrigatórias

## Configuração Avançada

### Customizar Instruções LLM

Editar `subtitle_cleaner.py`, método `create_llm_markdown()`:

```python
# Adicionar instruções customizadas
md_lines.append("## Additional Guidelines")
md_lines.append("")
md_lines.append("- Use linguagem jovem e descontraída")
md_lines.append("- Foco em público 18-25 anos")
md_lines.append("- Incluir call-to-action para inscrição")
```

### Processar Apenas Texto

```python
cleaner = SubtitleCleaner()
text = cleaner.clean_vtt(Path("video.vtt"))
# text contém apenas o texto limpo, sem Markdown
```

## Limitações

- Funciona melhor com VTT/SRT gerados por plataformas de vídeo
- Legendas muito fragmentadas podem precisar revisão manual
- Arquivos muito grandes (>10MB) podem demorar mais para processar
- Não traduz legendas (mantém idioma original)

## Troubleshooting

### Texto com Duplicações

Se ainda houver duplicações:
```bash
# Usar modo text-only e revisar manualmente
python cli_subtitle_cleaner.py clean video.vtt --text-only
```

### Encoding Incorreto

```python
# Especificar encoding ao ler arquivo
with open(vtt_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()
```

### Arquivo Não Encontrado

Verificar caminho absoluto:
```bash
python cli_subtitle_cleaner.py clean "$(pwd)/video.vtt"
```

## Integração com Outros Serviços

### Com Video Clipper

Legendas são geradas automaticamente junto com os clipes:
```bash
python cli_clipper.py --input moments.json
python cli_subtitle_clipper.py --video-id VIDEO_ID -l en
python cli_subtitle_cleaner.py batch processed_videos/VIDEO_ID/
```

### Com YouTube Publisher

Metadados gerados podem ser usados diretamente:
```bash
# Após gerar metadados com LLM
python cli_publisher.py upload video.mp4 \
  --title "$(cat metadata_title.txt)" \
  --description "$(cat metadata_description.txt)" \
  --tags "$(cat metadata_tags.txt)"
```

## Performance

- **VTT pequeno (< 50KB)**: < 1 segundo
- **VTT médio (50-500KB)**: 1-3 segundos
- **VTT grande (> 500KB)**: 3-10 segundos
- **Batch (100 arquivos)**: 1-2 minutos

## Roadmap

- [ ] Suporte para mais formatos (ASS, SSA)
- [ ] Detecção automática de idioma
- [ ] Geração de metadados com IA integrada
- [ ] Templates customizáveis por nicho
- [ ] Export para outros formatos (JSON, TXT, DOCX)
- [ ] API REST para processamento remoto

## Contribuindo

Melhorias são bem-vindas! Áreas de interesse:
- Otimização do algoritmo de deduplicação
- Suporte para legendas multi-idioma
- Templates adicionais para LLMs
- Integração com APIs de IA

## Licença

Segue a licença do projeto principal.

---

**Status**: Produção
**Versão**: 1.0.0
**Última Atualização**: 2025-12-05
