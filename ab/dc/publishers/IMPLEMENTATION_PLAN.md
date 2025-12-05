# Social Media Publishers Implementation Plan

## Overview
Implementation of automated video publishing to TikTok and YouTube platforms using their official APIs.

## Architecture

```
ab/dc/publishers/
├── __init__.py                 # Package initialization
├── base_publisher.py           # Abstract base class for all publishers
├── tiktok_publisher.py         # TikTok Content Posting API implementation
├── youtube_publisher.py        # YouTube Data API v3 implementation
├── publisher_config.py         # Configuration management
├── oauth_manager.py            # OAuth 2.0 flow management
├── upload_queue.py             # Queue system for batch uploads
├── publisher_service.py        # Main orchestrator service
├── cli_publisher.py            # Command-line interface
└── utils/
    ├── __init__.py
    ├── video_validator.py      # Video format/size validation
    ├── metadata_builder.py     # Platform-specific metadata
    ├── retry_handler.py        # Retry logic with exponential backoff
    └── rate_limiter.py         # API rate limiting
```

---

## 1. TikTok Content Posting API

### API Reference
- **Documentation**: https://developers.tiktok.com/doc/content-posting-api-reference-upload-video
- **Authentication**: OAuth 2.0
- **Scopes Required**: `video.upload`, `video.publish`

### Upload Process Flow

```
1. Initialize Upload (POST /v2/post/publish/inbox/video/init/)
   ↓
2. Upload Video Chunks (POST /v2/post/publish/video/upload/)
   ↓
3. Publish Video (POST /v2/post/publish/status/fetch/)
```

### Implementation Details

#### 1.1 Authentication
```python
# OAuth 2.0 Flow
- Authorization URL: https://www.tiktok.com/v2/auth/authorize/
- Token URL: https://open.tiktokapis.com/v2/oauth/token/
- Required Scopes: video.upload, video.publish
- Access Token expires: 24 hours
- Refresh Token expires: Never (unless revoked)
```

#### 1.2 Video Requirements
- **Format**: MP4 or WebM
- **Codec**: H.264 or H.265
- **Resolution**:
  - Minimum: 360p
  - Maximum: 4K (4096x2160)
  - Recommended: 1080x1920 (9:16 vertical)
- **File Size**: Maximum 4GB
- **Duration**:
  - Minimum: 3 seconds
  - Maximum: 10 minutes
- **Aspect Ratio**: 9:16 (vertical) recommended

#### 1.3 Upload Steps

**Step 1: Initialize Upload**
```http
POST https://open.tiktokapis.com/v2/post/publish/inbox/video/init/
Headers:
  Authorization: Bearer {access_token}
  Content-Type: application/json

Body:
{
  "post_info": {
    "title": "Video title",
    "privacy_level": "PUBLIC_TO_EVERYONE",
    "disable_duet": false,
    "disable_comment": false,
    "disable_stitch": false,
    "video_cover_timestamp_ms": 1000
  },
  "source_info": {
    "source": "FILE_UPLOAD",
    "video_size": 123456789,
    "chunk_size": 10485760,
    "total_chunk_count": 12
  }
}

Response:
{
  "data": {
    "publish_id": "v_pub_7123456789",
    "upload_url": "https://upload.tiktokapis.com/..."
  }
}
```

**Step 2: Upload Video Chunks**
```http
POST {upload_url}
Headers:
  Content-Range: bytes 0-10485759/123456789
  Content-Length: 10485760
  Content-Type: video/mp4

Body: [binary video chunk data]
```

**Step 3: Check Publish Status**
```http
POST https://open.tiktokapis.com/v2/post/publish/status/fetch/
Headers:
  Authorization: Bearer {access_token}
  Content-Type: application/json

Body:
{
  "publish_id": "v_pub_7123456789"
}

Response:
{
  "data": {
    "status": "PUBLISHED",
    "publicaly_available_post_id": ["7123456789012345678"],
    "fail_reason": null
  }
}
```

