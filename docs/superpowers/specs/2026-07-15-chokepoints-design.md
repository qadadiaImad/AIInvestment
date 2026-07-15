# Round 6 — Supply-Chain Chokepoint Layer — Merged Design Spec (v1)

> Role: lead architect merging two independent design passes (Design A: curator + dataset,
> Design B: map/UI) into one shippable v1. This document supersedes both — where they
> disagreed, this doc states the final decision and why. No files outside this spec and
> `chokepoints_source.json` were created by this merge pass; `scripts/build_chokepoints.py`,
> `web/lib/chokepoints.ts`, and the UI components are specified here for the *next* round to
> build.
>
> Educational / research only — not investment advice. NFA on every capture surface.

---

## 0. What changed in the merge (read this first)

Both source designs were strong but disagreed on two load-bearing points. Both are resolved
here in favor of **actual repo convention**, verified live against the codebase this pass:

1. **Storage tier of `web/public/data/chokepoints.json`.** Design B asserted it should be
   *committed* (like `capital_web.json`) because `/chokepoints` is a public page and "must
   build on Vercel without the owner's machine." This is **wrong** — verified this pass:
   `git ls-files web/public/data/` returns **nothing**; the entire directory is gitignored
   (`.gitignore` line: `web/public/data/`), including `graph_analysis.json`, which
   `/resiliency` already reads. Every existing bundle in that directory (`risk.json`,
   `archetypes.json`, `macro.json`, `graph_analysis.json`, `site.json`, `ta_desk.json`,
   `backtests.json`, `congress.json`) is a **generated, gitignored, owner-machine-produced**
   artifact, and every reader (`lib/risk.ts`, `lib/ta.ts`, `getGraphAnalysis()` in
   `lib/data.ts`) is `existsSync`-guarded and **never throws** — the site is expected to
   render a graceful empty/degraded state on a fresh clone or a Vercel build that hasn't
   had the pipeline run. `chokepoints.json` follows this exact same tier: **generated,
   gitignored, guarded reader.** Design A had this right; Design B's contract is corrected
   below (§2, §5).
2. **The curated *source* file is the one that's committed**, exactly like
   `capital_web.json` — `chokepoints_source.json` at repo root, hand/AI-curated, versioned
   in git, reviewed like any other committed input. This is Design A's model and it stands.
3. **Field names.** Design A and Design B used different field names for overlapping
   concepts (`layer` vs `affected_layers`, `single_point_entities` vs `node_ids`,
   `affected_public_tickers` vs `tickers`, `last_reviewed` vs `last_updated`, no
   `severity_score` vs `severity_score`, string `mitigation_watch` vs array). §1 below is
   the **final, single** field list — every field name in it is binding. Where Design B's
   richer UI-facing fields (`severity_score`, `summary`, `card_tagline`, `graph_crossref`)
   were clearly needed for the UI to work and Design A's dataset didn't have them, they were
   added to the curated 13-entry dataset in this merge (severity scores assigned, taglines
   written, summaries written) rather than deferred.
