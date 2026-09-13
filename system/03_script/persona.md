# Tone/persona options — researched 2026-08-04

This started as a decision doc, not a locked reference — everything else in `system/` (script structure, narration pacing target, ElevenLabs technique) was built around Ink Explainer's dramatic-but-earnest tone. The options below range from "same tone, faster" to "same visual style, fully comedic," and picking one changes the script formula, not just the voice performance. Status: **Locked 2026-08-04 — see "Decision log" below for the chosen blend.** (This status line previously said "not decided yet" even after the Decision log below documented a firm choice on the same date — fixed 2026-08-12 to stop the file contradicting itself.)

## Four reference archetypes

### 1. Fireship — hyper-fast, dense, meme-literate
- Blazing pace: a topic other creators take 30 minutes on gets done in a self-aware "100 seconds."
- Deadpan humor woven through via memes and industry in-jokes, rapid cuts synced to jokes for constant momentum.
- Despite the comedy, treats itself as a serious educational resource underneath — the jokes are garnish, not the point.
- **Relevance to us:** the pacing philosophy (compress hard, cut anything not earning its second) is portable even without adopting the meme-humor. Less portable: the in-jokes rely on a tech-insider audience that has a direct analogue for "in on the joke" — history/survival content doesn't have an equivalent built-in in-group the same way.

### 2. CGP Grey — fast but clear, dry deadpan, near-zero decoration
- Speaks quickly but stays clear — a "voice that sounds almost too calm for the subject."
- Minimal visuals (stick figures, geometric shapes, white backgrounds) exist purely to support the narration, never to distract.
- The dry wit is understatement, not jokes — restraint is the entire style. No sound effects, no comedic asides, no character voices.
- **Relevance to us:** closest of the four to what's already documented for Ink Explainer (calm, measured, no theatrics) — this is really the "turn the dial toward maximum clarity and restraint" end of the spectrum, not a comedy option at all.

### 3. OverSimplified — historically accurate *and* funny, stick-figure visuals
- 8M+ subs, covers wars/revolutions/historical figures. Narration is explicitly described as "calm, clear, and slightly humorous, but never sarcastic or dismissive" — the creator (Stuart Webster) speaks directly to the viewer in plain, relatable language.
- Visual style: stick figures with blocky bodies, flexible limbs, oversized heads (Cyanide & Happiness-adjacent) — **the same visual family as our own stickman genre**, not a coincidence to ignore.
- Comedy sits on top of real historical accuracy and "surprisingly thoughtful insight" — it's not comedy replacing substance, it's comedy as delivery on top of substance.
- **Relevance to us:** this is the strongest direct precedent that "stickman visuals + genuinely accurate research-backed history + humor" is a proven, massive-scale combination — arguably a closer visual match to our genre than Ink Explainer itself.

### 4. Sam O'Nella Academy — deadpan, dark humor, "friend telling you an insane Wikipedia story at 4am"
- Voiceover described as deadpan and unbothered, paired with deliberately crude stick-figure visuals — "dumb-looking stick figures and razor-sharp narration."
- Leans into genuinely dark subject matter (death, disease, gruesome history) played completely straight-faced, letting the gap between flat delivery and dark content do the comedic work.
- Low-effort visuals + high-effort writing — the punchlines carry the video, not the animation.
- **Relevance to us:** the closest match to "dark humor" specifically. Also stickman-visual-family. Riskier than OverSimplified because it leans harder into genuinely dark material for comedic effect rather than keeping comedy secondary to accuracy — worth being deliberate about how dark is too dark for a channel that also wants YPP monetization and broad watchability.

_Note: "genz/monkey humor" as a specific named channel wasn't identified — if there's a specific channel behind that description, name it and it can get the same treatment as the four above._

## Where this leaves the decision

Two real axes, not one:

