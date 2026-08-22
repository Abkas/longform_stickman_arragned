# Pipeline

This is the authoritative description of the workflow's order, why it runs
that way, and what's actually proven vs. still manual/broken. **Read this
before working on any stage** — `CLAUDE.md` points here first for exactly
that reason. Each stage's own `.md` file (next to its code/config, in
`system/<NN_stage>/`) has that stage's implementation detail; this file has
the shape and the reasoning for the shape, modeled on the same split used
in the `movie_auto_narration_fb` sister project.

## The order, and why it's narration-first from the start

```
1. system/01_topic/        pick + vet a topic/angle (skill: topic-scout)
                            reads: shared/references/channel_reports,
                            03_script/structure.md's format-fit checklist
                            no dedicated brain file of its own -- see
                            01_topic/topic.md for why

2. system/02_title/        title.md's data-derived formula -> 2-3 candidates
                            (skill: title-writer)

3. system/03_script/       structure.md + persona.md -> locked script.md
                            (skill: script-writer)
                            this is the story-telling decision point --
                            everything downstream serves this script,
                            nothing upstream of it exists yet

4. system/04_shots/        locked script.md -> shot_list.md, one shot per
                            sentence, classified character/diagram/
                            environment, self-contained prompts
                            (agent: shot-list-builder)

5. system/05_visuals/      shot_list.md's prompts -> generated stills/clips
                            (agent: visual-generator; script:
                            generate_visuals.py, paid Gemini API path, OR
                            manual Flow/browser-batch-extension path)

6. system/06_voice/        locked script.md -> narration audio
                            (manual -- ElevenLabs, no specialist yet)
                            depends only on script.md being locked, same as
                            the sister project's voice stage -- can in
                            principle run any time after stage 3, in
                            parallel with stages 4-5, though the usual run
                            order lists it after visuals

7. system/07_assembly/     shot_list.md + generated stills + narration audio
                            -> a rendered <slug>_v1.mp4 (assemble.py, Ken
                            Burns pan/zoom per still) -- needs stages 4-6 all
                            finished; CapCut is the manual fallback if you'd
                            rather hand-edit than run the script

8. system/08_export/       final render -> upload-ready metadata
                            (description.md, thumbnail_prompt.md, chapter
                            timestamps, tags) -- manual, no specialist yet
```

Unlike the sister project, this pipeline has always been narration-first —
script-writer already ran before any visual existed, from the very first
video. The lesson that project learned the hard way (write the story before
picking footage, but ground it in something real) doesn't need re-learning
here in the same form, because there's no real footage to match against —
every visual is generated fresh from the locked script's own shot list, so
"grounding" isn't a separate concern the way it is when cutting real film.

## Stage dependencies

`01_topic` → `02_title` → `03_script` is a straight line — each stage needs
the previous one locked. `04_shots` needs `03_script`'s `script.md` locked.
`05_visuals` needs `04_shots`'s `shot_list.md` locked. `06_voice` needs only
`03_script`'s locked `script.md` — it does **not** depend on `04_shots` or
`05_visuals` at all, and can run in parallel with them. `07_assembly` needs
`04_shots` (for durations/shot classification), `05_visuals` (for the
actual images), and `06_voice` (for the actual audio) all finished. `08_export`
needs `07_assembly`'s final render.

## What's real vs. still manual/rough

| Stage | Status |
|---|---|
| `01_topic` | skill exists, runs conversationally, no dedicated brain file (see its own doc for why) |
| `02_title` | skill exists, `title.md`'s formula is data-derived from a real competitor catalog |
| `03_script` | skill exists, `structure.md`/`persona.md` locked and used for both videos so far |
| `04_shots` | agent exists; **known bug, found + fixed 2026-08-13**: shot durations were computed from an assumed 207 WPM narration pace — the real ElevenLabs output for video 002 measured 166 WPM, a 24.6% overrun. Durations should be computed against the *real* generated audio length, not an assumed WPM — not yet automated, currently a manual proportional-scale workaround in `assemble.py` |
| `05_visuals` | both paths exist (paid API script, manual Flow/batch-extension). **Known bug, found + fixed 2026-08-13**: `generate_visuals.py` wrote to the wrong output folder (`<video>/visuals/` instead of the real convention, `<video>/generate/generated/images/`) — never caught because video 001 was generated manually, not through this script. **Known unresolved issue**: browser batch extensions (FlowBatch) can lose sync with their own prompt queue on slow generations, producing duplicate images and silently dropping others — video 002's first batch came back 47% wrong (52/111 shots) from this. See `system/04_shots/workflow.md`'s "Post-batch verification" section for the mitigation (hash-check for duplicates, smaller batch chunks, always audit before trusting a finished batch). **Known unresolved issue**: character art style has drifted off the locked stick-figure design on video 002's regenerated batch even after tightening the prompt wording — text-only prompting has a real consistency ceiling (see `system/04_shots/character.md`'s "Video 002 drift" section); the documented fallback (attach `system/05_visuals/character_reference/host_reference.png` as a real reference image) hasn't been successfully run yet — blocked on a working `GEMINI_API_KEY` as of this writing |
| `06_voice` | fully manual — no specialist, no script; `voice.md` covers settings/technique only |
| `07_assembly` | `assemble.py` built and tested 2026-08-13 (Ken Burns pan/zoom per still, alternating zoom/pan direction) — see `system/07_assembly/assembly.md` for its real limitations, especially the duration-sync approximation above |
| `08_export` | manual, conventions documented in `system/08_export/export.md`, proven once (video 001) |

## Load-bearing formats (shared across multiple stages — change with care)

- **`script.md`** — the locked narration, written by `03_script`. `04_shots`
  parses its sentences programmatically to build `shot_list.md`; changing
  `script.md` after `shot_list.md` exists means re-running `04_shots`.
- **`shot_list.md`** (`## Shot NNN` / `- Narration:` / `- Duration:` /
  `- Type:` / `- Visual:` / `- Prompt:`) — built by `04_shots`, parsed
  literally by `05_visuals`'s `generate_visuals.py` and `07_assembly`'s
  `assemble.py`. Keep field labels exact — both scripts regex-match them.
- **`generate/generate_image.md` / `generate/generate_voice.md`** — plain
  export files mechanically extracted from `shot_list.md`/`script.md` by
  `04_shots`, meant for pasting into Flow/ElevenLabs by hand. Build
  artifacts, not hand-maintained — regenerate whenever the source files
  change.
- **`generate/generated/images/`** — the real convention for where
  generated stills live, named `{shot_num}_{slug-of-that-shot's-prompt}.ext`
  (not zero-padded). `07_assembly`'s `assemble.py` looks here by default.
  If a video ends up with more than one source folder (e.g. an early batch
  plus a later re-render for specific shots), `assemble.py`'s `--override
  FROM_SHOT:PATH` flag handles that without hardcoding any video-specific
  folder name into the shared script.
- **The narration audio file** — currently just a single combined file
  (`audio/` or `generate/generated/voice/`), no per-shot or per-word
  timestamps. This is the root cause of the duration-sync approximation in
  `07_assembly` — see that stage's own doc for what would actually fix it.

## Conventions that apply across every stage

See `CLAUDE.md` for cross-cutting conventions (frozen reference docs, how
skills vs. agents run, folder structure) — kept there rather than
duplicated here, since that file is about *how to work in this repo*, not
*what the pipeline does*.
