"""
Skeleton Channel — Full Automation Pipeline
Step 1: Claude generates topic + script + SEO
Step 2: ElevenLabs converts script to voiceover
Step 3: Build video with Archive.org footage + styled captions
Step 4: Upload to YouTube
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

from topic_generator import generate_topic_and_script
from voiceover import generate_voiceover
from video_builder import build_video
from youtube_uploader import upload_to_youtube
from logger import log

def run_pipeline():
    log("=" * 50)
    log(f"Pipeline started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 50)

    # STEP 1 — Generate script
    log("\n[STEP 1] Generating anime theory script + SEO via Claude...")
    content = generate_topic_and_script("anime theory shorts")
    log(f"  Title   : {content['title']}")
    log(f"  Keyword : {content['keyword']}")
    log(f"  Script  : {len(content['script'])} characters")

    # STEP 2 — Generate voiceover
    log("\n[STEP 2] Generating voiceover via ElevenLabs...")
    audio_path = generate_voiceover(content["script"])
    log(f"  Audio saved: {audio_path}")

    # STEP 3 — Build video
    log("\n[STEP 3] Building video...")
    temp_video_path = build_video(
        audio_path=audio_path,
        title=content["title"],
        script=content["script"],
        anime_series=content.get("anime_series", "one_piece")
    )
    
    # Move to Desktop for easy access (handles OneDrive too)
    import shutil
    home = os.environ.get("USERPROFILE") or os.environ.get("HOME") or os.path.expanduser("~")
    desktop_options = [
        os.path.join(home, "Desktop"),
        os.path.join(home, "OneDrive", "Desktop"),
        os.path.join(home, "OneDrive - Personal", "Desktop")
    ]
    
    desktop_path = next((d for d in desktop_options if os.path.exists(d)), home)
    video_filename = f"AnimeTheory_Short_{datetime.now().strftime('%H%M%S')}.mp4"
    final_video_path = os.path.join(desktop_path, video_filename)
    
    try:
        shutil.move(temp_video_path, final_video_path)
        log(f"  SUCCESS! Video saved to: {final_video_path}")
    except Exception:
        shutil.copy(temp_video_path, final_video_path)
        log(f"  SUCCESS! Video copied to: {final_video_path}")

    # STEP 4 — Upload to YouTube
    log("\n[STEP 4] Uploading to YouTube...")
    try:
        video_id = upload_to_youtube(
            video_path=final_video_path,
            title=content["title"],
            description=content["description"],
            tags=content["tags"],
            thumbnail_text=content["title"]
        )
        log(f"  Uploaded! https://youtube.com/shorts/{video_id}")
    except Exception as e:
        log(f"  (Note: Auto-upload skipped because: {e})")
        log(f"  Your video is ready on your Desktop!")
    log("\nPipeline complete.")

if __name__ == "__main__":
    run_pipeline()
