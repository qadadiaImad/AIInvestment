# Halal Generation Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "halal mode" to the kit-driven content pipeline: halal-screen carousels + Karim-voiced VO reels with a locked cloned voice, per `docs/superpowers/specs/2026-07-21-halal-generation-design.md`.

**Architecture:** Extend (not fork) the existing chain: `reels_<date>_kit.md` (new `halal_script` key) → `kit_md.py` parse → new `halal_join.py` (joins `web/public/data/halal.json`) + `halal_lint.py` (rails enforcement) → `_build_v4.py` (badge + screen-card slide + 9:16 reel frames) → new `_gen_halal_voice.py` (TTS via locked voice, manifest update) → untouched `make_reel.py` assembly (tiny `--skip-frames` switch).

**Tech Stack:** Python 3.14, pytest (run from `scripts/`), Playwright (render), ffmpeg, Higgsfield CLI (`~/.higgsfield/bin/higgsfield.exe`, on PATH as `higgsfield`).

## Global Constraints

- Phrasing rails (enforced in code): scripts/slides say "passes the AAOIFI screen" — NEVER "X is halal"/"X is haram" as a claim; purification always "estimated"; takeaway/footer line: `Computed methodology result — not a fatwa · not financial advice`; spoken scripts end with `Educational, not financial or religious advice.`
- Naming conventions preserved: carousel slides `v4_<tkl>_{1_hook,2_data,3_takeaway}.png` (1080×1350); reel frames `reel_<tkl>_{hook,data,takeaway}.png` (1080×1920, hook transparent); reels `reel_<tkl>_<date>.mp4`.
- Design system: bg `#0A0D12`, emerald `#34D399`, amber `#E0A23B`, muted red `#C25E5E`, gray `#8893A4`; fonts Fraunces/Inter/JetBrains Mono (existing `BASE` css).
- `halal.json` is optional repo-wide: tolerate-missing everywhere EXCEPT halal-mode rendering, which refuses with an actionable message; warn if `generated_at` older than 7 days.
- English only. No Studio changes. No auto-posting. Voice config lives in `course/persona/higgsfield-ids.json` under key `voice`; fail loudly if unset.
- Spec deviations (approved rationale): halal activation = presence of `"halal_script"` CFG key (spec's `mode="halal"` collides with the existing data-slide `"mode"` key); `make_reel.py` gains an optional backward-compatible 4th arg `--skip-frames` (spec said untouched, but its step 1 hard-calls `_build_reel_stock.py`, which has no CFG for halal tickers).
- All pytest commands run from `scripts/` (`cd scripts && python -m pytest tests/<file> -v`).

---

### Task 1: Karim Voice Kit assets (`VOICE.md`, sample extraction, ids)

**Files:**
- Create: `course/persona/voice/karim_sample.wav` (extracted)
- Create: `course/persona/VOICE.md`
- Modify: `course/persona/higgsfield-ids.json` (add `voice` block)

**Interfaces:**
- Produces: `higgsfield-ids.json` key `voice = {"id": null, "type": "element", "variant": "elevenlabs", "source": "video/intro_desk.mp4", "created": null}` — Task 6 reads exactly this shape and fails while `id` is null (until the owner performs the web-UI clone step).

- [ ] **Step 1: Extract the voice sample**

```bash
cd "C:/Users/Amsegt/Downloads/AIInvestment-feat-multi-sector-research-platform/AIInvestment-feat-multi-sector-research-platform"
mkdir -p course/persona/voice
ffmpeg -y -i course/persona/video/intro_desk.mp4 -vn -acodec pcm_s16le -ar 44100 -ac 1 course/persona/voice/karim_sample.wav
```

- [ ] **Step 2: Verify the sample**

Run: `ffprobe -v error -show_entries format=duration -of csv=p=0 course/persona/voice/karim_sample.wav`
Expected: a duration ≈ `15.0` (±2s), file > 500KB.

- [ ] **Step 3: Write `course/persona/VOICE.md`**

```markdown
# Karim Voice Canon

## Locked voice (the ONLY voice for Karim VO)
- Source sample: `voice/karim_sample.wav` — extracted from `video/intro_desk.mp4` (the owner-validated pilot).
- Clone (one-time, owner, Higgsfield web UI): create a cloned voice from the sample; it then
  appears in `higgsfield voices list` with Voice Type `element`. Record its id in
  `higgsfield-ids.json` → `voice.id` (and `created` date). CLI cannot create clones (verified
  2026-07-21: `voices` supports list/get only).
- Usage (all VO): `higgsfield generate create text2speech_v2 --prompt "<script>"
  --variant elevenlabs --voice_id <voice.id> --voice_type element --wait`
- Fallback (if clone QA fails): pick the nearest preset from `higgsfield voices list`, set
  `voice.type = "preset"` + the preset id. Pipeline code reads the config either way.

## Delivery canon (calm educator, English)
- ~150 wpm; short declarative sentences; one idea per sentence.
- Micro-pause (comma or "...") immediately BEFORE each key number.
- Numbers spoken with unit and date ("thirty percent cap", "as of July twenty-first").
- No hype inflection, no exclamation stacks, no slang. Warm, unhurried, certain.
- Script text is written to be heard: digits as words where natural; no URLs; ticker letters
  spelled out only when ambiguous.
- Every script ends with the spoken line: "Educational, not financial or religious advice."
```

- [ ] **Step 4: Add the `voice` block to `course/persona/higgsfield-ids.json`**

Edit the JSON (top level) to add:

```json
"voice": {
  "id": null,
  "type": "element",
  "variant": "elevenlabs",
  "source": "video/intro_desk.mp4",
  "created": null,
  "note": "null id = owner has not yet created the cloned voice in the Higgsfield web UI from voice/karim_sample.wav"
}
```

- [ ] **Step 5: Commit**

```bash
git add course/persona
git commit -m "feat(persona): Karim voice kit — canonical sample, VOICE.md delivery canon, voice config"
```

---

### Task 2: kit parsing — `halal_script` key

**Files:**
- Modify: `scripts/aiinvest/kit_md.py:72-102` (`parse_cfg`)
- Test: `scripts/tests/test_kit_md_halal.py`

**Interfaces:**
- Produces: `parse_cfg(md, ticker)` dict gains key `"halal_script": str|None` (raw multiline string, `\"` unescaped). Tasks 5 and 6 read `cfg["halal_script"]`; `None` ⇒ not a halal post.

- [ ] **Step 1: Write the failing test** (`scripts/tests/test_kit_md_halal.py`)

```python
from aiinvest.kit_md import parse_cfg

KIT = '''
## REEL 1 — WULF
```python
"WULF":{ "hero":"hero_wulf_2026-07-21.png", "logo":"logo_WULF.png", "ex":"NASDAQ",
  "kick":"HALAL SCREEN", "head":"Bitcoin money, screened", "sub":"38 percent of revenue is mining.",
  "data_kick":"THE MATH", "data_title":"AAOIFI screen", "data_cap":"", "data_foot":"", "mode":"disc",
  "rows":[], "tk_kick":"TAKEAWAY", "big":"38", "unit":"%", "tk_label":"MINING REVENUE",
  "tk_body":"Purification, estimated.", "src":"site",
  "halal_script":"TeraWulf makes real money... but thirty-eight percent of it is bitcoin mining.
The AAOIFI screen flags it. Purification, estimated, about thirteen cents a share.
Educational, not financial or religious advice." }
```
'''

def test_halal_script_parsed_multiline():
    c = parse_cfg(KIT, "WULF")
    assert c["halal_script"].startswith("TeraWulf makes real money")
    assert "thirteen cents a share" in c["halal_script"]
    assert c["halal_script"].rstrip().endswith("religious advice.")

def test_halal_script_absent_is_none():
    md = '"NVDA":{ "hero":"h.png", "kick":"K" }'
    assert parse_cfg(md, "NVDA")["halal_script"] is None

def test_legacy_fields_unchanged():
    c = parse_cfg(KIT, "WULF")
    assert c["hook"]["kick"] == "HALAL SCREEN"
    assert c["data"]["mode"] == "disc"
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd scripts && python -m pytest tests/test_kit_md_halal.py -v`
Expected: FAIL — `KeyError: 'halal_script'`.

- [ ] **Step 3: Implement** — in `parse_cfg`'s returned dict (after `"src": _field(block, "src"),`) add:

```python
        "halal_script": _field(block, "halal_script"),
```

- [ ] **Step 4: Run tests (new + existing kit tests)**

Run: `cd scripts && python -m pytest tests/test_kit_md_halal.py tests/ -k kit -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/aiinvest/kit_md.py scripts/tests/test_kit_md_halal.py
git commit -m "feat(kit): parse optional halal_script CFG key (activates halal mode)"
```

---

### Task 3: halal data join — `scripts/aiinvest/halal_join.py`

**Files:**
- Create: `scripts/aiinvest/halal_join.py`
- Create: `scripts/tests/fixtures/halal_fixture.json`
- Test: `scripts/tests/test_halal_join.py`

**Interfaces:**
- Produces:
  - `load_halal(path, now=None) -> (dict verdicts, list[str] warnings)` — raises `HalalDataMissing(msg)` if the file is absent; warning string when `generated_at` > 7 days old vs `now` (UTC datetime, default now).
  - `screen_card_data(verdicts, tk) -> dict|None` with keys: `overall` (str), `badge` (`{"text","color"}`), `standards_rows` (list of `{"name","ok","binding_label","ratio","threshold","margin"}` — one row per standard, the *binding* test = smallest margin), `business_line` (str), `purification_line` (str), `inputs_asof` (str). `None` when ticker absent.
- Tasks 4, 5, 6 consume exactly these names.

- [ ] **Step 1: Write the fixture** (`scripts/tests/fixtures/halal_fixture.json`) — trimmed but schema-faithful:

```json
{
  "generated_at": "2026-07-21T13:07:37Z",
  "verdicts": {
    "GEV": {
      "symbol": "GEV", "overall": "halal", "overall_basis": "AAOIFI",
      "standards": {
        "AAOIFI": {"status": "pass", "tests": [
          {"id": "debt_mcap", "label": "debt / market cap", "ratio": 0.0099, "threshold": 0.30, "margin": 0.2901, "status": "pass"},
          {"id": "cash_mcap", "label": "cash / market cap", "ratio": 0.05, "threshold": 0.30, "margin": 0.25, "status": "pass"}],
          "activity_status": "pass"},
        "FTSE": {"status": "pass", "tests": [
          {"id": "debt_assets", "label": "debt / total assets", "ratio": 0.10, "threshold": 0.333, "margin": 0.233, "status": "pass"}],
          "activity_status": "pass"},
        "MSCI": {"status": "pass", "tests": [
          {"id": "debt_assets", "label": "debt / total assets", "ratio": 0.10, "threshold": 0.3333, "margin": 0.2333, "status": "pass"}],
          "activity_status": "pass"}
      },
      "business": {"status": "clean", "categories": [], "impermissible_revenue_pct": null},
      "purification": {"per_share": 0.0, "status": "computed"},
      "inputs_asof": "2026-07-21T13:07:36Z"
    },
    "WULF": {
      "symbol": "WULF", "overall": "questionable", "overall_basis": "AAOIFI",
      "standards": {
        "AAOIFI": {"status": "pass", "tests": [
          {"id": "debt_mcap", "label": "debt / market cap", "ratio": 0.21, "threshold": 0.30, "margin": 0.09, "status": "pass"}],
          "activity_status": "review"},
        "FTSE": {"status": "pass", "tests": [
          {"id": "debt_assets", "label": "debt / total assets", "ratio": 0.28, "threshold": 0.333, "margin": 0.053, "status": "pass"}],
          "activity_status": "review"},
        "MSCI": {"status": "pass", "tests": [
          {"id": "debt_assets", "label": "debt / total assets", "ratio": 0.28, "threshold": 0.3333, "margin": 0.0533, "status": "pass"}],
          "activity_status": "review"}
      },
      "business": {"status": "questionable", "categories": ["crypto-mining"],
        "impermissible_revenue_pct": {"value": 38.2, "basis": "Q1-2026 revenue mix"}},
      "purification": {"per_share": 0.1296, "status": "computed"},
      "inputs_asof": "2026-07-21T13:07:36Z"
    }
  }
}
```

- [ ] **Step 2: Write the failing tests** (`scripts/tests/test_halal_join.py`)

```python
import datetime as dt
import json
import pathlib
import pytest
from aiinvest.halal_join import HalalDataMissing, load_halal, screen_card_data

FIX = pathlib.Path(__file__).parent / "fixtures" / "halal_fixture.json"
NOW = dt.datetime(2026, 7, 22, tzinfo=dt.timezone.utc)

def test_missing_file_raises():
    with pytest.raises(HalalDataMissing):
        load_halal(FIX.parent / "nope.json", now=NOW)

def test_load_fresh_no_warning():
    verdicts, warnings = load_halal(FIX, now=NOW)
    assert "WULF" in verdicts and warnings == []

def test_stale_warns():
    _, warnings = load_halal(FIX, now=NOW + dt.timedelta(days=10))
    assert any("older than 7 days" in w for w in warnings)

def test_card_missing_ticker_is_none():
    verdicts, _ = load_halal(FIX, now=NOW)
    assert screen_card_data(verdicts, "ZZZZ") is None

def test_card_binding_row_and_lines():
    verdicts, _ = load_halal(FIX, now=NOW)
    card = screen_card_data(verdicts, "WULF")
    assert card["overall"] == "questionable"
    assert card["badge"] == {"text": "AAOIFI SCREEN: REVIEW", "color": "#E0A23B"}
    aaoifi = next(r for r in card["standards_rows"] if r["name"] == "AAOIFI")
    assert aaoifi["binding_label"] == "debt / market cap"
    assert aaoifi["ratio"] == "21.0%" and aaoifi["threshold"] == "30.0%" and aaoifi["margin"] == "+9.0pt"
    assert "38.2%" in card["business_line"] and "crypto-mining" in card["business_line"]
    assert card["purification_line"] == "Purification (estimated): ~$0.13/share"
    assert card["inputs_asof"].startswith("2026-07-21")

def test_card_clean_name():
    verdicts, _ = load_halal(FIX, now=NOW)
    card = screen_card_data(verdicts, "GEV")
    assert card["badge"] == {"text": "AAOIFI SCREEN: PASS", "color": "#34D399"}
    assert card["business_line"] == "Business activity: clean"
    assert card["purification_line"] == "Purification (estimated): $0.00/share"
```

- [ ] **Step 3: Run to verify failure**

Run: `cd scripts && python -m pytest tests/test_halal_join.py -v`
Expected: FAIL — `ModuleNotFoundError: aiinvest.halal_join`.

- [ ] **Step 4: Implement** (`scripts/aiinvest/halal_join.py`)

```python
"""Join web/public/data/halal.json into content-generation shapes (badge, screen card).

Presentation-side ONLY — the engine lives in aiinvest/halal.py. Rails: badge/lines phrase
results as screen outcomes ("AAOIFI SCREEN: PASS"), never as "is halal" claims.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib

BADGES = {
    "halal": ("AAOIFI SCREEN: PASS", "#34D399"),
    "questionable": ("AAOIFI SCREEN: REVIEW", "#E0A23B"),
    "not_halal": ("AAOIFI SCREEN: FAIL", "#C25E5E"),
    "insufficient_data": ("AAOIFI SCREEN: NO DATA", "#8893A4"),
}


class HalalDataMissing(RuntimeError):
    pass


def load_halal(path, now=None):
    """-> (verdicts dict, warnings list). Raises HalalDataMissing if absent."""
    p = pathlib.Path(path)
    if not p.exists():
        raise HalalDataMissing(
            f"{p} not found — run `python pull_halal.py` then `python export_halal.py` first.")
    doc = json.loads(p.read_text(encoding="utf-8"))
    warnings = []
    now = now or _dt.datetime.now(_dt.timezone.utc)
    gen = doc.get("generated_at")
    if gen:
        ts = _dt.datetime.fromisoformat(gen.replace("Z", "+00:00"))
        if (now - ts).days > 7:
            warnings.append(f"halal.json generated_at {gen} is older than 7 days — regenerate.")
    return doc.get("verdicts", {}), warnings


def _pct(x):
    return f"{x * 100:.1f}%"


def _row(name, std):
    tests = std.get("tests") or []
    if not tests:
        return {"name": name, "ok": std.get("status") == "pass",
                "binding_label": "activity", "ratio": "—", "threshold": "—", "margin": "—"}
    binding = min(tests, key=lambda t: t.get("margin", 0))
    sign = "+" if binding["margin"] >= 0 else "−"
    return {
        "name": name,
        "ok": std.get("status") == "pass",
        "binding_label": binding["label"],
        "ratio": _pct(binding["ratio"]),
        "threshold": _pct(binding["threshold"]),
        "margin": f"{sign}{abs(binding['margin']) * 100:.1f}pt",
    }


def screen_card_data(verdicts, tk):
    v = verdicts.get(tk.upper())
    if not v:
        return None
    text, color = BADGES.get(v.get("overall"), BADGES["insufficient_data"])
    biz = v.get("business") or {}
    pct = biz.get("impermissible_revenue_pct")
    if biz.get("status") == "clean":
        business_line = "Business activity: clean"
    elif pct and pct.get("value") is not None:
        cats = ", ".join(biz.get("categories") or []) or "flagged"
        business_line = f"Business activity: {cats} — {pct['value']}% impermissible ({pct.get('basis', '')})".rstrip(" ()")
    else:
        cats = ", ".join(biz.get("categories") or []) or "flagged"
        business_line = f"Business activity: {cats} — % undisclosed in filings"
    pur = v.get("purification") or {}
    if pur.get("status") == "computed":
        ps = pur.get("per_share") or 0.0
        purification_line = (f"Purification (estimated): ~${ps:.2f}/share" if ps > 0
                             else "Purification (estimated): $0.00/share")
    else:
        purification_line = "Purification: insufficient data"
    return {
        "overall": v.get("overall"),
        "badge": {"text": text, "color": color},
        "standards_rows": [_row(n, v["standards"][n]) for n in ("AAOIFI", "FTSE", "MSCI")
                           if n in (v.get("standards") or {})],
        "business_line": business_line,
        "purification_line": purification_line,
        "inputs_asof": v.get("inputs_asof") or "",
    }
```

- [ ] **Step 5: Run tests**

Run: `cd scripts && python -m pytest tests/test_halal_join.py -v`
Expected: all PASS. (If `test_card_binding_row_and_lines` fails on `−`/`+` signs, check the margin sign logic, not the test.)

- [ ] **Step 6: Commit**

```bash
git add scripts/aiinvest/halal_join.py scripts/tests/test_halal_join.py scripts/tests/fixtures/halal_fixture.json
git commit -m "feat(halal): halal_join — bundle loader (staleness guard) + screen-card shaping"
```

---

### Task 4: script lint — `scripts/aiinvest/halal_lint.py`

**Files:**
- Create: `scripts/aiinvest/halal_lint.py`
- Test: `scripts/tests/test_halal_lint.py`

**Interfaces:**
- Consumes: `screen_card_data(...)` dict from Task 3.
- Produces: `lint_halal_script(script: str, card: dict) -> list[str]` — empty list = clean; otherwise human-readable error strings. Task 6 refuses TTS on any error.

- [ ] **Step 1: Write the failing tests** (`scripts/tests/test_halal_lint.py`)

```python
from aiinvest.halal_lint import lint_halal_script

CARD = {"standards_rows": [{"name": "AAOIFI", "ratio": "21.0%", "threshold": "30.0%", "margin": "+9.0pt"}],
        "business_line": "Business activity: crypto-mining — 38.2% impermissible",
        "purification_line": "Purification (estimated): ~$0.13/share"}
GOOD = ("TeraWulf... thirty-eight point two percent of revenue is mining. "
        "The screen flags it for review. Educational, not financial or religious advice.")

def test_clean_script_passes():
    assert lint_halal_script(GOOD, CARD) == []

def test_is_halal_claim_rejected():
    errs = lint_halal_script("WULF is halal. Educational, not financial or religious advice.", CARD)
    assert any("is halal" in e for e in errs)

def test_is_haram_claim_rejected():
    errs = lint_halal_script("This stock is haram. Educational, not financial or religious advice.", CARD)
    assert any("is haram" in e for e in errs)

def test_missing_disclaimer_rejected():
    errs = lint_halal_script("Thirty-eight point two percent is mining revenue.", CARD)
    assert any("disclaimer" in e.lower() for e in errs)

def test_no_card_number_rejected():
    errs = lint_halal_script("A company did things. Educational, not financial or religious advice.", CARD)
    assert any("number" in e.lower() for e in errs)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd scripts && python -m pytest tests/test_halal_lint.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement** (`scripts/aiinvest/halal_lint.py`)

```python
"""Rails linter for Karim halal VO scripts. Code-enforced, not convention.

Blocks: 'is halal'/'is haram' verdict claims; missing spoken disclaimer; scripts whose
numbers have no anchor in the joined screen-card data (no invented figures).
"""
from __future__ import annotations

import re

DISCLAIMER = "educational, not financial or religious advice"
_WORDS = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
    "6": "six", "7": "seven", "8": "eight", "9": "nine",
}


def _spoken_forms(card):
    """Digit strings + spelled-digit fragments a script may legitimately contain."""
    nums = set()
    for row in card.get("standards_rows", []):
        for k in ("ratio", "threshold", "margin"):
            m = re.search(r"([\d.]+)", row.get(k, ""))
            if m:
                nums.add(m.group(1))
    for line in (card.get("business_line", ""), card.get("purification_line", "")):
        nums.update(re.findall(r"([\d.]+)", line))
    forms = set()
    for n in nums:
        forms.add(n)
        head = n.split(".")[0]
        forms.add(" ".join(_WORDS[d] for d in head if d in _WORDS))
        if head in ("13",): forms.add("thirteen")
        if head in ("30",): forms.add("thirty")
        if head in ("38",): forms.add("thirty-eight")
        if head in ("21",): forms.add("twenty-one")
        if head in ("9",): forms.add("nine")
    return {f for f in forms if f}


def lint_halal_script(script, card):
    errs = []
    low = script.lower()
    if re.search(r"\bis\s+(fully\s+)?halal\b", low):
        errs.append('forbidden claim: "is halal" — say "passes the AAOIFI screen"')
    if re.search(r"\bis\s+haram\b", low):
        errs.append('forbidden claim: "is haram" — say "fails the screen" / "the screen flags it"')
    if DISCLAIMER not in low:
        errs.append(f'missing spoken disclaimer line: "{DISCLAIMER}"')
    if not any(f in low for f in _spoken_forms(card)):
        errs.append("no number in the script matches the joined screen data — scripts must cite real figures")
    return errs
```

- [ ] **Step 4: Run tests**

Run: `cd scripts && python -m pytest tests/test_halal_lint.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/aiinvest/halal_lint.py scripts/tests/test_halal_lint.py
git commit -m "feat(halal): script linter — phrasing rails, disclaimer, number-consistency"
```

---

### Task 5: `_build_v4.py` — badge, screen-card slide, 9:16 halal frames

**Files:**
- Modify: `higgs/_build_v4.py` (`header`, new `slide_screen`, `build_slides` signature, new `build_halal_frames`, `main`)
- Test: `scripts/tests/test_screen_card.py`

**Interfaces:**
- Consumes: `parse_cfg(...)["halal_script"]` (Task 2); `load_halal`/`screen_card_data` (Task 3).
- Produces: `header(tk, ex, logo_b64=None, badge=None)`; `slide_screen(hero, topbar, card) -> html`; `build_slides(md, site_stocks, quantum_stocks, hero_map, logo_map, date, halal_map=None)`; `build_halal_frames(md, hero_map, halal_map) -> {filename: html}` (9:16, names `reel_<tkl>_{hook,data,takeaway}.png`). Task 6's run-book renders these via `main()`.

- [ ] **Step 1: Write the failing tests** (`scripts/tests/test_screen_card.py`)

```python
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "higgs"))
import _build_v4 as b4  # noqa: E402

