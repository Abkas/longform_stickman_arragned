# CLAUDE.md — longform_stickman_arragned

Orientation doc for future Claude Code sessions working on this channel.
This folder is the **complete, standalone home** for the project — brain
files, pipeline code, video content, and the orchestrator (skills/agents)
config all live here together.

**Read `pipeline.md` (project root) before working on any stage.** It's the
authoritative description of the workflow's order, why it's shaped that
way, and — as of 2026-08-13 — a real status table of what's automated vs.
manual vs. still broken. This file is for conventions that span *multiple*
stages; anything stage-specific belongs in that stage's own doc under
`system/<NN_stage>/`, not here.

**Structure note (2026-08-13):** everything pipeline-related now lives
under `system/<NN_stage>/`, one numbered folder per stage, modeled on the
`movie_auto_narration_fb` sister project's layout — nothing stage-specific
lives loose at the top level anymore. This replaced the old flat
`assets/brain/`, `assets/references/`, `assets/character/`, and `pipeline/`
folders. See `pipeline.md`'s stage table for what moved where.

## What this channel is

A video-sharing channel producing long-form (~10-15 min) animated
"ink"/stickman-style explainer videos — script → voiceover → animation →
final render — replicating the real `@Inkexplainer96` channel's format,
monetized via ad-network/YPP revenue.

## Project & Persona (frozen, one-time — locked, not re-decided per video)

- **Voice/tone** — `system/03_script/persona.md`: a three-way blend —
  Fireship's fast/sarcastic/self-aware energy as the default texture,
  OverSimplified's accuracy-first backbone underneath the jokes, Sam
  O'Nella's flat-deadpan delivery reserved specifically for genuinely dark
  or absurd facts. Locked 2026-08-04.
- **Visual design** — `system/04_shots/character.md`: a simple stick
  figure, natural messy brown hair, flat pale skin, bold black outlines, no
  photorealism anywhere. Locked 2026-08-09 (third pass) — **but see that
  file's "Video 002 drift" section: video 002's actual generated batch
  drifted off this design (full-bodied cartoon instead of a stick figure)
  even after a 2026-08-13 wording fix, so "locked" describes the intended
  design, not a guarantee every batch will hit it.**

These two files (plus `structure.md`, `title.md`, `voice.md`, `shot.md`
— the rest of the reference set under `system/`) are genuinely frozen —
skills/agents read them, none of them edit them (see each skill/agent's own
"What NOT to do" section).

## Skills vs. agents

**Skills** (`topic-scout`, `title-writer`, `script-writer`) run in one
continuous conversation — stay talking to the same session as it works
through each stage. **Agents** (`shot-list-builder`, `visual-generator`) run
isolated — dispatched separately for bulky/mechanical/long-running work,
reporting back a short result instead of filling the conversation.
`07_assembly`'s `assemble.py` and `08_export` are currently manual/scripted
with no dedicated skill or agent wrapping them yet.

## Folder structure

- `pipeline.md` — the pipeline's authoritative order + reasoning + status.
- `system/<NN_stage>/` — one folder per pipeline stage, each with its own
  doc and (where applicable) its own code/config. See `pipeline.md` for the
  full stage list.
- `system/shared/references/` — competitive research (channel deep-dives,
  niche-landscape survey, transcripts, thumbnail images) used across
  multiple stages, mainly `01_topic` and `03_script`.
- `videos/NNN-<slug>/` — one folder per video, **unchanged by the 2026-08-13
  restructure** (this is per-video runtime data, not pipeline definition —
  same distinction the sister project draws with its own `data/`):
  `notes.md` (sourcing), `title.md`, `script.md` (locked narration),
  `shot_list.md` (machine-parseable scene breakdown), `generate/generate_image.md`
  + `generate/generate_voice.md` (build artifacts, regenerated whenever
  script/shot-list changes), `audio/` or `generate/generated/voice/`
  (ElevenLabs output), `generate/generated/images/` (raw AI image/clip
  output — see `pipeline.md`'s "Load-bearing formats" for the exact naming
  convention `assemble.py` depends on), `generate/render_clips/` (per-shot
  rendered clips, an `07_assembly` intermediate), `testing/` (style-suffix
  iteration rounds), `output/` (final render + thumbnail), `description.md`
  + `thumbnail_prompt.md` (upload-ready metadata, see `system/08_export/export.md`).
- `.claude/skills/`, `.claude/agents/` — the specialist files themselves,
  unchanged location (Claude Code expects them here).

## Video tracker

