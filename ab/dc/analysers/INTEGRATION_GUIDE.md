# Integration Guide: YouTube Popular Moments Service

## Quick Start for API Integration

### Basic Integration (5 minutes)

```python
from replay_heatmap import get_popular_moments

# Simple usage - returns JSON-serializable dictionary
result = get_popular_moments('https://www.youtube.com/watch?v=dQw4w9WgXcQ')

if result['success']:
    # Process moments
    for moment in result['moments']:
        print(f"Popular moment at {moment['timestamp']}")
else:
    print(f"Error: {result['error']}")
```

### Flask API Example

```python
from flask import Flask, request, jsonify
from replay_heatmap import get_popular_moments

app = Flask(__name__)

@app.route('/api/moments', methods=['GET'])
def extract_moments():
    url = request.args.get('url')
    max_duration = int(request.args.get('max_duration', 40))
    min_duration = int(request.args.get('min_duration', 10))

    result = get_popular_moments(
        url_or_video_id=url,
        max_duration=max_duration,
        min_duration=min_duration
    )

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
```

### FastAPI Example (Recommended)

See `api_example.py` for a complete FastAPI implementation with:
- Interactive API documentation
- Request/response validation with Pydantic
- Type hints and OpenAPI schema
- Health check endpoints

To run:
```bash
python api_example.py
# Visit http://localhost:8000/docs for interactive API docs
```

## Response Schema

### Success Response

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

### Error Response

```json
{
  "success": false,
  "error": "No heatmap data available. Video may need 50,000+ views.",
  "video_id": "dQw4w9WgXcQ",
  "moments": [],
  "total_moments": 0
}
```

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the operation succeeded |
| `video_id` | string | YouTube video ID (11 characters) |
| `moments` | array | List of moment objects |
| `total_moments` | integer | Number of moments found |
| `error` | string/null | Error message if failed |

### Moment Object

| Field | Type | Description |
|-------|------|-------------|
| `start_time` | float | Start time in seconds |
| `end_time` | float | End time in seconds |
| `duration` | float | Duration in seconds |
| `score` | float | Engagement score (normalized, higher = more popular) |
| `timestamp` | string | Formatted timestamp (MM:SS or HH:MM:SS) |

## Configuration Parameters

### Required
- `url_or_video_id` (string): YouTube URL or 11-character video ID

### Optional
- `max_duration` (int, default=40): Maximum moment duration in seconds
- `min_duration` (int, default=10): Minimum moment duration in seconds
- `threshold` (float, default=0.45): Peak detection sensitivity (0.1-0.9)

### Parameter Guidelines

**max_duration**:
- Range: 10-300 seconds
- Recommended: 30-60 seconds for short clips
- Use case: Controls maximum length of extracted moments

**min_duration**:
- Range: 5-60 seconds
- Recommended: 10-20 seconds minimum
- Use case: Filters out very short engagement spikes

**threshold**:
- Range: 0.1-0.9
- Default: 0.45 (moderate sensitivity)
- Lower values: More moments detected (less selective)
- Higher values: Fewer moments detected (more selective)
- Recommended: 0.3-0.5 for most use cases

## Error Handling

### Common Errors

1. **Invalid URL/Video ID**
   ```json
   {
     "success": false,
     "error": "Invalid YouTube URL or video ID",
     "video_id": null
   }
   ```
   - Cause: Malformed URL or invalid video ID format
   - Solution: Validate URL/ID before calling service

2. **No Heatmap Data**
   ```json
   {
     "success": false,
     "error": "No heatmap data available. Video may need 50,000+ views.",
     "video_id": "dQw4w9WgXcQ"
   }
   ```
   - Cause: Video doesn't have enough views (typically needs 50K+)
   - Solution: Check video view count, try different video

3. **Fetch/Parse Errors**
   ```json
   {
     "success": false,
     "error": "Failed to fetch video data: ...",
     "video_id": "dQw4w9WgXcQ"
   }
   ```
   - Cause: Network issues, yt-dlp errors, malformed data
   - Solution: Retry with exponential backoff, log for debugging

### Recommended Error Handling

```python
from replay_heatmap import get_popular_moments
import time

def get_moments_with_retry(url, max_retries=3):
    """Get moments with retry logic"""
    for attempt in range(max_retries):
        result = get_popular_moments(url)

        if result['success']:
            return result

        # Don't retry for invalid URL/ID errors
        if 'Invalid YouTube URL' in result['error']:
            return result

        # Don't retry for missing heatmap data
        if 'No heatmap data' in result['error']:
            return result

        # Retry for network/parse errors
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # Exponential backoff
            time.sleep(wait_time)

    return result
```

## Performance Considerations

### Execution Time
- Average: 3-8 seconds per video
- Factors: Network speed, video length, heatmap data size
- Recommendation: Use async/background tasks for user-facing APIs

### Rate Limiting
- YouTube may rate-limit requests
- Recommendation:
  - Max 10 requests per minute per IP
  - Implement caching for frequently requested videos
  - Use request queuing for batch processing

### Caching Strategy

```python
from functools import lru_cache
from replay_heatmap import get_popular_moments

@lru_cache(maxsize=100)
def get_moments_cached(video_id, max_duration=40, min_duration=10):
    """Cached version for frequently accessed videos"""
    return get_popular_moments(video_id, max_duration, min_duration)
```

## Production Checklist

- [ ] Implement request validation
- [ ] Add rate limiting
- [ ] Set up error logging/monitoring
- [ ] Implement caching layer
- [ ] Add authentication if needed
- [ ] Set up CORS headers if web API
- [ ] Implement request timeouts
- [ ] Add health check endpoint
- [ ] Document API endpoints
- [ ] Set up CI/CD pipeline
- [ ] Review YouTube Terms of Service
- [ ] Implement analytics/usage tracking

## Example Implementations

### 1. Async FastAPI with Background Tasks

```python
from fastapi import FastAPI, BackgroundTasks
from replay_heatmap import get_popular_moments

app = FastAPI()

@app.post("/api/moments/async")
async def extract_moments_async(
    url: str,
    background_tasks: BackgroundTasks
):
    # Queue for background processing
    task_id = generate_task_id()
    background_tasks.add_task(process_video, task_id, url)
    return {"task_id": task_id, "status": "processing"}

@app.get("/api/moments/status/{task_id}")
async def get_status(task_id: str):
    # Check task status
    result = get_task_result(task_id)
    return result
```

### 2. Django View

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from replay_heatmap import get_popular_moments

@require_http_methods(["GET"])
def extract_moments_view(request):
    url = request.GET.get('url')
    if not url:
        return JsonResponse({'error': 'URL parameter required'}, status=400)

    result = get_popular_moments(url)
    status = 200 if result['success'] else 400
    return JsonResponse(result, status=status)
```

### 3. Celery Task (Async Processing)

```python
from celery import Celery
from replay_heatmap import get_popular_moments

app = Celery('tasks')

@app.task
def extract_moments_task(url):
    """Process video in background"""
    result = get_popular_moments(url)
    # Store result in database/cache
    store_result(result)
    return result
```

## Support

For issues or questions:
1. Check the README.md for basic usage
2. Review this integration guide
3. Check the technical documentation in replay_heatmap.md
4. Test with the CLI tool for debugging: `python cli.py <url>`

## Version History

- **1.0.0** (2025-01-05): Initial release
  - Core service with Goodman's algorithm
  - CLI tool
  - FastAPI example
  - Comprehensive documentation