1. **How much comedy at all** — from zero (current Ink Explainer-style default, CGP Grey-adjacent) to comedy-as-primary-driver (Sam O'Nella).
2. **What kind of comedy, if any** — dry/understated (CGP Grey) vs. meme/deadpan-fast (Fireship) vs. warm-and-slightly-humorous (OverSimplified) vs. dark/deadpan (Sam O'Nella).

Whichever direction gets picked changes real downstream artifacts:
- **Script formula** (`system/03_script/structure.md`) — the 5-part dramatic-immersive structure would need actual comedic beats written in, not just tonal polish, if leaning toward OverSimplified/Sam O'Nella.
- **Narration voice direction** (`system/06_voice/voice.md`) — currently says "not theatrical, calm, MrBallen-style restraint," which holds for CGP Grey-style but not for a Sam O'Nella-style deadpan-comedic read.
- **Title strategy** (`system/02_title/title.md`) — currently data-derived from Ink Explainer's straight-question titles; a comedic channel might title differently (worth re-deriving from OverSimplified/Sam O'Nella's own titles if that direction gets picked).

## Decision log

**Revised (2026-08-04): three-way blend — Fireship + OverSimplified + Sam O'Nella. Sarcasm and genZ humor are IN, not excluded.**

_Correction to the earlier version of this doc: it added a "never sarcastic or dismissive" guardrail, inherited from OverSimplified's own description rather than anything actually requested. That's removed — sarcasm and genZ-coded humor are an explicit, wanted part of the tone._

- **Base energy/pacing (Fireship): fast, sarcastic, meme-literate, self-aware.** Constant light wit and sarcastic asides running through the narration by default, not reserved for special moments — dry jokes about absurd historical decisions, self-aware quips, genZ-coded phrasing where it fits naturally. This is the default texture of the writing, not a garnish.
- **Clarity/accuracy backbone (OverSimplified): still plain, direct-address, and historically accurate underneath the jokes.** Sarcasm and humor sit on top of real research-backed content (citations still required, per `system/03_script/structure.md`'s sourcing convention) — the comedy doesn't replace the substance, same lesson as OverSimplified even though the "never sarcastic" boundary itself is dropped.
- **Deadpan dark-fact technique (Sam O'Nella): kept as-is.** When a genuinely dark or absurd fact comes up, state it completely flat — no dramatizing, no dwelling — and let the gap between casual delivery and grim content land the joke. This still stacks fine on top of a generally sarcastic/witty base register.

Net effect: a narrator who's consistently witty, sarcastic, and fun (Fireship) — not just occasionally light (OverSimplified alone) — who still gets the facts right and cites sources (OverSimplified's substance-first discipline), and who goes completely flat/deadpan specifically on the darkest beats for contrast (Sam O'Nella).

### What this changes downstream

- **Script formula** (`system/03_script/structure.md`): structure stays the same (hook -> pillar -> escalating pillars -> cultural payoff -> reframe). Sarcastic/witty asides get woven throughout the writing, not just at pillar-escalation beats; the deadpan-flat treatment is reserved specifically for the darkest/most absurd facts as a contrast beat.
- **Narration voice** (`system/06_voice/voice.md`): pacing target (~200-215 WPM) and "not theatrical" vocal-delivery guidance both still hold — sarcasm/wit lives in the writing and word choice, not in a big dramatic vocal performance, same mechanism as how Fireship and CGP Grey both stay dry/flat vocally while being funny/witty through content. Mark the deadpan dark-fact beats explicitly in `script.md` for ElevenLabs tagging (`[flatly]`, `[deadpan]`); everything else can carry a slightly more playful/sarcastic tag where natural (`[amused]`, `[wry]`).
- **Title strategy** (`system/02_title/title.md`): no change needed yet — still data-derived from Ink Explainer's titles. Worth revisiting once we have our own published titles, since a sarcastic/genZ-humor channel might title more playfully than Ink Explainer's straight factual-question format.

## Revision (2026-09-13): strip citation-speak out of narration — real competitor script analyzed

User flagged video 004's `script_draft.md` as "too science-centric... talking about science and hypothesis stuff" — and a real transcript pull of a Deep Epoch video (a direct clone-cluster competitor, `WkbdkfRETfk`, "How Did Ancient Humans Survive Without Clean Water?") confirmed the specific mechanism: **it never once names a researcher or cites a year-as-attribution in narration**, even though it's making real, specific, well-sourced claims (e.g. a precise archaeological date for German Neolithic wells) — the rigor lives in the specificity of the stated fact, not in showing its sourcing on-screen. Compare that to our own drift: `script_draft.md` had lines structured like "Mealey (1995) found..." or "a study showed X" — that's lecture/report voice, not immersive storytelling voice, and it was the single biggest tonal gap between us and the format we're supposed to be matching.

**New standing rule, effective immediately for every future script:**

1. **Never attribute a claim to a named researcher/study/year inside spoken narration.** State the finding as a flat, confident fact instead ("Evolution gave us excellent cooling and then handed us the bill" — not "researchers found that sweating evolved to..."). The citation still has to exist and be real — it just lives in `notes.md` as our own accuracy backstop, never spoken on-screen. This does not relax the sourcing requirement in `structure.md` (every major claim still needs a real citable source) — it only changes where that citation is allowed to surface.
2. **Hedge words are banned from narration voice.** "Researchers believe," "some evidence suggests," "it's thought that" — all report-voice, all cut. State it as true. Genuine scientific uncertainty (cases where we really don't know) gets dramatized as its own beat ("here's the part that's frustrating because we can't actually prove it") instead of hedged mid-sentence — uncertainty becomes a plot point, not a disclaimer.
3. **A joke or wry aside lands within 1-2 sentences of introducing any mechanism, not just at section boundaries.** The competitor script's density of one-liners (a mechanism explained, then immediately undercut or punched by a short quip) is much higher than our own drafts have been running — this is the actual lever for "too science-centric," more than word choice alone. If a paragraph explains a mechanism for 3+ sentences with no joke, that's the smell to look for when reviewing a draft.
4. **Prefer short declarative sentences for factual payload; save longer sentences for scene-setting/atmosphere.** Compound hedge-clause sentences ("it is possible that, under certain conditions, X may have contributed to Y") read as science-report style even with the citation stripped out — cut them to a flat statement.

Applies retroactively as a review pass on any unlocked draft (video 004's `script_draft.md` is the first candidate) before it gets locked, not just to scripts written from here on.
