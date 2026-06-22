# Feasibility Report & Build Spec — "Political Trading" (Congressional Stock Disclosures)

**Feature:** A free, REST-first "Political Trading" section of the AIInvestment engine that
ingests STOCK Act periodic transaction reports (PTRs) for **both chambers**, labels **every**
trade with a sector (all sectors, not just AI), and surfaces a strictly-correlational
**conflict-of-interest signal** linking a member's committee seat / sponsored bills to their
disclosed trades — for human review, never as an allegation.

**Engine:** REST-first (`requests`/`urllib`), TDD (`pytest`), stamped envelopes
(`retrieved_at` / `source` / `source_class`), fact-vs-reported-vs-rumored labeling.
**Site:** Next.js, data-terminal dark theme → new `/congress` route.
*Educational/research only — not investment advice. Not an accusation of wrongdoing against any individual.*

> Synthesized from a 5-agent live-probe research workflow. The synthesis agent **re-probed the
> load-bearing endpoints on 2026-05-31** before writing this spec (see §1 evidence column).

---

## 1. Verdict per capability

| Capability | Verdict | Why / live evidence (re-probed 2026-05-31) |
|---|---|---|
| **House trades (PTRs)** | **BUILDABLE — free, ungated, current** | `GET …/financial-pdfs/2026FD.zip` → **HTTP 200, 39873 bytes, application/x-zip-compressed**. Index (`<YEAR>FD.xml`) refreshed daily; per-trade PDF `GET …/ptr-pdfs/2025/20032062.pdf` → **HTTP 200, application/pdf**. Mode A (static HTTPS asset). |
| **Senate trades (PTRs)** | **BUILDABLE — free, but GATED session** | `GET efdsearch.senate.gov/search/home/` with no session → **HTTP 403** this run. Requires agree-to-terms handshake (csrfmiddlewaretoken → POST `prohibition_agreement=1` → carry `csrftoken` cookie + `X-CSRFToken` header + `X-Requested-With`). With session: POST `/search/report/data/` returns `application/json` (research run saw 72 PTRs for 2026); detail at `/search/view/ptr/{uuid}/` is HTML. **Mode B (isolated session).** |
| **Bill / committee / sponsorship** | **BUILDABLE — free, REST/JSON** | Congress.gov API v3 `GET /v3/bill/118/hr/1?api_key=DEMO_KEY` → **HTTP 200 application/json** this run (sponsor, policyArea, cosponsors, committees). DEMO_KEY = shared 10/hr; ship a free `api.data.gov` key = 5,000/hr. |
| **Committee ROSTER (member↔committee)** | **BUILDABLE — free, bulk JSON** | `unitedstates/congress-legislators` `committee-membership-current.json` + `legislators-current.yaml` (ID crosswalk bioguide↔govtrack↔opensecrets↔fec). **Required** because congress.gov member/committee endpoints do not link the two. |
| **Sector label (every ticker)** | **BUILDABLE — free, two independent sources** | SEC EDGAR `company_tickers.json` → **HTTP 200, 792364 bytes** this run; `data.sec.gov/submissions/CIK*.json` gives SIC + sicDescription (authoritative). TradingView scanner `america/scan` gives finer sector/industry (already used in repo via `tradingview.py`). **Neither is GICS.** |
| **Pre-parsed House+Senate JSON (house/senate-stock-watcher S3)** | **BLOCKED / DEAD** | `GET house-stock-watcher-data.s3-us-west-2…/all_transactions.json` → **HTTP 403 AccessDenied** this run. GitHub mirror frozen at 2021. **Do not build on it** (LLMs/tutorials still recommend it). |
| **Key-gated convenience APIs (Quiver/Finnhub/FMP)** | **PARTIAL — optional cross-check only** | Quiver `/beta/live/congresstrading` → **401** without bearer; congressional endpoints frequently sit behind paid tiers. Use only as optional validation, never a dependency. |
| **Conflict-of-interest signal (trade ↔ committee/bill timing)** | **BUILDABLE as CORRELATIONAL FLAG ONLY** | All inputs above are reachable & joinable on **bioguide ID** (via the legislators crosswalk). Precision is structurally capped by range buckets + ≤45-day lag. **Never a causal/intent claim.** |

