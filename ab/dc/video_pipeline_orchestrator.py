"""
Video Pipeline Orchestrator
Automates the complete video processing pipeline from URL to published clips
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Import existing services
try:
    # Try relative imports first (when run as module)
    from analysers.replay_heatmap import get_moments_with_metadata, extract_video_id
    from publishers.agents.metadata_generator_agent import MetadataGeneratorAgent
    from publishers.agents.thumbnail_generator_agent import ThumbnailGeneratorAgent
    from publishers.auto_publisher import AutoPublisher
except ImportError:
    # Fall back to absolute imports (when run from project root)
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from ab.dc.analysers.replay_heatmap import get_moments_with_metadata, extract_video_id
    from ab.dc.publishers.agents.metadata_generator_agent import MetadataGeneratorAgent
    from ab.dc.publishers.agents.thumbnail_generator_agent import ThumbnailGeneratorAgent
    from ab.dc.publishers.auto_publisher import AutoPublisher

logger = logging.getLogger(__name__)


class VideoPipelineOrchestrator:
    """
    Orchestrates the complete video processing pipeline:
    1. Extract video metadata and popular moments
    2. Download video and subtitles
    3. Create clips for each popular moment
    4. Generate AI metadata for clips
    5. Generate AI thumbnails from metadata
    6. Optionally publish to YouTube
    """

    def __init__(
        self,
        provider: str = "youtube",
        output_base: str = "output",
        max_clip_duration: int = 40,
        min_clip_duration: int = 10
    ):
        """
        Initialize the orchestrator

        Args:
            provider: Platform provider (default: youtube)
            output_base: Base output directory (default: output)
            max_clip_duration: Maximum clip duration in seconds
            min_clip_duration: Minimum clip duration in seconds
        """
        self.provider = provider
        self.output_base = Path(output_base)
        self.max_clip_duration = max_clip_duration
        self.min_clip_duration = min_clip_duration

        # Create base output directory
        self.output_base.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized VideoPipelineOrchestrator for {provider}")

    def process_video(
        self,
        url_or_id: str,
        publish: bool = False,
        privacy: str = "public",
        dry_run: bool = False
    ) -> Dict:
        """
        Process a video through the complete pipeline

        Args:
            url_or_id: YouTube URL or video ID
            publish: Whether to publish clips to YouTube
            privacy: Privacy status (public, private, unlisted)
            dry_run: Test without actually publishing

        Returns:
            Dictionary with processing results
        """
        try:
            # Extract video ID
            video_id = extract_video_id(url_or_id)
            if not video_id:
                return {
                    "success": False,
                    "error": "Invalid YouTube URL or video ID"
                }

            logger.info(f"Processing video: {video_id}")

            # Create video output directory
            video_dir = self.output_base / self.provider / video_id
            video_dir.mkdir(parents=True, exist_ok=True)

            result = {
                "success": True,
                "video_id": video_id,
                "video_dir": str(video_dir),
                "steps": {}
            }

            # Step 1: Extract moments and metadata
            logger.info("Step 1: Extracting popular moments and video metadata...")
            moments_result = self._extract_moments(video_id, video_dir)
            result["steps"]["extract_moments"] = moments_result

            if not moments_result["success"]:
                return moments_result

            # Step 2: Download video
            logger.info("Step 2: Downloading video...")
            download_result = self._download_video(video_id, video_dir)
            result["steps"]["download"] = download_result

            if not download_result["success"]:
                return download_result

            # Step 3: Download subtitles
            logger.info("Step 3: Downloading subtitles...")
            subtitle_result = self._download_subtitles(video_id, video_dir)
            result["steps"]["subtitles"] = subtitle_result

            # Step 4: Create clips for each moment
            logger.info("Step 4: Creating clips for each moment...")
            clips_result = self._create_clips(
                video_id,
                video_dir,
                moments_result["moments"],
                download_result["video_path"]
            )
            result["steps"]["clips"] = clips_result

            if not clips_result["success"]:
                return clips_result

            # Step 5: Generate AI metadata for clips
            logger.info("Step 5: Generating AI metadata for clips...")
            metadata_result = self._generate_metadata(video_dir, clips_result["clip_dirs"])
            result["steps"]["metadata"] = metadata_result

            # Step 6: Generate AI thumbnails
            logger.info("Step 6: Generating AI thumbnails...")
            thumbnails_result = self._generate_thumbnails(video_dir, clips_result["clip_dirs"])
            result["steps"]["thumbnails"] = thumbnails_result

            # Step 7: Publish (if requested)
            if publish:
                logger.info(f"Step 7: Publishing clips to YouTube (privacy: {privacy})...")
                publish_result = self._publish_clips(
                    video_dir,
                    clips_result["clip_dirs"],
                    privacy,
                    dry_run
                )
                result["steps"]["publish"] = publish_result
            else:
                logger.info("Step 7: Skipping publishing (--publish flag not set)")
                result["steps"]["publish"] = {"skipped": True}

            # Summary
            result["summary"] = self._generate_summary(result)

            return result

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_moments(self, video_id: str, video_dir: Path) -> Dict:
        """Extract popular moments and save metadata"""
        try:
            # Get moments with full metadata
            data = get_moments_with_metadata(
                url_or_video_id=video_id,
                max_duration=self.max_clip_duration,
                min_duration=self.min_clip_duration
            )

            if not data["success"]:
                return data

            # Save complete data
            moments_file = video_dir / "moments.json"
            with open(moments_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Save video metadata separately
            metadata_file = video_dir / "video_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data["video_info"], f, indent=2, ensure_ascii=False)

            logger.info(f"Found {data['total_moments']} popular moments")
            logger.info(f"Saved to: {moments_file}")

            return {
                "success": True,
                "moments": data["moments"],
                "video_info": data["video_info"],
                "moments_file": str(moments_file),
                "metadata_file": str(metadata_file)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to extract moments: {str(e)}"
            }

    def _download_video(self, video_id: str, video_dir: Path) -> Dict:
        """Download video using yt-dlp"""
        try:
            output_path = video_dir / f"{video_id}.mp4"

            cmd = [
                'yt-dlp',
                '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                '-o', str(output_path),
                f'https://www.youtube.com/watch?v={video_id}'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Downloaded video to: {output_path}")

            return {
                "success": True,
                "video_path": str(output_path)
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to download video: {e.stderr}"
            }

    def _download_subtitles(self, video_id: str, video_dir: Path) -> Dict:
        """Download subtitles using yt-dlp"""
        try:
            subtitle_path = video_dir / f"{video_id}_full_subtitle"

            cmd = [
                'yt-dlp',
                '--write-sub',
                '--write-auto-sub',
                '--sub-lang', 'en',
                '--sub-format', 'vtt',
                '--skip-download',
                '-o', str(subtitle_path),
                f'https://www.youtube.com/watch?v={video_id}'
            ]

            subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Find generated subtitle file
            subtitle_files = list(video_dir.glob(f"{video_id}_full_subtitle*.vtt"))
            if subtitle_files:
                logger.info(f"Downloaded subtitles to: {subtitle_files[0]}")
                return {
                    "success": True,
                    "subtitle_path": str(subtitle_files[0])
                }
            else:
                logger.warning("No subtitles available")
                return {
                    "success": True,
                    "subtitle_path": None,
                    "warning": "No subtitles available"
                }

        except subprocess.CalledProcessError as e:
            logger.warning(f"Subtitle download failed: {e.stderr}")
            return {
                "success": True,
                "subtitle_path": None,
                "warning": "Subtitle download failed"
            }

    def _create_clips(
        self,
        video_id: str,
        video_dir: Path,
        moments: List[Dict],
        video_path: str
    ) -> Dict:
        """Create video clips for each moment"""
        try:
            clip_dirs = []

            for i, moment in enumerate(moments):
                # Create clip directory
                clip_name = f"{video_id}_{i:04d}"
                clip_dir = video_dir / clip_name
                clip_dir.mkdir(parents=True, exist_ok=True)

                # Output paths
                duration = moment["duration"]
                score = int(moment["score"] * 1000)
                clip_filename = f"{clip_name}_{int(duration)}s_score_{score:03d}_original.mp4"
                clip_path = clip_dir / clip_filename

                # Extract clip using ffmpeg
                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-ss', str(moment["start_time"]),
                    '-t', str(duration),
                    '-c:v', os.getenv('VIDEO_CODEC', 'libx264'),
                    '-c:a', os.getenv('AUDIO_CODEC', 'aac'),
                    '-y',
                    str(clip_path)
                ]

                subprocess.run(cmd, capture_output=True, check=True)
                logger.info(f"Created clip {i+1}/{len(moments)}: {clip_path.name}")

                # Extract subtitle for this clip if available
                self._extract_clip_subtitle(video_id, video_dir, clip_dir, moment, clip_filename)

                clip_dirs.append({
                    "dir": str(clip_dir),
                    "clip_file": str(clip_path),
                    "moment": moment
                })

            return {
                "success": True,
                "clip_dirs": clip_dirs,
                "total_clips": len(clip_dirs)
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to create clips: {e.stderr}"
            }

    def _extract_clip_subtitle(
        self,
        video_id: str,
        video_dir: Path,
        clip_dir: Path,
        moment: Dict,
        clip_filename: str
    ):
        """Extract subtitle segment for a clip"""
        try:
            # Find full subtitle file
            subtitle_files = list(video_dir.glob(f"{video_id}_full_subtitle*.vtt"))
            if not subtitle_files:
                return

            full_subtitle = subtitle_files[0]
            clip_subtitle_path = clip_dir / f"{Path(clip_filename).stem}_en.vtt"

            # Use ffmpeg to extract subtitle segment
            cmd = [
                'ffmpeg',
                '-i', str(full_subtitle),
                '-ss', str(moment["start_time"]),
                '-t', str(moment["duration"]),
                '-y',
                str(clip_subtitle_path)
            ]

            subprocess.run(cmd, capture_output=True, check=True)
            logger.debug(f"Extracted subtitle: {clip_subtitle_path.name}")

        except Exception as e:
            logger.warning(f"Failed to extract subtitle: {e}")

    def _generate_metadata(self, video_dir: Path, clip_dirs: List[Dict]) -> Dict:
        """Generate AI metadata for all clips"""
        try:
            agent = MetadataGeneratorAgent(
                model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
                platform='youtube'
            )

            results = []
            for clip_info in clip_dirs:
                clip_dir = Path(clip_info["dir"])

                # Find transcript file
                transcript_files = list(clip_dir.glob("*_en.vtt"))
                if not transcript_files:
                    logger.warning(f"No transcript found for {clip_dir.name}, skipping metadata")
                    continue

                # Generate metadata
                result = agent.generate_metadata_from_transcript(
                    transcript_path=transcript_files[0],
                    output_dir=clip_dir
                )

                results.append(result)

            successful = sum(1 for r in results if r.get("success", False))
            logger.info(f"Generated metadata for {successful}/{len(clip_dirs)} clips")

            return {
                "success": True,
                "results": results,
                "successful": successful,
                "total": len(clip_dirs)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate metadata: {str(e)}"
            }

    def _generate_thumbnails(self, video_dir: Path, clip_dirs: List[Dict]) -> Dict:
        """Generate AI thumbnails from metadata"""
        try:
            agent = ThumbnailGeneratorAgent(
                model='gpt-3.5-turbo',
                image_provider='dalle'
            )

            results = []
            for clip_info in clip_dirs:
                clip_dir = Path(clip_info["dir"])

                # Find metadata file
                metadata_files = list(clip_dir.glob("*_metadata.json"))
                if not metadata_files:
                    logger.warning(f"No metadata found for {clip_dir.name}, skipping thumbnails")
                    continue

                # Generate thumbnails
                result = agent.generate_thumbnails_from_metadata(
                    metadata_path=metadata_files[0],
                    output_dir=clip_dir / 'thumbnails',
                    generate_images=True
                )

                results.append(result)

            successful = sum(1 for r in results if r.get("success", False))
            logger.info(f"Generated thumbnails for {successful}/{len(clip_dirs)} clips")

            return {
                "success": True,
                "results": results,
                "successful": successful,
                "total": len(clip_dirs)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate thumbnails: {str(e)}"
            }

    def _publish_clips(
        self,
        video_dir: Path,
        clip_dirs: List[Dict],
        privacy: str,
        dry_run: bool
    ) -> Dict:
        """Publish clips to YouTube"""
        try:
            publisher = AutoPublisher(
                platform='youtube',
                dry_run=dry_run
            )

            results = []
            for clip_info in clip_dirs:
                clip_dir = Path(clip_info["dir"])

                # Find publishable videos
                videos = publisher.find_publishable_videos(
                    directory=clip_dir,
                    require_metadata=True,
                    require_thumbnail=False
                )

                if not videos:
                    logger.warning(f"No publishable video in {clip_dir.name}")
                    continue

                # Publish the clip
                result = publisher.publish_video(
                    video_info=videos[0],
                    thumbnail_index=0,
                    privacy_status=privacy
                )

                results.append(result)

            successful = sum(1 for r in results if r.success)
            logger.info(f"Published {successful}/{len(results)} clips")

            return {
                "success": True,
                "results": results,
                "successful": successful,
                "total": len(results)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to publish clips: {str(e)}"
            }

    def _generate_summary(self, result: Dict) -> Dict:
        """Generate pipeline execution summary"""
        steps = result.get("steps", {})

        summary = {
            "video_id": result.get("video_id"),
            "video_dir": result.get("video_dir"),
            "moments_found": len(steps.get("extract_moments", {}).get("moments", [])),
            "clips_created": steps.get("clips", {}).get("total_clips", 0),
            "metadata_generated": steps.get("metadata", {}).get("successful", 0),
            "thumbnails_generated": steps.get("thumbnails", {}).get("successful", 0),
        }

        if "publish" in steps and not steps["publish"].get("skipped"):
            summary["published"] = steps["publish"].get("successful", 0)

        return summary


def main():
    """Example usage"""
    import sys
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s: %(message)s'
    )

    parser = argparse.ArgumentParser(description="Video Pipeline Orchestrator")
    parser.add_argument("url", help="YouTube URL or video ID")
    parser.add_argument("--publish", action="store_true", help="Publish clips to YouTube")
    parser.add_argument("--privacy", choices=["public", "private", "unlisted"],
                        default="public", help="Privacy status (default: public)")
    parser.add_argument("--dry-run", action="store_true", help="Test without publishing")
    parser.add_argument("--output", default="output", help="Output directory")

    args = parser.parse_args()

    orchestrator = VideoPipelineOrchestrator(output_base=args.output)
    result = orchestrator.process_video(
        url_or_id=args.url,
        publish=args.publish,
        privacy=args.privacy,
        dry_run=args.dry_run
    )

    if result["success"]:
        print("\n" + "="*70)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("="*70)
        print(json.dumps(result["summary"], indent=2))
        print("="*70)
    else:
        print(f"\nERROR: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
