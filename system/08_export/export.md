# Export — upload-ready metadata

Fully manual, no specialist skill/agent yet. Runs after `07_assembly`
produces a final render. Proven once so far, on video 001.

## What gets produced, per video

In `videos/NNN-slug/` (siblings of `output/<slug>_v1.mp4`):

- **`description.md`** — locked title, full sourced description (citing
  the same sources as `notes.md`), chapter timestamps matching the final
  render's actual cut points, and tags.
- **`thumbnail_prompt.md`** — a generation prompt built from the locked
  character suffix (`system/04_shots/character.md`) plus the thumbnail
  style notes in `system/shared/references/channel_reports/2026-08-04_inkexplainer96_deep_dive.md`
  (character prominent and close, dramatic background, 1-3 word bold text,
  a warm/cool palette split for safe-vs-danger beats). Same generation
  pipeline as the shot images — paste into Flow, no reference image
  required.
- **`output/thumbnail.jpg`** — the generated thumbnail itself, sitting
  alongside the final render.

## What's not built yet

No automated spec-check or per-platform export-variant step (the sister
project's `07_export/export.py` does this for its own platforms) — this
channel currently targets a single upload target, so a real render at
1920x1080 H.264/AAC has been sufficient so far. Worth building a real
`export.md`/script pair here if multi-platform export becomes a real need.

No upload automation exists or is planned to exist automatically — same
convention as the sister project's `upload/`: explicit-only, human-invoked,
never chained onto another script.
