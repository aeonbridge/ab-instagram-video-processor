#!/usr/bin/env python3
"""
YouTube Video Search Script
Busca vídeos do YouTube com filtros parametrizáveis usando a API do YouTube Data v3.

Requer:
    pip install google-api-python-client isodate python-dotenv
"""

import os
import sys
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import isodate
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv


class YouTubeVideoSearch:
    """Classe para buscar vídeos no YouTube com filtros avançados."""

    def __init__(self, api_key: str):
        """
        Inicializa o cliente da API do YouTube.

        Args:
            api_key: Chave da API do YouTube Data v3
        """
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def search_videos(
        self,
        query: str,
        language: str = 'pt',
        region_code: str = 'BR',
        min_duration_hours: float = 0,
        min_views: int = 0,
        days_ago: int = 365,
        order: str = 'rating',
        max_results: int = 50
    ) -> List[Dict]:
        """
        Busca vídeos com filtros específicos.

        Args:
            query: Termo de busca (ex: "jogos", "games", etc.)
            language: Código do idioma (ex: 'pt', 'en')
            region_code: Código da região (ex: 'BR', 'US')
            min_duration_hours: Duração mínima em horas
            min_views: Número mínimo de visualizações
            days_ago: Buscar vídeos publicados nos últimos N dias
            order: Ordenação ('rating', 'viewCount', 'date', 'relevance')
            max_results: Número máximo de resultados

        Returns:
            Lista de dicionários com informações dos vídeos
        """
        try:
            # Calcula data de publicação
            published_after = (datetime.utcnow() - timedelta(days=days_ago)).isoformat("T") + "Z"

            # Primeira busca: obtém IDs dos vídeos
            print(f"Buscando vídeos sobre '{query}'...")
            print(f"Filtros: idioma={language}, região={region_code}, últimos {days_ago} dias")

            search_response = self.youtube.search().list(
                q=query,
                type='video',
                part='id',
                maxResults=max_results,
                order=order,
                publishedAfter=published_after,
                relevanceLanguage=language,
                regionCode=region_code,
                videoDefinition='high',  # Apenas vídeos HD
                videoDuration='long'  # Vídeos > 20 minutos (filtro inicial)
            ).execute()

            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

            if not video_ids:
                print("Nenhum vídeo encontrado com os critérios iniciais.")
                return []

            print(f"Encontrados {len(video_ids)} vídeos. Obtendo detalhes...")

            # Segunda busca: obtém detalhes completos dos vídeos
            videos_response = self.youtube.videos().list(
                part='snippet,contentDetails,statistics,status,topicDetails',
                id=','.join(video_ids)
            ).execute()

            # Obtém IDs dos canais para buscar informações completas
            channel_ids = list(set([item['snippet']['channelId'] for item in videos_response.get('items', [])]))

            # Busca informações dos canais
            channels_info = {}
            if channel_ids:
                channels_response = self.youtube.channels().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(channel_ids)
                ).execute()

                for channel in channels_response.get('items', []):
                    channels_info[channel['id']] = {
                        'channel_url': f"https://www.youtube.com/channel/{channel['id']}",
                        'channel_custom_url': channel['snippet'].get('customUrl', ''),
                        'channel_description': channel['snippet'].get('description', ''),
                        'channel_subscriber_count': int(channel['statistics'].get('subscriberCount', 0)),
                        'channel_video_count': int(channel['statistics'].get('videoCount', 0)),
                        'channel_view_count': int(channel['statistics'].get('viewCount', 0)),
                        'channel_published_at': channel['snippet'].get('publishedAt', ''),
                        'channel_country': channel['snippet'].get('country', ''),
                    }

            # Filtra vídeos pelos critérios
            filtered_videos = []
            min_duration_seconds = min_duration_hours * 3600

            for item in videos_response.get('items', []):
                try:
                    # Extrai informações básicas
                    duration = isodate.parse_duration(item['contentDetails']['duration'])
                    duration_seconds = duration.total_seconds()
                    view_count = int(item['statistics'].get('viewCount', 0))
                    like_count = int(item['statistics'].get('likeCount', 0))
                    dislike_count = int(item['statistics'].get('dislikeCount', 0))  # Geralmente não disponível
                    comment_count = int(item['statistics'].get('commentCount', 0))
                    favorite_count = int(item['statistics'].get('favoriteCount', 0))

                    # Informações do snippet
                    snippet = item['snippet']
                    channel_id = snippet['channelId']

                    # Informações de conteúdo
                    content_details = item['contentDetails']

                    # Status
                    status = item.get('status', {})

                    # Topic details (categorias)
                    topic_details = item.get('topicDetails', {})
                    topic_categories = topic_details.get('topicCategories', [])

                    # Tags
                    tags = snippet.get('tags', [])
                    tags_str = '|'.join(tags) if tags else ''

                    # Thumbnails
                    thumbnails = snippet.get('thumbnails', {})

                    # Categoria
                    category_id = snippet.get('categoryId', '')

                    # Informações do canal
                    channel_info = channels_info.get(channel_id, {})

                    # Aplica filtros
                    if duration_seconds >= min_duration_seconds and view_count >= min_views:
                        video_info = {
                            # Identificação
                            'video_id': item['id'],
                            'video_url': f"https://www.youtube.com/watch?v={item['id']}",

                            # Informações básicas do vídeo
                            'title': snippet['title'],
                            'description': snippet.get('description', ''),
                            'published_at': snippet['publishedAt'],
                            'published_date': snippet['publishedAt'][:10],
                            'published_time': snippet['publishedAt'][11:19],

                            # Duração
                            'duration_iso': str(duration),
                            'duration_seconds': int(duration_seconds),
                            'duration_minutes': round(duration_seconds / 60, 2),
                            'duration_hours': round(duration_seconds / 3600, 2),

                            # Estatísticas
                            'view_count': view_count,
                            'like_count': like_count,
                            'dislike_count': dislike_count,
                            'comment_count': comment_count,
                            'favorite_count': favorite_count,

                            # Métricas calculadas
                            'engagement_rate': round((like_count + comment_count) / view_count * 100, 4) if view_count > 0 else 0,
                            'like_rate': round(like_count / view_count * 100, 4) if view_count > 0 else 0,
                            'comment_rate': round(comment_count / view_count * 100, 4) if view_count > 0 else 0,

                            # Informações do canal
                            'channel_id': channel_id,
                            'channel_title': snippet['channelTitle'],
                            'channel_url': channel_info.get('channel_url', f"https://www.youtube.com/channel/{channel_id}"),
                            'channel_custom_url': channel_info.get('channel_custom_url', ''),
                            'channel_description': channel_info.get('channel_description', ''),
                            'channel_subscriber_count': channel_info.get('channel_subscriber_count', 0),
                            'channel_video_count': channel_info.get('channel_video_count', 0),
                            'channel_view_count': channel_info.get('channel_view_count', 0),
                            'channel_published_at': channel_info.get('channel_published_at', ''),
                            'channel_country': channel_info.get('channel_country', ''),

                            # Categoria e tags
                            'category_id': category_id,
                            'tags': tags_str,
                            'tags_count': len(tags),
                            'topic_categories': '|'.join(topic_categories) if topic_categories else '',

                            # Conteúdo
                            'definition': content_details.get('definition', ''),
                            'caption': content_details.get('caption', ''),
                            'licensed_content': content_details.get('licensedContent', False),
                            'content_rating': str(content_details.get('contentRating', {})),

                            # Status
                            'upload_status': status.get('uploadStatus', ''),
                            'privacy_status': status.get('privacyStatus', ''),
                            'license': status.get('license', ''),
                            'embeddable': status.get('embeddable', True),
                            'public_stats_viewable': status.get('publicStatsViewable', True),
                            'made_for_kids': status.get('madeForKids', False),

                            # Thumbnails
                            'thumbnail_default': thumbnails.get('default', {}).get('url', ''),
                            'thumbnail_medium': thumbnails.get('medium', {}).get('url', ''),
                            'thumbnail_high': thumbnails.get('high', {}).get('url', ''),
                            'thumbnail_standard': thumbnails.get('standard', {}).get('url', ''),
                            'thumbnail_maxres': thumbnails.get('maxres', {}).get('url', ''),

                            # Localização
                            'default_language': snippet.get('defaultLanguage', ''),
                            'default_audio_language': snippet.get('defaultAudioLanguage', ''),

                            # Metadados de busca
                            'search_query': query,
                            'search_language': language,
                            'search_region': region_code,
                            'retrieved_at': datetime.utcnow().isoformat() + 'Z'
                        }
                        filtered_videos.append(video_info)

                except (KeyError, ValueError) as e:
                    print(f"Erro ao processar vídeo: {e}")
                    continue

            # Ordena por visualizações (decrescente)
            filtered_videos.sort(key=lambda x: x['view_count'], reverse=True)

            print(f"\nEncontrados {len(filtered_videos)} vídeos após filtragem.")
            return filtered_videos

        except HttpError as e:
            print(f"Erro na API do YouTube: {e}")
            return []
        except Exception as e:
            print(f"Erro inesperado: {e}")
            return []

    def print_results(self, videos: List[Dict]):
        """Imprime os resultados da busca de forma formatada."""
        if not videos:
            print("\nNenhum vídeo encontrado.")
            return

        print("\n" + "="*100)
        print(f"RESULTADOS DA BUSCA - {len(videos)} vídeos encontrados")
        print("="*100)

        for i, video in enumerate(videos, 1):
            print(f"\n{i}. {video['title']}")
            print(f"   Canal: {video['channel_title']} ({video['channel_subscriber_count']:,} inscritos)")
            print(f"   URL: {video['video_url']}")
            print(f"   Canal URL: {video['channel_url']}")
            print(f"   Duração: {video['duration_iso']} ({video['duration_hours']:.2f} horas)")
            print(f"   Visualizações: {video['view_count']:,}")
            print(f"   Likes: {video['like_count']:,} ({video['like_rate']:.2f}%)")
            print(f"   Comentários: {video['comment_count']:,} ({video['comment_rate']:.2f}%)")
            print(f"   Engajamento: {video['engagement_rate']:.2f}%")
            print(f"   Publicado em: {video['published_date']}")
            print(f"   Tags: {video['tags_count']}")

    def save_results_to_csv(self, videos: List[Dict], filename: str = 'youtube_search_results.csv'):
        """Salva os resultados em um arquivo CSV com todas as informações."""
        if not videos:
            print("Nenhum resultado para salvar.")
            return

        # Define as colunas do CSV (todas as chaves do primeiro vídeo)
        if videos:
            fieldnames = list(videos[0].keys())

            with open(filename, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(videos)

            print(f"\nDataset salvo em CSV: {filename}")
            print(f"Total de colunas: {len(fieldnames)}")
            print(f"Total de linhas: {len(videos)}")

    def save_results_to_file(self, videos: List[Dict], filename: str = 'youtube_search_results.txt'):
        """Salva os resultados em um arquivo de texto (formato legível)."""
        if not videos:
            print("Nenhum resultado para salvar.")
            return

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"RESULTADOS DA BUSCA DO YOUTUBE - {len(videos)} vídeos\n")
            f.write(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*100 + "\n\n")

            for i, video in enumerate(videos, 1):
                f.write(f"{i}. {video['title']}\n")
                f.write(f"   Canal: {video['channel_title']}\n")
                f.write(f"   URL: {video['video_url']}\n")
                f.write(f"   Canal URL: {video['channel_url']}\n")
                f.write(f"   Duração: {video['duration_iso']} ({video['duration_hours']:.2f} horas)\n")
                f.write(f"   Visualizações: {video['view_count']:,}\n")
                f.write(f"   Likes: {video['like_count']:,}\n")
                f.write(f"   Comentários: {video['comment_count']:,}\n")
                f.write(f"   Taxa de Engajamento: {video['engagement_rate']:.4f}%\n")
                f.write(f"   Inscritos do Canal: {video['channel_subscriber_count']:,}\n")
                f.write(f"   Publicado em: {video['published_date']}\n")
                f.write(f"   Tags: {video['tags_count']} tags\n\n")

        print(f"\nResumo legível salvo em: {filename}")


