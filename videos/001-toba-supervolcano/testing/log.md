# Style testing log

Trial-and-error space for dialing in the image style before generating the full 98-shot batch. Not part of the locked pipeline (`../shot_list.md` / `../generate/generate_image.md` stay the source of truth) — once a version's style is confirmed right, that wording gets folded back into `shot_list.md`'s style suffixes and `assets/brain/visuals/flow_workflow.md`.

**Structure:** one folder per version — `version_N/prompts.md` (clean prompts, one per paragraph, nothing else — paste straight into the generator) and `version_N/output/` (drop the generated images there for review). Generation mode: **text-to-image**, not image-to-image/"frame to image" — every prompt here is self-contained (style spelled out in words), so there's no reference image to feed in.

**Workflow:** generate a version's prompts -> save outputs in that version's `output/` -> report back -> if something's off, the style suffix gets fixed, a new `version_N+1/prompts.md` gets written, repeat. When a version comes back right, lock that wording in.

## Pre-versioning test (2026-08-05)

Before this folder structure existed. Shots 001, 002, 005, generated with the *original* style suffixes.

**Result:** character rendered correctly as a stick figure, but the background came out as a photorealistic photo, not a matching cartoon illustration — a cartoon pasted onto a photo, not one cohesive style. Shot 005 also produced an unwanted geological cross-section diagram (labels like "Magma Chamber") because the word "cutaway" in that prompt got misread as "cutaway diagram" rather than the intended filmmaking term.

**Fix applied:** rewrote all three style suffixes (`character`/`diagram`/`environment`) in `shot_list.md` with much more forceful, repeated anti-photorealism language, explicit instruction that the background must match the character's flat cartoon style (not just the character), and named reference styles (Cyanide & Happiness, OverSimplified, Sam O'Nella). Fixed the "cutaway" wording in both prompts that used it.

## Version 1 (2026-08-06)

Re-tests shots 001, 002, 005 with the fixed suffixes, plus two new shots not tested before: 008 (a `diagram`-type shot, first test of that visual category) and 054 (a `character`-type shot with two people interacting, first test of a multi-character scene).

Prompts: `version_1/prompts.md`. Outputs: `version_1/output/`.

**Result: mostly a success, one real issue found.**
- Shots 001, 002 (character): correct — flat cartoon throughout, background now matches the character's style, no more photorealism. Fix confirmed working.
- Shot 054 (character, two-person scene): excellent — comic-panel style, consistent character design, dialogue bubble, clean composition. Best result of the batch.
- Shot 008 (diagram, world map): good — reads as a clean labeled infographic, flat vector style, muted palette.
- Shot 005 (environment, distant eruption): style correct (flat cartoon, not photorealistic), but the model invented content not in the prompt — two characters, a road with cars, an "OBSERVATION POINT" sign, and an unrequested joke speech bubble. Risky for shots meant to set a somber tone before the mythbusting reveal; invented dialogue could clash with the real narration once assembled.

**Fix applied:** added an explicit constraint to the `environment` style suffix (all 26 environment-tagged shots in `shot_list.md`): "Show only what's described above — do not invent extra characters, dialogue, speech bubbles, signage, or text that isn't explicitly part of the prompt." Regenerated `generate/generate_image.md`.

## Version 2 (2026-08-06)

Re-tests all 5 shots from version 1 (001, 002, 005, 008, 054) to confirm the environment-suffix fix didn't disturb the 4 that already worked, plus two new `diagram`-type shots for wider infographic coverage (a minimal stat/icon infographic and a more scientific-illustration-style diagram — both structurally different from the map already tested in version 1). 7 prompts total.

Prompts: `version_2/prompts.md`. Outputs: `version_2/output/`.

