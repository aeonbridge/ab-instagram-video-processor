# models/channel.py
class Channel:
    id: str                    # YouTube channel ID
    name: str
    niche: str                 # "games", "humor", "tech"
    subscriber_count: int
    avg_views_per_video: int
    monitoring_priority: int   # 1-10
    last_checked: datetime

class Video:
    id: str                    # YouTube video ID
    channel_id: str
    title: str
    views: int
    likes: int
    comments: int
    published_at: datetime
    duration_seconds: int
    viral_score: float         # Calculado
    status: str                # "new", "analyzed", "processed", "published"