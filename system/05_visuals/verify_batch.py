#!/usr/bin/env python3
"""
Post-batch verification/assignment helper for the free FlowBatch path
(system/04_shots/shot.md's "Generating the shots: the free path" section).

FlowBatch (and similar browser extensions) queue a pasted list of prompts,
generate each one, and bulk-download the results -- but video 002's batch
proved a finished batch is NOT evidence it's a correct batch: the extension
lost sync with its own queue on slow generations, saving a duplicate instead
of the new result and silently dropping the next prompt in line. 52 of 111
shots (47%) came back wrong, cascading in runs of 14+ shots. See shot.md's
"Post-batch verification" section for the full incident writeup -- this
script automates the two mechanical checks that section calls for by hand:

    1. dedupe  -- hash-compare a folder of freshly downloaded files and flag
                  exact duplicates BEFORE any visual review (catches most of
                  the desync bug for free, zero vision effort).
    2. assign  -- rename an ordered batch of anonymously-named downloads
                  (Flow/FlowBatch don't preserve shot numbers) into the
                  "{shot_num}_{slug}.ext" convention assemble.py looks for,
                  using file mtime as the order proxy -- and print the
                  mapping for you to eyeball against the prompts you pasted
                  BEFORE trusting it, since order-based assignment is
                  exactly the assumption that broke in video 002.
    3. audit   -- after assignment, cross-check generate/generated/images/
                  against shot_list.md: every shot 1..N has exactly one
                  file, nothing stray, nothing missing.

This does not touch Flow or any browser -- pure local file processing on
what you already downloaded. Doesn't replace looking at the images
(prompt-vs-image drift, style drift) -- only catches the mechanical
duplicate/skip failure mode and missing/stray files.

Usage:
    # 1. After a FlowBatch chunk finishes, dedupe the raw download folder:
    python system/05_visuals/verify_batch.py dedupe ~/Downloads/flow_batch_1

    # 2. Assign shot numbers to that chunk (order = download/mtime order),
    #    matching the exact range of shots you pasted for that chunk:
    python system/05_visuals/verify_batch.py assign ~/Downloads/flow_batch_1 \\
        videos/003-stoned-ape --range 1-20

    # 3. After all chunks are assigned, audit the whole video:
    python system/05_visuals/verify_batch.py audit videos/003-stoned-ape
"""

from __future__ import annotations

import hashlib
import re
import shutil
import sys
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".webm"}
MEDIA_EXTS = IMAGE_EXTS | VIDEO_EXTS


def parse_shot_list(shot_list_path: Path) -> list[tuple[int, str]]:
    """Return [(shot_num, prompt_text), ...] sorted by shot_num."""
    text = shot_list_path.read_text(encoding="utf-8")
    headers = list(re.finditer(r"^## Shot (\d+)$", text, re.MULTILINE))
    shots = []
    for i, h in enumerate(headers):
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[start:end]
        pm = re.search(r"^- Prompt:\s*(.+)$", block, re.MULTILINE)
        if not pm:
            raise SystemExit(f"Shot {h.group(1)}: no Prompt field found")
        shots.append((int(h.group(1)), pm.group(1).strip()))
    shots.sort(key=lambda s: s[0])
    return shots


def slugify(prompt: str) -> str:
    # Same convention as generate_visuals.py, so filenames match what
    # assemble.py's find_image() looks for ({shot_num}_{slug}.ext).
    return re.sub(r"[^a-z0-9]+", "-", prompt.lower()).strip("-")[:50]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_dedupe(args: list[str]) -> None:
    if not args:
        raise SystemExit("Usage: verify_batch.py dedupe <folder>")
    folder = Path(args[0])
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in MEDIA_EXTS)
    if not files:
        print(f"No media files found in {folder}")
        return

    by_hash: dict[str, list[Path]] = {}
    for p in files:
        by_hash.setdefault(sha256(p), []).append(p)

    dupes = {h: paths for h, paths in by_hash.items() if len(paths) > 1}
    print(f"Checked {len(files)} files in {folder}")
    if not dupes:
        print("No exact duplicates found.")
        return

    print(f"\n{sum(len(v) for v in dupes.values())} files involved in {len(dupes)} duplicate group(s):")
    for h, paths in dupes.items():
        print(f"\n  hash {h[:12]}...")
        for p in paths:
            print(f"    {p.name}")
    print(
        "\nThis is the exact signature of FlowBatch's queue-desync bug "
        "(video 002): a duplicate here almost always means the prompt "
        "AFTER this one in your pasted list got silently dropped and "
        "every following shot is now shifted by one. Re-generate this "
        "chunk rather than trusting it."
    )


