# Video Clipper Service

Automated service for downloading YouTube videos and creating clips based on popular moments from replay heatmap analysis.

## Quick Start

```python
from ab.dc.analysers.replay_heatmap import get_popular_moments
from ab.dc.downloaders.video_clipper_service import process_video_moments

# Extract popular moments
moments = get_popular_moments('https://www.youtube.com/watch?v=RusBe_8arLQ')

# Create clips
result = process_video_moments(moments)

print(f"Created {result['clips_created']} clips in {result['processing_time_seconds']:.1f}s")
```

## Features

- ✅ Automatic video download with yt-dlp
- ✅ Skip download if video already exists
- ✅ Precise video cutting with FFmpeg
- ✅ Parallel clip processing (configurable)
- ✅ Organized file structure (video_id/clips)
- ✅ Comprehensive error handling
- ✅ Progress tracking and logging
- ✅ Configurable quality and codecs
- ✅ Subtitle download service (YouTube subtitles)
- ✅ Subtitle clipper service (generate subtitles for each clip)
- ✅ Video transcription with OpenAI Whisper

## File Structure

```
ab/dc/downloaders/
├── README.md                          # This file
├── ARCHITECTURE.md                    # Architecture diagrams and flow
├── video_clipper_service.md          # Detailed implementation plan
├── video_clipper_service.py          # Main orchestrator
├── video_downloader.py                # Download logic
├── video_cutter.py                    # FFmpeg cutting
├── video_transcriber.py               # Whisper transcription
├── subtitle_downloader.py             # Subtitle download service
├── subtitle_clipper_service.py        # Subtitle clipper for moments
├── storage_manager.py                 # File management
├── config_manager.py                  # Configuration management
├── cli_clipper.py                     # CLI tool for clipping
├── cli_transcriber.py                 # CLI tool for transcription
├── cli_subtitle.py                    # CLI tool for subtitles
├── cli_subtitle_clipper.py            # CLI tool for subtitle clipping
├── SUBTITLE_SERVICE.md                # Subtitle service documentation
├── SUBTITLE_CLIPPER_SERVICE.md        # Subtitle clipper documentation
└── TRANSCRIPTION_SERVICE.md           # Transcription service documentation
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Essential settings
DOWNLOADS_PATH=downloads/
STORED_PROCESSED_VIDEOS=processed_videos/
DOWNLOAD_QUALITY=best
VIDEO_CODEC=libx264
AUDIO_CODEC=aac

# Performance
MAX_CONCURRENT_CLIPS=4
ENABLE_PARALLEL_PROCESSING=true

# See .env.example for all options
```

## Input Format

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

## Output Format

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
      "path": "/path/to/processed_videos/RusBe_8arLQ/RusBe_8arLQ_0000_30s.mp4",
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

## File Naming Convention

- **Downloaded Videos**: `{video_id}.mp4` in `DOWNLOADS_PATH`
- **Clips**: `{video_id}_{clip_number:04d}_{duration}s.mp4` in `STORED_PROCESSED_VIDEOS/{video_id}/`

Example:
```
processed_videos/
└── RusBe_8arLQ/
    ├── RusBe_8arLQ_0000_30s.mp4
    ├── RusBe_8arLQ_0001_30s.mp4
    └── RusBe_8arLQ_0002_30s.mp4
```

## CLI Usage

```bash
# From moments JSON file
python cli_clipper.py --input moments.json

# Pipe from replay_heatmap service
python ../analysers/cli.py VIDEO_ID --format json | python cli_clipper.py

# Extract moments and create clips in one command
python cli_clipper.py --video-id RusBe_8arLQ --extract-moments

# With custom options
python cli_clipper.py --input moments.json \
  --quality 720p \
  --codec libx264 \
  --parallel \
  --output result.json
```

## API Integration

```python
from fastapi import FastAPI
from ab.dc.downloaders.video_clipper_service import process_video_moments
from ab.dc.analysers.replay_heatmap import get_popular_moments

app = FastAPI()

@app.post("/api/v1/extract-and-clip")
async def create_clips(url: str):
    # Extract moments
    moments = get_popular_moments(url)
    if not moments['success']:
        return moments

    # Create clips
    clips = process_video_moments(moments)
    return clips
```

## Dependencies

### Quick Install

**For subtitle services only:**
```bash
pip install yt-dlp
```

