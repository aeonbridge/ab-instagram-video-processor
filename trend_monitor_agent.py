#!/usr/bin/env python3
"""
Agente Agnóstico de Monitoramento de Trends
Monitora tendências de um assunto específico usando múltiplas fontes de dados.

Fontes suportadas:
- YouTube (vídeos, canais, trending)
- Twitter/X (tweets, hashtags, trending topics)
- Google Search (notícias, artigos, eventos)
- Reddit (posts, subreddits)

Requer:
    pip install google-api-python-client isodate python-dotenv tweepy requests
"""

import os
import sys
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import isodate
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import requests


class TrendDataCollector:
    """Classe base para coletores de dados de tendências."""

    def __init__(self, topic: str, config: Dict[str, Any]):
        """
        Inicializa o coletor.

        Args:
            topic: Tópico a ser monitorado (ex: "games", "tech", "sports")
            config: Configuração específica do tópico
        """
        self.topic = topic
        self.config = config
        self.results = []

    def collect(self) -> List[Dict]:
        """Coleta dados. Deve ser implementado pelas subclasses."""
        raise NotImplementedError

    def normalize_data(self, raw_data: Any) -> Dict:
        """Normaliza dados para formato padrão."""
        raise NotImplementedError


class YouTubeCollector(TrendDataCollector):
    """Coletor de dados do YouTube."""

    def __init__(self, topic: str, config: Dict[str, Any], api_key: str):
        super().__init__(topic, config)
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def collect(self) -> List[Dict]:
        """Coleta vídeos trending do YouTube."""
        results = []

        try:
            # Busca vídeos recentes sobre o tópico
            search_queries = self.config.get('youtube_queries', [self.topic])

            for query in search_queries:
                print(f"  Buscando vídeos do YouTube: '{query}'...")

                # Data de publicação (últimos N dias)
                days_ago = self.config.get('youtube_days_ago', 7)
                published_after = (datetime.utcnow() - timedelta(days=days_ago)).isoformat("T") + "Z"

                search_response = self.youtube.search().list(
                    q=query,
                    type='video',
                    part='id',
                    maxResults=self.config.get('youtube_max_results', 25),
                    order='viewCount',
                    publishedAfter=published_after,
                    relevanceLanguage=self.config.get('language', 'pt'),
                    regionCode=self.config.get('region', 'BR')
                ).execute()

                video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

                if not video_ids:
                    continue

                # Obtém detalhes dos vídeos
                videos_response = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(video_ids)
                ).execute()

                for item in videos_response.get('items', []):
                    try:
                        results.append(self.normalize_data(item))
                    except Exception as e:
                        print(f"    Erro ao processar vídeo: {e}")
                        continue

        except HttpError as e:
            print(f"  Erro na API do YouTube: {e}")

        return results

    def normalize_data(self, raw_data: Any) -> Dict:
        """Normaliza dados do YouTube para formato padrão."""
        snippet = raw_data['snippet']
        statistics = raw_data['statistics']
        content_details = raw_data['contentDetails']

        duration = isodate.parse_duration(content_details['duration'])
        duration_seconds = duration.total_seconds()

        return {
            'source': 'youtube',
            'type': 'video',
            'id': raw_data['id'],
            'url': f"https://www.youtube.com/watch?v={raw_data['id']}",
            'title': snippet['title'],
            'description': snippet.get('description', ''),
            'author': snippet['channelTitle'],
            'author_id': snippet['channelId'],
            'author_url': f"https://www.youtube.com/channel/{snippet['channelId']}",
            'published_at': snippet['publishedAt'],
            'view_count': int(statistics.get('viewCount', 0)),
            'like_count': int(statistics.get('likeCount', 0)),
            'comment_count': int(statistics.get('commentCount', 0)),
            'share_count': 0,
            'engagement_score': int(statistics.get('likeCount', 0)) + int(statistics.get('commentCount', 0)),
            'duration_seconds': int(duration_seconds),
            'tags': '|'.join(snippet.get('tags', [])),
            'language': snippet.get('defaultLanguage', ''),
            'category_id': snippet.get('categoryId', ''),
            'thumbnail': snippet['thumbnails'].get('high', {}).get('url', ''),
            'topic': self.topic,
            'collected_at': datetime.utcnow().isoformat() + 'Z'
        }


