# Edited Video Pack

Source videos (from Google Drive) were merged, given a cinematic filter, and split into 6 equal parts.

## Filter applied
- Slight contrast boost (+6%)
- Saturation boost (+15%)
- Soft vignette
- Mild sharpening (unsharp)

## Outputs

| File | Duration | Resolution | Size |
|------|----------|------------|------|
| `output/merged_full_filtered.mp4` | ~40:17 | 1920×1080 | ~2.9 GB |
| `output/part1.mp4` | ~6:43 | 1920×1080 | ~500 MB |
| `output/part2.mp4` | ~6:43 | 1920×1080 | ~581 MB |
| `output/part3.mp4` | ~6:43 | 1920×1080 | ~477 MB |
| `output/part4.mp4` | ~6:43 | 1920×1080 | ~553 MB |
| `output/part5.mp4` | ~6:43 | 1920×1080 | ~498 MB |
| `output/part6.mp4` | ~6:43 | 1920×1080 | ~300 MB |

## Workflow used
1. Downloaded both Drive MP4s
2. Concatenated into one continuous video (`edit/merged_raw.mp4`)
3. Re-encoded each segment with the cinematic filter
4. Reassembled the 6 filtered parts into `merged_full_filtered.mp4`

These video files are too large for GitHub and are kept locally in this workspace under `output/`.
