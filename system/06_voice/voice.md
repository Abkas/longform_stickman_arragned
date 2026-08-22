# Narration & voice strategy — how faceless channels actually do this

Researched 2026-08-04. Covers the broader faceless-narration landscape, then a measured data point pulled directly from Ink Explainer's own transcripts (not just described — computed from real caption timestamps). Apply this when writing `script.md` (tag it for delivery) and when generating voiceover in ElevenLabs.

## The 2026 landscape

AI narration is now the default for this genre, not a compromise: over 70% of educational/explainer faceless channels use AI voices as primary narration. ElevenLabs is the dominant platform for it — Turbo v3 voices are identified as AI only ~6% of the time in blind listening tests, with natural breathing, emotional range, and pacing that holds up over long-form runtimes. Competing platforms (WellSaid Labs, Resemble, Google Neural2/WaveNet, OpenAI voices) exist but ElevenLabs is the one most specifically called out for history/documentary-style faceless content — confirms the tool choice already made for this pipeline is the standard one for this niche, not a shortcut.

## Voice archetype by content type

Different faceless niches converge on different vocal registers:

| Niche | Typical register |
|---|---|
| Documentary / educational (our niche) | Deep, natural, measured — ElevenLabs voices commonly recommended for this: "Clyde" (narrative, gravitas), "Josh" (journalistic), "Thomas" (measured, serious). Named voices drift in availability over time — treat as search starting points, not a locked choice, when actually picking one in ElevenLabs. |
| Motivational / self-help | Warmer, more upbeat (e.g. OpenAI "onyx"/"nova"-style voices) |
| Reddit-story / suspense | Clean, neutral American or calm British — emotional range without being theatrical |

## Case study: what actually differentiates a good faceless narrator (MrBallen)

MrBallen built a multi-million-subscriber true-crime empire starting as a faceless channel, and the explicit lesson from how he describes his own delivery: **he never adopts a "dark and scary voice."** Suspense is built through pacing and story structure, not vocal theatrics — calm, measured, talking to the audience like he's recounting a story to a friend. The character is barely exaggerated at all.

This matches what the Ink Explainer deep-dive already found in its own transcripts: conversational register, second-person immersion, short punchy sentences — not a theatrical "movie trailer" voice. **Cross-channel pattern: understated, conversational delivery + strong script structure consistently beats a theatrical voice performance in this genre.** Don't direct the ElevenLabs voice toward "dramatic narrator" — direct it toward "smart friend telling you something wild they just learned."

## Our own measured data point: Ink Explainer's actual pace

Computed directly from the two downloaded transcripts' caption timestamps (not estimated):

- Rain video: 2,413 words over 698 seconds = **~207 WPM**
- Guns video: 2,736 words over 769 seconds = **~213 WPM**

This is notably brisk — typical documentary narration runs 150-160 WPM, calm storytelling narration runs 130-150 WPM. Ink Explainer reads roughly **35-40% faster than baseline documentary pace**. This is consistent with the short-sentence, quick-signpost writing style already documented in the deep-dive (`system/shared/references/channel_reports/2026-08-04_inkexplainer96_deep_dive.md`) — the pace is a product of the writing, not just a TTS speed setting.

**Target for our own scripts: ~200-215 WPM equivalent pacing**, achieved primarily by keeping sentences short and signposting frequently (as documented in the narration-style section of the deep-dive), not by just speeding up playback.

## Voice creation path: ElevenLabs offers three, we're using Voice Design

- **Voice Library** — 10,000+ pre-made community voices, use immediately.
- **Voice Cloning** — feed it 3-5 min of real audio (yours or a rights-cleared source) to clone an actual person's voice. Sounds most natural since it's grounded in a real voice, but requires a real voice to start from.
- **Voice Design** (chosen for this channel) — generates 3 brand-new synthetic voice options from a text description, no real person behind it. Two modes: Realistic (what we want) or Character (fictional/creature voices). Prompt should be descriptive and granular — accent, character-type, gender, age, vibe — 20-1,000 characters, optionally with 100-1,000 characters of preview text for it to read. Generates 3 candidates per prompt; pick the best, or refine the prompt and regenerate.

**Locked direction (2026-08-04):** male, late 20s-30s, neutral American accent.

**Voice Design prompt to use:**
> A man in his late 20s to early 30s with a neutral American accent. Warm, clear, and quick-witted — the voice of a smart friend who just went down a research rabbit hole and can't wait to tell you what he found. Confident and articulate, capable of brisk, energetic pacing without sounding rushed or breathless. Naturally sarcastic and a little irreverent, but never mean-spirited. Capable of dropping into a completely flat, deadpan register for dark or absurd asides, then snapping right back to warm energy after. Not a movie-trailer narrator — no dramatic gravitas, no over-enunciated documentary tone. Grounded, conversational, a little mischievous.

Run this in ElevenLabs (Voices -> My Voices -> Add a new voice -> Voice Design, Realistic mode) — I don't have API access to generate it directly. Audition the 3 candidates against a snippet of `script.md` once it's locked, pick one, and log it below. If none of the 3 land, refine the prompt (more specific accent/age/texture cues tend to help) and regenerate rather than settling.

## ElevenLabs technique for this style

**Starting settings** (community-reported defaults for natural, non-robotic narration):
- Stability: 0.35-0.45 — natural variation without instability/warble
- Similarity: 0.75-0.85 — keeps the voice consistent across a full script
- Style Exaggeration: 0.15-0.25 — natural emotional range without sounding over-the-top

**Eleven v3 audio tags** — bracketed inline tags instead of SSML, for directing delivery straight from the script text:
- Pacing: `[pause]`, `[rushed]`, `[drawn out]`
- Emotion: `[calm]`, `[excited]`, `[whispers]`, `[sigh]`
- Tone: `[deadpan]`, `[flatly]`, `[cheerfully]`
- Plain punctuation also works: ellipses (`...`) for a natural trailing pause, a line break for a longer beat, capital letters for emphasis.

**Practical approach for `script.md`:** annotate the locked script with these tags at the structural beats identified in the deep-dive — the cold open line, the "here's the thing"-style signposts, and the closing callback — rather than tagging every sentence. Over-tagging reads as try-hard; the goal is a few precisely-placed delivery cues, matching how sparingly Ink Explainer's actual writing does the work (word choice and sentence rhythm carry most of the pacing, not vocal performance).

## Recommendation for our channel

1. **Pick one consistent voice and never switch it** — same brand-recognition logic as the recurring visual host character.
2. **Register: conversational-but-informed**, second/third-person blend as documented in the deep-dive. Not theatrical, not a "scary narrator" cliché.
3. **Pace target: ~200-215 WPM equivalent**, driven by short sentences and frequent signposting in the script itself.
4. **Use v3 audio tags sparingly**, only at cold-open / signpost / callback beats.
5. Direction locked (male, late 20s-30s, neutral American — see "Voice creation path" below for the actual Voice Design prompt); still open until it's generated and audited by ear against a script snippet. Log the chosen voice below once picked, so every future video stays consistent.

## Voice decision log

| Video | Voice used | Notes |
|---|---|---|
| 001 | Locked Voice Design prompt (male, late 20s-30s, neutral American — see prompt above), used unmodified | One of the 3 Voice Design candidates generated from that prompt; confirmed 2026-08-12 (this row previously said "not yet picked" despite real audio already existing for this video) |