def cmd_assign(args: list[str]) -> None:
    if len(args) < 3 or args[2] != "--range" and "--range" not in args:
        raise SystemExit(
            "Usage: verify_batch.py assign <downloaded_folder> <video_dir> --range START-END"
        )
    folder = Path(args[0])
    video_dir = Path(args[1])
    range_idx = args.index("--range")
    range_str = args[range_idx + 1]
    start_s, end_s = range_str.split("-")
    start, end = int(start_s), int(end_s)

    shot_list_path = video_dir / "shot_list.md"
    shots = dict(parse_shot_list(shot_list_path))
    wanted = [n for n in range(start, end + 1) if n in shots]
    if len(wanted) != (end - start + 1):
        missing = set(range(start, end + 1)) - set(shots)
        raise SystemExit(f"shot_list.md is missing shot numbers in range: {sorted(missing)}")

    downloaded = sorted(
        (p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in MEDIA_EXTS),
        key=lambda p: p.stat().st_mtime,
    )
    if len(downloaded) != len(wanted):
        raise SystemExit(
            f"Range {start}-{end} is {len(wanted)} shots, but {folder} has "
            f"{len(downloaded)} media files. Counts must match exactly -- "
            f"fix the folder or the --range before assigning anything."
        )

    out_dir = video_dir / "generate" / "generated" / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Proposed mapping (order = file mtime, oldest first) for shots {start}-{end}:\n")
    mapping = []
    for shot_num, src in zip(wanted, downloaded):
        prompt = shots[shot_num]
        slug = slugify(prompt)
        dest_name = f"{shot_num}_{slug}{src.suffix.lower()}"
        mapping.append((src, out_dir / dest_name, prompt))
        print(f"  {src.name}")
        print(f"    -> Shot {shot_num}: {prompt[:90]}{'...' if len(prompt) > 90 else ''}")
        print(f"    -> {dest_name}\n")

    print(
        "^ Check this against the actual images and the prompts you pasted "
        "for this chunk BEFORE confirming -- mtime order only holds if "
        "downloads landed in generation order with nothing else written "
        "into this folder meanwhile."
    )
    resp = input("\nType 'yes' to copy these files into generate/generated/images/: ").strip().lower()
    if resp != "yes":
        print("Aborted -- no files copied.")
        return

    for src, dest, _ in mapping:
        if dest.exists():
            raise SystemExit(f"Refusing to overwrite existing file: {dest}")
        shutil.copy2(src, dest)
    print(f"\nCopied {len(mapping)} files into {out_dir}")


def cmd_audit(args: list[str]) -> None:
    if not args:
        raise SystemExit("Usage: verify_batch.py audit <video_dir>")
    video_dir = Path(args[0])
    shot_list_path = video_dir / "shot_list.md"
    images_dir = video_dir / "generate" / "generated" / "images"
    shots = parse_shot_list(shot_list_path)
    total = len(shots)

    if not images_dir.is_dir():
        raise SystemExit(f"No such folder: {images_dir}")
    files = [p for p in images_dir.iterdir() if p.is_file() and p.suffix.lower() in MEDIA_EXTS]

    by_num: dict[int, list[Path]] = {}
    stray: list[Path] = []
    for p in files:
        m = re.match(r"^(\d+)[_.]", p.name)
        if not m:
            stray.append(p)
            continue
        by_num.setdefault(int(m.group(1)), []).append(p)

    missing = [n for n, _ in shots if n not in by_num]
    dup_nums = {n: ps for n, ps in by_num.items() if len(ps) > 1}
    out_of_range = sorted(set(by_num) - {n for n, _ in shots})

    print(f"shot_list.md: {total} shots. {images_dir}: {len(files)} media files.\n")

    if not missing and not dup_nums and not stray and not out_of_range:
        print(f"All clear -- exactly one file per shot, {total}/{total}.")
    else:
        if missing:
            print(f"MISSING ({len(missing)}): shots with no file -- {missing}")
        if dup_nums:
            print(f"\nDUPLICATE SHOT NUMBERS ({len(dup_nums)}): more than one file claims the same shot")
            for n, ps in sorted(dup_nums.items()):
                print(f"  Shot {n}: {[p.name for p in ps]}")
        if out_of_range:
            print(f"\nOUT-OF-RANGE numbers (no matching shot in shot_list.md): {out_of_range}")
        if stray:
            print(f"\nUNPARSEABLE filenames (don't start with a shot number): {[p.name for p in stray]}")

    # Cheap extra pass: exact-duplicate content across the whole folder,
    # same check as `dedupe` but scoped to the final assembled set.
    by_hash: dict[str, list[Path]] = {}
    for p in files:
        by_hash.setdefault(sha256(p), []).append(p)
    content_dupes = {h: ps for h, ps in by_hash.items() if len(ps) > 1}
    if content_dupes:
        print(f"\nBYTE-IDENTICAL FILES across different shot numbers ({len(content_dupes)} group(s)) -- near-certain desync signature:")
        for h, ps in content_dupes.items():
            print(f"  {[p.name for p in ps]}")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("dedupe", "assign", "audit"):
        print(__doc__)
        raise SystemExit(1)
    cmd, rest = sys.argv[1], sys.argv[2:]
    {"dedupe": cmd_dedupe, "assign": cmd_assign, "audit": cmd_audit}[cmd](rest)


if __name__ == "__main__":
    main()
