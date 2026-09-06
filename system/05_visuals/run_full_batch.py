#!/usr/bin/env python3
"""
Orchestrates flow_batch_driver.py across an entire video's shot_list.md in
chunks, self-healing gaps as it goes, until every shot has a downloaded
file (or it's genuinely stuck and says so).

For each chunk of CHUNK_SIZE shots:
    1. Run flow_batch_driver.py --range <chunk>.
    2. Check which shots in that chunk are still missing a file.
    3. If any are missing, wait a bit and re-run the SAME range (the driver
       already skips shots that succeeded, so this only retries the gaps)
       -- up to --max-retries times per chunk.
    4. Move to the next chunk regardless (a chunk that's still short after
       its retries gets swept up in the final cleanup pass instead of
       blocking the rest of the video).

After all chunks: one final pass re-checks the WHOLE video for any still-
missing shot (from anywhere, not just chunk edges), groups whatever's left
into contiguous ranges, and runs those too. Prints a final summary --
either "all N shots present" or the exact list of shots that never made it
through, for you to investigate by hand (a real Flow-side problem, not
something more retries will fix).

This can safely be Ctrl+C'd and re-run later -- everything is driven off
which files already exist on disk, same idempotent convention as
flow_batch_driver.py and generate_visuals.py.

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
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify_batch import parse_shot_list  # noqa: E402

DRIVER = Path(__file__).parent / "flow_batch_driver.py"


def existing_shot_nums(images_dir: Path) -> set[int]:
    nums = set()
    if not images_dir.is_dir():
        return nums
    for p in images_dir.iterdir():
        if p.is_file():
            head = p.name.split("_", 1)[0].split(".", 1)[0]
            if head.isdigit():
                nums.add(int(head))
    return nums


def missing_in_range(all_nums: list[int], have: set[int], start: int, end: int) -> list[int]:
    return [n for n in all_nums if start <= n <= end and n not in have]


def group_into_ranges(nums: list[int]) -> list[tuple[int, int]]:
    """Collapse a sorted list of shot numbers into contiguous (start, end) runs."""
    if not nums:
        return []
    nums = sorted(nums)
    ranges = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        ranges.append((start, prev))
        start = prev = n
    ranges.append((start, prev))
    return ranges


def run_chunk(video_dir: Path, driver_account_args: list[str], start: int, end: int) -> None:
    print(f"\n{'='*60}\nRunning shots {start}-{end}\n{'='*60}")
    subprocess.run([
        sys.executable, str(DRIVER), str(video_dir),
        *driver_account_args,
        "--range", f"{start}-{end}",
    ])


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
    print(f"{total} shots total ({all_nums[0]}-{all_nums[-1]}). Chunk size {args.chunk_size}.")

    chunks = []
    for i in range(0, total, args.chunk_size):
        group = all_nums[i:i + args.chunk_size]
        chunks.append((group[0], group[-1]))

    # Circuit breaker: a chunk that ends with ZERO new files despite having
    # gaps to fill isn't "unlucky", it's almost certainly the daily quota
    # running out, a Google security/verification wall, or the session
    # dying -- every later chunk would fail the exact same way. Left
    # unchecked overnight, that means grinding through the remaining
    # chunks' full retry budget for hours producing nothing. Stop instead
    # after CIRCUIT_BREAKER_CHUNKS consecutive chunks like that.
    CIRCUIT_BREAKER_CHUNKS = 2
    consecutive_total_failures = 0
    aborted = False

    for ci, (start, end) in enumerate(chunks):
        have = existing_shot_nums(images_dir)
        gaps_before = missing_in_range(all_nums, have, start, end)
        if not gaps_before:
            print(f"\nChunk {start}-{end}: already complete, skipping.")
            continue

        for attempt in range(1 + args.max_retries):
            if attempt > 0:
                have = existing_shot_nums(images_dir)
                gaps = missing_in_range(all_nums, have, start, end)
                if not gaps:
                    break
                print(f"\nChunk {start}-{end}: {len(gaps)} shot(s) still missing "
                      f"({gaps}) -- retry {attempt}/{args.max_retries} in {args.retry_pause}s")
                time.sleep(args.retry_pause)
            run_chunk(args.video_dir, driver_account_args, start, end)

        have = existing_shot_nums(images_dir)
        gaps_after = missing_in_range(all_nums, have, start, end)
        got_any = len(gaps_before) > len(gaps_after)

        if gaps_after:
            print(f"\nChunk {start}-{end}: still missing after all retries: {gaps_after} "
                  f"-- will retry once more in the final cleanup pass.")

        if got_any:
            consecutive_total_failures = 0
        else:
            consecutive_total_failures += 1
            print(f"\nChunk {start}-{end} produced ZERO new files across "
                  f"{1 + args.max_retries} attempts ({consecutive_total_failures}/"
                  f"{CIRCUIT_BREAKER_CHUNKS} consecutive fully-failed chunks).")
            if consecutive_total_failures >= CIRCUIT_BREAKER_CHUNKS:
                print(f"\n{'!'*60}\nSTOPPING EARLY: {CIRCUIT_BREAKER_CHUNKS} chunks in a "
                      "row produced nothing at all. This is almost certainly NOT "
                      "random flakiness -- likely causes: Flow's daily free quota "
                      "ran out, Google threw a sign-in/security check the script "
                      "can't click through, or the browser session died/logged "
                      "out. Check system/05_visuals/.flow_debug/ screenshots and "
                      "the Chromium window itself. Skipping remaining chunks and "
                      f"the final cleanup pass.\n{'!'*60}")
                aborted = True
                break

        if ci < len(chunks) - 1:
            print(f"\nResting {args.chunk_pause}s before next chunk...")
            time.sleep(args.chunk_pause)

    # Final whole-video cleanup pass (skipped if the circuit breaker
    # already tripped -- it would just fail identically).
    if not aborted:
        have = existing_shot_nums(images_dir)
        still_missing = [n for n in all_nums if n not in have]
        if still_missing:
            print(f"\n{'='*60}\nFinal cleanup pass: {len(still_missing)} shot(s) still "
                  f"missing across the whole video: {still_missing}\n{'='*60}")
            for start, end in group_into_ranges(still_missing):
                run_chunk(args.video_dir, driver_account_args, start, end)
                time.sleep(args.chunk_pause)

    have = existing_shot_nums(images_dir)
    final_missing = [n for n in all_nums if n not in have]
    print(f"\n{'='*60}")
    if final_missing:
        print(f"DONE, but {len(final_missing)}/{total} shots never succeeded: {final_missing}")
        print("Re-running this script will retry only these (everything else is skipped).")
    else:
        print(f"DONE -- all {total} shots have a file.")
    print(f"{'='*60}")
    print(f"\nRun `python system/05_visuals/verify_batch.py audit {args.video_dir}` "
          "to check for duplicates/mismatches, and spot-check images by eye for "
          "style drift -- this script only confirms files exist, not that they're correct.")


if __name__ == "__main__":
    main()
