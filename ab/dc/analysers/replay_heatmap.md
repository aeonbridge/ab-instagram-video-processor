# YouTube Replay Heatmaps: Complete Technical Guide for Viral Clip Extraction

YouTube's "Most Replayed" heatmap feature—combined with Dan Goodman's peak detection algorithm—provides a powerful method for **automatically identifying high-engagement moments** in videos for viral clip extraction. The most reliable current approach uses **yt-dlp** to extract heatmap data, followed by signal processing to detect and group engagement peaks into actionable "moments." However, accessing this data comes with significant Terms of Service restrictions, and alternative approaches using transcript analysis or commercial tools offer compliant pathways for production systems.

## How YouTube replay heatmaps work

YouTube's "Most Replayed" feature launched publicly on **May 18, 2022** after two years of testing. The feature displays a translucent graph above the video progress bar, highlighting sections viewers have rewatched most often. YouTube generates this data by tracking viewer replay behavior and aggregating it to identify engagement hotspots across all viewers.

The data is **normalized relative to each video**, meaning a value of **1.0** represents the absolute peak (most replayed part) for that specific video, not an absolute replay count. This normalization makes cross-video comparisons difficult but enables consistent within-video analysis for clip identification.

**Technical requirements for heatmaps to appear:**
- Video must have approximately **50,000+ views** (threshold varies)
- Generally available on longer-form content
- Feature may not display on videos with manually defined chapters
- Heatmaps update as more views accumulate; best results on videos **5-7+ days old with 90K+ views**

YouTube renders the heatmap as an SVG element with class `ytp-heat-map-svg` using cubic Bézier curves within a **1000x100 viewBox**. The underlying data is also embedded in the page's `ytInitialData` JavaScript variable, which provides structured JSON with `heatMarkerIntensityScoreNormalized` values ranging from 0 to 1.

## Programmatic methods to extract heatmap data

**The YouTube Data API v3 does NOT officially support heatmap data extraction.** There is no `part=heatmap` parameter or official endpoint. All extraction methods rely on scraping or reverse-engineering approaches.

### yt-dlp: The recommended approach

