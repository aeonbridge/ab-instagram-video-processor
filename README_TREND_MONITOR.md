# Agente de Monitoramento de Tendências

Sistema agnóstico para monitorar tendências de qualquer assunto através de múltiplas plataformas e gerar datasets ricos em CSV.

## Características

### Fontes de Dados Suportadas

1. **YouTube**
   - Vídeos trending
   - Estatísticas completas (views, likes, comments)
   - Informações de canal
   - Tags e categorias

2. **Twitter/X**
   - Tweets recentes
   - Métricas de engajamento
   - Informações de perfil
   - Hashtags e menções

3. **Google Search**
   - Notícias recentes
   - Artigos
   - Eventos
   - Resultados ordenados por data

### Schema Unificado do Dataset

Todos os dados são normalizados em um schema comum com 25+ campos:

- **Identificação:** source, type, id, url
- **Conteúdo:** title, description, author, published_at
- **Métricas:** view_count, like_count, comment_count, share_count, engagement_score
- **Metadados:** tags, language, category_id, thumbnail
- **Contexto:** topic, collected_at

## Configuração

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar APIs

Copie `.env.example` para `.env` e adicione suas chaves:

```bash
cp .env.example .env
```

Edite `.env`:

```env
# YouTube Data API v3
YOUTUBE_API_KEY=sua_chave_aqui

# Twitter API v2
TWITTER_BEARER_TOKEN=seu_bearer_token_aqui

# Google Custom Search API
GOOGLE_API_KEY=sua_chave_aqui
GOOGLE_SEARCH_ENGINE_ID=seu_search_engine_id_aqui
```

#### Como Obter as Chaves de API

