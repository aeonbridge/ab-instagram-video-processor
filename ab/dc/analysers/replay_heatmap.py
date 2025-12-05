"""
YouTube Replay Heatmap Service
Extracts popular moments from YouTube videos using heatmap data and Goodman's algorithm.
"""

import subprocess
import json
import re
from typing import List, Dict, Optional


def extract_video_id(url_or_id: str) -> Optional[str]:
    """Extract YouTube video ID from URL or return the ID if already provided.

    Args:
        url_or_id: YouTube URL or video ID

    Returns:
        Video ID string or None if invalid

    Examples:
        >>> extract_video_id('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        'dQw4w9WgXcQ'
        >>> extract_video_id('dQw4w9WgXcQ')
        'dQw4w9WgXcQ'
    """
    # If it's already a video ID (11 characters, alphanumeric + - and _)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id

    # Extract from various YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    return None


def get_heatmap(video_id: str) -> List[Dict]:
    """Extract heatmap data using yt-dlp

    Returns:
        list: Array of heatmap points with 'start', 'end', and 'normalized' keys
    """
    cmd = ['yt-dlp', '--print', '%(heatmap)j', f'https://www.youtube.com/watch?v={video_id}']
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    data = json.loads(result.stdout)

    # yt-dlp returns heatmap data directly as an array
    raw_data = data if isinstance(data, list) else data.get('heatmap', [])

    # Normalize the data structure: yt-dlp uses 'start_time', 'end_time', 'value'
    # Convert to 'start', 'end', 'normalized' for consistency with documentation
    normalized_data = []
    for point in raw_data:
        normalized_data.append({
            'start': point.get('start_time', point.get('start', 0)),
            'end': point.get('end_time', point.get('end', 0)),
            'normalized': point.get('value', point.get('normalized', 0))
        })

    return normalized_data


def smooth_data(data, multiplier=1.0):
    """Apply Goodman's smoothing algorithm

    Args:
        data: List of heatmap points with 'normalized' values
        multiplier: Smoothing multiplier (default 1.0, Goodman used 1.9 but that overshoots)

    Returns:
        list: Smoothed data with updated 'normalized' values

    Note:
        Using multiplier=1.0 instead of 1.9 to avoid excessive capping at 1.0
        which prevents detection of local maxima. The algorithm still works well
        with conservative smoothing.
    """
    if not data:
        return []

    smoothed = []
    for i, point in enumerate(data):
        left = data[i - 1]['normalized'] if i > 0 else point['normalized']
        right = data[i + 1]['normalized'] if i < len(data) - 1 else point['normalized']
        # Weighted average: current point + 1/3 of neighbors on each side
        avg = (point['normalized'] + (left / 3) + (right / 3)) * multiplier
        smoothed.append({**point, 'normalized': avg})
    return smoothed


def find_local_extrema(data, threshold=0.45):
    """Find local maxima and minima above threshold

    Args:
        data: Smoothed heatmap data
        threshold: Minimum relative value for maxima (as fraction of max value)

    Returns:
        tuple: (maxima, minima) lists
    """
    if not data:
        return [], []

    max_val = max(p['normalized'] for p in data)
    threshold_value = max_val * threshold
    maxima, minima = [], []

    for i in range(1, len(data) - 1):
        curr = data[i]['normalized']
        prev = data[i - 1]['normalized']
        next_val = data[i + 1]['normalized']

        # Local maximum: current > both neighbors AND above threshold
        if curr > prev and curr > next_val and curr >= threshold_value:
            maxima.append({'index': i, **data[i]})
        # Local minimum: current < both neighbors
        elif curr < prev and curr < next_val:
            minima.append({'index': i, **data[i]})

    return maxima, minima


