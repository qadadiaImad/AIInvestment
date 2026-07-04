# Daily Market Brief — Design Spec

**Date:** 2026-07-02
**Status:** Approved (design); pending spec review → implementation plan
**Owner:** AIInvestment content layer

> Educational / market commentary only — **not financial advice**. All numbers are perishable
> and must be live + UTC-stamped (CLAUDE.md Rule #1).

---

## 1. Purpose

A once-daily, LinkedIn-friendly **market rundown** in the voice of a hedge-fund morning note /
financial-news desk — opening wide on the broad tape, then drilling into this project's edge (the
AI value chain + quantum/frontier). Auto-generated from the live data bundles so it can ship every
session day with minimal editing.

**Success criteria**
- A single, paste-ready LinkedIn post (~200–300 words) plus a dark-mode "chart of the day" image.
- Every datum live + UTC-stamped with `source_class`; nothing fabricated.
- Passes all project rails automatically (see §6).
- Reproducible from a single CLI command for a given date.

## 2. Scope / Non-goals

**In scope:** the post skeleton, a light index/macro REST helper, mover-ranking reuse, the
chart-of-the-day render, the file artifact + provenance.

**Non-goals (YAGNI):** Studio app page (deferred — artifact only for now); auto-posting to
LinkedIn; congress as a *fixed* section (may appear opportunistically, not guaranteed); broad
commodities/FX/crypto coverage; multi-post scheduling.

## 3. The post skeleton (fixed shape)

Institutional desk-note tone, third person, ~200–300 words:

1. **Hook + Market pulse** *(opening, 2–3 sentences)* — leads with the tape: S&P 500 & Nasdaq
   direction, VIX level, US 10Y yield; states the risk-on/off read.
2. **AI-stack spotlight** — the day's key AI value-chain move (chips / infra / models / apps):
   one hard number (e.g. 1-day or 1-year move, a growth/valuation figure) + the *why*, attributed
   to "the data" / "the tape" / "analysts".
3. **Quantum & frontier** — a notable quantum / frontier-tech mover, framed momentum-vs-fundamentals.
4. **What to watch** *(close)* — 1–2 concrete forward catalysts for the session/week ahead.
5. **Footer** — `Educational — not advice.` + UTC datestamp + 3–5 hashtags.

### Example (illustrative shape, not live numbers)
> **Risk-on tape, but the leadership is narrowing.** The S&P closed +0.6% and the Nasdaq +0.9% as
> the VIX slipped to ~13 and the 10Y held near 4.2% — a calm bid, led once again by a handful of AI names.
>
> **AI stack —** [Ticker] did the heavy lifting, up [X]% on [reported catalyst]. On the data it still
> trades at [multiple] versus a sector median of [median] — leadership that isn't yet expensive on earnings.
>
> **Quantum —** [Ticker] jumped [X]% on [reported item], even as revenue [trend] — a tape running ahead
> of the fundamentals, not because of them.
>
> **Watch:** [catalyst 1]; [catalyst 2].
>
> Educational — not advice. Data as of 2026-07-02 21:00 UTC. #AIstocks #Markets #Semiconductors #Quantum

## 4. Data sources

| Datum | Source | source_class |
|---|---|---|
| S&P 500 (`^GSPC`), Nasdaq (`^IXIC`), VIX (`^VIX`), 10Y (`^TNX`) | Yahoo chart REST; stooq fallback | api / xhr-json |
| AI-stack & quantum movers, ratios | existing `web/public/data/{site,quantum}.json` screeners | filing/api (as bundled) |
| Headlines / catalysts | existing `web/public/data/news.json` | html/api (as bundled) |
| Congress (optional) | existing `web/public/data/congress.json` | filing |
| Price curve for chart | existing `web/public/data/prices/<SYM>.json` | api |

**Index/macro endpoint (REST-first):**
`https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d`
→ `chart.result[0].meta.regularMarketPrice` and `.chartPreviousClose` → 1-day % change.
`^TNX` is the 10Y yield ×10 (divide by 10 for the percent). Fallback: stooq CSV
(`https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcv&h&e=csv`). Every value stamped `retrieved_at` (UTC ISO-8601) + `source`.

## 5. Architecture

Small, single-purpose, TDD'd modules following existing `scripts/aiinvest/` patterns:

- **`scripts/aiinvest/market.py`** — index/macro REST helper.
  - `fetch_market_pulse() -> dict`: returns `{ "sp500": {price, change_pct, retrieved_at, source, source_class}, "nasdaq": {...}, "vix": {...}, "ten_year": {...} }`. Yahoo primary, stooq fallback, validates numeric (rejects null/dirty).
- **`scripts/aiinvest/daily_brief.py`** — assembly + selection + copy.
  - `pick_movers(bundles) -> {ai: MoverRef, quantum: MoverRef}`: reuses the carousel "hottest" ranking (news heat × magnitude of move) constrained to AI-stack vs quantum sets.
  - `build_brief(date, pulse, bundles) -> Brief`: pure data model (no I/O).
  - `render_post(brief) -> str`: the ~200–300-word markdown post + hashtags.
  - `rail_check(text) -> list[str]`: returns rail violations (empty = clean) — see §6.
- **`scripts/build_daily_brief.py`** — CLI orchestrator.
  - `--date YYYY-MM-DD` (default: latest bundle date). Fetches pulse, loads bundles, builds brief, renders post, renders chart, writes artifacts, prints a provenance summary. Refuses to write if `rail_check` is non-empty (fails loud).
- **Chart of the day** — reuse the carousel dark-mode HTML/CSS template; a small render function emits a 1200×1200 PNG of the top AI-stack mover's price curve (inline SVG from `prices/<SYM>.json`), headless-rendered, then read back for self-QA.

## 6. Rails (enforced by `rail_check`, not just convention)

- No first person (`\b(I|me|my|we|our|us)\b`, case-insensitive, word-boundary) in the post body.
- No news-outlet names (denylist: Yahoo, Bloomberg, Reuters, CNBC, Motley/Fool, Barron, Seeking Alpha, …) — use "reportedly".
- Never the strings "GuruFocus" / "GF" — only "fundamental value".
- Must contain a not-advice disclaimer and a UTC datestamp.
- If a congress item is included: must carry its filing date and public-record framing (asserted by test).
- Word count within 180–320 (soft target 200–300).
- All numbers traceable to a stamped source in `meta.json`.

## 7. Output

`content/daily_brief/<YYYY-MM-DD>/`:
- `brief.md` — the paste-ready post + hashtags.
- `chart.png` — the dark-mode chart of the day (1200×1200).
- `meta.json` — provenance: `{ date, generated_at, picks: {ai, quantum}, market_pulse: {...stamped}, sources: [...], rails_passed: true }`.

## 8. Testing (TDD)

- `market.py`: mocked HTTP → correct parse of Yahoo & stooq; % change math; `^TNX` /10; dirty-value rejection; fallback path.
- `daily_brief.py`: `pick_movers` chooses expected tickers from fixture bundles; `render_post` shape (sections present, word count); `rail_check` catches injected first-person / outlet / "GuruFocus" / missing-disclaimer cases.
- CLI smoke: runs against fixture bundles → writes the three artifacts; refuses on a seeded rail violation.

## 9. Resolved decisions (approved 2026-07-02)
- **Hashtags:** per-topic, 3–5, derived from the day's picks (not a fixed set).
- **Chart of the day:** the top AI-stack mover's price curve (default).
- **LinkedIn image size:** 1200×1200 square.
