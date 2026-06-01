"""RED tests for export_congress.py — merges House PTR years into web/public/data/congress.json.

PURE FUNCTIONS ONLY — no filesystem writes. We feed synthetic in-memory inputs
that mirror the real shape of data/congress/house_YYYY.json and assert on the
merged/aggregated dict that the page consumes.

Honesty rails (CLAUDE.md):
- House amounts are RANGE BUCKETS (low/high), never a single fabricated number.
- Volume sums are explicitly low/high BOUNDS.
- The carried disclaimer must keep both required honesty clauses.
- null-sector rows are excluded from by_sector but still present in trades.
"""
import export_congress as ec


DISCLAIMER = (
    "Educational/research only -- not investment advice; amounts are reported "
    "ranges; up to 45-day lag. Self-reported, unverified STOCK Act filings with "
    "the U.S. House Clerk. Not an accusation of wrongdoing against any individual."
)


def _prov(year, skipped):
    return {
        "generated_at": f"{year}-01-01T00:00:00Z",
        "source": f"https://disclosures-clerk.house.gov/{year}FD.zip",
        "source_class": "filing",
        "year": year,
        "scanned_skipped": skipped,
        "disclaimer": DISCLAIMER,
    }


def _trade(politician, ticker, sector, txn_type, txn_date, lo, hi,
           state="AL01", filing_date="01/15/2025", lag=10):
    return {
        "politician": politician,
        "chamber": "House",
        "state": state,
        "party": None,
        "ticker": ticker,
        "sector": sector,
        "industry": "X",
        "asset": f"{ticker} stock",
        "txn_type": txn_type,
        "txn_date": txn_date,
        "filing_date": filing_date,
        "reporting_lag_days": lag,
        "amount_range_low": lo,
        "amount_range_high": hi,
        "source": f"https://disclosures-clerk.house.gov/ptr/{ticker}.pdf",
        "source_class": "filing",
        "retrieved_at": f"{txn_date[-4:]}-02-02T00:00:00Z",
    }


def _input_2025():
    return {
        "provenance": _prov(2025, 66),
        "scanned_skipped": [1] * 66,
        "http_failed": [],
        "trades": [
            _trade("Alice Member", "NVDA", "Electronic Technology", "P", "07/01/2025", 1001, 15000),
            _trade("Alice Member", "NVDA", "Electronic Technology", "S", "07/02/2025", 15001, 50000),
            _trade("Alice Member", "MSFT", "Technology Services", "P", "07/03/2025", 1001, 15000),
            _trade("Bob Member", "XOM", "Energy Minerals", "S (partial)", "06/15/2025", 50001, 100000, state="TX22"),
            # null-sector row (e.g. unresolved): must stay in trades, excluded from by_sector
            _trade("Bob Member", "ZZZZ", None, "P", "06/20/2025", 1001, 15000, state="TX22"),
        ],
    }


def _input_2026():
    return {
        "provenance": _prov(2026, 23),
        "scanned_skipped": [1] * 23,
        "http_failed": [],
        "trades": [
            _trade("Alice Member", "NVDA", "Electronic Technology", "P", "03/01/2026", 1001, 15000),
            _trade("Carol Member", "AAPL", "Electronic Technology", "S", "02/10/2026", 1001, 15000, state="CA12"),
        ],
    }


# --------------------------------------------------------------------------

def test_merge_count_equals_sum_of_inputs_minus_dups():
    a, b = _input_2025(), _input_2026()
    out = ec.build(a, b)
    # 5 + 2 = 7 distinct rows here (no dups across these two)
    assert len(out["trades"]) == 7
    assert out["totals"]["n_trades"] == 7


def test_dedup_identical_rows():
    a = _input_2025()
    b = _input_2026()
    # inject an exact duplicate of an existing 2025 row into 2026's list
    dup = dict(a["trades"][0])
    b["trades"].append(dup)
    out = ec.build(a, b)
    # still 7 — the duplicate collapses
    assert len(out["trades"]) == 7