def main():
    """Função principal - exemplo de uso com os parâmetros especificados."""

    # Carrega variáveis do arquivo .env
    load_dotenv()

    # Obter API Key do arquivo .env, ambiente ou argumento
    api_key = os.getenv('YOUTUBE_API_KEY')

    if not api_key:
        print("ATENÇÃO: Nenhuma chave de API encontrada!")
        print("\nPara usar este script, você precisa:")
        print("1. Obter uma chave de API do YouTube Data v3 em:")
        print("   https://console.developers.google.com/")
        print("2. Criar um arquivo .env na raiz do projeto com:")
        print("   YOUTUBE_API_KEY=sua_chave_aqui")
        print("3. OU definir a variável de ambiente YOUTUBE_API_KEY")
        print("4. OU passar a chave como argumento:\n")
        print("   python youtube_video_search.py YOUR_API_KEY\n")

        if len(sys.argv) > 1:
            api_key = sys.argv[1]
        else:
            api_key = input("Cole sua chave de API aqui (ou Enter para sair): ").strip()
            if not api_key:
                sys.exit(1)

    # Inicializa o buscador
    searcher = YouTubeVideoSearch(api_key)

    # TESTE COM OS PARÂMETROS ESPECIFICADOS:
    # - Assunto: jogos
    # - Idioma: português (Brasil)
    # - Duração: acima de 2 horas
    # - Rating: alto (ordenação por rating)
    # - Visualizações: pelo menos 1M
    # - Período: últimos 120 dias

    print("\n" + "="*100)
    print("BUSCA DE VÍDEOS DO YOUTUBE - TESTE")
    print("="*100)
    print("\nParâmetros de busca:")
    print("  - Assunto: jogos")
    print("  - Idioma: Português (Brasil)")
    print("  - Duração mínima: 2 horas")
    print("  - Visualizações mínimas: 1.000.000")
    print("  - Período: Últimos 120 dias")
    print("  - Ordenação: Por rating (melhor avaliados)")
    print("\n")

    videos = searcher.search_videos(
        query='jogos',
        language='pt',
        region_code='BR',
        min_duration_hours=2.0,
        min_views=1_000_000,
        days_ago=120,
        order='rating',
        max_results=50
    )

    # Exibe e salva resultados
    searcher.print_results(videos)

    if videos:
        # Salva em CSV (dataset completo)
        searcher.save_results_to_csv(videos, 'youtube_jogos_dataset.csv')

        # Salva em TXT (resumo legível)
        searcher.save_results_to_file(videos, 'youtube_jogos_results.txt')

        print(f"\n\nTotal de vídeos que atendem aos critérios: {len(videos)}")
        print("\nArquivos gerados:")
        print("  - youtube_jogos_dataset.csv (dataset completo para análise)")
        print("  - youtube_jogos_results.txt (resumo legível)")


if __name__ == '__main__':
    main()
