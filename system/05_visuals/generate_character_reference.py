#!/usr/bin/env python3
"""
Generate the channel's character reference SET and style reference image via
the Gemini API.

Was a single front-facing portrait until 2026-08-22 — research into how
Gemini 3 Pro Image ("Nano Banana Pro") actually implements character
consistency found it accepts up to 5 character-reference images per
generation specifically to give the model multiple angles/expressions to
lock onto, and that AI-illustration workflows generally get meaningfully
better consistency from a small turnaround+expression set than from one
portrait — one image only tells the model what the character looks like
face-on, not what stays true when the pose or expression changes, which is
exactly the failure mode video 002 hit (see system/04_shots/character.md's
"Video 002 drift" section). This script now generates a small reference SET
instead: front pose, an action/gesture pose (character shots need rotating
poses per shot.md's pacing rules, so the reference set should show the
model that's still the same character), and an alarmed/surprised expression
(structure.md's hook-shot and export.md's thumbnail-checklist rules both
call for a strong legible emotion on this character specifically, so it's
worth a dedicated reference rather than hoping a neutral-pose reference
generalizes to it).

OPTIONAL, not required for the primary workflow (see
system/04_shots/shot.md's "Primary method" section) — shot_list.md prompts are
fully self-contained (style described in the prompt text itself), so no
reference image is needed to generate on-style shots. This script exists for
generate_visuals.py's character-reference attachment (see that script's
"Visual: character" handling) and as a personal visual-QA anchor (eyeball
generated shots against these by eye).

Not free — roughly $0.07/image at default resolution with the model below, so
~$0.28 for the 3-image character set + 1 style image. Cheap, but real.

Usage:
    Put GEMINI_API_KEY=... in a .env file at the repo root (see .env.example),
    or export it in your shell instead if you prefer.
    pip install -r system/05_visuals/requirements.txt
    python system/05_visuals/generate_character_reference.py

Re-running regenerates everything by default (character design is worth
iterating on). Pass --character-only or --style-only to regenerate just one
group.
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # reads .env at the repo root if present; no-op otherwise

# See generate_visuals.py for why gemini-2.5-flash-image is avoided (short
# remaining lifespan) in favor of this newer model.
MODEL = "gemini-3.1-flash-image-preview"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = REPO_ROOT / "system" / "05_visuals" / "character_reference"

# Shared identity block, reused verbatim across all three character-set
# prompts below — per the "identity block" consistency technique (keep the
# character description word-for-word constant, only vary the pose/expression
# clause), rather than re-describing the character slightly differently each
# time and giving the model room to drift between the three references
# themselves.
IDENTITY_BLOCK = (
    "A stickman-style animated character reference image, centered on a flat "
    "plain light-gray background with no other objects or scenery. Round "
    "pale/white head with minimal facial features: simple small dot eyes and "
    "a short line mouth. Messy scribbly brown hair. Thin, black-outlined "
    "stick-like limbs and torso, no muscles or anatomical shading. Wearing "
    "simple prehistoric clothing: brown fur or leopard-print fabric wrapped "
    "around the torso and waist. Clean, fairly thick black outlines on the "
    "character, flat cel-shaded coloring with no gradients or painterly "
    "rendering on the figure itself. Sharp focus, evenly lit, no harsh "
    "shadows obscuring the design. This is one image in a reference set "
    "meant for reuse across many different scenes, not a finished "
    "illustration."
)

CHARACTER_PROMPTS = {
    "host_reference_front.png": (
        IDENTITY_BLOCK + " Pose: front-facing, standing in a plain neutral "
        "pose with arms slightly away from the body."
    ),
    "host_reference_action.png": (
        IDENTITY_BLOCK + " Pose: three-quarter angle, mid-stride walking "
        "with one arm gesturing outward — a dynamic action pose, not a "
        "static stand, to show the character holds together in motion, not "
        "just standing still."
    ),
    "host_reference_alarmed.png": (
        IDENTITY_BLOCK + " Pose: front-facing, same neutral stance as the "
        "front reference, but with an alarmed/surprised facial expression — "
        "eyes wide, mouth open — since hook shots and thumbnails specifically "
        "need this character able to carry a strong, legible emotion, not "
        "just a calm default face."
    ),
}

STYLE_PROMPT = (
    "A moody, atmospheric illustrated environment reference establishing a "
    "visual style: warm orange firelight glowing from within a dark cave "
    "interior, contrasted against a cold blue-grey exterior visible through "
    "the cave mouth with fine ash or rain falling outside. Fully painted, "
    "richly detailed background art with rocky textures and soft directional "
    "lighting, dramatic cinematic color grading. No characters or figures in "
    "this image — purely an environmental lighting and color-palette "
    "reference."
)


def generate_image(client, prompt: str, out_path: Path) -> None:
    response = client.models.generate_content(
        model=MODEL,
        contents=[prompt],
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    image = response.candidates[0].content.parts[0].as_image()
    image.save(out_path)
    print(f"  saved -> {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--character-only", action="store_true")
    parser.add_argument("--style-only", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: no GEMINI_API_KEY found. Put it in a .env file at the repo")
        print("root (GEMINI_API_KEY=...), or export it in your shell first.")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = genai.Client(api_key=api_key)

    if not args.style_only:
        for filename, prompt in CHARACTER_PROMPTS.items():
            print(f"Generating {filename}...")
            generate_image(client, prompt, OUT_DIR / filename)

    if not args.character_only:
        print("Generating style reference...")
        generate_image(client, STYLE_PROMPT, OUT_DIR / "style_reference.png")

    print("\nReview all images against system/shared/references/images/inkexplainer96_*")
    print("for style match, and against each other for consistency (same hair,")
    print("same proportions, same outfit across all three character poses) —")
    print("that cross-consistency matters more here than it did for a single")
    print("portrait, since generate_visuals.py now attaches this whole set")
    print("together. Re-run this script (or edit the prompts above and")
    print("re-run) if any of them don't land.")


if __name__ == "__main__":
    main()