**YouTube API:**
1. Acesse [Google Cloud Console](https://console.developers.google.com/)
2. Crie um projeto ou selecione existente
3. Ative a "YouTube Data API v3"
4. Crie credenciais (API Key)

**Twitter API:**
1. Acesse [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Crie um App
3. Gere um Bearer Token (Essential ou Elevated access)

**Google Search API:**
1. Acesse [Google Cloud Console](https://console.developers.google.com/)
2. Ative a "Custom Search API"
3. Crie credenciais (API Key)
4. Crie um [Custom Search Engine](https://programmablesearchengine.google.com/)
5. Configure para buscar em toda a web
6. Copie o Search Engine ID

## Uso

### Execução Única

```bash
# Usando configuração padrão (games)
python trend_monitor_agent.py

# Usando arquivo de configuração específico
python trend_monitor_agent.py --config config_games.json

# Especificando tópico diretamente
python trend_monitor_agent.py --topic tech
```

### Monitoramento Contínuo

```bash
# Executa a cada 6 horas (padrão)
python trend_monitor_scheduler.py --config config_games.json

# Intervalo customizado (em horas)
python trend_monitor_scheduler.py --config config_tech.json --interval 12

# Com tópico específico
python trend_monitor_scheduler.py --topic "inteligência artificial" --interval 3
```

## Configuração Customizada

### Estrutura do Arquivo de Configuração

```json
{
  "topic": "games",
  "language": "pt",
  "region": "BR",
  "youtube_queries": [
    "lançamento jogos",
    "gameplay",
    "esports"
  ],
  "twitter_queries": [
    "games",
    "esports",
    "streamer"
  ],
  "google_queries": [
    "lançamento jogos 2024",
    "evento esports"
  ],
  "youtube_max_results": 50,
  "youtube_days_ago": 7,
  "twitter_max_results": 100,
  "google_max_results": 10,
  "google_days_ago": 7,
  "output_dir": "trend_data/games",
  "enabled_sources": ["youtube", "twitter", "google"]
}
```

### Exemplos Incluídos

- **config_games.json** - Monitoramento do universo gaming
  - Lançamentos de jogos
  - Streamers
  - Campeonatos de esports
  - Conferências (Game Awards, etc)

- **config_tech.json** - Monitoramento de tecnologia
  - Lançamentos de produtos
  - Startups
  - Inteligência Artificial
  - Conferências tech

### Criar Configuração Customizada

```json
{
  "topic": "seu_topico",
  "language": "pt",
  "region": "BR",
  "youtube_queries": ["query1", "query2"],
  "twitter_queries": ["hashtag1", "hashtag2"],
  "google_queries": ["termo busca 1"],
  "youtube_max_results": 50,
  "youtube_days_ago": 7,
  "twitter_max_results": 100,
  "google_max_results": 10,
  "google_days_ago": 7,
  "output_dir": "trend_data/seu_topico",
  "enabled_sources": ["youtube", "twitter", "google"],
  "description": "Descrição do monitoramento"
}
```

## Output

### Estrutura de Diretórios

```
trend_data/
├── games/
│   ├── games_trends_20241204_143022.csv
│   ├── games_trends_20241204_203022.csv
│   └── ...
└── tech/
    ├── tech_trends_20241204_143022.csv
    └── ...
```

### Formato CSV

Cada linha representa um item coletado com campos:

| Campo | Descrição |
|-------|-----------|
| source | Plataforma de origem (youtube, twitter, google_search) |
| type | Tipo de conteúdo (video, tweet, article) |
| id | ID único na plataforma |
| url | Link direto para o conteúdo |
| title | Título ou resumo |
| description | Descrição completa |
| author | Nome do autor/canal |
| author_id | ID ou username do autor |
| author_url | Link do perfil do autor |
| published_at | Data de publicação (ISO 8601) |
| view_count | Número de visualizações |
| like_count | Número de likes/curtidas |
| comment_count | Número de comentários |
| share_count | Número de compartilhamentos |
| engagement_score | Score calculado de engajamento |
| duration_seconds | Duração (para vídeos) |
| tags | Tags separadas por \| |
| language | Código do idioma |
| category_id | ID da categoria |
| thumbnail | URL da thumbnail |
| topic | Tópico monitorado |
| collected_at | Timestamp da coleta |

## Casos de Uso

### 1. Monitoramento de Gaming

```bash
python trend_monitor_scheduler.py --config config_games.json --interval 6
```

**Coleta:**
- Lançamentos de jogos
- Vídeos de gameplay
- Reviews
- Principais streamers
- Torneios de esports
- Conferências (E3, Game Awards, etc)

### 2. Análise de Tendências Tech

```bash
python trend_monitor_scheduler.py --config config_tech.json --interval 12
```

**Coleta:**
- Lançamentos de produtos
- Startups em destaque
- Avanços em IA
- Conferências tech
- Artigos técnicos

### 3. Monitoramento de Marca

Crie `config_marca.json` com nome da sua marca:

```json
{
  "topic": "MinhaEmpresa",
  "youtube_queries": ["MinhaEmpresa", "MinhaEmpresa review"],
  "twitter_queries": ["@MinhaEmpresa", "#MinhaEmpresa"],
  "google_queries": ["MinhaEmpresa notícias"]
}
```

### 4. Análise de Concorrência

```json
{
  "topic": "concorrentes_setor",
  "youtube_queries": ["Empresa1", "Empresa2", "Empresa3"],
  "twitter_queries": ["@Empresa1", "@Empresa2", "@Empresa3"]
}
```

## Análise de Dados

### Usando Pandas

```python
import pandas as pd

# Carrega dataset
df = pd.read_csv('trend_data/games/games_trends_20241204_143022.csv')

# Top 10 por engajamento
top_engagement = df.nlargest(10, 'engagement_score')

# Análise por fonte
by_source = df.groupby('source').agg({
    'engagement_score': 'mean',
    'view_count': 'sum',
    'like_count': 'sum'
})

# Tendências ao longo do tempo
df['published_at'] = pd.to_datetime(df['published_at'])
daily_trends = df.groupby(df['published_at'].dt.date).size()
```

## Limitações das APIs

- **YouTube:** 10.000 unidades/dia (quota gratuita)
- **Twitter:**
  - Essential: 500.000 tweets/mês
  - Elevated: 2.000.000 tweets/mês
- **Google Search:** 100 consultas/dia (quota gratuita)

## Troubleshooting

### Erro: "Nenhum coletor disponível"

Verifique se pelo menos uma API está configurada no `.env`

### Erro 403 do YouTube

Quota da API excedida. Aguarde reset (meia-noite PST) ou solicite aumento de quota.

### Erro 429 do Twitter

Rate limit excedido. Aguarde ou reduza `twitter_max_results`.

### Google Search sem resultados

Verifique se o Custom Search Engine está configurado para buscar toda a web.

## Roadmap

- [ ] Suporte para Reddit API
- [ ] Suporte para TikTok
- [ ] Análise de sentimentos
- [ ] Detecção automática de trending topics
- [ ] Dashboard web para visualização
- [ ] Alertas em tempo real
- [ ] Exportação para outros formatos (JSON, Excel)
- [ ] Integração com bancos de dados

## Contribuindo

Contribuições são bem-vindas! Por favor, abra issues ou pull requests.

## Licença

MIT License
