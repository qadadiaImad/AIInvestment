# RUNBOOK — how to run the AI-stack research flow (as of today)

Educational research only — **not financial advice.** Every run pulls **live, UTC-stamped**
data; numbers decay, so re-run to refresh.

## 0. One-time setup
```
cd scripts
pip install -r requirements.txt      # requests, pytest
python -m pytest -q                  # sanity: should be all green
```

## 1. Single ticker — the agentic flow

**Step A — live data (deterministic, you run it):**
```
python analyze.py NVDA               # pull_dossier (TradingView+Yahoo+EDGAR+peers+history) -> fact sheet
```
Writes `data/<date>/dossier_NVDA_*.json` and `factsheet_NVDA_*.json`.

**Step B — GuruFocus GF Value (gated, optional).** GF Value has no REST API and is rate-gated,
so it's a Playwright/MCP step:
- In **Claude Code**, ask: *"fetch GuruFocus GF Value for NVDA"* — I open the `/valuation`
  page (Mode-B, isolated, rotates the instance), save the page text, and you re-run:
  `python analyze.py NVDA --gf-text-file <saved.txt>`
- Without it, the dossier still has price/fundamentals/peers/history; only GF Value is blank.

**Step C — the analysis (agentic, me):**
In Claude Code, say: **`analyze NVDA`**. I follow `skills/analyst/SKILL.md`: read the fact
sheet, write the narrative (valuation take, the one bottleneck, bull/base/bear scenarios,
risks, synthesis) — facts from the sheet, never invented — then run:
```
python render_dashboard.py NVDA --narrative <narrative.json>
```
→ `nvda_dashboard.html` (valuation · fundamentals · performance · multi-year history
sparklines · peer-vs-industry/layer percentiles · bottleneck · counterparties · catalysts ·
scenarios · risks · disclaimer).

## 2. Whole stack
```
python pull_ai_stack.py              # fundamentals for all 97 names (one TradingView POST)
python build_capital_web.py          # relationship graph -> capital_web.html (106 nodes, sourced edges)
# pull_dossier.py for each ticker you want in the screener, then:
python build_screener.py             # ranked sortable table -> stack_screener.html
```

## 3. View the HTML
Open the `.html` files directly, or serve them:
```
cd ..                                # repo root
python -m http.server 8000
# browse http://127.0.0.1:8000/nvda_dashboard.html  (and capital_web.html, stack_screener.html)
```

## 4. Resume a Claude Code session after restarting the terminal
- `claude --continue` — resume the most recent session in this folder, OR
- `claude --resume` — pick from a list.
- State also lives in `ROADMAP.md` (what's built) and your `MEMORY.md` (architecture), so a
  fresh session can pick up from there.

## Data sources (transport)
REST (no browser): TradingView scanner (fundamentals/peers/earnings), Yahoo chart + Yahoo
fundamentals-timeseries (multi-year history, keyless), SEC EDGAR (filings), FRED (macro).
Playwright/MCP (gated/no-API): GuruFocus GF Value, news. See `providers/README.md`.
