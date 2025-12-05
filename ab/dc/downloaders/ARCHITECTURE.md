# Video Clipper Service - Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT / API LAYER                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   CLI Tool   │  │  FastAPI     │  │   Direct     │                  │
│  │              │  │  Endpoint    │  │   Import     │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                  │                           │
│         └─────────────────┴──────────────────┘                           │
│                           │                                              │
└───────────────────────────┼──────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    VIDEO CLIPPER SERVICE CORE                            │
│                   (video_clipper_service.py)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  process_video_moments(moments_data, **options)                 │    │
│  │                                                                  │    │
│  │  1. Load Configuration (.env)                                   │    │
│  │  2. Validate Input JSON                                         │    │
│  │  3. Check Video Downloaded                                      │    │
│  │  4. Download if Needed                                          │    │
│  │  5. Create Output Directories                                   │    │
│  │  6. Cut Clips (parallel/sequential)                             │    │
│  │  7. Collect Metadata & Stats                                    │    │
│  │  8. Return Response                                             │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│         ┌──────────────┬──────────────┬──────────────┐                  │
│         │              │              │              │                   │
└─────────┼──────────────┼──────────────┼──────────────┼───────────────────┘
          │              │              │              │
          ▼              ▼              ▼              ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐
│  VIDEO          │ │   VIDEO     │ │  STORAGE    │ │   CONFIG        │
│  DOWNLOADER     │ │   CUTTER    │ │  MANAGER    │ │   MANAGER       │
│  (yt-dlp)       │ │   (ffmpeg)  │ │  (pathlib)  │ │   (.env)        │
├─────────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────────┤
│                 │ │             │ │             │ │                 │
│ • Check exists  │ │ • Cut clips │ │ • Create    │ │ • Load env vars │
│ • Download video│ │ • Parallel  │ │   dirs      │ │ • Validate      │
│ • Get metadata  │ │   process   │ │ • Generate  │ │   config        │
│ • Validate file │ │ • Validate  │ │   paths     │ │ • Get defaults  │
│                 │ │   output    │ │ • Calculate │ │                 │
│                 │ │             │ │   sizes     │ │                 │
└────────┬────────┘ └──────┬──────┘ └──────┬──────┘ └────────┬────────┘
         │                 │                │                 │
         ▼                 ▼                ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL DEPENDENCIES                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │  yt-dlp  │  │  FFmpeg  │  │   File   │  │  python- │               │
│  │          │  │          │  │  System  │  │  dotenv  │               │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘               │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
INPUT (JSON)
    │
    ├─ video_id: "RusBe_8arLQ"
    ├─ video_url: "https://youtube.com/watch?v=..."
    └─ moments: [...]
    │
    ▼
┌───────────────────┐
│  Validate Input   │  ← Check schema, video_id format, moments structure
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Check Downloaded  │  ← Look in DOWNLOADS_PATH/video_id.mp4
└─────────┬─────────┘
          │
          ├─ YES → Skip download
          │
          └─ NO
              ▼
      ┌───────────────────┐
      │  Download Video   │  ← yt-dlp with quality settings
      └─────────┬─────────┘
                │
                ▼
        ┌───────────────────┐
        │  Validate Video   │  ← Check file exists, duration, codecs
        └─────────┬─────────┘
                  │
                  ▼
          ┌───────────────────┐
          │ Create Directories│  ← STORED_PROCESSED_VIDEOS/video_id/
          └─────────┬─────────┘
                    │
                    ▼
            ┌───────────────────┐
            │  Cut Clips Loop   │
            │  (parallel/seq)   │
            └─────────┬─────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
    For Each Moment         For Each Moment
          │                       │
          ├─ start_time: 15.06    ├─ start_time: 75.30
          ├─ end_time: 45.06      ├─ end_time: 105.30
          ├─ duration: 30.0       ├─ duration: 30.0
          │                       │
          ▼                       ▼
    FFmpeg Cut              FFmpeg Cut
    video_id_0000_30s.mp4   video_id_0001_30s.mp4
          │                       │
          └───────────┬───────────┘
                      │
                      ▼
              ┌───────────────────┐
              │  Collect Metadata │  ← File sizes, paths, durations
              └─────────┬─────────┘
                        │
                        ▼
                ┌───────────────────┐
                │  Build Response   │
                └─────────┬─────────┘
                          │
                          ▼
