# Publishers Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Video Clipper Service                            │
│  (ab/dc/downloaders/ - Creates clips from popular moments)              │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             │ clips_metadata.json
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Publisher Service (Main Entry)                      │
│  - Reads clip metadata                                                   │
│  - Validates platform requirements                                       │
│  - Orchestrates multi-platform uploads                                   │
└──────────┬──────────────────────┬──────────────────────┬────────────────┘
           │                      │                      │
           ▼                      ▼                      ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  OAuth Manager   │  │  Upload Queue    │  │  Rate Limiter    │
│                  │  │                  │  │                  │
│ - Token storage  │  │ - Priority queue │  │ - Quota tracking │
│ - Auto refresh   │  │ - Retry logic    │  │ - Throttling     │
│ - Multi-account  │  │ - Progress track │  │ - Per-platform   │
└──────────────────┘  └──────────────────┘  └──────────────────┘
           │
           ├─────────────────┬─────────────────┬─────────────────┐
           │                 │                 │                 │
           ▼                 ▼                 ▼                 ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐
│ TikTok Publisher │  │   YouTube    │  │  Instagram   │  │   Future    │
│                  │  │  Publisher   │  │  (Planned)   │  │  Platforms  │
└──────────────────┘  └──────────────┘  └──────────────┘  └─────────────┘
           │                 │
           │                 │
           ▼                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        Platform APIs                                      │
│  - TikTok Content Posting API                                            │
│  - YouTube Data API v3                                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

### 1. Upload Flow

```
User/CLI
    │
    │ 1. Request upload
    ▼
Publisher Service
    │
    │ 2. Validate video
    ▼
Video Validator
    │ ✓ Format/size/duration OK
    │
    │ 3. Check auth
    ▼
OAuth Manager
    │ ✓ Token valid/refreshed
    │
    │ 4. Check rate limits
    ▼
Rate Limiter
    │ ✓ Under quota
    │
    │ 5. Add to queue
    ▼
Upload Queue
    │
    │ 6. Process upload
    ▼
TikTok/YouTube Publisher
    │
    │ 7. Chunked upload
    ▼
Platform API
    │
    │ 8. Return video ID
    ▼
Publisher Service
    │
    │ 9. Return result
    ▼
User/CLI
```

### 2. OAuth Flow

```
User initiates auth
    │
    │ 1. Generate auth URL
    ▼
OAuth Manager
    │
    │ 2. Open browser
    ▼
Platform Login Page
    │
    │ 3. User authorizes
    ▼
Callback Server
    │
    │ 4. Exchange code for tokens
    ▼
OAuth Manager
    │
    │ 5. Store encrypted tokens
    ▼
Token Storage
```

### 3. Batch Upload Flow

```
Batch Upload Request
    │
    │ 1. Read metadata file
    ▼
Publisher Service
    │
    │ 2. Validate all videos
    ▼
Video Validator (parallel)
    │
    │ 3. Add to priority queue
    ▼
Upload Queue
    │
    │ 4. Process with concurrency=2
    ▼
Workers Pool
    ├─► TikTok Publisher ─► Upload ─► Success/Fail
    └─► YouTube Publisher ─► Upload ─► Success/Fail
```

## Class Hierarchy

```
BasePublisher (ABC)
    │
    ├─► TikTokPublisher
    │       │
    │       ├─► authenticate()
    │       ├─► validate_video()
    │       ├─► upload_video()
    │       │       ├─► _init_upload()
    │       │       ├─► _upload_chunks()
    │       │       └─► _check_status()
    │       ├─► get_upload_status()
    │       ├─► delete_video()
    │       └─► get_video_analytics()
    │
    └─► YouTubePublisher
            │
            ├─► authenticate()
            ├─► validate_video()
            ├─► upload_video()
            │       ├─► _init_resumable_upload()
            │       ├─► _upload_content()
            │       └─► _check_processing()
            ├─► set_thumbnail()
            ├─► get_upload_status()
            ├─► delete_video()
            └─► get_video_analytics()
```

## Data Flow

