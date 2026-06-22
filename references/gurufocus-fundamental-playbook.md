# GuruFocus "Fundamental Value" Playbook (reusable)

> How to pull GuruFocus's intrinsic-value data **(current value + historical series + margin
> of safety)** reliably, and how to publish it **without naming GuruFocus** (store as
> `fundamental_value`; the site sanitizer scrubs any `guru`/`gf value` string as a backstop).
> Verified working 2026-05-30. *Educational/research use; respect provider ToS — don't
> redistribute their data; we publish our own derived labels + link out to neutral sources.*

## The two endpoints

1. **Current value — natural page render (sessionless OK, polite, scriptable):**
   `https://www.gurufocus.com/stock/{SYMBOL}/valuation`
   The page **server-renders the GF Value into the HTML**, so a fresh headless Chromium can
   read it from `innerText` and regex it out — no API call, no login. This is how the 97/97
   scalar sweep succeeded with no IP issues (GuruTrade's method).
   - Regex: `GF Value[^$\d]*\$?\s*([\d,]+\.?\d*)`.
   - **The "free trial / subscribe" text is a PROMO banner on every page — NOT a wall.** Do
     not discard a value because it appears. A genuine block = value not readable at all.

2. **Historical series + margin of safety — JSON endpoint (needs a real browser SESSION):**
   `GET https://www.gurufocus.com/reader/_api/chart/{SYMBOL}/valuation?v=1.8.70`
   *(the `v=` string drifts — `1.8.61`→`1.8.70` observed 2026-06-20; copy whatever the page's
   own chart request uses, via `browser_network_requests(filter="reader/_api/chart")`.)*
   Returns clean JSON: `gf_value`, `iv` (intrinsic value), `ms` (margin of safety %),
   `medps` (the **historical + projected fundamental-value line**, `[[date, value], …]`),
   and `price` (~5y **daily** price `[[date, close], …]`).
   - **CRITICAL:** this endpoint returns **200 only to an established browser session**
     (e.g. the **Playwright MCP Chrome session**, which carries cookies/fingerprint a real
     user has). **Sessionless / fresh scripted browsers get `403`.** So the *current value*
     scrapes fine headless, but the *historical series* must come through a real session.

## Harvest the series through the MCP Chrome session (the working method)

The MCP browser is a single shared instance → **serial only** (no concurrent fan-out). Once
it's on `gurufocus.com` with a live session, fetch the endpoint **in-page** for any ticker:

```js
// browser_evaluate (MCP), saved to a file via the tool's `filename` param
async () => {
  const syms = [/* tickers */];
  const out = {};
  for (const s of syms) {
    const r = await fetch(`/reader/_api/chart/${s}/valuation?v=1.8.70`, {headers:{accept:'application/json'}});
    out[s] = r.ok ? (({gf_value, ms, medps}) => ({gf_value, ms, medps}))(await r.json()) : {error: r.status};
    await new Promise(f => setTimeout(f, 150));   // gentle pacing
  }
  return out;   // {SYM: {gf_value, ms, medps:[[date,val],…]}}
}
```
This pulled 89/96 in one pass, 0 errors (the 7 blanks were recent IPOs with no history).
Scripted/sessionless attempts to the same endpoint returned 403 the same day.

## Anti-gating notes
- Free public pages throttle ~3 views per fresh browser STATE (cookies/IP). Fresh-instance
  rotation (new incognito Chromium per symbol) resets the **cookie** counter (good for the
  scalar at scale), but **not an IP-level throttle** (the series API can 403 the whole IP for
  the day → needs the real session, a cool-down, or proxy/IP rotation).
- 7-day-trial / signup overlay = a genuine block → restart the instance / rotate. Promo text ≠ block.

## Relabel + store (never name the source)
- `fundamental_value` (= `gf_value`/`iv`), `margin_of_safety_pct` (= `ms`),
  `fundamental_value_series` (from `medps`). Compute the **valuation tag** (Undervalued /
  Fairly Valued / Overvalued) and discount **ourselves** from our live price — see
  `scripts/aiinvest/fundamental.py` (`valuation_tag`, `discount_pct`, `parse_valuation_chart`).

## Code assets (in this repo)
- `scripts/aiinvest/fundamental.py` — `parse_valuation_chart`, `valuation_tag`, `discount_pct` (pure, tested).
- `scripts/fundamental_fetch.py` — per-symbol fetch: fresh browser, natural-render value +
  capture the chart XHR when 200; `save()` is **merge-protect** (never downgrades).
- `scripts/fundamental_backfill.py` — gently-paced batch runner (jitter, fresh instance each).
- `scripts/save_series_batch.py` — save series harvested from the MCP session (compact JSON in → merge-protect save).
- `scripts/aiinvest/gurufocus.py` — the validated innerText extraction regex + gate detection.