#### 1.4 Error Handling
- **Rate Limits**: 10 videos per day (per user)
- **Common Errors**:
  - `INVALID_TOKEN`: Refresh access token
  - `VIDEO_TOO_LARGE`: Video exceeds 4GB
  - `UNSUPPORTED_FORMAT`: Wrong codec/format
  - `DUPLICATE_VIDEO`: Video already uploaded
  - `RATE_LIMIT_EXCEEDED`: Wait and retry

---

## 2. YouTube Data API v3

### API Reference
- **Documentation**: https://developers.google.com/youtube/v3/guides/uploading_a_video
- **Authentication**: OAuth 2.0
- **Scopes Required**: `https://www.googleapis.com/auth/youtube.upload`

### Upload Process Flow

```
1. Authorize User (OAuth 2.0)
   ↓
2. Upload Video (POST /youtube/v3/videos)
   ↓
3. Set Thumbnail (Optional)
   ↓
4. Monitor Processing Status
```

### Implementation Details

#### 2.1 Authentication
```python
# OAuth 2.0 Flow
- Authorization URL: https://accounts.google.com/o/oauth2/v2/auth
- Token URL: https://oauth2.googleapis.com/token
- Required Scopes: https://www.googleapis.com/auth/youtube.upload
- Access Token expires: 1 hour
- Refresh Token expires: Never (unless revoked)
```

#### 2.2 Video Requirements
- **Format**: Most common formats supported (MP4, MOV, AVI, WMV, FLV, 3GP, WebM)
- **Codec**: H.264, MPEG-2, MPEG-4
- **Resolution**:
  - Minimum: 426x240
  - Maximum: 7680x4320 (8K)
  - Standard: 1920x1080 (16:9)
- **File Size**: Maximum 256GB (or 12 hours duration)
- **Duration**: Maximum 12 hours (15 minutes for unverified accounts)
- **Aspect Ratio**: 16:9 recommended, but supports vertical (9:16) via Shorts

#### 2.3 Upload Method

**Resumable Upload (Recommended for files > 5MB)**
```http
POST https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status
Headers:
  Authorization: Bearer {access_token}
  Content-Type: application/json
  X-Upload-Content-Length: 123456789
  X-Upload-Content-Type: video/mp4

Body:
{
  "snippet": {
    "title": "Video Title",
    "description": "Video description with #hashtags",
    "tags": ["tag1", "tag2", "tag3"],
    "categoryId": "22",
    "defaultLanguage": "en",
    "defaultAudioLanguage": "en"
  },
  "status": {
    "privacyStatus": "public",
    "selfDeclaredMadeForKids": false,
    "embeddable": true,
    "publicStatsViewable": true
  }
}

Response:
{
  "kind": "youtube#video",
  "id": "dQw4w9WgXcQ",
  "snippet": {
    "publishedAt": "2024-12-05T10:00:00Z",
    "channelId": "UCxxxxxx",
    "title": "Video Title"
  }
}
```

**Upload Video Content**
```http
PUT {session_uri}
Headers:
  Content-Length: 123456789
  Content-Type: video/mp4

Body: [binary video data]
```

#### 2.4 YouTube Shorts Support
- Videos < 60 seconds automatically treated as Shorts
- Use `#Shorts` in title/description
- Vertical aspect ratio (9:16) recommended
- Maximum 60 seconds duration

#### 2.5 Error Handling
- **Rate Limits**: 10,000 quota units per day
  - Video upload costs: 1600 units
  - ~6 videos per day
- **Common Errors**:
  - `INVALID_TOKEN`: Refresh access token
  - `QUOTA_EXCEEDED`: Wait until next day
  - `VIDEO_TOO_LARGE`: Video exceeds 256GB
  - `INVALID_VIDEO`: Processing error
  - `FORBIDDEN`: Channel not verified for long uploads

---

## 3. Base Publisher (Abstract Class)

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from pathlib import Path

