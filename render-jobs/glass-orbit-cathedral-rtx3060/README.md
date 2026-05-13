# glass-orbit-cathedral-rtx3060

Purpose: smoke-test the Blender backend on Vale/computment's RTX3060 laptop at better quality than Coda's CPU-only VPS.

Expected renderer:

- Blender installed on the laptop.
- Prefer Cycles + OptiX/CUDA enabled in Blender Preferences → System → Cycles Render Devices.
- 6GB VRAM should be enough for this starter scene.

Run from the repository root:

```bash
render-jobs/glass-orbit-cathedral-rtx3060/run.sh
```

Outputs:

- `outputs/glass-orbit-cathedral-rtx3060.mp4`
- `outputs/glass-orbit-cathedral-rtx3060.ffprobe.json`

Return both to Coda for QA/assembly.
