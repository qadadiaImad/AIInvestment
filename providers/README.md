# Providers — gating classification & playbooks

Per-source rules. **First question: does the source expose a usable REST/JSON API?**
- **Yes → REST** (direct call, scriptable, fast — no browser).
- **No / gated premium metric / news → Playwright**, and then: does it meter free access on
  accumulated session/IP state? **No → Mode A** (concurrent, one tab/agent). **Yes → Mode B**
  (isolated, rotate the instance). See `../references/playwright-mcp-protocol.md`.

> **GuruFocus fundamental value** (current value + historical series + margin of safety):
> see the reusable **`../references/gurufocus-fundamental-playbook.md`** — natural render for
> the scalar; the historical-series JSON endpoint returns 200 **only through the MCP Chrome
> session** (sessionless = 403). Stored generically as `fundamental_value` (never named).

## Classification table

| Provider | Key | Transport | Gate / limit | Endpoint or extraction | What it's for |
|---|---|---|---|---|---|
| **TradingView** | `tradingview` | **REST** (scanner) | none (polite rate) | `POST scanner.tradingview.com/america/scan` | **Fundamentals, ratios, earnings, screening** ✅ verified |
| Yahoo Finance | `yahoo` | **REST** | soft rate limit | `query1.finance.yahoo.com/v8/finance/chart/{sym}` ; `/v10/.../quoteSummary` (crumb) | Prices, fundamentals ✅ verified |
| SEC EDGAR | `edgar` | **REST** | fair-access (needs UA header, ≤10/s) | `data.sec.gov/submissions/CIK{##########}.json` | Filings, S-1s, 10-Ks — IPO source of truth |
| FRED | `fred` | **REST** | free API key | `api.stlouisfed.org/fred/series/observations` | Macro, rates, electricity prices |
| stockanalysis.com | `stockanalysis` | REST/PW | none | internal `/api/` JSON ; `__NEXT_DATA__` | Clean free fundamentals & financials |
| Finnhub | `finnhub` | **REST** | free key, rate-limited | `finnhub.io/api/v1/...` | Quotes, fundamentals, news |
| Alpha Vantage | `alphavantage` | **REST** | free key, 25/day · 5/min | `alphavantage.co/query` | Quotes, fundamentals |
| Financial Modeling Prep | `fmp` | **REST** | free key, rate-limited | `financialmodelingprep.com/api/v3/...` | Fundamentals, ratios |
| Tiingo | `tiingo` | **REST** | free key | `api.tiingo.com/...` | EOD prices, news |
| Polygon.io | `polygon` | **REST** | free key, delayed | `api.polygon.io/...` | Delayed quotes |
| Nasdaq Data Link | `quandl` | **REST** | free key, dataset-scoped | `data.nasdaq.com/api/v3/...` | Datasets |
| **GuruFocus** | `gurufocus` | **Playwright B** | **~3 free views then throttle + ads** | `/stock/{sym}/valuation` → innerText/XHR | **GF Value, GF Score, valuation verdict** ✅ verified |
| News (any) | `news` | **Playwright A** | varies (some paywalled) | snapshot / innerText / JSON-LD | Headlines, catalyst articles |
| Koyfin | `koyfin` | **Playwright B** | login/paywall | (login-gated) | Quality scores, charts |
| Simply Wall St | `simplywallst` | **Playwright B** | login/paywall | embedded-JSON | Fair-value, snowflake |

> **Transport rule (corrected per owner):** REST is the default for anything with an API —
> it's faster and scriptable. **Do NOT route APIs through the browser.** Playwright is only
> for API-less pages, gated premium metrics (GuruFocus GF Value), and news. API keys live in
> a gitignored `.env`, never in committed files — see §Secrets.
>
> ✅ = endpoint verified live on 2026-05-30 (NVDA): Yahoo price `211.14`; TradingView P/E
> `32.33`, mcap `$5.11T`; GuruFocus GF Value `$334.32` / "Possible Value Trap".

---

## TradingView (`tradingview`) — flagship REST source  ⚡ no browser

Fundamentals, ratios, earnings, and screening for the whole universe via the **scanner**
endpoint — one POST returns many tickers/columns. Scriptable, fast, no gate. **Verified.**

