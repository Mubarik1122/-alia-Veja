"""Upload all 10 videos to YouTube per youtube_metadata.json.

Video 1 -> public immediately. Videos 2-10 -> private with publishAt
(YouTube auto-publishes each at the scheduled time, one per day).

Tokens are read from /workspace/.youtube_tokens.json (never committed).
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
METADATA_FILE = "youtube_metadata.json"


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


def upload(youtube, meta, defaults):
    tags = list(defaults["common_tags"]) + meta["tags"]
    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": tags,
            "categoryId": defaults["category_id"],
            "defaultLanguage": defaults["default_language"],
        },
        "status": {
            "selfDeclaredMadeForKids": defaults["made_for_kids"],
            "license": defaults["license"],
        },
    }
    if meta["publish_mode"] == "immediate":
        body["status"]["privacyStatus"] = "public"
    else:
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = meta["publish_at"]

    media = MediaFileUpload(meta["file"], chunksize=4 * 1024 * 1024, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  {int(status.progress() * 100)}%", end="\r", flush=True)
    return response


def main():
    with open(METADATA_FILE) as f:
        config = json.load(f)
    defaults = config["channel_defaults"]
    youtube = get_youtube()

    only = int(sys.argv[1]) if len(sys.argv) > 1 else None
    results = []
    for meta in config["videos"]:
        if only and meta["order"] != only:
            continue
        print(f"[{meta['order']}/10] {meta['title'][:60]}")
        print(f"        mode={meta['publish_mode']} publish_at={meta['publish_at']}")
        try:
            resp = upload(youtube, meta, defaults)
            vid = resp["id"]
            print(f"        OK -> https://www.youtube.com/watch?v={vid}")
            results.append({"order": meta["order"], "id": vid, "mode": meta["publish_mode"], "publish_at": meta["publish_at"]})
        except HttpError as e:
            print(f"        FAILED: {e.resp.status} {e.content.decode()[:300]}")
            results.append({"order": meta["order"], "error": f"{e.resp.status}"})
            if e.resp.status in (403, 429):
                print("        quota/rate limit hit - stopping; rerun later to continue")
                break
        time.sleep(2)

    with open("upload_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSummary:")
    for r in results:
        print(" ", r)


if __name__ == "__main__":
    main()
