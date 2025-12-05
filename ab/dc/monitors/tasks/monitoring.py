# tasks/monitoring.py
import celery


@celery.task

import ab.dc.models.channel

def scan_channels_for_niche(niche: str):
    """Executa a cada 2 horas"""
    channels = Channel.query.filter_by(niche=niche, active=True).all()

    for channel in channels:
        recent_videos = youtube_api.get_recent_videos(
            channel_id=channel.id,
            max_results=10,
            published_after=datetime.now() - timedelta(days=3)
        )

        for video_data in recent_videos:
            video = Video.from_api_response(video_data)
            video.viral_score = calculate_viral_score(video, channel.avg_views)

            if video.viral_score >= VIRAL_THRESHOLD:
                queue_for_download.delay(video.id)