CARD = {
    "overall": "questionable",
    "badge": {"text": "AAOIFI SCREEN: REVIEW", "color": "#E0A23B"},
    "standards_rows": [
        {"name": "AAOIFI", "ok": True, "binding_label": "debt / market cap",
         "ratio": "21.0%", "threshold": "30.0%", "margin": "+9.0pt"},
        {"name": "FTSE", "ok": True, "binding_label": "debt / total assets",
         "ratio": "28.0%", "threshold": "33.3%", "margin": "+5.3pt"},
    ],
    "business_line": "Business activity: crypto-mining — 38.2% impermissible (Q1-2026 revenue mix)",
    "purification_line": "Purification (estimated): ~$0.13/share",
    "inputs_asof": "2026-07-21T13:07:36Z",
}

KIT = '''"WULF":{ "hero":"hero_wulf.png", "logo":"logo_WULF.png", "ex":"NASDAQ",
 "kick":"HALAL SCREEN", "head":"H", "sub":"S", "data_kick":"DK", "data_title":"DT",
 "data_cap":"", "data_foot":"", "mode":"disc", "rows":[], "tk_kick":"TK", "big":"38",
 "unit":"%", "tk_label":"L", "tk_body":"B", "src":"site",
 "halal_script":"thirty-eight. Educational, not financial or religious advice." }'''
