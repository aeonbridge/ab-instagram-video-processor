# Auto Publisher - Automated Video Publishing

Automated video publishing service that integrates AI-generated metadata and thumbnails to publish videos to YouTube.

## Features

- Automatic video scanning and discovery
- AI-generated metadata integration (title, description, tags, category)
- AI-generated thumbnail upload
- Automatic video transcoding (AV1 → H.264) for YouTube compatibility
- OAuth 2.0 authentication with token management
- Batch publishing support
- Dry-run mode for testing
- Privacy control (public, private, unlisted)
- Smart file discovery (handles different directory structures and naming patterns)

## Installation

Ensure you have the required dependencies:

```bash
pip install python-dotenv requests
```

Make sure you have `ffmpeg` installed for video transcoding:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Configuration

### YouTube API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable **YouTube Data API v3**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Choose **Desktop app** as application type
6. Download the credentials

### Environment Variables

Add your credentials to the `.env` file in the project root:

```bash
# YouTube OAuth Configuration
YOUTUBE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret_here
YOUTUBE_REDIRECT_URI=http://localhost:8088/callback

# Optional: Custom token storage
YOUTUBE_TOKEN_FILE=.youtube_tokens.json
```

The auto publisher will automatically load these credentials from the `.env` file.

## Usage

### CLI Commands

The auto publisher provides three main commands:

#### 1. Scan - List Publishable Videos

Scan a directory to see which videos are ready for publishing:

```bash
python ab/dc/publishers/cli_auto_publisher.py scan <directory>
```

**Options:**
- `--platform youtube`: Publishing platform (default: youtube)
- `--require-metadata`: Only show videos with metadata
- `--require-thumbnail`: Only show videos with thumbnails

**Examples:**

```bash
# Scan all videos
python ab/dc/publishers/cli_auto_publisher.py scan processed_videos/VIDEO_ID/

# Show only videos with metadata and thumbnails
python ab/dc/publishers/cli_auto_publisher.py scan processed_videos/VIDEO_ID/ --require-metadata --require-thumbnail
```

**Output:**
```
======================================================================
PUBLISHABLE VIDEOS IN: processed_videos/VIDEO_ID/
======================================================================

1. video_clip_001.mp4
   Location: processed_videos/VIDEO_ID/
   Metadata: ✓
   Title: Amazing Video Title
   Category: Entertainment
   Tags: 5
   Thumbnails: 3
     1. video_clip_001_thumbnail_1.png
     2. video_clip_001_thumbnail_2.png
     3. video_clip_001_thumbnail_3.png

======================================================================
Total: 1 video(s)
======================================================================
```

#### 2. Publish - Upload Single Video

Publish a single video to YouTube:

```bash
python ab/dc/publishers/cli_auto_publisher.py publish <video_file> [options]
```

**Options:**
- `--platform youtube`: Publishing platform (default: youtube)
- `--privacy {public,private,unlisted}`: Privacy status (overrides metadata)
- `--thumbnail-index N`: Thumbnail index to use (default: 0 = first)
- `--dry-run`: Test without actually publishing

**Examples:**

```bash
# Dry run (test without publishing)
python ab/dc/publishers/cli_auto_publisher.py publish video.mp4 --dry-run

# Publish as private
python ab/dc/publishers/cli_auto_publisher.py publish video.mp4 --privacy private

# Use second thumbnail (index 1)
python ab/dc/publishers/cli_auto_publisher.py publish video.mp4 --thumbnail-index 1 --privacy public
```

**Output:**
```
======================================================================
VIDEO PUBLISHED SUCCESSFULLY!
======================================================================
Video ID: abc123xyz
URL: https://www.youtube.com/watch?v=abc123xyz
Status: uploaded
======================================================================
```

#### 3. Batch - Publish Multiple Videos

Publish multiple videos from a directory:

```bash
python ab/dc/publishers/cli_auto_publisher.py batch <directory> [options]
```