**Bottom line:** the entire feature is buildable **today, fully free, no paid API**, by parsing
the two authoritative government sources ourselves (House Clerk bulk ZIP = Mode A; Senate eFD =
Mode B isolated session) and joining to Congress.gov + the `congress-legislators` crosswalk. The
only genuinely hard engineering is **PDF/OCR extraction of House PTRs** (many are scanned images).

---

## 2. Chosen sources — primary + fallback (REST-first, exact endpoints)

### (a) Trades

| Leg | Primary | Fallback / cross-check |
|---|---|---|
| **House** | **House Clerk bulk ZIP** (Mode A, ungated): `GET https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{YEAR}FD.zip` → unzip → parse `{YEAR}FD.xml` → filter `FilingType=='P'` → `GET https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{YEAR}/{DocID}.pdf` → text/OCR extract. UA with contact email (root portal 403s generic fetchers; **asset paths return 200**). | Quiver/Finnhub/FMP free tier (key-gated) for spot validation only. |
| **Senate** | **Senate eFD** (Mode B, isolated session): GET `/search/home/` → scrape `csrfmiddlewaretoken` → POST `/search/home/` `{prohibition_agreement:1, csrfmiddlewaretoken}` (sets `csrftoken` cookie) → POST `/search/report/data/` with `report_types=[11]`, `filer_types=[1]`, `submitted_start_date`, `draw/start/length`, headers `X-CSRFToken` + `X-Requested-With: XMLHttpRequest` + real UA → JSON index (filer + `/search/view/ptr/{uuid}/` link + filing date) → GET each detail page → parse HTML table. **403 without the handshake** (confirmed this run). | `requests.Session` first; **only escalate to Playwright Mode-B** if the CSRF/agree gate resists scripting. Treat eFD as ground truth over any mirror. |

**Access classes:** House XML index = `source_class: filing` (index); House PTR PDF = `filing`
(pdf-extracted, flag `dirty` aggressively); Senate index JSON = `xhr-json`; Senate detail = `html`.

**Paper/scanned filings:** Senate `/search/view/paper/{uuid}/` and many House PTR PDFs are scanned
images → OCR path, dirty-flagged, never silently trusted. Amendments are separate rows.

### (b) Bill / committee linkage

- **Primary:** **Congress.gov API v3** (`https://api.congress.gov/v3/…`, free `api.data.gov` key,
  5,000/hr). Pull `/bill/{congress}/{type}/{num}` (policyArea, subjects, sponsors+bioguideId,
  committees), `/member/{bioguide}/sponsored-legislation`, `/member/{bioguide}/cosponsored-legislation`.
- **Required companion (roster gap):** `unitedstates/congress-legislators`
  `committee-membership-current.json` + `committees-current.json` (jurisdiction) +
  `legislators-current.yaml` (the **bioguide↔govtrack↔opensecrets↔fec crosswalk** = the join key).
- **Fallback:** GovTrack API v2 (no key, needs a real UA — default fetcher UA 403s) for
  role/committee membership; GovInfo (free `api.data.gov` key) for committee-report full text.
- **Dead — do NOT use:** ProPublica Congress API (retired; confirmed "historical reference only").

### (c) Sector labeling (every ticker)

- **Primary:** TradingView scanner POST `https://scanner.tradingview.com/america/scan`
  (`columns:[name,sector,industry,…]`, many tickers per POST; `source_class: xhr-json`). Already
  wired in `scripts/aiinvest/tradingview.py`. Covers ETFs/ADRs lacking clean SIC.
