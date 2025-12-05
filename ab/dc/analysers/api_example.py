"""
Example FastAPI wrapper for the YouTube Heatmap Service
This demonstrates how to integrate the replay_heatmap service into a REST API.

Usage:
    pip install fastapi uvicorn
    python api_example.py

    # Then visit: http://localhost:8000/docs for interactive API documentation
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn

# Import the service
from replay_heatmap import get_popular_moments


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


# Initialize FastAPI app
app = FastAPI(
    title="YouTube Popular Moments API",
    description="Extract popular moments from YouTube videos using heatmap data",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "YouTube Popular Moments API",
        "version": "1.0.0",
        "endpoints": {
            "moments": "/api/v1/moments",
            "docs": "/docs"
        }
    }


@app.get("/api/v1/moments", response_model=PopularMomentsResponse)
async def get_moments(
    url: str = Query(..., description="YouTube URL or video ID"),
    max_duration: int = Query(40, ge=10, le=300, description="Maximum moment duration in seconds"),
    min_duration: int = Query(10, ge=5, le=60, description="Minimum moment duration in seconds"),
    threshold: float = Query(0.45, ge=0.1, le=0.9, description="Peak detection threshold (0.1-0.9)")
):
    """
    Extract popular moments from a YouTube video.

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


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "youtube-moments"}


if __name__ == "__main__":
    print("\n" + "="*60)
    print("YouTube Popular Moments API")
    print("="*60)
    print("\nStarting server...")
    print("  - API docs: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("  - Health check: http://localhost:8000/api/v1/health")
    print("\nExample request:")
    print("  curl 'http://localhost:8000/api/v1/moments?url=RusBe_8arLQ'")
    print("\n" + "="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)