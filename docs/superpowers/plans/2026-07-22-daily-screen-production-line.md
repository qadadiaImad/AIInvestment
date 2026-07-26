# The Daily Screen — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `python scripts/daily_post.py` emits one dated folder with two hook-variant voiced reels (Trial-Reel A/B), a 3-slide carousel, caption.txt, and manifest.json — from live halal data, verdict withheld to the end, all copy lint-gated.

**Architecture:** Thin orchestrator over four new pure modules (`daily_pick`, `daily_copy`, `align_beats`, plus a `halal_lint` extension) that extend the existing unified factory (`remotion/SlideStoryReel`, `scripts/build_reel_props.py`, `aiinvest.halal_stories`, `scripts/voice/karim_tts.py`, `higgs/_build_v4.py`). `halal-reels/` stays untouched.

**Tech Stack:** Python 3 + pytest (scripts/), Remotion 4 + zod + TS (remotion/), Chatterbox TTS (venv `C:/Users/Amsegt/.venvs/chatterbox`), faster-whisper.

**Spec:** `docs/superpowers/specs/2026-07-22-daily-screen-production-line-design.md`

## Global Constraints

- Copy rails: never "is halal / is haram" phrasing (screen phrasing only); disclaimer footer verbatim `Computed methodology result — not a fatwa · not financial advice`; spoken disclaimer sentence `Educational, not financial or religious advice.`; never name the data vendor; no signals/return promises.
- All copy that reaches a render or caption MUST pass `aiinvest.halal_lint` (existing rails + Task 2's visceral rule). Lint failure aborts the run (exit 2, violating line named).
- Series branding string, exact: `THE DAILY SCREEN` (header chip), trust stinger exact: `Method shown. Dated. Corrected when it changes.`
- Caption: ≤5 hashtags, must contain a natural-search phrase (`is <name> halal`-style) and a send-CTA sentence.
- Media (MP4/WAV) is gitignored — never `git add` them. PNGs/caption/manifest/props are committable but the daily output folder `higgs/daily/` is gitignored too (add the rule in Task 6).
- Python verify: `cd scripts && python -m pytest -q`. Remotion verify: `cd remotion && npx tsc --noEmit`.
- Windows console: set `PYTHONIOENCODING=utf-8` in any subprocess the orchestrator spawns.
- Commit trailer: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`. Branch `feat/multi-sector-research-platform`; no push until the final task.

---

### Task 1: `aiinvest/daily_pick.py` — snapshots, flips, candidate scoring

**Files:**
- Create: `scripts/aiinvest/daily_pick.py`
- Test: `scripts/tests/test_daily_pick.py`

**Interfaces:**
- Consumes: `aiinvest.halal_stories.pick_stories(bundle, alerts=None, top=3)` — alerts items shaped `{"symbol","from","to","old_value","new_value"}`.
- Produces (Task 6 consumes):
  - `verdict_map(bundle) -> dict[str, str]` — symbol → `overall`.
  - `detect_flips(prev_map: dict|None, bundle) -> list[dict]` — alert-shaped list (empty when prev_map is None: first run seeds, never alerts).
  - `news_heat(news_bundle: dict|None, symbols: set[str], now: datetime) -> dict[str, float]` — count of news items mentioning the symbol in `title`/`summary`/`tickers` fields, weighted `1.0` if published <48h before `now`, else `0.3`; missing/unparsable bundle → `{}`.
  - `rank_candidates(bundle, prev_map, news_bundle, posted_log: list[dict], now) -> list[dict]` — top-3 `{"symbol","score","reason","story"}`; `story` is the matching `pick_stories` story dict or a synthesized `{"symbol", "kind":"rotation", "headline_fact": None}` filler when scores run dry. Rotation penalty: symbol present in `posted_log` with `date` within 30 days of `now` → score × 0.1 (flips exempt: flips always outrank everything). `reason` is one plain sentence (e.g. `verdict flipped questionable -> not_halal on 2026-07-22`).
  - `load_history(dir_path) -> (prev_map|None, prev_date|None)` / `save_snapshot(dir_path, date_str, vmap)` / `load_posted_log(path) -> list` / `append_posted(path, entry)` — JSON I/O, `data/halal_history/` layout: `YYYY-MM-DD.json` snapshots + `posted_log.json` (list of `{"symbol","date","folder"}`).

- [ ] **Step 1: Write failing tests**

```python
# scripts/tests/test_daily_pick.py
import datetime as dt
from aiinvest import daily_pick

def _bundle(**verdicts):
    return {"verdicts": {s: {"overall": o, "standards": {}, "business": {}}
                         for s, o in verdicts.items()}}

NOW = dt.datetime(2026, 7, 22, tzinfo=dt.timezone.utc)

def test_verdict_map():
    assert daily_pick.verdict_map(_bundle(WULF="questionable")) == {"WULF": "questionable"}

def test_first_run_no_flips():
    assert daily_pick.detect_flips(None, _bundle(WULF="halal")) == []

def test_flip_detected_and_shaped():
    flips = daily_pick.detect_flips({"WULF": "questionable"}, _bundle(WULF="not_halal"))
    assert flips == [{"symbol": "WULF", "from": "questionable", "to": "not_halal",
                      "old_value": None, "new_value": None}]

def test_unchanged_and_new_symbols_do_not_flip():
    flips = daily_pick.detect_flips({"WULF": "halal"}, _bundle(WULF="halal", GEV="halal"))
    assert flips == []

def test_flip_outranks_everything_even_recently_posted():
    bundle = _bundle(WULF="not_halal", GEV="halal")
    posted = [{"symbol": "WULF", "date": "2026-07-20", "folder": "x"}]
    ranked = daily_pick.rank_candidates(bundle, {"WULF": "questionable"}, None, posted, NOW)
    assert ranked[0]["symbol"] == "WULF" and "flip" in ranked[0]["reason"]

def test_rotation_penalty_demotes_recent_post():
    # two identical extreme-ratio stories; the recently-posted one must rank lower
    v = {"overall": "not_halal", "business": {},
         "standards": {"AAOIFI": {"tests": [{"label": "debt/mcap", "status": "fail",
                                             "ratio": 0.9, "threshold": 0.3, "margin": -0.6}]}}}
    bundle = {"verdicts": {"AAA": v, "BBB": v}}
    posted = [{"symbol": "AAA", "date": "2026-07-10", "folder": "x"}]
    ranked = daily_pick.rank_candidates(bundle, None, None, posted, NOW)
    assert ranked[0]["symbol"] == "BBB"

def test_news_heat_recency_weighting():
    news = {"items": [
        {"tickers": ["GEV"], "published_at": "2026-07-21T12:00:00Z", "title": "x"},
        {"tickers": ["GEV"], "published_at": "2026-06-01T12:00:00Z", "title": "y"}]}
    heat = daily_pick.news_heat(news, {"GEV"}, NOW)
    assert heat["GEV"] == 1.3

def test_history_roundtrip(tmp_path):
    daily_pick.save_snapshot(tmp_path, "2026-07-21", {"WULF": "halal"})
    prev, prev_date = daily_pick.load_history(tmp_path)
    assert prev == {"WULF": "halal"} and prev_date == "2026-07-21"

def test_load_history_empty_dir(tmp_path):
    assert daily_pick.load_history(tmp_path) == (None, None)
```

- [ ] **Step 2: Run to verify failure** — `cd scripts && python -m pytest tests/test_daily_pick.py -q` → import error / failures.
- [ ] **Step 3: Implement `daily_pick.py`** — pure functions; `rank_candidates` builds alerts via `detect_flips`, calls `halal_stories.pick_stories(bundle, alerts=alerts, top=10)`, adds `news_heat` value to each non-flip story score, applies the ×0.1 rotation penalty to non-flip stories whose symbol was posted <30 days ago, sorts, tops up to 3 with rotation fillers (least-recently/never-posted symbols alphabetically), and writes a one-sentence `reason` per candidate. `news_heat` matches a symbol if it appears in the item's `tickers` list OR as a whole word in `title`; `published_at` parsed with `datetime.fromisoformat` (Z → +00:00), unparsable → weight 0.3. History I/O: snapshots are plain `{"date":..., "verdicts": {...}}`; `load_history` picks the lexicographically newest `*.json` excluding `posted_log.json`.
- [ ] **Step 4: Run to verify pass** — same command, all green (whole suite: `python -m pytest -q`).
- [ ] **Step 5: Commit** — `feat(daily): verdict snapshots, flip detection, candidate scoring`

---

### Task 2: `halal_lint.py` — visceral-number rule

**Files:**
- Modify: `scripts/aiinvest/halal_lint.py`
- Test: `scripts/tests/test_halal_lint.py` (append)

**Interfaces:**
- Produces (Tasks 3/6 consume): `lint_visceral(lines: list[str]) -> list[str]` — one violation string per offending line. A line offends when it contains a percentage token (regex `\d+(?:\.\d+)?\s*(?:%|percent)`) but NONE of the money/limit anchors: `$`, `cents`, `of every`, `for every`, `limit`, `cap`, `threshold`, `allowed` (case-insensitive). Lines with no percentage are never violations.

- [ ] **Step 1: Write failing tests** (append to existing test file; read its style first)

```python
def test_visceral_rejects_bare_ratio():
    bad = ["The AAOIFI debt ratio comes in at 56.9%."]
    assert daily := __import__("aiinvest.halal_lint", fromlist=["x"]).lint_visceral(bad)

def test_visceral_accepts_money_analogy():
    from aiinvest.halal_lint import lint_visceral
    ok = ["About 57 percent — that's $57 of every $100 — is borrowed, against a $30 limit."]
    assert lint_visceral(ok) == []

def test_visceral_accepts_limit_comparison():
    from aiinvest.halal_lint import lint_visceral
    assert lint_visceral(["Debt is 14.0% against a 30% cap."]) == []

def test_visceral_ignores_lines_without_percent():
    from aiinvest.halal_lint import lint_visceral
    assert lint_visceral(["Verdict: pass on the halal screen."]) == []
```

(Write the first test in the same plain style as the others — no walrus/`__import__` tricks; shown here compressed.)

- [ ] **Step 2: Verify failure** → `AttributeError: lint_visceral`.
- [ ] **Step 3: Implement** — module-level `_PCT_RE` and `_ANCHOR_RE`; ~10 lines.
- [ ] **Step 4: Verify pass** — `python -m pytest tests/test_halal_lint.py -q`, then full suite.
- [ ] **Step 5: Commit** — `feat(lint): visceral-number rule — every spoken ratio needs a money analogy or limit`

---

### Task 3: `aiinvest/daily_copy.py` — A/B props, VO, caption, carousel kit fields

**Files:**
- Create: `scripts/aiinvest/daily_copy.py`
- Test: `scripts/tests/test_daily_copy.py`

**Interfaces:**
- Consumes: `build_reel_props.build_props(ticker, bundle, story=None) -> dict` (import via `sys.path` sibling or move nothing — `scripts/` root is already on path for `build_reel_props` per its own tests; import as `import build_reel_props`), `halal_lint.lint_halal_script/lint_visceral`, `halal_join.load_halal/screen_card_data`.
- Produces (Task 6 consumes):
  - `build_daily(ticker, bundle, story, date_str) -> dict` with keys:
    - `props_a`, `props_b` — SlideStoryReel props dicts. Both derived from `build_props(...)` then transformed by `_daily_transform`:
      1. `tickerSub` → `f"THE DAILY SCREEN · {date_str}"`; badge unchanged.
      2. Beat order → cliffhanger: keep builder's order but insert a `hook`-kind tease beat immediately before the `stamp` beat: `{"kind":"hook","headline":"Three rulebooks have voted.","sub":"The verdict is one tap away — but first, remember what it's based on.","durationInFrames":90}` with VO line `Three rulebooks have voted. Before the stamp lands — every number you just saw is the reason.`
      3. Endcard `sub` → `f"THE DAILY SCREEN · data as of {date_str}"`; endcard VO line becomes the trust close: `Method shown. Dated. Corrected when it changes. Educational, not financial or religious advice.`
      4. Every VO ratio sentence rewritten viscerally (template: `X percent — that's $X of every $100 — ... against a $Y limit` for mcap-relative ratios; `cents a share` for purification, already present).
      5. Hook A (specific-number): headline from the story's `headline_fact` numbers or worst bar, e.g. `$57 of every $100 here is borrowed money.`; VO opening `Assalamu alaykum. {ticker}. ${r} of every hundred dollars of this company is borrowed money. The screen has a limit. Watch.` Hook B (contrarian): headline `The screeners don't agree on this one.` (split-verdict shape) or `Everyone assumes this one passes.` (fail shape) or `This one looks too clean. We checked anyway.` (pass shape); VO opening in the same register. A and B differ ONLY in `beats[0]` and `vo[0]`.
      6. Flip stories (`story["kind"] == "flip"`) override hook A headline to `This verdict just changed.` and prepend VO `This verdict just changed.` — plus a stamp-basis suffix `was {from} on {prev_date}`.
    - `caption` — string: line 1 natural-search hook (`Is {company_or_ticker} halal? We ran the {date_str} screen.`), body = 2–3 plain sentences with the key number + verdict tease (NOT the verdict itself — the reel reveals it), send-CTA (`Send this to the friend who keeps asking about {ticker}.`), footer disclaimer, exactly 5 hashtags: `#halalinvesting #islamicfinance #halalstocks #muslimmoney` + one topical (`#aistocks` default).
    - `kit_fields` — dict `{"screen_head","screen_body","screen_body2","halal_script"}` for the carousel (same plain-speak register; `halal_script` = the full A-variant VO joined, for archive).
  - Every emitted text passes lint: `build_daily` runs `lint_halal_script` (against `screen_card_data(verdicts, ticker)`) on the joined VO and caption, and `lint_visceral` on all VO lines; any violation → raise `daily_copy.LintError(violations)`.
- Note: `build_daily` must NOT mutate `build_props`' output in place for A when deriving B — `copy.deepcopy` per variant.

- [ ] **Step 1: Write failing tests**

```python
# scripts/tests/test_daily_copy.py — key cases (use the real bundle when present)
import json, pathlib, pytest
from aiinvest import daily_copy

BUNDLE = json.loads((pathlib.Path(__file__).resolve().parents[2]
                     / "web/public/data/halal.json").read_text(encoding="utf-8"))

def test_a_b_differ_only_in_hook():
    d = daily_copy.build_daily("WULF", BUNDLE, None, "2026-07-22")
    a, b = d["props_a"], d["props_b"]
    assert a["beats"][0] != b["beats"][0] and a["vo"][0] != b["vo"][0]
    assert a["beats"][1:] == b["beats"][1:] and a["vo"][1:] == b["vo"][1:]

def test_verdict_withheld_until_stamp():
    d = daily_copy.build_daily("GEV", BUNDLE, None, "2026-07-22")
    kinds = [bt["kind"] for bt in d["props_a"]["beats"]]
    stamp_i = kinds.index("stamp")
    assert stamp_i == len(kinds) - 2                      # stamp is second-to-last
    joined_before = " ".join(d["props_a"]["vo"][:stamp_i]).lower()
    for word in ("pass", "fail", "review"):
        assert word not in joined_before                  # no early verdict leak

def test_caption_rules():
    d = daily_copy.build_daily("ETN", BUNDLE, None, "2026-07-22")
    cap = d["caption"]
    assert cap.count("#") == 5 and "halal" in cap.lower() and "Send this" in cap

def test_all_texts_lint_clean_across_bundle():
    ok, skipped = 0, 0
    for sym in list(BUNDLE["verdicts"])[:40]:
        try:
            daily_copy.build_daily(sym, BUNDLE, None, "2026-07-22"); ok += 1
        except daily_copy.InsufficientDataError:
            skipped += 1
    assert ok >= 20 and ok + skipped == 40   # lint errors would raise LintError

def test_flip_story_changes_hook():
    story = {"symbol": "WULF", "kind": "flip", "headline_fact": "WULF flipped questionable -> not_halal",
             "verdict": "not_halal", "numbers": []}
    d = daily_copy.build_daily("WULF", BUNDLE, story, "2026-07-22")
    assert "changed" in d["props_a"]["beats"][0]["headline"].lower()
```

(Re-raise `build_reel_props.InsufficientDataError` as `daily_copy.InsufficientDataError = build_reel_props.InsufficientDataError` alias.)

- [ ] **Step 2: Verify failure.**
- [ ] **Step 3: Implement.** Template bank as module constants keyed by shape: `flip` / `split` (standards disagree: some binding tests pass, some fail) / `fail` / `pass` / `review`. Shape detection from the props' bars statuses + verdict. Keep the module pure (no file I/O).
- [ ] **Step 4: Verify pass** — `python -m pytest tests/test_daily_copy.py -q`, then full suite.
- [ ] **Step 5: Commit** — `feat(daily): A/B hook props, cliffhanger order, visceral VO, caption + kit copy`

---

### Task 4: `aiinvest/align_beats.py` + `scripts/voice/whisper_align.py`

**Files:**
- Create: `scripts/aiinvest/align_beats.py` (pure), `scripts/voice/whisper_align.py` (thin runner)
- Test: `scripts/tests/test_align_beats.py`

**Interfaces:**
- Produces (Task 6 consumes):
  - `align_beats.apply_timing(props: dict, words: list[dict], fps=30, pad=12, min_frames=60) -> dict` — new props (deepcopy) where each beat's `durationInFrames` is derived from its VO line's word span, and `captions` is filled with `{"text","fromMs","toMs"}` per VO line. `words` items: `{"word": str, "start": float, "end": float}` (seconds — the faster-whisper shape).
  - Matching: normalize tokens (`lower`, strip non-alphanumerics); walk the word list once, consuming greedily per VO line in order; a line's span = first..last matched word. If <60% of a line's tokens match, fall back for THAT line to proportional allocation (line's share of total VO chars × remaining audio duration). Beat N's duration = (line N end − line N start) + pad frames gap, clamped to ≥ `min_frames`; the final beat absorbs the remainder so `sum(durations) == ceil(audio_end*fps) + pad`.
  - `whisper_align.py` CLI: `python scripts/voice/whisper_align.py <wav> --out words.json` — runs faster-whisper `small.en`, `compute_type="int8"`, `word_timestamps=True`, dumps `[{"word","start","end"},...]`. Run with the chatterbox venv python (it has faster-whisper); document that in the module docstring.

- [ ] **Step 1: Write failing tests** — fixture words list built synthetically (no audio): 3 VO lines × 4 words each at known times; assert per-beat durations match spans + pad, min clamp honored (make line 2 span tiny), final beat absorbs tail, captions ms values correct, beats/vo length mismatch raises `ValueError`, unmatched line falls back proportionally (feed garbage tokens for line 3).
- [ ] **Step 2: Verify failure.** — `python -m pytest tests/test_align_beats.py -q`
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Verify pass**, full suite.
- [ ] **Step 5: Commit** — `feat(daily): whisper word-span → beat durations + caption spans`

---

### Task 5: Remotion — `voiceSrc` + caption track in `SlideStoryReel`

**Files:**
- Modify: `remotion/src/slides/slideProps.ts` (add `voiceSrc: z.string().optional()`)
- Modify: `remotion/src/compositions/SlideStoryReel.tsx` (when `voiceSrc` present: `<Audio src={staticFile(voiceSrc)} />`; when `captions` non-empty: bottom-third caption spans rendered per `fromMs/toMs` using `useCurrentFrame()/fps` — style: JetBrains Mono 34px, ink on `#0009` pill, matching the halal-reels caption look)
- Test: compile + composition listing (no jest in remotion/)

**Interfaces:**
- Consumes: props JSON from Task 3/4 with `voiceSrc` like `"daily/2026-07-22_WULF/voice_A.wav"` — Task 6 copies WAVs under `remotion/public/daily/...` so `staticFile` resolves.
- Produces: rendering `SlideStoryReel` with voiced props plays audio and shows word-timed captions; VO-less fixtures (`wulf_slides.json`) still render identically (field optional, default absent).

- [ ] **Step 1: Add schema field** + `npx tsc --noEmit` (expect clean — additive).
- [ ] **Step 2: Wire Audio + captions layer** in the composition; read the existing component structure first and follow its patterns (Series, AbsoluteFill, theme constants).
- [ ] **Step 3: Verify** — `cd remotion && npx tsc --noEmit` clean; `npx remotion compositions src/index.ts` still lists `SlideStoryReel`; render 90 frames of the untouched `wulf_slides.json` fixture (`npx remotion render SlideStoryReel out.mp4 --props=src/fixtures/wulf_slides.json --frames=0-89`) to prove no regression, then delete the MP4.
- [ ] **Step 4: Commit** — `feat(remotion): optional voiceSrc audio + whisper-timed caption track in SlideStoryReel`

---

### Task 6: `scripts/daily_post.py` — the one command

**Files:**
- Create: `scripts/daily_post.py`
- Modify: `.gitignore` (add `higgs/daily/` and `data/halal_history/`)
- Test: `scripts/tests/test_daily_post.py` (pure helpers only: folder naming, manifest assembly, candidate-prompt formatting)

**Interfaces:**
- Consumes everything above. CLI: `python daily_post.py [--auto] [--ticker X] [--dry-run] [--skip-refresh] [--skip-carousel]`.
- Pipeline (each step prints one progress line; any failure → named abort, temp dir removed):
  1. Freshness: read `web/public/data/halal.json` `generated_at`; if ≥24h old and not `--skip-refresh`, run `python pull_halal.py` then `python export_halal.py` (subprocess, cwd=scripts, `PYTHONIOENCODING=utf-8`); re-check, abort if still stale.
  2. History: `load_history(data/halal_history)`, `save_snapshot(...)` for today.
  3. Candidates: `rank_candidates(...)` with the news bundle from `web/public/data/news.json` if present; print top-3 with reasons; interactive `input()` pick (Enter=1) unless `--auto`/`--ticker`.
  4. Copy: `daily_copy.build_daily(...)`; `--dry-run` stops here printing VO/caption and exits 0.
  5. Voice: write the two VO scripts (all lines joined with blank lines) to the temp dir; call `karim_tts.py --text-file daily_a <path> --out <tmp>` and `daily_b` likewise via the chatterbox venv python `C:/Users/Amsegt/.venvs/chatterbox/Scripts/python.exe`.
  6. Align: `whisper_align.py` per WAV → `align_beats.apply_timing` per variant; write `props_A.json`/`props_B.json` with `voiceSrc` set; copy WAVs to `remotion/public/daily/<folder>/`.
  7. Render: `npx remotion render SlideStoryReel <tmp>/daily_A.mp4 --props=<tmp>/props_A.json` (cwd=remotion), then B.
  8. Carousel (skip with `--skip-carousel`): read `higgs/_build_v4.py`'s kit-driven entry point and `higgs/reels_2026-07-21_kit.md`'s section format FIRST; emit a minimal one-ticker kit md into the temp dir from `kit_fields`, invoke `_build_v4.py` the same way `make_reel.py` does, collect the 3 PNGs.
  9. Finalize: move temp dir → `higgs/daily/YYYY-MM-DD_TICKER/`; write `manifest.json` (ticker, reason, scores, data `generated_at`, `inputs_asof`, lint OK, seeds, files, posting instructions: `B = Trial Reel first, A = main slot`); `append_posted(...)`.
- Produces: the folder contract Studio indexes; `manifest.json` schema documented in the module docstring.

- [ ] **Step 1: Write failing tests for the pure helpers** — `folder_name(date_str, ticker)`, `build_manifest(...)` field presence, `format_candidates(...)` 3-line output.
- [ ] **Step 2: Verify failure. Implement helpers + orchestrator.** Keep subprocess calls in small functions so the helpers stay testable without GPU.
- [ ] **Step 3: Verify** — full pytest suite green; `python daily_post.py --dry-run --ticker WULF --skip-refresh` prints copy and exits 0 (no GPU touched).
- [ ] **Step 4: Commit** — `feat(daily): one-command daily post orchestrator (The Daily Screen)`

---

### Task 7: Wet run + parity + push

- [ ] **Step 1:** Full run: `python daily_post.py --auto` (GPU TTS ~3-5 min, two renders). Confirm the output folder contains 2 MP4s, 3 PNGs, caption.txt, manifest.json, props JSONs.
- [ ] **Step 2:** Open first-frame stills of `daily_A.mp4` vs the owner-validated look (`higgs/wulf_f1.png` reference family) — header chip, Fraunces hook scale, footer present; verdict stamp appears only near the end (scrub ~80% mark). Listen-check one WAV for the spoken disclaimer.
- [ ] **Step 3:** Studio smoke: confirm the folder appears in Studio's gallery (filename-convention indexer).
- [ ] **Step 4:** Update `remotion/README_FACTORY.md` with a "Daily line" section (the one command + folder contract). Commit docs; push the branch. Report to owner with the folder path and what to post where (B → Trial Reel, A → main).

---

## Self-Review

1. **Spec coverage:** named series + withheld verdict → T3 (order test) + T7 scrub check; hook A/B → T3 + T6 render×2; visceral lint → T2 + T3 gate; flips/trust → T1 + T3 flip templates + stinger; sends/SEO caption → T3 caption rules test; freshness gate/snapshots → T6/T1; dry-run → T6; atomic temp-dir → T6; carousel → T6 step 8; Studio pickup → T7; media gitignore → global + T6 .gitignore.
2. **Placeholders:** T6 step 8 directs the implementer to read `_build_v4.py`/kit format in-tree before wiring — deliberate (same pattern as the unification plan), the kit fields themselves are fully specified in T3. No TBDs remain.
3. **Type consistency:** alert shape (T1) matches `pick_stories`; `build_daily` return keys used identically in T6; `words` shape (T4) matches whisper runner output; `voiceSrc` path convention consistent between T5 and T6.
