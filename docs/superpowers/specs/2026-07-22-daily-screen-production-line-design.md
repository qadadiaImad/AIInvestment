# The Daily Screen — one-command daily post production line (design)

**Date:** 2026-07-22 · **Status:** approved by owner (option "Approved, build it")
**Goal:** `python scripts/daily_post.py` produces, in one run, everything needed for one
Instagram post: two hook-variant voiced reels (Trial-Reel A/B), a matching 3-slide
carousel, a caption file, and a provenance manifest — all from live halal-screen data,
with the five research-backed upgrades built in as code, not habits.

Research grounding: `docs/superpowers/research/` (niche brief + @musliminvesting
profile, 2026-07-22 agents). The five upgrades this line automates:

1. **Named series, verdict withheld** — "THE DAILY SCREEN · [TICKER]" branding; the
   pass/fail stamp is the second-to-last beat, never revealed early.
2. **Hook A/B for Trial Reels** — two renders per day differing only in the opening
   beat + opening VO sentence (A = specific-number hook, B = contrarian hook).
3. **Visceral numbers** — a lint rule rejects any VO ratio without a plain-money
   analogy or explicit limit comparison in the same beat.
4. **Trust weapon** — daily verdict snapshots; any verdict flip outranks everything
   and gets the "Verdict changed" treatment; endcard carries the trust stinger
   "Method shown. Dated. Corrected when it changes."
5. **Sends + caption SEO** — caption written as natural search language
   ("is TeraWulf halal…"), a send-to-a-friend CTA, ≤5 hashtags, non-fatwa footer.

## Architecture

Extends the existing unified factory (`remotion/SlideStoryReel` +
`scripts/build_reel_props.py`); `halal-reels/` remains untouched read-only reference.
New orchestrator + four small pure modules, TDD'd:

```
scripts/daily_post.py                 ← orchestrator (thin; sequencing + CLI only)
scripts/aiinvest/daily_pick.py        ← flip detection + candidate scoring (pure)
scripts/aiinvest/daily_copy.py        ← VO/caption/kit templates + hook A/B (pure)
scripts/aiinvest/align_beats.py       ← whisper words → beat durations + captions (pure core)
scripts/aiinvest/halal_lint.py        ← + visceral-number rule (extend existing)
remotion/src/slides/slideProps.ts     ← + optional voiceSrc field (additive)
remotion/src/compositions/SlideStoryReel.tsx ← play Audio when voiceSrc present
```

## Pipeline (one run)

1. **Freshness gate.** If `web/public/data/halal.json` `generated_at` < 24h old, reuse;
   else run the existing pull/export chain. Abort (exit 2, named reason) if the bundle
   is missing or stale after refresh. Every artifact carries `inputs_asof`.
2. **Snapshot + flip detection** (`daily_pick`). Copy today's verdicts to
   `data/halal_history/YYYY-MM-DD.json` (gitignored). Diff against the most recent
   prior snapshot: any ticker whose `overall` changed is a **flip**.
3. **Candidate scoring** (`daily_pick`). Score = flips first (absolute priority),
   then news-heat (ticker mentions in the news bundle, recency-weighted), then
   `pick_stories` story-worthiness, minus a rotation penalty (posted within 30 days,
   from `data/halal_history/posted_log.json`). Print top-3 with one-line reasons;
   interactive: Enter = #1, `2`/`3` or a ticker string overrides; `--auto` takes #1
   silently; `--ticker X` bypasses scoring.
4. **Copy build** (`daily_copy`). From `screen_card_data` numbers, generate:
   - beat list in cliffhanger order: `hook → business/donut or bars → bars →
     cliffhanger tease → stamp → endcard` (stamp = verdict reveal, beat N-1);
   - **two hook variants**: A specific-number ("$57 of every $100 in this company is
     borrowed money."), B contrarian ("Every screener passes this stock. One ratio
     disagrees."); body beats identical;
   - VO lines per beat (template bank keyed by verdict shape: clean pass / ratio fail /
     split standards / flip), every ratio wrapped in a money analogy;
   - flip days use the "Verdict changed" template set (old verdict, date, what moved);
   - caption.txt (natural-search phrasing, send CTA, ≤5 hashtags, non-fatwa footer);
   - carousel kit fields (screen_head/screen_body/screen_body2) for `_build_v4`.
   All VO + caption text passes `halal_lint` (existing rails + new visceral rule).
   Lint failure = abort with the violating line named; never render unclean copy.
5. **Voice** (reuse `scripts/voice/karim_tts.py` text-file mode; Chatterbox canon:
   seeds base 7 + chunk index, exaggeration 0.4, cfg 0.5). Two takes: `voice_A.wav`,
   `voice_B.wav` (shared body text, different opening sentence).
6. **Sync** (`align_beats`). faster-whisper (small.en, int8) per take → word
   timestamps → per-beat `durationInFrames` (beat boundary = end of its last VO word
   + breathing pad, floor/ceil clamps) + `captions[]` spans. Rewrites the props JSONs.
   Target total 30–45s; template word budgets keep VO ~85–110 words.
7. **Render.** `npx remotion render SlideStoryReel` twice → `daily_A.mp4`,
   `daily_B.mp4` (1080×1920, 30fps). Carousel: existing `_build_v4.py` halal mode →
   3 PNGs. (No 16:9 in the daily line; explainers keep that.)
8. **Output.** `higgs/daily/YYYY-MM-DD_TICKER/` containing the two MP4s, 3 PNGs,
   `caption.txt`, `props_A/B.json`, `voice_*.wav`, and `manifest.json` (ticker, scores
   and why picked, data stamps, lint results, seeds, file list, and posting
   instructions: B → Trial Reel, A → main slot, or winner-takes-slot). Studio's
   filename-convention indexer picks the folder up. Append to `posted_log.json`.

## Error handling

- Any step failure aborts the run with a named reason and leaves no partial folder
  (build into a temp dir, move into `higgs/daily/` only on success).
- Existing discipline preserved: props builder's exit-2-on-insufficient-data; lint
  hard-gates all user-facing text; GPU steps report progress lines.
- `--dry-run`: stop after step 4 with props + copy printed (no GPU, no render) — the
  cheap daily sanity check.

## Testing

- pytest (TDD): flip detection (incl. first-run/no-history), scoring order + rotation
  penalty, template outputs lint-clean for all verdict shapes across the real 128-name
  bundle, visceral-number rule positive/negative cases, duration math from a fixture
  timestamp file (sums, clamps, monotonicity).
- `npx tsc --noEmit` for the additive schema change; one manual parity render checked
  against the owner-validated WULF look before first real use.

## Rails (unchanged, enforced)

Never "is halal/is haram" (screen phrasing); non-fatwa footer; spoken disclaimer;
never name the data vendor ("a fundamental-value model"); "a read, not a call"; no
signals or return promises. Owner rules: all build subagents on Sonnet; media
(MP4/WAV) stays gitignored; PNGs + caption + manifest committable.

## Out of scope (this pass)

16:9 variants, French, auto-posting to Instagram (manual by owner), Higgsfield
talking-bubble clips (schema stays ready), scheduling (owner runs the command).
