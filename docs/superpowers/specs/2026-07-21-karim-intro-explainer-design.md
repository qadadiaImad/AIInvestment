# Karim Intro Explainer — Design Spec (2026-07-21)

> Approved by owner 2026-07-21 (brainstorm: format/visual/concepts questions + design walkthrough).
> A ~90s "What is halal finance, in human words" video narrated by the Karim cloned voice
> (Chatterbox), built in the existing `halal-reels/` Remotion project, rendered in BOTH 9:16
> and 16:9. Zero generation credits.

## Content (5 beats, ~205-word script)

1. **Hook (~10s)** — invest without trading away what you believe.
2. **What halal finance is (~20s)** — a filter: avoids interest-based earnings, haram
   industries, gambling-like bets.
3. **The screen (~30s)** — three questions, $100 analogy: what it sells (impure income ≈5%
   cap) · how much it borrows (≈$30 per $100 cap) · where cash sits (interest caps).
4. **Purification (~18s)** — the impure slice, computed per share, given to charity;
   "screen, own, purify."
5. **Close (~10s)** — computed results, not fatwas; ask a scholar; spoken disclaimer line.

Rails: no "is halal/haram" verdict claims; spoken close "Educational, not financial or
religious advice." — enforced by a new `lint_concept_script()` (phrasing + disclaimer checks;
the per-ticker number-anchor check does not apply to concept scripts).

## Visuals

- **Podcast bubble**: Karim desk-set portrait (`course/persona/reference/01_desk_front.png` →
  `halal-reels/public/karim.png`) in a circular frame, breathing scale + pulsing emerald ring,
  anchored bottom-right (9:16) / bottom-left (16:9). Present all video — he is the narrator.
- Center stage: existing motion kit (Slam/Kicker/Caption/CoinDrop/Stamp/EndCard) + one new
  **ThreeQuestions** diagram (three tiles sliding in: SELLS? / BORROWS? / CASH? with mini
  visualizations). Brand system unchanged.

## Build

- `scripts/voice/karim_tts.py` gains `--text-file NAME PATH` mode (kit-independent;
  concept-lint gate; same chunking/seeds/engine) — script source `halal-reels/public/intro_script.txt`.
- Whisper word timestamps appended to `halal-reels/word_timestamps.json` (key `intro`);
  scene boundaries beat-synced like the ticker reels.
- New `halal-reels/src/IntroScenes.tsx` (shared, `wide` prop) + comps `IntroReel`
  (1080×1920) and `IntroWide` (1920×1080) registered in Root.
- Outputs: `higgs/reel_intro_2026-07-21.mp4` (gallery-indexed) and
  `higgs/intro_wide_2026-07-21.mp4`; caption appended to `higgs/reels_2026-07-21.txt`.

## Out of scope

Lip-sync (needs paid avatar video) · burned captions (kinetic type carries the words) ·
French variant (later) · Higgsfield spend (none).