HALAL_MAP = {"WULF": CARD}

def test_header_badge_rendered():
    h = b4.header("WULF", "NASDAQ", badge=CARD["badge"])
    assert "AAOIFI SCREEN: REVIEW" in h and "#E0A23B" in h

def test_header_no_badge_backcompat():
    h = b4.header("NVDA", "NASDAQ")
    assert "AAOIFI" not in h

def test_screen_slide_contents():
    html = b4.slide_screen("", "<div/>", CARD)
    for needle in ("AAOIFI", "FTSE", "debt / market cap", "21.0%", "30.0%", "+9.0pt",
                   "38.2%", "~$0.13/share", "2026-07-21",
                   "not a fatwa"):
        assert needle in html

def test_build_slides_halal_swaps_slide2():
    out = b4.build_slides(KIT, {}, {}, {}, {}, "2026-07-21", halal_map=HALAL_MAP)
    assert "v4_wulf_2_data.png" in out
    assert "debt / market cap" in out["v4_wulf_2_data.png"]        # screen card, not bars
    assert "AAOIFI SCREEN: REVIEW" in out["v4_wulf_1_hook.png"]     # badge on every slide
    assert "not a fatwa" in out["v4_wulf_3_takeaway.png"]

def test_build_slides_no_halal_map_unchanged():
    out = b4.build_slides(KIT, {}, {}, {}, {}, "2026-07-21")
    assert "debt / market cap" not in out["v4_wulf_2_data.png"]     # ordinary bars slide

