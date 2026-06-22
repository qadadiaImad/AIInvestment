---
name: stock-carousel
description: >
  Build a social-media CAROUSEL (4-5 posts/slides) for each of the 3 hottest stocks in scope
  (AI value chain / Quantum / Congress), with a GuruFocus-grounded fundamental-value walkthrough.
  Whenever Fundamental Value is discussed: pull the necessary fundamentals from the stock's
  GuruFocus page via Playwright MCP, list the SECTOR-RELEVANT ratios that explain the price,
  compare them to industry ratios, and give a complete subjective walkthrough of the top factor.
  Renders as a mix of HTML/CSS slides + Higgsfield hero images. EXECUTE AS A WORKFLOW.
  Triggers: "stock carousel", "fundamental walkthrough", "carousel posts", "fundamental value
  breakdown", "explain the price", "hottest stocks posts".
---

# Stock Carousel — fundamental-value walkthrough as a 4-5 post carousel (×3 stocks)

Educational/market commentary only — **not financial advice**. Congress data = **public record,
not an accusation and not a trading signal**. Attention-first content phase: **no product / app /
"AI Stack" / terminal mention** anywhere (capture audience first). Never write "GuruFocus"/"GF" in
output copy — call the intrinsic estimate **"fundamental value"**.

## What it produces
For the **3 hottest stocks**, a carousel of **4-5 slides each**:

1. **Intro slide** — the stock's **price curve (price only, NO fundamental-value overlay)** + **YTD
   return**, and a one-line text featuring the **single hottest news** for that stock. **If a
   congressional disclosure with a material $ amount exists, that congress move IS the headline**
   (people find political signals compelling); the 2nd/3rd news items are deferred to the LAST slide.
2. **Slide 2** — set-up: the gap between price and **fundamental value** (price vs fundamental value,
   discount/premium %), framed as **analysts' fundamental-value model** (third person — NEVER "I / my /
   me / we / our"; attribute to "analysts" or "the data").
3. **Slide 3** — **fundamental value & its building blocks**: the SECTOR-RELEVANT valuation ratios that
   explain the value (see Ratio map), each shown **vs the industry median**, and a subjective call-out
   of the **TOP factor** justifying the value. (We don't reproduce the exact sector formula — we
   highlight the dominant factor in plain English.)
4. **Slide 4** — continuation of the fundamentals walkthrough (the next 1-2 ratios / margins / growth /
   balance-sheet item vs industry); if the fundamentals are fully covered, roll into news.
5. **Slide 5** — the remaining **2nd & 3rd news** items (incl. any deferred congress detail), with
   certainty labels and the not-advice/DYOR + (for congress) not-an-accusation beat.

## Fundamental data — GuruFocus via Playwright MCP (Mode B, orchestrator-serial)
For only ~3 focal stocks the gated fetch is cheap. The orchestrator (not parallel agents — one shared
MCP browser) drives it:
- Navigate `https://www.gurufocus.com/stock/{SYM}/valuation` (foreign: `XPAR:ALKAL` etc.), confirm 200,
  then same-origin `browser_evaluate` fetch of `/reader/_api/chart/{SYM}/valuation?v=…` (fundamental
  value + medps/iv/gf_valuation) and, if deeper ratios are needed, `/reader/_api/stocks/{stockid}/financial`
  + `/reader/_api/gf_rank/{EXCH:SYM}`. Parse with `aiinvest.fundamental.parse_valuation_chart`.
- The harvested `fundamental_value`/series already in `data/fundamental/<SYM>.json` and the company
  ratios in `web/public/data/{site,quantum,congress_stocks,extra}_stocks.json` (P/E, P/B, P/S, margins,
  ROE/ROA/ROIC, debt/equity, current ratio, rev/eps growth, sector, industry) are the primary inputs;
  use the live MCP fetch to refresh/fill gaps.
- **Industry comparison:** `aiinvest.peers.scan_industry(industry, columns)` (REST) for the median of
  each ratio across the stock's industry — that's the "vs industry" column.

