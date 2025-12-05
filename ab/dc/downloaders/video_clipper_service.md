# Video Clipper Service - Implementation Plan

## Overview
Service that receives popular moments JSON, downloads YouTube videos (if needed), and creates clips based on start/end times.

## Architecture

### Service Flow
```
Input (JSON) → Validate → Check if Downloaded → Download (if needed) → Cut Clips → Store → Return Response
```

### Directory Structure
```
ab/dc/downloaders/
├── __init__.py
├── video_clipper_service.py      # Main service
├── video_downloader.py            # Download logic
├── video_cutter.py                # FFmpeg cutting logic
├── storage_manager.py             # File management
└── cli_clipper.py                 # CLI tool
```

## Input Schema

### JSON Request Format
```json
{
  "video_id": "RusBe_8arLQ",
  "video_url": "https://www.youtube.com/watch?v=RusBe_8arLQ",
  "moments": [
    {
      "start_time": 15.06,
      "end_time": 45.06,
      "duration": 30.0,
      "score": 0.952,
      "timestamp": "0:15"
    }
  ]
}
```

## Output Schema

### Success Response
```json
{
  "success": true,
  "video_id": "RusBe_8arLQ",
  "video_url": "https://www.youtube.com/watch?v=RusBe_8arLQ",
  "video_downloaded": true,
  "video_path": "/path/to/downloads/RusBe_8arLQ.mp4",
  "clips_created": 6,
  "clips": [
    {
      "clip_id": 0,
      "filename": "RusBe_8arLQ_0000_30s.mp4",
      "path": "/path/to/stored/RusBe_8arLQ/RusBe_8arLQ_0000_30s.mp4",
      "start_time": 15.06,
      "end_time": 45.06,
      "duration": 30.0,
      "score": 0.952,
      "file_size_mb": 12.5
    }
  ],
  "total_size_mb": 75.3,
  "processing_time_seconds": 45.2
}
```

### Error Response
```json
{
  "success": false,
  "error": "Failed to download video",
  "video_id": "RusBe_8arLQ",
  "video_url": "https://www.youtube.com/watch?v=RusBe_8arLQ"
}
```

## File Naming Convention

### Downloaded Video
- Location: `downloads/` (configurable via env)
- Format: `{video_id}.mp4`
- Example: `RusBe_8arLQ.mp4`

### Processed Clips
- Location: `STORED_PROCESSED_VIDEOS/{video_id}/`
- Format: `{video_id}_{clip_number:04d}_{duration}s.mp4`
- Examples:
  - `RusBe_8arLQ_0000_30s.mp4`
  - `RusBe_8arLQ_0001_40s.mp4`
  - `RusBe_8arLQ_0002_25s.mp4`

### Directory Structure Example
```
STORED_PROCESSED_VIDEOS/
└── RusBe_8arLQ/
    ├── RusBe_8arLQ_0000_30s.mp4
    ├── RusBe_8arLQ_0001_30s.mp4
    ├── RusBe_8arLQ_0002_30s.mp4
    ├── RusBe_8arLQ_0003_30s.mp4
    ├── RusBe_8arLQ_0004_30s.mp4
    └── RusBe_8arLQ_0005_30s.mp4
```

## Environment Configuration

### .env Variables
```bash
# Download directory
DOWNLOADS_PATH=downloads/

# Processed videos storage
STORED_PROCESSED_VIDEOS=processed_videos/

# Video quality (best, 1080p, 720p, 480p, worst)
DOWNLOAD_QUALITY=best

# FFmpeg binary path (optional, uses system ffmpeg if not set)
FFMPEG_PATH=ffmpeg

# Temp directory for processing
TEMP_PATH=temp/

# Enable/disable audio in clips
INCLUDE_AUDIO=true

# Video codec for clips (libx264, libx265, copy)
VIDEO_CODEC=libx264

# Audio codec for clips (aac, mp3, copy)
AUDIO_CODEC=aac

# CRF quality for encoding (18-28, lower = better quality)
CRF_QUALITY=23
```

