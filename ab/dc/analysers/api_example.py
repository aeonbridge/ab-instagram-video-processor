"""
Example FastAPI wrapper for the YouTube Heatmap and Video Clipper Services
This demonstrates how to integrate both services into a REST API.

Usage:
    pip install fastapi uvicorn
    python api_example.py

    # Then visit: http://localhost:8000/docs for interactive API documentation
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'downloaders'))

# Import the services
from replay_heatmap import get_popular_moments, get_video_metadata, extract_video_id
from video_clipper_service import process_video_moments


# Pydantic models for request/response validation
class MomentResponse(BaseModel):
    """Individual moment data"""
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    duration: float = Field(..., description="Duration in seconds")
    score: float = Field(..., description="Engagement score (normalized)")
    timestamp: str = Field(..., description="Formatted timestamp (MM:SS or HH:MM:SS)")


class PopularMomentsResponse(BaseModel):
    """Response model for popular moments endpoint"""
    success: bool = Field(..., description="Whether the request was successful")
    video_id: Optional[str] = Field(None, description="YouTube video ID")
    video_url: Optional[str] = Field(None, description="YouTube video URL")
    moments: List[MomentResponse] = Field(default_factory=list, description="List of popular moments")
    total_moments: int = Field(..., description="Total number of moments found")
    error: Optional[str] = Field(None, description="Error message if success=False")


class ClipInfo(BaseModel):
    """Individual clip information"""
    clip_id: int = Field(..., description="Clip number")
    filename: str = Field(..., description="Clip filename")
    path: str = Field(..., description="Full path to clip file")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    duration: float = Field(..., description="Clip duration in seconds")
    score: float = Field(..., description="Engagement score")
    file_size_mb: float = Field(..., description="File size in MB")


class CreateClipsResponse(BaseModel):
    """Response model for create clips endpoint"""
    success: bool = Field(..., description="Whether the request was successful")
    video_id: str = Field(..., description="YouTube video ID")
    video_url: str = Field(..., description="YouTube video URL")
    video_downloaded: bool = Field(..., description="Whether video was downloaded in this request")
    video_path: str = Field(..., description="Path to downloaded video")
    clips_created: int = Field(..., description="Number of clips successfully created")
    clips_failed: int = Field(..., description="Number of clips that failed")
    clips: List[ClipInfo] = Field(default_factory=list, description="List of created clips")
    failed_clips: Optional[List[Dict[str, Any]]] = Field(None, description="List of failed clips with errors")
    total_size_mb: float = Field(..., description="Total size of all clips in MB")
    processing_time_seconds: float = Field(..., description="Total processing time in seconds")
    error: Optional[str] = Field(None, description="Error message if success=False")


class VideoMetadata(BaseModel):
    """Video metadata information"""
    title: str = Field(..., description="Video title")
    description: str = Field(..., description="Video description")
    tags: List[str] = Field(default_factory=list, description="Video tags")
    duration: int = Field(..., description="Video duration in seconds")
    view_count: int = Field(..., description="Total view count")
    like_count: int = Field(..., description="Total like count")
    comment_count: int = Field(..., description="Total comment count")
    upload_date: Optional[str] = Field(None, description="Upload date (ISO format)")
    video_age_days: Optional[int] = Field(None, description="Video age in days")
    analysis_date: str = Field(..., description="Analysis date (ISO format)")
    channel: str = Field(..., description="Channel name")
    channel_id: str = Field(..., description="Channel ID")
    channel_url: str = Field(..., description="Channel URL")
    thumbnail: str = Field(..., description="Thumbnail URL")
    webpage_url: str = Field(..., description="Video webpage URL")


class VideoAnalysisResponse(BaseModel):
    """Response model for video analysis endpoint (metadata + moments)"""
    success: bool = Field(..., description="Whether the request was successful")
    video_id: str = Field(..., description="YouTube video ID")
    video_url: str = Field(..., description="YouTube video URL")
    metadata: Optional[VideoMetadata] = Field(None, description="Video metadata")
    moments: List[MomentResponse] = Field(default_factory=list, description="List of popular moments")
    total_moments: int = Field(..., description="Total number of moments found")
    error: Optional[str] = Field(None, description="Error message if success=False")


# Initialize FastAPI app
app = FastAPI(
    title="YouTube Video Processing API",
    description="Extract popular moments from YouTube videos and create video clips",
    version="2.0.0"
)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "YouTube Video Processing API",
        "version": "2.0.0",
        "endpoints": {
            "analyze": "/api/v1/analyze",
            "moments": "/api/v1/moments",
            "clips": "/api/v1/clips",
            "process": "/api/v1/process",
            "health": "/api/v1/health",
            "docs": "/docs"
        }
    }


@app.get("/api/v1/analyze", response_model=VideoAnalysisResponse)
async def analyze_video(
    url: str = Query(..., description="YouTube URL or video ID"),
    max_duration: int = Query(40, ge=10, le=300, description="Maximum moment duration in seconds"),
    min_duration: int = Query(10, ge=5, le=60, description="Minimum moment duration in seconds"),
    threshold: float = Query(0.45, ge=0.1, le=0.9, description="Peak detection threshold (0.1-0.9)")
):
    """
    Analyze a YouTube video - get metadata and popular moments.

    This endpoint provides complete video analysis combining:
    1. Video metadata (title, description, views, likes, channel info, etc.)
    2. Popular moments detected from heatmap data

    **Parameters:**
    - **url**: YouTube URL (any format) or direct video ID
    - **max_duration**: Maximum duration for each moment (10-300 seconds)
    - **min_duration**: Minimum duration for each moment (5-60 seconds)
    - **threshold**: Sensitivity for peak detection (lower = more moments)

    **Example URLs:**
    - `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
    - `https://youtu.be/dQw4w9WgXcQ`
    - `dQw4w9WgXcQ` (direct video ID)

    **Returns:**
    - JSON with video metadata and list of popular moments with timestamps

    **Use Cases:**
    - Content analysis and research
    - Video discovery and recommendation systems
    - Marketing and trend analysis
    - Content creation planning
    """
    try:
        # Extract video ID
        video_id = extract_video_id(url)
        if not video_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid YouTube URL or video ID"
            )

        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Get video metadata
        try:
            metadata = get_video_metadata(video_id)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch video metadata: {str(e)}"
            )

        # Get popular moments
        moments_result = get_popular_moments(
            url_or_video_id=url,
            max_duration=max_duration,
            min_duration=min_duration,
            threshold=threshold
        )

        if not moments_result.get('success'):
            # Return partial result with metadata only
            return JSONResponse(content={
                "success": True,
                "video_id": video_id,
                "video_url": video_url,
                "metadata": metadata,
                "moments": [],
                "total_moments": 0,
                "error": f"Failed to extract moments: {moments_result.get('error', 'Unknown error')}"
            })

        # Return complete result
        return JSONResponse(content={
            "success": True,
            "video_id": video_id,
            "video_url": video_url,
            "metadata": metadata,
            "moments": moments_result.get('moments', []),
            "total_moments": moments_result.get('total_moments', 0),
            "error": None
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/v1/moments", response_model=PopularMomentsResponse)
async def get_moments(
    url: str = Query(..., description="YouTube URL or video ID"),
    max_duration: int = Query(40, ge=10, le=300, description="Maximum moment duration in seconds"),
    min_duration: int = Query(10, ge=5, le=60, description="Minimum moment duration in seconds"),
    threshold: float = Query(0.45, ge=0.1, le=0.9, description="Peak detection threshold (0.1-0.9)")
):
    """
    Extract popular moments from a YouTube video using heatmap data.

    **Parameters:**
    - **url**: YouTube URL (any format) or direct video ID
    - **max_duration**: Maximum duration for each moment (10-300 seconds)
    - **min_duration**: Minimum duration for each moment (5-60 seconds)
    - **threshold**: Sensitivity for peak detection (lower = more moments)

    **Example URLs:**
    - `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
    - `https://youtu.be/dQw4w9WgXcQ`
    - `dQw4w9WgXcQ` (direct video ID)

    **Returns:**
    - JSON with success status, video ID, and list of popular moments
    """
    try:
        # Call the service
        result = get_popular_moments(
            url_or_video_id=url,
            max_duration=max_duration,
            min_duration=min_duration,
            threshold=threshold
        )

        # Return the result
        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/api/v1/clips", response_model=CreateClipsResponse)
async def create_clips(
    url: str = Query(..., description="YouTube URL or video ID"),
    max_duration: int = Query(40, ge=10, le=300, description="Maximum moment duration in seconds"),
    min_duration: int = Query(10, ge=5, le=60, description="Minimum moment duration in seconds"),
    threshold: float = Query(0.45, ge=0.1, le=0.9, description="Peak detection threshold (0.1-0.9)"),
    force_redownload: bool = Query(False, description="Force re-download video even if exists"),
    force_reprocess: bool = Query(False, description="Force re-process clips even if they exist"),
    video_codec: Optional[str] = Query(None, description="Video codec (libx264, copy) - uses .env default if not specified"),
    audio_codec: Optional[str] = Query(None, description="Audio codec (aac, copy) - uses .env default if not specified")
):
    """
    Create video clips from popular moments.

    This endpoint combines moment detection and clip creation:
    1. Analyzes the video to find popular moments using heatmap data
    2. Downloads the video if not already downloaded
    3. Creates clips for each popular moment

    **Parameters:**
    - **url**: YouTube URL or video ID
    - **max_duration**: Maximum clip duration (10-300 seconds)
    - **min_duration**: Minimum clip duration (5-60 seconds)
    - **threshold**: Peak detection sensitivity (0.1-0.9, lower = more clips)
    - **force_redownload**: Re-download video even if exists
    - **force_reprocess**: Re-create clips even if they exist
    - **video_codec**: Override video codec (libx264 for re-encoding, copy for fast stream copy)
    - **audio_codec**: Override audio codec (aac for re-encoding, copy for fast stream copy)

    **Returns:**
    - JSON with clip creation results including file paths and sizes

    **Performance Tips:**
    - Use `video_codec=copy` and `audio_codec=copy` for 4K videos (240x faster)
    - Use `video_codec=libx264` for maximum compatibility with YouTube
    - Processing time varies: ~5 seconds with copy, ~20 minutes with re-encoding for 4K
    """
    try:
        # Step 1: Get popular moments
        moments_result = get_popular_moments(
            url_or_video_id=url,
            max_duration=max_duration,
            min_duration=min_duration,
            threshold=threshold
        )

        if not moments_result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract moments: {moments_result.get('error', 'Unknown error')}"
            )

        # Step 2: Prepare data for clipper service
        moments_data = {
            'video_id': moments_result['video_id'],
            'video_url': moments_result['video_url'],
            'moments': moments_result['moments']
        }

        # Step 3: Create FFmpeg options if codecs specified
        ffmpeg_options = {}
        if video_codec:
            ffmpeg_options['video_codec'] = video_codec
        if audio_codec:
            ffmpeg_options['audio_codec'] = audio_codec

        # Step 4: Process video and create clips
        result = process_video_moments(
            moments_data=moments_data,
            force_redownload=force_redownload,
            force_reprocess=force_reprocess,
            **ffmpeg_options
        )

        # Return the result
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/v1/process")
async def process_video(
    url: str = Query(..., description="YouTube URL or video ID"),
    max_duration: int = Query(40, ge=10, le=300, description="Maximum moment duration in seconds"),
    min_duration: int = Query(10, ge=5, le=60, description="Minimum moment duration in seconds"),
    threshold: float = Query(0.45, ge=0.1, le=0.9, description="Peak detection threshold (0.1-0.9)"),
    create_clips: bool = Query(False, description="Create video clips after finding moments")
):
    """
    Process a YouTube video - find moments and optionally create clips.

    **Simple Endpoint:**
    - Set `create_clips=false` (default) to only find popular moments
    - Set `create_clips=true` to find moments AND create video clips

    **Parameters:**
    - **url**: YouTube URL or video ID
    - **max_duration**: Maximum duration per moment/clip
    - **min_duration**: Minimum duration per moment/clip
    - **threshold**: Peak detection sensitivity (lower = more moments)
    - **create_clips**: Whether to create video clips (default: false)

    **Examples:**
    - Find moments only: `?url=RusBe_8arLQ`
    - Find moments and create clips: `?url=RusBe_8arLQ&create_clips=true`

    **Returns:**
    - If `create_clips=false`: List of popular moments
    - If `create_clips=true`: Clip creation results with file paths
    """
    try:
        if create_clips:
            # Use the clips endpoint logic
            moments_result = get_popular_moments(
                url_or_video_id=url,
                max_duration=max_duration,
                min_duration=min_duration,
                threshold=threshold
            )

            if not moments_result.get('success'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to extract moments: {moments_result.get('error', 'Unknown error')}"
                )

            moments_data = {
                'video_id': moments_result['video_id'],
                'video_url': moments_result['video_url'],
                'moments': moments_result['moments']
            }

            result = process_video_moments(moments_data=moments_data)
            return JSONResponse(content=result)
        else:
            # Just return moments
            result = get_popular_moments(
                url_or_video_id=url,
                max_duration=max_duration,
                min_duration=min_duration,
                threshold=threshold
            )
            return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "youtube-video-processing",
        "features": ["moments-detection", "video-clipping"]
    }


if __name__ == "__main__":
    print("\n" + "="*60)
    print("YouTube Video Processing API")
    print("="*60)
    print("\nStarting server...")
    print("  - API docs: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("  - Health check: http://localhost:8000/api/v1/health")
    print("\nExample requests:")
    print("  # Analyze video (metadata + moments)")
    print("  curl 'http://localhost:8000/api/v1/analyze?url=RusBe_8arLQ'")
    print("\n  # Get popular moments only")
    print("  curl 'http://localhost:8000/api/v1/moments?url=RusBe_8arLQ'")
    print("\n  # Create video clips")
    print("  curl -X POST 'http://localhost:8000/api/v1/clips?url=RusBe_8arLQ'")
    print("\n  # Process video (moments + clips)")
    print("  curl 'http://localhost:8000/api/v1/process?url=RusBe_8arLQ&create_clips=true'")
    print("\n" + "="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
