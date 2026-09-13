#!/usr/bin/env python3
"""
Automated narration for this channel's videos, via ElevenLabs' timestamped
TTS endpoint. Added 2026-09-12 -- 06_voice was fully manual (ElevenLabs web
app) until now; see this repo's CLAUDE.md "Known gaps" section for why
(no automated per-shot/per-word timing existed for 07_assembly to sync
against). This script fixes both at once: automated generation AND real
word-level timestamps, modeled directly on the proven design already
running in the sister project (movie_auto_narration_fb's
system/05_voice/tts_generate.py) -- same REST-API-directly approach (no
`elevenlabs` SDK dependency), same with-timestamps endpoint, same
alignment-to-words logic, adapted here for paragraph-based narration
instead of that project's beat-based script format.

Input: videos/<slug>/generate/generate_voice.md -- the plain narration
text (inline [tag] delivery cues, blank-line-separated paragraphs) that
shot-list-builder already exports from the locked script.md. This script
doesn't touch script.md or shot_list.md at all, purely reads that one
export file.

Output (videos/<slug>/generate/generated/voice/):
  - narration.mp3 -- the full narration, one ElevenLabs call (not one
    call per paragraph) so pacing/emphasis flows naturally across
    paragraph boundaries instead of sounding stitched together.
  - narration_timestamps.json -- word-level timing from ElevenLabs'
    character-level alignment, PLUS a start/end time per paragraph
    (mapping words back to the paragraph they came from by character
    offset) -- this is the real per-shot/paragraph timing data
    07_assembly's duration-sync was missing until now.

Needs ELEVENLABS_API_KEY in the repo root's .env (see .env.example for
the exact permissions to grant the key). Voice choice + generation
settings default to what system/06_voice/voice.md already locked
(stability/similarity/style ranges, the Voice Design character
description) -- pass --voice-id directly if you already know it (fastest,
works even with a Voices:Read-less key), or --voice-name to have this
script look it up by name (needs Voices:Read permission on the key).

Usage:
    # look up the account's voices (needs Voices:Read) to find the one
    # used for video 001, so 003 stays consistent (voice.md's own rule):
    python system/06_voice/voice_generate.py list-voices

    # generate, once you have the voice_id:
    python system/06_voice/voice_generate.py generate videos/003-stoned-ape \\
        --voice-id <id>

    # preview what would be sent (paragraph count, char/word count, a
    # rough cost estimate) without spending any credits:
    python system/06_voice/voice_generate.py generate videos/003-stoned-ape \\
        --voice-id <id> --dry-run
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # system/06_voice/ -> system/ -> repo root
DOTENV_PATH = ROOT / ".env"
LEGACY_CONFIG_PATH = Path.home() / ".config" / "movie-narration-generator" / "elevenlabs.json"

API_BASE = "https://api.elevenlabs.io/v1"
RETRIES = 3
RETRY_DELAY_SECONDS = 3
PARA_SEPARATOR = "\n\n"  # matches generate_voice.md's own paragraph breaks -- a real pause, not a mid-sentence gap
MAX_CHARS_PER_CALL = 4500  # ElevenLabs hard-caps a single TTS request at 5000 chars ("use Studio for
                            # long form TTS") -- margin below that for the separator overhead between
                            # the last paragraph counted and the next one that gets pushed to a new batch

# Defaults per system/06_voice/voice.md's "Starting settings" -- midpoints
# of its documented ranges (Stability 0.35-0.45, Similarity 0.75-0.85,
# Style 0.15-0.25). eleven_v3 specifically because voice.md's [tag]-style
# delivery cues (inline in generate_voice.md) are a v3 feature -- an older
# model would just read the brackets aloud as literal text.
DEFAULT_MODEL_ID = "eleven_v3"
DEFAULT_STABILITY = 0.40
DEFAULT_SIMILARITY = 0.80
DEFAULT_STYLE = 0.20


def load_dotenv(path: Path = DOTENV_PATH) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
        if not m:
            continue
        key, value = m.groups()
        os.environ.setdefault(key, value)


def load_api_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        return key
    if LEGACY_CONFIG_PATH.exists():
        try:
            return json.loads(LEGACY_CONFIG_PATH.read_text())["api_key"]
        except Exception:
            pass
    sys.exit(
        "No ElevenLabs API key found. Set ELEVENLABS_API_KEY in the repo "
        f"root's .env (see .env.example), or create {LEGACY_CONFIG_PATH} "
        'with {"api_key": "<your key>"}.'
    )


def api_request(path: str, api_key: str, method: str = "GET", body: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "application/json"},
    )
    last_error = None
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            if e.code < 500:
                sys.exit(f"ElevenLabs returned {e.code} for {path}: {detail}")
            last_error = RuntimeError(f"ElevenLabs returned {e.code}: {detail}")
        except (urllib.error.URLError, TimeoutError) as e:
            last_error = e
        if attempt < RETRIES:
            print(f"  API call to {path} failed (attempt {attempt}/{RETRIES}), retrying...")
            time.sleep(RETRY_DELAY_SECONDS)
    raise last_error


def cmd_list_voices(args: argparse.Namespace) -> None:
    api_key = load_api_key()
    result = api_request("/voices", api_key)
    voices = result.get("voices", [])
    if not voices:
        print("No voices returned (empty account, or the key lacks Voices:Read).")
        return
    print(f"{len(voices)} voice(s) on this account:\n")
    for v in voices:
        print(f"  {v['voice_id']}  |  {v['name']}  |  {v.get('category', '?')}")
        desc = v.get("description")
        if desc:
            print(f"      {desc[:120]}")


def parse_paragraphs(generate_voice_path: Path) -> list[str]:
    text = generate_voice_path.read_text(encoding="utf-8").strip()
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paras


def build_narration_text(paragraphs: list[str]) -> tuple[str, list[tuple[int, int, int]]]:
    """Returns (joined_text, para_ranges) where para_ranges is
    [(para_index, char_start, char_end), ...] -- char offsets into
    joined_text, used later to map each aligned word back to its
    paragraph, same technique as the sister project's beat mapping."""
    joined_parts = []
    para_ranges = []
    offset = 0
    for i, para in enumerate(paragraphs):
        joined_parts.append(para)
        start = offset
        end = start + len(para)
        para_ranges.append((i, start, end))
        offset = end + len(PARA_SEPARATOR)
        joined_parts.append(PARA_SEPARATOR)
    joined_text = "".join(joined_parts).rstrip()
    return joined_text, para_ranges


