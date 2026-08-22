# Ink/stickman long-form format — brain reference

Frozen reference on the "ink"/stickman-style long-form explainer format: the channel aim, the script-structure formula, and a worked example it was distilled from. Carried over from earlier project research. Treat as a starting hypothesis, not proven fact, until our own videos confirm or break it — update this file as our own patterns get established.

Reference images for this style (thumbnails, frame captures, style boards) live in `system/shared/references/images/` next to this file.

**Naming correction (2026-08-04, updated):** the "worked example" below is from the real channel **Ink Explainer**, handle `@Inkexplainer96` (44.8K subscribers) — an earlier pass at this incorrectly said the name didn't resolve to a channel; it does, the handle just needed the `96` suffix. This channel's own upload of the video has 1.07M views and is very likely the *original* that at least five other small channels (Deep Epoch, Before Civilization, Stick Plot, Brook Explains, Mack Explains, Before The Clock) cloned within about a month. See [`system/shared/references/channel_reports/2026-08-04_inkexplainer96_deep_dive.md`](../references/channel_reports/2026-08-04_inkexplainer96_deep_dive.md) for a full breakdown of this channel's catalog, performance pattern, visual style, and narration style (with quoted transcript examples) — this is the channel to actually study and replicate. The [niche landscape report](../references/channel_reports/2026-08-04_niche_landscape.md) still holds for the competitive-saturation point: treat the specific "rain" angle as taken and pick a different forced-constraint scenario for our own first video.

## Channel aim

Long-form animated "ink"/stickman-style explainer videos — immersive second-person narration over illustrative/silhouette animation, research-backed history/science/survival topics.

## Length target (locked 2026-08-04, revised from full-catalog data)

**11-13 min / ~2,450-2,800 words**, using the ~205-215 WPM pace target from `system/06_voice/voice.md`. This supersedes the original "~11-12 min" estimate, which was guessed from a single video before the full 12-video catalog was pulled. Ink Explainer's early videos ran 4-9 min, but their three most recent uploads — Rain (11:37), Winter (11:30), Guns (12:47) — average almost exactly 12 min, a deliberate recent trend, not noise. It also lines up with the channel's own YPP watch-hours goal: longer retained videos build watch hours faster per upload. Apply this to every video, not just one.

## Script structure formula (~11-12 min target, validated against the Ink Explainer worked example below)

