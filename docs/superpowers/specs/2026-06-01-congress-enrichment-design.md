# Congress endpoint enrichment — design

**Date:** 2026-06-01
**Status:** approved (brainstorming gate passed)
**Owner decisions:** (1) policy areas = committee-derived now + sponsored legislation if a
`CONGRESS_GOV_API_KEY` is present (graceful degradation); (2) ideology = DW-NOMINATE score +
labeled Lib↔Con axis chip (Voteview).

Educational/research only — not investment advice. **Not an accusation of wrongdoing against
any individual.**

---

## 1. Goal

Enrich every politician on `/congress` with: **party**, **political-spectrum/ideology**
(Voteview DW-NOMINATE), and **policy areas** they work on (committee jurisdiction; plus
sponsored legislation when a congress.gov key is available). Everything stays **factual,
sourced, and descriptive** — never an inference about motive.

## 2. Data sources (all Mode-A REST, public/academic, stamped)

| Field | Source | source_class | Verified 2026-06-01 |
|---|---|---|---|
| Party / state / district / bioguide | `legislators-current.json` (already fetched in `pull_conflict.py`) | filing | yes (existing) |
| Ideology dim1/dim2 | Voteview `https://voteview.com/static/data/out/members/H119_members.csv` | api (academic) | yes — 450 rows, `bioguide_id`,`nominate_dim1/2`,`party_code`,`chamber`,`state_abbrev`,`district_code`,`bioname` |
| Policy areas | committee assignments (from `pull_conflict` linkage) → curated committee→policy-domain map | filing | yes (existing linkage) |
| Sponsored bills *(optional)* | `https://api.congress.gov/v3/member/{bioguide}/sponsored-legislation` | api | yes — `sponsoredLegislation[]`; **no key in env → layer OFF by default** |

Voteview CSV carries an extra non-House `chamber=='President'` row → **filter `chamber=='House'`**.
`party_code`: 100→Democrat, 200→Republican, else Independent (cross-check only; roster party is authoritative).

## 3. JSON contract

### 3.1 `data/congress/member_profiles.json` (new, written by `pull_member_profiles.py`)
```json
{
  "generated_at": "<UTC ISO-8601>",
  "source": "<voteview> | <legislators> | <committees> | <membership> [| <congress.gov>]",
  "source_class": "api",
  "congress": 119,
  "disclaimer": "<educational + not-accusation + ideology/policy-descriptive clause>",
  "ideology_note": "DW-NOMINATE 1st dimension is a statistical measure of roll-call voting patterns (Voteview/academic), not a personal judgment.",
  "committee_policy_map": [ {"committee": "Energy and Commerce", "policy_areas": ["Energy","Health","Telecommunications","Consumer protection"]} ],
  "committee_policy_map_note": "APPROXIMATE curated mapping of House committees to policy domains; not a legal statement of jurisdiction.",
  "bills_enabled": false,
  "match_coverage": {"n_politicians": 0, "n_matched": 0, "coverage_pct": 0.0, "n_unmatched": 0, "unmatched": []},
  "by_politician": {
    "<display name>": {
      "bioguide": "A000370",
      "party": "Democrat|Republican|Independent|null",
      "ideology": {"dim1": -0.31, "dim2": 0.12, "label": "Liberal|Moderate|Conservative|null", "position": 0.0_to_1.0_or_null},
      "committees": ["Energy and Commerce", "..."],
      "policy_areas": ["Energy", "Health", "..."],
      "sponsored": null
    }
  }
}
```
`sponsored` (only when key present, else `null`):
```json
{"n": 14, "top_policy_areas": [{"area": "Energy", "n": 4}], "recent": [
  {"number": "1234", "type": "HR", "title": "<verbatim public-record title>", "policy_area": "Energy", "introduced_date": "2025-03-04", "latest_action": "<verbatim>"}]}
```

### 3.2 `web/public/data/congress.json` additions (merged by `export_congress.py` when `member_profiles.json` exists)
- `by_politician[i]` gains: `ideology` (object), `policy_areas` (string[]), `sponsored` (object|null). `party` already present.
- `totals` gains: `party_breakdown` ({Democrat,Republican,Independent,unknown}), `n_with_ideology` (int), `bills_enabled` (bool).
- top-level gains: `ideology_note`, `committee_policy_map`, `committee_policy_map_note`, `member_source`, `member_match_coverage`.
- Absent file → output byte-identical to today (overlay strictly additive, like the conflict overlay).

## 4. Code units