4. **Category enum.** Design B's 6-value enum (`foundry | lithography | memory | packaging
   | export_controls | grid_power`) could not represent Design A's `materials` (photoresist,
   HALEU) or `other` (EDA duopoly) entries without misclassifying them. Design A's 8-value
   enum is adopted, with `export_control` pluralized to `export_controls` to match the UI
   copy Design B already wrote. Final enum: `fab_concentration | equipment_monopoly |
   memory | packaging | export_controls | power_grid | materials | other`.
5. **IDs.** Design A used stable `CP-01`..`CP-13`; Design B used URL-friendly kebab-case
   slugs (needed for `/chokepoints#cp-<id>` anchors and the `/terminal/card/chokepoint/[id]`
   route param). Kebab-slugs win — they *are* stable (same "never renumber, deprecate don't
   reuse" rule applies to slugs as to `CP-NN` codes) and they double as the URL/route
   identifier with zero translation layer needed. Final 13 ids: `tsmc-advanced-node`,
   `asml-euv-monopoly`, `cowos-advanced-packaging`, `hbm-memory-concentration`,
   `us-export-controls-ai-chips`, `china-critical-minerals-leverage`,
   `grid-interconnection-queue-backlog`, `gas-turbine-manufacturing-backlog`,
   `power-transformer-shortage`, `eda-design-software-duopoly`,
   `japan-photoresist-euv-chemicals`, `haleu-enrichment-capacity`,
   `kla-process-control-dominance`.
6. **Everything else** — the UI plan (§6–§10), the fact/reported/rumored discipline (§9 of
   Design B), the build-script responsibilities and pytest list (§2 of Design A) — carried
   forward with only the field-name corrections threaded through.

The curated dataset itself was re-scrutinized during the merge: **all 13 entries from
Design A survive** — every claim has a class, source_name, source_url, source_class, and
`retrieved_at`; the one `rumored` claim (Japan photoresist-export rumor) is correctly
labeled by its own source and never used as a headline; every `single_point_entities`/
`node_ids` id was re-validated this pass against the live `capital_web.json` (117 nodes) —
**zero unresolved ids** (confirmed by script, not by inspection — see §1.3).

---

## 1. Final schema — `ChokepointEntry` (binding field names)

### 1.1 Curated source fields (live in `chokepoints_source.json`, hand/AI-authored)

```
id                    string    kebab-case slug, stable — never renumber/reuse; deprecate
                                 and leave a gap instead. Also the /chokepoints anchor
                                 (#cp-<id>) and the /terminal/card/chokepoint/[id] param.
name                  string    short human title, e.g. "TSMC leading-edge fab
                                 concentration (Taiwan)"
category              enum      fab_concentration | equipment_monopoly | memory |
                                 packaging | export_controls | power_grid | materials |
                                 other
layers                string[]  subset of ["L0-energy","L1-chips","L2-infra","L3-models",
                                 "L4-application"] — reuses build_risk.py's LAYER_ORDER
                                 verbatim, do not invent new layer codes
severity_score        number    0-100, curated analyst judgment (not computed/backtested)
severity_rationale    string    1-2 sentences: substitution difficulty + blast radius,
                                 never a bare "high/medium/low" label
summary               string    <=140 chars, one-liner for card/board subtitles
card_tagline          string    short punchy ALL-CAPS headline, capture-card only —
                                 never rendered as a factual claim, purely editorial framing
description           string    2-4 sentences, factual, states the mechanism (why it's a
                                 single point), no adjectival hype
node_ids              string[]  capital_web.json NODE IDS ONLY (cross-validated by
                                 build_chokepoints.py — see §2). Empty array is valid when
                                 the real chokepoint has no corresponding public-graph node
                                 (a regulatory regime, or a foreign/private supplier not in
                                 the curated graph).
external_entities     string[]  free-text names of the real single-point entities when NOT
                                 in capital_web.json (e.g. "SK hynix (KRX:000660)"). Keeps
                                 the entry honest about the true bottleneck even when the
                                 curated graph has no node for it.
tickers               string[]  best-effort exposure tickers (may include tickers outside
                                 capital_web.json — informational, NOT cross-validated like
                                 node_ids is)
claims                array     [{ text, class, source_name, source_url, source_class,
                                   retrieved_at, needs_verification }] — see 1.2
mitigation_watch      string[]  2-4 short bullet items naming concrete projects/policies to
                                 watch, not vague "diversification"
last_reviewed         string    "YYYY-MM-DD" — date of curation/review (not a claim date)
```

### 1.2 Claim object (nested in `claims[]`)

```
text                  string    ONE verifiable factual statement, not a paragraph
class                 enum      fact | reported | rumored
                                 - fact: primary/regulatory/filing source, or a company's
                                   own SEC-filed disclosure — directly verifiable
                                 - reported: secondary/trade-press/analyst-estimate source;
                                   credible but not primary
                                 - rumored: explicitly reported-as-unconfirmed by the
                                   source itself ("weighing", "considering", "rumored to")
source_name           string    outlet/publisher name
source_url            string    URL, must start with "http"
source_class          enum      api | html | xhr-json | filing  (CLAUDE.md §3 convention;
                                 almost everything here is "html" — news/trade-press pages;
                                 "filing" reserved for Federal Register, SEC EDGAR, LBNL/
                                 national-lab reports, congress.gov CRS reports)
retrieved_at           string    UTC ISO-8601 (this batch: "2026-07-15T16:00:00Z")
needs_verification     bool      true when the only available source is a lower-confidence
                                 secondary/aggregator source and the underlying primary
                                 document could not be reached in-session
```

### 1.3 Fields added by `build_chokepoints.py` (NOT in the source file — computed at build time)

```
needs_verification     bool      rolled up: true if ANY claim in `claims` has
                                 needs_verification=true. NEVER hand-set in the source file.
graph_crossref         object    { source_class: "computed", is_articulation: bool,
                                   betweenness: number } — live join against
                                 graph_analysis.json's articulation-point/betweenness
                                 output, keyed by the entry's node_ids (max betweenness /
                                 OR-of-is_articulation across the entry's node_ids; entries
                                 with empty node_ids get
                                 { source_class:"computed", is_articulation:false,
                                   betweenness:0 }). Corroborating evidence only — a
                                 graph-theoretic SPOF score is a DIFFERENT lens than this
                                 file's curated severity_score; never conflate the two on
                                 screen (see §7.2).
```

### 1.4 Node cross-reference — validated this pass, zero unresolved

All `node_ids` used across the 13 curated entries were checked against the live
`capital_web.json` (117 nodes) programmatically this merge pass:

```
distinct node_ids used: AMKR, ASML, CDNS, ENTG, GEV, KLAC, LEU, MU, SNPS, TSM
all resolved: True (0 missing)
```

`external_entities` (the real single points with no graph node) span 13 names across the
dataset: SK hynix, Samsung Electronics, US BIS, China MOFCOM, US ISOs/RTOs (PJM/ERCOT/
MISO), Siemens Energy, Mitsubishi Heavy Industries, Hitachi Energy, Rosatom/TENEX, JSR
Corp, Tokyo Ohka Kogyo, Shin-Etsu Chemical, Fujifilm Holdings, Siemens EDA — mostly
foreign-listed/private/state entities out of scope for `capital_web.json`'s
US-listed-ticker-centric build. Flagged as a possible future `capital_web.json` expansion,
not resolved this round.

### 1.5 Validation rules enforced by `build_chokepoints.py`

- `id` unique, matches `^[a-z0-9]+(-[a-z0-9]+)*$` (kebab-case).
- `category` in the fixed 8-value enum — **hard fail**, not a warning, on unknown values.
- `layers` non-empty, every element in the fixed `LAYER_ORDER` enum — hard fail on unknown.
- `severity_score` a number in `[0, 100]` — hard fail otherwise.
- `claims` non-empty; every claim has non-empty `text`, `class` in
  `{fact,reported,rumored}`, `source_url` starting with `http`, `retrieved_at` a parseable
  UTC timestamp — hard fail on any violation.
- `node_ids` cross-referenced against `capital_web.json["nodes"][*]["id"]`: unknown ids are
  a **warning** (printed, does not abort the build), collected into
  `validation.node_crossref_warnings`. Rationale: a curated node might legitimately predate
  the next `capital_web.json` refresh — don't brick the whole bundle over one stale id.
- No dirty sentinel strings anywhere (reuses `build_risk.py`'s `_DIRTY_STRINGS` walker:
  `""`, `"."`, `"-"`, `"--"`, `"n/a"`, `"na"`, `"none"`, `"null"`) — hard fail.
- `last_reviewed` parses as an ISO date and is not in the future relative to `generated_at`
  — hard fail.
- Duplicate `id` — hard fail.

---

## 2. Storage & build pipeline (final, corrected per §0.1)

**Curated source (committed, root-level — same tier as `capital_web.json`):**
```
/home/user/AIInvestment/chokepoints_source.json      ← WRITTEN THIS PASS (13 entries)
```
Shape: `{"schema_version": "chokepoints-source-v1", "chokepoints": [ ...13 entries... ]}`
using exactly the field list in §1.1/§1.2. See §4 below for the full file (also on disk).

**Build script (new, next round — mirrors `build_capital_web.py`/`build_risk.py`):**
```
scripts/build_chokepoints.py           ← argparse/IO shell
scripts/aiinvest/chokepoints.py        ← pure-function core (validate, crossref, rollup)
```

Responsibilities:
1. Load `chokepoints_source.json` (default `<repo_root>/chokepoints_source.json`,
   `--source` override).
2. Load `capital_web.json` (default `<repo_root>/capital_web.json`, `--capital-web`
   override) → build the set of valid node ids.
3. Load `web/public/data/graph_analysis.json` if present (`--graph-analysis` override,
   optional — absence is not fatal, `graph_crossref` degrades to all-false/zero) → build a
   `{node_id: {is_articulation, betweenness}}` lookup for §1.3's join.
4. Validate every entry per §1.5. Hard-fail (exit 1, print all issues) on schema
   violations. Warn-only (exit 0, collect into `validation.node_crossref_warnings`) on
   unknown `node_ids` — printed as
   `WARN  cowos-advanced-packaging: node_ids id 'FOO' not found in capital_web.json (117 nodes checked)`.
5. Roll up `needs_verification` per entry from its claims (§1.3).
6. Compute `graph_crossref` per entry (§1.3).
7. Compute a `summary` block (top-level, `source_class="computed"` — mirrors
   `risk.json`'s "computed" pattern even though leaf claims carry their own real
   `source_class`): counts by `category`, by union of `layers`, `n_entries`, `n_claims`,
   `n_fact`/`n_reported`/`n_rumored`, `n_needs_verification`, `n_node_ids_total`,
   `n_node_ids_resolved` vs `n_node_ids_unresolved`.
8. Stamp `generated_at` (UTC now) at the top level.
9. Write `web/public/data/chokepoints.json` — **gitignored**, generated on the owner's
   machine (or CI pipeline run), exactly like `risk.json`/`archetypes.json`/
   `graph_analysis.json`. NOT committed. NOT a build-time Vercel dependency — the reader
   (§6) degrades gracefully if the file is absent, same as every sibling reader.

**`refresh_daily.py` hook** (guarded optional step, same pattern as
`build_risk.py`/`build_archetypes.py`/`build_portfolio.py`; inserted after
`run_graph_analysis.py` since `graph_crossref` depends on a freshly-computed
`graph_analysis.json`, and does not need to wait for `export_site.py` since
`chokepoints.json` is consumed standalone):
```python
add("build capital web", [PY, "build_capital_web.py"])
add("graph analysis (metrics/health/macro/fed/vuln)", [PY, "run_graph_analysis.py"])
if os.path.exists(str(SCRIPTS / "build_chokepoints.py")):
    add("build chokepoint layer -> chokepoints.json", [PY, "build_chokepoints.py"])
if args.with_backtest:
    add("backtest (heavy)", [PY, "run_backtest.py"])
add("export site.json", [PY, "export_site.py"])
```

**pytest list** (`scripts/tests/test_build_chokepoints.py`, network-free, pure-function
tests against `aiinvest.chokepoints`, fixture-file style like `test_build_risk.py`):
1. `test_valid_entry_passes_schema_validation`
2. `test_missing_required_field_fails` (id/name/category/layers/description/claims each)
3. `test_unknown_category_enum_rejected`
4. `test_unknown_layer_code_rejected`
5. `test_severity_score_out_of_range_rejected` (< 0 or > 100)
6. `test_claim_class_enum_enforced` (only fact/reported/rumored accepted)
7. `test_claim_missing_source_url_rejected`
8. `test_claim_missing_retrieved_at_rejected`
9. `test_claim_retrieved_at_must_parse_as_utc_iso8601`
10. `test_duplicate_id_rejected`
11. `test_dirty_sentinel_string_rejected` (reuse `_DIRTY_STRINGS`-style walker)
12. `test_node_crossref_known_id_produces_no_warning`
13. `test_node_crossref_unknown_id_produces_warning_not_failure` ("warn not abort" contract)
14. `test_needs_verification_rolls_up_from_any_claim`
15. `test_graph_crossref_joins_betweenness_and_articulation_when_present`
16. `test_graph_crossref_degrades_gracefully_when_graph_analysis_missing`
17. `test_summary_counts_match_entry_counts` (by_category/layer union sum to n_entries)
18. `test_build_writes_expected_json_path_and_schema_version` (integration, tmp_path)
19. `test_last_reviewed_not_in_future`

Run: `cd scripts && python -m pytest tests/test_build_chokepoints.py`.

**Output shape — `web/public/data/chokepoints.json`:**
```json
{
  "schema_version": "chokepoints-v1",
  "generated_at": "2026-07-15T16:00:00Z",
  "source_class": "computed",
  "source": "chokepoints_source.json (curated) cross-referenced against capital_web.json + graph_analysis.json",
  "disclaimer": "Educational research only — not financial advice. Chokepoint severity is qualitative/indicative, not a probability-weighted loss estimate. Claims with needs_verification=true are directionally credible, not confirmed. graph_crossref is a structural (graph-theoretic) signal, distinct from the curated severity_score.",
  "validation": { "node_crossref_warnings": [], "schema_ok": true },
  "summary": {
    "n_entries": 13, "by_category": {"...": 0}, "by_layer": {"...": 0},
    "n_claims": 21, "n_fact": 3, "n_reported": 17, "n_rumored": 1,
    "n_needs_verification": 6,
    "n_node_ids_total": 10, "n_node_ids_resolved": 10, "n_node_ids_unresolved": 0
  },
  "chokepoints": [ "...the 13 entries, verbatim from source + needs_verification + graph_crossref..." ]
}
```

---

## 3. Contract deliverable — one full example entry (FINAL field names)

```jsonc
// web/public/data/chokepoints.json — one entry, fully annotated
{
  "id": "tsmc-advanced-node",                 // kebab-slug, stable, also #cp-<id> and /terminal/card/chokepoint/[id]
  "name": "TSMC leading-edge fab concentration (Taiwan)",
  "category": "fab_concentration",            // enum: fab_concentration|equipment_monopoly|memory|packaging|export_controls|power_grid|materials|other
  "layers": ["L1-chips", "L2-infra", "L3-models"],   // subset of LAYER_ORDER
  "severity_score": 92,                       // 0-100, curated
  "severity_rationale": "No foundry outside TSMC currently matches leading-edge yield/volume; Samsung and Intel trail materially, so a Taiwan-side disruption has no near-term substitution path for frontier AI compute.",
  "summary": "Sub-7nm logic - the silicon under every AI accelerator - runs through one company, on one island.",
  "card_tagline": "ONE EARTHQUAKE AWAY",      // capture-card headline only; never a factual claim
  "description": "TSMC manufactures the overwhelming majority of the world's leading-edge (sub-7nm) logic chips, and Taiwan hosts essentially all of that capacity today. Every frontier AI accelerator is fabricated on a TSMC process node, with no qualified alternative at comparable yield/volume.",
  "node_ids": ["TSM"],                        // capital_web.json ids only, cross-validated
  "external_entities": [],                    // real single points w/ no graph node (empty here)
  "tickers": ["NVDA", "AMD", "AVGO", "MRVL", "QCOM", "ASML", "AMKR"],  // informational, not cross-validated
  "claims": [
    {
      "text": "Chips at 7nm-and-below made up 74% of TSMC's own wafer revenue in 2025, and TSMC's share of leading-edge (sub-7nm) global foundry output exceeds 90%.",
      "class": "reported",                    // fact|reported|rumored
      "source_name": "Silicon Canals",
      "source_url": "https://siliconcanals.com/j-v-advanced-chips-of-7-nanometers-and-beyond-made-up-74-of-tsmcs-wafer-revenue-in-2025-the-frontier-the-rest-of-the-world-depends-on-has-quietly-become-the-companys-entire-business/",
      "source_class": "html",                 // api|html|xhr-json|filing
      "retrieved_at": "2026-07-15T16:00:00Z",
      "needs_verification": false
    }
    // ...2 more claims, see chokepoints_source.json
  ],
  "mitigation_watch": [
    "TSMC Arizona (Fab 21) yield ramp to leading-edge parity",
    "TSMC Kumamoto (Japan, JASM) or any announced non-Taiwan 2nm-class fab",
    "Samsung Foundry / Intel 18A yield catch-up",
    "Any formal US-Taiwan semiconductor security arrangement"
  ],
  "last_reviewed": "2026-07-15",
  // --- fields below are ADDED by build_chokepoints.py, not present in the source file ---
  "needs_verification": true,                 // rolled up: true because 1 of 3 claims is needs_verification=true
  "graph_crossref": {
    "source_class": "computed",
    "is_articulation": true,                  // joined from graph_analysis.json at build time
    "betweenness": 0.041
  }
}
```

**Where the curated source file lives:** `/home/user/AIInvestment/chokepoints_source.json`
(repo root, committed, all 13 entries — written this pass, see §4).

---

## 4. The curated dataset — `chokepoints_source.json` (13 entries, final)

This is the exact, complete content written to
`/home/user/AIInvestment/chokepoints_source.json` this pass. All `node_ids` re-verified
against the live 117-node `capital_web.json` (zero unresolved). All claims individually
labeled fact/reported/rumored with source_name/source_url/source_class/retrieved_at
(house rule #5) — 3 `fact`, 17 `reported`, 1 `rumored` across 21 total claims; 6 claims
flagged `needs_verification: true` where only secondary/aggregator sources were reachable
in-session. `severity_score` is a curated analyst judgment (0-100), not a computed metric —
it is a distinct lens from `graph_crossref`'s graph-theoretic betweenness/articulation
signal (§1.3), and the two must never be visually conflated in the UI (§7.2).

```json
{
  "schema_version": "chokepoints-source-v1",
  "chokepoints": [
    {
      "id": "tsmc-advanced-node",
      "name": "TSMC leading-edge fab concentration (Taiwan)",
      "category": "fab_concentration",
      "layers": ["L1-chips", "L2-infra", "L3-models"],
      "severity_score": 92,
      "severity_rationale": "No foundry outside TSMC currently matches leading-edge yield/volume; Samsung and Intel trail materially in commercial sub-7nm output, so a Taiwan-side disruption (natural, military, or blockade) has no near-term substitution path for frontier AI compute.",
      "summary": "Sub-7nm logic - the silicon under every AI accelerator - runs through one company, on one island.",
      "card_tagline": "ONE EARTHQUAKE AWAY",
      "description": "TSMC manufactures the overwhelming majority of the world's leading-edge (sub-7nm) logic chips, and Taiwan hosts essentially all of that capacity today. Every frontier AI accelerator (Nvidia, AMD, Google TPU, custom hyperscaler silicon) is fabricated on a TSMC process node, with no qualified alternative at comparable yield/volume. The concentration is simultaneously a manufacturing bottleneck (fab capacity/yield) and a geopolitical one (Taiwan Strait tension).",
      "node_ids": ["TSM"],
      "external_entities": [],
      "tickers": ["NVDA", "AMD", "AVGO", "MRVL", "QCOM", "ASML", "AMKR"],
      "claims": [
        {
          "text": "Chips at 7nm-and-below made up 74% of TSMC's own wafer revenue in 2025, and TSMC's share of leading-edge (sub-7nm) global foundry output exceeds 90%.",
          "class": "reported",
          "source_name": "Silicon Canals",
          "source_url": "https://siliconcanals.com/j-v-advanced-chips-of-7-nanometers-and-beyond-made-up-74-of-tsmcs-wafer-revenue-in-2025-the-frontier-the-rest-of-the-world-depends-on-has-quietly-become-the-companys-entire-business/",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        },
        {
          "text": "Advanced nodes (3nm-and-below) are projected to capture roughly 60% of global foundry shipment share in 2026, with TSMC the dominant supplier at that tier.",
          "class": "reported",
          "source_name": "Counterpoint Research",
          "source_url": "https://counterpointresearch.com/en/insights/advanced-nodes-shipment-to-capture-60-percent-in-2026",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        },
        {
          "text": "Analysts characterize the most likely near-term (pre-2027) China coercive action against Taiwan as a maritime/aerial quarantine rather than invasion; some models estimate a full Taiwan Strait conflict could reduce global GDP roughly 9.6% after one year and cost the global economy on the order of $2.5T/year via semiconductor disruption.",
          "class": "reported",
          "source_name": "Abhishek Gautam (analysis blog, citing broader macro-shock estimates)",
          "source_url": "https://www.abhs.in/blog/china-taiwan-chip-war-2026-global-semiconductor-cloud-impact",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": true
        }
      ],
      "mitigation_watch": [
        "TSMC Arizona (Fab 21) yield ramp to leading-edge parity",
        "TSMC Kumamoto (Japan, JASM) or any announced non-Taiwan 2nm-class fab",
        "Samsung Foundry / Intel 18A yield catch-up",
        "Any formal US-Taiwan semiconductor security arrangement"
      ],
      "last_reviewed": "2026-07-15"
    },
    {
      "id": "asml-euv-monopoly",
      "name": "ASML EUV lithography monopoly",
      "category": "equipment_monopoly",
      "layers": ["L1-chips"],
      "severity_score": 90,
      "severity_rationale": "Critical structural monopoly - every leading-edge fab on earth (TSMC, Samsung, Intel, and China's SMIC for sub-EUV nodes) is dependent on ASML tool deliveries; there is no qualified second source for EUV systems.",
      "summary": "No EUV machine, no leading-edge chip - and there is exactly one company on earth that makes EUV machines.",
      "card_tagline": "ONE SUPPLIER, ZERO ALTERNATIVES",
      "description": "ASML is the sole commercial supplier of extreme ultraviolet (EUV) lithography systems, the tool required to pattern any logic chip at 7nm and below. Nikon and Canon, ASML's only nominal lithography competitors, exited advanced (EUV-class) lithography R&D years ago and sell only mature-node DUV systems. Next-generation High-NA EUV (for 2nm-class production) extends the same monopoly into the following node generation.",
      "node_ids": ["ASML"],
      "external_entities": [],
      "tickers": ["TSM", "NVDA", "AMD", "AMAT", "LRCX", "KLAC"],
      "claims": [
        {
          "text": "ASML holds effectively 100% of the EUV lithography market and roughly 94% of the overall lithography-systems market; it is described as the world's sole supplier of EUV systems, the technology required for chips at 7nm and below.",
          "class": "reported",
          "source_name": "Asia Times",
          "source_url": "https://asiatimes.com/2026/04/asml-as-the-last-polite-monopolist/",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        },
        {
          "text": "High-NA EUV systems ($400M+ per unit), enabling 2nm-and-below production, began commercial rollout in 2025-2026, extending ASML's monopoly position into the next lithography generation.",
          "class": "reported",
          "source_name": "MindRemix (industry-analysis blog)",
          "source_url": "https://www.mindremix.com/2026/01/asml-monopoly-euv-lithography-semiconductor-future-2026.html",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": true
        }
      ],
      "mitigation_watch": [
        "China's SMEE domestic (non-EUV, DUV-multipatterning) lithography program",
        "Any credible second EUV entrant (none known as of this review)",
        "Dutch/EU export-license posture toward China on High-NA tools"
      ],
      "last_reviewed": "2026-07-15"
    },
    {
      "id": "cowos-advanced-packaging",
      "name": "CoWoS / advanced packaging capacity (TSMC)",
      "category": "packaging",
      "layers": ["L1-chips", "L2-infra"],
      "severity_score": 78,
      "severity_rationale": "CoWoS, not wafer starts, is the near-term gating factor on AI accelerator shipments; capacity is concentrated almost entirely at TSMC, with Amkor and other OSAT players as minority alternatives not fully qualified at the same performance tier.",
      "summary": "The wafer isn't the bottleneck anymore - the package it ships in is.",
      "card_tagline": "THE PACKAGE IS THE BOTTLENECK",
      "description": "TSMC's CoWoS (Chip-on-Wafer-on-Substrate) advanced packaging is the step that binds compute dies to HBM stacks for every modern AI accelerator, and it has become the binding capacity constraint ahead of raw wafer supply. Nvidia alone has booked roughly half or more of TSMC's 2026-2027 CoWoS capacity, crowding out smaller/rival buyers. TSMC has been rapidly expanding capacity but by its own CEO's account remains sold out through 2026.",
      "node_ids": ["TSM", "AMKR"],
      "external_entities": [],
      "tickers": ["NVDA", "AMD", "AVGO", "MU"],
      "claims": [
        {
          "text": "TSMC's CoWoS capacity scaled from roughly 35,000 wafers/month (end-2024) to roughly 75,000 (end-2025), targeting roughly 125,000-130,000/month by end-2026 - a near-4x expansion in two years that industry reporting still characterizes as insufficient to meet demand; Nvidia has booked on the order of half to 60% of 2026-2027 capacity.",
          "class": "reported",
          "source_name": "CNBC",
          "source_url": "https://www.cnbc.com/2026/04/08/tsmc-nvidia-advanced-packaging-intel.html",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        },
        {
          "text": "TSMC CEO C.C. Wei told shareholders at the company's June 4, 2026 annual meeting that CoWoS capacity remains 'extremely tight and sold out through 2026.'",
          "class": "reported",
          "source_name": "NextWaves Insight (trade press, quoting the shareholder meeting)",
          "source_url": "https://nextwavesinsight.com/tsmc-advanced-packaging-nvidia-ai-supply-chain-2026/",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        }
      ],
      "mitigation_watch": [
        "TSMC CoWoS capacity additions in Chiayi (AP7) and other Taiwan/overseas sites",
        "Amkor/ASE and other OSAT advanced-packaging qualification for AI-tier interposers",
        "Panel-level packaging R&D as a longer-run alternative to wafer-level CoWoS"
      ],
      "last_reviewed": "2026-07-15"
    },
    {
      "id": "hbm-memory-concentration",
      "name": "HBM (high-bandwidth memory) concentration",
      "category": "memory",
      "layers": ["L1-chips", "L2-infra"],
      "severity_score": 68,
      "severity_rationale": "A three-firm oligopoly (effectively a duopoly by revenue) with long multi-year qualification cycles per accelerator generation; a supply disruption at the leading supplier cannot be absorbed quickly by the other two given each vendor's own multi-quarter qualification lead time with GPU vendors.",
      "summary": "Every AI accelerator needs HBM stacked next to the die - and only three companies on earth make it.",
      "card_tagline": "THREE COMPANIES, ONE STACK",
      "description": "High-bandwidth memory, the DRAM stacked directly onto AI accelerators, is produced by only three qualified suppliers worldwide - SK hynix, Samsung, and Micron - and every frontier AI chip (Nvidia, AMD, custom silicon) depends on one of the three for HBM supply. SK hynix has held the leading position through the HBM3E generation, with Micron gaining share faster than Samsung as the market transitions to HBM4.",
      "node_ids": ["MU"],
      "external_entities": ["SK hynix (KRX:000660)", "Samsung Electronics (KRX:005930)"],
      "tickers": ["NVDA", "AMD", "MU"],
      "claims": [
        {
          "text": "SK hynix's HBM revenue share is estimated in the roughly 50-62% range across Q1-Q2 2026 depending on the tracker, with Micron overtaking Samsung for the #2 position as the market pivots to HBM4; estimates diverge notably by source (e.g. one tracker puts Samsung at 35-40% vs. another at 17%), reflecting genuine measurement uncertainty in a fast-shifting oligopoly rather than a single settled figure.",
          "class": "reported",
          "source_name": "Astute Group (aggregating multiple trackers)",
          "source_url": "https://www.astutegroup.com/news/general/sk-hynix-holds-62-of-hbm-micron-overtakes-samsung-2026-battle-pivots-to-hbm4/",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": true
        }
      ],
      "mitigation_watch": [
        "Samsung HBM4 qualification with Nvidia/AMD (the main swing factor in the duopoly-vs-triopoly balance)",
        "Micron's HBM capacity buildout pace",
        "Any new entrant (none currently qualified at volume)"
      ],
      "last_reviewed": "2026-07-15"
    },
    {
      "id": "us-export-controls-ai-chips",
      "name": "US export controls on advanced AI chips to China",
      "category": "export_controls",
      "layers": ["L1-chips", "L3-models"],
      "severity_score": 74,
      "severity_rationale": "Not a supply constraint but a demand-gating one; the policy directly determines a large addressable market's accessibility for the two leading GPU vendors, and reverses direction on a timescale of months, not years - re-verify every refresh, not on a fixed cadence.",
      "summary": "The rules on who can buy the world's best AI chips changed twice in 2026 alone - and can change again with one memo.",
      "card_tagline": "ONE MEMO AWAY",
      "description": "US Commerce Department (BIS) licensing policy governs which AI accelerators may be exported to China, directly gating Nvidia/AMD's addressable China revenue and shaping gray-market smuggling incentives. Policy has swung between near-total denial and case-by-case review across administrations, making it a genuinely volatile regulatory chokepoint rather than a fixed one.",
      "node_ids": [],
      "external_entities": ["US Bureau of Industry and Security (BIS)"],
      "tickers": ["NVDA", "AMD", "AVGO", "MRVL", "TSM"],
      "claims": [
        {
          "text": "Effective January 15, 2026, BIS revised its license-review policy for advanced computing chips (including Nvidia H200-class and AMD MI325X-class parts) destined for China/Macau from a presumption of denial to case-by-case review, conditioned on certifications including US market supply sufficiency, no diversion of global foundry capacity from higher-priority US customers, and independent US-based third-party performance verification; chips must fall below TPP 21,000 and total DRAM bandwidth 6,500 GB/s thresholds to qualify.",
          "class": "fact",
          "source_name": "Federal Register",
          "source_url": "https://www.federalregister.gov/documents/2026/01/15/2026-00789/revision-to-license-review-policy-for-advanced-computing-commodities",
          "source_class": "filing",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        },
        {
          "text": "The same policy shift was reportedly accompanied by a 25% duty on advanced computing chips manufactured outside the US that pass through the US en route to non-US customers.",
          "class": "reported",
          "source_name": "Morgan Lewis (law-firm client alert summarizing the proclamation)",
          "source_url": "https://www.morganlewis.com/pubs/2026/01/bis-revises-export-review-policy-for-advanced-ai-chips-destined-for-china-and-macau",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        },
        {
          "text": "A subsequent BIS rule announced in late May 2026 tightened controls again on Nvidia's most advanced (Blackwell-class) processors, requiring export licenses for transfers to China/Macau-headquartered entities and closing an offshore-subsidiary loophole.",
          "class": "reported",
          "source_name": "Congressional Research Service (Congress.gov)",
          "source_url": "https://www.congress.gov/crs-product/R48642",
          "source_class": "filing",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        }
      ],
      "mitigation_watch": [
        "Any further BIS rule revision - the single fastest-moving item in the whole dataset",
        "China's domestic accelerator progress (Huawei Ascend) reducing export-control leverage",
        "Enforcement actions on gray-market/transshipment smuggling routes"
      ],
      "last_reviewed": "2026-07-15"
    },
    {
      "id": "china-critical-minerals-leverage",
      "name": "China's critical-minerals export leverage (gallium, germanium, antimony, heavy rare earths)",
      "category": "export_controls",
      "layers": ["L0-energy", "L1-chips"],
      "severity_score": 71,
      "severity_rationale": "China's refining share for several of these materials exceeds 80-90%, but the controls themselves have been suspended/reinstated multiple times within a single year, so severity is more about policy-reversal risk than a static supply gap today.",
      "summary": "China refines the materials inside the chips, the magnets, and the grid gear - and has already used that leverage twice this year.",
      "card_tagline": "THE REFINERY IS THE LEVERAGE",
      "description": "China dominates global refining/processing of gallium, germanium, antimony and several heavy rare-earth elements used in semiconductor manufacturing, permanent magnets (wind turbines, generators, motors), and defense/energy equipment, and has repeatedly used export licensing/bans as leverage in trade disputes. Controls have oscillated sharply - an outright US export ban (Dec 2024), an extraterritorial extension to any product with 0.1%-or-more Chinese-origin rare-earth content (Oct 2025), then a suspension of both measures through Nov 27, 2026 (Nov 2025).",
      "node_ids": [],
      "external_entities": ["China Ministry of Commerce (MOFCOM)"],
      "tickers": ["GEV", "VRT", "ETN", "TSM"],
      "claims": [
        {
          "text": "China banned exports of gallium, germanium, antimony and superhard materials to the US in December 2024; extended controls to any foreign-made product containing 0.1%-or-more Chinese-origin rare-earth content or made with Chinese processing technology in October 2025; then suspended both the October 2025 extraterritorial rule and the December 2024 US-specific ban (via MOFCOM Announcements No. 70 and No. 72, 2025) through November 27, 2026.",
          "class": "reported",
          "source_name": "Pillsbury Law",
          "source_url": "https://www.pillsburylaw.com/en/news-and-insights/china-suspends-export-controls-certain-critical-minerals-related-items.html",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        },
        {
          "text": "Chinese antimony exports fell roughly 97% following the August 2024 restrictions, with global antimony prices roughly tripling.",
          "class": "reported",
          "source_name": "Fastmarkets",
          "source_url": "https://www.fastmarkets.com/insights/china-suspends-export-prohibition-on-superhard-materials-us/",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        }
      ],
      "mitigation_watch": [
        "Non-China gallium/germanium refining capacity build-out (US, EU, Canada critical-minerals initiatives)",
        "Rare-earth magnet recycling and non-rare-earth motor designs for turbines/generators",
        "The Nov 27 2026 suspension expiry date - a hard near-term date to re-check"
      ],
      "last_reviewed": "2026-07-15"
    },
    {
      "id": "grid-interconnection-queue-backlog",
      "name": "Grid interconnection queue backlog",
      "category": "power_grid",
      "layers": ["L0-energy", "L2-infra"],
      "severity_score": 63,
      "severity_rationale": "A process/regulatory bottleneck, not a single-company one, so there is no single entity to fix; it constrains essentially every new large load or generation project in the US simultaneously, regardless of vendor.",
      "summary": "Compute scales in months. The queue to connect it to the grid scales in years.",
      "card_tagline": "THE QUEUE CAN'T KEEP UP",
      "description": "New generation (and the large loads data centers represent) must clear a multi-year utility/ISO interconnection study queue before receiving grid power, and that queue has become the dominant near-term bottleneck on new AI data-center power availability in most US regions. Wait times have more than doubled over 15 years and now regularly exceed the construction timeline of the data center itself, pushing hyperscalers toward behind-the-meter gas and on-site generation as a workaround.",
      "node_ids": [],
      "external_entities": ["US regional ISOs/RTOs (PJM, ERCOT, MISO, etc.) and their interconnection-study processes"],
      "tickers": ["VST", "CEG", "NRG", "PEG", "SO", "D", "NEE", "DUK", "AEP", "XEL", "EXC", "GEV", "VRT", "ETN", "PWR"],
      "claims": [
        {
          "text": "LBNL's 'Queued Up: 2025 Edition' reports that the average time from initial interconnection request to commercial operation reached approximately 5 years by 2024, up from under 2 years in 2008; as of end-2025, over 2,060 GW of generation and storage capacity across roughly 8,200 projects were actively seeking grid interconnection in the US.",
          "class": "fact",
          "source_name": "Lawrence Berkeley National Laboratory (LBNL), Energy Markets & Policy Dept.",
          "source_url": "https://eta-publications.lbl.gov/sites/default/files/2025-12/queued_up_2025_edition_12.15.2025.pdf",
          "source_class": "filing",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        }
      ],
      "mitigation_watch": [
        "FERC Order 2023 interconnection-reform implementation pace by ISO",
        "Behind-the-meter/co-located generation deals bypassing the queue entirely",
        "Any 'fast lane' queue reform specifically for data-center loads"
      ],
      "last_reviewed": "2026-07-15"
    },
    {
      "id": "gas-turbine-manufacturing-backlog",
      "name": "Gas turbine manufacturing backlog",
      "category": "power_grid",
      "layers": ["L0-energy"],
      "severity_score": 72,
      "severity_rationale": "A 3-firm oligopoly with backlogs already extending to 2029-2030 at the largest player; even a buyer willing to pay a premium cannot compress the manufacturing lead time, making this a genuine physical (not just financial) bottleneck.",
      "summary": "Three companies build the turbines that power the AI buildout's bridge fuel - and they're sold out for years.",
      "card_tagline": "SOLD OUT THROUGH 2030",
      "description": "Heavy-duty gas turbines - the near-term workhorse for new dispatchable power to serve AI data-center load growth - are built by only three manufacturers worldwide (GE Vernova, Siemens Energy, Mitsubishi Heavy Industries), and order backlogs at the market leader now stretch years past the order date. This turns turbine manufacturing capacity itself, not fuel or siting, into a hard multi-year lead-time constraint on new gas-fired capacity.",
      "node_ids": ["GEV"],
      "external_entities": ["Siemens Energy (ETR:ENR)", "Mitsubishi Heavy Industries (TSE:7011)"],
      "tickers": ["VST", "CEG", "NRG", "PEG", "SO", "D"],
      "claims": [
        {
          "text": "GE Vernova's gas-turbine order backlog reached 100 GW in Q1 2026 (up 17 GW from year-end 2025), with guidance to reach at least 110 GW of combined backlog plus slot-reservation agreements by end-2026; the company's backlog stretches into 2029, with turbine delivery slots expected to be effectively sold out through 2030 by end-2026. The heavy-duty gas turbine market is controlled by just three manufacturers (GE Vernova, Siemens Energy, Mitsubishi Heavy Industries).",
          "class": "fact",
          "source_name": "Utility Dive (citing GE Vernova investor disclosures/earnings press releases)",
          "source_url": "https://www.utilitydive.com/news/ge-vernova-gas-turbine-backlog-hits-100-gw-as-prices-rise/818332/",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        }
      ],
      "mitigation_watch": [
        "New entrant capacity (none credible at scale currently)",
        "GE Vernova/Siemens Energy factory-expansion capex and its multi-year lag before shipping",
        "SMR/advanced-nuclear or behind-the-meter renewables+storage substituting for gas as the near-term bridge fuel"
      ],
      "last_reviewed": "2026-07-15"
    },
    {
      "id": "power-transformer-shortage",
      "name": "Power transformer shortage",
      "category": "power_grid",
      "layers": ["L0-energy"],
      "severity_score": 66,
      "severity_rationale": "Fragmented, capital-intensive manufacturing base (specialized steel, bushings, tap-changers with their own long lead times) that cannot be quickly expanded; domestic production covers only roughly 20% of US demand, so the bottleneck is import-dependent as well as manufacturing-constrained.",
      "summary": "Even a project that clears the interconnection queue and secures a turbine still needs a transformer to energize.",
      "card_tagline": "FOUR-YEAR LEAD TIMES",
      "description": "Large power transformers and generator step-up transformers - required to connect any new generation or large load (including data centers) to the transmission grid - face lead times that have roughly quadrupled versus pre-pandemic norms, and the US sources only about a fifth of its transformer needs domestically. This sits directly behind both the interconnection-queue and gas-turbine bottlenecks.",
      "node_ids": ["GEV"],
      "external_entities": ["Hitachi Energy (Hitachi Ltd., TSE:6501)", "Siemens Energy (ETR:ENR)"],
      "tickers": ["GEV", "ETN", "HUBB", "PWR"],
      "claims": [
        {
          "text": "As of Q2 2025, lead times for large power transformers averaged roughly 128 weeks (generator step-up transformers roughly 144 weeks), with some units requiring over four years; distribution-transformer lead times have stretched from roughly 12 weeks pre-pandemic to 30-50 weeks in 2026. The US sources only about 20% of its power-transformer needs domestically.",
          "class": "reported",
          "source_name": "pv magazine USA",
          "source_url": "https://pv-magazine-usa.com/2026/05/11/u-s-transformer-market-faces-severe-supply-constraints-as-lead-times-extend-to-four-years/",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        }
      ],
      "mitigation_watch": [
        "~$2B of announced North American transformer manufacturing expansion (Hitachi Energy, Siemens Energy and others), projected online by 2028",
        "Any DOE/utility bulk-procurement or standardization program to shorten custom-spec lead times"
      ],
      "last_reviewed": "2026-07-15"
    },
    {
      "id": "eda-design-software-duopoly",
      "name": "EDA design-software duopoly (Synopsys / Cadence)",
      "category": "other",
      "layers": ["L1-chips"],
      "severity_score": 55,
      "severity_rationale": "Not a physical-supply chokepoint like fabs or lithography, but a structural software dependency with essentially no viable second source for cutting-edge design flows; a disruption at either firm would stall chip design broadly, not just at one customer.",
      "summary": "Every advanced chip is designed inside software made by two companies.",
      "card_tagline": "TWO COMPANIES DESIGN EVERY CHIP",
      "description": "Synopsys and Cadence together control roughly 80-85% of the global electronic design automation (EDA) market - the software required to design any advanced logic chip - with Siemens EDA a distant third. Deep integration with foundry process-design kits and decades of accumulated verified IP make customer switching costs prohibitive, producing near-100% retention and a largely subscription-locked recurring-revenue base.",
      "node_ids": ["SNPS", "CDNS"],
      "external_entities": ["Siemens EDA (Siemens AG, ETR:SIE, distant #3)"],
      "tickers": ["NVDA", "AMD", "AVGO", "MRVL", "TSM", "ASML"],
      "claims": [
        {
          "text": "Synopsys and Cadence together hold on the order of 80-85% of the global EDA market, with near-100% customer retention and 80-85% recurring/subscription revenue, driven by deep foundry PDK integration and switching costs that make customer churn effectively nonexistent.",
          "class": "reported",
          "source_name": "HeyGoTrade (industry-analysis blog)",
          "source_url": "https://www.heygotrade.com/en/blog/synopsys-vs-cadence-snps-vs-cdns-eda-duopoly-ai-chip-boom/",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": true
        }
      ],
      "mitigation_watch": [
        "Open-source/AI-assisted EDA tooling maturing enough to lower switching costs (early-stage, unproven at leading-edge nodes)",
        "Chinese domestic EDA vendors (Empyrean, Primarius) closing the gap under export-control pressure",
        "Any US export restriction on EDA tool sales to China as a companion lever to the export-controls chokepoint"
      ],
      "last_reviewed": "2026-07-15"
    },
    {
      "id": "japan-photoresist-euv-chemicals",
      "name": "Japan's photoresist / EUV-chemicals concentration",
      "category": "materials",
      "layers": ["L1-chips"],
      "severity_score": 60,
      "severity_rationale": "High within its narrow scope - only three volume-qualified EUV-resist suppliers exist globally, all Japanese, so a Japan-side export restriction (rumored but unconfirmed as of this review) would bite even a fab that has EUV tools and wafers ready.",
      "summary": "Three Japanese chemical makers supply nearly all of the world's EUV photoresist.",
      "card_tagline": "THREE SUPPLIERS, ONE COUNTRY",
      "description": "A handful of Japanese chemical makers (JSR, Tokyo Ohka Kogyo, Shin-Etsu Chemical, Fujifilm) supply the large majority of the world's photoresist, and specifically the EUV-grade resist needed for leading-edge lithography is qualified at volume from only three suppliers (TOK, JSR, Shin-Etsu). This makes Japanese trade policy - not just ASML tool availability - a second, independent single point in the EUV process flow.",
      "node_ids": ["ENTG"],
      "external_entities": ["JSR Corp (Japan Investment Corp-owned, delisted 2024)", "Tokyo Ohka Kogyo (TSE:4186)", "Shin-Etsu Chemical (TSE:4063)", "Fujifilm Holdings (TSE:4901)"],
      "tickers": ["TSM", "ASML", "AMAT", "LRCX", "KLAC"],
      "claims": [
        {
          "text": "Japanese suppliers control over 70% of the global photoresist market and roughly 90-95% of the high-end EUV-photoresist segment specifically, with only three qualified volume suppliers (Tokyo Ohka Kogyo, JSR, Shin-Etsu Chemical) for leading-edge EUV resist.",
          "class": "reported",
          "source_name": "Fountyl Tech (industry-analysis blog)",
          "source_url": "https://www.fountyltech.com/news/japanese-companies-monopolize-the-euv-photoresist-supply-market/",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": true
        },
        {
          "text": "In Nov-Dec 2025, Japan was rumored to be weighing curbs on photoresist exports to China (in response to China's own rare-earth export measures), while China separately targeted 40% domestic photoresist self-sufficiency by 2026 - no formal Japanese export restriction has been confirmed as of this review.",
          "class": "rumored",
          "source_name": "TrendForce",
          "source_url": "https://www.trendforce.com/news/2025/12/03/news-japan-rumored-to-curb-photoresist-exports-as-china-targets-40-self-sufficiency-by-2026/",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": true
        }
      ],
      "mitigation_watch": [
        "JSR's new Taiwan photoresist plant (co-located with TSMC) as geographic diversification",
        "TOK's planned South Korea plant (targeted 2030 start)",
        "China's stated 40% photoresist self-sufficiency target and whether it's met"
      ],
      "last_reviewed": "2026-07-15"
    },
    {
      "id": "haleu-enrichment-capacity",
      "name": "HALEU enrichment capacity / Russian dependency",
      "category": "materials",
      "layers": ["L0-energy"],
      "severity_score": 58,
      "severity_rationale": "High for the advanced-nuclear sub-sector specifically - SMR economics/licensing already run on a 2035+ timeline per the investing brief, and fuel-supply concentration is an additional binding constraint on top of permitting; a Centrus production shortfall has no near-term domestic substitute.",
      "summary": "Advanced reactors need a specific fuel that, until recently, only Russia made at scale.",
      "card_tagline": "ONE US PLANT, ONE FUEL",
      "description": "Most next-generation small modular/advanced reactors (TerraPower Natrium, X-energy Xe-100, Kairos Hermes, Oklo Aurora) require HALEU (High-Assay Low-Enriched Uranium, 5-20% U-235), which until a 2024 US import ban was supplied almost exclusively at commercial scale by Russia's Rosatom/TENEX. Centrus Energy's Piketon, Ohio plant is, as of 2026, the only US facility producing HALEU, making it a direct domestic single point for the entire advanced-nuclear pipeline this stack's Layer-0 energy story depends on.",
      "node_ids": ["LEU"],
      "external_entities": ["Rosatom/TENEX (Russia, sanctioned/phasing out by 2028)"],
      "tickers": ["OKLO", "SMR", "NNE", "CCJ", "BWXT"],
      "claims": [
        {
          "text": "Until the 2024 US ban on Russian enriched-uranium imports (Russian deliveries phasing out through 2028 under the Prohibiting Russian Uranium Imports Act), Russia's Rosatom/TENEX was the only commercial-scale supplier of HALEU; Centrus Energy's American Centrifuge Plant in Piketon, Ohio is, as of 2026, the only US facility producing HALEU, having delivered over 900 kg to the DOE, with its DOE production contract extended and a roughly $2.7B DOE HALEU program announced in January 2026.",
          "class": "reported",
          "source_name": "Tech Times",
          "source_url": "https://www.techtimes.com/articles/319669/20260703/doe-locks-1b-centrus-haleu-deal-end-us-reliance-russian-enrichment.htm",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        }
      ],
      "mitigation_watch": [
        "Centrus Piketon capacity ramp and any second US HALEU producer (Orano, Urenco USA expansion plans)",
        "DOE's $2.7B program disbursement pace",
        "Whether SMR vendors qualify LEU+ (below-HALEU-assay) fuel cycles as a near-term workaround"
      ],
      "last_reviewed": "2026-07-15"
    },
    {
      "id": "kla-process-control-dominance",
      "name": "KLA process-control/inspection dominance",
      "category": "equipment_monopoly",
      "layers": ["L1-chips"],
      "severity_score": 52,
      "severity_rationale": "Process control is a mandatory yield-gating step, not an optional one, and KLA's share has been rising (not stable), so a KLA-specific disruption would slow leading-edge and advanced-packaging output broadly even though nominal competitors exist.",
      "summary": "Every advanced wafer has to pass inspection before the next step - and one company dominates that inspection.",
      "card_tagline": "THE GATEKEEPER OF YIELD",
      "description": "KLA Corporation supplies the wafer-inspection and metrology tools that must sign off on every advanced wafer (and, increasingly, advanced-packaging step) before it proceeds to the next process stage, and has been steadily gaining share against Applied Materials and other process-control vendors. Unlike ASML's binary sole-supplier position, KLA is a dominant-but-not-exclusive supplier - the risk here is concentration, not literal monopoly.",
      "node_ids": ["KLAC"],
      "external_entities": [],
      "tickers": ["TSM", "NVDA", "AMD", "AMAT", "LRCX"],
      "claims": [
        {
          "text": "KLA's semiconductor process-control market share reached approximately 58% in 2025 (up from roughly 50-54% in the 2010-2021 period), with over 85% share in optical wafer inspection specifically and the #1 share position in advanced wafer-level packaging process control; Applied Materials, the next-largest player, has meanwhile declined to under 8% share in the segments where the two compete directly.",
          "class": "reported",
          "source_name": "Investing.com (citing KLA's own Q3 FY2026 investor slides)",
          "source_url": "https://www.investing.com/news/company-news/kla-q3-fy2026-slides-market-share-hits-58-ambitious-2030-targets-93CH-4671214",
          "source_class": "html",
          "retrieved_at": "2026-07-15T16:00:00Z",
          "needs_verification": false
        }
      ],
      "mitigation_watch": [
        "Applied Materials/other process-control vendors regaining share (currently trending the opposite direction)",
        "Any qualification of a second inspection vendor at advanced-packaging nodes specifically, where KLA's share gain has been fastest"
      ],
      "last_reviewed": "2026-07-15"
    }
  ]
}
```

**Dataset provenance summary:** 13 entries, 21 claims total: **3 `fact`** (export-controls'
Federal Register rule + CRS report, grid-interconnection's LBNL report, gas-turbine's GE
Vernova disclosure via Utility Dive), **17 `reported`**, **1 `rumored`** (Japan photoresist
export-curb rumor, correctly labeled as such by its own source). **6 claims flagged
`needs_verification: true`**: TSMC's Taiwan-conflict GDP-impact estimate, ASML's High-NA
rollout characterization, HBM's market-share split (trackers disagree by double digits),
EDA duopoly's share figures, and both of Japan photoresist's claims (share figure + the
rumor itself) — all from lower-confidence secondary/aggregator sources where the primary
document could not be reached in-session. All retrieval performed live via web search this
session (2026-07-15, batch-stamped `2026-07-15T16:00:00Z`) — this is session-verified
content, not knowledge-cutoff recall, per the task's sandbox guidance (market-data APIs
blocked, general web search available). **Most volatile entries — re-check every refresh,
not just on `last_reviewed` cadence**: `us-export-controls-ai-chips` (policy has reversed
direction twice in 2026 already) and `china-critical-minerals-leverage` (already suspended
once mid-cycle, hard Nov 27 2026 re-check date baked into the claim itself).

---

## 5. `web/lib/chokepoints.ts` (final field names threaded through)

Same architecture as Design B's spec (own dedicated reader file mirroring `lib/risk.ts`/
`lib/macro.ts`/`lib/archetypes.ts`; client-safe types/helpers with the one `fs`-reading
exception at the bottom) — **with the reader corrected to the guarded/never-throws pattern**
per §0.1, and field names updated to the final list in §1.