## Implementation Details

### 1. Video Downloader (`video_downloader.py`)

**Responsibilities:**
- Check if video already exists locally
- Download video using yt-dlp
- Validate downloaded video
- Return video path

**Key Functions:**
```python
def is_video_downloaded(video_id: str, downloads_path: str) -> bool:
    """Check if video already exists"""

def download_video(video_url: str, video_id: str, downloads_path: str, quality: str = 'best') -> str:
    """Download video and return path"""

def get_video_info(video_path: str) -> dict:
    """Get video metadata (duration, resolution, codec)"""
```

**yt-dlp Command:**
```bash
yt-dlp \
  -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
  -o "downloads/%(id)s.%(ext)s" \
  --merge-output-format mp4 \
  <VIDEO_URL>
```

### 2. Video Cutter (`video_cutter.py`)

**Responsibilities:**
- Cut video segments using FFmpeg
- Create clips with precise timestamps
- Handle audio/video codec options
- Validate output files

**Key Functions:**
```python
def cut_video_segment(
    input_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    video_codec: str = 'libx264',
    audio_codec: str = 'aac',
    crf: int = 23,
    include_audio: bool = True
) -> bool:
    """Cut a single segment from video"""

def batch_cut_videos(
    input_path: str,
    output_dir: str,
    moments: list,
    video_id: str,
    **kwargs
) -> list:
    """Cut multiple segments and return clip info"""
```

**FFmpeg Command (Fast, Stream Copy):**
```bash
ffmpeg -ss <START_TIME> -i <INPUT> -t <DURATION> -c copy -avoid_negative_ts make_zero <OUTPUT>
```

**FFmpeg Command (Re-encode for Precision):**
```bash
ffmpeg -i <INPUT> -ss <START_TIME> -to <END_TIME> \
  -c:v libx264 -crf 23 -preset medium \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  <OUTPUT>
```

### 3. Storage Manager (`storage_manager.py`)

**Responsibilities:**
- Create directory structure
- Manage file paths
- Clean up old files (optional)
- Calculate storage usage

**Key Functions:**
```python
def create_video_directory(video_id: str, base_path: str) -> str:
    """Create directory for video clips"""

def get_clip_path(video_id: str, clip_number: int, duration: float, base_path: str) -> str:
    """Generate clip file path"""

def calculate_directory_size(path: str) -> float:
    """Calculate total size in MB"""

def cleanup_old_clips(video_id: str, base_path: str) -> bool:
    """Remove existing clips for re-processing"""
```

### 4. Main Service (`video_clipper_service.py`)

**Responsibilities:**
- Orchestrate entire workflow
- Validate input JSON
- Handle errors gracefully
- Return structured response

**Key Functions:**
```python
def process_video_moments(
    moments_data: dict,
    downloads_path: str = None,
    storage_path: str = None,
    force_redownload: bool = False,
    force_reprocess: bool = False,
    **ffmpeg_options
) -> dict:
    """
    Main service function

    Args:
        moments_data: JSON with video_id, video_url, moments
        downloads_path: Override downloads directory
        storage_path: Override storage directory
        force_redownload: Re-download even if exists
        force_reprocess: Re-cut clips even if exist
        **ffmpeg_options: video_codec, audio_codec, crf, etc.

    Returns:
        Response dict with success, clips, paths
    """
```

**Workflow Steps:**
1. Load environment variables
2. Validate input JSON schema
3. Check if video is downloaded
4. Download video if needed
5. Create output directory structure
6. Cut clips from video (parallel processing possible)
7. Calculate file sizes and metadata
8. Return response with clip information

### 5. CLI Tool (`cli_clipper.py`)

**Features:**
- Accept JSON file or pipe from replay_heatmap service
- Display progress bars for downloads and cuts
- Save response to output file
- Interactive mode

