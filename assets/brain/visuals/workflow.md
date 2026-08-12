# Visuals — image/video generation workflow

Researched 2026-08-04, revised 2026-08-05. Covers how to turn a locked `shot_list.md` into actual images/clips for a video. I don't have API/tool access to Flow, browser extensions, or a screen to operate any of this myself — everything below is prep for you to run.

## Validation: this is confirmed to be how the actual copycat cluster is produced

Researched how Ink Explainer-style channels are actually made, not just guessed. Two different production tiers exist in this space, and they're not interchangeable:

- **The AI-stickman channel cluster (Ink Explainer, Deep Epoch, Before Civilization, Stick Plot, Brook Explains, Mack Explains, Before The Clock — see `assets/references/channel_reports/2026-08-04_niche_landscape.md`)**: this exact genre is documented as a real, currently-exploding 2026 niche built on a specific three-tool AI workflow — **Claude AI for scripting, ElevenLabs for voiceover, and Flow AI for visuals.** That is precisely the pipeline already locked for this channel (`CLAUDE.md`) — not a guess, but a match to the actual documented production method for this exact channel cluster. One real warning that came with it: YouTube has started demonetizing mass-produced, low-effort AI content — quality and genuine human oversight at each step (the sourcing rigor already locked in `assets/brain/structure.md`, the tone work in `assets/brain/persona.md`) are what keep a channel like this monetizable, not just running the pipeline on autopilot.
- **OverSimplified and Sam O'Nella Academy — different production tier, tone-only borrowing.** OverSimplified is hand-animated in Adobe After Effects with assets built in Photoshop — a real animator's pipeline, not AI-generated. Sam O'Nella Academy is drawn by hand in MS Paint — deliberately lo-fi, fully manual. Both are why their *writing/tone* (the OverSimplified/Sam O'Nella blend in `assets/brain/persona.md`) is worth borrowing, but their *production method* isn't something an AI pipeline replicates — we're taking their comedic technique, not their tooling.

## Shot density: one image per sentence (locked 2026-08-05)

Researched actual practice for this specific genre (AI-generated faceless explainer channels), not generic film-editing advice. Two data points:

- Generic YouTube editing research suggests 8-12 cuts/minute for engaged tutorial-style content, with variation (fast micro-cuts mixed with longer holds) rather than a flat rhythm — useful context, but that's a different genre from a narrated documentary-style explainer.
- **The actual common default for AI-generated faceless-video tools is one image per sentence** — several script-to-video tools in this space generate a matching image prompt per sentence by default, splitting at natural sentence/paragraph boundaries so every scene is an independently swappable visual unit.

**Method used for `shot_list.md`:** split the locked script into its real sentences programmatically, then merge any sentence under 8 words forward into the next one (so no shot is an unusably short fragment, e.g. "Global population." alone). This produced **98 shots** for the ~2,451-word script — about 8.2 cuts/minute, denser than a slow documentary hold, close to the faster end of general pacing research. Apply this same method to every future video's shot list: split by sentence, merge tiny fragments, one shot per resulting unit.

**Do this programmatically, not by hand** — build the shot skeleton (sentence text + word count + duration) with a script first, verify the total duration and word-for-word coverage matches `script.md` exactly, *then* write prompts. Hand-computing durations across 90+ shots is error-prone (this drifted noticeably the first time it was tried by hand) — always verify the final shot list's concatenated narration matches the script word-for-word before treating it as locked.

## Primary method: fully self-contained prompts, no reference image required (revised 2026-08-05)

The original plan was to build one character reference image + one style reference image, attach them as "ingredients"/reference images to every generation, and keep the prompts themselves bare (scene/action only, no character description). That plan was dropped after research showed it doesn't hold up across batch tools: some Chrome extensions for Flow (FlowBatch in particular) only support **one global reference image applied to the whole batch**, with no per-prompt control. Since a large fraction of `shot_list.md`'s 98 shots are pure diagrams/maps/quote-cards/environment shots with no character in them at all, attaching a character reference for a whole batch risks forcing that character into shots that shouldn't have one.

**The fix: make every prompt fully self-describing instead.** No reference image needed, no dependency on how any particular batch tool handles attached references, works identically whether you're pasting into Flow by hand, a batch extension, or the paid API script.

Every shot in `shot_list.md` has a `- Visual:` tag — `character`, `diagram`, or `environment` — and its `- Prompt:` line has the matching fixed style-suffix text appended directly. The three suffixes (reused verbatim on every shot of that type, across every video):

