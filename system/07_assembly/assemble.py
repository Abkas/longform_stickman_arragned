#!/usr/bin/env python3
"""
Stage 07 — assembly. Turns a video's locked shot_list.md + generated stills
+ narration audio into a single rendered <slug>_v1.mp4.

Usage:
    python system/07_assembly/assemble.py videos/NNN-slug \
        [--images-dir PATH] [--audio PATH] \
        [--override FROM_SHOT:PATH ...] \
        [--sfx | --no-sfx] [--music | --no-music]

Defaults (matching the documented per-video folder convention, see
system/07_assembly/assembly.md):
    --images-dir  videos/NNN-slug/generate/generated/images/
    --audio       auto-detected: the one audio file under
                  videos/NNN-slug/audio/ or
                  videos/NNN-slug/generate/generated/voice/

--override lets a single video use more than one image source folder for
different shot ranges (e.g. an early batch plus a later re-render) without
hardcoding any video-specific folder name into this shared script:
    --override 88:videos/NNN-slug/generate/some_other_folder

Real per-shot timing (2026-09-12): if a `narration_timestamps.json` sits
next to the audio file (system/06_voice/voice_generate.py's output --
word-level timestamps from ElevenLabs' own alignment), each shot's actual
start/end time is computed by matching its `- Narration:` field against
that real word timeline, instead of the old fallback below. This is what
assembly.md's "Known limitation" section asked for -- word-perfect sync,
not a proportional guess. Falls back to the old approximation (each
shot's documented `- Duration:` scaled uniformly so the shots sum to the
real audio length) only when no timestamps file exists.

Every still gets a slow Ken Burns pan/zoom (alternating zoom-in/zoom-out,
cycling pan direction, with per-shot randomized intensity so it doesn't
read as one fixed mechanical formula -- see assembly.md's "Research: making
the edit feel human-made" section) instead of a hard static hold.

--sfx (default on) synthesizes a short, soft tick sound at every shot
transition -- no external sound library needed, generated in pure Python.
--music (default on) synthesizes a very quiet two-tone ambient pad under
the whole narration, heavily ducked -- a placeholder bed, not composed
music, so cuts have *something* to sit against instead of dead silence.
Both are cheap experiments per assembly.md's research notes, not a
finished sound-design pipeline -- turn either off if it doesn't help.
"""
import argparse
import array
import json
import math
import random
import re
import subprocess
import wave
from pathlib import Path

TAG_WORD_RE = re.compile(r"^\[[a-z ]+\]$")  # a whole "word" token that IS just a tag, e.g. in the
                                             # real word-alignment list, where each tag got its own entry
TAG_ANYWHERE_RE = re.compile(r"\[[a-z ]+\]")  # a tag occurring anywhere inside a longer string, e.g.
                                               # shot_list.md's `"[flatly] A hungry ape..."` narration text

W, H, FPS = 1920, 1080, 30
ZMAX_BASE = 1.12  # ~12% max zoom, standard Ken Burns range, before per-shot jitter
PAN_FRACTION_BASE = 0.035
SAMPLE_RATE = 44100


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ])
    return float(out.strip())


def parse_shots(shot_list_path: Path):
    text = shot_list_path.read_text(encoding="utf-8")
    headers = list(re.finditer(r"^## Shot (\d+)$", text, re.MULTILINE))
    shots = []
    for i, h in enumerate(headers):
        start, end = h.end(), (headers[i + 1].start() if i + 1 < len(headers) else len(text))
        block = text[start:end]
        dm = re.search(r"^- Duration:\s*~?(\d+(?:\.\d+)?)s", block, re.MULTILINE)
        if not dm:
            raise SystemExit(f"Shot {h.group(1)}: no Duration field")
        nm = re.search(r'^- Narration:\s*"(.*)"\s*$', block, re.MULTILINE)
        shots.append({
            "num": int(h.group(1)),
            "doc_duration": float(dm.group(1)),
            "narration": nm.group(1) if nm else None,
        })
    shots.sort(key=lambda s: s["num"])
    nums = [s["num"] for s in shots]
    assert nums == list(range(1, len(shots) + 1)), "shot numbers not contiguous starting at 1"
    return shots


def find_timestamps(audio_path: Path) -> Path | None:
    p = audio_path.parent / "narration_timestamps.json"
    return p if p.is_file() else None


