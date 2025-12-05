# YouTube Popular Moments Extractor

Service for extracting popular moments from YouTube videos using heatmap data and Dan Goodman's peak detection algorithm.

## Features

- ✅ Extract popular moments from YouTube videos
- ✅ Support for multiple URL formats (full URL, youtu.be, video ID)
- ✅ Configurable duration and threshold parameters
- ✅ JSON API response format
- ✅ CLI tool for command-line usage
- ✅ FastAPI example for REST API integration
- ✅ Formatted timestamps (MM:SS or HH:MM:SS)

## Requirements

- Python 3.8+
- yt-dlp (automatically installed by scripts if missing)
- Dependencies: `subprocess`, `json`, `re`, `typing`

## Installation

```bash
# Clone or download the files
cd ab/dc/analysers

# Optional: Install FastAPI for API server
pip install fastapi uvicorn
```

## Usage

### 1. As a Python Module

```python
from replay_heatmap import get_popular_moments
import json

# Extract moments from a video
result = get_popular_moments(
    url_or_video_id='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    max_duration=40,    # Maximum moment duration in seconds
    min_duration=10,    # Minimum moment duration in seconds
    threshold=0.45      # Peak detection threshold (0.1-0.9)
)

# Print results
print(json.dumps(result, indent=2))

# Access data
if result['success']:
    print(f"Found {result['total_moments']} moments")
    for moment in result['moments']:
        print(f"  [{moment['timestamp']}] "
              f"{moment['start_time']}s - {moment['end_time']}s "
              f"(score: {moment['score']})")
else:
    print(f"Error: {result['error']}")
```

### 2. Command-Line Interface

```bash
# Basic usage
python cli.py "https://www.youtube.com/watch?v=RusBe_8arLQ"

# With custom parameters
python cli.py RusBe_8arLQ --max-duration 60 --min-duration 15

# JSON output
python cli.py RusBe_8arLQ --format json --output moments.json

# CSV output
python cli.py RusBe_8arLQ --format csv --output moments.csv

# Help
python cli.py --help
```

### 3. REST API Server

```bash
# Start the API server
python api_example.py

# The server runs on http://localhost:8000
# - API docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc

# Example request
curl 'http://localhost:8000/api/v1/moments?url=RusBe_8arLQ'

# With parameters
curl 'http://localhost:8000/api/v1/moments?url=RusBe_8arLQ&max_duration=30&min_duration=10&threshold=0.45'
```

## API Response Format

```json
{
  "success": true,
  "video_id": "RusBe_8arLQ",
  "moments": [
    {
      "start_time": 15.06,
      "end_time": 45.06,
      "duration": 30.0,
      "score": 0.952,
      "timestamp": "0:15"
    }
  ],
  "total_moments": 6,
  "error": null
}
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url_or_video_id` | string | required | YouTube URL or video ID |
| `max_duration` | int | 40 | Maximum moment duration (10-300 seconds) |
| `min_duration` | int | 10 | Minimum moment duration (5-60 seconds) |
| `threshold` | float | 0.45 | Peak detection threshold (0.1-0.9, lower = more moments) |

## Supported URL Formats

- Full URL: `https://www.youtube.com/watch?v=VIDEO_ID`
- Short URL: `https://youtu.be/VIDEO_ID`
- Embed URL: `https://www.youtube.com/embed/VIDEO_ID`
- Direct ID: `VIDEO_ID` (11 characters)

## Algorithm

The service implements Dan Goodman's algorithm for detecting popular moments:

1. **Data Extraction**: Fetch heatmap data from YouTube using yt-dlp
2. **Smoothing**: Apply weighted average smoothing to reduce noise
3. **Peak Detection**: Identify local maxima above threshold
4. **Grouping**: Merge nearby peaks into unified moments
5. **Filtering**: Apply duration constraints (min/max)

## Requirements for Heatmap Data

- Videos typically need **50,000+ views** for heatmap data
- Heatmap data may not be available for all videos
- Best results on videos **5-7+ days old with 90K+ views**

## Error Handling

The service returns structured error responses:

```json
{
  "success": false,
  "error": "No heatmap data available. Video may need 50,000+ views.",
  "video_id": "VIDEO_ID",
  "moments": [],
  "total_moments": 0
}
```

Common errors:
- Invalid URL or video ID
- No heatmap data available (insufficient views)
- Failed to fetch video data
- Failed to parse heatmap data

## Integration Example (FastAPI)

```python
from fastapi import FastAPI, Query
from replay_heatmap import get_popular_moments

app = FastAPI()

@app.get("/moments")
async def get_moments(url: str = Query(...)):
    result = get_popular_moments(url)
    return result
```

## Integration Example (Flask)

```python
from flask import Flask, request, jsonify
from replay_heatmap import get_popular_moments

app = Flask(__name__)

@app.route('/moments')
def get_moments():
    url = request.args.get('url')
    result = get_popular_moments(url)
    return jsonify(result)
```

## Files

- `replay_heatmap.py` - Core service module
- `replay_heatmap.md` - Technical documentation
- `cli.py` - Command-line interface
- `api_example.py` - FastAPI REST API example
- `README.md` - This file

## Legal Considerations

This tool uses yt-dlp to extract publicly available heatmap data from YouTube. Please review YouTube's Terms of Service before using in production. The tool is intended for:

- Research and analysis
- Personal use
- Internal tools
- Educational purposes

For production systems requiring compliance, consider:
- Processing user-uploaded content instead of scraping
- Using official YouTube Data API where possible
- Implementing appropriate rate limiting
- Respecting robots.txt and Terms of Service

## References

- Dan Goodman's Peak Detection Algorithm (October 2022)
- YouTube "Most Replayed" Feature Documentation
- yt-dlp: https://github.com/yt-dlp/yt-dlp

## License

See project root LICENSE file.