### Input: Clip Metadata JSON
```json
{
  "video_id": "RusBe_8arLQ",
  "clips": [
    {
      "clip_id": 0,
      "filename": "RusBe_8arLQ_0000_40s_score_156_9x16.mp4",
      "path": "processed_videos/RusBe_8arLQ/...",
      "duration": 40.0,
      "score": 1.56,
      "aspect_ratio": "9:16"
    }
  ]
}
```

### Publisher Configuration
```json
{
  "platforms": ["tiktok", "youtube"],
  "metadata": {
    "title_template": "Amazing moment from {video_id} #{clip_id}",
    "description_template": "Score: {score} #viral #fyp",
    "privacy": "public",
    "tags": ["gaming", "highlights", "viral"]
  },
  "upload_options": {
    "auto_retry": true,
    "max_retries": 3,
    "chunk_size": 10485760
  }
}
```

### Output: Upload Result
```json
{
  "success": true,
  "platform": "tiktok",
  "video_id": "7123456789012345678",
  "publish_id": "v_pub_7123456789",
  "status": "PUBLISHED",
  "upload_time_seconds": 45.2,
  "video_url": "https://www.tiktok.com/@user/video/7123456789012345678",
  "metadata": {
    "title": "Amazing moment from RusBe_8arLQ #0",
    "duration": 40.0,
    "file_size_mb": 16.0
  }
}
```

## Error Handling Strategy

```
Upload Request
    │
    ▼
Try Upload
    │
    ├─► Success ──────► Return result
    │
    └─► Error
          │
          ├─► INVALID_TOKEN
          │       └─► Refresh token ──► Retry
          │
          ├─► RATE_LIMIT_EXCEEDED
          │       └─► Wait + retry later
          │
          ├─► NETWORK_ERROR
          │       └─► Exponential backoff retry
          │
          ├─► VIDEO_TOO_LARGE
          │       └─► Return error (no retry)
          │
          └─► UNKNOWN_ERROR
                  └─► Log + retry (max 3 attempts)
```

## Threading Model

```
Main Thread
    │
    ├─► OAuth Callback Server (Thread)
    │       └─► Listen on localhost:8080
    │
    ├─► Upload Queue Processor (Thread)
    │       ├─► Worker 1 (Thread)
    │       │       └─► Upload video 1
    │       └─► Worker 2 (Thread)
    │               └─► Upload video 2
    │
    └─► Rate Limit Monitor (Thread)
            └─► Check quotas every 60s
```

## Storage Structure

```
~/.publisher_cache/
    │
    ├─── tokens/
    │       ├─── tiktok_tokens.enc
    │       └─── youtube_tokens.enc
    │
    ├─── queue/
    │       ├─── pending.json
    │       ├─── processing.json
    │       └─── completed.json
    │
    ├─── logs/
    │       ├─── uploads_2024-12-05.log
    │       └─── errors_2024-12-05.log
    │
    └─── analytics/
            ├─── tiktok_quota.json
            └─── youtube_quota.json
```

## API Rate Limits

### TikTok
```
Daily Limits:
- Video uploads: 10 per day (per user)
- API requests: 100 per minute

Quota Tracking:
uploads_today: 3/10
requests_per_minute: 45/100
next_reset: 2024-12-06 00:00:00 UTC
```

### YouTube
```
Daily Limits:
- Quota units: 10,000 per day
- Video upload cost: 1,600 units (~6 videos/day)

Quota Tracking:
units_used: 3200/10000
uploads_today: 2/6
next_reset: 2024-12-06 00:00:00 PST
```

## Security Layers

```
1. Transport Layer
    └─► HTTPS/TLS 1.3 for all API calls

2. Authentication Layer
    └─► OAuth 2.0 with encrypted token storage

3. Application Layer
    ├─► Input validation
    ├─► File sanitization
    └─► Access control

4. Storage Layer
    ├─► Encrypted credentials (AES-256)
    └─► Restricted file permissions (600)

5. Logging Layer
    └─► No sensitive data in logs
```

## Monitoring & Observability

```
Metrics Tracked:
- Upload success rate
- Average upload time
- API error rates
- Token refresh failures
- Queue depth
- Concurrent uploads

Alerts:
- Upload failure > 10%
- Token refresh failure
- Rate limit approaching (80%)
- Queue backlog > 50 items
- Disk space low
```