def build_real_shot_timing(shots: list[dict], timestamps_path: Path, audio_duration: float) -> bool:
    """Assigns each shot a real start/end time by matching its quoted
    `- Narration:` field against ElevenLabs' actual word-level alignment
    (system/06_voice/voice_generate.py's output), instead of guessing from
    a documented word-count estimate. Returns True and mutates `shots` in
    place (adds "real_duration"/"cut_time" like the old scaling path did)
    on success; returns False (leaving `shots` untouched) if anything about
    the two sources doesn't line up -- caller falls back to the old
    proportional-scaling approach rather than silently mis-syncing.

    How the match works: shot_list.md's own header claims every shot's
    Narration field concatenates, in order, to reconstruct the exact text
    that was sent to ElevenLabs (word-for-word, no gaps/overlaps) -- so a
    shot's Nth narration word IS the same word as the real timeline's
    running Nth word, as long as both sides are tokenized the same way
    (split on whitespace, tags stripped) and counted up in lockstep."""
    data = json.loads(timestamps_path.read_text())
    real_words = [w for w in data["words"] if not TAG_WORD_RE.match(w["text"])]

    if any(s["narration"] is None for s in shots):
        print("  (some shots have no parseable Narration field -- falling back to scaling)")
        return False

    shot_word_lists = [[w for w in re.split(r"\s+", TAG_ANYWHERE_RE.sub("", s["narration"]).strip()) if w]
                        for s in shots]
    total_shot_words = sum(len(ws) for ws in shot_word_lists)
    if total_shot_words != len(real_words):
        print(f"  Word count mismatch: shot_list.md's Narration fields total {total_shot_words} "
              f"words, but the real timeline has {len(real_words)} -- falling back to scaling. "
              "(A shot_list.md hand-edit after voice generation, or a script/generate_voice.md "
              "drift, would cause this.)")
        return False

    idx = 0
    for s, words in zip(shots, shot_word_lists):
        s["_word_start_idx"] = idx
        idx += len(words)

    for i, s in enumerate(shots):
        start_idx = s["_word_start_idx"]
        s["cut_time"] = real_words[start_idx]["start"]
        next_start = (real_words[shots[i + 1]["_word_start_idx"]]["start"]
                      if i + 1 < len(shots) else audio_duration)
        s["real_duration"] = max(0.1, next_start - s["cut_time"])
        del s["_word_start_idx"]
    return True


def find_image(shot_num: int, images_dir: Path, overrides: list[tuple[int, Path]]) -> Path:
    src_dir = images_dir
    for from_shot, path in overrides:  # overrides sorted ascending; last match wins
        if shot_num >= from_shot:
            src_dir = path
    matches = list(src_dir.glob(f"{shot_num}_*")) + list(src_dir.glob(f"{shot_num}.*"))
    if not matches:
        raise SystemExit(f"Shot {shot_num}: no image found in {src_dir}")
    matches.sort(key=lambda p: len(p.name))  # prefer the plain "N.ext" over a slug variant
    return matches[0]


AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}


def find_audio(video_dir: Path, explicit: Path | None) -> Path:
    if explicit:
        return explicit
    candidates = []
    for sub in ("audio", "generate/generated/voice", "generate/voice"):
        d = video_dir / sub
        if d.is_dir():
            candidates += [p for p in d.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS]
    if len(candidates) == 1:
        return candidates[0]
    raise SystemExit(
        f"Could not auto-detect a single audio file under {video_dir} "
        f"(found {len(candidates)}: {candidates}) -- pass --audio explicitly."
    )


def build_zoompan_filter(shot_index: int, shot_num: int, duration: float) -> str:
    # Per-shot deterministic jitter (seeded on shot number, not time) so
    # re-running assemble.py on an unchanged shot list reproduces the same
    # clip byte-for-byte, matching the existing "skip if clip exists" logic.
    rng = random.Random(shot_num)
    zmax = ZMAX_BASE + rng.uniform(-0.02, 0.03)
    pan_fraction = PAN_FRACTION_BASE + rng.uniform(-0.01, 0.015)

    # Very short shots (the itemized-list "flash" tier from shot.md's v2
    # density rules, ~1.5-2.5s) get a gentler zoom -- the same intensity
    # crammed into 2s instead of 8s would read as a jarring snap, not a pan.
    if duration < 3.0:
        intensity = max(0.4, duration / 3.0)
        zmax = 1.0 + (zmax - 1.0) * intensity
        pan_fraction *= intensity

    d_frames = max(1, round(duration * FPS))
    zoom_in = (shot_index % 2 == 0)
    pan_mode = shot_index % 4  # 0/3=center, 1=pan right, 2=pan left

    inc = (zmax - 1) / d_frames
    z_expr = (f"min(zoom+{inc:.8f},{zmax:.6f})" if zoom_in
              else f"if(eq(on,0),{zmax:.6f},max(zoom-{inc:.8f},1.0))")

    base_x = "iw/2-(iw/zoom/2)"
    base_y = "ih/2-(ih/zoom/2)"
    if pan_mode == 1:
        x_expr = f"({base_x})+(iw*{pan_fraction:.6f})*(on/{d_frames})"
    elif pan_mode == 2:
        x_expr = f"({base_x})-(iw*{pan_fraction:.6f})*(on/{d_frames})"
    else:
        x_expr = base_x

    return (
        f"scale=3840:-2,"
        f"zoompan=z='{z_expr}':x='{x_expr}':y='{base_y}':d={d_frames}:s={W}x{H}:fps={FPS},"
        f"format=yuv420p"
    )


