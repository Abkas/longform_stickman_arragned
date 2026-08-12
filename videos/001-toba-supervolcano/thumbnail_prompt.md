# Video 001 — thumbnail generation prompt

Status: **new.** Built from the locked channel character suffix (`assets/brain/visuals/character_design.md`) + the thumbnail style notes in the Ink Explainer deep-dive (`assets/references/channel_reports/2026-08-04_inkexplainer96_deep_dive.md`: character prominent and close, dramatic painted background, 1-3 word bold text alternating white/yellow, blue-grey-for-danger vs warm-orange-for-safe palette). Same generation pipeline as the shot images (Gemini/Flow) — paste the prompt straight in, no reference image required.

## Concept

Thumbnails in this niche read at a glance: dramatic background = the crisis, character's expression = the hook's emotional angle. This video's hook is myth-busting ("everyone thinks it nearly ended humanity — it didn't"), so the character should read as **calm/unbothered**, not terrified, while the background sells the apocalypse. That contrast — chaos behind him, completely fine in front — *is* the thumbnail's job; it should make someone think "wait, why does he look okay?"

## Primary prompt (16:9, 1280x720)

```
YouTube thumbnail, 16:9, close medium shot from the chest up, character positioned right-of-center facing camera with a calm, faintly smug, unbothered half-smile — arms loosely crossed, completely relaxed posture. Behind him, a massive volcanic eruption fills the rest of the frame: a huge ash column and glowing orange debris rising into a dark, ash-choked sky, the whole scene lit in dramatic deep-orange and charcoal tones. Leave the upper-left third of the frame relatively clean sky/ash-cloud for bold text to be added afterward. Art style: flat 2D cartoon webcomic illustration, like Cyanide & Happiness, OverSimplified, or Sam O'Nella Academy — this is a STRICT requirement. ABSOLUTELY NOT photorealistic, NOT a digital painting, NOT concept art, NOT a photograph, no realistic textures or lighting anywhere in the image. Character: a simple stick figure with a round flat pale head, two small dot eyes, a short line mouth curved into a slight confident smirk, thin uniform-width black-outlined stick limbs and torso with no muscles or anatomical shading, wearing simple flat-colored brown or leopard-print fabric. Hair: natural messy brown hair, medium length and volume, a bit tousled and uneven like it was never combed, a few strands falling loosely over the forehead, solid flat medium-brown color with no gradient, shading, or highlights. Skin: completely flat, solid, uniform pale color with zero gradient, shading, or highlights anywhere on the face or body. Bold, thick, uniform black outlines on every element in the frame — the character AND the background must be drawn in the exact same flat, simplified cartoon style, with solid or simply-shaded flat colors, high contrast, punchy and readable at small size. Composition must stay legible when scaled down to a small thumbnail — strong silhouette, no cluttered detail, no invented extra characters, no text or speech bubbles baked into the image.
```

## Alt concept (backup / A-B test)

Swaps the "unbothered in front of the eruption" read for a more literal callback to the video's actual thesis (mastery, not survival) — character mid-action instead of posed:

```
YouTube thumbnail, 16:9, close medium shot, character crouched at a small glowing campfire in the foreground, confidently holding up a freshly heat-treated stone blade toward camera with a satisfied expression, warm orange firelight lighting his face from below. Behind him, out of focus but unmistakable, a massive volcanic eruption rages against a dark ash-filled sky. Leave the upper third relatively clean for bold text to be added afterward. Art style: flat 2D cartoon webcomic illustration, like Cyanide & Happiness, OverSimplified, or Sam O'Nella Academy — this is a STRICT requirement. ABSOLUTELY NOT photorealistic, NOT a digital painting, NOT concept art, NOT a photograph, no realistic textures or lighting anywhere in the image. Character: a simple stick figure with a round flat pale head, two small dot eyes, a short line mouth, thin uniform-width black-outlined stick limbs and torso with no muscles or anatomical shading, wearing simple flat-colored brown or leopard-print fabric. Hair: natural messy brown hair, medium length and volume, a bit tousled and uneven like it was never combed, a few strands falling loosely over the forehead, solid flat medium-brown color with no gradient, shading, or highlights. Skin: completely flat, solid, uniform pale color with zero gradient, shading, or highlights anywhere on the face or body. Bold, thick, uniform black outlines on every element in the frame, high contrast, punchy and readable at small size, strong clear silhouette, no invented extra characters, no text or speech bubbles baked into the image.
```