1. **Hook (0:00-~1:30)** — Immersive second-person scene dropping the viewer into the crisis/premise directly ("Imagine you..."). Establish stakes concretely (specific, visceral detail, not abstract danger). Contrast with a modern-day equivalent for relatability, then pivot: "for a human [X years/millennia] ago, the same situation could kill you in [N] specific ways." List them as a hook, not yet answered — trailer the whole video.
   **Sub-rule, locked 2026-08-22 (retention research, sourced):** the *whole 90-second section* is fine, but the actual stakes/curiosity payoff inside it must land within the **first ~15-20 seconds of narration**, not just sometime before the section ends — retention data shows viewers who don't get a clear payoff promise within ~15s drop off sharply, and the drop gets severe past 45s. Checked our own two scripts against this after the fact: video 002's real opening ("you skipped breakfast... you are, medically speaking, closer to starving to death than you've been all week") lands it inside 15s — that's the model to match. Video 001's opening spends a full paragraph (~30s) on scene-setting before its actual myth-busting tease arrives closer to 60-90s in — slower than this rule now wants. Not retroactively re-cut (it's a frozen, upload-ready video), but don't repeat that pacing on a future hook.
   **On-screen text during the hook, specifically:** many viewers start videos muted — a hook with on-screen text reinforcing the spoken line measurably holds more watch time than narration alone. For the hook section's shots, `shot-list-builder` should explicitly write a short on-screen text/label into the `- Prompt:` itself (e.g. "on-screen text reads '[key phrase]'") even on `character`-type shots that wouldn't normally carry text — this is deliberate, prompt-specified text, not the same thing as the invented-text bug `system/04_shots/character.md` guards against (that clause stops the *model* from inventing text nobody asked for; this rule is us deliberately asking for specific text, which is always allowed).
2. **First major pillar (~1:30-4:00)** — The single most foundational fact/technology/behavior the rest of the video depends on (in the rain example: fire). Ground it in real, dated archaeological evidence (site name + age), then walk through practical mechanics in plain, concrete terms.
3. **Middle pillars (~4:00-8:00)** — 2-4 sub-sections, each anchored to a specific site/study/date, building outward from survival to craft/production to art/culture. Each pillar should escalate in "surprise" value — save the most counter-intuitive fact for the section people remember (e.g. cave art as a rainy-day activity, not a special ritual-only act).
4. **Social/cultural payoff (~8:00-9:30)** — Zoom out from individual survival to group/cultural significance. This is where a named study or research finding (with a citable stat, e.g. "80% of nighttime talk was stories") gives the video intellectual weight beyond just "cool facts."
5. **Reframe / upside twist (~9:30-end)** — Flip the initial crisis framing: what the "downtime" or hardship actually enabled that benefited the people afterward. Close on a compact thesis sentence that reframes the whole video's premise, not just a summary.

Formula in one line: **immersive crisis -> grounded evidence pillars, escalating surprise -> cultural payoff -> reframe as advantage.**

**Open loops at every section transition (locked 2026-08-22, retention research, sourced).** The hook's "list threats, don't answer them yet" instruction above is already one open loop — the rule now is to use that same technique at *every* pillar-to-pillar transition, not just the cold open. End a section on an unanswered question or a dangling implication the next section resolves, rather than a flat summary-then-move-on. This is grounded in the Zeigarnik effect (unfinished questions get remembered/followed better than finished ones) — video 002's script already did this informally and noted it explicitly in its own header ("three explicit open loops... pillar-to-pillar transitions tightened to run on therefore/but causality rather than flat and-then sequencing") — that was the right instinct, now a standing rule for every future script, not a one-off choice.

## Title/hook checklist

1. **Does it pose a concrete, specific question or crisis, not a vague topic?** "What Did Ancient Humans Do When It Rained All Week?" is specific and visual — "Ancient Human Survival" is not.
2. **Is there an implied payoff/reveal, not just a premise?** The title should promise an answer exists, not just describe a scenario.
3. **Is it groundable in real evidence?** Every major claim in the script needs a citable site/study/date — don't script a claim that can't be sourced (this is core to the "research-backed" credibility the genre depends on).
4. **Does the thumbnail read as the genre in frame 1?** Dark/moody illustrated visuals should be unmistakable at a glance — stylized ink/silhouette look, not generic stock-photo energy. **Specifics, locked 2026-08-22 (CTR research, sourced)** — see `system/08_export/export.md` for the full checklist: ≤4 words of thumbnail text (text-heavy thumbnails measurably underperform), the character's face should carry a strong legible emotion (surprise/alarm/curiosity reads best, not a neutral expression), and the thumbnail must not repeat the title's actual information — the thumbnail opens a curiosity gap, the title gives it just enough context to make clicking worth it, and showing the same info in both wastes the pairing.
5. **Second-person or crisis framing in the hook, not third-person lecture opening?** "Imagine you..." pulls the viewer in; "Humans have long faced..." doesn't.

## Production/visual style notes

- **Animation aesthetic:** clean, stylized 2D/limited-animation — silhouettes or simplified figures, close-ups on hands/tools, glowing light sources contrasted against dark exteriors.
- **Pacing/tone:** slow-building tension -> explanatory calm -> reflective wonder. Dramatic contrast early, steady reveal-by-reveal flow through the middle, warmer tone for the social/cultural section. Soft ambient music, subtle tension under danger beats, warmer tones under social/art beats.
- **On-screen elements:** site names and dates shown cleanly as text; occasional simple diagrams for comparisons/mechanisms.
- **Voiceover:** second-person immersive narrative blended with factual delivery — engaging and slightly dramatic, not a dry lecture, not over-hyped either.

## Workflow for a new video

1. Pick a topic using the core-structure formula above: some "forced constraint" (weather, isolation, scarcity, disaster) that ancient/historical people had to survive or adapt to.
2. Research and lock 4-6 real, citable sites/studies/dates that map onto the pillar structure (foundational tech -> craft/production -> art/culture -> social payoff).
3. Draft the hook using the second-person crisis formula.
4. Write the full script following the 5-part structure above.
5. Draft 2-3 title variants using the title checklist.
6. Cross-check against the worked example below (and any other benchmark teardowns added later) — has this exact angle been done before? If yes, differentiate the specific evidence/angle, don't just re-tell the same facts.

## Worked example: Ink Explainer teardown

_Written 2026-08-02. Covers one video in detail: "What Did Ancient Humans Do When It Rained All Week?" by Ink Explainer — same long-form animated "ink"/stickman explainer genre. This is what the formula above was distilled from._

**Video basics:** ~11-12 min. Animated educational explainer (2D/stylized "ink"/illustrative animation). Atmospheric, cinematic storytelling with a calm, immersive second-person voiceover. Dark/moody cave-and-rain visuals mixed with clear archaeological evidence overlays. Research-backed, sources listed in the description.

**Hook (0:00-~1:30):** Immersive second-person scene: "Imagine you haven't eaten in 2 days. You know exactly where the herd is... and then it starts raining." Heavy, wind-driven, multi-day rain, not a drizzle. Hunting becomes impossible (tracks wash away, wet rocky ground risks injury/death). River rises, fire struggles. Contrast with modern cozy rainy day (close the window, coffee, Netflix, blanket). For a human 50,000 years ago, the same rain could kill in three ways: hypothermia (wet body loses heat up to 25x faster), flash floods in caves/rock shelters, predators forced into the same shelters (evidence of leopard puncture marks on human skulls in South African caves). Rain compressed the world — humans, prey, and predators squeezed into the same dry spots. Priority #1: keep the fire alive.

**Pillar 1 — Fire as life support (~1:30-4:00):** Controlled fire evidence goes back at least 400,000 years (Qesem Cave, Israel), possibly ~1 million years (Wonderwerk Cave, South Africa). Starting fire from scratch was unreliable for much of prehistory; most groups carried embers instead (wrapped in green leaves or tinder fungus / Fomes fomentarius — "biological lighter"). Ötzi the Iceman (5,300 years old) carried a full fire kit: tinder fungus, flint, iron pyrite, plant tinder. During rain: move fire deeper into the cave, shield with hides/brush, feed carefully — dry lower branches under conifer canopies, split wet logs for dry cores, birch bark (contains betulin, burns even when wet). Fire-tending could be a full-time job — warmth, light, predator safety, cooking, social center.

**Pillar 2 — Productive indoor work (~4:00-6:30):** Stone tools (debitage piles concentrated near firelight). Pigment/ochre processing workshop at Blombos Cave, South Africa (~100,000 years ago): abalone shells as mixing bowls, ground ochre, bone tools for stirring — systematic production. Bone needles with eyes (~61,000 years ago, Sibudu and later Europe/Asia). String/rope technology: oldest direct evidence of twisted plant-fiber string at Abri du Maras, France (~52,000 years ago, Neanderthal); dedicated mammoth-ivory rope-making tool at Hohle Fels Cave, Germany (~35,000 years ago). Bedding at Sibudu Cave (~77,000 years ago): layered sedges/rushes/grasses topped with Cape laurel leaves (natural insect repellent), periodically burned and replaced.

**Pillar 3 — Art & creativity (~6:30-8:00):** Cave art as a likely rainy-day activity: Chauvet Cave (France, ~36,000 years old) — highly skilled, anatomical paintings in motion. Sulawesi, Indonesia (oldest known figurative art, ≥45,500 years). Paintings often deep underground, requiring animal-fat lamps. Logic: people went deeper into the dark to create when outdoor life was impossible and practical tasks were already done.

**Cultural payoff (~8:00-9:30):** Forced proximity of 15-30 people for days around a fire created culture. Polly Wiessner's 2014 study of Ju/'hoansi Bushmen: daytime talk was practical, nighttime fireside talk shifted >80% to stories, songs, ceremonies. Stories transmitted survival knowledge (water sources, edible plants, tracking, flint locations) plus myths about rain. Australian Aboriginal oral traditions accurately describe sea-level rise from ~7,000 years ago — multi-millennial cultural memory built through repeated retelling during downtime.

**Reframe / upside twist (~9:30-end):** After rain: soft ground creates perfect animal tracks for hunting. Collectable rainwater in rock depressions (some deliberately deepened). Food boom — mushrooms/plants explode, tubers easier to dig, insects surface, termite swarms in tropical Africa (protein-dense, no tools needed). Closing thesis: rainy days weren't downtime or crisis alone — they were when humans prepared tools/clothing/rope, made art, told the stories that carried knowledge across generations. "Boredom didn't exist... you get creative, and that might be the single biggest reason we're still here."

## Open questions / things to verify once we have our own channel

- Actual view counts, retention curves, and upload cadence for Ink Explainer are unknown — this teardown is style/structure only, not a validated performance benchmark yet.
- No thumbnail or title-pattern data gathered yet across multiple Ink Explainer videos — only one video analyzed. Expand with more of their catalog (or other benchmark channels) before treating any single-video pattern as proven.
