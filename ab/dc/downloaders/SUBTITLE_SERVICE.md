# Subtitle Downloader Service

Service for downloading subtitles from YouTube videos using yt-dlp.

## Features

- Download subtitles by video URL or ID
- Support for multiple languages
- List available subtitles before downloading
- Both manual and auto-generated subtitles
- Multiple output formats (VTT, SRT)
- Export to plain text or markdown
- Parse and extract subtitle segments
- Metadata extraction

## Dependencies

- **yt-dlp**: Media downloader for YouTube

Install: `pip install yt-dlp`

## Usage

### Command Line Interface

#### List Available Subtitles

```bash
python cli_subtitle.py list "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### Download Single Subtitle

```bash
# Download English subtitle (VTT format)
python cli_subtitle.py download "VIDEO_ID" -l en

# Download Portuguese subtitle (SRT format)
python cli_subtitle.py download "VIDEO_ID" -l pt -f srt

# Download with text export
python cli_subtitle.py download "VIDEO_ID" -l en --export-text

# Download with markdown export and metadata
python cli_subtitle.py download "VIDEO_ID" -l en --export-markdown --metadata
```

#### Download All Available Subtitles

```bash
# Download all subtitles
python cli_subtitle.py download "VIDEO_ID" --all

# Download all manual subtitles (no auto-generated)
python cli_subtitle.py download "VIDEO_ID" --all --no-auto
```

#### Options

- `-l, --language LANG`: Language code (default: en)
- `-o, --output-dir DIR`: Output directory (default: ./subtitles)
- `-f, --format FORMAT`: Subtitle format (vtt or srt, default: vtt)
- `--all`: Download all available subtitles
- `--no-auto`: Disable auto-generated subtitles (manual only)
- `--export-text`: Export to plain text file
- `--export-markdown`: Export to markdown file
- `--timestamps`: Include timestamps in text export
- `--metadata`: Show subtitle metadata
- `--timeout SECS`: Download timeout (default: 60)

### Python API

#### List Available Subtitles

```python
from subtitle_downloader import list_available_subtitles

# List all available subtitles
subtitles = list_available_subtitles("https://www.youtube.com/watch?v=VIDEO_ID")

print("Manual subtitles:", subtitles['manual'])
print("Auto-generated:", subtitles['auto'])
```

#### Download Single Subtitle

```python
from pathlib import Path
from subtitle_downloader import download_subtitle

# Download English subtitle
subtitle_path = download_subtitle(
    video_url="https://www.youtube.com/watch?v=VIDEO_ID",
    video_id="VIDEO_ID",
    language="en",
    subtitles_path=Path("./subtitles"),
    format="vtt",
    auto_generated=True
)

print(f"Downloaded: {subtitle_path}")
```

#### Download Multiple Subtitles

```python
from pathlib import Path
from subtitle_downloader import download_all_subtitles

# Download specific languages
downloaded = download_all_subtitles(
    video_url="VIDEO_ID",
    video_id="VIDEO_ID",
    subtitles_path=Path("./subtitles"),
    format="vtt",
    languages=["en", "pt", "es"]
)

for lang, path in downloaded.items():
    print(f"{lang}: {path}")
```

#### Parse Subtitle File

```python
from pathlib import Path
from subtitle_downloader import parse_vtt_subtitle

# Parse VTT file into segments
segments = parse_vtt_subtitle(Path("subtitle.vtt"))

for segment in segments:
    print(f"[{segment['start']} - {segment['end']}]")
    print(segment['text'])
```

#### Export to Text/Markdown

```python
from pathlib import Path
from subtitle_downloader import (
    export_subtitle_to_text,
    export_subtitle_to_markdown
)

subtitle_path = Path("subtitle.vtt")

# Export to plain text
text_path = export_subtitle_to_text(
    subtitle_path,
    include_timestamps=True
)

# Export to markdown
markdown_path = export_subtitle_to_markdown(
    video_id="VIDEO_ID",
    subtitle_path=subtitle_path,
    video_title="My Video",
    language="English"
)
```

#### Get Subtitle Metadata

```python
from pathlib import Path
from subtitle_downloader import get_subtitle_metadata

