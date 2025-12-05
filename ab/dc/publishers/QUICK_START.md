# Publishers Quick Start Guide

## Prerequisites

### 1. TikTok Developer Account Setup

1. **Create TikTok for Developers Account**
   - Go to https://developers.tiktok.com/
   - Sign up with your TikTok account
   - Verify your email

2. **Create App**
   - Navigate to "Manage apps" → "Create app"
   - Fill in app details:
     - App name: "Video Publisher"
     - Category: "Content Creation"
     - Description: "Automated video publishing tool"

3. **Configure OAuth**
   - Go to "Login Kit" → "Web"
   - Add redirect URI: `http://localhost:8080/callback`
   - Request permissions:
     - ✅ `video.upload`
     - ✅ `video.publish`

4. **Get Credentials**
   - Copy **Client Key** (will be TIKTOK_CLIENT_KEY)
   - Copy **Client Secret** (will be TIKTOK_CLIENT_SECRET)

### 2. YouTube/Google Cloud Setup

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com/
   - Create new project: "Video Publisher"

2. **Enable YouTube Data API v3**
   - Navigate to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"

3. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Video Publisher Desktop"
   - Download JSON (save as `youtube_credentials.json`)

4. **Configure OAuth Consent Screen**
   - User type: "External"
   - Add scopes: `https://www.googleapis.com/auth/youtube.upload`
   - Add your email as test user

### 3. Environment Setup

```bash
# Install dependencies
pip install requests oauthlib google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Create .env file
cp .env.example .env
```

## Configuration

### .env File

```bash
# TikTok Configuration
TIKTOK_CLIENT_KEY=your_client_key_here
TIKTOK_CLIENT_SECRET=your_client_secret_here
TIKTOK_REDIRECT_URI=http://localhost:8080/callback

# YouTube Configuration
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_REDIRECT_URI=http://localhost:8080/callback

# General Settings
DEFAULT_PLATFORM=tiktok
UPLOAD_CHUNK_SIZE=10485760
MAX_RETRIES=3
RETRY_DELAY=5
MAX_CONCURRENT_UPLOADS=2
```

## First-Time Authorization

### TikTok

```bash
# Run authorization flow
python3 ab/dc/publishers/cli_publisher.py --authorize tiktok

# This will:
# 1. Open browser to TikTok login
# 2. You authorize the app
# 3. Redirect to localhost (callback)
# 4. Save tokens to ~/.publisher_cache/tokens/tiktok_tokens.enc
```

### YouTube

```bash
# Run authorization flow
python3 ab/dc/publishers/cli_publisher.py --authorize youtube

# This will:
# 1. Open browser to Google login
# 2. You select Google account
# 3. Grant permissions
# 4. Redirect to localhost (callback)
# 5. Save tokens to ~/.publisher_cache/tokens/youtube_tokens.enc
```

## Basic Usage Examples

### 1. Publish Single Video to TikTok

```bash
python3 ab/dc/publishers/cli_publisher.py \
  --platform tiktok \
  --video processed_videos/RusBe_8arLQ/RusBe_8arLQ_0000_40s_score_156_9x16.mp4 \
  --title "Epic gaming moment!" \
  --description "Check this out! #gaming #viral #fyp" \
  --privacy public
```

**Expected Output:**
```
✓ Video validated successfully
✓ TikTok authentication valid
✓ Upload initialized: v_pub_7123456789
↑ Uploading chunks: [██████████] 100% (16.0MB)
✓ Video published successfully!

Video Details:
- Platform: TikTok
- Video ID: 7123456789012345678
- Status: PUBLISHED
- URL: https://www.tiktok.com/@user/video/7123456789012345678
- Upload time: 45.2s
```

### 2. Publish to YouTube

```bash
python3 ab/dc/publishers/cli_publisher.py \
  --platform youtube \
  --video processed_videos/RusBe_8arLQ/RusBe_8arLQ_0000_40s_score_156_9x16.mp4 \
  --title "Amazing Gaming Moment #Shorts" \
  --description "Epic play from RusBe_8arLQ\n\n#gaming #shorts #viral" \
  --category 20 \
  --tags "gaming,highlights,shorts" \
  --privacy public
```

### 3. Cross-Platform Publishing

