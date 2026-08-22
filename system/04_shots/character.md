# Character design — locked, revised 2026-08-13 (fourth pass — no-invented-text + linework-vs-body-proportions clauses, see "Video 002 drift" below; hair itself unchanged since the 2026-08-09 third pass)

Channel-wide reference, not video-specific — applies to every future video's host character, same as the other `system/` reference docs.

## The problem (found by comparing real generated output)

User flagged liked outputs, saved to `videos/001-toba-supervolcano/testing/best_output/`. Comparing the three character portraits in that folder side by side surfaced a real consistency bug: **the hair is a different shape in every single generation**, despite using the exact same prompt text.

- `image.png` — big, loopy, wavy scribble hair, high volume, strands hanging over the forehead
- `image copy.png` — longer strands, swept to one side, asymmetric
- `image copy 2.png` — short, spiky tufts, low volume, doesn't cover the forehead

All three used the same character-suffix wording: *"messy scribbled brown hair drawn as a few loose lines."* That phrase is too open to interpretation — "a few loose lines" doesn't constrain shape, count, length, or position, so the model improvises something different every time.

## First fix attempt (2026-08-09, wrong direction — corrected below)

Locked onto `image copy 2.png`'s short-spiky-tufts look, on the reasoning that it was closest to the reference thumbnails. Tested in `testing/version_6/`. **User didn't like it** — confirmed the actual preferred look is `image.png`'s style, and explicitly saved that one plus its exact generation prompt into `testing/best_output/bst_ref/` (`image.png` + `ref.txt`) to remove any ambiguity about which one to lock onto.

Lesson: the fix needed wasn't just "make it prescriptive," it was "make it prescriptive *and confirm which specific look with the user before locking it in* — being specific about the wrong style is still wrong."

## Second fix attempt (also wrong direction — corrected below)

`bst_ref/image.png`'s hair, described precisely: a voluminous mop of loose, wavy, looping scribble-style strands — drawn as continuous loops and curls, not short spiky points. Several strands hang down loosely over the forehead and temples without covering the eyes. The overall shape is an unkempt, tousled mass extending outward and slightly upward on all sides, clearly more voluminous than a cropped/short cut.

> hair: a voluminous, messy mop of loose, wavy, looping scribble-style strands drawn as continuous loops and curls (not short spiky points), several strands hanging loosely down over the forehead and temples without covering the eyes, hair extends outward and slightly upward on all sides in an unkempt tousled shape, solid flat medium-brown color with zero gradient, shading, or highlights

Tested in `testing/version_7/`. **Also rejected by the user** — but for the opposite reason this time. The wording wasn't imprecise, it was *too* precise about drawing technique: "continuous loops and curls" got taken completely literally, and the model rendered dense, tight spiral ringlets across the whole head — much more ornate and curly than the loose, natural mess in `bst_ref/image.png`. User's direct feedback: *"you are doing too much with the hair, keep it natural like how it is in the best image, don't try to make it too detailed and stuff, just natural."*

Lesson: the first fix failed from being too vague (no shape/position constraints at all → wildly different hair every time). This second fix overcorrected by dictating actual stroke/drawing technique ("drawn as continuous loops and curls") — the model doesn't read that as "loosely wavy," it reads it as "draw literal curls." The fix is a middle ground: enough grounding to stay consistent (volume, length, general messiness, a few strands over the forehead) without specifying *how* the artist should render each strand.

## The actual fix: natural, not technical

Dropped "voluminous," "loops and curls," and "unkempt tousled shape extending outward/upward" — all language that reads as an instruction to draw literal spirals or an exaggerated poof. Replaced with a plain, natural description: medium length/volume, tousled/uneven, a few strands over the forehead, flat brown color. No stroke-technique instructions.

> hair: natural messy brown hair, medium length and volume, a bit tousled and uneven like it was never combed, a few strands falling loosely over the forehead, solid flat medium-brown color with no gradient, shading, or highlights