metadata = get_subtitle_metadata(Path("subtitle.vtt"))

print(f"File size: {metadata['file_size_kb']} KB")
print(f"Segments: {metadata['segment_count']}")
print(f"Duration: {metadata['duration_formatted']}")
print(f"Language: {metadata['language']}")
```

## API Reference

### Main Functions

#### `list_available_subtitles(video_url: str) -> Dict`

List all available subtitles for a video.

**Returns:**
```python
{
    'manual': [{'lang': 'en', 'name': 'English'}, ...],
    'auto': [{'lang': 'pt', 'name': 'Portuguese (auto-generated)'}, ...]
}
```

#### `download_subtitle(video_url, video_id, language, subtitles_path, format='vtt', auto_generated=True, timeout=60) -> Path`

Download a single subtitle file.

**Parameters:**
- `video_url`: YouTube URL or video ID
- `video_id`: Video ID for filename
- `language`: Language code (e.g., 'en', 'pt', 'es')
- `subtitles_path`: Directory to save subtitles
- `format`: 'vtt' or 'srt' (default: 'vtt')
- `auto_generated`: Allow auto-generated subtitles (default: True)
- `timeout`: Download timeout in seconds (default: 60)

**Returns:** Path to downloaded subtitle file

#### `download_all_subtitles(video_url, video_id, subtitles_path, format='vtt', languages=None, auto_generated=True, timeout=120) -> Dict[str, Path]`

Download multiple subtitles.

**Parameters:**
- `languages`: List of language codes or None for all available

**Returns:** Dictionary mapping language codes to file paths

#### `parse_vtt_subtitle(subtitle_path: Path) -> List[Dict]`

Parse VTT subtitle file into structured segments.

**Returns:**
```python
[
    {
        'index': 0,
        'start': '00:00:00.000',
        'end': '00:00:03.000',
        'start_seconds': 0.0,
        'end_seconds': 3.0,
        'text': 'Subtitle text'
    },
    ...
]
```

#### `export_subtitle_to_text(subtitle_path, output_path=None, include_timestamps=False) -> Path`

Export subtitle to plain text.

#### `export_subtitle_to_markdown(video_id, subtitle_path, output_path=None, video_title=None, language=None) -> Path`

Export subtitle to markdown with metadata.

#### `get_subtitle_metadata(subtitle_path: Path) -> Dict`

Get metadata about a subtitle file.

**Returns:**
```python
{
    'file_size_kb': float,
    'segment_count': int,
    'duration_seconds': float,
    'duration_formatted': str,
    'language': str
}
```

### Helper Functions

#### `get_subtitle_path(video_id, language, base_path, extension='.vtt') -> Path`

Generate path for subtitle file.

## Language Codes

Common language codes supported by YouTube:
- `en` - English
- `pt` - Portuguese
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `ja` - Japanese
- `ko` - Korean
- `zh` - Chinese
- `ru` - Russian
- `ar` - Arabic
- `hi` - Hindi

Use the `list` command to see all available languages for a specific video.

## Output Formats

### VTT (WebVTT)

Web Video Text Tracks format - standard for web video subtitles.

```
WEBVTT

00:00:00.000 --> 00:00:03.000
This is the first subtitle

00:00:03.000 --> 00:00:06.000
This is the second subtitle
```

### SRT (SubRip)

SubRip Text format - widely compatible with video players.

```
1
00:00:00,000 --> 00:00:03,000
This is the first subtitle

2
00:00:03,000 --> 00:00:06,000
This is the second subtitle
```

## File Naming

Downloaded subtitles are saved with the format:

```
{video_id}_{language}.{format}
```

Examples:
- `dQw4w9WgXcQ_en.vtt` - English VTT
- `dQw4w9WgXcQ_pt.srt` - Portuguese SRT

## Examples

### Download and Parse

```python
from pathlib import Path
from subtitle_downloader import download_subtitle, parse_vtt_subtitle