def test_halal_frames_names_and_size():
    frames = b4.build_halal_frames(KIT, {}, HALAL_MAP)
    assert set(frames) == {"reel_wulf_hook.png", "reel_wulf_data.png", "reel_wulf_takeaway.png"}
    assert "1920" in frames["reel_wulf_data.png"]                   # 9:16 sizing present
    assert "debt / market cap" in frames["reel_wulf_data.png"]
```

- [ ] **Step 2: Run to verify failure**

Run: `cd scripts && python -m pytest tests/test_screen_card.py -v`
Expected: FAIL — `TypeError: header() got an unexpected keyword argument 'badge'`.

- [ ] **Step 3: Implement in `higgs/_build_v4.py`**

3a. Replace `header()` with:

```python
def header(tk, ex, logo_b64=None, badge=None):
    inner = f'<img src="{logo_b64}">' if logo_b64 else ""
    b = ""
    if badge:
        b = (f"<div style=\"margin-left:auto;font-family:'JetBrains Mono';font-weight:700;"
             f"font-size:22px;letter-spacing:2px;color:#0A0D12;background:{badge['color']};"
             f"padding:12px 20px;border-radius:12px\">{badge['text']}</div>")
    return f"""<div class='hdr'><div class='logochip'>{inner}</div>
    <div><div class='tkr'>{tk}</div><div class='ex'>{ex}</div></div>{b}</div>"""
