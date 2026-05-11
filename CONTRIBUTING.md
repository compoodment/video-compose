# Contributor standards

This project is a small scripted video toolkit. Contributions should keep it useful for AI assistants, command-line workflows, and fast creative iteration without turning it into a heavy editor framework.

## Core values

- **Creative leverage first:** features should make it easier to compose new kinds of videos, not just add another narrow demo.
- **Dependency-light by default:** prefer Python standard library plus `ffmpeg`/`ffprobe`. Add dependencies only when the value is large and the fallback story is clear.
- **Scriptable over interactive:** this is a render/assembly toolkit, not a GUI editor.
- **Readable artifacts:** specs, examples, generated files, and issue descriptions should be easy to inspect after context is gone.
- **Small verified slices:** land features in focused steps with examples and verification instead of broad rewrites.

## Issue quality standard

Issues are part of the project memory. A good issue should let someone resume work weeks later without needing the original chat.

Every feature issue should include:

1. **Problem / opportunity** — what creative or workflow gap this solves.
2. **User-facing shape** — what the CLI/spec/API should feel like from a caller's point of view.
3. **Examples** — at least one concrete spec snippet, command, or storyboard beat.
4. **Acceptance criteria** — observable conditions that make the issue done.
5. **Verification** — commands or artifact checks expected before closing.
6. **Non-goals** — what this issue deliberately does not try to solve.

Prefer issue titles that name the feature and outcome, e.g. `Add reusable comedy beat presets`, not `Improve video stuff`.

## Feature design checklist

Before implementing a feature, answer:

- Can this be expressed cleanly in JSON specs or a simple CLI command?
- Does it compose with existing scenes/layers/templates?
- Does it avoid hardcoding one demo's taste into the core engine?
- Is there a small example that proves the feature?
- Can verification run locally without private media?
- What happens when input is missing, malformed, or unsupported?

## Implementation standards

- Keep the core renderer dependency-light and understandable.
- Prefer explicit validation errors over silent fallback when a spec is wrong.
- Keep generated temporary files under the relevant output/artifact directory.
- Avoid hidden global state; specs should be portable when possible.
- Preserve backwards compatibility for existing examples/templates unless an issue explicitly calls for a breaking change.
- When adding a spec field, update docs/examples and validation together.
- Use deterministic behavior where practical; if randomness is useful, allow seeding or keep it local to generated visuals.

## Examples and templates

New user-facing features should usually include one of:

- a small example JSON under `examples/`
- a built-in template update
- a focused self-test fixture
- a rendered verification artifact from `vidkit-verify`

Examples should be public-safe and should not depend on private files from a local workspace.

## Verification expectations

Use the smallest meaningful gate for the change:

- JSON validation for spec/schema changes
- `python3 tools/vidkit-selftest.py` for behavioral renderer changes
- `python3 tools/vidkit-verify.py` for template/render coverage
- `ffprobe` checks for emitted video/audio streams
- contact sheets or representative frames for visual features

When visual quality matters, include a short note about what was inspected, not just that ffmpeg exited.

## Documentation expectations

Documentation should explain the caller-facing behavior, not internal history.

Update docs when a change affects:

- CLI commands
- JSON spec fields
- layer/scene capabilities
- templates
- verification workflow
- contributor or issue standards

Keep examples concise. If a concept needs a long explanation, prefer a dedicated doc section over stuffing comments into a giant sample.

## Pull request standard

A good PR description includes:

- what changed
- why it changed
- how to try it
- what was verified
- any known gaps or follow-up issues

Do not claim a creative/video feature is done without either a render artifact, a contact sheet/frame inspection, or a clear reason visual verification was not possible.

## Backlog hygiene

Backlog items should stay actionable:

- Split large ideas into coherent feature issues.
- Link related issues instead of duplicating context.
- Close or rewrite issues that no longer match the project direction.
- Prefer a few high-quality issues over many vague placeholders.
