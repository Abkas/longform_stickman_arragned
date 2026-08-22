# Assembly — turning shots + audio into a rendered video

Built 2026-08-13, against video 002, after CapCut hand-assembly was
replaced with a script for this session's work. CapCut remains a valid
manual alternative if you'd rather hand-edit — see `system/04_shots/workflow.md`'s
"Assembly-stage pacing" section for the Ken Burns/parallax reasoning this
script implements automatically.

## What `assemble.py` does

```
python system/07_assembly/assemble.py videos/NNN-slug \
    [--images-dir PATH] [--audio PATH] \
    [--override FROM_SHOT:PATH ...]
```

1. Parses `shot_list.md` for each shot's documented `- Duration:`.
2. Finds the real narration audio (auto-detected under `audio/` or
   `generate/generated/voice/`, or pass `--audio` explicitly) and measures
   its real length via `ffprobe`.
3. Scales every shot's documented duration by the same factor so they sum
   to exactly the real audio length (see "Known limitation" below — this is
   an approximation, not a real sync).
4. Renders each shot as its own short clip: a slow Ken Burns zoom
   (alternating zoom-in/zoom-out shot-to-shot) plus a cycling pan direction,
   never a hard static hold — matches `workflow.md`'s locked assembly
   guidance.
5. Concatenates all clips, muxes in the narration audio, writes
   `output/<slug>_v1.mp4`.

`--override FROM_SHOT:PATH` lets one video pull images from more than one
source folder for different shot ranges (e.g. video 002 needed shots 1-87
from one batch and 88-111 from a later re-render) without hardcoding any
video-specific folder name into the shared script:
```
python system/07_assembly/assemble.py videos/002-built-to-starve \
    --images-dir videos/002-built-to-starve/generate/image_v2/vdieo__0022222_v1 \
    --override 88:videos/002-built-to-starve/generate/image_v2/asdf
```

## Known limitation: duration sync is an approximation, not a real one

There's no per-shot or per-word timestamp data for the narration — just one
combined audio file. Scaling `shot_list.md`'s documented durations
proportionally to match the real audio length (step 3 above) preserves each
shot's *relative* pacing but does not guarantee any given shot's on-screen
time actually lines up with when that line is spoken. Video 002 surfaced
why this matters: its shot list assumed 207 WPM: the real ElevenLabs output
measured 166 WPM, a 24.6% overrun, which is also most of why that video felt
slow/draggy before this was diagnosed.

**The real fix, not yet built**: ElevenLabs' API can return word-level
timestamps alongside the audio (see the sister project `movie_auto_narration_fb`'s
`05_voice`/`narration_timestamps.json` for a working example of this exact
pattern — word + beat-level timestamps produced by the voice stage,
consumed by editing to retime shots to real narration timing instead of an
assumed pace). This project's voice stage is still fully manual (copy
narration text into ElevenLabs' web app by hand), which is exactly why no
timestamp data exists to use. Automating `06_voice` via the API (instead of
the web app) would produce that data essentially for free and let
`assemble.py` retime shots against real speech boundaries instead of a
scaled guess — worth doing before the next video if pacing accuracy matters
more than staying on the free/manual ElevenLabs path.

## Known limitation: motion ratio

Only shots explicitly marked `- Type: video` in `shot_list.md` get real
motion (a short generated clip instead of a still). Everything else is one
image with a pan/zoom applied at this stage — better than a hard static
hold, but still not real movement. Video 002 shipped with only 5 of 111
shots (4.5%) marked `Type: video`, which read as boring/slideshow-like
despite the Ken Burns treatment. If a future video feels the same way,
raise the `Type: video` bar in `system/04_shots/workflow.md`'s pacing rules
rather than trying to fix it at the assembly stage — Ken Burns can't
manufacture motion that was never generated.

## Output

`videos/NNN-slug/output/<slug>_v1.mp4` — 1920x1080, H.264/AAC. Intermediate
per-shot clips live in `videos/NNN-slug/generate/render_clips/` (safe to
delete and re-render; the script skips any shot whose clip already exists,
so re-running after fixing a bad source image only re-renders that one
shot's clip, not the whole video).
