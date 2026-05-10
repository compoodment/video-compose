---
name: video-compose
description: Create, edit, compose, render, verify, or iterate scripted videos using the local video-compose/video-kit ffmpeg toolkit, including generated scenes, media layers, text/lower-thirds, transitions, audio, keyframes, and glitch effects.
---

# Video Compose

Use this when computment asks to make or edit videos programmatically.

## Local tools

- Composer: `tools/video-compose.py` or an installed `video-compose` wrapper.
- Edit helper: `tools/video-kit.py` or an installed `video-kit` wrapper.
- Verification: `tools/video-compose-verify.py`.
- Put rendered artifacts under `artifacts/video-compose/` or another task-specific output folder.

## Workflow

1. Decide whether the task is:
   - a template render (`video-compose template:<name> out.mp4`)
   - a custom JSON scene spec
   - an edit of existing media with `video-kit`
2. Prefer protected text/layout defaults:
   - use `lower_third` for readable captions
   - use panels behind small text
   - keep glitch/effects off foreground text unless explicitly requested
3. Render with `video-compose`.
4. Verify with `ffprobe`, a contact sheet, and one representative frame when visual quality matters.
5. Send the output video with the message tool.

## Built-in templates

- `lower-third`
- `motion-card`
- `glitch-card`
- `band-glitch`
- `media-card`
- `split-screen`

Example:

```bash
video-compose template:media-card artifacts/video-compose/media-card.mp4
```

## Verification

Run all core templates:

```bash
video-compose-verify
```

It renders known templates to `artifacts/video-compose/verify/`, probes streams, and creates contact sheets for key templates.

## Notes

- This is a scripted motion-graphics/video assembly engine, not an interactive editor.
- Keep the composer dependency-light: prefer Python stdlib + ffmpeg.
- Do not publish/upload to GitHub without explicit confirmation.