```ts
// web/lib/chokepoints.ts
//
// Supply-chain chokepoint layer (Round 6). Data source: web/public/data/chokepoints.json —
// GENERATED, GITIGNORED (same tier as risk.json / archetypes.json / graph_analysis.json),
// produced by scripts/build_chokepoints.py on the owner's machine. NOT committed, NOT a
// Vercel build-time dependency — may legitimately be absent (fresh clone, CI, pre-pipeline
// Vercel build). Every caller must degrade gracefully, never 500. Curated INPUT lives at
// chokepoints_source.json (repo root, committed — see docs/superpowers/specs/
// 2026-07-15-chokepoints-design.md).
//
// LEGAL/HONESTY: every claim carries class fact|reported|rumored + source + retrieved_at
// (CLAUDE.md rule #5). Never launder a rumored claim into a fact — see headlineClaim().

import fs from "node:fs";
import path from "node:path";

export type ChokepointCategory =
  | "fab_concentration" | "equipment_monopoly" | "memory" | "packaging"
  | "export_controls" | "power_grid" | "materials" | "other";

export type ClaimClass = "fact" | "reported" | "rumored";
export type SourceClass = "api" | "html" | "xhr-json" | "filing";

export interface ChokepointClaim {
  text: string;
  class: ClaimClass;
  source_name: string;
  source_url: string;
  source_class: SourceClass;
  retrieved_at: string; // UTC ISO-8601
  needs_verification: boolean;
}

export interface GraphCrossref {
  source_class: "computed";
  is_articulation: boolean;
  betweenness: number;
}

export interface Chokepoint {
  id: string;                    // kebab-slug, stable
  name: string;
  category: ChokepointCategory;
  layers: string[];              // LayerKey[]
  severity_score: number;        // 0-100, curated
  severity_rationale: string;
  summary: string;
  card_tagline: string;          // capture-card headline only, never rendered elsewhere as fact
  description: string;
  node_ids: string[];            // capital_web.json ids -> /map ring highlight
  external_entities: string[];
  tickers: string[];
  claims: ChokepointClaim[];
  mitigation_watch: string[];
  last_reviewed: string;
  needs_verification: boolean;   // rolled up by build_chokepoints.py
  graph_crossref?: GraphCrossref; // joined by build_chokepoints.py against graph_analysis.json
}

export interface ChokepointsValidation {
  node_crossref_warnings: string[];
  schema_ok: boolean;
}
export interface ChokepointsSummary {
  n_entries: number;
  by_category: Record<string, number>;
  by_layer: Record<string, number>;
  n_claims: number;
  n_fact: number;
  n_reported: number;
  n_rumored: number;
  n_needs_verification: number;
  n_node_ids_total: number;
  n_node_ids_resolved: number;
  n_node_ids_unresolved: number;
}
export interface ChokepointsData {
  schema_version: string; // "chokepoints-v1"
  generated_at: string;
  source_class: "computed";
  source: string;
  disclaimer: string;
  validation: ChokepointsValidation;
  summary: ChokepointsSummary;
  chokepoints: Chokepoint[];
}

// ---- category display metadata ----
export const CHOKEPOINT_CATEGORY_LABELS: Record<ChokepointCategory, string> = {
  fab_concentration: "Foundry / Advanced Node",
  equipment_monopoly: "Equipment Monopoly",
  memory: "Memory (HBM)",
  packaging: "Advanced Packaging",
  export_controls: "Export Controls",
  power_grid: "Grid & Power",
  materials: "Materials",
  other: "Other Structural",
};

// Spread across the hue wheel so up to 8 simultaneous ring colors stay distinguishable
// (warm/cool alternation, colorblind-conscious). NOT reused 1:1 from LAYER_COLORS/
// ARCHETYPE_COLORS/MACRO_GROUP_COLORS — those are fills on a different visual channel
// (node body vs. this feature's ring/glow); within THIS legend all values are distinct.
export const CHOKEPOINT_CATEGORY_COLORS: Record<ChokepointCategory, string> = {
  fab_concentration: "#fb923c",   // orange-400
  equipment_monopoly: "#d946ef",  // fuchsia-500
  memory: "#22d3ee",              // cyan-400
  packaging: "#facc15",           // yellow-400
  export_controls: "#f43f5e",     // rose-500
  power_grid: "#14b8a6",          // teal-500
  materials: "#a3e635",           // lime-400
  other: "#94a3b8",               // slate-400
};

export function categoryColor(c: ChokepointCategory): string {
  return CHOKEPOINT_CATEGORY_COLORS[c] ?? "#6b7280";
}
export function categoryLabel(c: ChokepointCategory): string {
  return CHOKEPOINT_CATEGORY_LABELS[c] ?? c;
}

// ---- severity bands (curated severity_score, distinct from graph_crossref.betweenness) ----
const SEVERITY_RED = "#ef4444";
const SEVERITY_AMBER = "#f59e0b";
const SEVERITY_GREY = "#6b7280";

export function severityColor(score: number): string {
  if (score >= 75) return SEVERITY_RED;
  if (score >= 40) return SEVERITY_AMBER;
  return SEVERITY_GREY;
}
export function severityBand(score: number): "CRITICAL" | "ELEVATED" | "MODERATE" {
  if (score >= 75) return "CRITICAL";
  if (score >= 40) return "ELEVATED";
  return "MODERATE";
}

// ---- claim-class badge metadata ----
// Strongest -> weakest color ramp mirrors lib/news.ts's certaintyMeta() (filed=sky,
// reported=emerald, rumored=amber) for a consistent "how sure are we" visual grammar
// site-wide, even though the vocabulary here (fact/reported/rumored) is distinct from
// news.ts's (filed/reported/rumored) by design (different provenance systems).
export interface ClaimClassMeta { label: string; chipCls: string; note: string; }
const CLAIM_CLASS_META: Record<ClaimClass, ClaimClassMeta> = {
  fact: {
    label: "FACT",
    chipCls: "text-sky-300 border-sky-500/50 bg-sky-500/10",
    note: "Grounded in a primary source (filing, regulatory rule, official statement).",
  },
  reported: {
    label: "REPORTED",
    chipCls: "text-emerald-300 border-emerald-500/50 bg-emerald-500/10",
    note: "Reported by credible secondary sources — not independently re-verified here.",
  },
  rumored: {
    label: "RUMORED",
    chipCls: "text-amber-300 border-amber-500/50 bg-amber-500/10",
    note: "Speculative / unconfirmed — treat as color, not conclusion.",
  },
};
export function claimClassMeta(c: ClaimClass): ClaimClassMeta {
  return CLAIM_CLASS_META[c];
}

// The single most important guardrail in this file: pick the claim a capture card is
// allowed to headline. NEVER returns a rumored claim (CLAUDE.md rule #5). Prefers
// fact > reported; returns null if the chokepoint has no fact/reported claims, so the
// card renders its documented fallback instead of ever mislabeling a rumor as stronger.
export function headlineClaim(cp: Chokepoint): ChokepointClaim | null {
  const fact = cp.claims.find((c) => c.class === "fact");
  if (fact) return fact;
  const reported = cp.claims.find((c) => c.class === "reported");
  return reported ?? null;
}

const CLASS_RANK: Record<ClaimClass, number> = { fact: 0, reported: 1, rumored: 2 };
export function sortedClaims(cp: Chokepoint): ChokepointClaim[] {
  return [...cp.claims].sort((a, b) => CLASS_RANK[a.class] - CLASS_RANK[b.class]);
}

// Chokepoints touching a given capital_web node id — used by NodeDetailPanel's "Linked
// chokepoints" row and CapitalGraph's ring-highlight lookup.
export function chokepointsForNode(data: ChokepointsData, nodeId: string): Chokepoint[] {
  return data.chokepoints.filter((cp) => cp.node_ids.includes(nodeId));
}

export const CATEGORY_ORDER: ChokepointCategory[] = [
  "fab_concentration", "equipment_monopoly", "packaging", "memory",
  "export_controls", "power_grid", "materials", "other",
];
export function groupByCategory(
  data: ChokepointsData,
): { category: ChokepointCategory; items: Chokepoint[] }[] {
  return CATEGORY_ORDER.map((category) => ({
    category,
    items: data.chokepoints
      .filter((cp) => cp.category === category)
      .sort((a, b) => b.severity_score - a.severity_score),
  })).filter((g) => g.items.length > 0);
}

// ---- fs reader (server-only; the one non-client-safe export in this file) ----
// GUARDED, NEVER THROWS — mirrors getGraphAnalysis()/getTaDeskData() exactly. The file
// may legitimately not exist (fresh clone, CI, Vercel build before the owner has run
// build_chokepoints.py). Callers (page components) must handle `null` with an empty
// state, not assume presence.
let cached: ChokepointsData | null | undefined;

export function getChokepointsData(): ChokepointsData | null {
  if (cached !== undefined) return cached;
  try {
    const file = path.join(process.cwd(), "public", "data", "chokepoints.json");
    if (!fs.existsSync(file)) {
      cached = null;
      return cached;
    }
    const raw = fs.readFileSync(file, "utf-8");
    cached = JSON.parse(raw) as ChokepointsData;
  } catch {
    cached = null;
  }
  return cached;
}

export function getChokepointById(id: string): Chokepoint | undefined {
  return getChokepointsData()?.chokepoints.find((cp) => cp.id === id);
}
```

