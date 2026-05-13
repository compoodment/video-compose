# Render jobs

Render jobs are tiny handoff packets for a remote renderer/agent such as Vale on a GPU laptop.

The repo branch carries the reusable renderer code. A job folder carries the specific scene, output name, quality settings, and exact command for one render request.

Recommended handoff loop:

1. Coda creates a branch, e.g. `render/glass-orbit-cathedral-rtx3060`.
2. Coda adds/updates `render-jobs/<job-id>/` with `scene.json`, `run.sh`, and `README.md`.
3. Vale pulls that exact branch and runs the job script.
4. Vale returns `outputs/<job-id>.mp4`, `ffprobe.json`, and any error log.
5. Coda verifies frames/contact sheet and assembles/polishes with Vidkit if needed.

This keeps the instructions deterministic: Vale does not infer what to render; it checks out the branch/job ID Coda names and runs the script in that job folder.