- **Authoritative cross-check / fallback:** SEC EDGAR — `company_tickers.json` (ticker→CIK) →
  `https://data.sec.gov/submissions/CIK{10-digit}.json` (`sic`, `sicDescription`); `source_class: api`.
  **Descriptive UA with contact email required**, ~10 req/s fair-access.
- **Honesty:** SIC ≠ TRBC ≠ GICS. Keep **both** labels rather than forcing one; never label as GICS.
- **Non-equity rows:** PTR `Ticker` is frequently `--` (munis, mutual funds, options, crypto,
  private holdings). Sector = `null` / `"non-equity"`; do not fabricate a mapping.

---

## 3. Canonical schema

New module `scripts/aiinvest/congress.py`; envelopes via existing `schema.make_envelope`
(`clean`/`parse_number` reject dirty values, mirroring the GuruTrade `"."` fix). Site export
shape under `web/public/data/congress.json` (or a `/api/congress` route). All times UTC ISO-8601.

### 3.1 `congress_trade`
```jsonc
{
  "politician": "Hon. Robert B. Aderholt",     // raw filed name string
  "bioguide_id": "A000055",                     // resolved via legislators crosswalk; null if unmatched
  "chamber": "house",                            // "house" | "senate"
  "party": "R",                                  // from crosswalk; null if unresolved
  "state": "AL",
  "district": "AL04",                            // House only; null for Senate
  "ticker": "NVDA",                              // null when filing shows "--"
  "sector": "Electronic Technology",             // TradingView primary; null/"non-equity" if no ticker
  "sector_sic": "3674",                          // SEC SIC cross-check; null if unmatched
  "sector_source": "tradingview",                // which label won the render
  "asset": "NVIDIA Corp - Common Stock",         // free-text asset description (authoritative)
  "asset_type": "Stock",                         // Stock | Municipal Security | Mutual Fund | Option | ...
  "txn_type": "purchase",                         // purchase | sale | exchange  (P/S/E)
  "owner": "self",                               // self | spouse | dependent | joint
  "txn_date": "2026-05-08",                       // transaction date (from PTR body)
  "filing_date": "2026-05-28",                    // disclosure/filing date (from index)
  "reporting_lag_days": 20,                       // filing_date - txn_date (computed; may be negative→flag dirty)
  "amount_range_low": 1001,                        // bucket low bound (int USD)
  "amount_range_high": 15000,                      // bucket high bound (int USD); null/Infinity-sentinel for "Over $50,000,000"
  "amount_range_label": "$1,001 - $15,000",       // verbatim filed string (NEVER a point estimate)
  "is_amendment": false,
  "fact_label": "reported",                       // ALWAYS "reported"/"filed" — self-reported, unverified
  "source": "House Clerk PTR DocID 20032062",     // provider + specific id
  "source_url": "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/20032062.pdf",
  "source_class": "filing",                       // filing | xhr-json | html | api
  "extraction_method": "pdf-text",                // pdf-text | ocr | html-table | json
  "dirty": false,                                 // true if any field failed validation (esp. OCR)
  "retrieved_at": "2026-05-31T00:00:00Z"
}
```
**Bucket parser** maps the fixed STOCK Act tiers to `(low, high)`:
`$1,001–$15,000 · $15,001–$50,000 · $50,001–$100,000 · $100,001–$250,000 · $250,001–$500,000 · $500,001–$1,000,000 · $1,000,001–$5,000,000 · $5,000,001–$25,000,000 · $25,000,001–$50,000,000 · Over $50,000,000`
Store `low`/`high` only. **Never** sum, average, or render a midpoint as a fact (a labeled
estimated-range aggregate with disclosed midpoint assumption is the only permitted aggregation).

