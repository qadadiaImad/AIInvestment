---
name: short-form-scripting
description: >
  Write a tight short-form SCRIPT for @valuewithvalues finance Reels (flat-2D deadpan sketch,
  ~15-20s): beat sheet with word budgets, optimal length + WPM numbers, pattern-interrupt
  cadence, word-by-word caption rules, CTAs that convert vs cringe, and the finance
  compliance disclosure line-item (2025-26, source-backed). Use AFTER picking a structure
  (viral-short-storytelling) and BEFORE VO (viral-voiceover-audio). Triggers: "write the
  script", "script this reel", "how long", "pacing", "caption", "CTA", "call to action".
---

# Short-Form Scripting — Beats, Pacing, Captions, CTAs (2025-26)

Assumes our format: flat-2D deadpan finance sketch, ~15-20s, word-by-word captions, optional
pitched-TTS VO + newsroom bed. Feeds `QuarterlyReport.tsx` (beat lengths) and `gen_qr_audio.py`
(the `LINES` dict). Design **audio-first**: write the VO line + rhythm before locking animation
timing so cuts land on vocal emphasis.

## Beat sheet (template)

| Beat | Window | Purpose | Rule |
|---|---|---|---|
| **Hook** | 0:00-0:02 | Scroll-stop; cold open on claim/visual | Payoff/promise visible before frame 1 ends; no "hey guys" |
| **Setup** | 0:02-0:06 | One sentence of context | 1-2 short sentences; numbers concrete |
| **Turn** | 0:06-0:12 | Mechanism/math/reveal — the payoff | Front-load the number/chart; biggest pattern interrupt lands here |
| **Button** | 0:12-0:16 | Deadpan punchline / "so what" | Land flat, let the visual carry it |
| **CTA** | 0:16-0:20 | One earned ask | Content-matched only (table below) |

For 45-90s content, plant a **second hook at 20-30s** (new visual + fresh line: *"But here's
the part nobody's pricing in…"*) before the next Turn/Payoff.

## Length & pace

| Content | Target | Notes |
|---|---|---|
| Single-insight / single-ticker (default) | **15-20s** (inside the 21-34s sweet-spot band) | one hook, one payoff, one CTA |
| Real comparison / walkthrough | **45-90s** | requires a planted 20-30s re-hook |
| Dense/multi-part (DCF, full fundamentals) | **Part 1/2 at 15-20s each** | cliffhanger cut |

**Don't chase the shortest runtime** — the algorithm scores completion/rewatch %, not
duration. A truncated video that cuts the payoff loses to a slightly longer one watched to the end.

**Speaking pace:** default **135-160 wpm** (≈2.4 words/sec at 145). Reserve 170-200 wpm for a
rare punch-line only. **20s ≈ 48 words total:** Hook ~6-8, Setup ~12-15, Turn ~15-18, Button ~8-10, CTA ~5-6.

## Pattern interrupts

- One real interrupt (cut, zoom, SFX hit, text-slam, contrast beat) **every 3-5s**. <3 in a
  15-20s video feels flat; >5 reads chaotic and buries the numbers.
- **Audit:** scan for any 5s span with zero change and plug it. The **Turn beat** is the home
  for the biggest interrupt (number/chart reveal + sting).

## Captions

- **Word-by-word (karaoke/highlight) captions**, ~250-400ms/word, synced to VO — the dominant
  2025-26 style; beats static blocks on completion/engagement/share.
- **85%+ watch sound-off**; captioned reels get 40-60% higher avg watch time. Captions carry
  retention independent of VO.
- Frame 1 still needs its own baked-in overlay (the "thumbnail" value prop) before VO line 1.

## CTAs — converts vs cringe

| CTA | Verdict |
|---|---|
| "Follow for Part 2" (episodic) | ✅ earned by structure |
| "Save this" (chart/data-dense) | ✅ saves are a strong finance-niche signal |
| Genuine debate prompt ("agree, or is this wrong?") | ✅ drives real comments |
| "Comment [WORD] and I'll DM you…" | ❌ detected + throttled as engagement bait |
| "Comment YES if you agree" | ❌ named engagement-bait, suppressed |
| Generic "follow for more" | ❌ not earned by the video |
| Stacking 2+ CTAs | ❌ dilutes the one ask |

**Exactly one CTA per video**, chosen by what the content earned (episodic→follow; data-dense→save; opinionated→debate).

## Compliance line-item (fold into the script, not an afterthought)

Put **"educational only, not financial advice" on-screen AND spoken within the first ~30s** of
any ticker/trade-specific video (restate in caption; restate later if >30s). End-card-only
disclosure is a top SEC-flagged failure (Dec-2025 risk alert). For our 15-20s sketch: a small
persistent lower-third on ticker-specific videos + one spoken mention in the button/CTA beat
for trade-adjacent takes (not needed for pure concept-education).

Full write-up + source URLs: [`docs/research/scripting.md`](../../../docs/research/scripting.md).
