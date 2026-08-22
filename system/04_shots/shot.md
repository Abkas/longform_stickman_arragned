# Visuals — image/video generation workflow

Researched 2026-08-04, revised 2026-08-05. Covers how to turn a locked `shot_list.md` into actual images/clips for a video. I don't have API/tool access to Flow, browser extensions, or a screen to operate any of this myself — everything below is prep for you to run.

## Validation: this is confirmed to be how the actual copycat cluster is produced

Researched how Ink Explainer-style channels are actually made, not just guessed. Two different production tiers exist in this space, and they're not interchangeable:

- **The AI-stickman channel cluster (Ink Explainer, Deep Epoch, Before Civilization, Stick Plot, Brook Explains, Mack Explains, Before The Clock — see `system/shared/references/channel_reports/2026-08-04_niche_landscape.md`)**: this exact genre is documented as a real, currently-exploding 2026 niche built on a specific three-tool AI workflow — **Claude AI for scripting, ElevenLabs for voiceover, and Flow AI for visuals.** That is precisely the pipeline already locked for this channel (`CLAUDE.md`) — not a guess, but a match to the actual documented production method for this exact channel cluster. One real warning that came with it: YouTube has started demonetizing mass-produced, low-effort AI content — quality and genuine human oversight at each step (the sourcing rigor already locked in `system/03_script/structure.md`, the tone work in `system/03_script/persona.md`) are what keep a channel like this monetizable, not just running the pipeline on autopilot.
- **OverSimplified and Sam O'Nella Academy — different production tier, tone-only borrowing.** OverSimplified is hand-animated in Adobe After Effects with assets built in Photoshop — a real animator's pipeline, not AI-generated. Sam O'Nella Academy is drawn by hand in MS Paint — deliberately lo-fi, fully manual. Both are why their *writing/tone* (the OverSimplified/Sam O'Nella blend in `system/03_script/persona.md`) is worth borrowing, but their *production method* isn't something an AI pipeline replicates — we're taking their comedic technique, not their tooling.

## Shot density v1: one image per sentence (locked 2026-08-05, superseded 2026-08-13 — see v2 below)

Researched actual practice for this specific genre (AI-generated faceless explainer channels), not generic film-editing advice. Two data points:

- Generic YouTube editing research suggests 8-12 cuts/minute for engaged tutorial-style content, with variation (fast micro-cuts mixed with longer holds) rather than a flat rhythm — useful context, but that's a different genre from a narrated documentary-style explainer.
- **The actual common default for AI-generated faceless-video tools is one image per sentence** — several script-to-video tools in this space generate a matching image prompt per sentence by default, splitting at natural sentence/paragraph boundaries so every scene is an independently swappable visual unit.

**Method used for `shot_list.md`:** split the locked script into its real sentences programmatically, then merge any sentence under 8 words forward into the next one (so no shot is an unusably short fragment, e.g. "Global population." alone). This produced **98 shots** for video 001's ~2,451-word script (111 for video 002's ~2,561-word script) — roughly one shot per 23 words.

**Status: this rule produced videos 001 and 002. It's kept here as history and both those videos' own `shot_list.md`s stay built this way — don't retroactively rebuild them.** After watching video 002's actual result, the user's direct feedback was that shot planning at this density still felt thin and the visuals weren't good enough — see v2 below, which replaces this rule for **video 003 onward**.

## Shot density v2: maximum density + itemized lists (locked 2026-08-13, video 003 onward)

Two compounding changes, both aimed at "the video needs way more, way more specific visuals," not just more shots for their own sake:

