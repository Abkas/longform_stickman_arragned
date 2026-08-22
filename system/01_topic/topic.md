# Topic — picking and vetting a video idea

Handled by the `topic-scout` skill, run conversationally (stays in the same
session through to `title-writer`/`script-writer`, doesn't get dispatched
as an isolated agent).

## Why there's no dedicated brain file here

Every other stage folder under `system/` has at least one locked reference
doc specific to that stage. This one doesn't, on purpose: topic vetting
isn't a fixed formula the way title-writing or narration structure are —
it's a judgment call against two things that already live elsewhere:

- **Format fit + the worked-example teardown** — `system/03_script/structure.md`'s
  checklist for whether an angle actually suits the channel's 5-part
  structure.
- **Competitive saturation** — `system/shared/references/channel_reports/`,
  especially `2026-08-04_niche_landscape.md`'s survey of what the copycat
  cluster has already covered (e.g. the "rain" angle is flagged there as
  saturated — avoid re-treading it without a genuinely different angle).

If a real, reusable topic-vetting formula emerges after enough videos (the
same way `title.md`'s formula got distilled from a full competitor catalog),
it belongs in a new `topic.md` doc here — until then, this file is just the
pointer explaining why that doesn't exist yet.

## Output

No file — a topic gets locked conversationally, then immediately feeds
`02_title`/`03_script`. The first artifact that actually gets written is
`videos/NNN-slug/notes.md` (sourcing), once title-writer or script-writer
starts building on the locked topic.
