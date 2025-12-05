#!/usr/bin/env python3
"""
Test script for subtitle downloader service
"""

import sys
from pathlib import Path
import logging

from subtitle_downloader import (
    list_available_subtitles,
    download_subtitle,
    download_all_subtitles,
    parse_vtt_subtitle,
    export_subtitle_to_text,
    export_subtitle_to_markdown,
    get_subtitle_metadata,
    SubtitleDownloadError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_list_subtitles(video_id: str):
    """Test listing available subtitles"""
    print("\n" + "="*60)
    print("TEST: List Available Subtitles")
    print("="*60)

    try:
        subtitles = list_available_subtitles(video_id)

        print(f"\nVideo ID: {video_id}")

        if subtitles['manual']:
            print(f"\nManual subtitles ({len(subtitles['manual'])}):")
            for sub in subtitles['manual'][:5]:  # Show first 5
                print(f"  - {sub['lang']:5s} {sub['name']}")

        if subtitles['auto']:
            print(f"\nAuto-generated subtitles ({len(subtitles['auto'])}):")
            for sub in subtitles['auto'][:5]:  # Show first 5
                print(f"  - {sub['lang']:5s} {sub['name']}")

        print("\nResult: PASSED")
        return True

    except SubtitleDownloadError as e:
        print(f"\nResult: FAILED - {e}")
        return False


def test_download_single(video_id: str, language: str = 'en'):
    """Test downloading single subtitle"""
    print("\n" + "="*60)
    print("TEST: Download Single Subtitle")
    print("="*60)

    try:
        output_dir = Path("./test_subtitles")
        output_dir.mkdir(exist_ok=True)

        subtitle_path = download_subtitle(
            video_url=video_id,
            video_id=video_id,
            language=language,
            subtitles_path=output_dir,
            format='vtt'
        )

        print(f"\nDownloaded: {subtitle_path}")
        print(f"File size: {subtitle_path.stat().st_size / 1024:.2f} KB")

        # Parse and show first few segments
        segments = parse_vtt_subtitle(subtitle_path)
        print(f"\nTotal segments: {len(segments)}")
        print("\nFirst 3 segments:")
        for segment in segments[:3]:
            print(f"  [{segment['start']} - {segment['end']}]")
            print(f"  {segment['text']}")

        print("\nResult: PASSED")
        return True

    except SubtitleDownloadError as e:
        print(f"\nResult: FAILED - {e}")
        return False


def test_export_formats(video_id: str, language: str = 'en'):
    """Test exporting to different formats"""
    print("\n" + "="*60)
    print("TEST: Export to Different Formats")
    print("="*60)

    try:
        output_dir = Path("./test_subtitles")
        subtitle_path = output_dir / f"{video_id}_{language}.vtt"

        if not subtitle_path.exists():
            print("Downloading subtitle first...")
            subtitle_path = download_subtitle(
                video_url=video_id,
                video_id=video_id,
                language=language,
                subtitles_path=output_dir
            )

        # Export to text
        text_path = export_subtitle_to_text(
            subtitle_path,
            include_timestamps=True
        )
        print(f"\nText export: {text_path}")
        print(f"Size: {text_path.stat().st_size / 1024:.2f} KB")

        # Export to markdown
        markdown_path = export_subtitle_to_markdown(
            video_id=video_id,
            subtitle_path=subtitle_path,
            language=language
        )
        print(f"\nMarkdown export: {markdown_path}")
        print(f"Size: {markdown_path.stat().st_size / 1024:.2f} KB")

        # Show metadata
        metadata = get_subtitle_metadata(subtitle_path)
        print("\nMetadata:")
        print(f"  - Segments: {metadata['segment_count']}")
        print(f"  - Duration: {metadata['duration_formatted']}")
        print(f"  - Language: {metadata['language']}")

        print("\nResult: PASSED")
        return True

    except Exception as e:
        print(f"\nResult: FAILED - {e}")
        return False


def test_download_multiple(video_id: str):
    """Test downloading multiple subtitles"""
    print("\n" + "="*60)
    print("TEST: Download Multiple Subtitles")
    print("="*60)

    try:
        output_dir = Path("./test_subtitles")

        # Try to download English and Portuguese
        languages = ['en', 'pt']

        downloaded = download_all_subtitles(
            video_url=video_id,
            video_id=video_id,
            subtitles_path=output_dir,
            languages=languages,
            format='vtt'
        )

        print(f"\nRequested languages: {languages}")
        print(f"Downloaded: {list(downloaded.keys())}")

        for lang, path in downloaded.items():
            size_kb = path.stat().st_size / 1024
            print(f"\n  - {lang}: {path}")
            print(f"    Size: {size_kb:.2f} KB")

        print("\nResult: PASSED")
        return True

    except SubtitleDownloadError as e:
        print(f"\nResult: FAILED - {e}")
        return False


def run_tests(video_id: str):
    """Run all tests"""
    print("\n" + "="*70)
    print("SUBTITLE DOWNLOADER SERVICE - TEST SUITE")
    print("="*70)
    print(f"\nTest video: {video_id}")
    print(f"URL: https://www.youtube.com/watch?v={video_id}")

    results = []

    # Test 1: List subtitles
    results.append(("List Subtitles", test_list_subtitles(video_id)))

    # Test 2: Download single subtitle
    results.append(("Download Single", test_download_single(video_id, 'en')))

    # Test 3: Export formats
    results.append(("Export Formats", test_export_formats(video_id, 'en')))

    # Test 4: Download multiple
    results.append(("Download Multiple", test_download_multiple(video_id)))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name:30s} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll tests PASSED!")
        return 0
    else:
        print(f"\n{total - passed} test(s) FAILED")
        return 1


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_subtitle_service.py VIDEO_ID")
        print("\nExample:")
        print("  python test_subtitle_service.py dQw4w9WgXcQ")
        print("\nNote: Use a video ID that you know has subtitles.")
        sys.exit(1)

    video_id = sys.argv[1]

    # Extract video ID if URL provided
    if 'youtube.com' in video_id or 'youtu.be' in video_id:
        if 'watch?v=' in video_id:
            video_id = video_id.split('watch?v=')[1].split('&')[0]
        elif 'youtu.be/' in video_id:
            video_id = video_id.split('youtu.be/')[1].split('?')[0]

    exit_code = run_tests(video_id)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()