def test_trades_keep_only_essential_fields_with_year():
    out = ec.build(_input_2025(), _input_2026())
    keys = set(out["trades"][0].keys())
    assert keys == {
        "politician", "state", "party", "year", "ticker", "sector", "asset",
        "txn_type", "txn_date", "filing_date", "reporting_lag_days",
        "amount_range_low", "amount_range_high", "source",
    }
    # year is derived and correct
    years = {t["year"] for t in out["trades"]}
    assert years == {2025, 2026}


def test_disclaimer_carried_with_both_required_clauses():
    out = ec.build(_input_2025(), _input_2026())
    d = out["disclaimer"]
    assert "not investment advice" in d
    assert "Not an accusation of wrongdoing against any individual" in d
    assert out["source_class"] == "filing"


def test_by_politician_volume_math_and_buy_sell_split():
    out = ec.build(_input_2025(), _input_2026())
    alice = next(p for p in out["by_politician"] if p["politician"] == "Alice Member")
    # Alice: 2025 -> P 1001/15000, S 15001/50000, P 1001/15000 ; 2026 -> P 1001/15000
    assert alice["n_trades"] == 4
    assert alice["n_buys"] == 3   # three P
    assert alice["n_sells"] == 1  # one S
    assert alice["est_volume_low"] == 1001 + 15001 + 1001 + 1001
    assert alice["est_volume_high"] == 15000 + 50000 + 15000 + 15000
    # last trade date is the max txn_date
    assert alice["last_trade_date"] == "03/01/2026"
    # top_sectors present
    secs = {s["sector"]: s["n"] for s in alice["top_sectors"]}
    assert secs.get("Electronic Technology") == 3
    assert secs.get("Technology Services") == 1


def test_partial_sell_counts_as_sell():
    out = ec.build(_input_2025(), _input_2026())
    bob = next(p for p in out["by_politician"] if p["politician"] == "Bob Member")
    # Bob: 'S (partial)' XOM + null-sector 'P' ZZZZ
    assert bob["n_sells"] == 1
    assert bob["n_buys"] == 1


def test_by_sector_excludes_null_but_trades_keep_it():
    out = ec.build(_input_2025(), _input_2026())
    sectors = {s["sector"] for s in out["by_sector"]}
    assert None not in sectors
    assert "" not in sectors
    # the null-sector ZZZZ row is still in trades
    assert any(t["ticker"] == "ZZZZ" and t["sector"] is None for t in out["trades"])


def test_by_sector_volume_and_politician_count():
    out = ec.build(_input_2025(), _input_2026())
    et = next(s for s in out["by_sector"] if s["sector"] == "Electronic Technology")
    # rows: Alice NVDA P, Alice NVDA S, Alice NVDA P(2026), Carol AAPL S  => 4 trades
    assert et["n_trades"] == 4
    assert et["n_buys"] == 2   # two P
    assert et["n_sells"] == 2  # one S + Carol S
    assert et["n_politicians"] == 2  # Alice + Carol
    assert et["est_volume_low"] == 1001 + 15001 + 1001 + 1001
    assert et["est_volume_high"] == 15000 + 50000 + 15000 + 15000


def test_by_sector_volume_sum_equals_trades_sum():
    """Bucket-sum identity: summing by_sector volumes (non-null sectors) +
    null-sector trade volumes must equal the grand total of all trades."""
    out = ec.build(_input_2025(), _input_2026())
    sector_low = sum(s["est_volume_low"] for s in out["by_sector"])
    null_low = sum(t["amount_range_low"] for t in out["trades"] if t["sector"] in (None, ""))
    grand_low = sum(t["amount_range_low"] for t in out["trades"])
    assert sector_low + null_low == grand_low


