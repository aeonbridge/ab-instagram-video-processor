# Subtitle Download Service - Quick Start

Quick reference guide for downloading YouTube subtitles.

## Installation

```bash
pip install yt-dlp
```

## Basic Usage

### 1. List Available Subtitles

```bash
python cli_subtitle.py list "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Output:**
```
============================================================
AVAILABLE SUBTITLES
============================================================

Manual Subtitles:
  - en    English
  - pt    Portuguese
  - es    Spanish

Auto-generated Subtitles:
  - en    English (auto-generated)
  - pt    Portuguese (auto-generated)
============================================================
```

### 2. Download Single Subtitle

```bash
# Download English subtitle
python cli_subtitle.py download "VIDEO_ID" -l en

# Download Portuguese subtitle
python cli_subtitle.py download "VIDEO_ID" -l pt

# Download as SRT instead of VTT
python cli_subtitle.py download "VIDEO_ID" -l en -f srt
```

### 3. Download All Subtitles

```bash
# Download all available subtitles
python cli_subtitle.py download "VIDEO_ID" --all

# Download only manual subtitles (no auto-generated)
python cli_subtitle.py download "VIDEO_ID" --all --no-auto
```

### 4. Export to Different Formats

```bash
# Export to plain text
python cli_subtitle.py download "VIDEO_ID" -l en --export-text

# Export to markdown with metadata
python cli_subtitle.py download "VIDEO_ID" -l en --export-markdown

# Export with timestamps
python cli_subtitle.py download "VIDEO_ID" -l en --export-text --timestamps
```

### 5. View Metadata

```bash
python cli_subtitle.py download "VIDEO_ID" -l en --metadata
```

**Output:**
```
Metadata:
  - File size: 45.23 KB
  - Segments: 234
  - Duration: 08:45
  - Language: en
```

## Python API

### Basic Download

```python
from pathlib import Path
from subtitle_downloader import download_subtitle

subtitle_path = download_subtitle(
    video_url="VIDEO_ID",
    video_id="VIDEO_ID",
    language="en",
    subtitles_path=Path("./subtitles")
)

print(f"Downloaded: {subtitle_path}")
```

### List and Download

```python
from pathlib import Path
from subtitle_downloader import list_available_subtitles, download_subtitle

# List available
subtitles = list_available_subtitles("VIDEO_ID")

# Download first available manual subtitle
if subtitles['manual']:
    lang = subtitles['manual'][0]['lang']
    path = download_subtitle(
        video_url="VIDEO_ID",
        video_id="VIDEO_ID",
        language=lang,
        subtitles_path=Path("./subtitles")
    )
```

### Parse Subtitle

```python
from pathlib import Path
from subtitle_downloader import parse_vtt_subtitle

segments = parse_vtt_subtitle(Path("subtitle.vtt"))

for segment in segments[:5]:  # First 5 segments
    print(f"[{segment['start']}] {segment['text']}")
```

### Search in Subtitles

```python
from pathlib import Path
from subtitle_downloader import parse_vtt_subtitle

segments = parse_vtt_subtitle(Path("subtitle.vtt"))

# Find segments containing keyword
keyword = "important"
matches = [s for s in segments if keyword.lower() in s['text'].lower()]

for match in matches:
    print(f"[{match['start']}] {match['text']}")
```

## Common Patterns

### Download Multiple Languages

```python
from pathlib import Path
from subtitle_downloader import download_all_subtitles

languages = ["en", "pt", "es"]

downloaded = download_all_subtitles(
    video_url="VIDEO_ID",
    video_id="VIDEO_ID",
    subtitles_path=Path("./subtitles"),
    languages=languages
)

for lang, path in downloaded.items():
    print(f"{lang}: {path}")
```

### Batch Download for Multiple Videos

```python
from pathlib import Path
from subtitle_downloader import download_subtitle

video_ids = ["VIDEO_ID_1", "VIDEO_ID_2", "VIDEO_ID_3"]
output_dir = Path("./subtitles")