**For all services (video + subtitles + transcription):**
```bash
# System dependencies
brew install ffmpeg  # macOS
# or
sudo apt-get install ffmpeg  # Ubuntu/Debian

# Python packages
pip install yt-dlp ffmpeg-python python-dotenv openai-whisper torch
```

**See INSTALLATION.md for complete installation guide and troubleshooting.**

## Implementation Status

### Phase 1 - MVP (To Implement)
- [ ] Environment configuration loader
- [ ] Video downloader with yt-dlp
- [ ] Video cutter with FFmpeg
- [ ] Storage manager for paths
- [ ] Main service orchestrator
- [ ] CLI tool
- [ ] Basic error handling

### Phase 2 - Production (Planned)
- [ ] Parallel clip processing
- [ ] Progress bars and tracking
- [ ] Comprehensive error handling
- [ ] Input validation
- [ ] Logging system
- [ ] Unit tests
- [ ] Integration tests

### Phase 3 - Advanced (Future)
- [ ] Thumbnail generation
- [ ] Cloud storage (S3/GCS)
- [ ] Webhook notifications
- [ ] Quality presets
- [ ] Hardware acceleration
- [ ] Batch processing
- [ ] Resume/retry logic

## Performance

### Processing Times (Estimated)
- Extract moments: 3-8 seconds
- Download video: 30-120 seconds (depends on size)
- Cut 6 clips (sequential): 180-360 seconds
- Cut 6 clips (parallel, 4 workers): 45-90 seconds

**Total**: 1.5-8 minutes per video (depending on settings)

### Resource Usage
- **CPU**: 25-50% (sequential), 80-100% (parallel)
- **Memory**: ~500MB (sequential), ~1GB (parallel)
- **Disk**: ~100MB per 10min of source video
- **Network**: During download only

## Error Handling

The service handles common errors gracefully:
- **Video download failures**: Retry with exponential backoff (3 attempts)
- **Invalid timestamps**: Skip invalid clips, continue with valid ones
- **FFmpeg errors**: Try alternative parameters, log and continue
- **Disk space**: Check before processing, clear error messages
- **Timeout**: Kill hung processes, return partial results

## Security

- Input validation (sanitize video_id, validate URLs)
- Resource limits (max duration, clip count, timeouts)
- File system safety (pathlib, disk space checks)
- Process isolation (subprocess with timeouts)

## Additional Services

### Subtitle Download Service

Download subtitles from YouTube videos in various languages:

```bash
# List available subtitles
python cli_subtitle.py list "VIDEO_ID"

# Download English subtitle
python cli_subtitle.py download "VIDEO_ID" -l en

# Download all available subtitles
python cli_subtitle.py download "VIDEO_ID" --all

# Download with markdown export
python cli_subtitle.py download "VIDEO_ID" -l en --export-markdown
```

See **SUBTITLE_SERVICE.md** for complete documentation.

### Subtitle Clipper Service

Generate subtitle files for each video clip based on popular moments:

```bash
# Extract moments and generate subtitles
python cli_subtitle_clipper.py --video-id "VIDEO_ID" -l en -l pt

# From moments JSON file
python cli_subtitle_clipper.py --input moments.json -l en

# With aspect ratio for clip naming
python cli_subtitle_clipper.py --video-id "VIDEO_ID" -l en --aspect-ratio 9:16
```

See **SUBTITLE_CLIPPER_SERVICE.md** for complete documentation.

### Video Transcription Service

Transcribe videos using OpenAI Whisper:

```bash
# Transcribe video
python cli_transcriber.py transcribe video.mp4

# Transcribe with specific model
python cli_transcriber.py transcribe video.mp4 --model medium --language pt

# Download and transcribe from YouTube
python cli_transcriber.py from-url "VIDEO_ID" --model base
```

See **TRANSCRIPTION_SERVICE.md** for complete documentation.

## Documentation

- **INSTALLATION.md**: Complete installation guide and troubleshooting
- **ARCHITECTURE.md**: System architecture, data flow, component interaction
- **video_clipper_service.md**: Detailed implementation plan, specifications
- **SUBTITLE_SERVICE.md**: Subtitle download service documentation
- **SUBTITLE_CLIPPER_SERVICE.md**: Subtitle clipper service documentation
- **TRANSCRIPTION_SERVICE.md**: Video transcription service documentation
- **README.md**: This file (quick start and overview)

## Support

For implementation questions or issues:
1. Review ARCHITECTURE.md for system design
2. Check video_clipper_service.md for implementation details
3. See .env.example for configuration options
4. Test with CLI tool for debugging

## License

See project root LICENSE file.