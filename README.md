# longform_stickman_arragned

Complete home for the `long-form-stickman-yt` channel — brain files
(format/tone/narration/visual rules), competitive research, video content,
the Gemini-based visual-generation pipeline, and Claude Code skills/agents
(`topic-scout`, `title-writer`, `script-writer`, `shot-list-builder`,
`visual-generator`) that turn the pipeline into an actual delegated
workflow instead of ad-hoc re-application each session.

Run Claude Code from this folder to work on a video — see `CLAUDE.md` for
the full pipeline map, current video status, and known gaps.

`pipeline/.venv/` isn't included — set it up once:
```
python3.11 -m venv pipeline/.venv
source pipeline/.venv/bin/activate
pip install -r pipeline/requirements.txt
```
Needs `GEMINI_API_KEY` in `.env` (already present, gitignored) for the
automated visual-generation path; the manual Flow/browser-extension path
works without it.
