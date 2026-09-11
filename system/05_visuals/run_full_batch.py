#!/usr/bin/env python3
"""
Orchestrates flow_batch_driver.py across an entire video's shot_list.md,
chunk by chunk (default 20 shots/chunk), with a full verify-before-advance
gate on each chunk -- rewritten 2026-09-10 at the user's request, after a
real bug where the same generated image ended up saved under more than one
shot number (shots 1/18/20 all identical; 23/24 identical) once a chunk's
files were trusted without checking.

Per chunk:
    1. Generate into its OWN subfolder, images/chunkN/ -- not the shared
       flat images/ directory -- so a chunk's files can be fully checked in
       isolation before anything from it is trusted.
    2. Run flow_batch_driver.py --range <chunk> --out-dir images/chunkN/,
       retrying missing shots up to --max-retries times.
    3. Audit images/chunkN/ for duplicate images: the same picture saved
       under two DIFFERENT shot numbers is treated as a real bug (not
       "duplicate files", a mismatch), never just deduped and kept -- ALL
       copies of an affected shot are deleted and regenerated with
       --force, then re-audited, up to a few rounds.
    4. Only once a chunk has every shot present AND zero duplicate images
       is it "verified": every file gets copied into the flat images/
       directory (the location the rest of the pipeline, assemble.py,
       expects), and a chunkN/.verified marker is written.
    5. A chunk with a .verified marker is skipped entirely on every future
       run -- never touched, never re-audited, never re-downloaded.

A chunk that ends up NOT fully clean (missing shots, or duplicates that
survived every regeneration round) is left unmarked and simply retried
whole the next time this script runs -- it does not block later chunks,
but it also never gets falsely marked done.

Any images/ files that predate this chunked design (already on disk from
before this rewrite) get migrated into their chunk's subfolder on first
encounter (not re-downloaded) specifically so they still go through the
duplicate audit -- this is how a video that already has undiscovered
cross-shot duplicates (like this one) gets them found and fixed, not just
silently trusted because a file already existed.

Usage:
    python system/05_visuals/run_full_batch.py videos/003-stoned-ape \\
        --project-url https://flow.google.com/project/<your-project-id>

    # optional tuning:
    python system/05_visuals/run_full_batch.py videos/003-stoned-ape \\
        --project-url https://flow.google.com/project/<id> \\
        --chunk-size 20 --max-retries 2 --chunk-pause 30

    # multi-account rotation (see flow_batch_driver.py's own docstring for
    # how the rotation/cooldown ladder works) -- just forwarded through
    # to each chunk's flow_batch_driver.py call unchanged:
    python system/05_visuals/run_full_batch.py videos/003-stoned-ape \\
        --accounts "default=https://flow.google.com/project/aaa,acc2=https://flow.google.com/project/bbb"
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify_batch import parse_shot_list  # noqa: E402

DRIVER = Path(__file__).parent / "flow_batch_driver.py"


def existing_shot_nums(a_dir: Path) -> set[int]:
    """Shot numbers with a file directly inside a_dir (non-recursive --
    won't reach into a chunk subfolder from the parent, or vice versa)."""
    nums = set()
    if not a_dir.is_dir():
        return nums
    for p in a_dir.iterdir():
        if p.is_file():
            head = p.name.split("_", 1)[0].split(".", 1)[0]
            if head.isdigit():
                nums.add(int(head))
    return nums


def file_hash(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def find_duplicate_shots(chunk_dir: Path) -> dict[str, list[int]]:
    """Group chunk_dir's files by content hash; return only groups where
    the SAME image is saved under 2+ DIFFERENT shot numbers -- a real
    correctness bug (the wrong tile got downloaded for one of them), not
    just "duplicate files" to dedupe and move on from."""
    by_hash: dict[str, list[int]] = {}
    if not chunk_dir.is_dir():
        return {}
    for p in sorted(chunk_dir.iterdir()):
        if not p.is_file() or p.name.startswith("."):
            continue
        head = p.name.split("_", 1)[0].split(".", 1)[0]
        if not head.isdigit():
            continue
        by_hash.setdefault(file_hash(p), []).append(int(head))
    return {h: nums for h, nums in by_hash.items() if len(set(nums)) > 1}


def run_driver(video_dir: Path, driver_account_args: list[str], out_dir: Path,
                *, range_: str | None = None, shots: str | None = None, force: bool = False) -> None:
    cmd = [sys.executable, str(DRIVER), str(video_dir), *driver_account_args,
           "--out-dir", str(out_dir)]
    cmd += ["--range", range_] if range_ else ["--shots", shots]
    if force:
        cmd.append("--force")
    subprocess.run(cmd)


def migrate_preexisting_flat_files(images_dir: Path, chunk_dir: Path, nums_in_chunk: list[int]) -> None:
    """Copy (not move -- images_dir stays intact until this chunk is
    re-promoted) any file already sitting in the flat images_dir for a
    shot in this chunk's range into chunk_dir, so it gets audited instead
    of silently trusted. Only applies to files predating this chunked
    rewrite; a chunk that's gone through the new flow never has stray
    flat files needing migration since they'd already be inside some
    chunk's own .verified subfolder."""
    have_chunk = existing_shot_nums(chunk_dir)
    for n in nums_in_chunk:
        if n in have_chunk:
            continue
        for p in images_dir.glob(f"{n}_*"):  # non-recursive: direct children of images_dir only
            if p.is_file():
                shutil.copy2(p, chunk_dir / p.name)


def verify_and_fix_chunk(video_dir: Path, driver_account_args: list[str], chunk_dir: Path,
                          nums_in_chunk: list[int], max_dedup_rounds: int = 3) -> bool:
    """Regenerate any shot whose image content collides with a different
    shot's, up to max_dedup_rounds times. Returns True only if the chunk
    ends up with every shot present and zero duplicate images."""
    for round_num in range(1, max_dedup_rounds + 1):
        dupes = find_duplicate_shots(chunk_dir)
        if not dupes:
            break
        bad_shots = sorted({n for nums in dupes.values() for n in nums})
        print(f"\n  !! Duplicate-image check: {len(bad_shots)} shot(s) share content with "
              f"a DIFFERENT shot number (round {round_num}/{max_dedup_rounds}):")
        for nums in dupes.values():
            print(f"     same image used for shots: {sorted(set(nums))}")
        print(f"  Deleting and regenerating: {bad_shots}")
        for n in bad_shots:
            for p in chunk_dir.glob(f"{n}_*"):
                p.unlink()
        run_driver(video_dir, driver_account_args, chunk_dir,
                   shots=",".join(str(n) for n in bad_shots), force=True)

    dupes = find_duplicate_shots(chunk_dir)
    have = existing_shot_nums(chunk_dir)
    gaps = [n for n in nums_in_chunk if n not in have]
    if dupes:
        print(f"\n  !! Still has duplicate images after {max_dedup_rounds} regeneration "
              "round(s) -- leaving unverified, will retry on the next run.")
        return False
    if gaps:
        print(f"\n  Still missing {gaps} -- leaving unverified.")
        return False
    return True


def promote_chunk(chunk_dir: Path, images_dir: Path) -> None:
    """Copy a verified-clean chunk's files into the flat images/ directory
    (what the rest of the pipeline -- assemble.py -- expects), then mark
    the chunk done so it's never regenerated, re-audited, or even looked
    at again."""
    images_dir.mkdir(parents=True, exist_ok=True)
    for p in sorted(chunk_dir.iterdir()):
        if p.is_file() and p.suffix.lower() == ".png":
            shutil.copy2(p, images_dir / p.name)
    (chunk_dir / ".verified").touch()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video_dir", type=Path)
    ap.add_argument("--project-url", help="Single-account mode. Mutually exclusive with --accounts.")
    ap.add_argument("--accounts", help="Multi-account rotation mode -- same "
                     "name=project-url,... format as flow_batch_driver.py's "
                     "--accounts, forwarded through unchanged to every chunk "
                     "run. Mutually exclusive with --project-url.")
    ap.add_argument("--chunk-size", type=int, default=20)
    ap.add_argument("--max-retries", type=int, default=2, help="extra attempts per chunk if shots are still missing after the first run")
    ap.add_argument("--chunk-pause", type=int, default=120, help="seconds to rest between chunks (widened after a real run got flagged by Google for unusual activity)")
    ap.add_argument("--retry-pause", type=int, default=30, help="seconds to wait before retrying a chunk's gaps")
    args = ap.parse_args()

    if bool(args.project_url) == bool(args.accounts):
        raise SystemExit("Pass exactly one of --project-url (single account) "
                          "or --accounts (multi-account rotation).")
    driver_account_args = (["--project-url", args.project_url] if args.project_url
                            else ["--accounts", args.accounts])

    shot_list_path = args.video_dir / "shot_list.md"
    images_dir = args.video_dir / "generate" / "generated" / "images"
    all_nums = [n for n, _ in parse_shot_list(shot_list_path)]
    total = len(all_nums)
    print(f"{total} shots total ({all_nums[0]}-{all_nums[-1]}). Chunk size {args.chunk_size}, "
          "each chunk fully verified (all present, no cross-shot duplicates) before the next one starts.")

    chunks = []  # (chunk_index, start, end, [shot nums])
    for i in range(0, total, args.chunk_size):
        group = all_nums[i:i + args.chunk_size]
        chunks.append((i // args.chunk_size + 1, group[0], group[-1], group))

    # Circuit breaker: a chunk that ends its attempt loop with ZERO new
    # files despite having gaps almost certainly means something
    # structural is broken (quota exhausted everywhere, no internet, a
    # security wall) -- every later chunk would fail identically. Stop
    # rather than grinding through the rest of the video for hours.
    CIRCUIT_BREAKER_CHUNKS = 2
    consecutive_total_failures = 0

    for ci, start, end, nums_in_chunk in chunks:
        chunk_dir = images_dir / f"chunk{ci}"
        marker = chunk_dir / ".verified"
        if marker.exists():
            print(f"\nChunk {ci} ({start}-{end}): already verified, skipping.")
            continue

        chunk_dir.mkdir(parents=True, exist_ok=True)
        migrate_preexisting_flat_files(images_dir, chunk_dir, nums_in_chunk)

        print(f"\n{'='*60}\nChunk {ci}: shots {start}-{end} -> {chunk_dir}\n{'='*60}")

        # Snapshot taken right after migration, before ANY of this chunk's
        # own work (gap-filling below, or the dedup regeneration inside
        # verify_and_fix_chunk) -- compared against a snapshot after
        # EVERYTHING, so "did this chunk make progress" credits a
        # successful dedup regeneration just as much as a successful
        # gap-fill. Snapshotting only around the gap-fill loop (as an
        # earlier version of this function did) meant a chunk that fixed
        # real duplicates via regeneration but didn't happen to fill a
        # gap got miscounted as "zero new files" -- nearly tripped the
        # circuit breaker on a chunk that was actually working.
        have_before = existing_shot_nums(chunk_dir)
        for attempt in range(1 + args.max_retries):
            have = existing_shot_nums(chunk_dir)
            gaps = [n for n in nums_in_chunk if n not in have]
            if not gaps:
                break
            if attempt > 0:
                print(f"\nChunk {ci}: {len(gaps)} shot(s) still missing ({gaps}) "
                      f"-- retry {attempt}/{args.max_retries} in {args.retry_pause}s")
                time.sleep(args.retry_pause)
            run_driver(args.video_dir, driver_account_args, chunk_dir, range_=f"{start}-{end}")

        clean = verify_and_fix_chunk(args.video_dir, driver_account_args, chunk_dir, nums_in_chunk)
        have_after = existing_shot_nums(chunk_dir)
        got_any = len(have_after) > len(have_before)
        if clean:
            promote_chunk(chunk_dir, images_dir)
            print(f"\nChunk {ci} ({start}-{end}): verified clean (all present, no "
                  f"duplicates), promoted to {images_dir}, marked done -- won't be touched again.")
            consecutive_total_failures = 0
        else:
            print(f"\nChunk {ci} ({start}-{end}): NOT fully clean -- will be retried "
                  "whole on the next run (not marked done).")
            if got_any:
                consecutive_total_failures = 0
            else:
                consecutive_total_failures += 1
                print(f"Chunk {ci} produced ZERO new files "
                      f"({consecutive_total_failures}/{CIRCUIT_BREAKER_CHUNKS} consecutive "
                      "fully-failed chunks).")
                if consecutive_total_failures >= CIRCUIT_BREAKER_CHUNKS:
                    print(f"\n{'!'*60}\nSTOPPING EARLY: {CIRCUIT_BREAKER_CHUNKS} chunks in a "
                          "row produced nothing at all. Almost certainly NOT random flakiness "
                          "-- likely causes: quota exhausted on every account, no internet, a "
                          "Google security/sign-in wall the script can't click through, or the "
                          "browser session died/logged out. Check system/05_visuals/.flow_debug/ "
                          "screenshots.\n" + "!" * 60)
                    break

        if ci < len(chunks):
            print(f"\nResting {args.chunk_pause}s before next chunk...")
            time.sleep(args.chunk_pause)

    have_flat = existing_shot_nums(images_dir)
    final_missing = [n for n in all_nums if n not in have_flat]
    print(f"\n{'='*60}")
    if final_missing:
        print(f"DONE for now, but {len(final_missing)}/{total} shots never made it into "
              f"{images_dir}: {final_missing}")
        print("Re-running this script retries only the chunks that aren't marked verified "
              "-- already-verified chunks are skipped entirely.")
    else:
        print(f"DONE -- all {total} shots verified (present, no cross-shot duplicates) "
              f"and promoted to {images_dir}.")
    print(f"{'='*60}")
    print(f"\nRun `python system/05_visuals/verify_batch.py audit {args.video_dir}` for a "
          "second opinion, and spot-check images by eye for style drift -- the duplicate-image "
          "check here catches exact content collisions, not subjective quality/style issues.")


if __name__ == "__main__":
    main()
