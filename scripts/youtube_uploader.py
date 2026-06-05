"""
Uploads the finished MP4 to YouTube using the Data API v3.
Uses a refresh token (no browser needed once set up).

How to get your refresh token: see SETUP.md
"""

import os
import json
import tempfile
import requests
from pathlib import Path

YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
YOUTUBE_THUMBNAIL_URL = "https://www.googleapis.com/youtube/v3/thumbnails/set"

# Optimal upload time: schedule the workflow for 13:00 UTC (good for US afternoon)
CATEGORY_ID = "22"   # 22 = People & Blogs (best fit for skeleton story Shorts)
                      # 27=Education, 24=Entertainment, 28=Science&Tech

PRIVACY = "public"   # "public" | "private" | "unlisted"


def get_access_token() -> str:
    """Exchange refresh token for a short-lived access token with retry mechanism."""
    import time
    last_err = None
    for attempt in range(4):
        try:
            resp = requests.post(YOUTUBE_TOKEN_URL, data={
                "client_id": os.environ["YOUTUBE_CLIENT_ID"],
                "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
                "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"],
                "grant_type": "refresh_token"
            }, timeout=30)
            if resp.status_code == 200:
                return resp.json()["access_token"]
            print(f"  Token refresh warning (Attempt {attempt+1}): Status {resp.status_code} - {resp.text}")
            last_err = RuntimeError(f"Token refresh failed: {resp.text}")
        except Exception as e:
            print(f"  Token refresh connection/SSL warning (Attempt {attempt+1}): {e}")
            last_err = e
        time.sleep(3)
    raise last_err



def upload_to_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    thumbnail_text: str = ""
) -> str:
    """Upload video and return the YouTube video ID."""
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    # ── Metadata ──────────────────────────────────────────────────────────────
    metadata = {
        "snippet": {
            "title": title[:100],          # YouTube max title length
            "description": description[:5000],
            "tags": tags[:30],             # YouTube allows up to 500 chars of tags
            "categoryId": CATEGORY_ID,
            "defaultLanguage": "en"
        },
        "status": {
            "privacyStatus": PRIVACY,
            "selfDeclaredMadeForKids": False,
            "madeForKids": False
        }
    }

    # ── Resumable upload ──────────────────────────────────────────────────────
    file_size = Path(video_path).stat().st_size

    init_resp = None
    last_err = None
    import time
    for attempt in range(4):
        try:
            init_resp = requests.post(
                f"{YOUTUBE_UPLOAD_URL}?uploadType=resumable&part=snippet,status",
                headers={**headers, "Content-Type": "application/json",
                         "X-Upload-Content-Type": "video/mp4",
                         "X-Upload-Content-Length": str(file_size)},
                json=metadata,
                timeout=30
            )
            if init_resp.status_code in (200, 201):
                break
            print(f"  Upload init warning (Attempt {attempt+1}): Status {init_resp.status_code} - {init_resp.text}")
            last_err = RuntimeError(f"Upload init failed: {init_resp.text}")
        except Exception as e:
            print(f"  Upload init connection/SSL warning (Attempt {attempt+1}): {e}")
            last_err = e
        time.sleep(3)
    else:
        raise last_err

    upload_url = init_resp.headers["Location"]

    # Upload in 10 MB chunks for reliability
    chunk_size = 10 * 1024 * 1024
    uploaded = 0
    video_id = None

    with open(video_path, "rb") as f:
        while uploaded < file_size:
            chunk = f.read(chunk_size)
            end = uploaded + len(chunk) - 1

            chunk_resp = requests.put(
                upload_url,
                headers={
                    **headers,
                    "Content-Range": f"bytes {uploaded}-{end}/{file_size}",
                    "Content-Type": "video/mp4"
                },
                data=chunk,
                timeout=120
            )

            if chunk_resp.status_code in (200, 201):
                video_id = chunk_resp.json()["id"]
                break
            elif chunk_resp.status_code == 308:
                uploaded = int(chunk_resp.headers.get("Range", f"0-{end}").split("-")[1]) + 1
                pct = int(uploaded / file_size * 100)
                print(f"  Upload progress: {pct}%")
            else:
                raise RuntimeError(f"Chunk upload failed: {chunk_resp.text}")

    if not video_id:
        raise RuntimeError("Upload completed but no video ID returned.")

    print(f"  Video ID: {video_id}")
    return video_id
