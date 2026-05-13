---
name: vidkit
description: Create, edit, compose, render, verify, or iterate scripted videos using the local vidkit/vidkit-helper ffmpeg toolkit, including generated scenes, media layers, text/lower-thirds, transitions, audio, keyframes, and glitch effects.
---

# Vidkit

Use this when computment asks to make or edit videos programmatically.

## Local tools

- Composer: `tools/vidkit-compose.py` or an installed `vidkit` wrapper.
- Edit helper: `tools/vidkit-helper.py` or an installed `vidkit-helper` wrapper.
- Optional 3D backend: `tools/vidkit-blender.py` / `vidkit blender ...` / `vidkit-blender`. It validates specs and emits Blender Python without Blender installed; rendering requires a `blender` binary.
- Verification: `tools/vidkit-verify.py` and selftests.
- Put rendered artifacts under `artifacts/vidkit/` or another task-specific output folder.

## Workflow

1. Decide whether the task is:
   - a template render (`vidkit template:<name> out.mp4`)
   - a starter from a built-in template (`vidkit init <name> spec.json`)
   - a custom JSON scene spec
   - a Blender-backed 3D scene spec (`vidkit blender validate/render/script ...`)
   - an edit of existing media with `vidkit-helper`
2. Validate specs before rendering when editing JSON:
   - `vidkit --validate-only spec.json`
   - fix schema/source/timing errors before chasing ffmpeg output
3. Prefer protected text/layout defaults:
   - use `lower_third` for readable captions
   - use panels behind small text
   - use `radius` for rounded panels/media masks
   - use `animate` presets for common entrances/exits before hand-authoring keyframes
   - keep glitch/effects off foreground text unless explicitly requested
4. Render with `vidkit` or `vidkit blender render` when 3D is the right backend.
5. Verify with `ffprobe`, a contact sheet, and one representative frame when visual quality matters.
6. Send the output video with the message tool.

## Built-in templates

- `lower-third`
- `motion-card`
- `glitch-card`
- `band-glitch`
- `media-card`
- `split-screen`

Examples:

```bash
vidkit templates
vidkit show template:media-card
vidkit init media-card artifacts/vidkit/starter.json
vidkit template:media-card artifacts/vidkit/media-card.mp4
```

## Verification

Run all core templates:

```bash
vidkit-verify
```

It renders known templates to `artifacts/vidkit/verify/`, probes streams, and creates contact sheets for key templates. Run `vidkit-selftest` after CLI/schema changes. For Blender backend changes, validate a spec and emit a script even when Blender is not installed:

```bash
vidkit blender validate examples/vidkit.blender-glass-orbit-cathedral.json
vidkit blender script examples/vidkit.blender-glass-orbit-cathedral.json /tmp/scene.py
python3 -m py_compile /tmp/scene.py
```

## Notes

- This is a scripted motion-graphics/video assembly engine, not an interactive editor.
- Keep the composer dependency-light: prefer Python stdlib + ffmpeg.
- `x`, `y`, `opacity`, and media `scale` keyframes are supported; `animate` offers preset fade/slide/pop entrances and exits.
- Do not publish/upload to GitHub without explicit confirmation.