def test_totals_block():
    out = ec.build(_input_2025(), _input_2026())
    tot = out["totals"]
    assert tot["n_trades"] == 7
    assert tot["n_politicians"] == 3            # Alice, Bob, Carol
    assert tot["n_tickers"] == 5                # NVDA, MSFT, XOM, ZZZZ, AAPL
    assert tot["n_sectors"] == 3                # ET, Tech Services, Energy Minerals (null excluded)
    assert tot["n_scanned_skipped"] == 66 + 23  # summed from both inputs
    # date range over all txn_date (MM/DD/YYYY string compare won't work -> must be real dates)
    assert tot["date_min"] == "2025-06-15"
    assert tot["date_max"] == "2026-03-01"
    assert tot["est_volume_low"] == sum(t["amount_range_low"] for t in out["trades"])
    assert tot["est_volume_high"] == sum(t["amount_range_high"] for t in out["trades"])


def test_generated_at_and_source_present():
    out = ec.build(_input_2025(), _input_2026())
    assert out["generated_at"].endswith("Z")
    assert "disclosures-clerk.house.gov" in out["source"]


# --------------------------------------------------------------------------
# Conflict overlay merge (strictly CORRELATIONAL committee/sector overlap).
# When conflict_signals.json is present, build(..., conflict_doc=...) merges it:
#   (a) per-trade `conflict_signal` (certainty 'correlational' + matching
#       committee(s) + the exact validated rationale),
#   (b) by_politician gains `committees` + `jurisdiction_sectors`,
#   (c) totals gains `n_conflict_flagged` + `n_politicians_matched`.
# Absent conflict_doc -> output is byte-for-byte the legacy shape (rails kept).
# --------------------------------------------------------------------------

# Curated APPROXIMATE map (short committee name -> sectors), mirroring the one
# pull_conflict.py writes into conflict_signals.json.
_MAP = [
    {"committee": "Financial Services", "sectors": ["Finance"]},
    {"committee": "Science, Space, and Technology",
     "sectors": ["Technology Services", "Electronic Technology"]},
    {"committee": "Energy and Commerce",
     "sectors": ["Energy Minerals", "Utilities"]},
]


def _conflict_doc():
    """A conflict_signals.json-shaped dict for the synthetic 2025/2026 inputs.

    - Alice: Science, Space, and Technology -> covers Electronic Technology +
      Technology Services (so her NVDA/MSFT trades flag; her trades are all in
      those sectors).
    - Bob: Energy and Commerce -> covers Energy Minerals (his XOM trade flags;
      his null-sector ZZZZ trade does NOT).
    - Carol: NOT matched to any roster member (absent) -> her AAPL trade,
      though Electronic Technology, gets NO signal (no member entry).
    """
    return {
        "generated_at": "2026-05-31T00:00:00Z",
        "source": "https://unitedstates.github.io/congress-legislators/legislators-current.json",
        "source_class": "filing",
        "committee_sector_map": _MAP,
        "committee_sector_map_note": "APPROXIMATE / curated heuristic mapping.",
        "match_coverage": {"n_politicians": 3, "n_matched": 2, "coverage_pct": 66.7,
                           "n_unmatched": 1, "unmatched": ["Carol Member"]},
        "by_politician": {
            "Alice Member": {
                "bioguide": "A000001",
                "committees": ["House Committee on Science, Space, and Technology"],
                "jurisdiction_sectors": ["Electronic Technology", "Technology Services"],
            },
            "Bob Member": {
                "bioguide": "B000001",
                "committees": ["House Committee on Energy and Commerce"],
                "jurisdiction_sectors": ["Energy Minerals", "Utilities"],
            },
        },
    }


def test_no_conflict_doc_keeps_legacy_trade_shape():
    # Backward-compat: without a conflict_doc, trades keep ONLY essential fields
    # and there is no conflict_signal / committees enrichment / new totals.
    out = ec.build(_input_2025(), _input_2026())
    assert all("conflict_signal" not in t for t in out["trades"])
    assert all("committees" not in p for p in out["by_politician"])
    assert "n_conflict_flagged" not in out["totals"]
    assert "n_politicians_matched" not in out["totals"]
    assert "committee_sector_map" not in out


