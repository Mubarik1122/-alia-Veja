"""Upload the 10 car videos to YouTube: video 1 publishes immediately,
videos 2-10 are scheduled one per day at 18:00 UTC (per youtube_metadata.json).

Prerequisites (one-time setup):
  1. Create a Google Cloud project and enable "YouTube Data API v3".
  2. Create OAuth 2.0 credentials (Desktop app type).
  3. Provide credentials as environment variables (e.g. via Cursor Dashboard
     Cloud Agents > Secrets, or a local .env):
       YOUTUBE_CLIENT_ID
       YOUTUBE_CLIENT_SECRET
       YOUTUBE_REFRESH_TOKEN
     To obtain a refresh token, run once locally:
       python upload_to_youtube.py --auth
     which opens a browser consent flow and prints the token.

Usage:
  python upload_to_youtube.py --auth          # one-time OAuth setup
  python upload_to_youtube.py --upload-all    # upload all 10 videos per schedule
  python upload_to_youtube.py --upload 3      # upload only video #3
"""

import argparse
import json
import os
import sys
import time

METADATA_FILE = "youtube_metadata.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_credentials(interactive=False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    if not client_id or not client_secret:
        sys.exit("Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET first.")

    if refresh_token:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )
        creds.refresh(Request())
        return creds

    if not interactive:
        sys.exit("YOUTUBE_REFRESH_TOKEN missing. Run: python upload_to_youtube.py --auth")

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        },
        scopes=SCOPES,
    )
    creds = flow.run_local_server(port=8080)
    print("\nSave this as YOUTUBE_REFRESH_TOKEN:\n")
    print(creds.refresh_token)
    return creds


def build_service(creds):
    from googleapiclient.discovery import build

    return build("youtube", "v3", credentials=creds)


def upload_video(youtube, meta, defaults):
    from googleapiclient.http import MediaFileUpload

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
        body["status"]["privacyStatus"] = defaults["privacy_status_first_video"]
    else:
        # Scheduled: must be uploaded as private with a publishAt timestamp.
        body["status"]["privacyStatus"] = defaults["privacy_status_scheduled_videos"]
        body["status"]["publishAt"] = meta["publish_at"]

    media = MediaFileUpload(meta["file"], chunksize=8 * 1024 * 1024, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  upload {int(status.progress() * 100)}%", end="\r")
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auth", action="store_true", help="run one-time OAuth consent flow")
    parser.add_argument("--upload-all", action="store_true", help="upload every video per schedule")
    parser.add_argument("--upload", type=int, metavar="N", help="upload only video number N (1-10)")
    args = parser.parse_args()

    if args.auth:
        get_credentials(interactive=True)
        return

    with open(METADATA_FILE) as f:
        config = json.load(f)
    defaults = config["channel_defaults"]
    videos = config["videos"]

    if args.upload:
        videos = [v for v in videos if v["order"] == args.upload]
        if not videos:
            sys.exit(f"No video with order {args.upload}")
    elif not args.upload_all:
        parser.print_help()
        return

    youtube = build_service(get_credentials())
    for meta in videos:
        print(f"Uploading {meta['file']} -> {meta['title']}")
        print(f"  mode: {meta['publish_mode']}, publish_at: {meta['publish_at']}")
        resp = upload_video(youtube, meta, defaults)
        video_id = resp["id"]
        print(f"  done: https://www.youtube.com/watch?v={video_id}")
        time.sleep(2)


if __name__ == "__main__":
    main()