### 3.2 `politician_profile`
```jsonc
{
  "bioguide_id": "A000055",
  "name": "Hon. Robert B. Aderholt",
  "chamber": "house",
  "party": "R",
  "state": "AL",
  "district": "AL04",
  "committees": [                                  // from unitedstates/congress-legislators roster
    { "system_code": "hsap00", "name": "Appropriations",
      "role": "Member", "jurisdiction": "Appropriations" }
  ],
  "id_crosswalk": { "govtrack": 400004, "opensecrets": "N00003028", "fec": ["H6AL04098"] },
  "trade_count": 37,
  "sectors_traded": ["Electronic Technology", "Finance"],
  "source": "unitedstates/congress-legislators + congress.gov v3",
  "source_class": "api",
  "retrieved_at": "2026-05-31T00:00:00Z"
}
```

### 3.3 `conflict_signal` (optional, strictly correlational)
```jsonc
{
  "bioguide_id": "A000055",
  "politician": "Hon. Robert B. Aderholt",
  "ticker": "NVDA",
  "sector": "Electronic Technology",
  "trade_ref": "House Clerk PTR DocID 20032062",   // links to a congress_trade
  "txn_date": "2026-05-08",
  "linkage_type": "committee_jurisdiction",         // committee_jurisdiction | sponsored_bill | cosponsored_bill
  "committee": { "system_code": "hsap00", "name": "Appropriations", "role": "Member" },
  "bill": { "congress": 119, "type": "hr", "number": 1234,
            "policy_area": "Science, Technology, Communications",
            "latest_action_date": "2026-04-20" },
  "sector_policy_match": "Semiconductors ↔ Science/Technology policyArea",
  "days_between_trade_and_action": 18,              // |txn_date - bill action| ; informational, NOT evidence
  "certainty": "correlational",                     // ENUM: ONLY "correlational" is valid for this record
  "signal_note": "Member sits on a committee with jurisdiction over this policy area AND traded a stock in that sector near a legislative action date. Co-occurrence only — not evidence of wrongdoing, intent, or non-public information.",
  "for_human_review": true,
  "source": "congress.gov v3 + congress-legislators + PTR",
  "source_class": "api",
  "retrieved_at": "2026-05-31T00:00:00Z"
}
```
**Hard rule in code:** `conflict_signal.certainty` is a closed enum whose only value is
`"correlational"`. There is no schema path to emit a causal/intent claim. `fact_label` on any
trade is constrained to `{"reported","filed"}` — never `"bought"`/`"sold"` as bare fact.

---

## 4. Honest limits, disclaimer & labeling rules

**Structural truths the feature must carry (these are not bugs to fix — they cap what can be claimed):**

1. **Dollar amounts are RANGE BUCKETS, never exact.** PTRs disclose tiers (`$1,001–$15,000` …
   `Over $50,000,000`). Store `low`/`high`; render the verbatim band. A midpoint is an estimate,
   never a traded figure. The House XML index carries **no dollar field at all** — amounts live
   only inside the PTR PDF.
2. **Reporting lag up to 45 days** (file within 30 days of notification, ≤45 days after the trade —
   and members miss it). `txn_date` ≠ `filing_date`; the dataset is structurally stale and may be
   incomplete. "Traded the day before the vote" claims are fragile at the day level — show both
   dates and treat timing as approximate.
3. **Correlation, never causation.** A committee seat + a sector trade + nearby legislative action
   is **co-occurrence only**. The filer may not even control the account (blind trust, spouse,
   advisor-managed; many PTRs are spouse/dependent). **Intent is unobservable.**
4. **"Pushing favorable laws" is only ever a flagged signal — never a stated fact.** Asserting a
   member traded on non-public information or legislated to enrich a holding is an **unproven intent
   claim with defamation + accuracy risk**. The data can show co-occurrence; it can never show
   intent or wrongdoing. Every such linkage is labeled `correlational`, deep-links the primary
   filing + the bill record, and is surfaced for human review only.
5. **Self-reported & amendable.** All trades are self-reported, unverified filings; amendments and
   late filings occur — carry an `is_amendment` / `dirty` / "may be incomplete" flag.
