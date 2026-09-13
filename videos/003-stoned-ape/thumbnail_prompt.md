# Video 003 — thumbnail generation prompt

Status: **new.** Built from the locked channel character suffix
(`system/04_shots/character.md`) plus the thumbnail checklist in
`system/08_export/export.md` (≤4 words on-thumbnail text, strong legible
facial emotion, thumbnail/title carry different information, character
prominent and close, dramatic background, warm/cool palette split). Same
generation pipeline as the shot images (Flow) — paste the prompt straight
in, no reference image required.

## Concept (2nd revision — group of characters visibly high, mushrooms scattered around, full title baked in as bold yellow text)

User's direction: several stick-figure characters (not just the solo host)
shown visibly high together — loopy, blissed-out, half-closed eyes, goofy
grins — with mushrooms scattered on the ground and floating/glowing around
them, and the on-thumbnail text should be the video's own locked title
(`title.md`), in bold yellow, not a separate short tagline. Note this
trades away the export checklist's "thumbnail and title shouldn't repeat
the same information" guideline on purpose, per explicit direction — the
title itself becomes the thumbnail's headline rather than a separate
curiosity-gap phrase. The full 9-word title is long for thumbnail text, so
it's set in 3 short stacked lines rather than one long line, sized to stay
legible at small scale.

```
YouTube thumbnail, 16:9, medium wide shot, three stick-figure early-hominin characters sitting and lounging together in a grassland clearing, all visibly high — half-closed heavy-lidded eyes, loose goofy grins, relaxed slouched postures, one leaning back with arms out, one hugging his own knees and giggling, one lying back on the ground. Mushrooms are scattered across the ground all around them, and several small glowing mushroom shapes float gently in the air around the group like a light psychedelic effect. Background is a muted, dusky grassland-at-dusk in the channel's earthy olive-green, ochre, and maroon tones. In bold, thick, heavy-outlined block-letter text stacked across three lines filling the top of the frame, bright yellow fill with a heavy black outline, large and clearly legible even at small size, reads exactly: "ANCIENT HUMANS GOT STONED" / "AND ACCIDENTALLY" / "INVENTED HUMANITY". Art style: flat 2D cartoon webcomic illustration, like Cyanide & Happiness, OverSimplified, or Sam O'Nella Academy — this is a STRICT requirement. ABSOLUTELY NOT photorealistic, NOT a digital painting, NOT concept art, NOT a photograph, no realistic textures or lighting anywhere in the image. Characters: simple stick figures with round flat pale heads, two small dot eyes drawn as heavy-lidded half-closed curves, loose open-mouthed grins, thin uniform-width black-outlined stick limbs and torsos with no muscles or anatomical shading, wearing simple flat-colored brown or leopard-print fabric. Hair: natural messy brown hair, medium length and volume, a bit tousled and uneven like it was never combed, a few strands falling loosely over the forehead, solid flat medium-brown color with no gradient, shading, or highlights. Skin: completely flat, solid, uniform pale color with zero gradient, shading, or highlights anywhere on the face or body. Bold, thick, uniform black outlines on every element in the frame — the characters AND the background must be drawn in the exact same flat, simplified cartoon style, with solid or simply-shaded flat colors, high contrast, punchy and readable at small size. Composition must stay legible when scaled down to a small thumbnail — strong clear silhouettes, no cluttered extra detail beyond what's described. On-screen text: ONLY the exact three lines described above — this is a STRICT requirement — no other captions, taglines, or lettering anywhere else in the frame.
```

## Earlier revision (kept below for reference — solo "enlightenment" concept, superseded by the above)

