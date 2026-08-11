# Publishing the 10 Car Shorts to YouTube

All metadata is ready in `youtube_metadata.json`. Uploads are handled by `upload_to_youtube.py`.

## Publish plan

| # | Video | Mode | Publish date (18:00 UTC) |
|---|-------|------|--------------------------|
| 1 | BMW M4 — Pearl White | Immediate | 2026-08-11 (today, on upload) |
| 2 | Porsche 911 GT3 — Jet Black | Scheduled | 2026-08-12 |
| 3 | Lamborghini Huracán — Racing Red | Scheduled | 2026-08-13 |
| 4 | Ferrari 488 Pista — Electric Blue | Scheduled | 2026-08-14 |
| 5 | McLaren 720S — Matte Grey | Scheduled | 2026-08-15 |
| 6 | Audi R8 — Metallic Silver | Scheduled | 2026-08-16 |
| 7 | Mercedes-AMG GT — Deep Emerald Green | Scheduled | 2026-08-17 |
| 8 | Nissan GT-R — Sunset Orange | Scheduled | 2026-08-18 |
| 9 | Chevrolet Corvette C8 — Titanium Gold | Scheduled | 2026-08-19 |
| 10 | Mustang Shelby GT500 — Midnight Purple | Scheduled | 2026-08-20 |

## One-time setup (what's needed)

1. **Google Cloud project** with **YouTube Data API v3** enabled (free).
2. **OAuth 2.0 credentials** (Desktop app type) from that project.
3. Provide these three secrets (Cursor Dashboard → Cloud Agents → Secrets, or a local `.env`):
   - `YOUTUBE_CLIENT_ID`
   - `YOUTUBE_CLIENT_SECRET`
   - `YOUTUBE_REFRESH_TOKEN`
4. To generate the refresh token (one-time, on any machine with a browser):
   ```bash
   pip install google-api-python-client google-auth-oauthlib
   export YOUTUBE_CLIENT_ID=... YOUTUBE_CLIENT_SECRET=...
   python upload_to_youtube.py --auth
   ```
   Sign in with the YouTube channel's Google account and copy the printed token.
5. **Channel requirements for scheduling:** the YouTube account must be phone-verified
   (YouTube Studio → Settings → Channel → Feature eligibility). Scheduling requires
   the "Intermediate features" verification.

## Run the uploads

```bash
pip install google-api-python-client google-auth-oauthlib
python upload_to_youtube.py --upload-all    # uploads all 10 per schedule
python upload_to_youtube.py --upload 3      # or a single video
```

Video 1 goes live immediately. Videos 2–10 are uploaded as **private with a
`publishAt` timestamp** — YouTube automatically makes each one public at its
scheduled time. They will appear in YouTube Studio as "Scheduled".

## Notes

- Default API quota (10,000 units/day) allows ~6 video uploads/day; uploading all
  10 at once requires a quota increase, or run the upload across two days.
  Uploading one per day fits the default quota comfortably.
- Titles, descriptions, hashtags, and tags can be edited per video in
  `youtube_metadata.json` before uploading.
- To change the daily publish time, edit `publish_time_local`/`publish_timezone`
  and each video's `publish_at` in `youtube_metadata.json`.

## Manual alternative

If you prefer not to use the API: upload each MP4 from `output/` in YouTube
Studio, copy the title/description/hashtags from `youtube_metadata.json`, set
video 1 to "Public", and set videos 2–10 to "Schedule" with the dates above.