- **Endpoint:** `POST https://scanner.tradingview.com/america/scan`
- **Body:** `{"symbols":{"tickers":["NASDAQ:NVDA"],"query":{"types":[]}},"columns":[...]}`
- **Useful columns:** `close`, `market_cap_basic`, `price_earnings_ttm`,
  `earnings_per_share_diluted_ttm`, `price_book_fq`, `price_revenue_ttm`, `dividend_yield_recent`,
  `sector`, `description`, `earnings_release_next_date`, `Recommend.All` (analyst signal).
- **Verified pull (PowerShell, 2026-05-30):**
  ```powershell
  $cols = @("close","market_cap_basic","price_earnings_ttm","earnings_per_share_diluted_ttm","price_book_fq","price_revenue_ttm","sector")
  $body = @{ symbols=@{ tickers=@("NASDAQ:NVDA"); query=@{ types=@() } }; columns=$cols } | ConvertTo-Json -Depth 6
  Invoke-RestMethod -Uri "https://scanner.tradingview.com/america/scan" -Method Post -Body $body -ContentType "application/json"
  # → NVDA: close 211.14, mcap $5.11T, P/E 32.33, EPS 6.53, P/B 26.16, P/S 20.32
  ```
- **Screening:** swap the `tickers` list for a `filter` block to scan the whole market by
  sector/metric (e.g. find undervalued L0-energy or L1-chips names) — no per-symbol loop.
- **News / charts / historical metric computation on graphs:** for these, TradingView is a
  **Playwright** target (Mode A) — the scanner API covers point-in-time fundamentals, but
  chart-derived historical series and the news feed need page rendering. Other markets: swap
  `/america/` for `/global/`, `/crypto/`, etc.
- **Sector / industry join — works for ALL sectors, not just AI (verified live 2026-05-31):**
  The existing helper `aiinvest.tradingview.scan(tickers, columns=...)` is fully generic — it
  takes any explicit ticker list and the `sector`/`industry` columns are already in
  `DEFAULT_COLUMNS`. No AI-universe coupling. The build phase's sector join should call:
  ```python
  from aiinvest import tradingview as tv
  recs = tv.scan(["NYSE:JPM", "NASDAQ:WMT"], columns=["description", "sector", "industry"])
  # each rec: {"symbol","ticker","metrics":{"sector":{"value":...},"industry":{"value":...}}}
  sector   = rec["metrics"]["sector"]["value"]     # stamped envelope, read .value
  industry = rec["metrics"]["industry"]["value"]
  ```
  Live results (non-AI tickers): `NYSE:JPM → sector="Finance", industry="Major Banks"`;
  `NASDAQ:WMT → sector="Retail Trade", industry="Specialty Stores"`. Equivalent raw endpoint:
  `POST scanner.tradingview.com/america/scan` with
  `{"symbols":{"tickers":["NYSE:JPM"],"query":{"types":[]}},"columns":["sector","industry"]}`.
  **Gotcha — the EXCHANGE PREFIX is mandatory and must be correct.** Bare symbols (`"JPM"`)
  and wrong-exchange specs (`"NYSE:WMT"`) return an EMPTY `data` array silently — no error.
  WMT is `NASDAQ:WMT`, not NYSE. The join must resolve each symbol's real exchange first
  (e.g. via the symbol-search endpoint) or carry the `EXCHANGE:SYMBOL` form in the universe.

## Yahoo Finance (`yahoo`) — REST  ⚡ no browser

- **Verified (price/52wk/prev-close):**
  `GET https://query1.finance.yahoo.com/v8/finance/chart/NVDA?interval=1d&range=1d`
  → `chart.result[0].meta` (needs a real `User-Agent` header). Returned NVDA `211.14`.
- **Fundamentals:** `https://query1.finance.yahoo.com/v10/finance/quoteSummary/{SYMBOL}?modules=price,summaryDetail,defaultKeyStatistics,financialData`
  — this module endpoint now needs a **crumb + cookie**; if it 401s, fetch a crumb first
  (`/v1/test/getcrumb` with the consent cookie) or fall back to TradingView for fundamentals.
- Soft rate limits → polite jitter; only escalate to Playwright if a hard wall appears.

## GuruFocus (`gurufocus`) — the flagship gated case  ⚑ Mode B

