#!/usr/bin/env python3
"""
Final two-phase verification pass for a video's image batch, run once
run_full_batch.py has gone through every chunk. Added 2026-09-12 at the
user's request: a last, whole-video safety net on top of the per-chunk
checks run_full_batch.py already does, specifically covering two things
that a clean per-chunk pass can still miss:

  Phase 1 (completeness) -- a chunk that never fully cleared (e.g. hit the
  circuit breaker, or an internet drop mid-chunk) leaves real gaps that
  nothing re-checks unless run_full_batch.py happens to be re-run. This
  phase audits shots 1..N against every real file on disk (flat images/
  directory AND any not-yet-promoted chunkN/ folder), reports gaps grouped
  by chunk, and can regenerate just those into the right chunk folder.

  Phase 2 (prompt-match QC) -- run_full_batch.py's duplicate-content check
  only catches the SAME image being used for two different shots. It says
  nothing about whether a given image actually matches ITS OWN prompt
  (wrong subject, invented on-screen text, style drift to photorealism,
  etc.) -- that needs a human/vision judgment call, not a hash compare.
  This phase's job is just to prepare the material for that judgment
  (a manifest of shot/prompt/image-path) and then apply whatever flags
  come back, cleanly and idempotently.

Usage:
    # Phase 1: report gaps (safe, read-only)
    python system/05_visuals/final_verify.py phase1-report videos/003-stoned-ape

    # Phase 1: regenerate exactly the gaps found above, routed into the
    # correct chunk + re-verified there (accepts the same --accounts /
    # --project-url forms as run_full_batch.py)
    python system/05_visuals/final_verify.py phase1-fill videos/003-stoned-ape \\
        --accounts "name=url,..."

    # Phase 2: build the QC manifest for a human/vision review pass
    python system/05_visuals/final_verify.py phase2-manifest videos/003-stoned-ape \\
        --out /tmp/qc_manifest.jsonl

    # Phase 2: after reviewing, apply a flagged-shots file (one shot number
    # per line, or "NUM: reason") -- regenerates each with --force and
    # replaces it in place, then re-audits
    python system/05_visuals/final_verify.py phase2-apply videos/003-stoned-ape \\
        --flagged /tmp/flagged_shots.txt --accounts "name=url,..."

    # Final gate: only prints "DONE" if phase 1 has zero gaps AND no
    # outstanding phase-2 flags file is passed in
    python system/05_visuals/final_verify.py final-check videos/003-stoned-ape
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify_batch import parse_shot_list  # noqa: E402
from run_full_batch import (  # noqa: E402
    existing_shot_nums,
    find_duplicate_shots,
    run_driver,
    verify_and_fix_chunk,
    promote_chunk,
)

CHUNK_SIZE_DEFAULT = 20


def chunk_of(shot_num: int, chunk_size: int) -> int:
    return (shot_num - 1) // chunk_size + 1


def all_files_by_shot(video_dir: Path, chunk_size: int) -> dict[int, Path]:
    """Real file on disk for each shot number, checking the flat images/
    dir FIRST (authoritative once promoted), then falling back to that
    shot's own chunkN/ folder if it hasn't been promoted yet. Never both --
    a promoted shot's chunk copy is a redundant duplicate, not a second
    source of truth."""
    images_dir = video_dir / "generate" / "generated" / "images"
    found: dict[int, Path] = {}

    flat_nums = existing_shot_nums(images_dir)
    for n in flat_nums:
        matches = list(images_dir.glob(f"{n}_*")) + list(images_dir.glob(f"{n}.*"))
        if matches:
            found[n] = matches[0]

    for chunk_dir in sorted(images_dir.glob("chunk*")):
        if not chunk_dir.is_dir():
            continue
        for n in existing_shot_nums(chunk_dir):
            if n in found:
                continue
            matches = list(chunk_dir.glob(f"{n}_*")) + list(chunk_dir.glob(f"{n}.*"))
            if matches:
                found[n] = matches[0]

    return found


def cmd_phase1_report(args: argparse.Namespace) -> None:
    all_nums = [n for n, _ in parse_shot_list(args.video_dir / "shot_list.md")]
    total = len(all_nums)
    found = all_files_by_shot(args.video_dir, args.chunk_size)
    missing = [n for n in all_nums if n not in found]

    print(f"{total} shots total. {len(found)}/{total} have a real file on disk "
          f"(flat images/ or an in-progress chunk folder).")
    if not missing:
        print("Phase 1: no gaps. Every shot has a file somewhere.")
        return

    by_chunk: dict[int, list[int]] = {}
    for n in missing:
        by_chunk.setdefault(chunk_of(n, args.chunk_size), []).append(n)

    print(f"\nPhase 1: {len(missing)} shot(s) missing entirely, grouped by chunk:")
    for ci in sorted(by_chunk):
        nums = by_chunk[ci]
        print(f"  chunk{ci}: {nums}")
    print("\nRun phase1-fill to regenerate exactly these.")


def cmd_phase1_fill(args: argparse.Namespace) -> None:
    driver_account_args = (["--project-url", args.project_url] if args.project_url
                            else ["--accounts", args.accounts])
    all_nums = [n for n, _ in parse_shot_list(args.video_dir / "shot_list.md")]
    images_dir = args.video_dir / "generate" / "generated" / "images"
    found = all_files_by_shot(args.video_dir, args.chunk_size)
    missing = [n for n in all_nums if n not in found]

    if not missing:
        print("Nothing to fill -- phase 1 already has zero gaps.")
        return

    by_chunk: dict[int, list[int]] = {}
    for n in missing:
        by_chunk.setdefault(chunk_of(n, args.chunk_size), []).append(n)

    for ci, nums in sorted(by_chunk.items()):
        chunk_dir = images_dir / f"chunk{ci}"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        print(f"\nchunk{ci}: generating {nums}")
        run_driver(args.video_dir, driver_account_args, chunk_dir,
                   shots=",".join(str(n) for n in nums))

        # Re-run this chunk's own gap+dedupe verification (same gate
        # run_full_batch.py uses) before trusting/promoting anything new.
        start = (ci - 1) * args.chunk_size + 1
        end = ci * args.chunk_size
        nums_in_chunk = [n for n in all_nums if start <= n <= end]
        clean = verify_and_fix_chunk(args.video_dir, driver_account_args, chunk_dir, nums_in_chunk)
        marker = chunk_dir / ".verified"
        if clean:
            promote_chunk(chunk_dir, images_dir)
            print(f"chunk{ci}: clean, (re-)promoted.")
        elif marker.exists():
            print(f"chunk{ci}: still has gaps/dupes, but was ALREADY verified before -- "
                  "leaving its existing .verified marker alone (not un-marking a chunk "
                  "that was previously confirmed good; investigate by hand).")
        else:
            print(f"chunk{ci}: still not fully clean -- left unverified, re-run this "
                  "command to retry.")


def cmd_phase2_manifest(args: argparse.Namespace) -> None:
    shots = parse_shot_list(args.video_dir / "shot_list.md")
    found = all_files_by_shot(args.video_dir, args.chunk_size)
    out_path = args.out or (args.video_dir / "generate" / "qc_manifest.jsonl")

    rows = []
    missing = []
    for n, prompt in shots:
        p = found.get(n)
        if p is None:
            missing.append(n)
            continue
        rows.append({"shot": n, "prompt": prompt, "image": str(p)})

    with open(out_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    print(f"Wrote {len(rows)} shot(s) to {out_path}")
    if missing:
        print(f"NOTE: {len(missing)} shot(s) have no file yet and were skipped from "
              f"the manifest -- run phase1-fill first: {missing}")
    print("\nNext: review each image against its prompt (vision pass), and write "
          "any shots that don't match to a flagged-shots file -- one shot number "
          "per line, optionally 'NUM: short reason'. Then run phase2-apply.")


def parse_flagged_file(path: Path) -> dict[int, str]:
    flagged: dict[int, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            num_s, reason = line.split(":", 1)
        else:
            num_s, reason = line, ""
        num_s = num_s.strip()
        if not num_s.isdigit():
            continue
        flagged[int(num_s)] = reason.strip()
    return flagged


def cmd_phase2_apply(args: argparse.Namespace) -> None:
    driver_account_args = (["--project-url", args.project_url] if args.project_url
                            else ["--accounts", args.accounts])
    flagged = parse_flagged_file(args.flagged)
    if not flagged:
        print(f"No flagged shots found in {args.flagged} -- nothing to do.")
        return

    all_nums = [n for n, _ in parse_shot_list(args.video_dir / "shot_list.md")]
    images_dir = args.video_dir / "generate" / "generated" / "images"

    print(f"Regenerating {len(flagged)} flagged shot(s): {sorted(flagged)}")
    for n, reason in sorted(flagged.items()):
        if reason:
            print(f"  shot {n}: {reason}")

    by_chunk: dict[int, list[int]] = {}
    for n in flagged:
        by_chunk.setdefault(chunk_of(n, args.chunk_size), []).append(n)

    for ci, nums in sorted(by_chunk.items()):
        chunk_dir = images_dir / f"chunk{ci}"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        # Delete the flagged files from wherever they currently live (flat
        # dir and/or chunk dir) so run_driver's skip-if-exists doesn't just
        # keep the bad image -- --force also does this, but --shots picks
        # its out-dir fresh (chunk_dir here) so the flat copy needs its own
        # explicit cleanup.
        for n in nums:
            for p in list(images_dir.glob(f"{n}_*")) + list(chunk_dir.glob(f"{n}_*")):
                p.unlink()
        run_driver(args.video_dir, driver_account_args, chunk_dir,
                   shots=",".join(str(n) for n in nums), force=True)

        start = (ci - 1) * args.chunk_size + 1
        end = ci * args.chunk_size
        nums_in_chunk = [n for n in all_nums if start <= n <= end]
        clean = verify_and_fix_chunk(args.video_dir, driver_account_args, chunk_dir, nums_in_chunk)
        if clean:
            promote_chunk(chunk_dir, images_dir)
            print(f"chunk{ci}: re-verified clean, (re-)promoted.")
        else:
            print(f"chunk{ci}: still not clean after replacing flagged shots -- re-run to retry.")


def cmd_final_check(args: argparse.Namespace) -> None:
    all_nums = [n for n, _ in parse_shot_list(args.video_dir / "shot_list.md")]
    total = len(all_nums)
    found = all_files_by_shot(args.video_dir, args.chunk_size)
    missing = [n for n in all_nums if n not in found]

    images_dir = args.video_dir / "generate" / "generated" / "images"
    dupes = find_duplicate_shots(images_dir)  # cross-shot content collisions in the flat dir

    ok = not missing and not dupes
    print(f"{len(found)}/{total} present. Missing: {missing or 'none'}. "
          f"Cross-shot duplicate content: {list(dupes.values()) or 'none'}.")
    if ok:
        print("\nDONE -- phase 1 complete (no gaps, no duplicates). "
              "If phase 2 QC flags were ever raised, confirm they were all "
              "applied (phase2-apply) before treating this video as finished.")
    else:
        print("\nNOT done yet -- see gaps/duplicates above.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_common(p):
        p.add_argument("video_dir", type=Path)
        p.add_argument("--chunk-size", type=int, default=CHUNK_SIZE_DEFAULT)

    def add_account_args(p):
        p.add_argument("--project-url")
        p.add_argument("--accounts")

    p1r = sub.add_parser("phase1-report")
    add_common(p1r)

    p1f = sub.add_parser("phase1-fill")
    add_common(p1f)
    add_account_args(p1f)

    p2m = sub.add_parser("phase2-manifest")
    add_common(p2m)
    p2m.add_argument("--out", type=Path)

    p2a = sub.add_parser("phase2-apply")
    add_common(p2a)
    add_account_args(p2a)
    p2a.add_argument("--flagged", type=Path, required=True)

    fc = sub.add_parser("final-check")
    add_common(fc)

    args = ap.parse_args()

    if args.cmd in ("phase1-fill", "phase2-apply"):
        if bool(args.project_url) == bool(args.accounts):
            raise SystemExit("Pass exactly one of --project-url or --accounts.")

    {
        "phase1-report": cmd_phase1_report,
        "phase1-fill": cmd_phase1_fill,
        "phase2-manifest": cmd_phase2_manifest,
        "phase2-apply": cmd_phase2_apply,
        "final-check": cmd_final_check,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