def test_merge_flags_only_overlapping_trades():
    out = ec.build(_input_2025(), _input_2026(), conflict_doc=_conflict_doc())
    flagged = [t for t in out["trades"] if t.get("conflict_signal")]
    # Alice: NVDA(ET) x2 in 2025 + MSFT(Tech Svcs) + NVDA(ET) 2026 = 4 flagged.
    # Bob: XOM(Energy Minerals) = 1 flagged. Bob ZZZZ null-sector = NOT flagged.
    # Carol: unmatched member -> NOT flagged even though AAPL is ET.
    assert len(flagged) == 5
    # the null-sector trade is never flagged
    assert all(t.get("sector") not in (None, "") for t in flagged)
    # Carol's AAPL is present in trades but unflagged
    carol = next(t for t in out["trades"] if t["politician"] == "Carol Member")
    assert "conflict_signal" not in carol


def test_merge_signal_is_correlational_with_exact_rationale():
    out = ec.build(_input_2025(), _input_2026(), conflict_doc=_conflict_doc())
    xom = next(t for t in out["trades"]
               if t["ticker"] == "XOM" and t.get("conflict_signal"))
    sig = xom["conflict_signal"]
    assert sig["certainty"] == "correlational"
    assert sig["committees"] == ["Energy and Commerce"]
    assert sig["sector"] == "Energy Minerals"
    assert sig["rationale"] == (
        "Serves on the Energy and Commerce Committee, which has jurisdiction over "
        "the Energy Minerals sector. This is a correlational overlap only — not "
        "evidence of wrongdoing, insider trading, or any improper conduct."
    )


def test_merge_every_signal_passes_the_validator():
    from aiinvest import conflict
    out = ec.build(_input_2025(), _input_2026(), conflict_doc=_conflict_doc())
    for t in out["trades"]:
        sig = t.get("conflict_signal")
        if sig is not None:
            conflict.validate_signal(sig)  # must not raise


def test_merge_enriches_by_politician():
    out = ec.build(_input_2025(), _input_2026(), conflict_doc=_conflict_doc())
    alice = next(p for p in out["by_politician"] if p["politician"] == "Alice Member")
    assert alice["committees"] == ["House Committee on Science, Space, and Technology"]
    assert alice["jurisdiction_sectors"] == ["Electronic Technology", "Technology Services"]
    # Carol (unmatched) gains no committees/jurisdiction keys
    carol = next(p for p in out["by_politician"] if p["politician"] == "Carol Member")
    assert "committees" not in carol
    assert "jurisdiction_sectors" not in carol


def test_merge_totals_gain_conflict_counts():
    out = ec.build(_input_2025(), _input_2026(), conflict_doc=_conflict_doc())
    tot = out["totals"]
    assert tot["n_conflict_flagged"] == 5
    # Alice + Bob are matched AND present in the trade set (Carol not in index).
    assert tot["n_politicians_matched"] == 2
    # legacy totals untouched
    assert tot["n_trades"] == 7


def test_merge_carries_curated_map_and_caveat():
    out = ec.build(_input_2025(), _input_2026(), conflict_doc=_conflict_doc())
    assert out["committee_sector_map"] == _MAP
    assert "APPROXIMATE" in out["committee_sector_map_note"]
    assert out["conflict_match_coverage"]["n_matched"] == 2


# --------------------------------------------------------------------------
# Member-profile overlay merge (party + ideology + policy areas + sponsored).
# When member_profiles.json is present, build(..., member_doc=...) merges it:
#   (a) by_politician gains `ideology` (object), `policy_areas` (string[]),
#       `sponsored` (object|null),
#   (b) totals gains `party_breakdown`, `n_with_ideology`, `bills_enabled`,
#   (c) top-level gains `ideology_note`, `committee_policy_map`,
#       `committee_policy_map_note`, `member_source`, `member_match_coverage`.
# Absent member_doc -> output is byte-for-byte the legacy shape (rails kept).
# --------------------------------------------------------------------------

