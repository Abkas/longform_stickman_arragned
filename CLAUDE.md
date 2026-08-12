# CLAUDE.md — longform_stickman_arragned

Orientation doc for future Claude Code sessions working on this channel.
This folder is the **complete, standalone home** for the project — brain
files, pipeline code, video content, and the orchestrator (skills/agents)
config all live here together. It replaces an earlier two-folder split
(`longform_stickman_arragned/` as thin config + a sibling
`long-form-stickman-yt/` for content) — that split felt cramped/fragmented
in practice, so everything was migrated into one folder on 2026-08-12. The
old folder still exists on disk as an untouched, unused safety-net copy but
should be treated as retired — work happens here now.

## What this channel is

A video-sharing channel producing long-form (~10-15 min) animated
"ink"/stickman-style explainer videos — script → voiceover → animation →
final render — replicating the real `@Inkexplainer96` channel's format,
monetized via ad-network/YPP revenue.

## Project & Persona (frozen, one-time — locked, not re-decided per video)

- **Voice/tone** — `assets/brain/persona.md`: a three-way blend —
  Fireship's fast/sarcastic/self-aware energy as the default texture,
  OverSimplified's accuracy-first backbone underneath the jokes, Sam
  O'Nella's flat-deadpan delivery reserved specifically for genuinely dark
  or absurd facts. Locked 2026-08-04.
- **Visual design** — `assets/brain/visuals/character.md`: a simple
  stick figure, natural messy brown hair (specific locked wording after 3
  real testing rounds — see the file for the full history of what went
  wrong and why), flat pale skin, bold black outlines, no photorealism
  anywhere. Locked 2026-08-09 (third pass).

These two files are genuinely frozen — `script-writer`, `title-writer`, and
`shot-list-builder` all read them, none of them edit them.

## Format reference

- Script structure + title/hook checklist + worked-example teardown:
  `assets/brain/structure.md`.
- Title formula, data-derived from a full competitor catalog:
  `assets/brain/title.md`.
- Narration pacing + ElevenLabs technique: `assets/brain/voice.md`.
- Visual generation workflow (shot density, self-contained prompts, style
  suffixes): `assets/brain/visuals/workflow.md`.
- Competitive research: `assets/references/channel_reports/` (deep-dive on
  the primary benchmark channel + a wider niche-landscape survey),
  `assets/references/transcripts/`, `assets/references/images/`.

## Pipeline stages and who handles them

| Stage | Handled by | Type | Reads |
|---|---|---|---|
| 1. Topic | `topic-scout` | skill | `structure.md`, `references/channel_reports/*` |
| 2. Title | `title-writer` | skill | `title.md`, `structure.md`, `persona.md` |
| 3. Script | `script-writer` | skill | `structure.md`, `persona.md`, `voice.md` |
| 4. Shot list | `shot-list-builder` | agent | `visuals/workflow.md`, `visuals/character.md` |
| 5. Visuals | `visual-generator` | agent | `visuals/workflow.md` |
| 6. Voiceover (ElevenLabs) | manual — no specialist | — | `voice.md` for settings/prompt |
| 7. Assembly (CapCut) | manual — no specialist | — | `structure.md`'s visual-style notes |

All brain-file paths above are relative to `assets/brain/` **in this same
folder** — no more cross-repo `../` paths anywhere in the specialist files.

**Skills** (`topic-scout`, `title-writer`, `script-writer`) run in one
continuous conversation — stay talking to the same session as it works
through each stage. **Agents** (`shot-list-builder`, `visual-generator`) run
isolated — dispatched separately for bulky/mechanical/long-running work,
reporting back a short result instead of filling the conversation.

## Folder structure

- `videos/NNN-<slug>/` — one folder per video: `notes.md` (sourcing),
  `title.md`, `script.md` (locked narration), `shot_list.md` (machine-
  parseable scene breakdown), `generate/generate_image.md` +
  `generate/generate_voice.md` (build artifacts, regenerated whenever
  script/shot-list changes), `audio/` (ElevenLabs output), `generate/generated/`
  (raw AI image/clip output), `testing/` (style-suffix iteration rounds),
  `output/` (final render + thumbnail), `description.md` + `thumbnail_prompt.md`
  (upload-ready metadata).
- `assets/brain/` — frozen format/tone/narration/visual reference (see
  above).
- `assets/references/` — competitive research.
- (No `assets/character/` folder currently — it was an empty placeholder
  in the old project and got removed 2026-08-12. `assets/brain/visuals/workflow.md`'s
  "Optional: reference-image" section describes an optional built-once
  character reference image; if that path is ever used, create
  `assets/character/host_reference.png` then.)
- `pipeline/` — `generate_visuals.py` (per-video shot generation via Gemini
  API), `generate_character_reference.py` (one-time character reference
  generation), `requirements.txt`. **`pipeline/.venv/` is not committed and
  not migrated from the old folder** — recreate it fresh:
  `python3.11 -m venv pipeline/.venv && source pipeline/.venv/bin/activate
  && pip install -r pipeline/requirements.txt`. Needs `GEMINI_API_KEY` in
  `.env` (gitignored; copied over from the old folder, still valid).
- `.claude/skills/`, `.claude/agents/` — the specialist files themselves.

## Video tracker

| # | Slug | Status | Notes |
|---|------|--------|-------|
| 001 | toba-supervolcano | **Effectively upload-ready** | "How Did Ancient Humans Survive Earth's Worst Volcano?" — myth-busting angle. `script.md` locked (2,451 words, ~11.9-12 min). `shot_list.md`: 98 shots, verified word-for-word against the script. Style suffixes tuned across 8 test rounds (`testing/version_1`-`8`, see `testing/log.md`) — final locked wording in `assets/brain/visuals/character.md`. All 98 shots generated (`generate/generated/`), ElevenLabs VO generated (`audio/`), and a **finished render already exists**: `output/001-toba-supervolcano_v2.mp4` + `output/thumbnail.jpg`. `description.md` has a locked title, full sourced description, chapter timestamps, and tags — upload-ready. (This row was stale as of the migration — it previously said "next: run the batch, generate VO, assemble," despite all of that already being done. Fixed 2026-08-12.) `videos/001-toba-supervolcano.zip` also exists alongside the folder — looks like a possibly-stale backup archive, worth checking before relying on it. |

## Known gaps

- No `002-<slug>` video started yet.
- `assets/character/` has no reference image built yet (optional, per
  `assets/brain/visuals/workflow.md`).
- The `videos/001-toba-supervolcano.zip` archive's relationship to the real
  `videos/001-toba-supervolcano/` folder hasn't been confirmed (stale
  duplicate vs. intentional backup) — flagged during the 2026-08-12
  migration, not yet resolved.

## Working notes

- This file does not auto-update — update it directly as pipeline decisions
  get made or videos progress.
- Next concrete step: pick a video 002 topic (`topic-scout`), avoiding the
  "rain" angle — already crowded, see `assets/references/channel_reports/2026-08-04_niche_landscape.md`.

---

_Migrated from the old two-folder split 2026-08-12. Last updated: 2026-08-12._