OUTPUT (JSON)
    │
    ├─ success: true
    ├─ video_id: "RusBe_8arLQ"
    ├─ video_url: "https://..."
    ├─ clips_created: 6
    ├─ clips: [
    │    {
    │      clip_id: 0,
    │      filename: "RusBe_8arLQ_0000_30s.mp4",
    │      path: "/path/to/processed_videos/RusBe_8arLQ/...",
    │      start_time: 15.06,
    │      end_time: 45.06,
    │      duration: 30.0,
    │      score: 0.952,
    │      file_size_mb: 12.5
    │    }, ...
    │  ]
    ├─ total_size_mb: 75.3
    └─ processing_time_seconds: 45.2
```

## Module Interaction Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     VIDEO CLIPPER SERVICE                        │
│                                                                   │
│  process_video_moments()                                         │
│     │                                                             │
│     ├─► config_manager.load_config()                             │
│     │      └─► Returns: Config object                            │
│     │                                                             │
│     ├─► validate_moments_data(input_json)                        │
│     │      └─► Returns: (bool, error_msg)                        │
│     │                                                             │
│     ├─► video_downloader.is_video_downloaded(video_id)           │
│     │      └─► Returns: bool                                     │
│     │                                                             │
│     └─► IF NOT downloaded:                                       │
│            video_downloader.download_video(url, video_id)        │
│               │                                                   │
│               ├─► Execute: yt-dlp                                │
│               │      └─► Download to DOWNLOADS_PATH              │
│               │                                                   │
│               └─► video_downloader.get_video_info(path)          │
│                      └─► Returns: {duration, resolution, ...}    │
│                                                                   │
│     ├─► storage_manager.create_video_directory(video_id)         │
│     │      └─► Create: STORED_PROCESSED_VIDEOS/video_id/         │
│     │                                                             │
│     ├─► FOR EACH moment IN moments:                              │
│     │      │                                                      │
│     │      ├─► storage_manager.get_clip_path(...)                │
│     │      │      └─► Returns: output_path                       │
│     │      │                                                      │
│     │      └─► video_cutter.cut_video_segment(                   │
│     │             input_path,                                     │
│     │             output_path,                                    │
│     │             start_time,                                     │
│     │             end_time,                                       │
│     │             **codec_options                                │
│     │          )                                                  │
│     │             │                                               │
│     │             ├─► Build FFmpeg command                        │
│     │             ├─► Execute: ffmpeg                             │
│     │             └─► Validate output file                        │
│     │                    └─► Returns: bool                        │
│     │                                                             │
│     ├─► storage_manager.calculate_directory_size(video_dir)      │
│     │      └─► Returns: total_size_mb                            │
│     │                                                             │
│     └─► Build response JSON with all clip metadata               │
│            └─► Returns: response_dict                            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### 1. Video Clipper Service (Orchestrator)
```python
# Main orchestration and business logic
- Entry point for all clip creation requests
- Coordinates all submodules
- Handles high-level error recovery
- Manages workflow state
- Assembles final response
```

### 2. Video Downloader
```python
# Download management
- Check if video exists locally
- Download using yt-dlp
- Extract video metadata
- Handle download errors
- Retry logic for failed downloads
```

### 3. Video Cutter
```python
# Video processing with FFmpeg
- Build FFmpeg commands
- Execute video cuts
- Handle codec parameters
- Validate output files
- Parallel processing support
```

### 4. Storage Manager
```python
# File system operations
- Create directory structures
- Generate file paths
- Calculate storage usage
- Manage file cleanup
- Path validation and sanitization
```

### 5. Config Manager
```python
# Configuration handling
- Load .env variables
- Provide default values
- Validate configuration
- Type conversions (str → bool, int)
- Environment-specific overrides
```

## Error Handling Flow

```
┌──────────────────────┐
│  Request Received    │
└──────────┬───────────┘
           │
           ▼
    ┌──────────────┐       ┌─────────────────┐
    │  Validation  │──NO──►│ Return Error    │
    │              │       │ (400 Bad Req)   │
    └──────┬───────┘       └─────────────────┘
           │ YES
           ▼
    ┌──────────────┐       ┌─────────────────┐
    │  Download    │──FAIL►│ Retry 3x        │
    │              │       │ Exponential     │
    └──────┬───────┘       │ Backoff         │
           │ SUCCESS        └────────┬────────┘
           │                         │
           ▼                         │ ALL FAILED
    ┌──────────────┐                │
    │  Cut Clips   │◄───────────────┘
    │  (Loop)      │
    └──────┬───────┘
           │
           ├─ Clip 1 ─► Success
           ├─ Clip 2 ─► FAIL ──┐
           ├─ Clip 3 ─► Success│
           ├─ Clip 4 ─► Success│
           └─ Clip N ─► Success│
                                │
                         ┌──────▼──────┐
                         │  Log Error  │
                         │  Skip Clip  │
                         │  Continue   │
                         └──────┬──────┘
                                │
                                ▼
                    ┌───────────────────┐
                    │  Return Partial   │
                    │  Success Response │
                    │  (some clips OK)  │
                    └───────────────────┘