```bash
# Publish same video to both TikTok and YouTube
python3 ab/dc/publishers/cli_publisher.py \
  --platforms tiktok,youtube \
  --video video.mp4 \
  --title "My Amazing Video" \
  --description "Description here #viral" \
  --config cross_platform_config.json
```

**cross_platform_config.json:**
```json
{
  "tiktok": {
    "privacy_level": "PUBLIC_TO_EVERYONE",
    "disable_duet": false,
    "disable_comment": false,
    "disable_stitch": false
  },
  "youtube": {
    "category_id": "22",
    "privacy_status": "public",
    "made_for_kids": false
  }
}
```

### 4. Batch Upload

```bash
# Upload all clips from a directory
python3 ab/dc/publishers/cli_publisher.py \
  --platform tiktok \
  --batch-dir processed_videos/RusBe_8arLQ/ \
  --metadata-file batch_metadata.json \
  --auto-title \
  --auto-description
```

**batch_metadata.json:**
```json
{
  "template": {
    "title": "Gaming Moment #{clip_id} - Score {score}",
    "description": "Epic moment from {video_id}\n\n#gaming #viral #fyp",
    "privacy": "public"
  },
  "clips": [
    {
      "filename": "RusBe_8arLQ_0000_40s_score_156_9x16.mp4",
      "score": 1.56
    },
    {
      "filename": "RusBe_8arLQ_0001_40s_score_137_9x16.mp4",
      "score": 1.37
    }
  ]
}
```

### 5. Scheduled Upload

```bash
# Schedule video to publish at specific time
python3 ab/dc/publishers/cli_publisher.py \
  --platform youtube \
  --video video.mp4 \
  --title "Morning Upload" \
  --schedule "2024-12-06 08:00:00" \
  --timezone "America/New_York"
```

## Integration with Video Clipper Service

### Complete Workflow: Extract → Clip → Publish

```bash
#!/bin/bash
# complete_workflow.sh

VIDEO_ID="RusBe_8arLQ"
ASPECT_RATIO="9:16"
PLATFORM="tiktok"

# Step 1: Extract popular moments
echo "📊 Extracting popular moments..."
python3 ab/dc/analysers/cli.py $VIDEO_ID --format json > moments.json

# Step 2: Create vertical clips
echo "✂️ Creating clips..."
python3 ab/dc/downloaders/cli_clipper.py \
  --input moments.json \
  --aspect-ratio $ASPECT_RATIO \
  --output clips_result.json

# Step 3: Auto-publish to TikTok
echo "🚀 Publishing to $PLATFORM..."
python3 ab/dc/publishers/cli_publisher.py \
  --platform $PLATFORM \
  --batch-metadata clips_result.json \
  --auto-title \
  --auto-description \
  --privacy public

echo "✅ Complete workflow finished!"
```

**Run:**
```bash
chmod +x complete_workflow.sh
./complete_workflow.sh
```

## Checking Upload Status

```bash
# Check status of specific upload
python3 ab/dc/publishers/cli_publisher.py \
  --status \
  --platform tiktok \
  --upload-id v_pub_7123456789

# List recent uploads
python3 ab/dc/publishers/cli_publisher.py \
  --list \
  --platform tiktok \
  --limit 10

# Check quota usage
python3 ab/dc/publishers/cli_publisher.py \
  --quota
```

## Video Requirements

### TikTok
```
✓ Format: MP4, WebM
✓ Codec: H.264, H.265
✓ Resolution: 360p - 4K
✓ Aspect Ratio: 9:16 recommended
✓ File Size: Max 4GB
✓ Duration: 3s - 10min
✓ FPS: 23.976, 25, 29.97, 30, 60
```

### YouTube
```
✓ Format: MP4, MOV, AVI, WMV, FLV, 3GP, WebM
✓ Codec: H.264, MPEG-2, MPEG-4
✓ Resolution: 426x240 - 8K
✓ Aspect Ratio: Any (16:9 recommended)
✓ File Size: Max 256GB
✓ Duration: Max 12 hours (15min for unverified)
✓ FPS: Any
```

### Automatic Validation

The publisher automatically validates videos:

```bash
python3 ab/dc/publishers/cli_publisher.py \
  --validate \
  --video video.mp4 \
  --platform tiktok
```

