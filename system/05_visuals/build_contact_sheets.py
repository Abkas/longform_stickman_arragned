#!/usr/bin/env python3
"""
Builds labeled contact sheets (grids of thumbnails, N per sheet) from a
video's generate/generated/images/ folder, for visual QC review.

Why: reviewing 262 individual images one-by-one is impractical. Grouping
them into ~20-per-sheet grids, each thumbnail labeled with its shot
number, means the whole video can be visually scanned in ~13 sheet reads
instead of 262 individual ones -- each sheet lines up with one
run_full_batch.py chunk.

This does NOT do the actual quality judgment -- it only prepares the
sheets for a human (or Claude, reading them one at a time) to look at and
flag shot numbers that have a real problem: distorted anatomy (extra/
missing limbs, wrong hand count), wrong or garbled on-screen text,
off-model character style, or content that doesn't match the shot's own
prompt. Record flagged shot numbers in a redo list, then regenerate just
those with:

    python system/05_visuals/flow_batch_driver.py <video_dir> \\
        --project-url <url> --shots 5,9,201 --force

Usage:
    python system/05_visuals/build_contact_sheets.py videos/003-stoned-ape
    # writes videos/003-stoned-ape/generate/qc_sheets/sheet_001-020.jpg etc.

    python system/05_visuals/build_contact_sheets.py videos/003-stoned-ape --per-sheet 20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from verify_batch import parse_shot_list, MEDIA_EXTS  # noqa: E402

THUMB_W = 320  # per-cell width; height follows each image's own aspect ratio, capped
THUMB_MAX_H = 240
LABEL_H = 28
PADDING = 6
COLS = 5


def find_image_for_shot(images_dir: Path, shot_num: int) -> Path | None:
    matches = [p for p in images_dir.glob(f"{shot_num}_*") if p.suffix.lower() in MEDIA_EXTS]
    matches += [p for p in images_dir.glob(f"{shot_num}.*") if p.suffix.lower() in MEDIA_EXTS]
    if not matches:
        return None
    matches.sort(key=lambda p: len(p.name))
    return matches[0]


def make_sheet(cells: list[tuple[int, Path | None]], out_path: Path) -> None:
    rows = (len(cells) + COLS - 1) // COLS
    cell_h = THUMB_MAX_H + LABEL_H + PADDING * 2
    cell_w = THUMB_W + PADDING * 2
    sheet = Image.new("RGB", (cell_w * COLS, cell_h * rows), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
    except Exception:
        font = ImageFont.load_default()

    for i, (shot_num, img_path) in enumerate(cells):
        col, row = i % COLS, i // COLS
        x0 = col * cell_w + PADDING
        y0 = row * cell_h + PADDING

        if img_path is None:
            draw.rectangle([x0, y0, x0 + THUMB_W, y0 + THUMB_MAX_H], outline="red", width=3)
            draw.text((x0 + 10, y0 + 10), "MISSING", fill="red", font=font)
        else:
            try:
                im = Image.open(img_path).convert("RGB")
                im.thumbnail((THUMB_W, THUMB_MAX_H))
                paste_x = x0 + (THUMB_W - im.width) // 2
                paste_y = y0 + (THUMB_MAX_H - im.height) // 2
                sheet.paste(im, (paste_x, paste_y))
                draw.rectangle([x0, y0, x0 + THUMB_W, y0 + THUMB_MAX_H], outline="black", width=1)
            except Exception as e:
                draw.rectangle([x0, y0, x0 + THUMB_W, y0 + THUMB_MAX_H], outline="orange", width=3)
                draw.text((x0 + 10, y0 + 10), f"ERROR: {e}", fill="orange", font=font)

        label_y = y0 + THUMB_MAX_H + 4
        draw.text((x0, label_y), f"Shot {shot_num}", fill="black", font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=85)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video_dir", type=Path)
    ap.add_argument("--per-sheet", type=int, default=20)
    args = ap.parse_args()

    shot_list_path = args.video_dir / "shot_list.md"
    images_dir = args.video_dir / "generate" / "generated" / "images"
    out_dir = args.video_dir / "generate" / "qc_sheets"

    all_nums = [n for n, _ in parse_shot_list(shot_list_path)]

    sheets_written = []
    for i in range(0, len(all_nums), args.per_sheet):
        group = all_nums[i:i + args.per_sheet]
        cells = [(n, find_image_for_shot(images_dir, n)) for n in group]
        out_path = out_dir / f"sheet_{group[0]:03d}-{group[-1]:03d}.jpg"
        make_sheet(cells, out_path)
        sheets_written.append(out_path)
        missing_here = [n for n, p in cells if p is None]
        note = f" ({len(missing_here)} missing: {missing_here})" if missing_here else ""
        print(f"Wrote {out_path}{note}")

    print(f"\n{len(sheets_written)} sheet(s) written to {out_dir}")
    print("Have these reviewed (by eye, or hand each one to Claude to look at) for:")
    print("  - distorted anatomy (extra/missing limbs, wrong hand/finger count)")
    print("  - wrong or garbled on-screen text")
    print("  - character off the locked stick-figure design")
    print("  - content that doesn't match the shot's own prompt")
    print("Then regenerate flagged shots with:")
    print(f"  python system/05_visuals/flow_batch_driver.py {args.video_dir} "
          "--project-url <url> --shots <comma,separated,list> --force")


if __name__ == "__main__":
    main()
