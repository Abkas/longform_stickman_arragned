#!/usr/bin/env python3
"""
Generate per-shot visuals (images and/or short video clips) for a video from its
shot_list.md, using the Gemini API directly.

Prompts in shot_list.md are expected to be fully self-contained (character
appearance / art style spelled out in the prompt text itself, per each shot's
"- Visual:" tag — see assets/brain/visuals/flow_workflow.md's "Primary method"
section) rather than relying on an attached reference image, since some batch
tools only support one reference image for a whole batch and that risks forcing
a character into diagram/environment shots that shouldn't have one. A character
reference image at assets/character/host_reference.png is therefore OPTIONAL —
if present, it gets attached as an extra consistency aid; if absent, generation
just proceeds on the prompt text alone.

This bypasses Google Flow's UI entirely — Flow wraps the same underlying
Gemini/Imagen (image) and Veo (video) models, which are also available directly
through the API, and Flow itself has no official automation API.

Each shot in shot_list.md can specify "- Type: image" or "- Type: video"
(defaults to image if omitted). Video generation is meaningfully more expensive
and slower (polls for completion, ~1-3 min per clip) than image generation —
per assets/brain/visuals/flow_workflow.md's recommendation, most shots should be
images with a small number of video clips reserved for key dynamic beats.

KNOWN ISSUE (as of 2026-08-04): there are live reports of the video API's
reference_images parameter throwing a 400 INVALID_ARGUMENT error despite being
documented as supported. If video generation fails specifically on the
reference_images argument, check the Gemini API developer forum for current
status — this may need to fall back to a strongly-worded text description of
the character instead of an attached reference image until Google fixes it.

Neither image nor video generation is free — see assets/brain/visuals/flow_workflow.md
for current per-shot cost estimates. Not huge for one video (a few dollars),
but not zero either.

Usage:
    Put GEMINI_API_KEY=... in a .env file at the repo root (see .env.example),
    or export it in your shell instead if you prefer.
    pip install -r pipeline/requirements.txt
    python pipeline/generate_visuals.py videos/001-toba-supervolcano

Re-running is safe: shots that already have an output file in visuals/ are
skipped. Delete a specific output file to force that one shot to regenerate.
"""

import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()  # reads .env at the repo root if present; no-op otherwise

# gemini-2.5-flash-image is cheaper (~$0.039/image) but Google has it scheduled
# to shut down 2026-10-02 — too close to the start of production to build on.
# gemini-3.1-flash-image-preview (~$0.067/image) is the current, longer-lived
# default. Swap to "gemini-3-pro-image-preview" for higher quality (4K, better
# text rendering) at higher cost if this one's consistency isn't good enough.
IMAGE_MODEL = "gemini-3.1-flash-image-preview"

# Veo video generation — significantly more expensive per generation than the
# image model above. Clips come out ~8s by default; treat duration as fixed
# and do any trimming/extension in CapCut rather than fighting the API for it.
VIDEO_MODEL = "veo-3.1-generate-preview"
VIDEO_POLL_SECONDS = 10

REPO_ROOT = Path(__file__).resolve().parent.parent
CHARACTER_REF = REPO_ROOT / "assets" / "character" / "host_reference.png"
STYLE_REF = REPO_ROOT / "assets" / "character" / "style_reference.png"

SHOT_BLOCK_RE = re.compile(r"^##\s*Shot\s+(\d+)\s*$", re.MULTILINE)
PROMPT_LINE_RE = re.compile(r"^-\s*Prompt:\s*(.+)$", re.MULTILINE)
TYPE_LINE_RE = re.compile(r"^-\s*Type:\s*(image|video)\s*$", re.MULTILINE | re.IGNORECASE)

RATE_LIMIT_SECONDS = 2