Also keeping the flat-skin-color reinforcement from the first attempt (that part wasn't the problem, no reason to drop it).

## Locked character suffix (revised 2026-08-13 — see "Video 002 drift" section below; supersedes the version_7-era text, applies to every `character`-tagged shot)

> Art style: flat 2D cartoon webcomic illustration, like Cyanide & Happiness, OverSimplified, or Sam O'Nella Academy — this is a STRICT requirement. ABSOLUTELY NOT photorealistic, NOT a digital painting, NOT concept art, NOT a photograph, no realistic textures or lighting anywhere in the image. These named references describe the flat 2D linework/illustration technique only — NOT body proportions; the character's body must follow the stick-limb description below exactly, even where that diverges from those comics' own fuller, clothed-body house style. Character: a simple stick figure with a round flat pale head, two small dot eyes, a short line mouth, thin uniform-width black-outlined stick limbs and torso with no muscles or anatomical shading, wearing simple flat-colored brown or leopard-print fabric. Hair: natural messy brown hair, medium length and volume, a bit tousled and uneven like it was never combed, a few strands falling loosely over the forehead, solid flat medium-brown color with no gradient, shading, or highlights. Skin: completely flat, solid, uniform pale color with zero gradient, shading, or highlights anywhere on the face or body. Bold, thick, uniform black outlines on every element in the frame — the character AND the background must be drawn in the exact same flat, simplified cartoon style, with solid or simply-shaded flat colors. The background is a simplified cartoon illustration, not a realistic painted scene or photo — same rule as the character: flat colors, bold outlines, no photorealistic texture or lighting. Do not add any speech bubbles, captions, sound-effect text (e.g. "CRUNCH", "SLURP"), on-screen dialogue, or any lettering anywhere in the frame unless it is explicitly described in this shot's own prompt text — no invented text of any kind, repeat: none.

## Video 002 drift (found + fixed 2026-08-13)

A full-batch audit of video 002's 111 generated images (documented in that
video's own review) surfaced two failures in this suffix that video 001
didn't have, both now fixed in the locked text above:

1. **Invented on-screen text.** ~8 of video 002's `character`-type shots
   added speech bubbles/sound-effect text/captions that weren't in the
   prompt at all (e.g. a fabricated "*CRUNCH! SMACK! CHOMP! SLURP!*"
   bubble). Diffing against the `diagram`/`environment` suffixes in
   `shot.md` found the actual gap: both of those suffixes already
   explicitly forbid inventing on-screen text — this one never did. Fixed
   by adding the same prohibition here.
2. **Full-bodied character instead of a stick figure.** Most/all of video
   002's character shots rendered a fully-bodied Cyanide & Happiness-style
   cartoon (visible torso mass, hands, shoulders) rather than the locked
   thin-stick-limb design — on the *exact same suffix wording* video 001
   used to produce a genuine stick figure (confirmed: video 001's shot 1
   prompt was 1,388 characters, video 002's was 1,395 — not a truncation
   issue). Most likely cause: real tension in the wording itself between
   "look like Cyanide & Happiness" (whose actual house style is
   fuller-bodied) and "thin stick limbs" — video 001 resolved it one way,
   video 002 resolved it the other way, on identical text. Fixed by adding
   the explicit "references are linework-technique only, not body
   proportions" sentence above. **This may not fully close the gap** — per
   "Worth knowing" below, text-only prompting has a real consistency
   ceiling; if drift shows up again on the next batch, stop iterating on
   wording and switch to attaching a real reference image instead.

## Worth knowing: text-only has a ceiling on consistency

Even a very natural-sounding text description will still have *some* run-to-run variance — that's inherent to text-to-image generation, not a wording problem. If version 8 still shows meaningful drift (or swings back toward being too plain/inconsistent now that the technical language is gone), the more reliable next step is attaching `bst_ref/image.png` itself as a per-shot visual reference wherever the generation tool supports it (Flow's manual "Ingredients" feature, or an image-to-image mode) rather than continuing to refine text alone — a real reference image constrains shape far more tightly than any description can. That's a manual, per-shot step rather than something batchable across all 98 prompts at once, so worth treating as a fallback if text tuning plateaus, not the default.

## Status: LOCKED

This is the final character suffix for video 001 and the channel-wide default going forward — applied to all 46 `character`-tagged shots in `shot_list.md`, `generate/generate_image.md` regenerated with the full 98-shot batch. `testing/version_8/` holds the same 5 shots as version 7 for a direct before/after comparison if you want to spot-check the hair before running the full batch, but it's no longer a blocker — the full `generate_image.md` is ready to use as-is.