The title already states the claim outright ("Ancient Humans Got Stoned
and Accidentally Invented Humanity"), so per the checklist's "don't repeat
the same information" rule, the thumbnail's job is pure curiosity, not
restating the thesis. Visual hook: the character crouched low, holding a
single glowing mushroom up close to his face at eye level, inspecting it
with a soft, awe-struck, "enlightened" expression — wide eyes, gentle
open-mouthed wonder, not shock or panic. Warm golden-white light glows
outward from the mushroom itself, lighting his face from below like a
lightbulb-moment. Warm/cool split: the glow around the mushroom and his
face is warm gold/white (the "enlightenment," the payoff), while the
grassland-at-dusk background behind him stays dark, cool, and muted
(indigo-violet and charcoal) — the contrast between the small warm glow
and the big dark unknown around it is the whole image. Unlike the earlier
draft, **this version bakes the on-thumbnail text directly into the
generation prompt** rather than leaving it for a manual editor pass.

## Primary prompt (16:9, 1280x720)

```
YouTube thumbnail, 16:9, close medium shot from the chest up, character crouched low in the foreground, holding a single glowing mushroom up close to his face at eye level with both hands, gazing at it with a soft, awe-struck expression of wonder — eyes wide but gentle, mouth slightly open as if having a realization, not shocked or panicked. Warm golden-white light glows outward from the mushroom, softly lighting his face and hands from below like a lightbulb moment. Behind him, a dark, muted grassland-at-dusk background in deep indigo-violet and charcoal tones, sparse and empty, in quiet contrast to the small warm glow in the foreground. In the upper third of the frame, bold, thick, heavy-outlined block-letter text reads "MIND. BLOWN." stacked on two lines, in bright yellow fill with a heavy black outline, large and clearly legible even at small size. Art style: flat 2D cartoon webcomic illustration, like Cyanide & Happiness, OverSimplified, or Sam O'Nella Academy — this is a STRICT requirement. ABSOLUTELY NOT photorealistic, NOT a digital painting, NOT concept art, NOT a photograph, no realistic textures or lighting anywhere in the image. Character: a simple stick figure with a round flat pale head, two small dot eyes drawn wide with gentle wonder, a softly open mouth, thin uniform-width black-outlined stick limbs and torso with no muscles or anatomical shading, wearing simple flat-colored brown or leopard-print fabric. Hair: natural messy brown hair, medium length and volume, a bit tousled and uneven like it was never combed, a few strands falling loosely over the forehead, solid flat medium-brown color with no gradient, shading, or highlights. Skin: completely flat, solid, uniform pale color with zero gradient, shading, or highlights anywhere on the face or body, except where the warm mushroom glow lights it from below. Bold, thick, uniform black outlines on every element in the frame — the character AND the background must be drawn in the exact same flat, simplified cartoon style, with solid or simply-shaded flat colors, high contrast, punchy and readable at small size. Composition must stay legible when scaled down to a small thumbnail — strong silhouette, no cluttered detail, no invented extra characters. On-screen text: ONLY the exact words "MIND. BLOWN." as described above — this is a STRICT requirement — no other captions, taglines, or lettering anywhere else in the frame.
```

## Alt concept (backup / A-B test) — same enlightenment theme, different pose

Instead of crouching and holding the mushroom up, the character sits
cross-legged in a calm, meditative pose, eyes closed in a peaceful,
serene half-smile, with the glowing mushroom floating/hovering just above
his open upturned palms rather than being held — a slightly more
surreal, "spiritual awakening" read than concept 1's more grounded
"inspecting it closely" pose. Useful if concept 1's read feels too busy or
its text placement doesn't land.

```
YouTube thumbnail, 16:9, close medium shot from the chest up, character sitting cross-legged in a calm meditative pose, eyes gently closed, a peaceful serene half-smile, both hands open and upturned in his lap. A single mushroom glows warmly, hovering just above his open palms, radiating soft golden-white light upward onto his face. Behind him, a dark, muted grassland-at-dusk background in deep indigo-violet and charcoal tones, sparse and empty, in quiet contrast to the small warm glow in the foreground. In the upper third of the frame, bold, thick, heavy-outlined block-letter text reads "MIND. BLOWN." stacked on two lines, in bright yellow fill with a heavy black outline, large and clearly legible even at small size. Art style: flat 2D cartoon webcomic illustration, like Cyanide & Happiness, OverSimplified, or Sam O'Nella Academy — this is a STRICT requirement. ABSOLUTELY NOT photorealistic, NOT a digital painting, NOT concept art, NOT a photograph, no realistic textures or lighting anywhere in the image. Character: a simple stick figure with a round flat pale head, eyes drawn as two closed curved lines, a small peaceful half-smile, thin uniform-width black-outlined stick limbs and torso with no muscles or anatomical shading, wearing simple flat-colored brown or leopard-print fabric. Hair: natural messy brown hair, medium length and volume, a bit tousled and uneven like it was never combed, a few strands falling loosely over the forehead, solid flat medium-brown color with no gradient, shading, or highlights. Skin: completely flat, solid, uniform pale color with zero gradient, shading, or highlights anywhere on the face or body, except where the warm mushroom glow lights it from below. Bold, thick, uniform black outlines on every element in the frame, high contrast, punchy and readable at small size, strong clear silhouette, no invented extra characters. On-screen text: ONLY the exact words "MIND. BLOWN." as described above — this is a STRICT requirement — no other captions, taglines, or lettering anywhere else in the frame.
```

## If the baked-in text doesn't render cleanly

Flow/the image model doesn't always render text perfectly (the same issue
QC'd out 75 shots in the actual video body — see `CLAUDE.md`'s video 003
tracker entry). If "MIND. BLOWN." comes out garbled, misspelled, or oddly
placed after a couple of tries, fall back to the old approach: regenerate
with the on-screen-text sentence removed from the prompt entirely, and add
the text afterward in CapCut/Canva/Photoshop instead — same words, just
added as a clean editable layer rather than trusting the model to render
it. Other short text options if "MIND. BLOWN." doesn't read well:

- **"WAIT, REALLY?"** *(2 words, curiosity-gap, doesn't repeat the title's payoff)*
- **"IT'S TRUE?"** *(2 words, skeptical curiosity)*
- **"ENLIGHTENED?"** *(1 word, most literal callback to this concept's visual)*

## Next

Generate both concepts via the existing pipeline (manual Flow, same as the
shot images), pick the stronger read at actual thumbnail scale (view it
shrunk down, not full-size), add text in the editor, drop the final into
`output/thumbnail.jpg`.
