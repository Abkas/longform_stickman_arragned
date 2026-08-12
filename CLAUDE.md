# CLAUDE.md — longform_stickman_arragned (orchestrator)

This folder is the **orchestrator workspace** for the `long-form-stickman-yt`
production pipeline. It holds nothing production-related itself — no videos,
no brain files, no pipeline code. Its only job is to be where you run Claude
Code from so it can dispatch pipeline stages to specialist skills/agents.

**The real project lives in the sibling folder:** `../long-form-stickman-yt/`.
Every specialist here reads and writes into it via `../long-form-stickman-yt/...`
relative paths — which only resolve correctly if Claude Code's working
directory is *this* folder. Always launch sessions for this pipeline from
here, not from inside the sibling repo.

This file is orchestration/meta only. The sibling project's own `CLAUDE.md`
(`../long-form-stickman-yt/CLAUDE.md`) remains the real production-status
source of truth — video tracker, current pipeline state, working
conventions. Don't duplicate that table here; read it there.

## Project & Persona (frozen, one-time — not a pipeline stage)

Before any per-video work, the channel's identity was locked once and never
re-decided per video:

- **What the project is:** a video-sharing channel producing long-form
  (~10-15 min) animated "ink"/stickman-style explainer videos — script →
  voiceover → animation → final render, monetized via ad-network/YPP
  revenue, replicating the real `@Inkexplainer96` channel's format.
- **Who the host character is** — locked across two dimensions, mirrored
  into this folder at `persona/tone.md` and `persona/character_design.md`
  so you can work from here without opening the sibling repo:
  - **Voice/tone** (`persona/tone.md`): a three-way blend — Fireship's
    fast/sarcastic/self-aware energy as the default texture, OverSimplified's
    accuracy-first backbone underneath the jokes, Sam O'Nella's flat-deadpan
    delivery reserved specifically for genuinely dark or absurd facts.
  - **Visual design** (`persona/character_design.md`): a simple stick
    figure, natural messy brown hair (specific locked wording after 3 real
    testing rounds — see the file for the full history of what went wrong
    and why), flat pale skin, bold black outlines, no photorealism anywhere.
- These two files are **mirrors** of the sibling repo's
  `assets/brain/tone/persona.md` and `assets/brain/visuals/character_design.md`
  — frozen/locked content, not living docs. If either original is ever
  revised in the sibling repo, resync the copy here by hand.
- `script-writer`, `title-writer`, and `shot-list-builder` all read these
  local mirrors directly rather than reaching into the sibling repo for them.

## Pipeline stages and who handles them

| Stage | Handled by | Type | Reads |
|---|---|---|---|
| 1. Topic | `topic-scout` | skill | `format/structure.md`, `references/channel_reports/*` |
| 2. Title | `title-writer` | skill | `title/strategy.md`, `format/structure.md`, `tone/persona.md` |
| 3. Script | `script-writer` | skill | `format/structure.md`, `tone/persona.md`, `narration/voice.md` |
| 4. Shot list | `shot-list-builder` | agent | `visuals/flow_workflow.md`, `visuals/character_design.md` |
| 5. Visuals | `visual-generator` | agent | `visuals/flow_workflow.md` |
| 6. Voiceover (ElevenLabs) | manual — no specialist | — | `narration/voice.md` for settings/prompt |
| 7. Assembly (CapCut) | manual — no specialist | — | `format/structure.md`'s visual-style notes |

All brain-file paths above are relative to `../long-form-stickman-yt/assets/brain/`.

**Skills** (`topic-scout`, `title-writer`, `script-writer`) run in this same
conversation — you stay talking to one continuous session as it works
through each stage, so you can correct/redirect it conversationally at any
point. **Agents** (`shot-list-builder`, `visual-generator`) run isolated —
dispatched separately, they do bulky/mechanical/long-running work off to the
side and report back a short result rather than filling this conversation
with their intermediate output.

## Trust boundaries — what specialists will and won't touch

- **Frozen reference files** (`assets/brain/format/structure.md`,
  `tone/persona.md`, `visuals/character_design.md`, etc.) — read-only to
  every specialist here. None of them edit these; they're the channel's
  locked rules, changed deliberately by a human, not by pipeline automation.
- **Living tracking docs** (`../long-form-stickman-yt/CLAUDE.md`'s video
  tracker table, `assets/brain/title/strategy.md`'s track record table) —
  specialists report locked decisions back to you in conversation, but
  **do not** write to these docs themselves. You update them. (This was a
  deliberate choice — keeps the channel's status docs under your direct
  control rather than auto-edited by an agent.)
- **`videos/NNN-slug/` content** (`notes.md`, `script.md`, `shot_list.md`,
  `generate/*.md`) — this is where specialists actively read and write, per
  the stage table above.

## Working a video end to end

1. Start a session here, ask for a new topic — this invokes `topic-scout`.
2. Once a topic locks, `title-writer` drafts titles.
3. Once topic + title are settled, `script-writer` drafts `script.md`,
   iterating with you until locked.
4. Dispatch `shot-list-builder` (an isolated agent call) once `script.md`
   is locked — it builds `shot_list.md` + the `generate/` export files.
5. Dispatch `visual-generator` once `shot_list.md` is locked — it either
   runs the paid Gemini pipeline or tells you the manual-Flow export is
   ready.
6. Voiceover (ElevenLabs) and assembly (CapCut) stay fully manual — no
   specialist here automates either; see the sibling project's `CLAUDE.md`
   and `assets/brain/narration/voice.md` for the actual settings/technique.

---

_This file does not auto-update — update it directly if the specialist
roster or pipeline mapping changes. Last updated: 2026-08-12._
