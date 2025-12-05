# Social Media Publishers

Automated video publishing system for TikTok and YouTube with support for batch uploads, scheduling, and multi-platform distribution.

## 🚀 Features

- ✅ **Multi-Platform Support**: TikTok, YouTube (Instagram Reels planned)
- ✅ **OAuth 2.0 Authentication**: Secure token management with auto-refresh
- ✅ **Batch Uploads**: Process multiple videos concurrently
- ✅ **Chunked Uploads**: Resume support for large files
- ✅ **Rate Limiting**: Automatic quota tracking and throttling
- ✅ **Retry Logic**: Exponential backoff for failed uploads
- ✅ **Video Validation**: Format, codec, size, and duration checks
- ✅ **Metadata Templates**: Auto-generate titles and descriptions
- ✅ **Scheduled Uploads**: Queue videos for future publishing
- ✅ **Analytics**: Track upload performance and video metrics
- ✅ **CLI Interface**: Easy command-line usage
- ✅ **Python API**: Programmatic access for integrations

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Platform Setup](#-platform-setup)
- [Usage Examples](#-usage-examples)
- [API Reference](#-api-reference)
- [Integration](#-integration)
- [Documentation](#-documentation)
- [Troubleshooting](#-troubleshooting)

## ⚡ Quick Start

```bash
# 1. Set up credentials
cp .env.example .env
# Edit .env with your API keys

# 2. Authorize platforms
python3 cli_publisher.py --authorize tiktok
python3 cli_publisher.py --authorize youtube

# 3. Upload video
python3 cli_publisher.py \
  --platform tiktok \
  --video video.mp4 \
  --title "Amazing video!" \
  --description "#viral #fyp"
```

**Full example in 30 seconds**: See [QUICK_START.md](QUICK_START.md)

## 📦 Installation

### Dependencies

```bash
pip install requests oauthlib google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Optional Dependencies

```bash
# For video validation
pip install ffmpeg-python

# For progress bars
pip install tqdm

# For scheduled uploads
pip install schedule
```

## 🔑 Platform Setup

### TikTok

1. Create app at https://developers.tiktok.com/
2. Request `video.upload` and `video.publish` scopes
3. Add redirect URI: `http://localhost:8080/callback`
4. Copy Client Key and Client Secret to `.env`

**Detailed guide**: [QUICK_START.md#tiktok-developer-account-setup](QUICK_START.md#1-tiktok-developer-account-setup)

### YouTube

1. Create project at https://console.cloud.google.com/
2. Enable YouTube Data API v3
3. Create OAuth 2.0 Desktop credentials
4. Download credentials JSON
5. Copy Client ID and Secret to `.env`

**Detailed guide**: [QUICK_START.md#youtube-google-cloud-setup](QUICK_START.md#2-youtubegoogle-cloud-setup)

## 💡 Usage Examples

### Single Video Upload

```bash
# TikTok
python3 cli_publisher.py \
  --platform tiktok \
  --video clip.mp4 \
  --title "Epic moment! 🔥" \
  --description "Check this out #fyp #viral"

# YouTube
python3 cli_publisher.py \
  --platform youtube \
  --video clip.mp4 \
  --title "Amazing Video #Shorts" \
  --description "Full description" \
  --category 22 \
  --tags "gaming,viral,shorts"
```

### Batch Upload

```bash
python3 cli_publisher.py \
  --platform tiktok \
  --batch-dir processed_videos/RusBe_8arLQ/ \
  --metadata-file metadata.json \
  --auto-title
```

### Cross-Platform

```bash
python3 cli_publisher.py \
  --platforms tiktok,youtube \
  --video clip.mp4 \
  --title "My Video" \
  --config cross_platform.json
```

### Complete Workflow

```bash
# Extract moments → Create clips → Publish
python3 ../analysers/cli.py VIDEO_ID --format json | \
  python3 ../downloaders/cli_clipper.py --aspect-ratio 9:16 | \
  python3 cli_publisher.py --platform tiktok --batch-metadata -
```

## 📚 API Reference

### Python API

```python
from publishers import TikTokPublisher, YouTubePublisher

# TikTok
publisher = TikTokPublisher()
publisher.authenticate(credentials)

result = publisher.upload_video(
    video_path="clip.mp4",
    metadata={
        "title": "My Video",
        "description": "Description",
        "privacy_level": "PUBLIC_TO_EVERYONE"
    }
)

print(f"Video published: {result['video_url']}")

# YouTube
publisher = YouTubePublisher()
publisher.authenticate(credentials)

result = publisher.upload_video(
    video_path="clip.mp4",
    metadata={
        "title": "My Video",
        "description": "Description",
        "category_id": "22",
        "privacy_status": "public"
    }
)

print(f"Video ID: {result['video_id']}")
```

### CLI Commands

```bash
# Authorization
--authorize PLATFORM              Authorize platform (tiktok/youtube)

# Upload
--platform PLATFORM               Target platform
--platforms PLATFORM1,PLATFORM2   Multiple platforms
--video PATH                      Video file path
--batch-dir DIR                   Batch upload directory
--batch-metadata FILE             Batch metadata JSON

# Metadata
--title TEXT                      Video title
--description TEXT                Video description
--tags TAG1,TAG2                  YouTube tags
--category ID                     YouTube category ID
--privacy LEVEL                   Privacy level (public/private)
--auto-title                      Auto-generate titles
--auto-description                Auto-generate descriptions
--metadata-template FILE          Custom metadata template

# Scheduling
--schedule DATETIME               Schedule upload
--timezone TZ                     Timezone for schedule

# Management
--status --upload-id ID           Check upload status
--list --platform PLATFORM        List uploads
--quota                           Check quota usage
--retry-failed                    Retry failed uploads
--queue                           Show upload queue

# Validation
--validate --video PATH           Validate video
--analytics --video-id ID         Get video analytics
```

## 🔗 Integration

### With Video Clipper Service

The publisher integrates seamlessly with the Video Clipper Service:

```python
from downloaders import process_video_moments
from publishers import TikTokPublisher

# 1. Create clips from popular moments
result = process_video_moments(moments_data, aspect_ratio='9:16')

# 2. Publish clips
publisher = TikTokPublisher()
for clip in result['clips']:
    publisher.upload_video(
        video_path=clip['path'],
        metadata={
            "title": f"Moment {clip['clip_id']} - Score {clip['score']}",
            "description": "#fyp #viral"
        }
    )
```

### With FastAPI

```python
from fastapi import FastAPI, UploadFile
from publishers import PublisherService

app = FastAPI()
service = PublisherService()

@app.post("/publish")
async def publish_video(
    file: UploadFile,
    platform: str,
    title: str,
    description: str
):
    result = await service.upload_async(
        video_path=file.filename,
        platform=platform,
        metadata={"title": title, "description": description}
    )
    return result
```

## 📖 Documentation

- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)**: Complete technical specification
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture and diagrams
- **[QUICK_START.md](QUICK_START.md)**: Step-by-step setup guide
- **[API_REFERENCE.md](API_REFERENCE.md)** _(Coming soon)_: Detailed API documentation

## 🔧 Configuration

### Environment Variables

```bash
# TikTok
TIKTOK_CLIENT_KEY=              # Your app's client key
TIKTOK_CLIENT_SECRET=           # Your app's client secret
TIKTOK_REDIRECT_URI=http://localhost:8080/callback

# YouTube
YOUTUBE_CLIENT_ID=              # OAuth client ID
YOUTUBE_CLIENT_SECRET=          # OAuth client secret
YOUTUBE_REDIRECT_URI=http://localhost:8080/callback

# Settings
DEFAULT_PLATFORM=tiktok         # Default platform
UPLOAD_CHUNK_SIZE=10485760      # 10MB chunks
MAX_RETRIES=3                   # Retry attempts
RETRY_DELAY=5                   # Seconds between retries
MAX_CONCURRENT_UPLOADS=2        # Concurrent uploads
ENABLE_AUTO_RETRY=true          # Auto-retry failed uploads
ENABLE_QUEUE_PROCESSING=true    # Background queue processing
```

### Video Requirements

| Platform | Format | Max Size | Max Duration | Aspect Ratio |
|----------|--------|----------|--------------|--------------|
| **TikTok** | MP4, WebM | 4GB | 10 minutes | 9:16 (recommended) |
| **YouTube** | MP4, MOV, AVI, etc. | 256GB | 12 hours | Any (16:9 recommended) |

## ❓ Troubleshooting

### Common Issues

**"INVALID_TOKEN" Error**
```bash
# Re-authorize
python3 cli_publisher.py --authorize tiktok
```

**"RATE_LIMIT_EXCEEDED" Error**
```bash
# Check quota
python3 cli_publisher.py --quota --platform tiktok

# Wait for reset (TikTok: 24h, YouTube: midnight PST)
```

**Upload Stuck**
```bash
# Check queue
python3 cli_publisher.py --queue

# Retry
python3 cli_publisher.py --retry-failed
```

**Video Too Large**
```bash
# Re-encode with lower quality
python3 ../downloaders/cli_clipper.py \
  --input moments.json \
  --crf 28 \
  --preset fast
```

**Full troubleshooting guide**: [QUICK_START.md#troubleshooting](QUICK_START.md#troubleshooting)

## 📊 Supported Platforms

| Platform | Status | Upload | Scheduled | Analytics | Notes |
|----------|--------|--------|-----------|-----------|-------|
| **TikTok** | ✅ Planned | ✅ | ✅ | ✅ | Content Posting API |
| **YouTube** | ✅ Planned | ✅ | ✅ | ✅ | Data API v3 + Shorts |
| **Instagram Reels** | 🔄 Planned | 🔄 | 🔄 | 🔄 | Graph API |
| **Facebook** | 📅 Future | 📅 | 📅 | 📅 | Graph API |
| **Twitter/X** | 📅 Future | 📅 | 📅 | 📅 | API v2 |
| **LinkedIn** | 📅 Future | 📅 | 📅 | 📅 | Share API |

## 🛣️ Roadmap

### Phase 1: Foundation _(Current)_
- [x] Architecture design
- [x] API research
- [x] Documentation
- [ ] Base publisher implementation
- [ ] OAuth manager
- [ ] Video validator

### Phase 2: TikTok
- [ ] Authentication
- [ ] Upload implementation
- [ ] Error handling
- [ ] Testing

### Phase 3: YouTube
- [ ] Authentication
- [ ] Resumable upload
- [ ] Shorts support
- [ ] Testing

### Phase 4: Advanced
- [ ] Upload queue
- [ ] Batch processing
- [ ] Scheduled uploads
- [ ] CLI interface
- [ ] Analytics

### Phase 5: Future
- [ ] Instagram Reels
- [ ] Facebook
- [ ] REST API
- [ ] Web dashboard

## 📄 License

Same as parent project.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Test thoroughly
4. Submit pull request

## 📮 Support

- **Issues**: GitHub Issues
- **Documentation**: See docs above
- **API Docs**:
  - TikTok: https://developers.tiktok.com/doc/content-posting-api-reference-upload-video
  - YouTube: https://developers.google.com/youtube/v3/guides/uploading_a_video

## ⚠️ Important Notes

- **Rate Limits**: TikTok allows 10 videos/day per user
- **Quota**: YouTube allows ~6 videos/day (10,000 units)
- **Verification**: YouTube requires channel verification for >15min videos
- **Content Policy**: Follow platform guidelines to avoid bans
- **Testing**: Use separate test accounts during development

---

**Made with ❤️ for content creators**