# Download subtitle
subtitle_path = download_subtitle(
    video_url="dQw4w9WgXcQ",
    video_id="dQw4w9WgXcQ",
    language="en",
    subtitles_path=Path("./subtitles")
)

# Parse into segments
segments = parse_vtt_subtitle(subtitle_path)

# Find segments containing specific text
matches = [s for s in segments if "never gonna" in s['text'].lower()]
for match in matches:
    print(f"Found at {match['start']}: {match['text']}")
```

### Batch Download

```python
from pathlib import Path
from subtitle_downloader import download_all_subtitles

video_ids = ["VIDEO_ID_1", "VIDEO_ID_2", "VIDEO_ID_3"]
output_dir = Path("./subtitles")

for video_id in video_ids:
    try:
        downloaded = download_all_subtitles(
            video_url=video_id,
            video_id=video_id,
            subtitles_path=output_dir,
            languages=["en", "pt"]
        )
        print(f"{video_id}: Downloaded {len(downloaded)} subtitles")
    except Exception as e:
        print(f"{video_id}: Failed - {e}")
```

### Search in Subtitles

```python
from pathlib import Path
from subtitle_downloader import parse_vtt_subtitle

def search_subtitle(subtitle_path: Path, query: str):
    """Search for text in subtitle"""
    segments = parse_vtt_subtitle(subtitle_path)

    results = []
    for segment in segments:
        if query.lower() in segment['text'].lower():
            results.append({
                'time': segment['start'],
                'text': segment['text']
            })

    return results

# Search
results = search_subtitle(Path("subtitle.vtt"), "important")
for result in results:
    print(f"[{result['time']}] {result['text']}")
```

## Error Handling

All functions raise `SubtitleDownloadError` on failures:

```python
from subtitle_downloader import download_subtitle, SubtitleDownloadError

try:
    subtitle_path = download_subtitle(
        video_url="VIDEO_ID",
        video_id="VIDEO_ID",
        language="en",
        subtitles_path=Path("./subtitles")
    )
except SubtitleDownloadError as e:
    print(f"Download failed: {e}")
```

## Integration with Other Services

### With Video Transcriber

```python
from pathlib import Path
from subtitle_downloader import download_subtitle
from video_transcriber import transcribe_video

# Download subtitle
subtitle_path = download_subtitle(
    video_url="VIDEO_ID",
    video_id="VIDEO_ID",
    language="en",
    subtitles_path=Path("./subtitles")
)

# Or transcribe with Whisper for better accuracy
transcription = transcribe_video(
    video_path=Path("video.mp4"),
    model_size="base",
    output_dir=Path("./transcriptions")
)
```

### With Video Clipper

```python
from pathlib import Path
from subtitle_downloader import download_subtitle, parse_vtt_subtitle

# Download subtitle
subtitle_path = download_subtitle(
    video_url="VIDEO_ID",
    video_id="VIDEO_ID",
    language="en",
    subtitles_path=Path("./subtitles")
)

# Parse to find interesting moments
segments = parse_vtt_subtitle(subtitle_path)

# Find segments with keywords
keywords = ["amazing", "incredible", "wow"]
interesting_moments = []

for segment in segments:
    for keyword in keywords:
        if keyword in segment['text'].lower():
            interesting_moments.append({
                'start': segment['start_seconds'],
                'text': segment['text']
            })

# Use these timestamps for clipping
print(f"Found {len(interesting_moments)} interesting moments")
```

## Notes

- YouTube may not have subtitles for all videos
- Auto-generated subtitles are less accurate than manual ones
- Some videos may only have subtitles in specific languages
- Downloaded subtitles are cached locally for reuse
- VTT format is recommended for web use
- SRT format is more compatible with video editing software

## Troubleshooting

### No subtitles available

Some videos don't have subtitles. Use the `list` command to check availability.

### Language not found

Check available languages using `list` command. Some videos may only have auto-generated subtitles in certain languages.

### Download timeout

Increase timeout with `--timeout` option or `timeout` parameter.

### Permission errors

Ensure you have write permissions in the output directory.