## Sector → top-ratio map (which ratios "explain" the value; highlight the dominant one)
- **Software / Application / Tech Services** → P/S, EV/Rev, rev growth, gross margin, Rule-of-40.
- **Semis / Chips / Hardware / Electronic Tech** → P/E, P/FCF, gross margin, ROIC, rev growth.
- **Energy / Utilities / Power** → EV/EBITDA, P/E, dividend yield, debt/equity, FCF.
- **Financials / Banks** → P/E, P/B, ROE, net interest trend.
- **Quantum pure-plays / pre-revenue** → P/S (or "no earnings → story-priced"), cash runway, rev growth,
  burn; be explicit the price is narrative, fundamental value tiny.
- **Healthcare / Pharma** → P/E, P/FCF, margins, pipeline (qualitative).
- Fallback → P/E, P/S, ROIC, growth, margin. Always pick ONE dominant factor and say why (subjectively).

## Rendering — HTML/CSS + Higgsfield (DUAL-MODE design system)
Render slides as standalone vertical **HTML/CSS** (1080×1350) via the headless browser (NOT matplotlib —
matplotlib looks flat). **Two surfaces of ONE brand**, chosen by content type:
- 🌑 **Dark** (data/analysis): charts, curves, big numbers, ratio walkthroughs. bg `#0A0D12` + emerald
  radial glow + faint 40px grid; mono numbers; sharp. Price curve = inline SVG from
  `web/public/data/prices/<SYM>.json`; fundamental line emerald glow (`#10B981`), projected dashed cyan
  (`#38BDF8`); ratio cards = company value + industry median + colored over/under badge.
- ☀️ **Soft** (story/news/**congress**): intro hook, news, congress disclosure, closing takeaway. warm
  cream gradient `#FAF7F0→#E7DECB` + faint grain; rounded; elegant serif headline.
- 🔗 **Shared spine** (both): accent emerald `#10B981`; fonts **Fraunces** (display) + **Inter** (body)
  + **JetBrains Mono** (numbers/labels, via Google Fonts @import); same margins + small wordmark; ink
  `#16181D` (soft) / `#E8EDF2` (dark). Reference template: `higgs/_build_v2.py`.
- **Mapping:** intro hook = soft; price/fundamental/ratio slides = dark; congress disclosure slide = soft;
  closing news/takeaway = soft (or a dark "big number" if it's a stat). So a carousel breathes soft→dark→soft.
- **Visual QA (required):** after rendering, OPEN each slide in **Playwright MCP** (`browser_navigate` to
  the file:// path, `browser_screenshot`) or read the PNG, and FIX layout issues — clipped/overflowing text,
  labels colliding with the chart edge, bad wrapping — then re-render. Do not ship un-inspected slides.
- Use **Higgsfield** for HERO/aesthetic imagery (not data charts) — emit a copy-paste Higgsfield prompt per
  carousel for an attention-grabbing cover frame; keep it on-brand and de-cringe (see the higgsfield-ugc
  persona/tone). Data slides stay HTML/CSS for accuracy.
- Output to `content/carousel_<YYYY-MM-DD>/<TICKER>/slide_1.html … slide_N.html` + `brief.md`
  (caption, posting order, the fundamental walkthrough text, Higgsfield prompt, sources/numbers).

## Hard rails
- Not financial advice; DYOR. Congress = public-record disclosure only, not accusation, not a signal.
- Respect certainty labels (filed/reported/rumored). Use only real headlines + real numbers from the
  data files; never fabricate. No product/app/terminal mention (attention-first).
- **No first person anywhere** (no "I / my / me / we / our"): attribute valuation reads to **"analysts"**
  / "an analyst fundamental-value model" / "the data", and political trades to **"congress" / "a House
  member" / "the filing"**.
- **Never name the news source** — do NOT write "Yahoo" (or any outlet). If a headline came from there,
  slightly rephrase and present it as **"reportedly"** with no outlet named.

## Execution — AS A WORKFLOW
1. **Detect** (1 agent): rank the 3 hottest stocks from `news.json` + `congress.json` (+ the stock bundles);
   for each, assign the headline (congress $-move first if material) and order the news across slides.
2. **Build** (parallel, 1 agent per stock): generate the 4-5 HTML/CSS slides + `brief.md` + Higgsfield
   hero prompt per stock, with the GuruFocus-grounded fundamental walkthrough vs industry.
3. **Verify**: files present, rails present, no product mention, numbers traceable to the data files.
The gated GuruFocus MCP fetch for the 3 focal stocks is done by the orchestrator (serial) before/around
the Build phase; the workflow parallelism is the per-stock slide generation.