The reason this engine exists. Free public fundamental pages throttle after ~3 hits and
inject ads. Mirror GuruTrade's statelessness, but with detection + clean extraction.

- **URL:** `https://www.gurufocus.com/stock/{SYMBOL}/summary` and `/valuation`
  (GuruTrade used `/valuation` only — the GF Value page).
- **Protocol:** Mode B. Run alone, no other tabs. **Budget ≤2 page views per fresh
  instance**, then `browser_close()` → relaunch. Quiesce all Mode-A work first.
- **Extraction:**
  1. `browser_network_requests()` → look for GuruFocus internal API XHR (JSON) carrying GF
     Value / GF Score / ratios → `browser_network_request(url)`. Cleanest.
  2. Fallback to `innerText` + regex (GuruTrade's patterns, but **validated**):
     - `GF Score:\s*(\d+)\s*/100`
     - `GF Value:\s*\$?([\d,]+\.?\d*)`
     - `P/E:\s*([\d,]+\.?\d*)`, `P/B:\s*([\d,]+\.?\d*)`
     - `(Fairly Valued|Overvalued|Undervalued)`
     - `Market Cap:\s*\$?\s*([\d,\.]+[KMB]?T?)`
     - Scroll (`browser_evaluate(()=>window.scrollBy(0,1000))` + `browser_wait_for`) to
       lazy-load correlation/extra metrics.
- **Detect gate:** 402/403/429 in network, or text `sign in`/`upgrade`/`premium`/`limit`
  → rotate immediately.
- **Stealth:** apply the bundle (`../references/anti-gating-cookbook.md` Recipe 2) on each
  fresh instance.
- **Known GuruTrade pitfalls to avoid:** static UA/viewport (rotate them); blind always-fresh
  with no detection (we detect); dirty regex values like `current_ratio: "."` (validate per
  `../references/data-schema.md`).

---

## SEC EDGAR (`edgar`) — REST  ⚡ no browser
- **APIs:** `https://data.sec.gov/api/xbrl/companyconcept/CIK{##########}/...` and
  `https://data.sec.gov/submissions/CIK{##########}.json`; full-text search at
  `https://efts.sec.gov/LATEST/search-index?q=...`.
- **Must send a descriptive `User-Agent` header** (SEC requires it, e.g. your email).
  Fair-access: keep ≤10 req/s. Authoritative for S-1/IPO data.

## FRED (`fred`) — REST  ⚡ no browser
- **API:** `https://api.stlouisfed.org/fred/series/observations?series_id=...&api_key=...&file_type=json`.
- Useful series: electricity prices, rates, industrial production — feeds the brief's energy
  constraint analysis.

## stockanalysis.com (`stockanalysis`) — REST-ish
- Excellent free fundamentals, ungated. Prefer its internal `/api/` JSON via direct GET; if
  that's awkward, Playwright Mode A and read `__NEXT_DATA__`
  (`browser_evaluate(()=>JSON.parse(document.getElementById('__NEXT_DATA__').textContent))`).

## Keyed API providers (`finnhub`, `alphavantage`, `fmp`, `tiingo`, `polygon`, `quandl`) — REST  ⚡
- All JSON REST — **direct calls**, key in URL/header (from `.env`). Mind free-tier caps
  (Alpha Vantage strictest: 25/day, 5/min). Back off on 429.

## Koyfin / Simply Wall St (`koyfin`, `simplywallst`) — Playwright  ⚑ Mode B
- Login/paywall-gated, no clean public API. Treat as isolated; only access what the owner is
  authorized to see. Simply Wall St exposes fair-value via embedded JSON on public company
  pages. Respect ToS.

---

## Secrets
API keys go in a local **`.env` (gitignored)**, read at runtime — never hardcoded in these
docs or committed files. When this becomes a real repo, add `.env` to `.gitignore` before
the first commit.

## Adding a new provider
1. **Has a usable REST/JSON API?** → REST (direct call). Else → Playwright.
2. If Playwright: metered on accumulated state? → Mode B (isolated, rotate), else Mode A (tab).
3. Find the cleanest extraction (network XHR / JSON first).
4. Add a row to the table + a short playbook. Note gate signals and the harvest budget.