def extract_moments(heatmap_data, max_duration=40, min_duration=10):
    """Extract popular moments using Goodman's algorithm

    Args:
        heatmap_data: List of heatmap points with 'start', 'end', 'normalized' keys
        max_duration: Maximum moment duration in seconds (default 40)
        min_duration: Minimum moment duration in seconds (default 10)

    Returns:
        list: List of moments with 'start', 'end', 'peak' keys
    """
    if not heatmap_data:
        return []

    smoothed = smooth_data(heatmap_data)
    if not smoothed:
        return []

    maxima, minima = find_local_extrema(smoothed)

    # Group nearby peaks into unified moments
    # Sort maxima by normalized value (descending)
    maxima_sorted = sorted(maxima, key=lambda x: x['normalized'], reverse=True)

    # Track which maxima/minima to keep
    removed_maxima = set()
    removed_minima = set()

    # Grouping algorithm: iterate through maxima and merge nearby ones
    for current_max in maxima_sorted:
        if current_max['index'] in removed_maxima:
            continue

        # Find nearest maxima on left and right
        left_max = None
        right_max = None

        for other_max in maxima:
            if other_max['index'] in removed_maxima:
                continue
            if other_max['index'] < current_max['index']:
                if left_max is None or other_max['index'] > left_max['index']:
                    left_max = other_max
            elif other_max['index'] > current_max['index']:
                if right_max is None or other_max['index'] < right_max['index']:
                    right_max = other_max

        # Process left neighbor
        if left_max:
            between_minima = [m for m in minima
                              if left_max['index'] < m['index'] < current_max['index']
                              and m['index'] not in removed_minima]
            # Check if minima are too high (>65% of both maxima)
            if between_minima and all(m['normalized'] > 0.65 * min(left_max['normalized'], current_max['normalized'])
                                      for m in between_minima):
                removed_maxima.add(left_max['index'])
                for m in between_minima:
                    removed_minima.add(m['index'])

        # Process right neighbor
        if right_max:
            between_minima = [m for m in minima
                              if current_max['index'] < m['index'] < right_max['index']
                              and m['index'] not in removed_minima]
            # Check if minima are too high (>65% of both maxima)
            if between_minima and all(m['normalized'] > 0.65 * min(current_max['normalized'], right_max['normalized'])
                                      for m in between_minima):
                removed_maxima.add(right_max['index'])
                for m in between_minima:
                    removed_minima.add(m['index'])

    # Keep only non-removed maxima
    final_maxima = [m for m in maxima if m['index'] not in removed_maxima]
    final_minima = [m for m in minima if m['index'] not in removed_minima]

    # Build moments by finding boundaries for each maxima
    moments = []
    for peak in final_maxima:
        # Find left boundary (nearest minima to the left, or start)
        left_boundary = 0
        for m in final_minima:
            if m['index'] < peak['index']:
                left_boundary = max(left_boundary, m['index'])

        # Find right boundary (nearest minima to the right, or end)
        right_boundary = len(smoothed) - 1
        for m in final_minima:
            if m['index'] > peak['index']:
                right_boundary = min(right_boundary, m['index'])
                break

        # Get time range from smoothed data
        start_time = smoothed[left_boundary]['start']
        end_time = smoothed[right_boundary]['end']
        duration = end_time - start_time

        # Skip moments that are too short or too long
        if duration < min_duration:
            continue
        if duration > max_duration:
            # Subdivide long moments at natural minima
            # For simplicity, we'll just take the first max_duration seconds
            end_time = start_time + max_duration

        moments.append({
            'start': start_time,
            'end': end_time,
            'peak': peak['normalized']
        })

    # Sort moments by start time
    moments.sort(key=lambda x: x['start'])

    return moments


