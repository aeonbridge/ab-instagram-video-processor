# YouTube Publisher Setup Guide

Complete guide to setting up the YouTube publisher for automated video uploads.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Creating YouTube API Credentials](#creating-youtube-api-credentials)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- Python 3.8+
- FFmpeg and FFprobe installed
- Internet connection
- Google account with YouTube channel

### Python Dependencies

```bash
pip install requests python-dotenv
```

---

## Creating YouTube API Credentials

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `ab-video-publisher`
4. Click "Create"

### Step 2: Enable YouTube Data API v3

1. In your project, go to "APIs & Services" → "Library"
2. Search for "YouTube Data API v3"
3. Click on it and press "Enable"

### Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen first:
   - User Type: External
   - App name: `AB Video Publisher`
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Add `youtube.upload` and `youtube`
   - Test users: Add your Google account email
   - Click "Save and Continue"

4. Create OAuth Client ID:
   - Application type: **Desktop app**
   - Name: `AB Video Publisher Desktop Client`
   - Click "Create"

5. Download credentials:
   - Click "Download JSON" button
   - Or copy Client ID and Client Secret

### Step 4: Configure OAuth Consent Screen

1. Go to "OAuth consent screen"
2. Add test users (your Google account)
3. Status: Testing (allows up to 100 test users)
4. For production, submit for verification

---

## Configuration

### 1. Update .env File

Edit your `.env` file in the project root:

```bash
# YouTube OAuth Configuration
YOUTUBE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret_here
YOUTUBE_REDIRECT_URI=http://localhost:8080

# Publisher Settings
DEFAULT_PLATFORM=youtube
UPLOAD_CHUNK_SIZE=10485760
MAX_RETRIES=3
```

### 2. Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `YOUTUBE_CLIENT_ID` | OAuth 2.0 Client ID | `123456789.apps.googleusercontent.com` |
| `YOUTUBE_CLIENT_SECRET` | OAuth 2.0 Client Secret | `GOCSPX-abc123xyz` |
| `YOUTUBE_REDIRECT_URI` | OAuth callback URL | `http://localhost:8080` |
| `UPLOAD_CHUNK_SIZE` | Upload chunk size in bytes | `10485760` (10MB) |
| `MAX_RETRIES` | Retry attempts for failed uploads | `3` |

### 3. Optional Settings

```bash
# Token storage (where OAuth tokens are saved)
TOKEN_STORAGE_PATH=~/.ab_publisher_tokens.json

# Video validation
FFPROBE_PATH=ffprobe

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/publisher.log
```

---

## Authentication

### First-Time Authentication

Run the authentication command:

```bash
cd ab/dc/publishers
python cli_publisher.py auth
```

This will:
1. Open your default web browser
2. Ask you to log in to Google
3. Request permission to upload videos to your channel
4. Redirect back to localhost with authorization code
5. Exchange code for access/refresh tokens
6. Save tokens to `~/.ab_publisher_tokens.json`

### Token Management

Tokens are automatically managed:
- **Access Token**: Valid for 1 hour, auto-refreshed
- **Refresh Token**: Valid indefinitely (unless revoked)
- **Storage**: Encrypted and saved locally

To re-authenticate (if tokens expire or are revoked):

```bash
python cli_publisher.py auth
```

---

## Usage Examples

### Basic Upload

```bash
python cli_publisher.py upload my_video.mp4 \
  --title "My Amazing Video" \
  --description "Check this out!" \
  --privacy public
```

### Complete Upload with All Options

```bash
python cli_publisher.py upload gameplay.mp4 \
  --title "Epic Minecraft Build Tutorial" \
  --description "Learn how to build amazing structures in Minecraft!

Follow me for more tutorials!

Timestamps:
0:00 - Introduction
1:30 - Materials needed
3:45 - Building process
10:20 - Final touches

#minecraft #tutorial #gaming" \
  --tags "minecraft,gaming,tutorial,build,creative" \
  --category gaming \
  --privacy public \
  --language en \
  --thumbnail custom_thumb.jpg
```

### Upload YouTube Short

```bash
python cli_publisher.py upload short_clip.mp4 \
  --title "Quick Tip #Shorts" \
  --description "One minute life hack!" \
  --privacy public
```

Note: Videos under 60 seconds with vertical aspect ratio (9:16) are automatically treated as Shorts.

### Check Upload Status

```bash
python cli_publisher.py status VIDEO_ID
```

### Delete Video

```bash
python cli_publisher.py delete VIDEO_ID
```

---

## Upload from Processed Clips

### Workflow: Extract Popular Moments → Upload to YouTube

```bash
# 1. Extract popular moments from YouTube video
cd ab/dc/analysers
python cli.py VIDEO_ID --format json > moments.json

# 2. Create vertical clips (9:16 for Shorts)
cd ../downloaders
python cli_clipper.py \
  --input ../analysers/moments.json \
  --aspect-ratio 9:16 \
  --output clips_metadata.json

# 3. Upload clips to YouTube
cd ../publishers
for clip in ../../processed_videos/*.mp4; do
  python cli_publisher.py upload "$clip" \
    --title "Epic Moment from [Original Video]" \
    --tags "shorts,viral,epic" \
    --privacy public
done
```

---

## Video Requirements

### Technical Specifications

| Requirement | Value |
|-------------|-------|
| **Maximum file size** | 256 GB |
| **Maximum duration** | 12 hours |
| **Minimum duration** | 1 second |
| **Supported formats** | MP4, MOV, AVI, WMV, FLV, 3GP, WebM, MKV |
| **Supported codecs** | H.264, H.265, MPEG-2, MPEG-4 |
| **Minimum resolution** | 426x240 |
| **Maximum resolution** | 7680x4320 (8K) |
| **Recommended resolution** | 1920x1080 (1080p) |

### YouTube Shorts Requirements

- **Duration**: Maximum 60 seconds
- **Aspect ratio**: 9:16 (vertical)
- **Resolution**: Minimum 1080x1920
- **Title/Description**: Include `#Shorts`

---

## Rate Limits and Quotas

### YouTube API Quotas

- **Daily quota**: 10,000 units
- **Video upload cost**: 1,600 units
- **Maximum uploads per day**: ~6 videos
- **Quota reset**: Midnight PST

### Rate Limiting

The publisher includes built-in rate limiting:
- Automatic quota tracking
- Request throttling
- Retry with exponential backoff
- Quota reset monitoring

To check remaining quota:

```python
from youtube_publisher import YouTubePublisher
from publisher_config import get_config

config = get_config()
publisher = YouTubePublisher(config.get_youtube_credentials())
remaining = publisher.rate_limiter.get_remaining_quota()
print(f"Remaining quota: {remaining} units")
```

---

## Privacy Settings

### Available Privacy Levels

| Privacy | Description | Use Case |
|---------|-------------|----------|
| `public` | Anyone can search and view | General content |
| `unlisted` | Only people with link can view | Sharing with specific audience |
| `private` | Only you can view | Testing before publishing |

### Changing Privacy After Upload

Videos are uploaded as `public` by default. To change:

1. Go to [YouTube Studio](https://studio.youtube.com/)
2. Select video → Details
3. Change visibility settings

---

## Troubleshooting

### Authentication Issues

**Problem**: "Authentication failed"

**Solutions**:
1. Check Client ID and Secret in `.env`
2. Ensure OAuth consent screen has test users
3. Verify redirect URI matches exactly: `http://localhost:8080`
4. Check if port 8080 is available
5. Try re-authentication: `python cli_publisher.py auth`

### Upload Failures

**Problem**: "Upload failed: quota exceeded"

**Solution**: YouTube has daily upload limits. Wait until quota resets (midnight PST).

**Problem**: "Video validation failed"

**Solutions**:
1. Check video format and codec
2. Verify FFprobe is installed: `ffprobe -version`
3. Test video file: `ffprobe your_video.mp4`

**Problem**: "Token expired"

**Solution**: Tokens are auto-refreshed. If this fails, re-authenticate:
```bash
python cli_publisher.py auth
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `INVALID_TOKEN` | Access token expired | Auto-refreshed, or re-auth |
| `QUOTA_EXCEEDED` | Daily quota limit reached | Wait for reset or request increase |
| `VIDEO_TOO_LARGE` | File exceeds 256GB | Compress or split video |
| `FORBIDDEN` | Channel not verified | Verify channel for uploads > 15 min |
| `INVALID_VIDEO` | Processing error | Check video format/codec |

### Debugging

Enable debug logging:

```bash
# In .env
LOG_LEVEL=DEBUG
LOG_FILE=logs/publisher.log
```

View logs:
```bash
tail -f logs/publisher.log
```

---

## Security Best Practices

1. **Never commit credentials**:
   - Add `.env` to `.gitignore`
   - Use environment variables in production

2. **Protect token file**:
   ```bash
   chmod 600 ~/.ab_publisher_tokens.json
   ```

3. **Rotate credentials** regularly:
   - Revoke old OAuth clients
   - Create new credentials
   - Update `.env` file

4. **Limit OAuth scopes**:
   - Only request `youtube.upload` scope
   - Avoid full `youtube` scope unless needed

---

## Advanced Features

### Custom Thumbnails

Upload custom thumbnail (JPG, PNG):

```bash
python cli_publisher.py upload video.mp4 \
  --title "My Video" \
  --thumbnail custom_thumb.jpg
```

Requirements:
- Format: JPG, PNG, GIF, BMP
- Max file size: 2MB
- Resolution: 1280x720 (recommended)
- Aspect ratio: 16:9

### Scheduled Uploads (Future)

Planned feature for scheduling uploads:

```bash
python cli_publisher.py upload video.mp4 \
  --title "Scheduled Video" \
  --schedule "2024-12-10 10:00:00"
```

### Batch Uploads (Future)

Planned feature for batch processing:

```bash
python cli_publisher.py batch \
  --directory processed_videos/ \
  --metadata batch_metadata.json
```

---

## API Reference

### Command-Line Interface

```bash
# Authenticate
python cli_publisher.py auth

# Upload video
python cli_publisher.py upload VIDEO_FILE [OPTIONS]

# Check status
python cli_publisher.py status VIDEO_ID

# Delete video
python cli_publisher.py delete VIDEO_ID [--confirm]
```

### Python API

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

# Upload video
metadata = VideoMetadata(
    title="My Video",
    description="Video description",
    tags=["tag1", "tag2"],
    privacy="public"
)

result = publisher.upload_video(
    video_path=Path("video.mp4"),
    metadata=metadata
)

if result.success:
    print(f"Video uploaded: {result.video_url}")
else:
    print(f"Upload failed: {result.error}")
```

---

## Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [YouTube Upload Best Practices](https://support.google.com/youtube/answer/1722171)
- [YouTube Shorts Guidelines](https://support.google.com/youtube/answer/10059070)

---

## Support

For issues and questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review error logs: `logs/publisher.log`
3. Verify configuration: `.env` file
4. Test authentication: `python cli_publisher.py auth`

---

## License

This publisher follows the project's main license agreement.

**Important**: Ensure compliance with [YouTube's Terms of Service](https://www.youtube.com/t/terms) and [API Services Terms](https://developers.google.com/youtube/terms/api-services-terms-of-service).