def call_elevenlabs_tts(text: str, api_key: str, voice_id: str, model_id: str,
                         stability: float, similarity: float, style: float) -> dict:
    body = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity,
            "style": style,
            "use_speaker_boost": True,
        },
    }
    return api_request(f"/text-to-speech/{voice_id}/with-timestamps", api_key, method="POST", body=body)


def words_from_alignment(alignment: dict) -> list[dict]:
    characters = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]

    words = []
    cur_chars: list[str] = []
    cur_start_time = None
    cur_start_index = None
    for i, ch in enumerate(characters):
        if ch.isspace():
            if cur_chars:
                words.append({
                    "text": "".join(cur_chars),
                    "start": cur_start_time,
                    "end": ends[i - 1],
                    "char_start_index": cur_start_index,
                })
                cur_chars = []
                cur_start_time = None
        else:
            if not cur_chars:
                cur_start_time = starts[i]
                cur_start_index = i
            cur_chars.append(ch)
    if cur_chars:
        words.append({
            "text": "".join(cur_chars),
            "start": cur_start_time,
            "end": ends[-1],
            "char_start_index": cur_start_index,
        })
    return words


def build_paragraph_timing(words: list[dict], para_ranges: list[tuple[int, int, int]]) -> list[dict]:
    timing = []
    for idx, start_char, end_char in para_ranges:
        para_words = [w for w in words if start_char <= w["char_start_index"] < end_char]
        if not para_words:
            print(f"  Warning: paragraph {idx} has no words in the alignment.")
            continue
        timing.append({
            "paragraph": idx,
            "start": para_words[0]["start"],
            "end": para_words[-1]["end"],
            "text": " ".join(w["text"] for w in para_words),
        })
    return timing