```

## Parallel Processing Architecture

```
┌────────────────────────────────────────────────────────────┐
│              SEQUENTIAL MODE (default for small tasks)      │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  Main Thread                                                │
│  │                                                           │
│  ├─► Cut Clip 0 ────► [█████████] ─► Done                  │
│  ├─► Cut Clip 1 ────► [█████████] ─► Done                  │
│  ├─► Cut Clip 2 ────► [█████████] ─► Done                  │
│  └─► Cut Clip 3 ────► [█████████] ─► Done                  │
│                                                              │
│  Total Time: 4 × clip_duration                              │
│                                                              │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│      PARALLEL MODE (enabled via ENABLE_PARALLEL_PROCESSING) │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  ThreadPoolExecutor (max_workers=4)                         │
│  │                                                           │
│  ├─► Worker 1: Cut Clip 0 ──► [█████████] ─► Done          │
│  ├─► Worker 2: Cut Clip 1 ──► [█████████] ─► Done          │
│  ├─► Worker 3: Cut Clip 2 ──► [█████████] ─► Done          │
│  ├─► Worker 4: Cut Clip 3 ──► [█████████] ─► Done          │
│  │                                                           │
│  ├─► Worker 1: Cut Clip 4 ──► [█████████] ─► Done          │
│  └─► Worker 2: Cut Clip 5 ──► [█████████] ─► Done          │
│                                                              │
│  Total Time: (total_clips / max_workers) × clip_duration    │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

## Directory Structure After Processing

```
project_root/
│
├── downloads/                           ← DOWNLOADS_PATH
│   ├── RusBe_8arLQ.mp4                 ← Downloaded video (kept for reuse)
│   ├── dQw4w9WgXcQ.mp4
│   └── another_video.mp4
│
├── processed_videos/                    ← STORED_PROCESSED_VIDEOS
│   ├── RusBe_8arLQ/                    ← Video ID directory
│   │   ├── RusBe_8arLQ_0000_30s.mp4   ← Clip files
│   │   ├── RusBe_8arLQ_0001_30s.mp4
│   │   ├── RusBe_8arLQ_0002_30s.mp4
│   │   ├── RusBe_8arLQ_0003_30s.mp4
│   │   ├── RusBe_8arLQ_0004_30s.mp4
│   │   └── RusBe_8arLQ_0005_30s.mp4
│   │
│   └── dQw4w9WgXcQ/
│       ├── dQw4w9WgXcQ_0000_25s.mp4
│       └── dQw4w9WgXcQ_0001_40s.mp4
│
├── temp/                                ← TEMP_PATH (optional)
│   └── (temporary processing files)
│
└── logs/                                ← LOG_FILE directory
    └── video_clipper.log
```

