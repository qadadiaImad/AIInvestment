# Halal Generation Framework — Design Spec (2026-07-21)

> Approved by owner 2026-07-21 (brainstorm: 4 batched questions + design walkthrough).
> Adds a "halal mode" to the existing kit-driven content pipeline: halal-screen carousels and
> Karim-voiced VO reels, with a locked, canonical cloned voice. Educational content only —
> the non-fatwa/not-advice rails are enforced in code, not just convention.

## 1. Goals / non-goals

**Goals (v1):**
- G1 — A locked, reproducible "Karim voice": cloned from the validated pilot video, used for all
  halal VO via Higgsfield `text2speech_v2` (`voice_type=element`, locked `voice_id`).
- G2 — Halal screen **carousels**: kit-driven, verdict badge + worked-math "screen card" slide,
  rendered by the existing `_build_v4.py` (extended, not forked).
- G3 — Karim **VO reels**: kit-driven scripts voiced with the canonical voice over slide frames,
  assembled by the untouched `make_reel.py`.
- G4 — Rails enforced programmatically: "passes the AAOIFI screen" phrasing, estimated-purification
  wording, non-fatwa footer, AI-persona disclosure note in captions.

**Non-goals (v1):** weekly-ritual generator · talking-head (Marketing Studio) videos · French ·
Studio UI changes (posts surface via existing filename conventions) · auto-posting · wiring
`pull_halal`/`export_halal` into `refresh_all.py` (separate small task, not this spec).

## 2. Voice canon — "Karim Voice Kit"

**Files:** `course/persona/VOICE.md` (the canon) · `course/persona/voice/karim_sample.wav`
(extracted sample) · `course/persona/higgsfield-ids.json` (gains `voice` block).

**Clone workflow (one-time):**
1. Extract audio: `ffmpeg -i course/persona/video/intro_desk.mp4 -vn -acodec pcm_s16le -ar 44100
   course/persona/voice/karim_sample.wav` (~15s sample).
2. **Owner manual step (web UI):** create a cloned voice in Higgsfield from `karim_sample.wav`
   (CLI has no `voices create`; cloned voices appear in `higgsfield voices list` as
   Voice Type `element`).
3. Lock the returned id: `higgsfield-ids.json` → `voice: {id, type: "element", variant:
   "elevenlabs", source: "intro_desk.mp4", created}`; mirrored in `VOICE.md`.
4. All VO calls: `higgsfield generate create text2speech_v2 --prompt "<script>" --variant
   elevenlabs --voice_id <id> --voice_type element --wait`.

**Fallback chain (recorded in VOICE.md):** if the 15s-sample clone quality is rejected at pilot
QA → pick the nearest preset from `higgsfield voices list` and lock it (`voice_type=preset`)
instead. The pipeline reads the voice config from `higgsfield-ids.json` either way — no code
difference between clone and preset.

**Delivery canon (VOICE.md, enforced by script-composer lint where mechanical):** calm educator,
English v1. ~150 wpm; short declarative sentences; micro-pause (comma or ellipsis) before each
key number; no hype inflection, no exclamation stacks; numbers spoken with their unit and date;
closes with the spoken line "Educational, not financial or religious advice." Script text is
written to be *heard*: digits as words where natural, tickers spelled ("N-V-D-A" only when
ambiguous), no URLs.

## 3. Kit format extension (extend `reels_<date>_kit.md`, backward compatible)

Inside the existing per-reel fenced-python CFG block, two new optional keys:

```python
mode = "halal"            # activates halal rendering + VO composition for this entry
halal_script = """
Hook line... <pause> key number... takeaway... Educational, not financial or religious advice.
"""
```

- Numbers are **never hand-copied** into the kit: at render time the builder joins
  `web/public/data/halal.json` by ticker and pulls verdict, per-standard tests
  (ratio/threshold/margin), business-activity line, and purification.
- `scripts/aiinvest/kit_md.py::parse_cfg` passes unknown keys through today's dict shape — add
  explicit tests that `mode`/`halal_script` round-trip. `studio/src/main/kit.ts` requires no
  change (extra CFG keys are simply not displayed in v1).