```

3b. Add `slide_screen()` after `slide_takeaway()`:

```python
def slide_screen(hero, topbar, card, foot="Computed methodology result — not a fatwa · not financial advice"):
    rows = ""
    for r in card["standards_rows"]:
        mark = "✓" if r["ok"] else "✕"
        mcol = "#10B981" if r["ok"] else "#C25E5E"
        rows += f"""<div style='display:flex;align-items:center;margin:20px 0;gap:18px'>
        <div style="width:120px;font-family:'JetBrains Mono';font-weight:700;font-size:28px">{r['name']}</div>
        <div style='font-size:34px;color:{mcol};width:44px'>{mark}</div>
        <div style='flex:1'>
          <div style='font-size:24px;color:#9FB0A8'>{r['binding_label']}</div>
          <div style="font-family:'JetBrains Mono';font-weight:700;font-size:28px;color:#E8EDF2">
            {r['ratio']} <span style='color:#8893A4'>vs cap {r['threshold']}</span>
            <span style='color:{mcol}'>({r['margin']})</span></div></div></div>"""
    return page(f"""<div class='hero' style="background-image:url('{hero}');opacity:.12;transform:scale(1.1)"></div>
    <div class='scrim' style="background:linear-gradient(180deg,#0A0D12 30%,rgba(10,13,18,.55) 100%)"></div>
    <div class='pad'>{topbar}
      <div style='margin-top:22px' class='kick'>THE SCREEN — WORKED MATH</div>
      <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
        <div style='background:rgba(255,255,255,.04);border:1.5px solid rgba(255,255,255,.12);border-radius:18px;padding:30px 36px'>{rows}</div>
        <div style='font-size:27px;color:#D7DEE8;margin-top:26px'>{card['business_line']}</div>
        <div style='font-size:27px;color:#7FE9C2;margin-top:10px'>{card['purification_line']}</div>
        <div class='foot' style='margin-top:18px'>inputs as of {card['inputs_asof'][:10]}</div></div>
      <div class='foot'>{foot}</div></div>""")
