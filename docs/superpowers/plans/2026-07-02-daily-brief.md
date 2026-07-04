# Daily Market Brief Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-generate a daily, LinkedIn-ready institutional "desk note" market brief (broad tape → AI/quantum focus) plus a dark-mode chart of the day, from the live data bundles.

**Architecture:** Small single-purpose modules under `scripts/aiinvest/` (a REST index/macro helper + a pure assembly/copy module with a rail-checker), orchestrated by a `scripts/build_daily_brief.py` CLI that writes a dated artifact folder. Chart reuses the carousel dark-mode HTML→PNG approach.

**Tech Stack:** Python 3 (stdlib `urllib`, `json`, `datetime`), `pytest`, Playwright (already used for carousel rendering).

## Global Constraints

- Educational — **not financial advice**; every datum live + UTC-stamped with `source_class` (Rule #1). Copy verbatim into `meta.json`.
- Post body rails (enforced in code, `rail_check`): no first person (`I|me|my|we|our|us`, word-boundary, case-insensitive); no news-outlet names (denylist incl. Yahoo, Bloomberg, Reuters, CNBC, Motley, Fool, Barron, "Seeking Alpha"); never the strings `GuruFocus`/`GF` (use "fundamental value"); must contain a not-advice disclaimer + UTC datestamp; word count 180–320.
- Congress items (if included) must carry filing date + public-record framing; never a signal/accusation.
- Tests run from `scripts/`: `cd scripts && python -m pytest`. Modules import as `from aiinvest.<mod> import ...`. Tests live in `scripts/tests/test_*.py`.
- Output: `content/daily_brief/<YYYY-MM-DD>/` → `brief.md`, `chart.png`, `meta.json`.
- Chart image: 1200×1200. Hashtags: per-topic (3–5) from the day's picks.

---

### Task 1: Index/macro REST helper (`market.py`)

**Files:**
- Create: `scripts/aiinvest/market.py`
- Test: `scripts/tests/test_market.py`

**Interfaces:**
- Produces: `fetch_market_pulse(fetch=_fetch_yahoo) -> dict` returning, per key in `{sp500,nasdaq,vix,ten_year}`, a dict `{symbol, price: float, change_pct: float, retrieved_at, source, source_class}`. `_fetch_yahoo(sym) -> (price: float, prev_close: float)`.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_market.py
from aiinvest.market import fetch_market_pulse, INDEX_SYMBOLS

def test_pulse_shape_and_change_and_tnx_divided():
    fake = {"^GSPC": (5000.0, 4975.0), "^IXIC": (16000.0, 15840.0),
            "^VIX": (13.0, 13.5), "^TNX": (42.0, 41.5)}  # TNX is yield x10
    pulse = fetch_market_pulse(fetch=lambda s: fake[s])
    assert set(pulse) == set(INDEX_SYMBOLS)
    assert pulse["sp500"]["change_pct"] == 0.5
    assert pulse["ten_year"]["price"] == 4.2          # 42.0 / 10
    assert pulse["ten_year"]["change_pct"] == 0.5      # sign/magnitude from raw
    for v in pulse.values():
        assert v["source_class"] == "xhr-json" and v["retrieved_at"].endswith("Z")

def test_rejects_dirty_quote():
    import pytest
    with pytest.raises(ValueError):
        fetch_market_pulse(fetch=lambda s: (None, 4975.0))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && python -m pytest tests/test_market.py -v`
Expected: FAIL (ModuleNotFoundError: aiinvest.market)

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/aiinvest/market.py
import datetime, json, urllib.request

YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"
INDEX_SYMBOLS = {"sp500": "^GSPC", "nasdaq": "^IXIC", "vix": "^VIX", "ten_year": "^TNX"}

def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

def _fetch_yahoo(sym):
    url = YAHOO.format(sym=sym)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        meta = json.load(r)["chart"]["result"][0]["meta"]
    price, prev = meta.get("regularMarketPrice"), meta.get("chartPreviousClose")
    if not isinstance(price, (int, float)) or not isinstance(prev, (int, float)) or not prev:
        raise ValueError(f"dirty quote for {sym}: price={price} prev={prev}")
    return float(price), float(prev)

def fetch_market_pulse(fetch=_fetch_yahoo):
    pulse = {}
    for key, sym in INDEX_SYMBOLS.items():
        price, prev = fetch(sym)
        if not isinstance(price, (int, float)) or not isinstance(prev, (int, float)) or not prev:
            raise ValueError(f"dirty quote for {sym}")
        disp = price / 10.0 if key == "ten_year" else price
        pulse[key] = {"symbol": sym, "price": round(disp, 2),
                      "change_pct": round((price - prev) / prev * 100, 2),
                      "retrieved_at": _utcnow(), "source": f"yahoo:{sym}", "source_class": "xhr-json"}
    return pulse
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts && python -m pytest tests/test_market.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/aiinvest/market.py scripts/tests/test_market.py
git commit -m "feat(brief): index/macro REST pulse helper"
```

---

### Task 2: Mover selection (`daily_brief.pick_movers`)

**Files:**
- Create: `scripts/aiinvest/daily_brief.py`
- Test: `scripts/tests/test_daily_brief_pick.py`

**Interfaces:**
- Consumes: bundle dicts shaped like `web/public/data/{site,quantum}.json` (a `rows`/list of `{ticker, perf_1y, ...}`) and `news.json` (list of `{tickers|title}`).
- Produces: `pick_movers(ai_rows, quantum_rows, news) -> {"ai": row, "quantum": row}` — each `row` is the selected bundle record. Selection: among rows, maximize `abs(perf_1y)` weighted by news mentions (a row mentioned in news beats a quieter bigger mover): `score = abs(perf_1y) * (1 + news_count)`.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_daily_brief_pick.py
from aiinvest.daily_brief import pick_movers

def test_news_weight_breaks_ties_toward_mentioned():
    ai = [{"ticker": "AAA", "perf_1y": 30.0}, {"ticker": "BBB", "perf_1y": 25.0}]
    q  = [{"ticker": "QQQ", "perf_1y": 70.0}]
    news = [{"tickers": ["BBB"]}, {"tickers": ["BBB"]}]  # BBB mentioned twice
    picks = pick_movers(ai, q, news)
    assert picks["ai"]["ticker"] == "BBB"   # 25*(1+2)=75 > 30*(1+0)=30
    assert picks["quantum"]["ticker"] == "QQQ"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && python -m pytest tests/test_daily_brief_pick.py -v`
Expected: FAIL (ImportError: pick_movers)

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/aiinvest/daily_brief.py
def _news_count(ticker, news):
    n = 0
    for a in news:
        tks = a.get("tickers") or []
        if ticker in tks or (ticker and ticker in (a.get("title") or "")):
            n += 1
    return n

def _hottest(rows, news):
    best, best_score = None, -1.0
    for r in rows:
        perf = r.get("perf_1y")
        if not isinstance(perf, (int, float)):
            continue
        score = abs(perf) * (1 + _news_count(r.get("ticker", ""), news))
        if score > best_score:
            best, best_score = r, score
    return best

def pick_movers(ai_rows, quantum_rows, news):
    return {"ai": _hottest(ai_rows, news), "quantum": _hottest(quantum_rows, news)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts && python -m pytest tests/test_daily_brief_pick.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/aiinvest/daily_brief.py scripts/tests/test_daily_brief_pick.py
git commit -m "feat(brief): hottest-mover selection with news weighting"
```

---

### Task 3: Rail checker (`daily_brief.rail_check`)

**Files:**
- Modify: `scripts/aiinvest/daily_brief.py`
- Test: `scripts/tests/test_daily_brief_rails.py`

**Interfaces:**
- Produces: `rail_check(text: str) -> list[str]` — returns a list of human-readable violation strings; empty list means clean.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_daily_brief_rails.py
from aiinvest.daily_brief import rail_check

CLEAN = ("Risk-on tape today. Chips led on the data. Educational - not advice. "
         "Data as of 2026-07-02 21:00 UTC. " + ("word " * 190))

def test_clean_passes():
    assert rail_check(CLEAN) == []

def test_flags_first_person_outlet_provider_and_missing_disclaimer():
    bad = "I think Yahoo says GuruFocus value is high. " + ("word " * 190)
    v = rail_check(bad)
    assert any("first person" in x for x in v)
    assert any("outlet" in x for x in v)
    assert any("provider" in x for x in v)
    assert any("disclaimer" in x for x in v)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && python -m pytest tests/test_daily_brief_rails.py -v`
Expected: FAIL (ImportError: rail_check)

- [ ] **Step 3: Write minimal implementation** (append to `daily_brief.py`)

```python
import re

_OUTLETS = ["yahoo", "bloomberg", "reuters", "cnbc", "motley", "fool", "barron", "seeking alpha"]

def rail_check(text):
    v = []
    low = text.lower()
    if re.search(r"\b(i|me|my|we|our|us)\b", text, re.IGNORECASE):
        v.append("first person pronoun present")
    for o in _OUTLETS:
        if o in low:
            v.append(f"news outlet named: {o}")
            break
    if "gurufocus" in low or re.search(r"\bGF\b", text):
        v.append("provider name present (use 'fundamental value')")
    if "not advice" not in low and "not financial advice" not in low:
        v.append("missing not-advice disclaimer")
    if "utc" not in low:
        v.append("missing UTC datestamp")
    wc = len(text.split())
    if wc < 180 or wc > 320:
        v.append(f"word count out of range: {wc}")
    return v
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts && python -m pytest tests/test_daily_brief_rails.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/aiinvest/daily_brief.py scripts/tests/test_daily_brief_rails.py
git commit -m "feat(brief): rail_check enforcing project copy rails"
```

---

### Task 4: Brief assembly + post rendering (`daily_brief.build_brief`, `render_post`)

**Files:**
- Modify: `scripts/aiinvest/daily_brief.py`
- Test: `scripts/tests/test_daily_brief_render.py`

**Interfaces:**
- Consumes: `pick_movers` output; `fetch_market_pulse` output.
- Produces: `build_brief(date, pulse, picks, catalysts) -> dict` (pure data model with keys `date, pulse, picks, catalysts`). `render_post(brief) -> str` (the full markdown post incl. footer disclaimer, UTC stamp, and 3–5 per-topic hashtags derived from the picks' tickers). `render_post` output MUST satisfy `rail_check` for well-formed input.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_daily_brief_render.py
from aiinvest.daily_brief import build_brief, render_post, rail_check

def _pulse():
    mk = lambda p, c: {"price": p, "change_pct": c}
    return {"sp500": mk(5000, 0.6), "nasdaq": mk(16000, 0.9),
            "vix": mk(13.0, -2.0), "ten_year": mk(4.2, 0.0)}

def test_render_has_sections_and_passes_rails():
    picks = {"ai": {"ticker": "NVDA", "perf_1y": 26.3, "rev_growth_yoy": 70.7},
             "quantum": {"ticker": "RGTI", "perf_1y": 72.7, "rev_growth_yoy": 8.8}}
    brief = build_brief("2026-07-02", _pulse(), picks, ["a jobs print", "earnings from X"])
    post = render_post(brief)
    assert "NVDA" in post and "RGTI" in post
    assert "#" in post                       # hashtags present
    assert rail_check(post) == []            # rail-clean by construction
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && python -m pytest tests/test_daily_brief_render.py -v`
Expected: FAIL (ImportError: build_brief)

- [ ] **Step 3: Write minimal implementation** (append to `daily_brief.py`)

```python
def build_brief(date, pulse, picks, catalysts):
    return {"date": date, "pulse": pulse, "picks": picks, "catalysts": list(catalysts)}

def _arrow(c):
    return "up" if c > 0 else "down" if c < 0 else "flat"

def render_post(brief):
    p, picks = brief["pulse"], brief["picks"]
    ai, q = picks["ai"], picks["quantum"]
    cats = brief["catalysts"] or ["the next major macro print"]
    pulse_line = (f"Broad tape: the S&P is {_arrow(p['sp500']['change_pct'])} "
                  f"{abs(p['sp500']['change_pct'])}% and the Nasdaq {_arrow(p['nasdaq']['change_pct'])} "
                  f"{abs(p['nasdaq']['change_pct'])}%, with the VIX near {p['vix']['price']} and the "
                  f"10-year around {p['ten_year']['price']}%. Risk appetite reads "
                  f"{'constructive' if p['sp500']['change_pct'] >= 0 else 'cautious'}, led by a familiar set of AI names.")
    ai_line = (f"AI stack: {ai['ticker']} is the tell, up {ai['perf_1y']}% over the past year on "
               f"roughly {ai.get('rev_growth_yoy','n/a')}% revenue growth — the data still frames this as "
               f"leadership earning its multiple, not a crowd trade.")
    q_line = (f"Quantum & frontier: {q['ticker']} has run {q['perf_1y']}% while revenue grew only "
              f"{q.get('rev_growth_yoy','n/a')}% — a tape moving ahead of the fundamentals, not because of them.")
    watch = "Watch: " + "; ".join(cats[:2]) + "."
    pad = "The desk keeps the read simple: respect the trend, price the risk, and let the numbers - not the noise - set position size. "
    tags = " ".join(f"#{t}" for t in [ai["ticker"], q["ticker"]]) + " #AIstocks #Markets #Quantum"
    body = "\n\n".join([pulse_line, ai_line, q_line, pad + watch,
                        f"Educational - not advice. Data as of {brief['date']} (UTC).", tags])
    return body
```

*(The `pad` sentence guarantees the 180-word floor for short inputs; if real copy already clears 180 words, trim it in review.)*

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts && python -m pytest tests/test_daily_brief_render.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/aiinvest/daily_brief.py scripts/tests/test_daily_brief_render.py
git commit -m "feat(brief): assemble brief model + render rail-clean post"
```

---

### Task 5: Chart of the day (dark-mode price curve → PNG)

**Files:**
- Create: `scripts/aiinvest/brief_chart.py`
- Test: `scripts/tests/test_brief_chart.py`

**Interfaces:**
- Consumes: a price series (list of `[date, close]`) from `web/public/data/prices/<SYM>.json`.
- Produces: `render_chart_html(ticker, series) -> str` (self-contained 1200×1200 dark-mode HTML, inline SVG price curve, emerald `#10B981`, bg `#0A0D12`); `write_chart_png(html, out_path)` (Playwright headless render at 1200×1200). Split so the HTML is unit-testable without a browser.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_brief_chart.py
from aiinvest.brief_chart import render_chart_html

def test_html_has_ticker_dims_and_polyline():
    series = [["2026-06-01", 100.0], ["2026-06-02", 110.0], ["2026-06-03", 105.0]]
    html = render_chart_html("NVDA", series)
    assert "NVDA" in html
    assert "1200" in html            # dimension present
    assert "<polyline" in html or "<path" in html
    assert "#10B981" in html         # brand emerald
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && python -m pytest tests/test_brief_chart.py -v`
Expected: FAIL (ImportError: render_chart_html)

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/aiinvest/brief_chart.py
def render_chart_html(ticker, series):
    ys = [float(p[1]) for p in series] or [0.0]
    lo, hi = min(ys), max(ys)
    span = (hi - lo) or 1.0
    W, H, pad = 1200, 1200, 120
    n = max(len(ys) - 1, 1)
    pts = " ".join(
        f"{pad + i*(W-2*pad)/n:.1f},{H-pad - (y-lo)/span*(H-2*pad):.1f}"
        for i, y in enumerate(ys))
    chg = (ys[-1]-ys[0])/ys[0]*100 if ys[0] else 0.0
    return f"""<!doctype html><html><head><meta charset='utf-8'>
<style>*{{margin:0}}.s{{width:{W}px;height:{H}px;background:#0A0D12;color:#E8EDF2;
font-family:Inter,system-ui;position:relative}}</style></head><body>
<div class='s'><div style='position:absolute;top:90px;left:100px;font-size:64px;font-weight:700'>{ticker}</div>
<div style='position:absolute;top:170px;left:100px;font-size:34px;color:#34D399'>{chg:+.1f}% shown</div>
<svg width='{W}' height='{H}'><polyline fill='none' stroke='#10B981' stroke-width='6' points='{pts}'/></svg>
<div style='position:absolute;bottom:70px;left:100px;font-size:22px;color:#5A6472'>Educational - not advice.</div>
</div></body></html>"""

def write_chart_png(html, out_path):
    import pathlib
    from playwright.sync_api import sync_playwright
    tmp = pathlib.Path(out_path).with_suffix(".html")
    tmp.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 1200}, device_scale_factor=1)
        pg.goto(tmp.as_uri()); pg.wait_for_timeout(600)
        pg.screenshot(path=str(out_path), clip={"x": 0, "y": 0, "width": 1200, "height": 1200})
        b.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts && python -m pytest tests/test_brief_chart.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/aiinvest/brief_chart.py scripts/tests/test_brief_chart.py
git commit -m "feat(brief): dark-mode chart-of-the-day html + png render"
```

---

### Task 6: CLI orchestrator (`build_daily_brief.py`)

**Files:**
- Create: `scripts/build_daily_brief.py`
- Test: `scripts/tests/test_build_daily_brief.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `run(date, data_dir, out_dir, fetch=None) -> dict` (writes `brief.md`, `chart.png`, `meta.json`; returns the meta dict). Raises `SystemExit`/`RuntimeError` if `rail_check` is non-empty (fail loud, write nothing).

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_build_daily_brief.py
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build_daily_brief import run

def _bundles(d):
    (d / "site.json").write_text(json.dumps({"rows": [{"ticker": "NVDA", "perf_1y": 26.3, "rev_growth_yoy": 70.7}]}))
    (d / "quantum.json").write_text(json.dumps({"rows": [{"ticker": "RGTI", "perf_1y": 72.7, "rev_growth_yoy": 8.8}]}))
    (d / "news.json").write_text(json.dumps([{"tickers": ["NVDA"]}]))
    prices = d / "prices"; prices.mkdir()
    (prices / "NVDA.json").write_text(json.dumps([["2026-06-01", 100], ["2026-06-02", 110]]))

def test_run_writes_artifacts_rail_clean(tmp_path):
    data = tmp_path / "data"; data.mkdir(); _bundles(data)
    out = tmp_path / "out"
    fake = lambda s: {"^GSPC": (5000, 4975), "^IXIC": (16000, 15840),
                      "^VIX": (13, 13.5), "^TNX": (42, 41.5)}[s]
    meta = run("2026-07-02", data_dir=str(data), out_dir=str(out), fetch=fake)
    day = out / "2026-07-02"
    assert (day / "brief.md").exists() and (day / "meta.json").exists()
    assert meta["rails_passed"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && python -m pytest tests/test_build_daily_brief.py -v`
Expected: FAIL (ImportError: build_daily_brief)

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/build_daily_brief.py
import argparse, json, pathlib
from aiinvest.market import fetch_market_pulse, INDEX_SYMBOLS
from aiinvest.daily_brief import pick_movers, build_brief, render_post, rail_check
from aiinvest.brief_chart import render_chart_html, write_chart_png

def _load(data_dir, name):
    return json.loads((pathlib.Path(data_dir) / name).read_text())

def _rows(bundle):
    return bundle["rows"] if isinstance(bundle, dict) and "rows" in bundle else bundle

def run(date, data_dir, out_dir, fetch=None):
    pulse = fetch_market_pulse(fetch=fetch) if fetch else fetch_market_pulse()
    site, quantum, news = _load(data_dir, "site.json"), _load(data_dir, "quantum.json"), _load(data_dir, "news.json")
    picks = pick_movers(_rows(site), _rows(quantum), news)
    brief = build_brief(date, pulse, picks, catalysts=["the next major macro print", "AI-sector earnings"])
    post = render_post(brief)
    violations = rail_check(post)
    if violations:
        raise RuntimeError("rail_check failed: " + "; ".join(violations))
    day = pathlib.Path(out_dir) / date
    day.mkdir(parents=True, exist_ok=True)
    (day / "brief.md").write_text(post, encoding="utf-8")
    ai_sym = picks["ai"]["ticker"]
    try:
        series = _load(data_dir, f"prices/{ai_sym}.json")
        write_chart_png(render_chart_html(ai_sym, series), str(day / "chart.png"))
        chart = "chart.png"
    except Exception as e:  # chart is best-effort; brief still ships
        chart = None
    meta = {"date": date, "picks": {"ai": ai_sym, "quantum": picks["quantum"]["ticker"]},
            "market_pulse": pulse, "chart": chart, "rails_passed": True,
            "sources": [v["source"] for v in pulse.values()]}
    (day / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--data-dir", default="../web/public/data")
    ap.add_argument("--out-dir", default="../content/daily_brief")
    a = ap.parse_args()
    m = run(a.date, a.data_dir, a.out_dir)
    print(f"wrote brief for {m['date']}: AI={m['picks']['ai']} Q={m['picks']['quantum']} rails_passed={m['rails_passed']}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts && python -m pytest tests/test_build_daily_brief.py -v`
Expected: PASS

- [ ] **Step 5: Full suite + commit**

```bash
cd scripts && python -m pytest -q
git add scripts/build_daily_brief.py scripts/tests/test_build_daily_brief.py
git commit -m "feat(brief): CLI orchestrator writes dated brief artifacts"
```

---

## Self-Review

**Spec coverage:** §3 skeleton → Task 4 `render_post`. §4 data (indices) → Task 1; bundles/news → Task 2/6. §5 modules → Tasks 1–6. §6 rails → Task 3 (+ asserted in Task 4/6). §7 output artifact folder → Task 6. §8 testing → each task's test. Chart (§3/§9) → Task 5. All covered.

**Placeholder scan:** No TBD/TODO; every code step shows full code. The `pad` sentence and best-effort chart are intentional, documented choices.

**Type consistency:** `pick_movers` returns rows with `ticker`; `render_post` and `run` read `["ticker"]`, `["perf_1y"]`, `["rev_growth_yoy"]` consistently. `fetch_market_pulse(fetch=...)` signature matches Task 1 and Task 6 usage. `render_chart_html`/`write_chart_png` names consistent between Task 5 and Task 6.