## 4. Carousel — `_build_v4.py` extension

- **Verdict badge (all posts):** `load_halal()` reads `web/public/data/halal.json`
  tolerate-missing; when the ticker has a verdict, `header()` renders a small pill
  (`halal` emerald / `questionable` amber / `not_halal` muted red / absent → nothing), text
  "AAOIFI screen: PASS|REVIEW|FAIL" — never the word-only "halal is/isn't".
- **Screen-card slide (`mode="halal"` posts):** slide 2 replaced by the worked-math card —
  3 standards rows (AAOIFI/FTSE/MSCI: ratio vs threshold vs margin, pass/fail mark), one
  business-activity line (with impermissible-% or "undisclosed"), one purification line
  ("estimated ~$X.XX/share"), `inputs_asof` timestamp rendered on-card (Rule: the stamp is a
  visible, branded element). Visual parity target: `web/components/HalalCard.tsx`; reuses the
  existing v4 design system (#0A0D12 / #34D399 / Fraunces-Inter-JetBrains).
- Slide 3 (takeaway) gains the fixed footer: "Computed methodology result — not a fatwa, not
  financial advice." Output naming unchanged (`v4_<tk>_1_hook/2_data/3_takeaway.png`, 1080×1350)
  → Studio gallery indexes them with zero changes.

## 5. Karim VO reel

- Frames: 9:16 (1080×1920) variants of the same hook/screen/takeaway renders (builder emits both
  sizes for `mode="halal"` entries).
- Voice: `halal_script` → canonical voice (Section 2) → voice URL recorded in
  `higgs/reels_manifest.json` (existing shape: per-entry hero/voice URLs + top-level `voice`
  field documents the canon id).
- Assembly: existing `higgs/make_reel.py <TK> <hero_url> <voice_url>` untouched (ffmpeg
  ken-burns, `-loop 1` + `-frames:v` cap, <40MB guard). Hero animation optional per entry:
  reuse desk-set/hero art (cheap) or full hero flow (~18 credits).

## 6. Guards & error handling

- Halal mode refuses to render if `halal.json` is absent (actionable message: run
  `pull_halal.py` + `export_halal.py`); warns if `generated_at` older than 7 days.
- Tickers without verdicts: skipped with a printed list (never silently dropped).
- Script-composer lint (code, not convention): rejects scripts containing "is halal"/"is haram"
  claims about a ticker (requires screen-phrasing), requires the closing disclaimer line,
  requires ≥1 number that matches the joined halal data for that ticker (no invented figures).
- Voice step fails loudly if `higgsfield-ids.json` has no `voice` block.

## 7. Testing (TDD, pytest in `scripts/tests/`)

- `test_kit_md_halal.py` — `mode`/`halal_script` parsing round-trip; legacy kits unaffected.
- `test_halal_join.py` — builder's halal-data join on a fixture `halal.json` (verdict, margins,
  purification, missing-ticker skip, stale-warning, absent-file refusal).
- `test_screen_card.py` — rendered HTML contains: 3 standards rows, margin values, purification
  "estimated" wording, `inputs_asof` stamp, footer line; badge tone mapping.
- `test_halal_script_lint.py` — rails enforcement (phrasing rejection, disclaimer required,
  number-consistency check).
- Voice generation + ffmpeg assembly: manual QA (existing pattern; visual/audio judgment).

## 8. Open items / constraints

- Voice-element creation is a **manual owner step** in the Higgsfield web UI (CLI limitation
  verified 2026-07-21: `voices` supports list/get only).
- Higgsfield balance at spec time: ~20 credits — enough for voice tests + a pilot VO reel without
  hero regeneration; content-cadence production needs a top-up (owner decision, out of scope).
- Caption/CTA posture for the halal handle (CTA-to-Skool from day one) is a content-ops decision
  recorded in the phase-2 briefing; kit captions carry it, not this framework's code.
