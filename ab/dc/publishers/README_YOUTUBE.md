# YouTube Publisher

Automated video publishing to YouTube using Data API v3.

## Quick Start

### 1. Install Dependencies

```bash
pip install requests python-dotenv
```

### 2. Configure Credentials

Get YouTube API credentials from [Google Cloud Console](https://console.developers.google.com/).

Edit `.env` file in project root:

```bash
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_REDIRECT_URI=http://localhost:8080
```

See [YOUTUBE_SETUP.md](YOUTUBE_SETUP.md) for detailed setup instructions.

### 3. Authenticate

```bash
cd ab/dc/publishers
python cli_publisher.py auth
```

This opens your browser for OAuth authorization.

### 4. Upload Video

```bash
python cli_publisher.py upload path/to/video.mp4 \
  --title "My Amazing Video" \
  --description "Check this out!" \
  --tags "tag1,tag2,tag3" \
  --privacy public
```

## Features

- OAuth 2.0 authentication with automatic token refresh
- Resumable uploads (handles interruptions gracefully)
- YouTube Shorts auto-detection (< 60s + vertical)
- Custom thumbnail upload
- Video validation before upload
- Rate limiting and quota tracking
- Progress bar for uploads
- Comprehensive error handling

## Commands

### Authenticate
```bash
python cli_publisher.py auth
```

### Upload Video
```bash
python cli_publisher.py upload VIDEO_FILE [OPTIONS]

Options:
  --title TEXT              Video title (required)
  --description TEXT        Video description
  --tags TEXT               Comma-separated tags
  --category TEXT           Category (default: entertainment)
  --privacy public|private|unlisted
  --language TEXT           Language code (default: en)
  --thumbnail PATH          Custom thumbnail image
  --no-progress            Disable progress bar
```

### Check Video Status
```bash
python cli_publisher.py status VIDEO_ID
```

### Delete Video
```bash
python cli_publisher.py delete VIDEO_ID [--confirm]
```

## Examples

### Upload YouTube Short
```bash
python cli_publisher.py upload short.mp4 \
  --title "Quick Tip #Shorts" \
  --description "One minute life hack!" \
  --privacy public
```

### Upload with Custom Thumbnail
```bash
python cli_publisher.py upload video.mp4 \
  --title "My Video" \
  --thumbnail custom_thumb.jpg \
  --privacy public
```

### Upload Gaming Video
```bash
python cli_publisher.py upload gameplay.mp4 \
  --title "Epic Minecraft Build" \
  --description "Amazing castle build tutorial" \
  --tags "minecraft,gaming,tutorial" \
  --category gaming \
  --privacy public
```

## Video Requirements

- **Formats**: MP4, MOV, AVI, WMV, FLV, 3GP, WebM, MKV
- **Codecs**: H.264, H.265, MPEG-2, MPEG-4
- **Max Size**: 256GB
- **Max Duration**: 12 hours
- **Resolution**: 426x240 to 7680x4320 (8K)

### YouTube Shorts
- **Duration**: ≤ 60 seconds
- **Aspect Ratio**: 9:16 (vertical)
- **Auto-detected**: No need for special flags

## Rate Limits

- **Daily Quota**: 10,000 units
- **Upload Cost**: 1,600 units per video
- **Max Uploads**: ~6 videos per day
- **Reset Time**: Midnight PST

Built-in rate limiting prevents quota exhaustion.

## Troubleshooting

### Authentication Failed
```bash
# Re-authenticate
python cli_publisher.py auth

# Check .env file has correct credentials
cat ../.env | grep YOUTUBE
```

### Upload Failed
```bash
# Check video format
ffprobe video.mp4

# Enable debug logging
# Edit .env:
LOG_LEVEL=DEBUG

# Try again
python cli_publisher.py upload video.mp4 --title "Test"
```

### Quota Exceeded
YouTube limits daily uploads. Wait until quota resets (midnight PST) or request quota increase from Google.

## Integration with Video Clipper

```bash
# 1. Extract popular moments
cd ../analysers
python cli.py VIDEO_ID --format json > moments.json

# 2. Create clips (vertical for Shorts)
cd ../downloaders
python cli_clipper.py --input ../analysers/moments.json --aspect-ratio 9:16

# 3. Upload clips to YouTube
cd ../publishers
for clip in ../../processed_videos/*.mp4; do
  python cli_publisher.py upload "$clip" \
    --title "Epic Moment #Shorts" \
    --tags "shorts,viral,gaming" \
    --privacy public
done
```

## Python API

```python
from pathlib import Path
from youtube_publisher import YouTubePublisher
from base_publisher import VideoMetadata
from publisher_config import get_config

# Initialize
config = get_config()
publisher = YouTubePublisher(config.get_youtube_credentials())

# Authenticate
publisher.authenticate()

# Upload
metadata = VideoMetadata(
    title="My Video",
    description="Description here",
    tags=["tag1", "tag2"],
    privacy="public"
)

result = publisher.upload_video(
    video_path=Path("video.mp4"),
    metadata=metadata,
    progress_callback=lambda p: print(f"Progress: {p*100:.1f}%")
)

if result.success:
    print(f"Uploaded: {result.video_url}")
else:
    print(f"Failed: {result.error}")
```

## Documentation

- [YOUTUBE_SETUP.md](YOUTUBE_SETUP.md) - Complete setup guide
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Architecture overview
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Implementation details

## Architecture

```
publishers/
├── base_publisher.py          # Abstract base class
├── youtube_publisher.py       # YouTube implementation
├── oauth_manager.py           # OAuth 2.0 flow
├── publisher_config.py        # Configuration
├── cli_publisher.py           # CLI interface
└── utils/
    ├── video_validator.py     # Video validation
    ├── metadata_builder.py    # Metadata optimization
    ├── rate_limiter.py        # Rate limiting
    └── retry_handler.py       # Retry logic
```

## Security

- Tokens stored in `~/.ab_publisher_tokens.json`
- Automatic token refresh
- No credentials in logs
- HTTPS for all API calls
- Local OAuth callback server

## Support

For detailed help:
1. Read [YOUTUBE_SETUP.md](YOUTUBE_SETUP.md)
2. Check logs: `logs/publisher.log`
3. Enable debug: `LOG_LEVEL=DEBUG` in `.env`

## License

Follows project's main license. Complies with:
- YouTube Terms of Service
- YouTube API Services Terms
- Google API Guidelines

---

**Status**: Production-ready

**Version**: 1.0.0

**Last Updated**: 2025-12-05