**Usage Examples:**
```bash
# From JSON file
python cli_clipper.py --input moments.json

# Pipe from replay_heatmap
python ../analysers/cli.py RusBe_8arLQ --format json | python cli_clipper.py

# With options
python cli_clipper.py --input moments.json --output result.json --quality 720p --force-reprocess

# Direct integration
python cli_clipper.py --video-id RusBe_8arLQ --extract-moments
```

## Error Handling

### Common Errors

1. **Video Download Failure**
   - Cause: Network issues, invalid URL, geo-restrictions
   - Action: Retry with exponential backoff (3 attempts)
   - Response: Include error details

2. **FFmpeg Errors**
   - Cause: Invalid timestamps, codec issues, corrupt video
   - Action: Try alternative ffmpeg parameters
   - Response: Skip problematic clips, continue with others

3. **Disk Space Issues**
   - Cause: Insufficient storage
   - Action: Check available space before processing
   - Response: Clear error message with space requirements

4. **Invalid Moments**
   - Cause: Start time > video duration, invalid timestamps
   - Action: Validate and skip invalid moments
   - Response: Include validation warnings

### Validation Rules

```python
def validate_moments_data(data: dict) -> tuple[bool, str]:
    """
    Validate input data

    Checks:
    - Required fields: video_id, video_url, moments
    - video_id format (11 chars)
    - video_url format (valid YouTube URL)
    - moments is non-empty list
    - Each moment has start_time, end_time, duration
    - start_time < end_time
    - Times are non-negative
    """
```

## Performance Considerations

### Parallel Processing
- Cut multiple clips in parallel using ThreadPoolExecutor
- Default: 4 concurrent FFmpeg processes
- Configurable via environment variable

### Stream Copy vs Re-encode
- **Stream Copy** (fast, ~10s per clip):
  - Pros: Very fast, no quality loss
  - Cons: Less precise timestamps, may include keyframe gaps
  - Use case: Quick previews, internal processing

- **Re-encode** (slower, ~30-60s per clip):
  - Pros: Frame-accurate cuts, consistent quality
  - Cons: Slower, slight quality loss from re-encoding
  - Use case: Production clips, exact timing required

### Caching Strategy
- Keep downloaded videos in cache
- Implement LRU cache for video files
- Configurable cache size limit
- Clean up old downloads automatically

## Integration with Replay Heatmap Service

### Combined Workflow

```python
from ab.dc.analysers.replay_heatmap import get_popular_moments
from ab.dc.downloaders.video_clipper_service import process_video_moments

# Step 1: Extract moments
moments_result = get_popular_moments('https://www.youtube.com/watch?v=RusBe_8arLQ')

if moments_result['success']:
    # Step 2: Create clips
    clips_result = process_video_moments(moments_result)

    if clips_result['success']:
        print(f"Created {clips_result['clips_created']} clips")
        for clip in clips_result['clips']:
            print(f"  - {clip['filename']}: {clip['duration']}s")
```

### API Endpoint Example

```python
@app.post("/api/v1/create-clips")
async def create_clips_from_url(
    url: str,
    quality: str = "best",
    force_reprocess: bool = False
):
    # Extract moments
    moments = get_popular_moments(url)

    if not moments['success']:
        raise HTTPException(400, moments['error'])

    # Create clips
    result = process_video_moments(
        moments,
        force_reprocess=force_reprocess
    )

    return result
```

## Dependencies

### Python Packages
```
yt-dlp>=2023.10.0
ffmpeg-python>=0.2.0
python-dotenv>=1.0.0
pydantic>=2.0.0  # For validation
tqdm>=4.65.0     # For progress bars
```

### System Requirements
- FFmpeg installed (with libx264, aac codecs)
- Sufficient disk space (estimate: video size × 0.3 per clip)
- Python 3.8+

## Testing Strategy

### Unit Tests
```python
# test_video_downloader.py
def test_is_video_downloaded()
def test_download_video()
def test_get_video_info()

# test_video_cutter.py
def test_cut_video_segment()
def test_batch_cut_videos()
def test_invalid_timestamps()

# test_storage_manager.py
def test_create_video_directory()
def test_get_clip_path()
def test_cleanup_old_clips()

# test_video_clipper_service.py
def test_process_video_moments()
def test_validate_moments_data()
def test_error_handling()
```