## Concept 3 — shocked reaction, hair singed (used for the "WORST VOLCANO IN HISTORY" text)

Different emotional read than concepts 1-2: instead of "unbothered," character reacts in visible shock/horror — mouth open, wide eyes, a few strands of hair catching a small flame at the tips. Matches a more literal, high-drama thumbnail read (crisis-forward rather than irony-forward) paired with the "WORST VOLCANO IN HISTORY / SURVIVED" text already rendered onto `output/thumbnail.jpg`.

```
YouTube thumbnail, 16:9, close medium shot from the chest up, character positioned right-of-center facing camera in visible shock and horror — eyes wide open, eyebrows raised high, mouth open in a startled gasp, both hands slightly raised near shoulder height in a flinching reaction. A few strands of his hair have caught a small flame at the very tips, with a couple of small flat-style flame icons and a few embers/sparks near his head — the fire is a minor, localized detail, not covering his whole head. Behind him, a massive volcanic eruption fills the rest of the frame: a huge ash column and glowing orange-red debris rising into a dark, ash-choked sky, the whole scene lit in dramatic deep-orange and charcoal tones. Leave the upper-left third of the frame relatively clean sky/ash-cloud for bold text to be added afterward. Art style: flat 2D cartoon webcomic illustration, like Cyanide & Happiness, OverSimplified, or Sam O'Nella Academy — this is a STRICT requirement. ABSOLUTELY NOT photorealistic, NOT a digital painting, NOT concept art, NOT a photograph, no realistic textures or lighting anywhere in the image. Character: a simple stick figure with a round flat pale head, two small dot eyes drawn wide open in shock, an open oval mouth, thin uniform-width black-outlined stick limbs and torso with no muscles or anatomical shading, wearing simple flat-colored brown or leopard-print fabric. Hair: natural messy brown hair, medium length and volume, a bit tousled and uneven like it was never combed, a few strands falling loosely over the forehead, solid flat medium-brown color with no gradient, shading, or highlights, except the singed tips described above which are small flat orange/yellow flame shapes. Skin: completely flat, solid, uniform pale color with zero gradient, shading, or highlights anywhere on the face or body. Bold, thick, uniform black outlines on every element in the frame — the character AND the background must be drawn in the exact same flat, simplified cartoon style, with solid or simply-shaded flat colors, high contrast, punchy and readable at small size. Composition must stay legible when scaled down to a small thumbnail — strong silhouette, no cluttered detail, no invented extra characters, no text or speech bubbles baked into the image.
```

Text to add after (same treatment as the current `output/thumbnail.jpg` — big, bold, white + yellow, heavy black outline, upper-left):

- **"WORST VOLCANO"** (white) / **"IN HISTORY"** (white) / **"SURVIVED"** (huge, yellow) — the exact copy already in use, reads well against a shocked expression too since the text states the threat and the payoff word still lands as the twist.

## Text overlay (add after generation, in CapCut/Canva/Photoshop — don't rely on the image model to render clean text)

Per the channel's real pattern (1-3 words, bold heavy-outline sans-serif, alternating white/yellow fill):

- **"STILL HERE"** *(yellow, leans into the myth-busted punchline)*
- **"THEY SURVIVED?"** *(white, question form matches the locked video title)*
- **"NOT EXTINCT"** *(yellow, most literal callback to the myth)*

Place in the clean upper-left space the prompt already reserves. Keep it to one of these three, not a stacked multi-line block — legibility at mobile thumbnail size (roughly 120×67px in the suggested-videos rail) is the whole point.

## Next

Generate both concepts via the existing pipeline (`pipeline/generate_visuals.py` or manual Flow), pick the stronger read at actual thumbnail scale (view it shrunk down, not full-size), then add text in the editor and drop the final into `output/`.
