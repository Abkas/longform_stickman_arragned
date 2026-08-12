---
name: topic-scout
description: Brainstorm and vet a new video topic/angle for the ink/stickman channel — checks format fit, competitive saturation, and citability before locking a topic. Use at the start of a new video cycle, before title-writer and script-writer.
---

# Topic Scout

You are picking the next video's topic for the `long-form-stickman-yt`
channel. This is stage 1 of the pipeline — everything downstream (title,
script) depends on getting this right. **Never rely on memory of these docs
from a past session** — re-read them fresh every time this skill runs, since
they're living references that can be revised.

## Read first, in this order

1. `assets/brain/structure.md` — read
   "Channel aim" and "Workflow for a new video" step 1. The core move: some
   *forced constraint* (weather, isolation, scarcity, disaster) ancient/
   historical people had to survive or adapt to.
2. `assets/references/channel_reports/2026-08-04_niche_landscape.md`
   — confirms which angles are already saturated by the copycat cluster
   (Ink Explainer, Deep Epoch, Before Civilization, Stick Plot, Brook
   Explains, Mack Explains, Before The Clock). The "rain" angle is
   confirmed taken — don't propose it or a thin variant of it.
3. `assets/references/channel_reports/2026-08-04_inkexplainer96_deep_dive.md`
   — the full catalog/performance pattern of the primary channel being
   replicated, for a sense of what's already been done well.
4. `CLAUDE.md` — read the "Video tracker" table so
   a new pitch doesn't collide with something already published or in
   progress.
5. `assets/brain/title.md` — skim the
   "non-negotiable" line at the bottom: title/topic must read as a
   sustained-or-existential threat, not a mundane occurrence. Topic and
   title are coupled — a topic that can't clear this bar isn't worth
   pitching even if it clears everything else.

## What to do

1. Brainstorm 3-5 candidate forced-constraint scenarios.
2. For each candidate, check it against three things pulled live from the
   docs above, not from memory:
   - Are there plausibly 4-6 *real, citable* sites/studies/dates that could
     fill the pillar structure (foundational tech → craft/production →
     art/culture → social payoff)? Don't propose something you can't
     imagine sourcing.
   - Is it meaningfully different from what the competitor cluster has
     already done (per the niche landscape report)?
   - Does it read as a sustained/existential threat, not a mundane
     inconvenience (per `title/strategy.md`'s stakes finding)?
3. Present the candidates to the user as a short list: one-line pitch + any
   risk/caveat each. Let them pick, or ask for a different direction if none
   land.
4. Once a topic is picked:
   - Find the next video number: list `videos/`
     and pick the next unused `NNN` (zero-padded, sequential).
   - Propose a `<slug>` for the folder name.
   - Do an initial sourcing pass: find 4-6 real, citable sites/studies/dates
     that map onto the pillar structure. Don't fabricate sources — if you
     can't find enough real ones, say so rather than inventing citations.
   - Write `videos/NNN-slug/notes.md` — mirror the
     existing convention (see another video's `notes.md` for the exact
     shape: a status line, the sourcing list with citation + one-line
     takeaway per source, and any early thoughts on the reframe/closing
     thesis).

## What NOT to do

- Do not edit `CLAUDE.md`'s video tracker table or
  `assets/brain/title.md`'s track record table — those stay
  user-maintained. Just tell the user what got locked so they can update
  them.
- Do not edit any file under `assets/brain/` — those are frozen references,
  read-only from this skill's perspective.
- Don't invent sources. A thin, honestly-sourced topic beats a
  well-populated but fabricated one — this channel's whole credibility
  angle depends on every claim being real and citable.

## Handoff

Once `notes.md` is written and the topic is locked, tell the user the next
step is the `title-writer` skill.
