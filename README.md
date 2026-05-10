# video-compose

A tiny scripted motion-graphics/video assembly toolkit for AI assistants and command-line workflows.

It is not an interactive editor. It renders videos from JSON scene specs using Python + ffmpeg: generated visuals, media layers, text/lower-thirds, transitions, audio, keyframes, and glitch effects.

## Requirements

- Python 3.11+
- `ffmpeg` and `ffprobe` on PATH

No Python package dependencies are required.

## Quick start

```bash
python3 tools/video-compose.py template:media-card out.mp4
python3 tools/video-compose.py template:band-glitch glitch.mp4
python3 tools/video-compose-verify.py
```

Core templates:

- `lower-third`
- `motion-card`
- `glitch-card`
- `band-glitch`
- `media-card`
- `split-screen`

## Custom specs

Render a JSON spec:

```bash
python3 tools/video-compose.py examples/video-compose.lower-third-example.json out.mp4
```

Specs can define generated scenes, layered media, text/panels, keyframes, transitions, generated audio, and audio-bed mixing.

## Helper tool

`tools/video-kit.py` provides practical ffmpeg helpers: trim, contact sheets, frame extraction, GIF export, mux audio, burn subtitles, crop/scale/rotate/speed/concat, title cards, captions, fades, slideshow, and remix.

## OpenClaw skill

A draft AgentSkill is included at `skill/SKILL.md` for local OpenClaw usage.

## Status

Early and intentionally small. Built to stay dependency-light and assistant-friendly.