def audio_duration(path: Path) -> float | None:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        )
        return float(result.stdout.strip())
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        return None


def batch_paragraphs(paragraphs: list[str], max_chars: int) -> list[list[int]]:
    """Groups paragraph indices into batches whose joined length (with
    PARA_SEPARATOR between them) stays under max_chars, never splitting a
    paragraph across two calls -- ElevenLabs' 5000-char cap forces multiple
    TTS calls for anything long-form ("use Studio for long form TTS", which
    this project deliberately doesn't depend on -- REST-only, no separate
    app dependency)."""
    batches: list[list[int]] = []
    current: list[int] = []
    current_len = 0
    for i, para in enumerate(paragraphs):
        added_len = len(para) + (len(PARA_SEPARATOR) if current else 0)
        if current and current_len + added_len > max_chars:
            batches.append(current)
            current = []
            current_len = 0
            added_len = len(para)
        current.append(i)
        current_len += added_len
    if current:
        batches.append(current)
    return batches


def concat_audio(parts: list[Path], dest: Path) -> None:
    filelist = dest.parent / "_concat_list.txt"
    filelist.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(filelist), "-c", "copy", str(dest)],
            capture_output=True, text=True, check=True,
        )
    except FileNotFoundError:
        sys.exit("ffmpeg not found -- needed to stitch the batched TTS calls into one narration.mp3.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"ffmpeg concat failed:\n{e.stderr}")
    finally:
        filelist.unlink(missing_ok=True)


def cmd_generate(args: argparse.Namespace) -> None:
    video_dir: Path = args.video_dir
    src = video_dir / "generate" / "generate_voice.md"
    if not src.exists():
        sys.exit(f"No such file: {src} -- run shot-list-builder first to export it from script.md.")

    out_dir = video_dir / "generate" / "generated" / "voice"
    audio_path = out_dir / "narration.mp3"
    timestamps_path = out_dir / "narration_timestamps.json"
    if audio_path.exists() and not args.force:
        sys.exit(f"{audio_path} already exists. Pass --force to re-generate (costs ElevenLabs credits again).")

    paragraphs = parse_paragraphs(src)
    full_text_for_count = PARA_SEPARATOR.join(paragraphs)
    word_count = len(re.findall(r"\S+", re.sub(r"\[[a-z ]+\]", "", full_text_for_count)))
    batches = batch_paragraphs(paragraphs, MAX_CHARS_PER_CALL)
    print(f"{len(paragraphs)} paragraph(s), {len(full_text_for_count)} characters, ~{word_count} words "
          f"(tags stripped) -- target pace ~205-210 WPM per voice.md => "
          f"~{word_count / 207 * 60:.0f}s expected. Splitting into {len(batches)} API call(s) "
          f"(ElevenLabs caps a single call at 5000 chars).")

    if args.dry_run:
        print("\n--dry-run: not calling the API. Batch plan:\n")
        for bi, idxs in enumerate(batches):
            chars = sum(len(paragraphs[i]) for i in idxs) + len(PARA_SEPARATOR) * (len(idxs) - 1)
            print(f"  batch {bi}: paragraphs {idxs[0]}-{idxs[-1]} ({len(idxs)} paras, {chars} chars)")
        return

    api_key = load_api_key()
    voice_id = args.voice_id
    if not voice_id:
        sys.exit("Pass --voice-id (run `list-voices` first if you need to find it).")

    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = out_dir / "_batch_tmp"
    tmp_dir.mkdir(exist_ok=True)

    all_words: list[dict] = []
    all_para_timing: list[dict] = []
    batch_audio_paths: list[Path] = []
    time_offset = 0.0

    try:
        for bi, idxs in enumerate(batches):
            batch_paras = [paragraphs[i] for i in idxs]
            joined_text, local_ranges = build_narration_text(batch_paras)
            print(f"\nBatch {bi + 1}/{len(batches)}: paragraphs {idxs[0]}-{idxs[-1]} "
                  f"({len(joined_text)} chars) -> calling ElevenLabs (model={args.model_id}, voice={voice_id})...")
            result = call_elevenlabs_tts(joined_text, api_key, voice_id, args.model_id,
                                          args.stability, args.similarity, args.style)

            batch_audio_path = tmp_dir / f"batch_{bi:03d}.mp3"
            batch_audio_path.write_bytes(base64.b64decode(result["audio_base64"]))
            batch_audio_paths.append(batch_audio_path)

            words = words_from_alignment(result["alignment"])
            # local_ranges' para_index is 0..len(batch_paras)-1 -- remap to the
            # real global paragraph index (idxs[local_i]) before building timing.
            global_ranges = [(idxs[local_i], start, end) for local_i, start, end in local_ranges]
            para_timing = build_paragraph_timing(words, global_ranges)

            for w in words:
                w["start"] += time_offset
                w["end"] += time_offset
                all_words.append(w)
            for pt in para_timing:
                pt["start"] += time_offset
                pt["end"] += time_offset
                all_para_timing.append(pt)

            batch_duration = audio_duration(batch_audio_path)
            if batch_duration is None:
                sys.exit(f"Couldn't read {batch_audio_path}'s duration (ffprobe missing/failed) -- "
                         "can't safely offset the next batch's timestamps.")
            time_offset += batch_duration

        print(f"\nStitching {len(batch_audio_paths)} batch(es) into {audio_path}...")
        concat_audio(batch_audio_paths, audio_path)
    finally:
        for p in tmp_dir.glob("*.mp3"):
            p.unlink(missing_ok=True)
        tmp_dir.rmdir()

    all_para_timing.sort(key=lambda pt: pt["paragraph"])
    duration = audio_duration(audio_path)

    timestamps_path.write_text(json.dumps({
        "duration": duration,
        "words": [{k: v for k, v in w.items() if k != "char_start_index"} for w in all_words],
        "paragraphs": all_para_timing,
    }, indent=2) + "\n")

    print(f"\nDone -> {audio_path}" + (f" ({duration:.1f}s)" if duration else "") + f", {timestamps_path}")
    if duration:
        expected = word_count / 207 * 60
        drift = (duration - expected) / expected * 100
        print(f"  Expected ~{expected:.0f}s at target pace, got {duration:.1f}s "
              f"({drift:+.1f}% vs. target) -- large drift means the delivery came out "
              "much slower/faster than voice.md's pace target; worth a listen.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    lv = sub.add_parser("list-voices", help="List voices on this ElevenLabs account (needs Voices:Read)")

    gen = sub.add_parser("generate", help="Generate narration for one video")
    gen.add_argument("video_dir", type=Path)
    gen.add_argument("--voice-id")
    gen.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    gen.add_argument("--stability", type=float, default=DEFAULT_STABILITY)
    gen.add_argument("--similarity", type=float, default=DEFAULT_SIMILARITY)
    gen.add_argument("--style", type=float, default=DEFAULT_STYLE)
    gen.add_argument("--force", action="store_true", help="regenerate even if narration.mp3 already exists")
    gen.add_argument("--dry-run", action="store_true", help="preview without calling the API")

    args = ap.parse_args()
    load_dotenv()
    if args.cmd == "list-voices":
        cmd_list_voices(args)
    else:
        cmd_generate(args)


if __name__ == "__main__":
    main()