```

3c. In `build_slides`, change the signature to
`def build_slides(md, site_stocks, quantum_stocks, hero_map, logo_map, date, halal_map=None):`
and replace the per-ticker body (the part building the three slides) with:

```python
        card = (halal_map or {}).get(tk)
        is_halal_post = bool(c.get("halal_script")) and card is not None
        badge = card["badge"] if card else None
        hdr = header(tk, c.get("ex") or "", logo_map.get(c.get("logo")), badge=badge)
        mode = c["data"]["mode"] or "disc"
        rows = _rows_from_bundle(c["data"]["rows"], stocks, mode)
        tkl = tk.lower()
        hk = c["hook"]; dt = c["data"]; tkw = c["takeaway"]
        out[f"v4_{tkl}_1_hook.png"] = slide_hook(
            hero, hk["kick"] or "", hk["head"] or "", hk["sub"] or "", topbar=hdr)
        if is_halal_post:
            out[f"v4_{tkl}_2_data.png"] = slide_screen(hero, hdr, card)
            out[f"v4_{tkl}_3_takeaway.png"] = slide_takeaway(
                hero, hdr, tkw["kick"] or "", tkw["big"] or "", tkw["unit"] or "",
                tkw["label"] or "", tkw["body"] or "",
                foot="Computed methodology result — not a fatwa · not financial advice")
        else:
            out[f"v4_{tkl}_2_data.png"] = slide_bars(
                hero, hdr, dt["kick"] or "", dt["title"] or "", rows, dt["cap"] or "", mode, foot=dt["foot"] or "")
            out[f"v4_{tkl}_3_takeaway.png"] = slide_takeaway(
                hero, hdr, tkw["kick"] or "", tkw["big"] or "", tkw["unit"] or "", tkw["label"] or "", tkw["body"] or "")
```

3d. Add `build_halal_frames()` after `build_slides()` (9:16 frames; `.slide` size overridden inline; hook has NO hero/scrim so it can be screenshotted transparent):

```python
RW, RH = 1080, 1920

def _page916(body, transparent=False):
    bg = "background:transparent" if transparent else ""
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}"
            f".slide{{width:{RW}px;height:{RH}px;{bg}}}</style></head>"
            f"<body style='{bg}'><div class='slide' style='width:{RW}px;height:{RH}px;{bg}'>{body}</div></body></html>")


def build_halal_frames(md, hero_map, halal_map):
    """Halal entries -> 9:16 reel frames {reel_<tkl>_{hook,data,takeaway}.png: html}.
    Hook frame is transparent (make_reel.py overlays it on the animated hero)."""
    out = {}
    for tk in _cfg_tickers(md):
        c = parse_cfg(md, tk)
        card = (halal_map or {}).get(tk)
        if not c or not c.get("halal_script") or not card:
            continue
        tkl = tk.lower()
        hdr = header(tk, c.get("ex") or "", badge=card["badge"])
        hk = c["hook"]; tkw = c["takeaway"]
        hero = hero_map.get(c.get("hero")) or ""
        out[f"reel_{tkl}_hook.png"] = _page916(f"""<div class='pad'>{hdr}
          <div style='margin-top:34px' class='kick'>{hk['kick'] or ''}</div>
          <div class='head' style='margin-top:auto;font-size:96px'>{hk['head'] or ''}</div>
          <div style='font-size:38px;line-height:1.4;color:#D7DEE8;margin-top:28px'>{hk['sub'] or ''}</div>
          <div class='foot' style='margin-top:40px'>Educational · not financial or religious advice</div></div>""",
          transparent=True)
        out[f"reel_{tkl}_data.png"] = _page916(
            slide_screen(hero, hdr, card).split("<div class='slide'>")[1].rsplit("</div></body>")[0])
        out[f"reel_{tkl}_takeaway.png"] = _page916(f"""<div class='pad'>{hdr}
          <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
            <div class='kick'>{tkw['kick'] or ''}</div>
            <div style="font-family:Fraunces;font-weight:700;font-size:260px;line-height:.86;letter-spacing:-6px;margin-top:16px;background:linear-gradient(180deg,#fff,#7FE9C2);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{tkw['big'] or ''}<span style='font-size:130px'>{tkw['unit'] or ''}</span></div>
            <div style="font-family:'JetBrains Mono';font-size:30px;letter-spacing:2px;color:#CFE8DD;margin-top:16px">{tkw['label'] or ''}</div>
            <div style='font-size:36px;line-height:1.42;color:#D7DEE8;margin-top:40px'>{tkw['body'] or ''}</div></div>
          <div class='foot'>Computed methodology result — not a fatwa · not financial advice</div></div>""")
    return out
```

  *(Note: the `slide_screen(...).split(...)` reuse extracts the card body into the 9:16 shell. If the split proves brittle in the red-green cycle, factor `_screen_body(hero, topbar, card, foot)` out of `slide_screen` and call it from both — same rendered content, cleaner seam.)*

3e. In `main()`, after loading `site`/`quantum`, add the halal join + render pass:

```python
    halal_map = None
    from aiinvest.halal_join import HalalDataMissing, load_halal, screen_card_data
    tk_list = _cfg_tickers(md)
    wants_halal = any((parse_cfg(md, t) or {}).get("halal_script") for t in tk_list)
    try:
        verdicts, warns = load_halal(ROOT / "web/public/data/halal.json")
        for w in warns:
            print("WARN", w)
        halal_map = {t: screen_card_data(verdicts, t) for t in tk_list}
        halal_map = {t: c for t, c in halal_map.items() if c}
        skipped = [t for t in tk_list if (parse_cfg(md, t) or {}).get("halal_script") and t not in halal_map]
        if skipped:
            print(f"WARN halal_script tickers missing from halal.json (skipped halal mode): {skipped}")
    except HalalDataMissing as e:
        if wants_halal:
            print(f"REFUSED: kit has halal posts but {e}")
            return 3
