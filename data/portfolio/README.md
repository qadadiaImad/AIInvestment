# data/portfolio/ — owner positions (never committed)

This directory holds the PORTFOLIO module's input: your real holdings. It is read by
`scripts/build_portfolio.py` to compute exposure, P&L, and risk for the gated
`/terminal/portfolio` desk.

`positions.json` is your real, private data. It is **gitignored** — see the root
`.gitignore`'s `data/portfolio/` block. Only `positions.example.json` and this README are
committed as templates.

## Setup

```bash
cp data/portfolio/positions.example.json data/portfolio/positions.json
```

Edit `data/portfolio/positions.json` with your real holdings:

```json
{
  "base_currency": "USD",
  "cash_usd": 1000.00,
  "positions": [
    { "symbol": "NVDA", "quantity": 10, "cost_basis_per_share": 400.00,
      "acquired_date": "2024-01-10", "note": "core position" },
    { "symbol": "MSFT", "quantity": 20, "cost_basis_per_share": 250.00,
      "acquired_date": "2024-02-01" }
  ]
}
```

Field rules (see
`docs/superpowers/specs/2026-07-15-portfolio-design.md` §1 for the full binding contract):

- `base_currency` — optional, only `"USD"` supported (no FX conversion in v1).
- `cash_usd` — optional, defaults `0.0`; must be `>= 0`.
- `positions[].symbol` — **required**. Row dropped if missing/empty.
- `positions[].quantity` — **required**, must be `> 0`. Row dropped otherwise.
- `positions[].cost_basis_per_share` — optional. If missing/invalid, P&L is unavailable
  for that lot (position still gets a market value and weight).
- `positions[].acquired_date` — optional ISO `YYYY-MM-DD`.
- `positions[].note` — optional free text, truncated to 280 chars.
- Multiple rows with the same `symbol` are merged into one position (lots summed,
  cost-weighted-average cost basis, earliest acquired date).
- Unknown symbols (not in the AI-stack universe, no price file) are **never dropped** —
  they appear with quantity/cost-basis but null price/market-value/weight/layer, so you
  can see they're tracked even if unpriced.

## Run

```bash
cd scripts
python build_portfolio.py
```

This reads `data/portfolio/positions.json` + `web/public/data/site.json` +
`web/public/data/prices/*.json` and writes `web/data/portfolio.json` — **never**
`web/public/data/`, and never committed. The gated `/terminal/portfolio` page (and its
percentage-only capture card at `/terminal/card/portfolio`) reads that file server-side.

If `data/portfolio/positions.json` doesn't exist yet, `build_portfolio.py` degrades
gracefully to an empty-state bundle and exits 0 — this is normal on a fresh clone, not an
error. The daily refresh (`scripts/refresh_daily.py`) runs this step automatically
whenever `build_portfolio.py` is present.

Educational/research only — not financial advice.
