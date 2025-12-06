# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python scripts for downloading Instagram videos and extracting audio. Built on `yt-dlp` for downloading and `ffmpeg` for audio processing.

## Dependencies

- **yt-dlp**: Media downloader (auto-installed by scripts if missing)
- **ffmpeg-python**: Python bindings for FFmpeg
- **ffmpeg**: System binary required for audio extraction (must be installed separately)

Install manually: `pip install yt-dlp ffmpeg-python`

## Scripts

### Video Download
- `instagram_quick_download.py` - Simple video download with minimal options
  ```bash
  python instagram_quick_download.py [URL]
  ```

### Audio Extraction
- `audio_extractor.py` - Full-featured interactive audio extractor with format/quality options
  ```bash
  python audio_extractor.py [URL_or_file]
  ```
- `quick_audio_extract.py` - Quick audio extraction to MP3
  ```bash
  python quick_audio_extract.py [source] [format]
  ```
- `batch_audio_extract.py` - Batch processing with parallel extraction support
  ```bash
  python batch_audio_extract.py
  ```

### Audio Transcription
- `transcribe_audio.py` - Transcribe audio/video files to Markdown using OpenAI Whisper
  ```bash
  python transcribe_audio.py <file> [model] [language]
  ```
  - **Models:** tiny, base, small, medium, large (larger = more accurate but slower)
  - **Languages:** pt, en, es, fr, de, etc. (or leave empty for auto-detection)

### YouTube Video Search
- `youtube_video_search.py` - Search YouTube videos with advanced filters
  ```bash
  python youtube_video_search.py [API_KEY]
  ```
  - Requires YouTube Data API v3 key from Google Cloud Console
  - Set environment variable: `export YOUTUBE_API_KEY=your_key_here`
  - **Filters:** topic, language, region, duration, views, date range, rating
  - Results saved to CSV and text file with video details

### Trend Monitoring Agent
- `trend_monitor_agent.py` - Agnostic agent for monitoring trends across multiple platforms
  ```bash
  python trend_monitor_agent.py --config config_games.json
  python trend_monitor_agent.py --topic tech
  ```
  - **Sources:** YouTube, Twitter/X, Google Search
  - **Data collected:** videos, tweets, news, articles, events
  - **Output:** CSV dataset with unified schema
  - **Use cases:** games (releases, streamers, esports), tech (launches, startups, AI), any topic

- `trend_monitor_scheduler.py` - Schedule periodic trend monitoring
  ```bash
  python trend_monitor_scheduler.py --config config_games.json --interval 6
  ```
  - Runs monitoring at specified intervals (hours)
  - Continuous data collection for trend analysis
  - Automatic CSV generation with timestamps

## Supported URL Patterns

- Posts: `https://www.instagram.com/p/XXXXX/`
- Reels: `https://www.instagram.com/reel/XXXXX/`
- IGTV: `https://www.instagram.com/tv/XXXXX/`

## Audio Formats

Supported output formats: MP3, M4A, WAV, FLAC, OGG

## Output Directories

- `downloads/` - Downloaded videos
- `audio_downloads/` - Extracted audio files
- `batch_audio/` - Batch extraction output
- `transcriptions/` - Audio transcriptions in Markdown format
- `trend_data/` - Trend monitoring datasets (CSV files)
- agno tasks related ceck @output/agno and @output/agno_data/