**1. Split at clause boundaries, not just sentence boundaries.** Instead of
one shot per sentence (~23 words/shot at v1's density), split additionally
at commas, coordinating conjunctions (and/but/or/so), subordinating
conjunctions (because/since/when/while/although), and semicolons — aim for
roughly **8-12 words per shot as the new baseline**, close to one shot per
distinct idea/phrase rather than per sentence. For a script the same length
as video 002's (~2,561 words), this lands around **250-350+ shots** instead
of 111 — expect the total shot count and generation cost/time to roughly
triple. This is a deliberate, confirmed trade-off (2026-08-13): the user
chose "maximum" density over a more moderate ~2x increase, explicitly
accepting the cost/time hit for a visually richer result.

**2. Itemized-list override — takes priority over everything else,
including the merge-forward rule below.** When a clause or sentence
enumerates 2+ distinct things — a comma-list, "X, Y, or Z", "X, Y, and Z",
anything that names multiple concrete items, actions, or examples in a
row — give **each item its own shot**, regardless of word count, even a
single word. Example: narration "societies turned to hoarding, trading, or
raiding" becomes 3 shots, one per item, not one shot covering the whole
clause. Each item-shot:
- Gets its own `- Duration: ~1.5-2.5s` (a new short "flash" tier, distinct
  from the normal 5-10s narrative shot) — several of these back-to-back
  should read as one quick-cut burst, not three slow holds.
- Gets a **genuinely distinct visual treatment** per item (a different
  icon, a different character action, a different concrete example) —
  never the same generic image repeated with a different label, which
  would defeat the entire point of calling these out individually.
- Classify each item-shot normally (`character`/`diagram`/`environment`)
  based on what that specific item actually depicts — there's no new
  `- Visual:` type for this, just apply the existing three per-item.
- No new `shot_list.md` field is needed for this — the short
  `~1.5-2.5s` duration on several consecutive shots is itself the signal
  that they're a burst, and `assemble.py`/`generate_visuals.py`'s existing
  parsers don't need to know anything changed.

**3. Revised merge-forward safety net.** v1's "merge anything under 8 words
forward" rule is too aggressive for v2's target density — at ~8-12
words/shot baseline, plenty of legitimate, meaningful shots will
legitimately be short. Lower the merge threshold to **under 4 words** for
*ordinary* (non-list) fragments — only merge genuinely unshowable stray
fragments (a lone transitional word, a dangling conjunction), not every
short-but-meaningful clause. **List items from rule 2 are exempt from this
merge rule entirely** — a one-word item shot stays its own shot.

**4. Raise the `Type: video` ratio too.** Video 002 shipped with only 5 of
111 shots (4.5%) as real motion — everything else was a still with a
pan/zoom applied at assembly. That read as a slideshow despite the Ken
Burns treatment (see `system/07_assembly/assembly.md`'s "Known limitation:
motion ratio"). At v2's higher shot count, don't just scale the *count* of
video shots proportionally and call it done — actively look for beats that
need real movement (a gesture landing, a reaction, a head turn) and mark
them `Type: video` more liberally than v1 did. This is a direction, not a
hard percentage — flag candidates generously in the build report rather
than defaulting to `image` out of caution.

**Do this programmatically, not by hand** — build the shot skeleton
(clause/item text + word count + duration) with a script first, verify the
total duration and word-for-word coverage matches `script.md` exactly,
*then* write prompts. Hand-computing durations across hundreds of shots is
even more error-prone than it was at v1's ~100-shot scale — always verify
the final shot list's concatenated narration matches the script word-for-word
before treating it as locked.

**Given the much larger batch size this produces, the post-batch
verification process in "Post-batch verification" below matters even more
than it did at v1's scale** — the queue-desync bug that corrupted 47% of
video 002's 111-shot batch has more room to cascade across 300+ shots, not
less. Generate in smaller chunks, hash-check for duplicates immediately,
don't trust a finished batch by default.

## Pacing fix: cap the long end too (lesson from watching video 001's actual render, locked 2026-08-12; word-count references below predate v2's density change — see note at the end of this section)

The rule above only protects against shots being too *short* (merge sub-8-word
fragments forward). Watching video 001's finished render surfaced the
opposite, uncaught problem: some sentences ran long, got mapped to **one
static image held on screen for an unusually long stretch**, and long runs of
that made whole sections of the video feel still/frozen even though the
narration kept moving. Three fixes, apply to every future `shot_list.md`
(including video 002 onward):

1. **Cap max shot duration around ~10-12 seconds.** If a sentence (or a
   fragment merged forward per the rule above) would run longer than that at
   the script's target WPM, split it into two shots at a natural
   clause/comma break instead of leaving it as one. Each half keeps its own
   `- Duration:` — and, critically, gets a genuinely different camera
   angle/framing/action in its `- Prompt:`, not a near-duplicate of the same
   static scene. Two visually distinct beats, not one frozen image stretched
   across double the time.
2. **Every `character`-type shot's `- Prompt:` needs a specific physical
   action or posture, not just a scene description.** "A stick figure
   standing in a cave" is the failure mode to avoid — write "gesturing
   toward the horizon," "crouched over a small fire, adjusting a stick,"
   "mid-stride, glancing back over one shoulder," etc. **Rotate the
   action/posture across consecutive character shots** so the same held pose
   doesn't repeat back-to-back — a run of similar static poses reads as
   "stillness" to a viewer even when the individual images are technically
   different.
3. **Short (<8-word) character beats: prefer promoting to `- Type: video`
   over silently merging into stillness.** The merge-forward rule above still
   applies by default to `diagram`/`environment` shots, where a static hold
   reads fine. But for a `character`-type shot specifically, a short punchy
   line is often exactly the moment that benefits from a brief (~8s) dynamic
   clip — a head turn, a flinch, a gesture landing — instead of getting
   quietly absorbed into a longer neighboring image and losing its own
   beat entirely. When a short character-type shot's narration content
   implies physical motion or a reaction, mark it `- Type: video` and note
   it as such in the final report, rather than defaulting to `image` and
   merging it away by default.

Net effect: fewer long static holds, more shot-to-shot visual variation even
within a single scene/character, and short character beats get their own
dynamic moment instead of disappearing into a neighboring shot's stillness.

**Reconciling with v2 (video 003 onward):** rules 1 and 2 above still apply
unchanged — cap long shots, rotate character poses. Rule 3's "<8-word"
threshold and the opening paragraph's "sub-8-word" merge reference are both
v1 numbers; under v2, the ordinary merge threshold is 4 words (not 8), and
list items are exempt from merging entirely regardless of length — see
v2's "Revised merge-forward safety net" and "Itemized-list override" above.
Rule 3's actual intent (a short punchy character beat deserves `Type: video`
rather than getting merged into stillness) still holds — just apply it
against v2's 4-word threshold, not the original 8.

## Primary method: fully self-contained prompts, no reference image required (revised 2026-08-05)

The original plan was to build one character reference image + one style reference image, attach them as "ingredients"/reference images to every generation, and keep the prompts themselves bare (scene/action only, no character description). That plan was dropped after research showed it doesn't hold up across batch tools: some Chrome extensions for Flow (FlowBatch in particular) only support **one global reference image applied to the whole batch**, with no per-prompt control. Since a large fraction of `shot_list.md`'s 98 shots are pure diagrams/maps/quote-cards/environment shots with no character in them at all, attaching a character reference for a whole batch risks forcing that character into shots that shouldn't have one.

**The fix: make every prompt fully self-describing instead.** No reference image needed, no dependency on how any particular batch tool handles attached references, works identically whether you're pasting into Flow by hand, a batch extension, or the paid API script.

Every shot in `shot_list.md` has a `- Visual:` tag — `character`, `diagram`, or `environment` — and its `- Prompt:` line has the matching fixed style-suffix text appended directly. The three suffixes (reused verbatim on every shot of that type, across every video):

**Character** (a shot featuring the recurring host): **see `character.md`'s "Locked character suffix" section (same folder, `system/04_shots/`) for the current, exact wording — that file is the single source of truth for this text, don't copy it here again.** (This section used to quote the suffix inline, but that copy went stale after the character-design hair fix and started contradicting the real locked version — removed 2026-08-12 so there's only ever one place this text can drift out of date.) The suffix wraps the same art-style framing used by the `diagram`/`environment` suffixes below (flat 2D cartoon webcomic illustration, strict non-photorealistic requirement) around the locked character description.

**Diagram** (maps, timelines, quote cards, DNA trees, icon montages, on-screen text overlays — no character, no painted scene):
> Art style: flat 2D vector infographic illustration, like a clean explainer-video graphic — this is a STRICT requirement. ABSOLUTELY NOT photorealistic, NOT a painting, NOT 3D rendered, NOT a photograph. Simple flat 2D icons and shapes only, thin sans-serif on-screen text labels where needed, muted flat color palette, bold clean outlines, no gradients, no realistic textures or lighting, no painterly brushwork. On-screen text: ONLY the specific labels described in the prompt (site names, numbers, dates) — this is a STRICT requirement, repeated because it gets violated otherwise: do not add extra captions, taglines, marketing-style phrases, headers, citations, or any other label that isn't explicitly spelled out in the prompt text, no matter how plausible or on-topic it seems. Keep the composition simple and uncluttered, the same reductive simplicity as the character style — only the specific icons/shapes/labels described, no decorative filler shapes added just for visual interest.

**Environment** (object/landscape/still-life shots with no character and no infographic data — a campfire, a shell midden, an eggshell close-up, a distant eruption):
> Art style: flat 2D cartoon webcomic illustration, like Cyanide & Happiness, OverSimplified, or Sam O'Nella Academy — this is a STRICT requirement. ABSOLUTELY NOT photorealistic, NOT a digital painting, NOT concept art, NOT a photograph, no realistic textures or lighting anywhere in the image. Bold, thick, uniform black outlines on every object and shape, flat or simply-shaded solid colors, simplified geometric forms rather than realistic detail. Muted, moody color palette matching a dark documentary tone, but rendered entirely as a flat cartoon illustration — no gradients, no soft painterly brushwork, no photorealistic lighting or texture. Keep the composition simple and uncluttered, the same reductive simplicity as the character style — only the few main shapes needed to read the scene, no busy backgrounds, no extra scenery or filler detail beyond what's described. Show ONLY what's described above — this is a STRICT requirement, repeated because it gets violated otherwise: do not invent extra characters, dialogue, speech bubbles, sound-effect text, signage, captions, or any other text that isn't explicitly part of the prompt.

**Note (fixed 2026-08-12):** the two blocks above previously omitted the "keep composition simple," "don't invent extra content" clauses — video 001's actual generated shots used a longer version of both suffixes than what was documented here, a drift caught by `shot-list-builder` while building video 002's shot list. Backfilled the generically-useful clauses (both apply to every video); left out video 001's own specific warm/cold color-palette sentence, since that was tuned to Toba's own visual mood, not a universal rule. **Each video should define its own locked color-palette line** (matching that video's tone/mood, the same way video 001 did) and append it into these suffixes when building that video's `shot_list.md` — don't reuse Toba's warm-browns/charcoal palette wholesale for an unrelated video.

These three blocks match the established visual style from `system/shared/references/images/inkexplainer96_*` and the production notes in `system/03_script/structure.md`. **Apply this same classify-and-append method to every future video** — tag each shot's `- Visual:` type when writing `shot_list.md`, append the matching suffix to its prompt, done. No character/style reference image needs to be built before generating.

**Lesson learned from the first real test batch (2026-08-05):** the first version of these suffixes was too weak — it named the style once ("stickman-style," "flat cel-shaded") but didn't repeat/enforce it hard enough, and the model defaulted to photorealistic digital painting for backgrounds even when the character itself came out correctly as a stick figure (a cartoon character pasted onto a photo-real background, not a cohesive illustration). Two fixes: (1) the suffix now explicitly demands the *background* match the *same* flat cartoon style as the character, not just the character on its own, and (2) it names concrete reference styles (Cyanide & Happiness, OverSimplified, Sam O'Nella) and repeats "ABSOLUTELY NOT photorealistic" rather than a single soft mention — image models need forceful, repeated, unambiguous style language, a single stylistic adjective buried in a longer prompt gets ignored. Also caught: the word "cutaway" in a prompt (meant as a filmmaking term, "cutaway shot") got misread as "cutaway diagram" and produced an unwanted geological cross-section with labels — avoid words with a strong competing meaning in visual-generation contexts; watch for this in future shot lists.

**Always test a small batch (3-5 shots spanning all three `- Visual:` types) before generating the full shot list**, and actually look at the results — this is exactly how the above bug was caught, before spending the effort/cost generating all 98.

## Optional: reference-image / "Ingredients" approach (secondary, not required)

Flow's own manual UI has a feature called **Ingredients to Video** — attach up to 3 reference images (character/object/style) to a single generation and it maintains that subject's appearance across shots. This is a real, documented feature and can still be useful:

- As a **personal visual-QA anchor** — build a character reference image once (manually in Flow, or via `system/05_visuals/generate_character_reference.py`) and eyeball generated shots against it by hand, without feeding it into every generation.
- For **single-shot manual generation** in Flow's own UI, where you can attach it per-shot with full control (unlike bulk-batch tools) if you want extra consistency insurance on top of the self-contained prompt text.

Not required for the primary workflow above. If built, save to `system/05_visuals/character_reference/host_reference.png` / `system/05_visuals/character_reference/style_reference.png`, generated once per channel, reused (optionally) across videos.

## Confirmed 2026-08-05: free vs. paid is about *which door*, not which model

Ran `generate_character_reference.py` against a real API key with no billing enabled. Result: `429 RESOURCE_EXHAUSTED`, `limit: 0` for `generativelanguage.googleapis.com/generate_content_free_tier_requests` on `gemini-3.1-flash-image`. Confirmed directly from Google's own API, not a search result — **the developer API has a hard $0 free tier for image generation on this project, full stop.**

But the same underlying model is free through Google's *consumer* surfaces — Flow's own web app (`flow.google.com`), the Gemini app, and AI Studio's interactive playground all give free daily quotas (Flow: sign in with any Google account, no billing; Gemini app: ~20 free images/day; AI Studio playground: ~50/day). Same model ("Nano Banana"/Gemini image family), different access path — the API is metered/billed, the interactive apps are free with a daily cap. **Given cost is a real concern here, the manual Flow path is now the recommended default, not just a fallback** — reserve the API script (below) for later if/when paid full automation is worth it.

## Generating the shots: the free path (recommended for now)

**Option A — one at a time, directly in Flow:**
1. Go to `flow.google.com`, sign in with a Google account — no billing needed.
2. Copy a shot's full `- Prompt:` line straight from `shot_list.md` (already self-contained, includes the style suffix) into Flow's text-to-image.
3. Generate, compare against the established style thumbnails (`system/shared/references/images/`) for consistency, regenerate if it drifts.
4. Save the output into `videos/NNN-<slug>/generate/generated/images/`, named
   `{shot_num}_{brief-slug-of-the-prompt}.ext` (not zero-padded) — e.g.
   `4_standing-in-front-of-a-vending-machine.jpeg` — matching the real
   convention `assemble.py` looks for.

**Option B — batch, via a browser extension (faster for this many shots):** third-party Chrome extensions (FlowBatch and similar — see Chrome Web Store) sit inside your own already-logged-in Flow tab and process a whole list of prompts automatically. Format confirmed: paste prompts **one per line**, no numbering or extra formatting, into the extension's side panel; it queues and generates each one, with bulk download. Since every prompt is now self-contained (no shared reference-image state needed), any batch tool works regardless of how it handles reference images — that whole class of problem no longer applies. Open `generate/generate_image.md`, copy the whole file, paste into the extension.

**Pacing around the free daily cap:** 98 generations is more than most free daily quotas allow in one sitting — expect to spread it across several days, or check if the batch extension's own free tier (often ~10/day without a license) is more limiting than Flow's own quota.

## Post-batch verification: never trust a finished batch by default (locked 2026-08-13, after video 002's real error rate)

Video 002's 111-shot batch (generated via a browser batch extension) was
audited shot-by-shot against its own `shot_list.md` prompts after the fact
and came back **47% wrong** — 52 of 111 files didn't show what their own
prompt described. Root cause: the extension lost sync with its own prompt
queue on slow generations, saved a duplicate instead of the new result, then
silently dropped the next prompt in line — cascading every shot after it
down by one until another duplicate/skip cancelled the drift back out. This
was not a rare edge case; it happened repeatedly across the batch, at
different points, for runs of 14+ shots at a time. A batch extension
finishing without errors is not evidence it produced the right images —
treat "the batch completed" and "the batch is correct" as two separate,
unrelated facts going forward. Four standing rules for every future video's
batch generation, not just a one-off catch:

1. **A finished batch is unverified until checked, full stop.** Build a
   post-batch verification pass into the plan for every video from the
   start, not as an afterthought — at minimum a spot-check across the
   video's length (beginning/middle/end, all three `- Visual:` types), and
   a full shot-by-shot check for anything this size before treating the
   images as ready for assembly.
2. **Check for exact duplicates programmatically, before any visual
   review.** Every duplicate found in video 002's audit was byte-identical.
   A simple hash comparison across `generate/generated/images/*` (e.g.
   `md5sum generate/generated/images/* | sort | uniq -c -w32 | sort -rn`)
   catches those instantly with zero manual/vision effort — run this first,
   every time, before spending any visual-review effort.
3. **Generate in smaller chunks (roughly 15-20 shots at a time) rather than
   the full shot count in one sitting**, when using a batch extension. A
   long single-session batch is exactly the condition that gives a
   queue-desync bug room to cascade for many shots before it happens to
   self-correct — smaller chunks make it cheap to spot-check right after
   each run and catch drift before it compounds across the whole video.
4. **Reserve the batch extension for lower-stakes `diagram`/`environment`
   shots.** Generate `character`-type shots one at a time in Flow's own UI
   (Option A above) instead, where each result can be eyeballed and
   accepted/rejected individually before moving to the next — the
   consistency stakes on the recurring host character are higher than on a
   one-off diagram, and video 002's invented-dialogue defect concentrated
   almost entirely in character shots (see `character.md`'s "Video 002
   drift" section for that specific fix).

## Per-video `generate/` folder (locked 2026-08-05 — do this for every future video)

Once a video's `shot_list.md` is locked (including `- Visual:` tags and style suffixes on every prompt), produce two plain export files in a `generate/` subfolder next to it — `videos/NNN-<slug>/generate/`:

- **`generate_image.md`** — every shot's full `- Prompt:` line (self-contained, suffix included), one per line, **separated by a blank line (paragraph break) between each prompt** (fixed 2026-08-12 — video 002's first build had every prompt packed back-to-back with no separation, hard to scan/spot-check by eye). Nothing else in the file (no numbering, no narration/duration). Extract this programmatically from `shot_list.md` (don't hand-copy — risk of transcription drift). This is what gets pasted into Flow or a batch extension — the blank lines don't break the "one per line" paste requirement below, since line-based batch parsers skip empty lines rather than treating them as an empty prompt.
- **`generate_voice.md`** — the locked script's full narration text, audio tags converted from `*[tag]*` to plain `[tag]` (ElevenLabs v3 reads bracket tags directly, see `system/06_voice/voice.md`), paragraph breaks kept, no other markdown/metadata. Extract programmatically from `script.md` the same way. This is what gets pasted into ElevenLabs.

Regenerate both whenever `shot_list.md` or `script.md` changes — treat them as build artifacts, not hand-maintained files.

## Alternative: the paid/automated path

`system/05_visuals/generate_visuals.py`: reads `shot_list.md` directly (prompts are already self-contained, so it no longer needs a reference image to produce on-style results, though it can still optionally attach one if `system/05_visuals/character_reference/host_reference.png` exists), calls the Gemini API, saves straight into `generate/generated/images/` (fixed 2026-08-13 — it used to write to a `visuals/` folder that never matched the real convention, a latent bug never caught since video 001 was generated manually, not through this script). This is not Flow itself — Flow the consumer app wraps the same underlying Veo/Imagen models, which are also available directly through the official Gemini API — but this route is billed with no free tier, unlike Flow's own web app. **Both images and short video clips are supported**, per-shot, via the same script, if/when paid automation is worth it (e.g. producing many videos at volume, where manual generation in Flow doesn't scale).

Google Flow's own consumer app doesn't have a clean official automation API (third-party browser extensions exist but are unofficial). The models underneath it — Veo 3.1 (video) and the Gemini/Imagen image models — **are** available through the official Gemini API.

**Setup (one-time):**
1. Get a Gemini API key from Google AI Studio (`ai.google.dev`) — note this is **paid, no free tier**, not the free consumer Flow app, so billing needs to be set up. See "Real cost" below for actual per-image/per-video numbers — small for one video, but not zero.
2. Copy `.env.example` (repo root) to `.env` and fill in `GEMINI_API_KEY=...` — both scripts load `.env` automatically via `python-dotenv`. `.env` is gitignored, never committed. (An `export GEMINI_API_KEY="..."` in your shell also works if preferred, but only lasts that terminal session — `.env` persists.)
3. `pip install -r system/05_visuals/requirements.txt`
4. A character reference image is now **optional** for this script (see "Primary method" above) — if `system/05_visuals/character_reference/host_reference.png` doesn't exist, the script just skips attaching one rather than refusing to run.

**Real cost (checked 2026-08-04):** no free tier on any of these models.
- Images via `gemini-3.1-flash-image-preview` (the current default — see "Model choice" below for why): ~$0.067/image at default 1K resolution. At 98 shots that's roughly **$6.57** for a full video. Scales with shot count, so a denser shot list (recommended, see "Shot density" above) costs more via this paid path than it does via Flow's free path.
- Video via `veo-3.1-generate-preview`: meaningfully more per clip than images — check current pricing at `ai.google.dev` before generating more than a couple, since it adds up fast if a whole video's worth of shots get switched to `Type: video`.

**Required `shot_list.md` format** (the script parses this exactly — keep the field labels as-is):

```markdown
## Shot 001
- Narration: "the script line(s) this shot covers"
- Duration: ~8s
- Type: image
- Visual: character
- Prompt: full generation prompt for this shot, one line (self-contained, style suffix included)
```

One `## Shot NN` block per scene, `NN` zero-padded and sequential. `- Type:` is optional and defaults to `image` if omitted — set it to `video` for the small number of shots that should be short (~8s) video clips instead of stills. `- Visual:` (`character`/`diagram`/`environment`) determines which style suffix gets appended when writing the prompt — it's not read by the generation script itself, just documentation of why the prompt looks the way it does. The `- Prompt:` line must stay on a single line — that's the field the script actually sends to the model.

**Running it:**
```
python system/05_visuals/generate_visuals.py videos/001-toba-supervolcano
```
Generates any shot in `shot_list.md` that doesn't already have a matching output file in `generate/generated/images/` (`.png` for images, `.mp4` for video — safe to re-run after adding new shots or fixing a bad generation, just delete the specific output file to force a regenerate). Video shots poll until the generation completes (typically 1-3 min per clip) before moving to the next shot.

**Model choice:** images default to `gemini-3.1-flash-image-preview` (~$0.067/image). The cheaper `gemini-2.5-flash-image` (~$0.039/image) was deliberately avoided as the default despite costing less — Google has it scheduled to shut down 2026-10-02, too close to the start of production to build on. Swap to `gemini-3-pro-image-preview` in the script's `IMAGE_MODEL` constant for higher quality (4K, better text rendering) at higher cost if needed. Video defaults to `veo-3.1-generate-preview` (`VIDEO_MODEL` constant).

**Known issue (as of 2026-08-04):** there are live developer-forum reports of the video API's `reference_images` parameter throwing a 400 error despite being documented as supported. If video generation fails specifically on that argument, this is likely why — check the Gemini API forum for current status before assuming the script is broken.

## Assembly-stage pacing: fix stillness in CapCut, not just in generation (researched + locked 2026-08-12)

Watching video 001's finished render surfaced a real complaint: long stretches
felt static/frozen even where the shot list itself was reasonably dense. The
`shot_list.md` pacing fix above (cap shot length, rotate character
poses, promote some short character beats to `Type: video`) addresses half of
this — the other half is an **assembly-stage (CapCut) technique that costs
nothing extra and applies to every still image, not just a few promoted
ones**:

- **Default every still image to a slow Ken Burns pan/zoom** (a documentary
  technique: slow zoom in/out and/or a slow pan across the frame) rather than
  a hard static hold. This alone fixes most of the "looks frozen" problem for
  free, since it's applied in editing, not generation — CapCut has this
  built in natively (slow zoom in/out, camera pan, keyframe animation on
  stills), no extra tool needed.
- **Vary the pan/zoom direction shot-to-shot** the same way character poses
  get rotated — a run of identical zoom-ins reads as repetitive too, just
  more slowly than a hard static image does.
- **Parallax (2.5D layering — separating a shot into foreground/background
  layers that move at slightly different speeds) is a stronger version of
  the same trick**, worth reaching for on the handful of shots per video
  that most reward it (a clear foreground subject against a distinct
  background — a character silhouette against a painted cave/landscape,
  for instance) rather than attempting it on every shot.
- **This changes the cost/benefit of `Type: video` shots**: since Ken
  Burns/parallax now handles the baseline "don't look frozen" problem for
  every image at zero extra generation cost, reserve actual `Type: video`
  generation (meaningfully more expensive than an image, per the real cost
  numbers above) specifically for beats that need *real* character movement
  a pan/zoom can't fake — a gesture landing, a head turn, a flinch — not as
  a general-purpose fix for stillness. Two-tier approach: Ken Burns as the
  default treatment on every still, `Type: video` as the narrow exception
  for a genuinely dynamic beat.
- **If a `Type: video` shot does get generated**, real motion isn't
  constant-speed — per basic animation timing principles, a gesture should
  accelerate into a brief hold at full extension before recoiling, or it
  reads as a blur with no impact. Worth a line in the prompt itself (e.g.
  "arm extended, held for a beat") rather than just describing the action
  in the abstract.

Net effect: most of the fix for "the video looked still" lives in the CapCut
assembly step (free, applies to 100% of shots), with the shot-list-level fixes
above (duration caps, pose rotation, selective `Type: video`) handling what
pan/zoom alone can't.

## Status

`shot_list.md` fully built and verified for video 001: 98 shots, all classified (`character`/`diagram`/`environment`), all prompts self-contained with style suffixes, word-for-word match against `script.md` confirmed. `generate/generate_image.md` and `generate/generate_voice.md` both generated. Next concrete step: paste `generate_image.md` into Flow or a batch extension (free path) and generate the 98 shots — no reference image build step required first.

Video 002 ("built-to-starve"): shot-list pacing fixes above apply from this
video onward. Video 001 itself is left as-is unless revisited separately —
these fixes are forward-looking, not a retroactive edit to a finished video.