### 4.1 `scripts/aiinvest/member_profile.py` (pure, TDD)
- `parse_dwnominate(csv_text) -> {bioguide: {"dim1","dim2","party_code"}}` — House rows only; skip blank bioguide.
- `ideology_label(dim1) -> "Liberal"|"Moderate"|"Conservative"|None` — `<-0.25`→Liberal, `>0.25`→Conservative, between→Moderate, `None`→None.
- `ideology_position(dim1) -> float|None` — `clamp((dim1+1)/2, 0, 1)`.
- `normalize_party(raw) -> "Democrat"|"Republican"|"Independent"|None` — accepts roster strings or DW party_code.
- `committee_policy_areas(committees, policy_map) -> sorted unique list`.
- `summarize_sponsored(bills, top_n=5) -> {"n","top_policy_areas","recent"}`.
- `build_member_profile(name, bioguide, party, committees, dwnom_row, policy_map, sponsored) -> profile dict` (§3.1 shape).
- `validate_profile(profile)` — raises if: ideology `label` not in allowed set; `party` not in allowed set; any **generated** descriptive field contains a `conflict.BANNED_WORDS` term. **Does NOT scan verbatim public-record bill titles** (they are facts, not generated prose).
- `COMMITTEE_POLICY_MAP` constant — curated, APPROXIMATE, human-readable policy domains (distinct from the conflict TradingView-sector map). Procedural/broad committees (Rules, Ethics, House Administration) omitted.

### 4.2 `scripts/pull_member_profiles.py` (CLI)
Reuses `pull_conflict.fetch_roster`, `pull_conflict.fetch_membership_linkage`, `conflict.match_member`,
`pull_conflict.load_traded_politicians`. Fetches Voteview CSV. If `os.environ.get("CONGRESS_GOV_API_KEY")`,
also fetches sponsored legislation per matched bioguide (polite delay; cap recent at top_n) and sets
`bills_enabled=true`; else `sponsored=null`, `bills_enabled=false`. Writes §3.1. Flags: `--years`, `--out`, `--delay`, `--limit-members` (debug).

### 4.3 `scripts/export_congress.py`
Add `_load_member_doc()` (reads `member_profiles.json` or None) and merge into `aggregate_by_politician`
+ `compute_totals` + top-level (§3.2). Additive; absent → unchanged. Mirror the existing conflict-overlay pattern.

### 4.4 `scripts/refresh_congress.py`
Insert a `pull_member_profiles.py` step after the conflict step and before `export_congress.py`
(guarded by file existence, like conflict). Update `test_refresh.py` expectations.

### 4.5 Web
- `web/lib/congress_profile.ts` (client-safe, no node:fs): `Ideology` type, `ideologyLabel(dim1)`, `ideologyPosition(dim1)` (mirror the Python thresholds), `SponsoredSummary` type.
- `web/lib/data.ts`: extend `CongressPolitician` with `ideology?`, `policy_areas?`, `sponsored?`; extend `CongressTotals` with `party_breakdown?`, `n_with_ideology?`, `bills_enabled?`; add top-level `ideology_note?`, `committee_policy_map?`.
- `web/components/CongressInteractive.tsx`: per-politician summary card gains party chip, **ideology axis chip** (`‹Lib —●— Con›` + numeric score; tooltip cites Voteview + "statistical measure, not a judgment"), policy-area tags, and a sponsored-bill list when present. New filters: by party, by ideology bucket.
- `web/app/congress/page.tsx`: explainer + provenance + disclaimer extended for ideology (Voteview) and policy areas (committee jurisdiction; public record). Keep the amber non-accusation banner.

## 5. Legal rails (hard)
- The phrase **"fighting for" is banned** from data + UI (implies unverifiable motive). Fields are
  labeled **"Policy areas (committee jurisdiction)"** and **"Sponsored legislation (public record)."**
- Ideology = an **academic measurement of voting patterns**, explicitly labeled, never a character judgment.
- Reuse `conflict.BANNED_WORDS`; `validate_profile` enforces it on generated prose only.
- Disclaimer retains "not investment advice" + "Not an accusation of wrongdoing against any individual."
- Honest coverage: report match rate; never fabricate an ideology/party/policy value (use `null`).

## 6. Testing (TDD)
- `scripts/tests/test_member_profile.py` — parse_dwnominate (House-only, blank-skip), ideology_label
  thresholds + None, ideology_position clamp, normalize_party (strings + codes), committee_policy_areas,
  summarize_sponsored, build_member_profile shape, validate_profile (rejects banned word in generated
  prose, rejects bad label/party, ACCEPTS a banned-substring inside a verbatim bill title).
- `scripts/tests/test_export_congress.py` — additive merge present/absent; totals fields; byte-identical when absent.
- `scripts/tests/test_refresh.py` — new step ordering, guarded by file existence.

## 7. Orchestration
A Workflow runs the build with **disjoint file sets** coded against this contract concurrently:
CORE (4.1 + 4.2), WIRING (4.3 + 4.4), WEB (4.5) — each TDD where a test harness exists. Then a verify
phase (pytest + tsc/next build). Integration (run `pull_member_profiles.py` with real data →
`export_congress.py` → rebuild congress.json) and the final `vercel --prod` deploy are done by the
orchestrator (keeps data/ writes serial and the human in the loop).
