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

## Thumbnail checklist (locked 2026-08-22, CTR research, sourced)

`thumbnail_prompt.md` and the final `output/thumbnail.jpg` should hit all
of these, not just "reads as the genre at a glance" (`structure.md`'s
checklist item 4 points here for the specifics):

1. **≤4 words of on-thumbnail text.** Text-heavy thumbnails measurably
   underperform minimal-text ones — this tightens the existing "1-3 word
   bold text" convention inherited from the Ink Explainer deep-dive, now
   with a hard ceiling, not just a stylistic default.
2. **The character's face carries a strong, legible emotion** — surprise,
   alarm, or curiosity read best; a neutral/calm expression is a wasted
   opportunity on a thumbnail specifically (calm/content expressions are
   fine and correct for in-video shots, this is thumbnail-only).
3. **Thumbnail and title must not repeat the same information.** The pair
   works as a unit: the thumbnail opens a curiosity gap (a striking image,
   an unresolved "before" without the "after"), the title gives just enough
   context to make the click worth it. Showing the payoff or the full
   premise in both wastes the pairing — pick which one carries the "what,"
   and let the other carry the "why should I care."
4. Character prominent and close, dramatic background, warm/cool palette
   split for safe-vs-danger beats — unchanged from the existing convention.

## Compliance note: AI-content disclosure (checked 2026-08-22)

YouTube's "Altered or Synthetic Content" policy (full enforcement since
January 2026) only requires a disclosure label for content realistic
enough to be mistaken for actual footage of a real person/place/event.
Confirmed directly against the policy's own stated exemptions: obviously
animated/cartoon content and AI-generated voiceover are both explicitly
**exempt** — this channel's entire output (stickman animation + ElevenLabs
narration) doesn't trigger the requirement. Nothing to add to the upload
flow for this. The actual monetization risk for this genre is the
separate "inauthentic content" policy (mass-produced, templated,
near-identical videos) — not AI use itself — which is exactly what the
per-video sourcing rigor already locked in `system/03_script/structure.md`
(real, citable sites/studies/dates per video) defends against. Keep doing
that; don't start treating AI disclosure as a to-do, it isn't one.

## What's not built yet

No automated spec-check or per-platform export-variant step (the sister
project's `07_export/export.py` does this for its own platforms) — this
channel currently targets a single upload target, so a real render at
1920x1080 H.264/AAC has been sufficient so far. Worth building a real
`export.md`/script pair here if multi-platform export becomes a real need.

No upload automation exists or is planned to exist automatically — same
convention as the sister project's `upload/`: explicit-only, human-invoked,
never chained onto another script.