Re-export the type-only surface from `lib/data.ts`, matching how `news.ts`/`conflict.ts`/
`congress_profile.ts` are re-exported today:
```ts
export type { ChokepointCategory, ClaimClass, ChokepointClaim, Chokepoint, ChokepointsData } from "./chokepoints";
export { categoryColor, categoryLabel, severityColor, severityBand, claimClassMeta, headlineClaim, chokepointsForNode, getChokepointsData, getChokepointById } from "./chokepoints";
```

---

## 6. UI plan (final — Design B's plan, field names corrected, storage tier corrected)

Everything below carries forward from Design B with only two systemic corrections applied
throughout: (a) field names per §1/§5 above (`node_ids` not `single_point_entities`,
`layers` not `affected_layers`, `last_reviewed` not `last_updated`, `mitigation_watch` is
`string[]` not `string`), and (b) **every page/component that reads `chokepoints.json`
must treat `getChokepointsData()` as possibly `null` and render a graceful empty state**
(new instruction — Design B assumed unconditional presence, which contradicted actual repo
convention per §0.1).

### 6.1 `/map` — chokepoint overlay

- New toggle pill `⛓ Chokepoints` next to "Color nodes by" in `MapExplorer.tsx`, styled
  identically to existing active-state language, disabled/grayed in company-view mode
  (`CompanyValueChain` untouched this round).
