#!/usr/bin/env python3
"""
Generate the channel's character and style reference images via the Gemini API.

OPTIONAL, not required for the primary workflow (see
system/04_shots/shot.md's "Primary method" section) — shot_list.md prompts are now
fully self-contained (style described in the prompt text itself), so no
reference image is needed to generate on-style shots. This script is still
useful as a personal visual-QA anchor (eyeball generated shots against it by
eye) or if generate_visuals.py's optional reference-image attachment is wanted
as extra consistency insurance on top of the self-contained prompts.

Not free — roughly $0.07/image at default resolution with the model below, so
~$0.13 for both. Cheap, but real.

Usage:
    Put GEMINI_API_KEY=... in a .env file at the repo root (see .env.example),
    or export it in your shell instead if you prefer.
    pip install -r system/05_visuals/requirements.txt
    python system/05_visuals/generate_character_reference.py

Re-running regenerates both images by default (character design is worth
iterating on). Pass --character-only or --style-only to regenerate just one.
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

CHARACTER_PROMPT = (
    "A single stickman-style animated character reference sheet, front-facing, "
    "standing in a plain neutral pose with arms slightly away from the body, "
    "centered on a flat plain light-gray background with no other objects or "
    "scenery. Round pale/white head with minimal facial features: simple small "
    "dot eyes and a short line mouth. Messy scribbly brown hair. Thin, "
    "black-outlined stick-like limbs and torso. Wearing simple prehistoric "
    "clothing: brown fur or leopard-print fabric wrapped around the torso and "
    "waist. Clean, fairly thick black outlines on the character, flat "
    "cel-shaded coloring with no gradients or painterly rendering on the "
    "figure itself. Sharp focus, evenly lit, no harsh shadows obscuring the "
    "design. This is a character reference sheet meant for reuse across many "
    "different scenes, not a finished illustration."
)

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
        print("Generating character reference...")
        generate_image(client, CHARACTER_PROMPT, OUT_DIR / "host_reference.png")

    if not args.character_only:
        print("Generating style reference...")
        generate_image(client, STYLE_PROMPT, OUT_DIR / "style_reference.png")

    print("\nReview both images against system/shared/references/images/inkexplainer96_*")
    print("for style match. Re-run this script (or edit the prompts above and")
    print("re-run) if either doesn't land — cheap and fast to iterate on since")
    print("these are single images, not a full shot-list batch.")


if __name__ == "__main__":
    main()
