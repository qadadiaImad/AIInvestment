# NVDA — Carousel Brief (2026-06-03)

Educational / market commentary only — **not financial advice. DYOR.** Congress data is
**public record**: not an accusation, not a trading signal. Figures stamped **as of 02 Jun 2026**
and will decay.

---

## Posting order
1. `slide_1.html` — INTRO: 5-yr price curve (price line only) + **+19.5% YTD**; headline = Pelosi NVDA disclosure.
2. `slide_2.html` — THE GAP: $222.82 price vs **$336.11 fundamental value** (33.7% discount / 36.1% margin of safety).
3. `slide_3.html` — BUILDING BLOCKS (semis): ROIC, gross margin, rev growth, P/E vs peers; dominant factor = **ROIC ~106%**.
4. `slide_4.html` — CONTINUED: P/FCF, net margin, debt/equity, P/S vs peers.
5. `slide_5.html` — NEWS: Truist/GTC Taipei + NVDA-vs-Broadcom + the deferred Pelosi detail; DYOR + not-an-accusation beat.

---

## Caption (paste-ready)

> NVDA is up ~20% YTD and just printed a fresh political footnote: a congressional disclosure shows a Nancy Pelosi NVDA **purchase** in the $250,001–$500,000 range (txn 16 Jan 2026, filed 23 Jan 2026, House Clerk PTR). Public record — not an accusation, not a signal.
>
> The more interesting question for me: the tape says $222.82, but my own fundamental-value read lands at **$336** — a ~34% discount. Why? Not because it's "cheap" on sales (P/S ~21x is actually rich vs peers) — it's the **capital machine underneath**: ROIC near **106%**, gross margin **74%**, net margin **63%**, revenue still growing **~71% YoY**, all on a balance sheet with almost no debt (D/E 0.07). That quality is what lets a 34x P/E coexist with a value estimate above the price.
>
> Swipe for the full walkthrough 👉
>
> Educational / market commentary only. Not financial advice. Do your own research.
> #NVDA #semiconductors #investing #stockmarket #AIstocks

---

## Full fundamental walkthrough (script text)

**The setup.** NVDA closed at **$222.82** on 02 Jun 2026, a **$5.39T** market cap, **+19.5% YTD**
(from $186.50 at 2025 year-end) and **+62% over the last year**. My fundamental-value estimate is
**$336.11**, which puts the stock at a **33.7% discount** / **36.1% margin of safety** on my read.
That's the creator's own model output — an estimate, not a price target.

**Building blocks (semis ratio map: P/E, P/FCF, gross margin, ROIC, revenue growth).** Compared to the
median of 21 named semiconductor peers (from the cached stock bundle):

| Metric | NVDA | Peer median | Read |
|---|---|---|---|
| ROIC | **106%** | ~18% | ~6x — dominant factor |
| Gross margin | 74.1% | ~55% | well above |
| Revenue growth YoY | +71% | ~23% | ~3x |
| P/E | 34x | ~62x | below peers |
| P/FCF | 49x | ~75x | below peers |
| Net margin | 63% | ~23% | ~3x |
| Debt / equity | 0.07 | ~0.30 | far less levered |
| P/S | 21x | ~17x | the one rich number |

**The one factor.** Subjectively, the value is carried by **ROIC near 106%** — every dollar reinvested
earns back roughly itself, which is extraordinary for a hardware business. Paired with 74% gross margins,
that capital efficiency is what lets the model justify a worth above today's price *even at* a 34x P/E.

**The honest counterweight.** P/S (~21x vs ~17x peers) is the one ratio that looks expensive. The reason
it still hangs together: **63% net margins** convert those sales into profit at a rate peers can't match,
so the P/E and P/FCF come back down to *below*-peer levels. If growth or margins slip, the discount thins
fast — the cushion is conditional.

**News & public record (slide 5).**
- Hottest (slide 1 headline): Pelosi NVDA purchase disclosure — see below.
- 2nd: "Nvidia's GTC Taipei Announcements Offer Significant Growth Potential, Truist Says" (Yahoo Finance, 02 Jun 2026, *reported*).
- 3rd: "NVIDIA vs. Broadcom: Which Is the Better Long-Term AI Chip Bet?" (Yahoo Finance, 02 Jun 2026, *reported*).

---

## Congress angle (materiality applied)

Among 125 NVDA congressional transactions on record, the freshest **material purchase** is:
**Nancy Pelosi · type "P" (purchase) · amount range $250,001–$500,000 · transaction date 16 Jan 2026 ·
filed 23 Jan 2026** (House Clerk Periodic Transaction Report). This clears the materiality bar (a
six-figure purchase range, recent, a buy), so per the rules it **leads as the slide-1 headline** and the
full detail is repeated on slide 5. Public record only — not an accusation, not a trading signal.

(Context, not used as headline: an earlier Pelosi NVDA "P" of $100,001–$250,000 dated 30 Dec 2025 is also
on record; the 16 Jan 2026 buy is larger and more recent, so it headlines.)

---

## HIGGSFIELD hero prompt (cover frame)

```
A cinematic dark-fintech hero frame, 4:5 vertical. A single sleek silicon wafer / GPU die rendered in
brushed graphite and emerald-green edge lighting, floating above a calm reflective black surface. Faint
volumetric green and electric-blue light beams in the deep background, subtle particle bokeh. One bold
floating glass-morphism panel, lower third, with a clean upward price line in emerald green. Premium,
restrained, editorial — think a serious markets publication cover, NOT a meme. High contrast, deep
shadows, soft rim light, shallow depth of field, photorealistic, 8k, no text, no logos, no faces.
Negative: clutter, neon overload, cartoon, stock-photo cheesiness, watermarks, garbled text.
```
Overlay the ticker "NVDA" + "+19.5% YTD" in your own typeface afterward (keep the AI render text-free).

---

## Sources & numbers used

- **Fundamental value $336.11 / margin of safety 36.11% / discount 33.7%** — `content/carousel_2026-06-03/_guru.json` (NVDA) + `web/public/data/site.json` stocks.NVDA.valuation.
- **Price $222.82, mkt cap $5.39T, P/E 34.1, P/B 27.6, P/S 21.4** — `web/public/data/site.json` valuation.
- **YTD +19.5% (186.50→222.82), 1Y +62.2%, 5-yr curve ($12→$223)** — `web/public/data/prices/NVDA.json` (retrieved 2026-06-02).
- **Fundamentals** (gross 74.1%, op 64.0%, net 63.0%, FCF 41.8%, ROE 114%, ROA 83%, **ROIC 106.2%**, D/E 0.066, current ratio 3.44, rev growth +70.7%, EPS growth +110%, P/FCF 48.5) — `site.json` stocks.NVDA.fundamentals.
- **Peer medians (21 named Semiconductors)** — computed from `web/public/data/site.json` (industry=="Semiconductors"): P/E ~62x, P/FCF ~75x, P/S ~17x, gross margin ~55%, ROIC ~18%, rev growth ~23%, net margin ~23%, D/E ~0.30. (Live `aiinvest.peers.scan_industry` returned only gross-margin populated this run; medians sourced from the cached site bundle — quantitative, 21-name basis.)
- **News** — `web/public/data/news.json` (NVDA-tagged, all *reported*, Yahoo Finance, 02 Jun 2026).
- **Congress** — `web/public/data/congress.json` (Pelosi NVDA "P" $250,001–$500,000, txn 16 Jan 2026, filed 23 Jan 2026, House Clerk PTR).

*Not financial advice. Educational/market-commentary only. DYOR. Congress = public record, not an accusation, not a signal.*