```

pass `halal_map=halal_map` into the `build_slides(...)` call, and after the existing 4:5 render loop add:

```python
        frames = build_halal_frames(md, hero_map, halal_map or {})
        if frames:
            pg2 = b.new_page(viewport={"width": RW, "height": RH})
            for name, html in frames.items():
                pg2.set_content(html, wait_until="networkidle")
                pg2.evaluate("document.fonts.ready")
                pg2.wait_for_timeout(600)
                pg2.screenshot(path=str(HIGGS / name), omit_background=name.endswith("_hook.png"),
                               clip={"x": 0, "y": 0, "width": RW, "height": RH})
                print("rendered", name)
```

(inside the existing `sync_playwright` block, before `b.close()`).

- [ ] **Step 4: Run the new tests + the whole suite**

Run: `cd scripts && python -m pytest tests/test_screen_card.py tests/test_build_v4.py -v`
Expected: all PASS (existing `test_build_v4.py` must stay green — `halal_map` defaults to `None`).

- [ ] **Step 5: Commit**

```bash
git add higgs/_build_v4.py scripts/tests/test_screen_card.py
git commit -m "feat(carousel): halal mode — verdict badge, screen-card slide, 9:16 reel frames"
```

---

### Task 6: voice generation + manifest — `higgs/_gen_halal_voice.py`

**Files:**
- Create: `higgs/_gen_halal_voice.py`
- Test: `scripts/tests/test_halal_voice.py` (pure parts only — no network in tests)

**Interfaces:**
- Consumes: `parse_cfg` (Task 2), `load_halal`/`screen_card_data` (Task 3), `lint_halal_script` (Task 4), `course/persona/higgsfield-ids.json` `voice` block (Task 1).
- Produces (pure, tested): `collect_halal_entries(md) -> [(tk, script)]`; `compose_tts_cmd(script, voice) -> list[str]`; `merge_manifest(manifest: dict, date: str, tk: str, voice_url: str) -> dict`. CLI: `python higgs/_gen_halal_voice.py [--date D] [--dry-run]`.

- [ ] **Step 1: Write the failing tests** (`scripts/tests/test_halal_voice.py`)

```python
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "higgs"))
import _gen_halal_voice as gv  # noqa: E402

KIT = '''"WULF":{ "kick":"K", "halal_script":"thirty-eight. Educational, not financial or religious advice." }
"NVDA":{ "kick":"K" }'''
VOICE = {"id": "abc-123", "type": "element", "variant": "elevenlabs"}

def test_collect_only_halal_entries():
    assert gv.collect_halal_entries(KIT) == [
        ("WULF", "thirty-eight. Educational, not financial or religious advice.")]

def test_compose_tts_cmd():
    cmd = gv.compose_tts_cmd("hello world", VOICE)
    assert cmd[:3] == ["higgsfield", "generate", "create"]
    assert "text2speech_v2" in cmd
    assert "--voice_id" in cmd and cmd[cmd.index("--voice_id") + 1] == "abc-123"
    assert "--voice_type" in cmd and cmd[cmd.index("--voice_type") + 1] == "element"
    assert "--variant" in cmd and cmd[cmd.index("--variant") + 1] == "elevenlabs"
    assert "--wait" in cmd and "--json" in cmd

def test_compose_refuses_null_voice():
    import pytest
    with pytest.raises(SystemExit):
        gv.compose_tts_cmd("x", {"id": None, "type": "element", "variant": "elevenlabs"})

def test_merge_manifest_updates_existing_and_appends():
    m = {"date": "2026-06-30", "reels": [{"tk": "WULF", "hero": "H", "voice": "OLD"}]}
    out = gv.merge_manifest(m, "2026-07-21", "WULF", "NEW")
    assert out["date"] == "2026-07-21"
    assert out["reels"][0]["voice"] == "NEW" and out["reels"][0]["hero"] == "H"
    out2 = gv.merge_manifest(out, "2026-07-21", "GEV", "V2")
    assert {"tk": "GEV", "hero": "", "voice": "V2", "voice_name": "Karim"} in out2["reels"]
```

- [ ] **Step 2: Run to verify failure**

Run: `cd scripts && python -m pytest tests/test_halal_voice.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement** (`higgs/_gen_halal_voice.py`)

