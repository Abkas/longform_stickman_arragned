#!/usr/bin/env python3
"""
Generate per-shot visuals (images and/or short video clips) for a video from its
shot_list.md, using the Gemini API directly.

Prompts in shot_list.md are expected to be fully self-contained (character
appearance / art style spelled out in the prompt text itself, per each shot's
"- Visual:" tag — see system/04_shots/shot.md's "Primary method"
section) rather than relying on an attached reference image, since some batch
tools only support one reference image for a whole batch and that risks forcing
a character into diagram/environment shots that shouldn't have one. A character
reference SET at system/05_visuals/character_reference/host_reference_*.png
(see generate_character_reference.py) is therefore OPTIONAL — if present, it
gets attached, but ONLY on "- Visual: character" shots, never on diagram/
environment shots, for the same reason a batch tool shouldn't force a
character reference onto a shot that isn't supposed to have one. If absent,
generation just proceeds on the prompt text alone.

Character shots also default to a different, pricier model than everything
else (see CHARACTER_MODEL below) — research 2026-08-22 found Gemini 3 Pro
Image ("Nano Banana Pro") specifically documents support for up to 5
character-reference images used to hold one character's identity consistent
across generations, which is exactly the video-002 failure mode (character
style drifted off-model across a batch using the same text prompt). The
flash model used for diagram/environment shots doesn't carry that same
documented guarantee, but is fine for those since there's no recurring
character identity to hold onto there.

This bypasses Google Flow's UI entirely — Flow wraps the same underlying
Gemini/Imagen (image) and Veo (video) models, which are also available directly
through the API, and Flow itself has no official automation API.

Each shot in shot_list.md can specify "- Type: image" or "- Type: video"
(defaults to image if omitted). Video generation is meaningfully more expensive
and slower (polls for completion, ~1-3 min per clip) than image generation —
per system/04_shots/shot.md's recommendation, most shots should be
images with a small number of video clips reserved for key dynamic beats.

KNOWN ISSUE (as of 2026-08-04): there are live reports of the video API's
reference_images parameter throwing a 400 INVALID_ARGUMENT error despite being
documented as supported. If video generation fails specifically on the
reference_images argument, check the Gemini API developer forum for current
status — this may need to fall back to a strongly-worded text description of
the character instead of an attached reference image until Google fixes it.

Neither image nor video generation is free — see system/04_shots/shot.md
for current per-shot cost estimates. Not huge for one video (a few dollars),
but not zero either.

Usage:
    Put GEMINI_API_KEY=... in a .env file at the repo root (see .env.example),
    or export it in your shell instead if you prefer.
    pip install -r system/05_visuals/requirements.txt
    python system/05_visuals/generate_visuals.py videos/001-toba-supervolcano

Re-running is safe: shots that already have an output file in
generate/generated/images/ are skipped. Delete a specific output file to
force that one shot to regenerate.

Output location fixed 2026-08-13: this used to write to <video_dir>/visuals/,
which never matched the real convention actually used in practice (see
video 001's real files, all under generate/generated/images/) -- this was a
latent bug, never actually caught because video 001 was generated manually
through Flow, not through this script.
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
# default for diagram/environment shots, which don't need cross-shot identity
# consistency.
IMAGE_MODEL = "gemini-3.1-flash-image-preview"

# Character shots use this model instead (research 2026-08-22, see module
# docstring) — gemini-3-pro-image-preview is the tier Google specifically
# documents multi-image ("up to 5") character-reference consistency support
# on. Meaningfully pricier than the flash model above and 4K by default;
# check current per-image pricing at ai.google.dev before a full batch, the
# same way VIDEO_MODEL's cost is treated below. Worth the premium specifically
# for the shot type where video 002's style actually broke.
CHARACTER_MODEL = "gemini-3-pro-image-preview"

# Veo video generation — significantly more expensive per generation than the
# image model above. Clips come out ~8s by default; treat duration as fixed
# and do any trimming/extension in CapCut rather than fighting the API for it.
VIDEO_MODEL = "veo-3.1-generate-preview"
VIDEO_POLL_SECONDS = 10

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHARACTER_REF_DIR = REPO_ROOT / "system" / "05_visuals" / "character_reference"
# Matches host_reference_front.png, host_reference_action.png,
# host_reference_alarmed.png, etc. (see generate_character_reference.py) —
# glob rather than hardcoding the set so adding a new pose/expression later
# doesn't require a code change here too.
CHARACTER_REF_GLOB = "host_reference_*.png"
STYLE_REF = CHARACTER_REF_DIR / "style_reference.png"
# Gemini 3 Pro Image documents support for up to 5 character-reference images
# per generation (see module docstring) — cap here so an ever-growing
# reference set doesn't silently exceed that and start erroring or getting
# truncated by the API.
MAX_CHARACTER_REFS = 5

SHOT_BLOCK_RE = re.compile(r"^##\s*Shot\s+(\d+)\s*$", re.MULTILINE)
PROMPT_LINE_RE = re.compile(r"^-\s*Prompt:\s*(.+)$", re.MULTILINE)
TYPE_LINE_RE = re.compile(r"^-\s*Type:\s*(image|video)\s*$", re.MULTILINE | re.IGNORECASE)
VISUAL_LINE_RE = re.compile(r"^-\s*Visual:\s*(character|diagram|environment)\s*$", re.MULTILINE | re.IGNORECASE)

RATE_LIMIT_SECONDS = 2


def parse_shot_list(path: Path) -> list[tuple[int, str, str, str]]:
    """Returns a list of (shot_num, shot_type, visual_type, prompt) tuples."""
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

        # Defaults to "character" (the safer-to-over-attach-a-reference-on
        # side) only if the field is missing entirely, which shouldn't
        # happen on a real shot_list.md — every shot is supposed to be
        # tagged. Missing entirely is itself worth a warning.
        visual_match = VISUAL_LINE_RE.search(block)
        if not visual_match:
            print(f"  WARNING: Shot {shot_num:02d} has no '- Visual:' tag, assuming character")
        visual_type = visual_match.group(1).lower() if visual_match else "character"

        shots.append((shot_num, shot_type, visual_type, prompt_match.group(1).strip()))
    return shots


def load_character_references() -> list[Image.Image]:
    """The character reference SET (see generate_character_reference.py) —
    optional, returns [] if the directory/files don't exist yet rather than
    requiring the caller to build them first."""
    if not CHARACTER_REF_DIR.exists():
        return []
    paths = sorted(CHARACTER_REF_DIR.glob(CHARACTER_REF_GLOB))[:MAX_CHARACTER_REFS]
    return [Image.open(p) for p in paths]


def load_reference(path: Path) -> Image.Image | None:
    """Single optional reference image (used for the style reference) — just
    return None if not present, rather than requiring the caller to build one
    first."""
    if path.exists():
        return Image.open(path)
    return None


def generate_image_shot(client, model: str, character_refs, style_ref, prompt: str, out_path: Path) -> None:
    contents = list(character_refs)
    if style_ref is not None:
        contents.append(style_ref)
    contents.append(prompt)

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    image = response.candidates[0].content.parts[0].as_image()
    image.save(out_path)


def generate_video_shot(client, character_refs, style_ref, prompt: str, out_path: Path) -> None:
    reference_images = list(character_refs)
    if style_ref is not None:
        reference_images.append(style_ref)

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
        print("Usage: python system/05_visuals/generate_visuals.py videos/<slug>")
        sys.exit(1)

    video_dir = Path(sys.argv[1])
    shot_list_path = video_dir / "shot_list.md"
    images_dir = video_dir / "generate" / "generated" / "images"

    if not shot_list_path.exists():
        print(f"ERROR: no shot_list.md at {shot_list_path}")
        sys.exit(1)
    images_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: no GEMINI_API_KEY found. Put it in a .env file at the repo")
        print("root (GEMINI_API_KEY=...), or export it in your shell first.")
        sys.exit(1)

    character_refs = load_character_references()
    style_ref = load_reference(STYLE_REF)
    if not character_refs:
        print("No character reference set found (optional) — character shots will")
        print("generate from prompt text alone. Run generate_character_reference.py")
        print("first if you want the consistency boost (see that script + this")
        print("script's module docstring, research 2026-08-22).")
    else:
        print(f"Loaded {len(character_refs)} character reference image(s) — will attach")
        print("to '- Visual: character' shots only, not diagram/environment shots.")

    client = genai.Client(api_key=api_key)

    shots = parse_shot_list(shot_list_path)
    print(f"Found {len(shots)} shots in {shot_list_path}")

    for shot_num, shot_type, visual_type, prompt in shots:
        ext = "mp4" if shot_type == "video" else "png"
        # Plain, non-zero-padded shot number + a short slug of the prompt text,
        # matching the real naming convention already used by manually-generated
        # (Flow) shots -- e.g. "4_standing-in-front-of-a-vending-machine...jpeg".
        # assemble.py's image lookup globs "{shot_num}_*"/"{shot_num}.*", so this
        # naming isn't just cosmetic -- a zero-padded name wouldn't be found.
        slug = re.sub(r"[^a-z0-9]+", "-", prompt.lower()).strip("-")[:50]
        existing = list(images_dir.glob(f"{shot_num}_*")) + list(images_dir.glob(f"{shot_num}.*"))
        if existing:
            print(f"Shot {shot_num:02d} ({shot_type}/{visual_type}): already generated, skipping")
            continue
        out_path = images_dir / f"{shot_num}_{slug}.{ext}"

        # Only attach the character reference set on shots actually tagged
        # "character" — attaching it to a diagram/environment shot risks
        # forcing the host into a shot that isn't supposed to have one, the
        # same reasoning that ruled out a single global reference for batch
        # tools in the first place (see shot.md's "Primary method" section).
        shot_character_refs = character_refs if visual_type == "character" else []
        model = CHARACTER_MODEL if visual_type == "character" else IMAGE_MODEL

        print(f"Shot {shot_num:02d} ({shot_type}/{visual_type}, model={model}): generating ({prompt[:60]}...)")
        try:
            if shot_type == "video":
                generate_video_shot(client, shot_character_refs, style_ref, prompt, out_path)
            else:
                generate_image_shot(client, model, shot_character_refs, style_ref, prompt, out_path)
            print(f"  saved -> {out_path}")
        except Exception as exc:  # noqa: BLE001 - report and continue to next shot
            print(f"  FAILED shot {shot_num:02d}: {exc}")
            if shot_type == "video" and "reference_image" in str(exc).lower():
                print("  ^ this may be the known reference_images API bug — see module docstring")

        time.sleep(RATE_LIMIT_SECONDS)


if __name__ == "__main__":
    main()