def render_clip(shot_index: int, shot_num: int, image_path: Path, duration: float, out_path: Path):
    if out_path.exists():
        return
    vf = build_zoompan_filter(shot_index, shot_num, duration)
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(image_path),
        "-t", f"{duration:.3f}",
        "-vf", vf,
        "-r", str(FPS),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
        str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg failed on shot {shot_index}:\n{r.stderr[-3000:]}")


def synth_tick_samples() -> array.array:
    """A short (~70ms), soft descending tick -- pure Python, no assets, no
    new dependencies. Sine tone with a fast exponential decay envelope."""
    dur = 0.07
    freq0, freq1 = 1400.0, 700.0  # slight downward pitch sweep, softer than a flat beep
    n = int(SAMPLE_RATE * dur)
    samples = array.array("h", [0] * n)
    peak = 6000  # well under int16 max (32767) -- this gets volume-scaled again at mix time
    for i in range(n):
        t = i / SAMPLE_RATE
        frac = i / n
        freq = freq0 + (freq1 - freq0) * frac
        envelope = math.exp(-frac * 7.0)  # fast decay -- reads as a soft "tick", not a beep
        samples[i] = int(peak * envelope * math.sin(2 * math.pi * freq * t))
    return samples


def build_tick_track(cut_times: list[float], total_duration: float, out_path: Path):
    """Writes a mono WAV, silent except for a short tick at each cut time."""
    tick = synth_tick_samples()
    total_samples = int(total_duration * SAMPLE_RATE)
    track = array.array("h", [0] * total_samples)
    for t in cut_times:
        start = int(t * SAMPLE_RATE)
        end = min(start + len(tick), total_samples)
        for i in range(end - start):
            # add (not overwrite) in case cuts ever land closer together than
            # the tick's own length -- clamped to int16 range either way
            v = track[start + i] + tick[i]
            track[start + i] = max(-32768, min(32767, v))
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(track.tobytes())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video_dir", type=Path)
    ap.add_argument("--images-dir", type=Path, default=None)
    ap.add_argument("--audio", type=Path, default=None)
    ap.add_argument("--override", action="append", default=[],
                     help="FROM_SHOT:PATH -- use PATH as the image source from shot FROM_SHOT onward")
    ap.add_argument("--no-sfx", dest="sfx", action="store_false", default=True,
                     help="Disable the synthesized tick at each shot transition (default: on)")
    ap.add_argument("--vertical", action="store_true",
                     help="9:16 output (1080x1920) for Shorts, instead of the default 16:9 "
                     "landscape (1920x1080) long-form videos use. build_zoompan_filter()'s "
                     "pre-crop upscale (scale=3840:-2) works unchanged either way -- it always "
                     "scales to a fixed working width regardless of source image orientation, "
                     "so only the final W/H (the zoompan crop window) needs to change here.")
    ap.add_argument("--no-music", dest="music", action="store_false", default=True,
                     help="Disable the synthesized ambient pad under the narration (default: on)")
    args = ap.parse_args()

    if args.vertical:
        global W, H
        W, H = 1080, 1920

    video_dir = args.video_dir
    shot_list_path = video_dir / "shot_list.md"
    images_dir = args.images_dir or (video_dir / "generate" / "generated" / "images")
    audio_path = find_audio(video_dir, args.audio)

    overrides = []
    for o in args.override:
        from_shot_s, path_s = o.split(":", 1)
        overrides.append((int(from_shot_s), Path(path_s)))
    overrides.sort(key=lambda t: t[0])

    output_dir = video_dir / "output"
    clips_dir = video_dir / "generate" / "render_clips"
    output_dir.mkdir(parents=True, exist_ok=True)
    clips_dir.mkdir(parents=True, exist_ok=True)
    slug = video_dir.name
    silent_concat = output_dir / "_silent_concat.mp4"
    concat_list = clips_dir / "_concat_list.txt"
    tick_track_path = clips_dir / "_tick_track.wav"
    final_out = output_dir / f"{slug}_v1.mp4"

    shots = parse_shots(shot_list_path)
    audio_duration = ffprobe_duration(audio_path)
    print(f"Audio: {audio_path} ({audio_duration:.2f}s)")

    timestamps_path = find_timestamps(audio_path)
    used_real_timing = False
    if timestamps_path:
        print(f"Found {timestamps_path} -- attempting real word-level sync...")
        used_real_timing = build_real_shot_timing(shots, timestamps_path, audio_duration)
        if used_real_timing:
            print("  Real per-shot timing applied (word-perfect sync, not an approximation).")

    if not used_real_timing:
        doc_total = sum(s["doc_duration"] for s in shots)
        scale = audio_duration / doc_total
        print(f"Using proportional-scaling fallback | documented shot-duration sum: "
              f"{doc_total:.2f}s | scale factor: {scale:.4f}")
        cumulative = 0.0
        for s in shots:
            s["real_duration"] = s["doc_duration"] * scale
            s["cut_time"] = cumulative
            cumulative += s["real_duration"]

    for s in shots:
        s["image"] = find_image(s["num"], images_dir, overrides)

    print("\nRendering per-shot Ken Burns clips...")
    for i, s in enumerate(shots):
        out_path = clips_dir / f"{s['num']:03d}.mp4"
        render_clip(i, s["num"], s["image"], s["real_duration"], out_path)
        s["clip"] = out_path
        print(f"  shot {s['num']:3d}  src={s['image'].parent.name:22s}  dur={s['real_duration']:5.2f}s")

    print("\nConcatenating...")
    with open(concat_list, "w") as f:
        for s in shots:
            f.write(f"file '{s['clip'].resolve()}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
                     "-c", "copy", str(silent_concat)], check=True)

    audio_inputs = ["-i", str(audio_path)]
    filter_parts = ["[1:a]volume=1.0[narr]"]
    mix_labels = ["[narr]"]
    next_input_index = 2

    if args.sfx:
        print("Synthesizing transition ticks...")
        cut_times = [s["cut_time"] for s in shots[1:]]  # skip t=0, nothing to punctuate yet
        build_tick_track(cut_times, audio_duration, tick_track_path)
        audio_inputs += ["-i", str(tick_track_path)]
        filter_parts.append(f"[{next_input_index}:a]volume=0.35[ticks]")
        mix_labels.append("[ticks]")
        next_input_index += 1

    if args.music:
        print("Synthesizing ambient pad...")
        audio_inputs += ["-f", "lavfi", "-i", f"sine=frequency=110:duration={audio_duration:.3f}"]
        audio_inputs += ["-f", "lavfi", "-i", f"sine=frequency=110.6:duration={audio_duration:.3f}"]
        i1, i2 = next_input_index, next_input_index + 1
        filter_parts.append(
            f"[{i1}:a][{i2}:a]amix=inputs=2:duration=first:normalize=0,"
            f"lowpass=f=300,volume=0.045[pad]"
        )
        mix_labels.append("[pad]")
        next_input_index += 2

    if len(mix_labels) > 1:
        filter_parts.append(
            f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:"
            f"normalize=0,alimiter=limit=0.95[aout]"
        )
        final_map = "[aout]"
    else:
        final_map = "[narr]"

    print("Muxing audio...")
    cmd = ["ffmpeg", "-y", "-i", str(silent_concat), *audio_inputs,
           "-filter_complex", ";".join(filter_parts),
           "-map", "0:v:0", "-map", final_map,
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
           "-shortest", str(final_out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg audio mux failed:\n{r.stderr[-3000:]}")
    silent_concat.unlink(missing_ok=True)
    tick_track_path.unlink(missing_ok=True)

    final_dur = ffprobe_duration(final_out)
    print(f"\nDone: {final_out}")
    print(f"Final duration: {final_dur:.2f}s ({final_dur/60:.2f} min) vs audio {audio_duration:.2f}s")
    print(f"sfx={'on' if args.sfx else 'off'}  music={'on' if args.music else 'off'}")


if __name__ == "__main__":
    main()