_POLICY_MAP = [
    {"committee": "Energy and Commerce",
     "policy_areas": ["Energy", "Health", "Telecommunications"]},
    {"committee": "Science, Space, and Technology",
     "policy_areas": ["Science", "Technology"]},
]

_IDEOLOGY_NOTE = (
    "DW-NOMINATE 1st dimension is a statistical measure of roll-call voting "
    "patterns (Voteview/academic), not a personal judgment."
)


def _member_doc():
    """A member_profiles.json-shaped dict (spec 3.1) for the synthetic inputs.

    - Alice: Democrat, has ideology + policy areas + a sponsored summary.
    - Bob: Republican, ideology present, no sponsored (bills layer off for him).
    - Carol: NOT in the member index (unmatched) -> gains no enrichment.
    """
    return {
        "generated_at": "2026-06-01T00:00:00Z",
        "source": "voteview | legislators | committees | membership",
        "source_class": "api",
        "congress": 119,
        "disclaimer": "Educational. Not an accusation of wrongdoing against any individual.",
        "ideology_note": _IDEOLOGY_NOTE,
        "committee_policy_map": _POLICY_MAP,
        "committee_policy_map_note": "APPROXIMATE curated mapping of House committees to policy domains.",
        "bills_enabled": True,
        "match_coverage": {"n_politicians": 3, "n_matched": 2, "coverage_pct": 66.7,
                           "n_unmatched": 1, "unmatched": ["Carol Member"]},
        "by_politician": {
            "Alice Member": {
                "bioguide": "A000001",
                "party": "Democrat",
                "ideology": {"dim1": -0.31, "dim2": 0.12, "label": "Liberal", "position": 0.345},
                "committees": ["Science, Space, and Technology"],
                "policy_areas": ["Science", "Technology"],
                "sponsored": {"n": 2, "top_policy_areas": [{"area": "Science", "n": 2}],
                              "recent": [{"number": "1234", "type": "HR",
                                          "title": "A Science Bill", "policy_area": "Science",
                                          "introduced_date": "2025-03-04",
                                          "latest_action": "Referred to committee."}]},
            },
            "Bob Member": {
                "bioguide": "B000001",
                "party": "Republican",
                "ideology": {"dim1": 0.42, "dim2": -0.05, "label": "Conservative", "position": 0.71},
                "committees": ["Energy and Commerce"],
                "policy_areas": ["Energy", "Health", "Telecommunications"],
                "sponsored": None,
            },
        },
    }


def test_no_member_doc_keeps_legacy_shape():
    # Backward-compat: without a member_doc, by_politician/totals/top-level are
    # untouched (no ideology/policy_areas/sponsored, no new totals/top-level keys).
    out = ec.build(_input_2025(), _input_2026())
    assert all("ideology" not in p for p in out["by_politician"])
    assert all("policy_areas" not in p for p in out["by_politician"])
    assert all("sponsored" not in p for p in out["by_politician"])
    assert "party_breakdown" not in out["totals"]
    assert "n_with_ideology" not in out["totals"]
    assert "bills_enabled" not in out["totals"]
    assert "ideology_note" not in out
    assert "committee_policy_map" not in out
    assert "committee_policy_map_note" not in out
    assert "member_source" not in out
    assert "member_match_coverage" not in out


def test_member_doc_absent_is_byte_identical():
    """Passing member_doc=None must produce the exact same dict as omitting it."""
    import json as _json
    out_omitted = ec.build(_input_2025(), _input_2026())
    out_none = ec.build(_input_2025(), _input_2026(), member_doc=None)
    # generated_at differs by wall clock; normalize before comparison.
    out_omitted["generated_at"] = "X"
    out_none["generated_at"] = "X"
    assert _json.dumps(out_omitted, sort_keys=True) == _json.dumps(out_none, sort_keys=True)