## API Integration Example

```python
# FastAPI endpoint combining both services
@app.post("/api/v1/extract-and-clip")
async def extract_moments_and_create_clips(url: str):
    """
    Complete workflow: Extract moments → Create clips
    """
    # Step 1: Extract popular moments
    from ab.dc.analysers.replay_heatmap import get_popular_moments

    moments_result = get_popular_moments(url)

    if not moments_result['success']:
        raise HTTPException(400, moments_result['error'])

    # Step 2: Create clips from moments
    from ab.dc.downloaders.video_clipper_service import process_video_moments

    clips_result = process_video_moments(moments_result)

    return {
        "moments": moments_result,
        "clips": clips_result
    }
```

## Performance Metrics

### Expected Processing Times

| Stage            | Sequential Time | Parallel Time (4 workers) |
|------------------|-----------------|---------------------------|
| Extract Moments  | 3-8s            | 3-8s                      |
| Download Video   | 30-120s         | 30-120s                   |
| Cut 6 Clips      | 180-360s        | 45-90s                    |
| **Total**        | **3.5-8min**    | **1.5-3.5min**            |

### Resource Usage

| Resource     | Sequential | Parallel (4 workers) |
|--------------|------------|----------------------|
| CPU Usage    | 25-50%     | 80-100%              |
| Memory       | ~500MB     | ~1GB                 |
| Disk I/O     | Moderate   | High                 |
| Network      | During DL  | During DL            |

## Security Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. INPUT VALIDATION                                         │
│     ├─ Sanitize video_id (no path traversal)                │
│     ├─ Validate video_url (whitelist YouTube domains)       │
│     ├─ Limit number of clips (max 50)                       │
│     └─ Validate timestamps (no negative, no overflow)       │
│                                                               │
│  2. RESOURCE LIMITS                                          │
│     ├─ Max video duration: 2 hours                          │
│     ├─ Max clip duration: 5 minutes                         │
│     ├─ Download timeout: 10 minutes                         │
│     ├─ Clip timeout: 2 minutes per clip                     │
│     └─ Max total size: 1GB per video                        │
│                                                               │
│  3. FILE SYSTEM SAFETY                                       │
│     ├─ Use pathlib for path operations                      │
│     ├─ Check available disk space                           │
│     ├─ Prevent overwriting system files                     │
│     └─ Sandbox all file operations                          │
│                                                               │
│  4. PROCESS ISOLATION                                        │
│     ├─ Run yt-dlp in subprocess                             │
│     ├─ Run FFmpeg in subprocess                             │
│     ├─ Timeout all subprocesses                             │
│     └─ Kill hung processes                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Monitoring & Observability

```python
# Key metrics to track
METRICS = {
    "downloads": {
        "total_downloads": 0,
        "successful_downloads": 0,
        "failed_downloads": 0,
        "avg_download_time_seconds": 0
    },
    "clips": {
        "total_clips_created": 0,
        "failed_clips": 0,
        "avg_clip_time_seconds": 0,
        "total_clips_size_mb": 0
    },
    "processing": {
        "videos_in_progress": 0,
        "avg_processing_time_seconds": 0,
        "concurrent_jobs": 0
    },
    "storage": {
        "total_disk_usage_mb": 0,
        "available_disk_space_mb": 0
    }
}
```

## Next Steps

See `video_clipper_service.md` for detailed implementation plan and code specifications.