**Output:**
```
Video Validation Report
=======================
File: video.mp4
Platform: TikTok

✓ Format: MP4 (valid)
✓ Codec: H.264 (valid)
✓ Resolution: 1080x1920 (valid - vertical)
✓ Aspect Ratio: 9:16 (optimal for TikTok)
✓ File Size: 16.0MB (valid, max 4GB)
✓ Duration: 40.2s (valid, 3s-10min)
✓ FPS: 23.976 (valid)

Status: ✅ Video meets all TikTok requirements
```

## Troubleshooting

### Common Issues

#### 1. "INVALID_TOKEN" Error
```bash
# Refresh authorization
python3 ab/dc/publishers/cli_publisher.py --authorize tiktok

# Or manually delete tokens to re-authorize
rm ~/.publisher_cache/tokens/tiktok_tokens.enc
```

#### 2. "RATE_LIMIT_EXCEEDED" Error
```bash
# Check current quota usage
python3 ab/dc/publishers/cli_publisher.py --quota --platform tiktok

# Wait for quota reset (TikTok: 24h, YouTube: daily at midnight PST)
```

#### 3. "VIDEO_TOO_LARGE" Error
```bash
# For TikTok (max 4GB), re-encode with lower quality:
python3 ab/dc/downloaders/cli_clipper.py \
  --input moments.json \
  --aspect-ratio 9:16 \
  --crf 28 \
  --preset fast
```

#### 4. Upload Stuck/Failed
```bash
# Check upload queue
python3 ab/dc/publishers/cli_publisher.py --queue

# Retry failed uploads
python3 ab/dc/publishers/cli_publisher.py --retry-failed

# Clear queue
python3 ab/dc/publishers/cli_publisher.py --clear-queue
```

## Advanced Features

### Custom Metadata Templates

Create `metadata_template.json`:
```json
{
  "title_templates": [
    "Epic Moment #{clip_id} 🔥",
    "You Won't Believe This! #{clip_id}",
    "Gaming Highlight #{clip_id} - Score {score}"
  ],
  "description_template": "Amazing moment from {video_id}\n\nScore: {score}/2.0\nClip: {clip_id}/{total_clips}\n\n{hashtags}",
  "hashtags": {
    "tiktok": ["#fyp", "#viral", "#gaming", "#highlights"],
    "youtube": ["#shorts", "#gaming", "#viral"]
  }
}
```

Use with random title selection:
```bash
python3 ab/dc/publishers/cli_publisher.py \
  --platform tiktok \
  --video video.mp4 \
  --metadata-template metadata_template.json \
  --random-title
```

### Analytics Tracking

```bash
# Get video analytics
python3 ab/dc/publishers/cli_publisher.py \
  --analytics \
  --platform tiktok \
  --video-id 7123456789012345678

# Export analytics to CSV
python3 ab/dc/publishers/cli_publisher.py \
  --analytics \
  --export analytics.csv \
  --date-range "2024-12-01:2024-12-05"
```

## Best Practices

### 1. Video Optimization
- Use 9:16 aspect ratio for TikTok
- Keep file size under 100MB for faster uploads
- Use H.264 codec for maximum compatibility
- Set FPS to 30 or 60 for smooth playback

### 2. Metadata Optimization
- Use relevant hashtags (5-10 per video)
- Write engaging titles (under 100 characters)
- Include call-to-action in descriptions
- Add timestamps for longer videos

### 3. Upload Strategy
- Upload during peak hours (7-9 PM local time)
- Spread uploads throughout the day
- Don't exceed 10 videos/day on TikTok
- Monitor quota usage regularly

### 4. Security
- Never commit credentials to git
- Rotate API keys every 90 days
- Use separate accounts for testing
- Enable 2FA on platform accounts

## Next Steps

1. ✅ Complete OAuth setup for both platforms
2. ✅ Run test upload with sample video
3. ✅ Create metadata templates for your use case
4. ✅ Set up automated workflows
5. ✅ Monitor analytics and optimize

## Support

- **Documentation**: See `IMPLEMENTATION_PLAN.md` and `ARCHITECTURE.md`
- **Issues**: Create issue on GitHub
- **API Docs**:
  - TikTok: https://developers.tiktok.com/doc/content-posting-api-reference-upload-video
  - YouTube: https://developers.google.com/youtube/v3/guides/uploading_a_video