class BasePublisher(ABC):
    """Abstract base class for social media publishers"""

    @abstractmethod
    def authenticate(self, credentials: Dict) -> bool:
        """Authenticate with OAuth 2.0"""
        pass

    @abstractmethod
    def validate_video(self, video_path: Path) -> tuple[bool, str]:
        """Validate video meets platform requirements"""
        pass

    @abstractmethod
    def upload_video(self, video_path: Path, metadata: Dict) -> Dict:
        """Upload video to platform"""
        pass

    @abstractmethod
    def get_upload_status(self, upload_id: str) -> Dict:
        """Check upload/processing status"""
        pass

    @abstractmethod
    def delete_video(self, video_id: str) -> bool:
        """Delete published video"""
        pass

    @abstractmethod
    def get_video_analytics(self, video_id: str) -> Dict:
        """Get video performance metrics"""
        pass
```

---

## 4. Configuration Management

### Environment Variables (.env)
```bash
# TikTok Configuration
TIKTOK_CLIENT_KEY=your_client_key
TIKTOK_CLIENT_SECRET=your_client_secret
TIKTOK_REDIRECT_URI=http://localhost:8080/callback
TIKTOK_ACCESS_TOKEN=
TIKTOK_REFRESH_TOKEN=

# YouTube Configuration
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_REDIRECT_URI=http://localhost:8080/callback
YOUTUBE_ACCESS_TOKEN=
YOUTUBE_REFRESH_TOKEN=

# Publisher Settings
DEFAULT_PLATFORM=tiktok
UPLOAD_CHUNK_SIZE=10485760  # 10MB
MAX_RETRIES=3
RETRY_DELAY=5
ENABLE_AUTO_RETRY=true
ENABLE_QUEUE_PROCESSING=true
MAX_CONCURRENT_UPLOADS=2
```

---

## 5. Key Features

### 5.1 OAuth 2.0 Manager
- Automated authorization flow with local callback server
- Token storage and encryption
- Automatic token refresh
- Multi-account support
- Token expiration handling

### 5.2 Upload Queue System
- Background processing
- Priority queue support
- Scheduled uploads
- Batch processing
- Failed upload retry
- Upload progress tracking

### 5.3 Video Validation
- Format/codec verification
- File size limits
- Resolution requirements
- Duration limits
- Aspect ratio checks
- Bitrate validation

### 5.4 Metadata Builder
- Platform-specific formatting
- Hashtag optimization
- Caption generation
- Category selection
- Privacy settings
- Thumbnail generation

### 5.5 Rate Limiting
- Per-platform quota tracking
- Automatic throttling
- Request queuing
- Quota reset tracking
- Warning notifications

### 5.6 Retry Handler
- Exponential backoff
- Configurable retry attempts
- Error-specific handling
- Partial upload resume
- Network error recovery

---

## 6. CLI Interface

```bash
# Publish single video to TikTok
python3 ab/dc/publishers/cli_publisher.py \
  --platform tiktok \
  --video path/to/video.mp4 \
  --title "Amazing video!" \
  --description "Check this out #fyp #viral" \
  --privacy public

# Publish to YouTube
python3 ab/dc/publishers/cli_publisher.py \
  --platform youtube \
  --video path/to/video.mp4 \
  --title "My Video Title" \
  --description "Full description here" \
  --category 22 \
  --tags "tag1,tag2,tag3" \
  --privacy public

# Publish to multiple platforms
python3 ab/dc/publishers/cli_publisher.py \
  --platforms tiktok,youtube \
  --video path/to/video.mp4 \
  --title "Cross-platform video" \
  --config metadata.json

# Batch upload from directory
python3 ab/dc/publishers/cli_publisher.py \
  --platform tiktok \
  --batch-dir processed_videos/ \
  --metadata-file batch_metadata.json

# Schedule upload
python3 ab/dc/publishers/cli_publisher.py \
  --platform youtube \
  --video video.mp4 \
  --schedule "2024-12-06 10:00:00" \
  --title "Scheduled Video"