### Integration Tests
- End-to-end test with real video
- Test with various moment configurations
- Test error scenarios (network failure, invalid video, etc.)

## Security Considerations

### Input Validation
- Sanitize video_id to prevent directory traversal
- Validate video URLs (only allow YouTube domains)
- Limit number of clips per request (max 50)
- Validate timestamp ranges

### File System Safety
- Use pathlib for safe path operations
- Check available disk space before processing
- Implement file size limits
- Prevent overwriting system files

### Resource Limits
- Max video duration: 2 hours
- Max clip duration: 5 minutes
- Max total clips size: 1GB per video
- Timeout for downloads: 10 minutes
- Timeout for each clip: 2 minutes

## Monitoring & Logging

### Logging Strategy
```python
import logging

logger = logging.getLogger('video_clipper')

# Log levels:
# - INFO: Start/complete processing, clip creation
# - WARNING: Skipped clips, validation issues
# - ERROR: Download failures, FFmpeg errors
# - DEBUG: Detailed FFmpeg commands, file operations
```

### Metrics to Track
- Total videos processed
- Total clips created
- Average processing time per clip
- Disk space usage
- Error rates by type
- Download success rate

## Future Enhancements

### Phase 2 Features
1. **Thumbnail Generation**: Create thumbnail for each clip
2. **Video Preview**: Generate animated GIFs or WebM previews
3. **Metadata Extraction**: Add video title, description, tags
4. **Subtitle Support**: Include captions in clips
5. **Quality Presets**: Add preset profiles (mobile, web, high-quality)
6. **Batch Processing**: Process multiple videos in one request
7. **Cloud Storage**: Upload clips to S3/GCS
8. **Webhook Notifications**: Notify when processing completes
9. **Resume Support**: Resume failed/interrupted processing
10. **Video Watermarking**: Add custom watermarks to clips

### Optimization Ideas
- Use hardware acceleration (NVENC, VideoToolbox)
- Implement distributed processing
- Add Redis queue for async processing
- Create clip previews without full re-encode
- Smart caching with deduplication

## Implementation Priority

### Phase 1 (MVP)
1. ✅ Environment configuration and .env setup
2. ✅ Video downloader with yt-dlp
3. ✅ Basic FFmpeg video cutting
4. ✅ Storage manager for file organization
5. ✅ Main service orchestration
6. ✅ CLI tool for testing
7. ✅ Basic error handling

### Phase 2 (Production Ready)
1. Parallel clip processing
2. Progress tracking and reporting
3. Comprehensive error handling
4. Input validation and sanitization
5. Logging and monitoring
6. Unit and integration tests
7. API endpoint integration

### Phase 3 (Advanced Features)
1. Thumbnail generation
2. Cloud storage integration
3. Webhook notifications
4. Advanced quality presets
5. Hardware acceleration
6. Batch processing
7. Resume/retry logic

## File Size Estimates

For a typical YouTube video:
- **Original Video**: ~100MB per 10 minutes (720p)
- **Single Clip (30s)**: ~10-15MB (re-encoded)
- **Single Clip (30s)**: ~5MB (stream copy)
- **6 Clips per video**: ~30-90MB total

Example storage requirements:
- 100 videos with 6 clips each = ~3-9GB
- 1000 videos with 6 clips each = ~30-90GB

## Success Criteria

### MVP Success Metrics
- ✅ Successfully download 95%+ of valid YouTube videos
- ✅ Create clips with <5s timestamp accuracy
- ✅ Process 6 clips in <2 minutes (with re-encode)
- ✅ Handle errors gracefully without crashes
- ✅ Generate correct file names and directory structure

### Production Success Metrics
- ✅ 99%+ uptime for service
- ✅ Process 100+ videos per hour
- ✅ <1% clip creation failure rate
- ✅ Automated error recovery
- ✅ Comprehensive logging and monitoring