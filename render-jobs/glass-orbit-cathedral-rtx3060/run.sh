#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
JOB_DIR="$ROOT/render-jobs/glass-orbit-cathedral-rtx3060"
OUT_DIR="$ROOT/outputs"
mkdir -p "$OUT_DIR"
OUT_MP4="$OUT_DIR/glass-orbit-cathedral-rtx3060.mp4"
PROBE="$OUT_DIR/glass-orbit-cathedral-rtx3060.ffprobe.json"
BLENDER_BIN="${BLENDER_BIN:-blender}"
python3 "$ROOT/tools/vidkit-blender.py" validate "$JOB_DIR/scene.json"
python3 "$ROOT/tools/vidkit-blender.py" render "$JOB_DIR/scene.json" "$OUT_MP4" --blender "$BLENDER_BIN" --keep-script "$OUT_DIR/glass-orbit-cathedral-rtx3060.blender.py"
ffprobe -v error -show_entries format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate -of json "$OUT_MP4" | tee "$PROBE"
echo "Rendered $OUT_MP4"