def get_popular_moments(
    url_or_video_id: str,
    max_duration: int = 40,
    min_duration: int = 10,
    threshold: float = 0.45
) -> Dict:
    """
    Main service function to extract popular moments from a YouTube video.
    This is the primary entry point for API integration.

    Args:
        url_or_video_id: YouTube URL or video ID
        max_duration: Maximum moment duration in seconds (default 40)
        min_duration: Minimum moment duration in seconds (default 10)
        threshold: Minimum relative value for peak detection (default 0.45)

    Returns:
        Dictionary with structure:
        {
            "success": bool,
            "video_id": str,
            "video_url": str,
            "moments": [
                {
                    "start_time": float,
                    "end_time": float,
                    "duration": float,
                    "score": float,
                    "timestamp": str  # formatted as MM:SS or HH:MM:SS
                },
                ...
            ],
            "total_moments": int,
            "error": str (only if success=False)
        }

    Example:
        >>> result = get_popular_moments('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        >>> print(json.dumps(result, indent=2))
    """
    try:
        # Extract video ID from URL if needed
        video_id = extract_video_id(url_or_video_id)
        if not video_id:
            return {
                "success": False,
                "error": "Invalid YouTube URL or video ID",
                "video_id": None,
                "video_url": None,
                "moments": [],
                "total_moments": 0
            }

        # Construct video URL
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Get heatmap data
        heatmap = get_heatmap(video_id)
        if not heatmap:
            return {
                "success": False,
                "error": "No heatmap data available. Video may need 50,000+ views.",
                "video_id": video_id,
                "video_url": video_url,
                "moments": [],
                "total_moments": 0
            }

        # Extract moments
        moments = extract_moments(heatmap, max_duration, min_duration)

        # Format moments for API response
        formatted_moments = []
        for moment in moments:
            duration = moment['end'] - moment['start']
            formatted_moments.append({
                "start_time": round(moment['start'], 2),
                "end_time": round(moment['end'], 2),
                "duration": round(duration, 2),
                "score": round(moment['peak'], 3),
                "timestamp": _format_timestamp(moment['start'])
            })

        return {
            "success": True,
            "video_id": video_id,
            "video_url": video_url,
            "moments": formatted_moments,
            "total_moments": len(formatted_moments),
            "error": None
        }

    except subprocess.CalledProcessError as e:
        video_id_local = video_id if 'video_id' in locals() else None
        return {
            "success": False,
            "error": f"Failed to fetch video data: {str(e)}",
            "video_id": video_id_local,
            "video_url": f"https://www.youtube.com/watch?v={video_id_local}" if video_id_local else None,
            "moments": [],
            "total_moments": 0
        }
    except json.JSONDecodeError as e:
        video_id_local = video_id if 'video_id' in locals() else None
        return {
            "success": False,
            "error": f"Failed to parse heatmap data: {str(e)}",
            "video_id": video_id_local,
            "video_url": f"https://www.youtube.com/watch?v={video_id_local}" if video_id_local else None,
            "moments": [],
            "total_moments": 0
        }
    except Exception as e:
        video_id_local = video_id if 'video_id' in locals() else None
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "video_id": video_id_local,
            "video_url": f"https://www.youtube.com/watch?v={video_id_local}" if video_id_local else None,
            "moments": [],
            "total_moments": 0
        }


def _format_timestamp(seconds: float) -> str:
    """Format seconds into MM:SS or HH:MM:SS timestamp.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def main():
    """Example usage demonstrating the service API"""
    import sys

    # Test with different URL formats
    test_cases = [
        'RusBe_8arLQ',  # Direct video ID
        'https://www.youtube.com/watch?v=RusBe_8arLQ',  # Full URL
    ]

    # Use command line argument if provided, otherwise use test case
    if len(sys.argv) > 1:
        test_cases = [sys.argv[1]]

    for test_url in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing with: {test_url}")
        print('='*60)

        # Call the main service function
        result = get_popular_moments(
            url_or_video_id=test_url,
            max_duration=30,
            min_duration=10
        )

        # Display results as JSON
        print(json.dumps(result, indent=2))

        # Pretty print for human readability
        if result['success']:
            print(f"\n✓ Successfully extracted {result['total_moments']} moments")
            print(f"  Video ID: {result['video_id']}")
            print("\n  Popular Moments:")
            for i, moment in enumerate(result['moments'], 1):
                print(f"  {i}. [{moment['timestamp']}] "
                      f"{moment['start_time']:.1f}s - {moment['end_time']:.1f}s "
                      f"(duration: {moment['duration']:.1f}s, score: {moment['score']:.2f})")
        else:
            print(f"\n✗ Error: {result['error']}")


if __name__ == "__main__":
    main()