6. **Legal/ToS gate (Senate eFD).** The Ethics in Government Act prohibition (5 U.S.C. app. §105(c))
   bars use of the disclosures "for any commercial purpose" (news/communications media excepted),
   solicitation, or credit-rating; civil penalty up to $10,000. This repo is **educational/research
   only**; commercial productization may violate the statute and the agree-to-terms gate. House
   data is public domain but treat figures as indicative.

**Exact disclaimer (ship verbatim on every `/congress` view and export):**

> Educational and informational use only. Not investment advice. Source: periodic transaction
> reports (PTRs) and annual financial disclosures filed under the Stop Trading on Congressional
> Knowledge (STOCK) Act of 2012 with the U.S. House Clerk and U.S. Senate Office of Public Records.
> Dollar figures are the disclosed RANGE BRACKETS (e.g. $1,001–$15,000), not exact amounts; we
> display the filed range. Filings are reported with a lag of up to 45 days after the transaction,
> so this data is not real-time and may be incomplete. All trades shown are SELF-REPORTED FILINGS
> that have not been independently verified; amendments and late filings occur. Any timing
> relationship between a filed trade and legislation, hearings, or committee activity is shown for
> transparency and is CORRELATIONAL ONLY. Nothing here states or implies that any official traded
> on, or possessed, material non-public or inside information, or violated any law. We make no such
> allegation.

**Mandatory labeling rules (enforced in code + UI):**
(a) every `$` rendered as a range string, never a single number, never midpoint-as-fact;
(b) every record tagged `source_class: filing` + `filing_date` + `txn_date` + a visible "up-to-45-day lag" note;
(c) every trade prefixed "reported"/"filed"/"disclosed" — never "bought"/"sold" as bare fact;
(d) any trade↔bill/committee correlation badge labeled "CORRELATIONAL — not evidence of wrongdoing", with **causal verbs banned** ("traded on", "profited from inside info", "pushed laws to benefit");
(e) an "amended / may be incomplete" flag;
(f) every claim deep-links the primary filing PDF/page so the user verifies the source, not our restatement.

---

## 5. Phased build plan (TDD throughout; mark first defensible slice)

> Per CLAUDE.md: `superpowers:brainstorming` before build, `superpowers:test-driven-development`
> for parsers, `superpowers:verification-before-completion` before claiming any pull "works"
> (show extracted values + timestamp). Run `cd scripts && python -m pytest`.

**P0 — House trades pull module (SHIP FIRST — most defensible).**
Pure Mode A, no gate, no browser, all-free, confirmed 200 this run.
- `congress.py`: download `{YEAR}FD.zip` (real UA + contact email) → parse `{YEAR}FD.xml` →
  filter `FilingType=='P'` → build PTR PDF URLs → extract trades (pdfplumber/PyPDF; OCR via
  tesseract for scanned PDFs, dirty-flagged).
- Tests: XML index parse (fixture), bucket-string → `(low,high)` parser (all 10 tiers + "Over"),
  `reporting_lag_days` computation, dirty-value rejection on OCR garbage, FilingType filter
  (only `P`, exclude `O/C/D/X/A`). **Defensible to ship standalone.**

**P1 — Schema, validation & sector enrichment.**
- `congress_trade` envelope via `schema.make_envelope`; integrate `tradingview.py` (primary) +
  EDGAR SIC (`company_tickers.json` → `submissions/CIK*.json`, cross-check). `--` ticker → sector null.
- Tests: every trade carries `retrieved_at`/`source`/`source_class`; sector reconciliation keeps
  both labels; non-equity rows handled.

**P2 — Senate trades pull (Mode B isolated session).**
- `requests.Session` agree-handshake → JSON index → HTML detail parser; escalate to Playwright
  Mode-B only if the gate resists scripting. Quiesce other browser work; close/reopen on rotation.