for video_id in video_ids:
    try:
        path = download_subtitle(
            video_url=video_id,
            video_id=video_id,
            language="en",
            subtitles_path=output_dir
        )
        print(f"{video_id}: Success - {path}")
    except Exception as e:
        print(f"{video_id}: Failed - {e}")
```

### Export to Markdown

```python
from pathlib import Path
from subtitle_downloader import (
    download_subtitle,
    export_subtitle_to_markdown
)

# Download
subtitle_path = download_subtitle(
    video_url="VIDEO_ID",
    video_id="VIDEO_ID",
    language="en",
    subtitles_path=Path("./subtitles")
)

# Export to markdown
markdown_path = export_subtitle_to_markdown(
    video_id="VIDEO_ID",
    subtitle_path=subtitle_path,
    video_title="My Video Title",
    language="English"
)

print(f"Markdown: {markdown_path}")
```

## Common Language Codes

| Code | Language |
|------|----------|
| en   | English |
| pt   | Portuguese |
| es   | Spanish |
| fr   | French |
| de   | German |
| it   | Italian |
| ja   | Japanese |
| ko   | Korean |
| zh   | Chinese |
| ru   | Russian |
| ar   | Arabic |
| hi   | Hindi |

## File Formats

### VTT (WebVTT)
- Default format
- Web standard
- Best for web video players
- Extension: `.vtt`

### SRT (SubRip)
- Alternative format
- Widely compatible
- Best for video editing software
- Extension: `.srt`

## Output Directory Structure

```
subtitles/
├── VIDEO_ID_1_en.vtt
├── VIDEO_ID_1_pt.vtt
├── VIDEO_ID_1_en.txt
├── VIDEO_ID_1_en.md
├── VIDEO_ID_2_en.vtt
└── VIDEO_ID_2_es.vtt
```

## Error Handling

```python
from subtitle_downloader import download_subtitle, SubtitleDownloadError

try:
    path = download_subtitle(
        video_url="VIDEO_ID",
        video_id="VIDEO_ID",
        language="en",
        subtitles_path=Path("./subtitles")
    )
except SubtitleDownloadError as e:
    print(f"Download failed: {e}")
```

## Tips

1. **Check availability first**: Use `list` command to see what's available
2. **Use auto-generated**: Set `auto_generated=True` for better coverage
3. **Cache downloads**: Files are saved locally, reuse them
4. **Parse for analysis**: Use `parse_vtt_subtitle()` to extract segments
5. **Export formats**: Use markdown for documentation, text for processing

## Full Example

```python
from pathlib import Path
from subtitle_downloader import (
    list_available_subtitles,
    download_subtitle,
    parse_vtt_subtitle,
    export_subtitle_to_markdown
)

# Step 1: Check what's available
video_id = "dQw4w9WgXcQ"
subtitles = list_available_subtitles(video_id)
print(f"Available: {[s['lang'] for s in subtitles['manual']]}")

# Step 2: Download
subtitle_path = download_subtitle(
    video_url=video_id,
    video_id=video_id,
    language="en",
    subtitles_path=Path("./subtitles")
)

# Step 3: Parse and analyze
segments = parse_vtt_subtitle(subtitle_path)
print(f"Total segments: {len(segments)}")

# Step 4: Search for keywords
keyword = "never gonna"
matches = [s for s in segments if keyword in s['text'].lower()]
for match in matches:
    print(f"[{match['start']}] {match['text']}")

# Step 5: Export to markdown
markdown_path = export_subtitle_to_markdown(
    video_id=video_id,
    subtitle_path=subtitle_path,
    video_title="Rick Astley - Never Gonna Give You Up",
    language="English"
)
print(f"Markdown saved: {markdown_path}")
```

## See Also

- **SUBTITLE_SERVICE.md** - Complete documentation
- **cli_subtitle.py** - CLI tool source code
- **subtitle_downloader.py** - Core service implementation