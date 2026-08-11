"""Upload and schedule the 3 weekly chaos episodes.

Credentials from env vars or .youtube_tokens.json (never committed).
"""

import json
import os
import sys
import time

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

CLIENT_ID = os.environ["YOUTUBE_CLIENT_ID"]
CLIENT_SECRET = os.environ["YOUTUBE_CLIENT_SECRET"]
TOKEN_FILE = "/workspace/.youtube_tokens.json"
METADATA_FILE = "weekly_metadata.json"


def get_youtube():
    with open(TOKEN_FILE) as f:
        tokens = json.load(f)
    creds = Credentials(
        token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    if not creds.valid:
        creds.refresh(Request())
        tokens["access_token"] = creds.token
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f)
    return build("youtube", "v3", credentials=creds)


def upload_video(youtube, meta):
    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"] + meta["hashtags"],
            "categoryId": "20",  # Gaming
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": meta["publish_at"],
            "selfDeclaredMadeForKids": False,
            "license": "youtube",
        },
    }
    media = MediaFileUpload(meta["file"], chunksize=8 * 1024 * 1024, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  upload {int(status.progress() * 100)}%", end="\r", flush=True)
    return response


def set_thumbnail(youtube, video_id, path):
    media = MediaFileUpload(path, mimetype="image/jpeg")
    return youtube.thumbnails().set(videoId=video_id, media_body=media).execute()


def main():
    with open(METADATA_FILE) as f:
        config = json.load(f)
    youtube = get_youtube()
    results = []
    for meta in config["videos"]:
        print(f"[{meta['order']}/3] {meta['title'][:65]}")
        print(f"        schedule: {meta['publish_at']}")
        try:
            resp = upload_video(youtube, meta)
            vid = resp["id"]
            print(f"        uploaded: https://www.youtube.com/watch?v={vid}")
            thumb_ok = False
            try:
                set_thumbnail(youtube, vid, meta["thumbnail"])
                thumb_ok = True
                print("        thumbnail: set")
            except HttpError as e:
                print(f"        thumbnail: skipped ({e.resp.status}) — set manually in Studio")
            results.append({
                "order": meta["order"],
                "id": vid,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "publish_at": meta["publish_at"],
                "title": meta["title"],
                "thumbnail_set": thumb_ok,
            })
        except HttpError as e:
            print(f"        FAILED: {e.resp.status} {e.content.decode()[:400]}")
            results.append({"order": meta["order"], "error": str(e.resp.status)})
            if e.resp.status in (403, 429):
                break
        time.sleep(2)
    with open("weekly_upload_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nDone:")
    for r in results:
        print(" ", r)


if __name__ == "__main__":
    main()