```python
"""Generate Karim VO for halal kit entries via the locked cloned voice; update the manifest.

    python higgs/_gen_halal_voice.py                 # newest kit
    python higgs/_gen_halal_voice.py --date 2026-07-21
    python higgs/_gen_halal_voice.py --dry-run       # lint + print commands, no spend

Refuses on: missing halal.json, lint errors, or a null voice id (course/persona/higgsfield-ids.json).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

HIGGS = pathlib.Path(__file__).resolve().parent
ROOT = HIGGS.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from aiinvest.kit_md import parse_cfg                       # noqa: E402
from aiinvest.halal_join import load_halal, screen_card_data  # noqa: E402
from aiinvest.halal_lint import lint_halal_script           # noqa: E402
import re                                                    # noqa: E402

IDS = ROOT / "course/persona/higgsfield-ids.json"
MANIFEST = HIGGS / "reels_manifest.json"


def collect_halal_entries(md):
    out, seen = [], set()
    for tk in re.findall(r'"([A-Z0-9.]{1,12})":\{', md):
        if tk in seen:
            continue
        seen.add(tk)
        c = parse_cfg(md, tk)
        if c and c.get("halal_script"):
            out.append((tk, c["halal_script"].strip()))
    return out


def compose_tts_cmd(script, voice):
    if not voice.get("id"):
        raise SystemExit("voice.id is null in course/persona/higgsfield-ids.json — "
                         "create the cloned voice in the Higgsfield web UI first (see VOICE.md).")
    return ["higgsfield", "generate", "create", "text2speech_v2",
            "--prompt", script,
            "--variant", voice.get("variant", "elevenlabs"),
            "--voice_id", voice["id"],
            "--voice_type", voice.get("type", "element"),
            "--wait", "--json"]


def merge_manifest(manifest, date, tk, voice_url):
    manifest = dict(manifest)
    manifest["date"] = date
    reels = list(manifest.get("reels", []))
    for e in reels:
        if e.get("tk") == tk:
            e["voice"] = voice_url
            e["voice_name"] = "Karim"
            break
    else:
        reels.append({"tk": tk, "hero": "", "voice": voice_url, "voice_name": "Karim"})
    manifest["reels"] = reels
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    from _build_v4 import pick_kit  # local import: same conventions
    kit = pick_kit(HIGGS, args.date, None)
    if not kit or not kit.exists():
        raise SystemExit(f"no kit found ({kit})")
    md = kit.read_text(encoding="utf-8")
    m = re.search(r"reels_(\d{4}-\d{2}-\d{2})_kit", kit.name)
    date = args.date or (m.group(1) if m else "")

    verdicts, warns = load_halal(ROOT / "web/public/data/halal.json")
    for w in warns:
        print("WARN", w)

    voice = json.loads(IDS.read_text(encoding="utf-8")).get("voice") or {}
    entries = collect_halal_entries(md)
    if not entries:
        print("no halal_script entries in kit — nothing to do")
        return 0

    failed = False
    for tk, script in entries:
        card = screen_card_data(verdicts, tk)
        if card is None:
            print(f"SKIP {tk}: not in halal.json")
            continue
        errs = lint_halal_script(script, card)
        if errs:
            failed = True
            for e in errs:
                print(f"LINT {tk}: {e}")
            continue
        cmd = compose_tts_cmd(script, voice)
        if args.dry_run:
            print(f"DRY {tk}:", " ".join(cmd[:8]), "...")
            continue
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"TTS failed for {tk}:\n{r.stderr[-800:]}")
        url = ""
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if line.startswith("http") and (".mp3" in line or ".wav" in line or ".m4a" in line):
                url = line
        if not url:
            try:
                doc = json.loads(r.stdout)
                if isinstance(doc, list):
                    doc = doc[0]
                url = doc.get("result_url") or doc.get("url") or ""
            except Exception:
                pass
        if not url:
            raise SystemExit(f"could not find voice URL in CLI output for {tk}:\n{r.stdout[-800:]}")
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"reels": []}
        MANIFEST.write_text(json.dumps(merge_manifest(manifest, date, tk, url), indent=1),
                            encoding="utf-8")
        print(f"OK {tk} voice -> {url}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests**

Run: `cd scripts && python -m pytest tests/test_halal_voice.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add higgs/_gen_halal_voice.py scripts/tests/test_halal_voice.py
git commit -m "feat(halal): Karim VO generation — lint-gated TTS via locked voice + manifest merge"
```

---

### Task 7: `make_reel.py --skip-frames` + end-to-end run-book

**Files:**
- Modify: `higgs/make_reel.py:57-62`
- Modify: `docs/superpowers/specs/2026-07-21-halal-generation-design.md` (append run-book)

**Interfaces:**
- Produces: `python higgs/make_reel.py <TK> <HERO_URL> <VOICE_URL> --skip-frames` — skips the `_build_reel_stock.py` call and uses the pre-rendered `reel_<tkl>_{hook,data,takeaway}.png` written by `build_halal_frames` (Task 5). Without the flag, behavior is byte-identical to today.

- [ ] **Step 1: Modify step 1 of `make_reel.py`** — replace lines 57-59 (`# 1. frames` block) with:

```python
    # 1. frames (local, free) — skipped when pre-rendered (halal kit-driven frames)
    if "--skip-frames" not in sys.argv:
        rc, out, err = sh(f'python "{HG/"_build_reel_stock.py"}" {tk}')
        if rc != 0: raise SystemExit(f"frame build failed:\n{err[-1200:]}")
```

(the existing `for p in (hook_png, data_png, take_png): if not p.exists(): raise ...` guard stays — it now also validates pre-rendered frames.)

- [ ] **Step 2: Verify legacy path unaffected**

Run: `cd scripts && python -m pytest tests/ -q` (full suite) and `python higgs/make_reel.py 2>&1 | head -2`
Expected: suite green; bare invocation still fails with the usual IndexError/usage (no behavior change without the flag).

- [ ] **Step 3: Append the run-book to the spec** (new final section):

```markdown
## 9. Run-book (one halal post, end-to-end)

1. Fresh data: `cd scripts && python pull_halal.py && python export_halal.py`
2. Author the kit entry in `higgs/reels_<date>_kit.md`: normal CFG + `"halal_script": "..."`
   (write to the VOICE.md delivery canon; end with the spoken disclaimer line).
3. Render slides + reel frames: `python higgs/_build_v4.py --date <date>`
   (badge + screen card 4:5; `reel_<tk>_{hook,data,takeaway}.png` 9:16).
4. Lint + voice: `python higgs/_gen_halal_voice.py --date <date> --dry-run` → review → run
   without `--dry-run` (needs `voice.id` set after the one-time web-UI clone).
5. Assemble: `python higgs/make_reel.py <TK> <HERO_MP4_URL> <VOICE_MP3_URL> --skip-frames`
   (hero: reuse desk-set/hero art or generate via the usual Phase-1 flow).
6. QA vs `course/persona/RULES.md` §7 checklist + listen for VOICE.md canon; then post via
   Studio (copy caption / reveal file).
```

- [ ] **Step 4: Commit**

```bash
git add higgs/make_reel.py docs/superpowers/specs/2026-07-21-halal-generation-design.md
git commit -m "feat(reel): --skip-frames switch for pre-rendered halal frames + run-book"
```

---

## Self-Review (done at plan time)

- **Spec coverage:** G1→Task 1(+6); G2→Tasks 2,3,5; G3→Tasks 5,6,7; G4→Tasks 3,4,5 (rails in badge text, lint, slide footers). Guards §6→Tasks 3 (missing/stale), 5 (refuse/skip in `main`), 6 (lint gate, null-voice). Testing §7 mapped 1:1 (`test_kit_md_halal`, `test_halal_join`, `test_screen_card`, `test_halal_lint` + `test_halal_voice` added).
- **Deviations from spec (documented in Global Constraints):** activation key, `--skip-frames`.
- **Type consistency check:** `screen_card_data` card dict keys match between Tasks 3/4/5 tests; `voice` block shape matches Tasks 1/6; frame filenames match Tasks 5/7.
```