**Options:**
- `--platform youtube`: Publishing platform (default: youtube)
- `--require-metadata`: Only publish videos with metadata
- `--require-thumbnail`: Only publish videos with thumbnails
- `--privacy {public,private,unlisted}`: Privacy status for all videos (default: private)
- `--thumbnail-index N`: Thumbnail index to use (default: 0 = first)
- `--max-videos N`: Maximum number of videos to publish
- `--dry-run`: Test without actually publishing

**Examples:**

```bash
# Publish all videos as private
python ab/dc/publishers/cli_auto_publisher.py batch processed_videos/VIDEO_ID/ --privacy private

# Publish only first 3 videos
python ab/dc/publishers/cli_auto_publisher.py batch processed_videos/VIDEO_ID/ --max-videos 3 --privacy public

# Dry run to test
python ab/dc/publishers/cli_auto_publisher.py batch processed_videos/VIDEO_ID/ --dry-run

# Publish only videos with metadata AND thumbnails
python ab/dc/publishers/cli_auto_publisher.py batch processed_videos/VIDEO_ID/ \
  --require-metadata --require-thumbnail --privacy private

# Use second thumbnail for all videos
python ab/dc/publishers/cli_auto_publisher.py batch processed_videos/VIDEO_ID/ \
  --thumbnail-index 1 --privacy public
```

**Output:**
```
======================================================================
PUBLISHING RESULTS
======================================================================
1. ✓ Video ID: abc123xyz
   URL: https://www.youtube.com/watch?v=abc123xyz

2. ✓ Video ID: def456uvw
   URL: https://www.youtube.com/watch?v=def456uvw

======================================================================
Success Rate: 2/2 (100.0%)
======================================================================
```

### Programmatic Usage

You can also use the auto publisher in your Python code:

```python
from pathlib import Path
from ab.dc.publishers.auto_publisher import AutoPublisher

# Create publisher instance
publisher = AutoPublisher(
    platform='youtube',
    dry_run=False  # Set to True for testing
)

# Scan for publishable videos
videos = publisher.find_publishable_videos(
    directory=Path('processed_videos/VIDEO_ID/'),
    require_metadata=True,
    require_thumbnail=True
)

print(f"Found {len(videos)} publishable videos")

# Publish a single video
result = publisher.publish_video(
    video_info=videos[0],
    thumbnail_index=0,  # Use first thumbnail
    privacy_status='private'
)

if result.success:
    print(f"Published! URL: {result.video_url}")
    print(f"Video ID: {result.video_id}")
else:
    print(f"Error: {result.error}")

# Batch publish multiple videos
results = publisher.publish_batch(
    directory=Path('processed_videos/VIDEO_ID/'),
    require_metadata=True,
    require_thumbnail=True,
    privacy_status='private',
    max_videos=5
)

# Check results
successful = sum(1 for r in results if r.success)
print(f"Published {successful}/{len(results)} videos")
```

## Complete Workflow

The complete workflow from video processing to publishing:

```bash
# 1. Process video and extract clips
python video_clipper.py <youtube_url>

# 2. Generate AI metadata for clips
python ab/dc/publishers/agents/cli_metadata_agent.py batch processed_videos/VIDEO_ID/

# 3. Generate AI thumbnails from metadata
python ab/dc/publishers/agents/cli_thumbnail.py from-metadata processed_videos/VIDEO_ID/

# 4. Scan videos ready for publishing
python ab/dc/publishers/cli_auto_publisher.py scan processed_videos/VIDEO_ID/

# 5. Test publishing (dry-run)
python ab/dc/publishers/cli_auto_publisher.py batch processed_videos/VIDEO_ID/ \
  --dry-run --max-videos 1

# 6. Publish videos
python ab/dc/publishers/cli_auto_publisher.py batch processed_videos/VIDEO_ID/ \
  --privacy private --max-videos 5
```

## Authentication

On first use, the publisher will:

