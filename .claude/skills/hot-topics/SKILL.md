---
name: hot-topics
description: Rank the hottest tickers and themes of the last N days (default 30) from the local refreshed bundles — news volume/recency × price action + material congressional filings. Use when asked "what's hot", to seed carousels/reels/briefs, or before a detect stage.
---

# Hot Topics — last-N-days attention ranking

Deterministic, offline ranking over the already-refreshed bundles. **Refresh first**
(`python scripts/refresh_all.py` or at least `refresh_daily.py`) — numbers are perishable;
the CLI prints the bundle `generated_at` stamps so staleness is visible.

## Run

```
cd scripts
python hot_topics.py --days 30 --top 15          # human table
python hot_topics.py --days 30 --top 15 --json   # machine-readable (feed to agents)
```

## How the score works (aiinvest/hot_topics.py — unit-tested)

- **News**: each in-window article adds a recency weight (fresh ≈ 2×, month-old ≈ 1×) per tagged ticker.
- **Price action**: news score is multiplied by `1 + |perf_1y|/100` from site/quantum screener rows.
- **Congress**: material filings in-window (`amount_range_low ≥ $15,001`, dated by `filing_date`)
  add a flat boost scaled by amount and count. Congress rows are **public record, dated —
  not accusations, not trading signals**; they only measure attention.
- Themes: top keywords across in-window headlines (stopworded).

## Rails for anything written from this output

No first person; never "GuruFocus"/"GF" (say "fundamental value"); never name a news outlet
("reportedly"); certainty labels (filed/reported/rumored); congress framing as above;
NFA/DYOR; stamp data as of the bundle date (UTC). Never launder a score into a recommendation.

## Typical chain

`refresh_all.py` → `hot_topics.py --json` → detect/build agents (stock-carousel skill,
reel kit, daily brief) pick from the ranked list instead of re-mining raw JSON.
