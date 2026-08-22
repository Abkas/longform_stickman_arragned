#!/usr/bin/env python3
"""
Stage 07 — assembly. Turns a video's locked shot_list.md + generated stills
+ narration audio into a single rendered <slug>_v1.mp4.

Usage:
    python system/07_assembly/assemble.py videos/NNN-slug \
        [--images-dir PATH] [--audio PATH] \
        [--override FROM_SHOT:PATH ...]

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

No per-shot audio timestamps are assumed to exist. Each shot's documented
`- Duration:` in shot_list.md is scaled uniformly so the shots sum to the
real audio length -- see assembly.md's "Known limitation" section for why
this is an approximation, not a word-perfect sync, and what would fix that
properly (real ElevenLabs word timestamps, not implemented yet).

Every still gets a slow Ken Burns pan/zoom (alternating zoom-in/zoom-out,
cycling pan direction) per system/04_shots/workflow.md's locked
assembly-stage guidance, instead of a hard static hold.
"""
import argparse
import re
import subprocess
from pathlib import Path

W, H, FPS = 1920, 1080, 30
ZMAX = 1.12  # 12% max zoom, standard Ken Burns range
PAN_FRACTION = 0.035  # modest pan, stays inside the zoom margin at ZMAX


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
        shots.append({"num": int(h.group(1)), "doc_duration": float(dm.group(1))})
    shots.sort(key=lambda s: s["num"])
    nums = [s["num"] for s in shots]
    assert nums == list(range(1, len(shots) + 1)), "shot numbers not contiguous starting at 1"
    return shots


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


def find_audio(video_dir: Path, explicit: Path | None) -> Path:
    if explicit:
        return explicit
    candidates = []
    for sub in ("audio", "generate/generated/voice", "generate/voice"):
        d = video_dir / sub
        if d.is_dir():
            candidates += [p for p in d.iterdir() if p.is_file()]
    if len(candidates) == 1:
        return candidates[0]
    raise SystemExit(
        f"Could not auto-detect a single audio file under {video_dir} "
        f"(found {len(candidates)}: {candidates}) -- pass --audio explicitly."
    )


def build_zoompan_filter(shot_index: int, duration: float) -> str:
    d_frames = max(1, round(duration * FPS))
    zoom_in = (shot_index % 2 == 0)
    pan_mode = shot_index % 4  # 0/3=center, 1=pan right, 2=pan left

    inc = (ZMAX - 1) / d_frames
    z_expr = (f"min(zoom+{inc:.8f},{ZMAX})" if zoom_in
              else f"if(eq(on,0),{ZMAX},max(zoom-{inc:.8f},1.0))")

    base_x = "iw/2-(iw/zoom/2)"
    base_y = "ih/2-(ih/zoom/2)"
    if pan_mode == 1:
        x_expr = f"({base_x})+(iw*{PAN_FRACTION})*(on/{d_frames})"
    elif pan_mode == 2:
        x_expr = f"({base_x})-(iw*{PAN_FRACTION})*(on/{d_frames})"
    else:
        x_expr = base_x

    return (
        f"scale=3840:-2,"
        f"zoompan=z='{z_expr}':x='{x_expr}':y='{base_y}':d={d_frames}:s={W}x{H}:fps={FPS},"
        f"format=yuv420p"
    )


def render_clip(shot_index: int, image_path: Path, duration: float, out_path: Path):
    if out_path.exists():
        return
    vf = build_zoompan_filter(shot_index, duration)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_dir", type=Path)
    ap.add_argument("--images-dir", type=Path, default=None)
    ap.add_argument("--audio", type=Path, default=None)
    ap.add_argument("--override", action="append", default=[],
                     help="FROM_SHOT:PATH -- use PATH as the image source from shot FROM_SHOT onward")
    args = ap.parse_args()

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
    final_out = output_dir / f"{slug}_v1.mp4"

    shots = parse_shots(shot_list_path)
    audio_duration = ffprobe_duration(audio_path)
    doc_total = sum(s["doc_duration"] for s in shots)
    scale = audio_duration / doc_total
    print(f"Audio: {audio_path} ({audio_duration:.2f}s) | documented shot-duration sum: "
          f"{doc_total:.2f}s | scale factor: {scale:.4f}")

    for s in shots:
        s["real_duration"] = s["doc_duration"] * scale
        s["image"] = find_image(s["num"], images_dir, overrides)

    print("\nRendering per-shot Ken Burns clips...")
    for i, s in enumerate(shots):
        out_path = clips_dir / f"{s['num']:03d}.mp4"
        render_clip(i, s["image"], s["real_duration"], out_path)
        s["clip"] = out_path
        print(f"  shot {s['num']:3d}  src={s['image'].parent.name:22s}  dur={s['real_duration']:5.2f}s")

    print("\nConcatenating...")
    with open(concat_list, "w") as f:
        for s in shots:
            f.write(f"file '{s['clip'].resolve()}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
                     "-c", "copy", str(silent_concat)], check=True)

    print("Muxing audio...")
    subprocess.run(["ffmpeg", "-y", "-i", str(silent_concat), "-i", str(audio_path),
                     "-map", "0:v:0", "-map", "1:a:0",
                     "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                     "-shortest", str(final_out)], check=True)
    silent_concat.unlink(missing_ok=True)

    final_dur = ffprobe_duration(final_out)
    print(f"\nDone: {final_out}")
    print(f"Final duration: {final_dur:.2f}s ({final_dur/60:.2f} min) vs audio {audio_duration:.2f}s")


if __name__ == "__main__":
    main()
