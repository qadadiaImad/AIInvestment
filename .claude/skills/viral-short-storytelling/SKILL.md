---
name: viral-short-storytelling
description: >
  Pick a viral short-form STORY STRUCTURE and write scroll-stopping HOOKS for
  @valuewithvalues finance Reels (flat-2D deadpan "Quarterly Report" sketch, ~15-20s).
  Decision guide by goal, 5 hook formulas with example lines, the default Myth-Bust beat
  sheet, and a VIRAL-vs-DEAD pattern table (2025-26, source-backed). Use BEFORE scripting
  or storyboarding an episode. Triggers: "story structure", "hook", "reel idea", "how
  should this open", "make it go viral", "what angle", planning any short-form video.
---

# Viral Short-Form Storytelling — Structures & Hooks (2025-26)

Use this to choose the narrative shape and opener for a reel **before** writing the script
(then use `short-form-scripting`) or recording VO (then `viral-voiceover-audio`).

**Our format assumption:** flat-2D animated deadpan finance sketch, ~15-20s, word-by-word
captions, optional pitched-TTS VO + newsroom bed (`QuarterlyReport.tsx` + `gen_qr_audio.py`,
character cast in `halal-reels/src/toon/characters.ts`). Cold open on the visual/number —
no logo sting, no "hey guys", one payoff per video.

## 1. Pick a structure by goal

| Goal | Structure | Length | Why |
|---|---|---|---|
| Single sharp insight, max reach | **Myth-Bust / Contrarian Flip** | 15-20s | Perspective-shift hook interrupts scroll in 1-3s; matches our single-scene sketch |
| Explain a mechanism (why a stock moved) | **Question → Math → Reveal** | 20-34s | Question hooks test highest for explainers; room for 2 beats |
| Dense/technical (DCF, full valuation) | **Episodic Part 1/2 cliffhanger** | 2×15-20s | Platform pushes ep.2 to ep.1 viewers; splits load without cutting content |
| Build a recurring habit | **Journey/Series** ("Day 47 of…") | 15-20s/ep | Session depth + follow-for-next; fits a recurring anchor character |
| Compliance-sensitive concept | **Practitioner Plain-Language** | 20-30s | Explains mechanics not trades; safest, still authoritative deadpan |
| Same-day news/earnings take | **Identity-Call Reaction** | 15-20s | "If you own X…" filters for invested viewers; fast to produce |

## 2. Hook formulas (first 1-3s = literal on-screen text + VO line 1)

1. **Identity Call** — "If you [own/bought/are still holding] {TICKER} [condition]…" → *"If you bought Palantir under $20, watch this before Friday."*
2. **Front-Loaded Payoff** — state the number/result FIRST → *"This stock is 40% overvalued — here's the math."*
3. **Why/How Question** (best for explainers) → *"Why did this AI chip stock drop 12% on good earnings?"*
4. **Myth-Bust / Contrarian Flip** — name the assumption, flip it → *"Nobody told you this about your 401k fee."*
5. **Cost-Framed Number** — a dollar loss, cold, no lead-in → *"$4,200 mistake."* (zoom-punch on word one)

**Rule:** open on frame 1 with the deadpan character already mid-scene and the hook as the
FIRST spoken word + simultaneous caption pop. Frame 1 IS the thumbnail — one bold number,
high contrast, before any camera move.

## 3. Default beat sheet — Myth-Bust (15-20s)

| Beat | Time | Content |
|---|---|---|
| Hook | 0-2s | Contrarian claim, cold open, caption pops with VO word 1 |
| Setup | 2-6s | One sentence — what people assume |
| Turn | 6-12s | The flip/math/reveal — the payoff, front-loaded as a visual (chart, number slam) |
| Button | 12-18s | Deadpan one-liner; **mirror frame 1** for a loop/rewatch trigger |
| CTA | 18-20s | Exactly one earned CTA (see `short-form-scripting`) |

## 4. VIRAL vs DEAD

| Pattern | Verdict |
|---|---|
| Identity-call hook ("if you own X…") | ✅ specificity > reach; filters for invested viewer |
| Front-loaded payoff (number in frame 1) | ✅ sets the retention-curve ceiling |
| Why/how question for explainers | ✅ highest avg-view hook for edu |
| Episodic Part 1/2 cliffhanger | ✅ platform recommends ep.2 to ep.1 viewers |
| Mirrored first/last frame (loop bait) | ✅ rewatch rate now outranks follower count |
| Mid-video re-hook at 20-30s (videos >20s) | ✅ beats the opening hook's shelf life |
| "POV: you just discovered X" | ❌ 2023 format, dead |
| Generic "Did you know…?" question | ❌ undifferentiated |
| Slow lead-in / logo intro / "hey guys" | ❌ burns the <3s window |
| Over-polished ad-like open | ❌ trips skepticism, esp. in finance |
| Single hook, no loop/re-hook plan | ❌ caps below the ~20-30% rewatch benchmark |
| Brainrot split-screen under finance VO | ❌ gimmicky, hurts comprehension/trust |
| "Day in the life of a trader" flex | ❌ oversaturated |

## Our-stack notes

- **Loop cheaply:** flat-2D poses/backgrounds are modular — end on the open pose/expression (or a sight-gag that only lands on rewatch).
- **Episodic split** reuses the same rig + set: "Part 1: the number everyone's misreading" / "Part 2: the actual math."
- **Identity-call hooks** map directly to our ticker-specific data — name the ticker + condition in VO line 1.

Full write-up + 20 source URLs: [`docs/research/storytelling.md`](../../../docs/research/storytelling.md). Cross-cut cheatsheet: [`docs/research/viral-cheatsheet.md`](../../../docs/research/viral-cheatsheet.md).