**Result: environment fix confirmed, new diagram-palette issue found.**
- Shot 005 (volcano, `environment`): no invented characters/dialogue/signage this time — the anti-invention fix works.
- Shot 001 (beach, `character`): still correct.
- Shot 008 (map, `diagram`): still correct, clean labeled infographic.
- Shot 054 (apprentice/fire, `character`): excellent, matches version 1's best result.
- Shot 015 (stat infographic, `diagram`) — **problem:** invented text not in the prompt ("PEOPLE REACHED" / "INDIVIDUALS," reads like a social-media metric, not a population stat), and rendered in a teal/orange corporate-marketing color scheme completely disconnected from the video's established warm/dark/muted palette. The `diagram` suffix said "muted flat color palette" without anchoring *which* palette, so it drifted to a generic template look.
- Shot 002 (sky-forward, `character`) and shot 020 (DNA tree, `diagram`): **inconclusive** — the saved output files for these looked like exact duplicates of shots 001 and 008 respectively (identical file sizes/content), most likely a save/download mixup in the batch tool rather than a real generation issue. Re-queued in version 3 to get an actual look at them.

**Fix applied:** rewrote the `diagram` suffix (all 26 diagram-tagged shots) to explicitly anchor the color palette to the same warm-browns/muted-oranges/dark-charcoal tones used everywhere else in the video (not teal/corporate blue), and to forbid inventing extra captions/taglines beyond what's explicitly in the prompt. Regenerated `generate/generate_image.md`.

## Version 3 (2026-08-06)

Re-tests shot 002 and shot 020 (inconclusive last round, likely a save mixup) plus shot 008 and shot 015 to confirm the diagram color-palette fix. 4 prompts.

**Extended (2026-08-06):** user confirmed liking version 2's character design specifically — appended 5 more `character`-type shots (006 close-up face, 038 crouching/examining, 059 standing at shoreline, 069 seated craft scene, 095 direct-to-camera) here to see the same unchanged character style across a wider range of poses/scenes. 9 prompts total in `version_3/prompts.md` now. These 5 use the same character suffix as version 2 — no wording changes, purely a broader scene sample.

Prompts: `version_3/prompts.md`. Outputs: `version_3/output/` — 3 of 4 files received (map, stat infographic x2 variants), shot 002 (sky-forward) missing. Not yet analyzed in detail.

**Result:** pending full analysis.

**Note (2026-08-06):** before finishing that analysis, user flagged a preference directly: likes how the character looked in version 1, wants the other visual types (`diagram`/`environment`) to have that same "normal and simple" quality. Looking back at version 2's results with that lens: the volcano (`environment`) had a fair amount of incidental detail (trees, distant buildings), and the stat infographic (`diagram`) had decorative filler shapes (floating dots/triangles) not asked for — the character suffix already says "no muscles or anatomical shading" (deliberately reductive) but the `diagram`/`environment` suffixes never got an equivalent "keep it simple" instruction.

**Fix applied:** added an explicit "keep the composition simple and uncluttered, the same reductive simplicity as the character style — no busy backgrounds/filler detail/decorative shapes" instruction to both the `diagram` and `environment` suffixes (52 shots total). Regenerated `generate/generate_image.md`.

## Version 4 (2026-08-06)