1. Open your browser for YouTube OAuth authorization
2. Ask you to sign in with your Google account
3. Request permission to upload videos
4. Save access tokens to `.youtube_tokens.json`

Subsequent runs will use the saved tokens automatically. The tokens are automatically refreshed when they expire.

## Automatic Features

The auto publisher handles these automatically:

### Video Transcoding

If your video uses an unsupported codec (like AV1), it will automatically transcode to H.264:

```
WARNING: Video codec not supported, transcoding required
INFO: Transcoding video to h264...
INFO: Original size: 21.78 MB
INFO: Transcoded size: 30.07 MB
INFO: Transcoding successful!
```

### Smart File Discovery

The publisher intelligently finds metadata and thumbnails even when they're in different directories:

- Searches current directory and parent directory
- Handles language suffixes (e.g., `_en_metadata.json`)
- Finds thumbnails in subdirectories (`thumbnails/dalle/`, `thumbnails/gemini/`)
- Supports wildcard pattern matching

### Cleanup

Temporary files (transcoded videos) are automatically cleaned up after upload.

## File Structure

Expected directory structure:

```
processed_videos/
└── VIDEO_ID/
    ├── VIDEO_ID/                    # Video files directory
    │   ├── clip_001.mp4
    │   ├── clip_002.mp4
    │   └── clip_003.mp4
    ├── clip_001_metadata.json       # Metadata files
    ├── clip_002_metadata.json
    ├── clip_003_metadata.json
    └── thumbnails/                  # Thumbnails directory
        └── dalle/                   # Provider subdirectory
            ├── clip_001_thumbnail_1.png
            ├── clip_001_thumbnail_2.png
            ├── clip_001_thumbnail_3.png
            ├── clip_002_thumbnail_1.png
            └── ...
```

The publisher is flexible and will find files even if they're in different locations or have slight naming variations.

## Metadata Format

Metadata JSON files should follow this structure:

```json
{
  "title": "Video Title",
  "description": "Video description with hashtags #tag1 #tag2",
  "tags": ["tag1", "tag2", "tag3"],
  "category": "Entertainment",
  "thumbnail_ideas": [
    {
      "concept": "Thumbnail concept description",
      "text_overlay": "Text on thumbnail",
      "color_scheme": "Blue and white"
    }
  ],
  "target_audience": "Description of target audience",
  "video_hook": "Opening hook for the video",
  "call_to_action": "CTA for viewers"
}
```

## Privacy Options

- **private**: Only you can see the video
- **unlisted**: Anyone with the link can see it (not searchable)
- **public**: Everyone can see and search for it

## Troubleshooting

### "YouTube credentials not found"

Make sure your `.env` file contains:
```bash
YOUTUBE_CLIENT_ID=your_client_id_here
YOUTUBE_CLIENT_SECRET=your_client_secret_here
```

### "Codec not supported"

The auto publisher will automatically transcode unsupported codecs. Make sure `ffmpeg` is installed.

### "Thumbnail upload failed: 413 Request Entity Too Large"

Thumbnails larger than 2MB cannot be uploaded to YouTube. The publisher should compress them automatically (feature in development).

### "Authentication failed"

Delete `.youtube_tokens.json` and try again to re-authenticate.

## Limitations

- **YouTube Quota**: YouTube API has daily quota limits (default: 10,000 units/day)
  - Each video upload costs ~1,600 units
  - You can upload ~6 videos per day with default quota
- **Video Size**: Maximum 256 GB or 12 hours duration
- **Thumbnail Size**: Maximum 2 MB (PNG, JPG, GIF)
- **Title**: Maximum 100 characters
- **Description**: Maximum 5,000 characters
- **Tags**: Maximum 500 characters total

## Support

For issues or questions:
- Check the logs for detailed error messages
- Use `--dry-run` to test without actually publishing
- Ensure your `.env` file is properly configured
- Verify YouTube API is enabled in Google Cloud Console

## License

Part of the AEON-BRIDGE ab-video-processor project.