- Tests: handshake mock (csrf extraction), index JSON parse, detail HTML table parse,
  paper/PDF (`/view/paper/`) routed to OCR path, amendment rows.

**P3 — Politician profile + conflict-signal join.**
- Pull `legislators-current.yaml` (crosswalk) + `committee-membership-current.json` once (cache).
  Congress.gov v3 (real `api.data.gov` key, **not** DEMO_KEY) for sponsored/cosponsored bills +
  policyArea. Name→bioguide via crosswalk (handles nicknames/suffixes/replacements — **the weak
  point**; never naive string match). Emit `conflict_signal` with `certainty:"correlational"` only.
- Tests: name→bioguide resolution incl. ambiguous names → `bioguide_id:null` + flag; signal never
  emits a non-`correlational` certainty; policyArea→sector map is auditable & conservative.

**P4 — Site page `/congress`** (Next.js, see §6). Static export `web/public/data/congress.json`
via `siteexport.py` pattern. Disclaimer banner is a P4 acceptance gate — page cannot render trades
without it.

**Cross-cutting:** never depend on dead S3 / frozen GitHub mirror / ProPublica; Quiver/Finnhub/FMP
are optional cross-check only (key-gated). Stamp everything UTC. Cache crosswalk & sector labels.

---

## 6. Site UX sketch — `/congress` (data-terminal dark theme)

**Top:** persistent disclaimer banner (§4 verbatim, dismissible-but-re-shown) + global "up-to-45-day
lag · amounts are filed ranges · self-reported, unverified" strip.

**Main: sortable/filterable trade table.**
- Columns: Politician (party chip R/D/I) · Chamber · State/District · Ticker · **Sector** (colored
  chip; "non-equity" when `--`) · Asset · Type (Buy/Sell/Exchange icon, prefixed "reported") ·
  **Amount range** (rendered band, never a number) · Txn date · Filing date · **Lag (days)** ·
  Conflict badge · source-PDF link icon.
- Sort by: politician, sector, amount-range (by `low` bound, with band tooltip), recency
  (filing_date or txn_date toggle).
- Filters: chamber, party, sector (multi-select, all sectors), txn_type, ticker search,
  date range (txn vs filing toggle), amount-band, "has conflict signal", "amended only".

**Per-politician drill-down `/congress/[bioguide]`:** profile header (committees + jurisdictions,
ID crosswalk links to OpenSecrets/GovTrack), trade history timeline (txn vs filing markers showing
the lag gap visually), sector-mix donut, list of correlational `conflict_signal`s — each a card
labeled "CORRELATIONAL — for review, not evidence of wrongdoing" with deep-links to both the PTR
and the bill on congress.gov.

**Sector breakdown view:** all-sectors treemap/bar of trade counts (and labeled estimated-range
aggregate $ with explicit midpoint-assumption disclaimer), drill into a sector → members + trades.

**Conflict-signal badges:** amber "⚑ correlational" chip on rows that have a `conflict_signal`;
hover → "Committee jurisdiction / sponsored bill in this sector near this trade date — co-occurrence
only." **No causal language anywhere.** Clicking always lands on the primary filing + bill record.

---

## 7. Provenance & caveats

Live-probed this run (2026-05-31, real UA): House ZIP 2026 **200/39873B**, House PTR PDF
**200/application-pdf**, Congress.gov v3 **200/json**, SEC `company_tickers.json` **200/792364B**,
Senate eFD home (no session) **403** (gated, as expected), house-stock-watcher S3 **403 AccessDenied**
(dead, as expected). Senate JSON index shape, congress.gov bill fields, GovTrack 403-on-default-UA,
and Quiver 401 are carried from the upstream research run (cited, not re-probed here). What can
decay: TradingView scanner is unofficial (may change without notice — EDGAR SIC is the durable
fallback); Senate eFD session/CSRF flow can change; PTR OCR quality is the main quality risk.
**Not financial advice; not an accusation of wrongdoing against any individual.**