def parse_shot_list(path: Path) -> list[tuple[int, str, str]]:
    """Returns a list of (shot_num, shot_type, prompt) tuples."""
    text = path.read_text(encoding="utf-8")
    headers = list(SHOT_BLOCK_RE.finditer(text))
    shots = []
    for i, header in enumerate(headers):
        shot_num = int(header.group(1))
        block_start = header.end()
        block_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[block_start:block_end]

        prompt_match = PROMPT_LINE_RE.search(block)
        if not prompt_match:
            print(f"  WARNING: Shot {shot_num:02d} has no '- Prompt:' line, skipping")
            continue

        type_match = TYPE_LINE_RE.search(block)
        shot_type = type_match.group(1).lower() if type_match else "image"

        shots.append((shot_num, shot_type, prompt_match.group(1).strip()))
    return shots


def load_reference(path: Path) -> Image.Image | None:
    """Reference images are optional (see module docstring) — just return None
    if not present, rather than requiring the caller to build one first."""
    if path.exists():
        return Image.open(path)
    return None


def generate_image_shot(client, character_ref, style_ref, prompt: str, out_path: Path) -> None:
    contents = []
    if character_ref is not None:
        contents.append(character_ref)
    if style_ref is not None:
        contents.append(style_ref)
    contents.append(prompt)

    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    image = response.candidates[0].content.parts[0].as_image()
    image.save(out_path)


def generate_video_shot(client, character_ref, style_ref, prompt: str, out_path: Path) -> None:
    reference_images = [ref for ref in (character_ref, style_ref) if ref is not None]

    config_kwargs = {}
    if reference_images:
        config_kwargs["reference_images"] = reference_images

    operation = client.models.generate_videos(
        model=VIDEO_MODEL,
        prompt=prompt,
        config=types.GenerateVideosConfig(**config_kwargs),
    )
    while not operation.done:
        time.sleep(VIDEO_POLL_SECONDS)
        operation = client.operations.get(operation)

    generated_video = operation.response.generated_videos[0]
    client.files.download(file=generated_video.video)
    generated_video.video.save(str(out_path))


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python pipeline/generate_visuals.py videos/<slug>")
        sys.exit(1)

    video_dir = Path(sys.argv[1])
    shot_list_path = video_dir / "shot_list.md"
    visuals_dir = video_dir / "visuals"

    if not shot_list_path.exists():
        print(f"ERROR: no shot_list.md at {shot_list_path}")
        sys.exit(1)
    visuals_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: no GEMINI_API_KEY found. Put it in a .env file at the repo")
        print("root (GEMINI_API_KEY=...), or export it in your shell first.")
        sys.exit(1)

    character_ref = load_reference(CHARACTER_REF)
    style_ref = load_reference(STYLE_REF)
    if character_ref is None:
        print("No character reference found (optional) — generating from prompt text alone.")

    client = genai.Client(api_key=api_key)

    shots = parse_shot_list(shot_list_path)
    print(f"Found {len(shots)} shots in {shot_list_path}")

    for shot_num, shot_type, prompt in shots:
        ext = "mp4" if shot_type == "video" else "png"
        out_path = visuals_dir / f"{shot_num:02d}.{ext}"
        if out_path.exists():
            print(f"Shot {shot_num:02d} ({shot_type}): already generated, skipping")
            continue

        print(f"Shot {shot_num:02d} ({shot_type}): generating ({prompt[:60]}...)")
        try:
            if shot_type == "video":
                generate_video_shot(client, character_ref, style_ref, prompt, out_path)
            else:
                generate_image_shot(client, character_ref, style_ref, prompt, out_path)
            print(f"  saved -> {out_path}")
        except Exception as exc:  # noqa: BLE001 - report and continue to next shot
            print(f"  FAILED shot {shot_num:02d}: {exc}")
            if shot_type == "video" and "reference_image" in str(exc).lower():
                print("  ^ this may be the known reference_images API bug — see module docstring")

        time.sleep(RATE_LIMIT_SECONDS)


if __name__ == "__main__":
    main()