- `CapitalGraph.tsx` gets `chokepoints`, `chokepointMode`, `activeChokepointId`,
  `onSelectChokepoint` props. Build `chokepointsByNode: Map<string, Chokepoint[]>` from
  `node_ids`. Member nodes get a colored ring (category color via `categoryColor()`,
  `borderWidth: 3`, bumped to match/exceed the SPOF ring's 4 when both apply — max, not
  additive) and a `⛓ ` label prefix (before the existing `⚠ ` SPOF prefix). Tooltip gets
  `"⛓ Chokepoint: <name> (<category>) · severity <severity_score>/100"` per membership.
- Focus state (`activeChokepointId` set): `network.fit({nodes: cp.node_ids, ...})`, member
  nodes get a stronger ring/glow, all other nodes dim via the rgba-alpha technique already
  used by the macro-stress overlay, edges reuse the existing `edgesDsRef` live-recolor
  mechanism (category color at 0.9 opacity for member edges, 0.12 for others). Stress
  overlay wins on edges if both are active simultaneously ("one live edge-overlay at a
  time" — matches the existing `colorMode`-disabled-in-company-mode discipline). Node
  rings and edge stress-color can coexist since they're different channels.
- `GraphLegend` gets a chokepoint-category swatch row (using
  `CHOKEPOINT_CATEGORY_COLORS`), rendered only when `chokepointMode` is true.
- Aside composition (`MapExplorer.tsx`), inserted above `NodeDetailPanel` in the existing
  scrollable column: `ChokepointSideList` (severity-ordered flat list, mobile
  horizontal-scroll) → `ChokepointClaimsPanel` (claims/sources/mitigation_watch for
  `activeChokepointId`, using `sortedClaims()`/`claimClassMeta()`) → `NodeDetailPanel`
  (modified: new optional "Linked chokepoints" chip row via `chokepointsForNode()`,
  clicking jumps into chokepoint-focus). **When `getChokepointsData()` returns `null`**,
  the `⛓ Chokepoints` toggle either hides entirely or renders disabled with a tooltip
  ("chokepoint data not yet built — run `build_chokepoints.py`") — never a runtime error.

### 6.2 `/chokepoints` — public board page (NEW, public, shareable)

- `web/app/chokepoints/page.tsx`, modeled on `/resiliency`: server component,
  `getChokepointsData()` (guarded), same header/banner/footer rhythm, `max-w-5xl`
  container. **If `getChokepointsData()` returns `null`**: render the same page chrome
  (header, methodology banner) with an explicit "Chokepoint data has not been generated
  yet on this deployment — run `scripts/build_chokepoints.py`" empty-state block instead
  of the card grid — never a 500, never a blank page.
- Metadata: indexable, OG-friendly (opposite of gated capture-card routes), title
  `"Supply-Chain Chokepoints · AI STACK"`.
- Layout: header/eyebrow → methodology/disclaimer banner (fact/reported/rumored
  explained) → 4-tile stat row (`n_entries`, critical-severity count [`severity_score`≥75],
  fact-class claim count, distinct layers touched) → category filter pills
  (`ChokepointBoard.tsx` client wrapper) → card grid grouped by `groupByCategory()`,
  severity-descending within each group → footer disclaimer + cross-link to `/map`.
- `ChokepointCard.tsx`: `id="cp-<id>"` anchor (deep-linkable), `border-l-4` category-color
  accent, `#` permalink icon. Body: category chip + severity badge
  (`severityBand(severity_score)`) → name → `summary` → `layers` as `LayerChip[]` →
  `tickers` strip (public tickers linked to `/stocks/[symbol]`) → top-3 `sortedClaims()`
  with class badge + text + linked source + `retrieved_at` (`<details>` for the rest, no
  JS needed) → `mitigation_watch` as a muted "WATCHING" bullet list → footer:
  `graph_crossref.is_articulation` badge ("⚠ also a graph SPOF") linking to `/map`, plus
  `last_reviewed`. Never links to the gated capture-card route (matches the house pattern
  that `/resiliency` doesn't link `/terminal/card/risk` either).

### 6.3 `/terminal/card/chokepoint/[id]` — gated capture card (NEW)

- Route mirrors `/terminal/card/[symbol]`; construction discipline mirrors
  `RiskCaptureCard.tsx` (`#capture-canvas`, `data-capture-ready="true"`, all-px inline
  styles, no client JS, no SVG). `notFound()` if `getChokepointById(id)` is undefined
  (covers both "id not found" and "chokepoints.json absent" — both are a loud 404, never
  a broken screenshot).
- `ChokepointCaptureCard.tsx`, 1080×1350: brand/eyebrow → category badge → headline block
  (`card_tagline` 56px + `name` subtitle) → **headline claim (fact-only rule)**: uses
  `headlineClaim(cp)` from `lib/chokepoints.ts` — renders a FACT-badged quote if a fact
  claim exists, a REPORTED-badged quote with a "no fact-class source yet" caption if only
  reported claims exist, or falls back to `summary` with no class badge at all if
  `headlineClaim()` returns `null` (only rumored claims exist) — the card never fabricates
  confidence it doesn't have. → ticker strip → 3-stat block (`SEVERITY` via
  `severity_score`/`severityBand`, `AFFECTED LAYERS` chips, `MITIGATION WATCH` first 1-2
  items) → footer: `Generated <last_reviewed> · chokepoint-board-v1` +
  **unconditional** `Educational research only — not financial advice. NFA.`

Of this round's 13 curated entries, `headlineClaim()` resolves to a **fact**-class claim
for 3 (`us-export-controls-ai-chips`, `grid-interconnection-queue-backlog`,
`gas-turbine-manufacturing-backlog`) and a **reported**-class claim (with the "no
fact-class source yet" caption) for the other 10 — **never** `null`, since every entry has
at least one non-rumored claim by construction (validated in §1.5/§2's build script).

### 6.4 Nav changes

- `web/components/Header.tsx`: insert `{ href: "/chokepoints", label: "CHOKEPOINTS" }`
  next to `/resiliency` in `NAV` (both are graph/structural-risk pages).
- `web/components/terminal/TerminalSubNav.tsx`: **unchanged**. The capture-card route is
  card-only, exactly like `/terminal/card/[symbol]` — never appears in `SUB_NAV`. No new
  terminal desk page this round.

### 6.5 Component/file inventory (next round)

**NEW:** `web/lib/chokepoints.ts`, `web/components/ChokepointSideList.tsx`,
`web/components/ChokepointClaimsPanel.tsx`, `web/app/chokepoints/page.tsx`,
`web/components/ChokepointBoard.tsx`, `web/components/ChokepointCard.tsx`,
`web/app/terminal/card/chokepoint/[id]/page.tsx`,
`web/components/terminal/ChokepointCaptureCard.tsx`, `scripts/build_chokepoints.py`,
`scripts/aiinvest/chokepoints.py`, `scripts/tests/test_build_chokepoints.py`.

**MODIFIED:** `web/components/CapitalGraph.tsx`, `web/components/MapExplorer.tsx`,
`web/components/NodeDetailPanel.tsx`, `web/components/Header.tsx`, `web/app/map/page.tsx`
(fetch `getChokepointsData()`, guarded), `scripts/refresh_daily.py` (one guarded hook line).

**Explicitly unchanged:** `web/components/terminal/TerminalSubNav.tsx`,
`web/components/CompanyValueChain.tsx`, `web/app/resiliency/page.tsx`, all other
`/terminal/*` desk pages.

**Written this pass:** `/home/user/AIInvestment/chokepoints_source.json` (13 entries).

---

## 7. Fact/Reported/Rumored discipline (final)

1. **Data layer**: `ChokepointClaim.class` is a closed enum; `sortedClaims()` only
   *orders*, never *relabels*.
2. **Card layer**: `headlineClaim()` structurally cannot return a rumored claim — only
   `fact`, `reported`, or `null` (never a silent downgrade).
3. **Badge layer**: `claimClassMeta()` gives every claim, everywhere rendered, the same
   colored badge — no component renders claim text without it.
4. **Source layer**: every claim carries `source_url`/`source_name`/`retrieved_at`,
   always rendered as a live outbound link, never bare text.
5. **Two independent lenses, never conflated**: `severity_score` (curated analyst
   judgment) and `graph_crossref.betweenness`/`is_articulation` (structural,
   graph-theoretic, computed) measure different things. `/resiliency`'s `top_spofs` and
   this file's `graph_crossref` **corroborate**, they don't **compute**, severity — the UI
   must label them distinctly wherever both appear (e.g. `ChokepointCard`'s "also a graph
   SPOF" badge is explicitly a cross-reference note, not a severity input).
6. **Honesty about this design pass**: claims were grounded via live web search
   2026-07-15 — real sources, real URLs, checked, not fabricated. This is
   **design/curation-time verification**, not the repo's REST-first/Playwright retrieval
   pipeline (CLAUDE.md §2/§3) — appropriate here since this is qualitative/regulatory/
   structural data, not scriptable price/fundamental data. A future refresh round should
   re-pull and re-stamp `retrieved_at` for the two fastest-moving entries
   (`us-export-controls-ai-chips`, `china-critical-minerals-leverage`) before their
   `last_reviewed` date goes stale, and treat the 6 `needs_verification: true` claims as
   upgrade candidates once a primary source is reachable (e.g. HBM's market-share claim
   could plausibly upgrade to `fact` if a future round sources SK hynix's own SEC-filed
   IPO disclosure rather than a tracker aggregation).

---

## 8. Out of scope / follow-up

1. Build `scripts/aiinvest/chokepoints.py` + `scripts/build_chokepoints.py` per §2 (TDD,
   pytest list in §2 ready to drive it) — not built this round, design only.
2. Build `web/lib/chokepoints.ts` + all UI components in §6 — not built this round.
3. Wire the `refresh_daily.py` guarded hook (one-line diff, shown in §2).
4. Decide whether to expand `capital_web.json` with foreign-listed/private nodes for the
   `external_entities` gap list (§1.4), or accept it as a permanent scope boundary.
5. Re-verify `us-export-controls-ai-chips` / `china-critical-minerals-leverage` (the two
   fastest-moving entries) before the next data refresh regardless of general
   `last_reviewed` cadence.
6. `CompanyValueChain.tsx` does not get chokepoint rings this round — toggle disabled in
   that mode, matching `colorMode`'s existing behavior there.
7. Dedicated OG image for `/chokepoints` (metadata text is specified in §6.2) — not built.
8. `/terminal/chokepoints` gated desk page (mentioned as a possibility in Design A's §3) —
   explicitly deferred; this round's UI mandate is the `/map` overlay + public board +
   capture card only, per Design B's more detailed and already-vetted plan.

Files referenced this round:
- `/home/user/AIInvestment/chokepoints_source.json` (WRITTEN this pass — 13 entries)
- `/home/user/AIInvestment/docs/superpowers/specs/2026-07-15-chokepoints-design.md` (this file)
- Read this round: `/home/user/AIInvestment/references/investing-brief.md` (Part D),
  `/home/user/AIInvestment/capital_web.json` (117 nodes, node-id cross-referenced by
  script), `/home/user/AIInvestment/scripts/build_risk.py`,
  `/home/user/AIInvestment/scripts/refresh_daily.py`,
  `/home/user/AIInvestment/.gitignore`, `/home/user/AIInvestment/web/lib/risk.ts`,
  `/home/user/AIInvestment/web/app/resiliency/page.tsx`,
  `/home/user/AIInvestment/web/components/CapitalGraph.tsx`.
- Not yet created (next round): `scripts/build_chokepoints.py`,
  `scripts/aiinvest/chokepoints.py`, `scripts/tests/test_build_chokepoints.py`,
  `web/lib/chokepoints.ts`, `web/components/ChokepointSideList.tsx`,
  `web/components/ChokepointClaimsPanel.tsx`, `web/app/chokepoints/page.tsx`,
  `web/components/ChokepointBoard.tsx`, `web/components/ChokepointCard.tsx`,
  `web/app/terminal/card/chokepoint/[id]/page.tsx`,
  `web/components/terminal/ChokepointCaptureCard.tsx`, generated (gitignored)
  `web/public/data/chokepoints.json`.