**Character** (a shot featuring the recurring host): **see `visuals/character.md`'s "Locked character suffix" section for the current, exact wording — that file is the single source of truth for this text, don't copy it here again.** (This section used to quote the suffix inline, but that copy went stale after the character-design hair fix and started contradicting the real locked version — removed 2026-08-12 so there's only ever one place this text can drift out of date.) The suffix wraps the same art-style framing used by the `diagram`/`environment` suffixes below (flat 2D cartoon webcomic illustration, strict non-photorealistic requirement) around the locked character description.

**Diagram** (maps, timelines, quote cards, DNA trees, icon montages, on-screen text overlays — no character, no painted scene):
> Art style: flat 2D vector infographic illustration, like a clean explainer-video graphic — this is a STRICT requirement. ABSOLUTELY NOT photorealistic, NOT a painting, NOT 3D rendered, NOT a photograph. Simple flat 2D icons and shapes only, thin sans-serif on-screen text labels where needed, muted flat color palette, bold clean outlines, no gradients, no realistic textures or lighting, no painterly brushwork.

**Environment** (object/landscape/still-life shots with no character and no infographic data — a campfire, a shell midden, an eggshell close-up, a distant eruption):
> Art style: flat 2D cartoon webcomic illustration, like Cyanide & Happiness, OverSimplified, or Sam O'Nella Academy — this is a STRICT requirement. ABSOLUTELY NOT photorealistic, NOT a digital painting, NOT concept art, NOT a photograph, no realistic textures or lighting anywhere in the image. Bold, thick, uniform black outlines on every object and shape, flat or simply-shaded solid colors, simplified geometric forms rather than realistic detail. Muted, moody color palette matching a dark documentary tone, but rendered entirely as a flat cartoon illustration — no gradients, no soft painterly brushwork, no photorealistic lighting or texture.

These three blocks match the established visual style from `assets/references/images/inkexplainer96_*` and the production notes in `assets/brain/structure.md`. **Apply this same classify-and-append method to every future video** — tag each shot's `- Visual:` type when writing `shot_list.md`, append the matching suffix to its prompt, done. No character/style reference image needs to be built before generating.

**Lesson learned from the first real test batch (2026-08-05):** the first version of these suffixes was too weak — it named the style once ("stickman-style," "flat cel-shaded") but didn't repeat/enforce it hard enough, and the model defaulted to photorealistic digital painting for backgrounds even when the character itself came out correctly as a stick figure (a cartoon character pasted onto a photo-real background, not a cohesive illustration). Two fixes: (1) the suffix now explicitly demands the *background* match the *same* flat cartoon style as the character, not just the character on its own, and (2) it names concrete reference styles (Cyanide & Happiness, OverSimplified, Sam O'Nella) and repeats "ABSOLUTELY NOT photorealistic" rather than a single soft mention — image models need forceful, repeated, unambiguous style language, a single stylistic adjective buried in a longer prompt gets ignored. Also caught: the word "cutaway" in a prompt (meant as a filmmaking term, "cutaway shot") got misread as "cutaway diagram" and produced an unwanted geological cross-section with labels — avoid words with a strong competing meaning in visual-generation contexts; watch for this in future shot lists.

**Always test a small batch (3-5 shots spanning all three `- Visual:` types) before generating the full shot list**, and actually look at the results — this is exactly how the above bug was caught, before spending the effort/cost generating all 98.

## Optional: reference-image / "Ingredients" approach (secondary, not required)

Flow's own manual UI has a feature called **Ingredients to Video** — attach up to 3 reference images (character/object/style) to a single generation and it maintains that subject's appearance across shots. This is a real, documented feature and can still be useful:

- As a **personal visual-QA anchor** — build a character reference image once (manually in Flow, or via `pipeline/generate_character_reference.py`) and eyeball generated shots against it by hand, without feeding it into every generation.
- For **single-shot manual generation** in Flow's own UI, where you can attach it per-shot with full control (unlike bulk-batch tools) if you want extra consistency insurance on top of the self-contained prompt text.

Not required for the primary workflow above. If built, save to `assets/character/host_reference.png` / `assets/character/style_reference.png`, generated once per channel, reused (optionally) across videos.

## Confirmed 2026-08-05: free vs. paid is about *which door*, not which model

Ran `generate_character_reference.py` against a real API key with no billing enabled. Result: `429 RESOURCE_EXHAUSTED`, `limit: 0` for `generativelanguage.googleapis.com/generate_content_free_tier_requests` on `gemini-3.1-flash-image`. Confirmed directly from Google's own API, not a search result — **the developer API has a hard $0 free tier for image generation on this project, full stop.**

But the same underlying model is free through Google's *consumer* surfaces — Flow's own web app (`flow.google.com`), the Gemini app, and AI Studio's interactive playground all give free daily quotas (Flow: sign in with any Google account, no billing; Gemini app: ~20 free images/day; AI Studio playground: ~50/day). Same model ("Nano Banana"/Gemini image family), different access path — the API is metered/billed, the interactive apps are free with a daily cap. **Given cost is a real concern here, the manual Flow path is now the recommended default, not just a fallback** — reserve the API script (below) for later if/when paid full automation is worth it.

## Generating the shots: the free path (recommended for now)

**Option A — one at a time, directly in Flow:**
1. Go to `flow.google.com`, sign in with a Google account — no billing needed.
2. Copy a shot's full `- Prompt:` line straight from `shot_list.md` (already self-contained, includes the style suffix) into Flow's text-to-image.
3. Generate, compare against the established style thumbnails (`assets/references/images/`) for consistency, regenerate if it drifts.
4. Save the output into `videos/NNN-<slug>/visuals/`, named to match the shot number (e.g. `001.png`).