def test_member_merge_enriches_by_politician():
    out = ec.build(_input_2025(), _input_2026(), member_doc=_member_doc())
    alice = next(p for p in out["by_politician"] if p["politician"] == "Alice Member")
    assert alice["ideology"] == {"dim1": -0.31, "dim2": 0.12, "label": "Liberal", "position": 0.345}
    assert alice["policy_areas"] == ["Science", "Technology"]
    assert alice["sponsored"]["n"] == 2
    bob = next(p for p in out["by_politician"] if p["politician"] == "Bob Member")
    assert bob["ideology"]["label"] == "Conservative"
    assert bob["policy_areas"] == ["Energy", "Health", "Telecommunications"]
    assert bob["sponsored"] is None
    # Carol (unmatched) gains no enrichment keys
    carol = next(p for p in out["by_politician"] if p["politician"] == "Carol Member")
    assert "ideology" not in carol
    assert "policy_areas" not in carol
    assert "sponsored" not in carol


def test_member_merge_backfills_null_party():
    """PTR trade rows carry no party; the member overlay must backfill the
    per-politician `party` (so the chip/filter work), without overwriting a
    party already present on the trade rows."""
    out = ec.build(_input_2025(), _input_2026(), member_doc=_member_doc())
    alice = next(p for p in out["by_politician"] if p["politician"] == "Alice Member")
    bob = next(p for p in out["by_politician"] if p["politician"] == "Bob Member")
    assert alice["party"] == "Democrat"
    assert bob["party"] == "Republican"
    # Unmatched member keeps whatever the trades carried (None here).
    carol = next(p for p in out["by_politician"] if p["politician"] == "Carol Member")
    assert carol["party"] is None


def test_member_merge_totals():
    out = ec.build(_input_2025(), _input_2026(), member_doc=_member_doc())
    tot = out["totals"]
    # party_breakdown counts politicians (by_politician rows) by party.
    # Alice=Democrat, Bob=Republican, Carol=unknown (no member entry, party None).
    assert tot["party_breakdown"] == {
        "Democrat": 1, "Republican": 1, "Independent": 0, "unknown": 1}
    assert tot["n_with_ideology"] == 2  # Alice + Bob
    assert tot["bills_enabled"] is True
    # legacy totals untouched
    assert tot["n_trades"] == 7


def test_member_merge_top_level_fields():
    out = ec.build(_input_2025(), _input_2026(), member_doc=_member_doc())
    assert out["ideology_note"] == _IDEOLOGY_NOTE
    assert out["committee_policy_map"] == _POLICY_MAP
    assert "APPROXIMATE" in out["committee_policy_map_note"]
    assert out["member_source"] == "voteview | legislators | committees | membership"
    assert out["member_match_coverage"]["n_matched"] == 2


def test_member_merge_no_banned_phrase_in_generated_top_level():
    # The banned phrase "fighting for" must never appear in the merged output's
    # generated descriptive fields.
    out = ec.build(_input_2025(), _input_2026(), member_doc=_member_doc())
    import json as _json
    blob = _json.dumps(out).lower()
    assert "fighting for" not in blob


def test_member_and_conflict_overlays_coexist():
    """Both overlays can merge into the same build without clobbering each other."""
    out = ec.build(_input_2025(), _input_2026(),
                   conflict_doc=_conflict_doc(), member_doc=_member_doc())
    alice = next(p for p in out["by_politician"] if p["politician"] == "Alice Member")
    # conflict overlay
    assert alice["jurisdiction_sectors"] == ["Electronic Technology", "Technology Services"]
    # member overlay
    assert alice["ideology"]["label"] == "Liberal"
    assert alice["policy_areas"] == ["Science", "Technology"]
    # totals carry both overlays' fields
    assert out["totals"]["n_conflict_flagged"] == 5
    assert out["totals"]["n_with_ideology"] == 2
