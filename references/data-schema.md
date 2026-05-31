# Data Schema & Validation

Canonical shape for everything this engine retrieves. Stamp provenance on every datum.
Improves on GuruTrade's flat all-strings records (which let `"."` and `""` through).

## Per-metric envelope

Every value is wrapped, not bare:
```json
{
  "value": 22.4,                 // parsed, typed (number|string|bool); null if unparseable
  "raw": "22.4",                 // exact string as scraped (audit trail)
  "unit": "ratio",               // ratio|usd|pct|shares|count|usd_per_share|...
  "dirty": false,                // true if validation failed (kept for inspection, not trusted)
  "retrieved_at": "2026-05-30T14:03:11Z",   // UTC ISO-8601
  "source": "gurufocus",                      // provider key (see providers/README.md)
  "source_url": "https://www.gurufocus.com/stock/NVDA/valuation",
  "source_class": "xhr-json"     // api | xhr-json | embedded-json | dom | innertext-regex | filing
}
```

## Per-symbol record
```json
{
  "symbol": "NVDA",
  "stack_layer": "L1-chips",          // L0-energy|L1-chips|L2-infra|L3-models|L4-application
  "as_of": "2026-05-30T14:03:11Z",
  "metrics": {
    "current_price": { ...envelope... },
    "gf_value":      { ...envelope... },
    "gf_score":      { ...envelope... },
    "valuation_label": { ...envelope... },   // Undervalued|Fairly Valued|Overvalued
    "pe_ratio":      { ...envelope... },
    "pb_ratio":      { ...envelope... },
    "market_cap":    { ...envelope... },
    "enterprise_value": { ...envelope... }
  },
  "provenance": { "providers_used": ["gurufocus","yahoo"], "gate_events": [] }
}
```

## Batch / run metadata (GuruTrade-compatible)
```json
{
  "batch_metadata": {
    "batch_timestamp": "2026-05-30T14:00:00Z",
    "total_symbols_requested": 0,
    "successful_symbols": 0,
    "failed_symbols": [],
    "retrieval_mode": "mode-a-concurrent | mode-b-isolated | mixed",
    "providers_used": [],
    "total_duration_seconds": 0
  },
  "financial_data": { "<SYMBOL>": { ...per-symbol record... } },
  "processing_details": { "<SYMBOL>": { "status": "ok|gated|error", "notes": "" } }
}
```

## Validation rules (enforce before storing `dirty:false`)
- Numerics parse to a **finite** number; reject `""`, `"."`, `"-"`, `"N/A"`, `"--"`.
- `current_price` > 0; `pe_ratio` finite (allow negative for losses, flag extreme); `pb_ratio` > 0.
- `pct` fields: keep sign; plausible magnitude (reject 9999%).
- `valuation_label` ∈ {Undervalued, Fairly Valued, Overvalued} (case-insensitive) else `dirty`.
- Always keep `raw`; on failure set `value:null, dirty:true` — never silently drop or store junk.

## Storage layout
```
data/
  YYYY-MM-DD/
    <provider>_<scope>_<UTCtimestamp>.json     # e.g. gurufocus_ai-stack_20260530T140311Z.json
    batch_aggregated_<UTCtimestamp>.json
```
One file per run; never overwrite — timestamps make every pull auditable and decay-trackable.