Shot 001 included as a direct-comparison anchor (the character look that's confirmed liked), plus shot 005 (volcano) and shot 015 (stat infographic) re-tested with the new simplicity constraint, plus one new diagram (shot 042, Pinnacle Point/Vleesbaai map) for further coverage. 4 prompts.

Prompts: `version_4/prompts.md`. Outputs: `version_4/output/` — 3 of 4 files received (beach, volcano, stat infographic), map (shot 042) missing. Not yet analyzed in detail.

**Result:** pending full analysis.

## Version 5 (2026-08-06)

Five new shots not tested in any prior version, for broader coverage: shot 064 (shell midden, `environment`), shot 077 (ochre/bone-tool/adhesive object arrangement, `environment`), shot 083 (southern Africa site-network map, `diagram` — different structure than the world map already tested), shot 091 (busy multi-activity cave scene, `character` — a good stress test with several things happening at once), shot 098 (the closing shot, `character` — bookends against shot 001's opening for a direct before/after comparison).

Prompts: `version_5/prompts.md`. Outputs: `version_5/output/` (pending).

**Result:** pending.

## Character consistency fix (2026-08-09)

User saved liked outputs to `testing/best_output/` and flagged directly: the character's hair is a different shape in every generation. Confirmed by comparing the 3 character portraits in that folder side by side — genuinely 3 different hairstyles (big loopy scribbles / long side-swept strands / short spiky tufts) from the exact same prompt text. Root cause: the hair phrase ("messy scribbled brown hair drawn as a few loose lines") was descriptive but not prescriptive — nothing constrained shape, count, or position, so the model improvised differently each time. Also caught a minor drift: one output had a faint shading gradient on the face, breaking the "completely flat, no gradients" rule.

Full writeup and the new locked wording: `assets/brain/visuals/character_design.md`. Short version: replaced the vague hair phrase with an exact, countable, positional description (5-6 specific tufts, exact position rule, exact color rule, zero ambiguity) and reinforced the flat-skin-color rule explicitly. Applied to all 46 `character`-tagged shots in `shot_list.md`, regenerated `generate/generate_image.md`.

(Note: the volcano shot also saved into `best_output/` is the original pre-fix test image with the invented characters/dialogue/signage — read as "liked for the rendering quality," not as walking back that fix; the anti-invention constraint on `environment` shots stays as-is.)

## Version 6 (2026-08-09)

5 close-up/face-forward `character` shots specifically chosen to stress-test hair consistency under the new locked description (hair reads most clearly in close-ups) — shot 001 again as the running baseline anchor, plus 4 new close-up face shots (010, 017, 034, 052) never tested before.

Prompts: `version_6/prompts.md`. Outputs: `version_6/output/` (pending).

**Result: hairstyle direction was wrong.** User confirmed they didn't like the short-spiky-tufts look — the actually-preferred look is `best_output/image.png`'s (voluminous, loose, wavy loops, strands hanging over the forehead), which the previous fix had specifically moved *away* from. User saved that exact image plus its generation prompt into `testing/best_output/bst_ref/` (`image.png` + `ref.txt`) to remove any ambiguity about which look to lock onto.

## Character consistency fix, corrected (2026-08-09)

Rewrote the hair description to precisely match `bst_ref/image.png` instead: a voluminous, messy mop of loose, wavy, looping scribble strands (continuous loops/curls, not short spiky points), several strands hanging over the forehead/temples without covering the eyes. Full writeup: `assets/brain/visuals/character_design.md` (includes a note on this being the wrong-direction lesson, and a fallback recommendation to attach `bst_ref/image.png` as a direct visual reference per-shot if text tuning alone plateaus). Applied to all 46 `character`-tagged shots in `shot_list.md`, regenerated `generate/generate_image.md`.

## Version 7 (2026-08-09)

5 new `character` shots (different scenes than version 6) to confirm the corrected hairstyle: shot 041 (hands holding stone), shot 047 (tending fire), shot 056 (apprentice's hands), shot 062 (standing at shoreline), shot 089 (facing camera, summarizing).

Prompts: `version_7/prompts.md`. Outputs: `version_7/output/`.

**Result: hairstyle direction wrong again, opposite problem this time.** 3 of 5 outputs reviewed (shots 041, 047, 056). The "continuous loops and curls" wording got taken literally — the model drew dense, tight spiral ringlets across the whole head, much more ornate/curly than the loose, natural mess in `bst_ref/image.png`. User's feedback: *"you are doing too much with the hair, keep it natural like how it is in the best image, don't try to make it too detailed and stuff, just natural."* Root cause: the wording didn't just describe the look, it prescribed drawing technique ("drawn as continuous loops and curls") — the model rendered that as an instruction to draw actual spirals, not as "loosely wavy."

## Character consistency fix, third pass — simplified to natural (2026-08-09)

Dropped the technical drawing-technique language ("voluminous," "continuous loops and curls," "unkempt tousled shape extending outward/upward") entirely. New wording just states the natural qualities — medium length/volume, tousled/uneven, a few strands over the forehead, flat brown color — without dictating how each strand should be drawn. Full writeup: `assets/brain/visuals/character_design.md`. Applied to all 46 `character`-tagged shots in `shot_list.md`, regenerated `generate/generate_image.md`.

## Version 8 (2026-08-09)

Same 5 shots as version 7 (041, 047, 056, 062, 089) for a direct apples-to-apples comparison against the ringlet-curl problem.

Prompts: `version_8/prompts.md`. Outputs: `version_8/output/` (pending).

**Result:** pending.