The most reliable method as of 2024-2025 is **yt-dlp**, the popular video download tool that was updated in September 2023 (PR #8299) to include heatmap extraction. This approach works without browser automation and provides structured data.

```bash
# Extract heatmap and save to JSON
yt-dlp --write-info-json --skip-download "https://www.youtube.com/watch?v=VIDEO_ID"

# Print heatmap directly to stdout
yt-dlp --print "%(heatmap)j" "https://www.youtube.com/watch?v=VIDEO_ID"
```

The output follows a standardized format with timestamps in seconds:

```json
{
  "heatmap": [
    {"start": 0, "end": 4.321, "normalized": 0.81},
    {"start": 4.321, "end": 8.642, "normalized": 0.93},
    {"start": 8.642, "end": 12.963, "normalized": 0.45}
  ]
}
```

### Direct web scraping via ytInitialData

For Python implementations without yt-dlp dependency, the heatmap data can be extracted directly from YouTube's page HTML:

```python
from bs4 import BeautifulSoup
import requests
import re
import json

url = "https://www.youtube.com/watch?v=VIDEO_ID"
soup = BeautifulSoup(requests.get(url).text, "html.parser")
data = re.search(r"var ytInitialData = ({.*?});", soup.prettify()).group(1)
data = json.loads(data)

heatmap_data = data['playerOverlays']['playerOverlayRenderer'] \
    ['decoratedPlayerBarRenderer']['decoratedPlayerBarRenderer']['playerBar'] \
    ['multiMarkersPlayerBarRenderer']['markersMap']
```

### Available libraries and packages

| Tool | Language | Method | Reliability |
|------|----------|--------|-------------|
| **yt-dlp** | Python | HTTP scraping | ⭐⭐⭐⭐⭐ High |
| **youtube-heatmap** | npm/Node.js | Puppeteer | ⭐⭐⭐ Medium |
| **yt_most_replayed** | npm/Node.js | HTTP scraping | ⭐⭐⭐ Medium |
| **ytb-most-replayed** | Python | Selenium SVG extraction | ⭐⭐⭐ Medium |
| **Apify Actors** | Cloud API | Various | ⭐⭐⭐⭐ High |

Note: The YouTube Operational API (yt.lemnoslife.com) that previously offered a `part=mostReplayed` endpoint was **shut down in October 2024** due to YouTube legal action, though self-hosting from the GitHub repository remains possible.

## Dan Goodman's peak detection algorithm

Dan Goodman's blog post from **October 2022** describes a sophisticated algorithm for converting raw heatmap data into actionable "moments"—time ranges representing the most engaging portions of a video. His approach involves three key phases: smoothing, peak detection, and moment grouping.

### Phase 1: Data smoothing

Raw heatmap data contains many small local peaks that create noise. Goodman's smoothing algorithm reduces this noise while preserving major engagement peaks:

```
For each point:
1. Get the point to the left (if exists)
2. Get the point to the right (if exists)  
3. Take the average of: current point + (⅓ × left point) + (⅓ × right point)
4. Multiply the final result by 1.9x to restore scale
```

This approach gives neighboring points weighted influence over each center point, creating a smoother curve while maintaining relative values (since all values are normalized 0-1 anyway).

### Phase 2: Local maxima and minima detection

After smoothing, the algorithm identifies all local maxima (peaks) and minima (valleys):

- **Local maxima** (green points): Represent engagement peaks
- **Local minima** (blue points): Represent engagement valleys between peaks
- **Threshold filtering**: Ignore maxima less than **45%** of the largest value in the graph—these moments aren't relatively popular enough to matter

### Phase 3: Moment grouping algorithm

The key innovation is grouping nearby peaks into unified "moments." Adjacent peaks often represent the same engaging segment, and the algorithm consolidates them:

```
Sort local maxima descending by value, then for each maxima:
1. Walk left and right to find the nearest maxima
2. Find all local minima between current and nearest maxima
3. If the nearest maxima is too close → remove that maxima and minima between
4. If far enough but ALL minima are >65% of both maxima → remove minima and border maxima
5. If too far apart → skip (keep as separate moments)
6. Repeat until no more removals occur
```

The final moment boundaries are determined by walking from each remaining maxima left and right until hitting the first minima (or video start/end). This creates clean, non-overlapping time ranges.

### Configurable parameters

Goodman's system supports parameterization for different use cases:
- **Maximum moment duration**: e.g., 30-40 seconds
- **Minimum moment duration**: e.g., 10 seconds
- **Maxima threshold**: 45% of maximum value (adjustable)
- **Minima grouping threshold**: 65% of both adjacent maxima

When a moment exceeds the maximum duration, it gets subdivided at natural minima points, creating multiple shorter clips from a single extended peak.

## Implementation example combining yt-dlp with peak detection

```python
import subprocess
import json
import numpy as np

def get_heatmap(video_id):
    """Extract heatmap data using yt-dlp"""
    cmd = ['yt-dlp', '--print', '%(heatmap)j', f'https://www.youtube.com/watch?v={video_id}']
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def smooth_data(data, multiplier=1.9):
    """Apply Goodman's smoothing algorithm"""
    smoothed = []
    for i, point in enumerate(data):
        left = data[i-1]['normalized'] if i > 0 else point['normalized']
        right = data[i+1]['normalized'] if i < len(data)-1 else point['normalized']
        avg = (point['normalized'] + (left/3) + (right/3)) * multiplier
        smoothed.append({**point, 'normalized': min(avg, 1.0)})
    return smoothed

def find_local_extrema(data, threshold=0.45):
    """Find local maxima and minima above threshold"""
    max_val = max(p['normalized'] for p in data)
    maxima, minima = [], []
    
    for i in range(1, len(data)-1):
        curr = data[i]['normalized']
        prev = data[i-1]['normalized']  
        next_val = data[i+1]['normalized']
        
        if curr > prev and curr > next_val and curr >= max_val * threshold:
            maxima.append({'index': i, **data[i]})
        elif curr < prev and curr < next_val:
            minima.append({'index': i, **data[i]})
    
    return maxima, minima

def extract_moments(heatmap, max_duration=40, min_duration=10):
    """Extract popular moments using Goodman's algorithm"""
    smoothed = smooth_data(heatmap)
    maxima, minima = find_local_extrema(smoothed)
    # ... implement grouping algorithm ...
    # Returns list of {start_time, end_time, peak_value} moments
    return moments

# Usage
heatmap = get_heatmap('RusBe_8arLQ')
moments = extract_moments(heatmap, max_duration=30, min_duration=10)
for m in moments:
    print(f"Moment: {m['start']:.1f}s - {m['end']:.1f}s (score: {m['peak']:.2f})")
```

## Terms of service and legal considerations

YouTube's Terms of Service and API Developer Policies **explicitly prohibit scraping**. Section III.E.6 states: "You and your API Clients must not, and must not encourage, enable, or require others to, directly or indirectly, scrape YouTube Applications or Google Applications."

**Key prohibitions include:**
- Accessing services by "automated means (such as robots, botnets or scrapers)"
- Downloading, caching, or storing copies of YouTube audiovisual content without written approval
- Using any technology other than YouTube API Services to access data
- Data aggregation to gain insights into YouTube's usage or business

**Enforcement reality:** The YouTube Operational API (yt.lemnoslife.com) was shut down in October 2024 after YouTube legal action. Active lawsuits in 2024-2025 include cases against OpenAI and Nvidia for allegedly scraping YouTube content for AI training. Consequences range from IP bans (most common) to potential copyright violations ($150,000 per work) and CFAA violations.

**Risk assessment:**
| Activity | Risk Level |
|----------|------------|
| Large-scale commercial scraping | High |
| Small-scale personal/research use | Medium |
| Using YouTube Data API within limits | Compliant |
| Processing user-uploaded files | Compliant |

## Compliant alternatives for production systems

For a production viral clips system, several ToS-compliant approaches can identify high-engagement moments without scraping heatmap data:

### Transcript-based analysis

Use the YouTube Data API to retrieve video captions (compliant), then apply NLP sentiment analysis:

```python
from nltk.sentiment.vader import SentimentIntensityAnalyzer
sid = SentimentIntensityAnalyzer()

# Score each transcript segment for emotional peaks
segments['sentiment'] = segments['text'].apply(lambda x: sid.polarity_scores(x)['compound'])
high_engagement = segments[segments['sentiment'].abs() > 0.6]
```

Detectable signals include emotional phrases, speaker emphasis, topic transitions, conflict points, and question/answer moments.

### Comment timestamp mining

Parse YouTube comments (via API) to extract timestamps viewers mention. Research from ACM CHI 2019 found that timestamped comments correlate strongly with viewer interest:

```python
import re
timestamps = re.findall(r'(\d{1,2}:\d{2}(?::\d{2})?)', comment_text)
# Aggregate and rank by frequency
```

### Commercial AI tools

Production-ready tools that process uploaded video files (fully compliant):

| Tool | Accuracy | Approach | Cost |
|------|----------|----------|------|
| **OpusClip** | 0.93 mAP | Multimodal AI (visual + audio + text) | Free tier + paid |
| **Descript** | High | Transcript analysis, AI clip finder | $12/mo+ |
| **Vidyo.ai** | High | AI video analysis, virality scoring | Free tier + paid |

### Audio analysis

For content you own or have rights to process, audio analysis can detect engagement signals:
- **Applause/laughter detection** using Hidden Markov Models
- **Energy/volume spike detection** using MFCC features
- **Libraries**: pyAudioAnalysis, jrgillick/laughter-detection (GitHub)

## Recommended architecture for automated clip production

For a compliant production system, consider a hybrid architecture:

```
[Input: YouTube URL]
        ↓
[Compliant Data Collection]
├── YouTube API: Get captions/transcript
├── YouTube API: Fetch top comments  
└── YouTube API: Get video metadata
        ↓
[Signal Processing]
├── Transcript NLP: Sentiment peaks, keyword density
├── Comment Mining: Parse mentioned timestamps
└── (Optional) Heatmap: If accepting legal risk
        ↓
[Moment Ranking Engine]
├── Combine signals with weighted scoring
└── Apply Goodman-style peak grouping
        ↓
[Output: Ranked timestamp ranges for clips]
```

If accepting the legal risks of scraping for internal/research use, the yt-dlp + Goodman algorithm combination provides the highest-quality engagement signals. For production systems requiring compliance, the transcript + comment approach offers **70-80%** of the accuracy with zero legal exposure.

## Conclusion

YouTube replay heatmaps offer genuine viewer engagement data that directly identifies viral-worthy moments, making them invaluable for automated clip production. **yt-dlp** provides the most reliable extraction method, outputting structured JSON with normalized engagement scores. **Dan Goodman's algorithm**—smoothing, peak detection, and moment grouping—transforms this raw data into actionable clip boundaries through configurable parameters for duration and significance thresholds.

The critical consideration is ToS compliance: direct scraping violates YouTube's terms and carries enforcement risk, as demonstrated by the 2024 shutdown of the YouTube Operational API. Production systems should evaluate whether to accept this risk for internal tools or adopt compliant alternatives combining transcript analysis, comment timestamp mining, and commercial AI tools. A hybrid approach—using heatmap data when available while falling back to transcript/comment signals—provides both high accuracy and operational resilience.