# Check upload status
python3 ab/dc/publishers/cli_publisher.py \
  --status \
  --upload-id abc123xyz

# List uploads
python3 ab/dc/publishers/cli_publisher.py \
  --list \
  --platform tiktok \
  --limit 10
```

---

## 7. Integration with Video Clipper Service

### Workflow Example
```bash
# 1. Extract popular moments
python3 ab/dc/analysers/cli.py VIDEO_ID --format json > moments.json

# 2. Create vertical clips for TikTok
python3 ab/dc/downloaders/cli_clipper.py \
  --input moments.json \
  --aspect-ratio 9:16 \
  --output clips_metadata.json

# 3. Auto-publish to TikTok
python3 ab/dc/publishers/cli_publisher.py \
  --platform tiktok \
  --batch-metadata clips_metadata.json \
  --auto-title \
  --auto-description \
  --privacy public
```

---

## 8. Implementation Priority

### Phase 1: Foundation (Week 1)
1. ✅ Base publisher abstract class
2. ✅ Configuration management
3. ✅ OAuth 2.0 manager
4. ✅ Video validator utility
5. ✅ Rate limiter utility

### Phase 2: TikTok Publisher (Week 2)
1. ✅ TikTok authentication
2. ✅ Upload initialization
3. ✅ Chunked upload implementation
4. ✅ Publish status checking
5. ✅ Error handling and retry logic
6. ✅ Testing with real videos

### Phase 3: YouTube Publisher (Week 3)
1. ✅ YouTube authentication
2. ✅ Resumable upload implementation
3. ✅ Shorts detection and handling
4. ✅ Thumbnail upload
5. ✅ Error handling and retry logic
6. ✅ Testing with real videos

### Phase 4: Advanced Features (Week 4)
1. ✅ Upload queue system
2. ✅ Batch processing
3. ✅ Scheduled uploads
4. ✅ CLI interface
5. ✅ Integration with clipper service
6. ✅ Documentation and examples

---

## 9. Testing Strategy

### Unit Tests
- OAuth flow simulation
- Video validation
- Metadata building
- Rate limiting
- Retry logic

### Integration Tests
- Full upload flow (TikTok)
- Full upload flow (YouTube)
- Multi-platform publishing
- Batch uploads
- Error scenarios

### Manual Testing
- Real video uploads
- Token refresh handling
- Rate limit testing
- Network failure recovery
- Cross-platform metadata

---

## 10. Security Considerations

1. **Token Storage**: Encrypt access/refresh tokens at rest
2. **Credentials**: Never commit API keys to git
3. **HTTPS**: All API calls over HTTPS
4. **Callback Server**: Secure OAuth callback handling
5. **Input Validation**: Sanitize all user inputs
6. **File Permissions**: Restrict access to credentials files
7. **Audit Logging**: Log all upload attempts and results

---

## 11. Documentation

### Required Documentation
1. **Setup Guide**: OAuth app creation for both platforms
2. **API Guide**: Publisher API usage examples
3. **CLI Guide**: Command-line usage and options
4. **Integration Guide**: Integration with other services
5. **Troubleshooting**: Common errors and solutions
6. **Best Practices**: Optimization tips and recommendations

---

## 12. Success Metrics

- ✅ Upload success rate > 95%
- ✅ Average upload time < 2 minutes (for 100MB video)
- ✅ Token refresh success rate > 99%
- ✅ API rate limit compliance 100%
- ✅ Support for videos up to 4GB (TikTok) / 256GB (YouTube)
- ✅ Concurrent uploads: 2-5 videos
- ✅ Zero credential leaks

---

## 13. Future Enhancements

- Instagram Reels support
- Facebook video publishing
- Twitter/X video posting
- LinkedIn video sharing
- Video scheduling calendar UI
- Analytics dashboard
- Automated A/B testing (titles, thumbnails)
- AI-powered metadata generation
- Multi-language support
- Webhook notifications
- REST API endpoint