class TwitterCollector(TrendDataCollector):
    """Coletor de dados do Twitter/X."""

    def __init__(self, topic: str, config: Dict[str, Any], bearer_token: Optional[str] = None):
        super().__init__(topic, config)
        self.bearer_token = bearer_token
        self.base_url = "https://api.twitter.com/2"

    def collect(self) -> List[Dict]:
        """Coleta tweets trending sobre o tópico."""
        results = []

        if not self.bearer_token:
            print("  Twitter API não configurada. Pulando...")
            return results

        try:
            # Busca tweets recentes
            queries = self.config.get('twitter_queries', [self.topic])

            for query in queries:
                print(f"  Buscando tweets: '{query}'...")

                # Monta query com filtros
                search_query = f"{query} -is:retweet lang:{self.config.get('language', 'pt')}"

                # Parâmetros da busca
                params = {
                    'query': search_query,
                    'max_results': min(self.config.get('twitter_max_results', 100), 100),
                    'tweet.fields': 'created_at,public_metrics,lang,entities,context_annotations',
                    'expansions': 'author_id',
                    'user.fields': 'username,name,verified,public_metrics'
                }

                headers = {
                    'Authorization': f'Bearer {self.bearer_token}'
                }

                response = requests.get(
                    f"{self.base_url}/tweets/search/recent",
                    params=params,
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    tweets = data.get('data', [])
                    users = {user['id']: user for user in data.get('includes', {}).get('users', [])}

                    for tweet in tweets:
                        try:
                            results.append(self.normalize_data({'tweet': tweet, 'users': users}))
                        except Exception as e:
                            print(f"    Erro ao processar tweet: {e}")
                            continue
                else:
                    print(f"    Erro na API do Twitter: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"  Erro ao coletar do Twitter: {e}")

        return results

    def normalize_data(self, raw_data: Any) -> Dict:
        """Normaliza dados do Twitter para formato padrão."""
        tweet = raw_data['tweet']
        users = raw_data['users']
        author = users.get(tweet['author_id'], {})

        metrics = tweet.get('public_metrics', {})
        author_metrics = author.get('public_metrics', {})

        return {
            'source': 'twitter',
            'type': 'tweet',
            'id': tweet['id'],
            'url': f"https://twitter.com/{author.get('username', 'i')}/status/{tweet['id']}",
            'title': tweet['text'][:100] + '...' if len(tweet['text']) > 100 else tweet['text'],
            'description': tweet['text'],
            'author': author.get('name', ''),
            'author_id': author.get('username', ''),
            'author_url': f"https://twitter.com/{author.get('username', '')}",
            'published_at': tweet['created_at'],
            'view_count': metrics.get('impression_count', 0),
            'like_count': metrics.get('like_count', 0),
            'comment_count': metrics.get('reply_count', 0),
            'share_count': metrics.get('retweet_count', 0) + metrics.get('quote_count', 0),
            'engagement_score': metrics.get('like_count', 0) + metrics.get('reply_count', 0) +
                              metrics.get('retweet_count', 0) + metrics.get('quote_count', 0),
            'duration_seconds': 0,
            'tags': '',
            'language': tweet.get('lang', ''),
            'category_id': '',
            'thumbnail': '',
            'author_followers': author_metrics.get('followers_count', 0),
            'author_verified': author.get('verified', False),
            'topic': self.topic,
            'collected_at': datetime.utcnow().isoformat() + 'Z'
        }


class GoogleSearchCollector(TrendDataCollector):
    """Coletor de dados do Google Search (notícias e artigos)."""

    def __init__(self, topic: str, config: Dict[str, Any], api_key: str, search_engine_id: str):
        super().__init__(topic, config)
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def collect(self) -> List[Dict]:
        """Coleta resultados de busca sobre o tópico."""
        results = []

        if not self.api_key or not self.search_engine_id:
            print("  Google Search API não configurada. Pulando...")
            return results

        try:
            queries = self.config.get('google_queries', [self.topic])

            for query in queries:
                print(f"  Buscando no Google: '{query}'...")

                # Parâmetros da busca
                params = {
                    'key': self.api_key,
                    'cx': self.search_engine_id,
                    'q': query,
                    'num': min(self.config.get('google_max_results', 10), 10),
                    'dateRestrict': f"d{self.config.get('google_days_ago', 7)}",
                    'sort': 'date'
                }

                response = requests.get(self.base_url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])

                    for item in items:
                        try:
                            results.append(self.normalize_data(item))
                        except Exception as e:
                            print(f"    Erro ao processar resultado: {e}")
                            continue
                else:
                    print(f"    Erro na API do Google: {response.status_code}")

        except Exception as e:
            print(f"  Erro ao coletar do Google: {e}")

        return results

    def normalize_data(self, raw_data: Any) -> Dict:
        """Normaliza dados do Google Search para formato padrão."""
        return {
            'source': 'google_search',
            'type': 'article',
            'id': raw_data.get('cacheId', ''),
            'url': raw_data['link'],
            'title': raw_data['title'],
            'description': raw_data.get('snippet', ''),
            'author': raw_data.get('displayLink', ''),
            'author_id': '',
            'author_url': raw_data.get('displayLink', ''),
            'published_at': '',
            'view_count': 0,
            'like_count': 0,
            'comment_count': 0,
            'share_count': 0,
            'engagement_score': 0,
            'duration_seconds': 0,
            'tags': '',
            'language': '',
            'category_id': '',
            'thumbnail': raw_data.get('pagemap', {}).get('cse_image', [{}])[0].get('src', ''),
            'topic': self.topic,
            'collected_at': datetime.utcnow().isoformat() + 'Z'
        }


class TrendMonitorAgent:
    """Agente principal de monitoramento de tendências."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa o agente.

        Args:
            config_file: Caminho para arquivo de configuração JSON
        """
        load_dotenv()

        # Carrega configuração
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = self._default_config()

        # APIs
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

        self.collectors = []

    def _default_config(self) -> Dict:
        """Retorna configuração padrão para tópico de games."""
        return {
            'topic': 'games',
            'language': 'pt',
            'region': 'BR',
            'youtube_queries': [
                'lançamento jogos',
                'gameplay',
                'game review',
                'esports',
                'game conference'
            ],
            'twitter_queries': [
                'games',
                'esports',
                'gaming',
                'streamer',
                'game release'
            ],
            'google_queries': [
                'lançamento jogos 2024',
                'conferência games',
                'evento esports',
                'novo jogo'
            ],
            'youtube_max_results': 50,
            'youtube_days_ago': 7,
            'twitter_max_results': 100,
            'google_max_results': 10,
            'google_days_ago': 7,
            'output_dir': 'trend_data',
            'enabled_sources': ['youtube', 'twitter', 'google']
        }

    def initialize_collectors(self):
        """Inicializa os coletores habilitados."""
        topic = self.config['topic']
        enabled = self.config.get('enabled_sources', [])

        if 'youtube' in enabled and self.youtube_api_key:
            print("Inicializando coletor do YouTube...")
            self.collectors.append(YouTubeCollector(topic, self.config, self.youtube_api_key))

        if 'twitter' in enabled and self.twitter_bearer_token:
            print("Inicializando coletor do Twitter...")
            self.collectors.append(TwitterCollector(topic, self.config, self.twitter_bearer_token))

        if 'google' in enabled and self.google_api_key and self.google_search_engine_id:
            print("Inicializando coletor do Google Search...")
            self.collectors.append(GoogleSearchCollector(
                topic, self.config, self.google_api_key, self.google_search_engine_id
            ))

        if not self.collectors:
            print("AVISO: Nenhum coletor foi inicializado. Verifique as chaves de API no .env")

    def collect_all(self) -> List[Dict]:
        """Coleta dados de todas as fontes."""
        all_data = []

        print(f"\nColetando dados sobre '{self.config['topic']}'...\n")

        for collector in self.collectors:
            print(f"Coletando de {collector.__class__.__name__}...")
            try:
                data = collector.collect()
                all_data.extend(data)
                print(f"  Coletados: {len(data)} itens")
            except Exception as e:
                print(f"  Erro: {e}")

        print(f"\nTotal coletado: {len(all_data)} itens")
        return all_data

    def save_to_csv(self, data: List[Dict], filename: Optional[str] = None):
        """Salva dados em CSV."""
        if not data:
            print("Nenhum dado para salvar.")
            return

        # Cria diretório de saída
        output_dir = self.config.get('output_dir', 'trend_data')
        os.makedirs(output_dir, exist_ok=True)

        # Nome do arquivo
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.config['topic']}_trends_{timestamp}.csv"

        filepath = os.path.join(output_dir, filename)

        # Salva CSV
        fieldnames = list(data[0].keys())

        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(data)

        print(f"\nDataset salvo: {filepath}")
        print(f"Total de colunas: {len(fieldnames)}")
        print(f"Total de linhas: {len(data)}")

        return filepath

    def generate_report(self, data: List[Dict]):
        """Gera relatório resumido dos dados coletados."""
        if not data:
            return

        # Agrupa por fonte
        by_source = {}
        for item in data:
            source = item['source']
            by_source[source] = by_source.get(source, 0) + 1

        # Top itens por engajamento
        top_engagement = sorted(data, key=lambda x: x['engagement_score'], reverse=True)[:10]

        print("\n" + "="*80)
        print(f"RELATÓRIO DE TENDÊNCIAS - {self.config['topic'].upper()}")
        print("="*80)

        print("\nDistribuição por fonte:")
        for source, count in by_source.items():
            print(f"  {source}: {count} itens")

        print("\nTop 10 por engajamento:")
        for i, item in enumerate(top_engagement, 1):
            print(f"\n{i}. [{item['source'].upper()}] {item['title'][:70]}")
            print(f"   Autor: {item['author']}")
            print(f"   URL: {item['url']}")
            print(f"   Engajamento: {item['engagement_score']:,} | Visualizações: {item['view_count']:,}")

    def run(self):
        """Executa o monitoramento completo."""
        print("="*80)
        print("AGENTE DE MONITORAMENTO DE TENDÊNCIAS")
        print("="*80)

        self.initialize_collectors()

        if not self.collectors:
            print("\nNenhum coletor disponível. Configure as APIs no arquivo .env:")
            print("  - YOUTUBE_API_KEY")
            print("  - TWITTER_BEARER_TOKEN")
            print("  - GOOGLE_API_KEY")
            print("  - GOOGLE_SEARCH_ENGINE_ID")
            return

        # Coleta dados
        data = self.collect_all()

        if data:
            # Salva CSV
            self.save_to_csv(data)

            # Gera relatório
            self.generate_report(data)

        print("\n" + "="*80)
        print("Monitoramento concluído!")
        print("="*80)


def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(description='Agente de Monitoramento de Tendências')
    parser.add_argument('--config', type=str, help='Arquivo de configuração JSON')
    parser.add_argument('--topic', type=str, help='Tópico a monitorar (ex: games, tech)')

    args = parser.parse_args()

    # Inicializa agente
    agent = TrendMonitorAgent(config_file=args.config)

    # Sobrescreve tópico se fornecido
    if args.topic:
        agent.config['topic'] = args.topic

    # Executa
    agent.run()


if __name__ == '__main__':
    main()