| # | Slug | Status | Notes |
|---|------|--------|-------|
| 001 | toba-supervolcano | **Upload-ready** | "How Did Ancient Humans Survive Earth's Worst Volcano?" — myth-busting angle. Script locked (2,451 words, ~12 min). 98 shots, all generated, VO generated, finished render exists (`output/001-toba-supervolcano_v2.mp4` + thumbnail). `description.md` locked. Treated as a frozen historical record during the 2026-08-13 restructure — a handful of exact-match paths got swept up in the global find/replace, but several already-stale pre-flatten paths from before that (e.g. `assets/brain/visuals/flow_workflow.md`, `assets/brain/visuals/character_design.md`) were deliberately left alone rather than fully repaired, since this is history, not a live doc. |
| 002 | built-to-starve | **In progress, real problems found** | Script locked (2,561 words). `shot_list.md`: 111 shots — but its `- Duration:` fields are still computed at an assumed 207 WPM; the real ElevenLabs audio measured 166 WPM (24.6% overrun), not yet fixed at the source (see `pipeline.md`'s stage-04 status). First image batch (browser batch extension) came back 47% wrong (52/111 shots) from a queue-desync bug — root-caused and the *doc* gaps that let invented text through are fixed (`system/04_shots/character.md`/`shot.md`), but a second regenerated batch still shows the character off the locked stick-figure design. A rough assembly exists (`output/002-built-to-starve_v1.mp4`, ~15:24) built from a mixed two-folder image source (`generate/image_v2/vdieo__0022222_v1` for shots 1-87, `generate/image_v2/asdf` for shots 88-111) via `assemble.py` — **not upload-ready**: character style still wrong, duration-sync is only a proportional approximation, motion ratio is low (5/111 shots). |
| 004 | psychopath-problem | **Short done, long-form script still a draft** | Title locked (user's exact phrasing, deliberately skips the "must name Ancient/Early Humans" non-negotiable — see `title.md`): "Why Didn't Evolution Get Rid of Psychopaths?" `notes.md`: 6 real sources (Mealey 1995 frequency-dependent selection, MAOA "warrior gene," psychopathy prevalence meta-analysis, game theory/tit-for-tat, UCSB cheater-detection, corporate-leadership prevalence). `script_draft.md`: full long-form draft, 2,485 words (~12.0 min), NOT yet locked/reviewed by the user — work paused here when the user asked to try a short/witty tone experiment instead. **`short_v1/`: this project's first-ever YouTube Shorts-format video, fully built and rendered 2026-09-12** — `output/short_v1_v1.mp4` (1080x1920 vertical, 55.36s, real word-level sync). Required two new pieces of infrastructure: `flow_batch_driver.py` gained a `--aspect-ratio` flag (Flow has a real per-session aspect-ratio UI control that was previously hardcoded to always select 16:9 landscape — confirmed and fixed), and `assemble.py` gained a `--vertical` flag (1080x1920 output). `short_v1/description.md`: first Shorts-specific export doc (no chapters, `#Shorts` hashtag, no custom thumbnail needed). **Next decision needed: return to finishing/locking the long-form `script_draft.md`, or treat the Short as this video's whole output.** |
| 003 | stoned-ape | **In progress** | Script locked (2,435 words, "Ancient Humans Got Stoned and Accidentally Invented Humanity"). `shot_list.md`: 262 shots. Images: automated multi-account Flow pipeline (`system/05_visuals/run_full_batch.py` + `flow_batch_driver.py`, 8-account rotation with adaptive quota cooldowns, running unattended via a systemd `--user` timer every 15 min) — chunked verify-before-promote design, cross-shot duplicate-content detection with auto-regen. See `system/05_visuals/accounts.local.md` for the account list. Voice: fully automated for the first time this channel (`system/06_voice/voice_generate.py`, new 2026-09-12) — narration.mp3 generated using ElevenLabs' "George" premade voice (see `voice.md`'s decision log for why, and why it deliberately breaks from video 001's voice). **Real narration measured 1057.6s (~17.6 min) vs. `structure.md`'s 11-13 min target — George's natural pace (~135-140 WPM) can't reach the channel's ~205-210 WPM target even at max `speed`; user's explicit call was to keep the voice and accept the longer runtime, not switch voices or cut the script.** Full visual QC pass done (2 background-subagent review rounds): 82/262 shots flagged for invented on-screen text (Flow adding captions/fake data the prompt never specified — a real, repeated failure mode, not noise); a plain re-roll with identical prompts only fixed 18/82 — user's explicit call was to accept the remaining 64 as-is rather than fix the prompt wording. **Assembled and rendered 2026-09-12**: `output/003-stoned-ape_v1.mp4` (152MB, 17.63 min) via `assemble.py`, now using real ElevenLabs word-level timestamps for exact per-shot sync (new capability — see `assembly.md`'s former "Known limitation", now fixed for any video with a `narration_timestamps.json`) instead of the old proportional-duration-scaling approximation every prior video used. Final duration matches the real audio to within 0.07s. **Not yet reviewed end-to-end by the user or upload-ready** — this is a first rough assembly. |

## Known gaps

- Video 002's character-style fix is blocked on a working `GEMINI_API_KEY`
  (current key returns 401) — the reference-image-attach approach
  (`system/04_shots/character.md`'s documented fallback) hasn't actually
  been tested yet because of this. **The plan itself got a real upgrade
  2026-08-22** (see that file's "Research: the real reference-image
  mechanism" section) — not just "attach an image and hope": a 3-image
  turnaround/expression reference set (`generate_character_reference.py`,
  rewritten) plus `generate_visuals.py` now defaulting character shots to
  `gemini-3-pro-image-preview`, the model tier that documents multi-image
  character-reference consistency as a first-class feature. Still can't
  verify any of it works until the key issue is resolved.
- No automated way to get real per-shot/per-word narration timestamps —
  `06_voice` is fully manual (ElevenLabs web app), so `07_assembly` can only
  approximate duration sync by scaling, not retime against real speech. See
  `system/07_assembly/assembly.md`'s "Known limitation" section.
- `videos/001-toba-supervolcano.zip` archive's relationship to the real
  folder next to it still hasn't been confirmed (stale duplicate vs.
  intentional backup) — flagged 2026-08-12, still unresolved.
- No `003-<slug>` video started yet.

## Working notes

- This file does not auto-update — update it directly as pipeline decisions
  get made or videos progress.
- Next concrete step on video 002: get a working `GEMINI_API_KEY` (or
  switch to the manual Flow reference-image path, attaching the full
  `host_reference_*.png` set to Flow's "Ingredients" feature rather than
  one image) and actually test whether the reference-set + pro-model
  approach fixes the stick-figure drift before spending more on a full
  re-render.