**Option B — batch, via a browser extension (faster for this many shots):** third-party Chrome extensions (FlowBatch and similar — see Chrome Web Store) sit inside your own already-logged-in Flow tab and process a whole list of prompts automatically. Format confirmed: paste prompts **one per line**, no numbering or extra formatting, into the extension's side panel; it queues and generates each one, with bulk download. Since every prompt is now self-contained (no shared reference-image state needed), any batch tool works regardless of how it handles reference images — that whole class of problem no longer applies. Open `generate/generate_image.md`, copy the whole file, paste into the extension.

**Pacing around the free daily cap:** 98 generations is more than most free daily quotas allow in one sitting — expect to spread it across several days, or check if the batch extension's own free tier (often ~10/day without a license) is more limiting than Flow's own quota.

## Per-video `generate/` folder (locked 2026-08-05 — do this for every future video)

Once a video's `shot_list.md` is locked (including `- Visual:` tags and style suffixes on every prompt), produce two plain export files in a `generate/` subfolder next to it — `videos/NNN-<slug>/generate/`:

- **`generate_image.md`** — every shot's full `- Prompt:` line (self-contained, suffix included), one per line, nothing else (no numbering, no narration/duration). Extract this programmatically from `shot_list.md` (don't hand-copy — risk of transcription drift). This is what gets pasted into Flow or a batch extension.
- **`generate_voice.md`** — the locked script's full narration text, audio tags converted from `*[tag]*` to plain `[tag]` (ElevenLabs v3 reads bracket tags directly, see `assets/brain/voice.md`), paragraph breaks kept, no other markdown/metadata. Extract programmatically from `script.md` the same way. This is what gets pasted into ElevenLabs.

Regenerate both whenever `shot_list.md` or `script.md` changes — treat them as build artifacts, not hand-maintained files.

## Alternative: the paid/automated path

`pipeline/generate_visuals.py`: reads `shot_list.md` directly (prompts are already self-contained, so it no longer needs a reference image to produce on-style results, though it can still optionally attach one if `assets/character/host_reference.png` exists), calls the Gemini API, saves straight into `visuals/`. This is not Flow itself — Flow the consumer app wraps the same underlying Veo/Imagen models, which are also available directly through the official Gemini API — but this route is billed with no free tier, unlike Flow's own web app. **Both images and short video clips are supported**, per-shot, via the same script, if/when paid automation is worth it (e.g. producing many videos at volume, where manual generation in Flow doesn't scale).

Google Flow's own consumer app doesn't have a clean official automation API (third-party browser extensions exist but are unofficial). The models underneath it — Veo 3.1 (video) and the Gemini/Imagen image models — **are** available through the official Gemini API.

**Setup (one-time):**
1. Get a Gemini API key from Google AI Studio (`ai.google.dev`) — note this is **paid, no free tier**, not the free consumer Flow app, so billing needs to be set up. See "Real cost" below for actual per-image/per-video numbers — small for one video, but not zero.
2. Copy `.env.example` (repo root) to `.env` and fill in `GEMINI_API_KEY=...` — both scripts load `.env` automatically via `python-dotenv`. `.env` is gitignored, never committed. (An `export GEMINI_API_KEY="..."` in your shell also works if preferred, but only lasts that terminal session — `.env` persists.)
3. `pip install -r pipeline/requirements.txt`
4. A character reference image is now **optional** for this script (see "Primary method" above) — if `assets/character/host_reference.png` doesn't exist, the script just skips attaching one rather than refusing to run.

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
python pipeline/generate_visuals.py videos/001-toba-supervolcano
```
Generates any shot in `shot_list.md` that doesn't already have a matching output file in `visuals/` (`.png` for images, `.mp4` for video — safe to re-run after adding new shots or fixing a bad generation, just delete the specific output file to force a regenerate). Video shots poll until the generation completes (typically 1-3 min per clip) before moving to the next shot.

**Model choice:** images default to `gemini-3.1-flash-image-preview` (~$0.067/image). The cheaper `gemini-2.5-flash-image` (~$0.039/image) was deliberately avoided as the default despite costing less — Google has it scheduled to shut down 2026-10-02, too close to the start of production to build on. Swap to `gemini-3-pro-image-preview` in the script's `IMAGE_MODEL` constant for higher quality (4K, better text rendering) at higher cost if needed. Video defaults to `veo-3.1-generate-preview` (`VIDEO_MODEL` constant).

**Known issue (as of 2026-08-04):** there are live developer-forum reports of the video API's `reference_images` parameter throwing a 400 error despite being documented as supported. If video generation fails specifically on that argument, this is likely why — check the Gemini API forum for current status before assuming the script is broken.

## Status

`shot_list.md` fully built and verified for video 001: 98 shots, all classified (`character`/`diagram`/`environment`), all prompts self-contained with style suffixes, word-for-word match against `script.md` confirmed. `generate/generate_image.md` and `generate/generate_voice.md` both generated. Next concrete step: paste `generate_image.md` into Flow or a batch extension (free path) and generate the 98 shots — no reference image build step required first.
