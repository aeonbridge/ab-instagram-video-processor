def calculate_viral_score(video, channel_avg_views):
    """
    Score de 0-100 baseado em múltiplos fatores
    """
    # Fator 1: Performance vs média do canal
    view_ratio = video.views / max(channel_avg_views, 1)

    # Fator 2: Engajamento (likes + comments / views)
    engagement_rate = (video.likes + video.comments * 2) / max(video.views, 1)

    # Fator 3: Velocidade de crescimento (views por hora desde publicação)
    hours_since_publish = (datetime.now() - video.published_at).total_seconds() / 3600
    velocity = video.views / max(hours_since_publish, 1)

    # Fator 4: Recência (vídeos mais novos = mais relevantes)
    recency_bonus = max(0, 30 - hours_since_publish) / 30

    # Ponderação final
    score = (
            view_ratio * 30 +
            engagement_rate * 1000 * 25 +
            min(velocity / 1000, 1) * 25 +
            recency_bonus * 20
    )

    return min(score, 100)