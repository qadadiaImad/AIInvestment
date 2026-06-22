#!/usr/bin/env python
"""export_congress.py — merge House PTR years into web/public/data/congress.json.

Reads the already-pulled, date-stamped inputs:
    data/congress/house_2025.json
    data/congress/house_2026.json
and emits a single page-ready file at:
    web/public/data/congress.json

Honesty rails (CLAUDE.md):
- House amounts are RANGE BUCKETS (low/high); we NEVER collapse to one number.
- "est_volume" sums are explicitly LOW/HIGH BOUNDS, not point estimates.
- The disclaimer is carried verbatim from the inputs and must keep both honesty
  clauses ("not investment advice" + "Not an accusation of wrongdoing...").
- null-sector trades are kept in `trades` but excluded from `by_sector`.

Conflict-overlay merge (OPTIONAL — only when data/congress/conflict_signals.json
exists). THE HIGHEST-RISK FEATURE — strictly CORRELATIONAL:
- Each trade whose member has CURATED committee jurisdiction over that trade's
  sector gains a `conflict_signal` object (certainty 'correlational' + the
  matching committee(s) + the exact required rationale, built and VALIDATED by
  aiinvest.conflict.build_conflict_signal).
- by_politician entries gain `committees` + `jurisdiction_sectors`.
- totals gains `n_conflict_flagged` + `n_politicians_matched`.
- It is NOT evidence of insider trading, influence, benefit, or any wrongdoing.

Pure functions (build/merge/aggregate) are import-safe and have no side effects;
`main()` does the I/O.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
from collections import OrderedDict

from aiinvest import conflict as _conflict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
IN_DIR = os.path.join(REPO, "data", "congress")
OUT_PATH = os.path.join(REPO, "web", "public", "data", "congress.json")
CONFLICT_PATH = os.path.join(IN_DIR, "conflict_signals.json")
MEMBER_PATH = os.path.join(IN_DIR, "member_profiles.json")

# transaction-type buckets
_BUY = {"P"}
_SELL = {"S", "S (partial)"}

# essential per-trade fields kept in the output (bound the file size)
_ESSENTIAL = (
    "politician", "state", "party", "year", "ticker", "sector", "asset",
    "txn_type", "txn_date", "filing_date", "reporting_lag_days",
    "amount_range_low", "amount_range_high", "source",
)


def _utc_now_iso():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_us_date(s):
    """Parse a US-style date string (M/D/YYYY or MM/DD/YYYY) -> date, or None."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return _dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _is_buy(txn_type):
    return txn_type in _BUY


def _is_sell(txn_type):
    return txn_type in _SELL


def _year_of(trade, fallback):
    """Derive the calendar year of a trade from its txn_date, else fallback."""
    d = _parse_us_date(trade.get("txn_date"))
    if d is not None:
        return d.year
    return fallback


def _slim_trade(trade, year):
    """Project a raw trade onto the essential output fields (+derived year)."""
    return {
        "politician": trade.get("politician"),
        "state": trade.get("state") or trade.get("state_dst"),
        "party": trade.get("party"),
        "year": year,
        "ticker": trade.get("ticker"),
        "sector": trade.get("sector") if trade.get("sector") not in ("",) else None,
        "asset": trade.get("asset"),
        "txn_type": trade.get("txn_type"),
        "txn_date": trade.get("txn_date"),
        "filing_date": trade.get("filing_date"),
        "reporting_lag_days": trade.get("reporting_lag_days"),
        "amount_range_low": trade.get("amount_range_low"),
        "amount_range_high": trade.get("amount_range_high"),
        "source": trade.get("source"),
    }


def merge_trades(*inputs):
    """Slim + concatenate trades from each input, de-duping identical rows."""
    seen = set()
    out = []
    for inp in inputs:
        fallback_year = (inp.get("provenance") or {}).get("year")
        for raw in inp.get("trades", []):
            year = _year_of(raw, fallback_year)
            slim = _slim_trade(raw, year)
            # de-dup on the full essential tuple
            key = tuple(slim.get(k) for k in _ESSENTIAL)
            if key in seen:
                continue
            seen.add(key)
            out.append(slim)
    return out


# ---------------------------------------------------------------------------
# Conflict overlay (OPTIONAL) — strictly correlational committee/sector overlap.
# All signal construction/validation is delegated to aiinvest.conflict so the
# hard honesty rails (certainty == 'correlational', exact rationale template,
# banned-word scan) are enforced in one audited place.
# ---------------------------------------------------------------------------

def _conflict_index(conflict_doc):
    """Map politician-name -> {bioguide, committees, jurisdiction_sectors}.

    None / empty doc -> {} (overlay simply absent). Reads the by_politician block
    written by pull_conflict.py.
    """
    if not conflict_doc:
        return {}
    return dict(conflict_doc.get("by_politician") or {})


def attach_conflict_signals(trades, conflict_doc):
    """Mutate `trades` in place: add a `conflict_signal` to each trade whose
    member has curated committee jurisdiction over that trade's sector.

    Returns (n_trades_flagged, set_of_flagged_politicians). The signal is built
    AND validated by aiinvest.conflict.build_conflict_signal; a trade with no
    overlap (or an unmatched member) is left untouched (no `conflict_signal`).
    """
    index = _conflict_index(conflict_doc)
    cmap = (conflict_doc or {}).get("committee_sector_map") or []
    n_flagged = 0
    flagged_pols = set()
    for t in trades:
        name = t.get("politician")
        entry = index.get(name)
        if not entry:
            continue
        committees = entry.get("committees") or []
        sig = _conflict.build_conflict_signal(t, committees, cmap)
        if sig is not None:
            t["conflict_signal"] = sig
            n_flagged += 1
            flagged_pols.add(name)
    return n_flagged, flagged_pols


# ---------------------------------------------------------------------------
# Member-profile overlay (OPTIONAL) — party + ideology (Voteview DW-NOMINATE) +
# policy areas (committee jurisdiction / public record). Strictly additive and
# descriptive; mirrors the conflict-overlay merge. Ideology is a statistical
# measure of voting patterns, NOT a personal judgment; no inference of motive.
# ---------------------------------------------------------------------------

def _member_index(member_doc):
    """Map politician-name -> {bioguide, party, ideology, policy_areas, sponsored}.

    None / empty doc -> {} (overlay simply absent). Reads the by_politician block
    written by pull_member_profiles.py (spec 3.1).
    """
    if not member_doc:
        return {}
    return dict(member_doc.get("by_politician") or {})


def _amount_low(t):
    v = t.get("amount_range_low")
    return v if isinstance(v, (int, float)) else 0


def _amount_high(t):
    v = t.get("amount_range_high")
    return v if isinstance(v, (int, float)) else 0


def aggregate_by_politician(trades, conflict_doc=None, member_doc=None):
    index = _conflict_index(conflict_doc)
    member_index = _member_index(member_doc)
    acc = OrderedDict()
    for t in trades:
        name = t.get("politician")
        a = acc.get(name)
        if a is None:
            a = {
                "politician": name,
                "state": t.get("state"),
                "party": t.get("party"),
                "n_trades": 0,
                "n_buys": 0,
                "n_sells": 0,
                "est_volume_low": 0,
                "est_volume_high": 0,
                "_sectors": {},
                "_last": None,
            }
            acc[name] = a
        a["n_trades"] += 1
        if _is_buy(t["txn_type"]):
            a["n_buys"] += 1
        elif _is_sell(t["txn_type"]):
            a["n_sells"] += 1
        a["est_volume_low"] += _amount_low(t)
        a["est_volume_high"] += _amount_high(t)
        sec = t.get("sector")
        if sec not in (None, ""):
            a["_sectors"][sec] = a["_sectors"].get(sec, 0) + 1
        d = _parse_us_date(t.get("txn_date"))
        if d is not None and (a["_last"] is None or d > a["_last"][0]):
            a["_last"] = (d, t.get("txn_date"))

    out = []
    for a in acc.values():
        top = sorted(a["_sectors"].items(), key=lambda kv: (-kv[1], kv[0]))[:3]
        row = {
            "politician": a["politician"],
            "state": a["state"],
            "party": a["party"],
            "n_trades": a["n_trades"],
            "n_buys": a["n_buys"],
            "n_sells": a["n_sells"],
            "est_volume_low": a["est_volume_low"],
            "est_volume_high": a["est_volume_high"],
            "top_sectors": [{"sector": s, "n": n} for s, n in top],
            "last_trade_date": a["_last"][1] if a["_last"] else None,
        }
        # conflict overlay: surface the member's (correlational) committees +
        # the sectors those committees have curated jurisdiction over.
        entry = index.get(a["politician"])
        if entry is not None:
            row["committees"] = list(entry.get("committees") or [])
            row["jurisdiction_sectors"] = list(entry.get("jurisdiction_sectors") or [])
        # member-profile overlay: surface the member's party, ideology (a
        # statistical measure of voting patterns, not a judgment), policy areas
        # (committee jurisdiction / public record), and sponsored-legislation
        # summary. Strictly additive — unmatched members gain no keys.
        m = member_index.get(a["politician"])
        if m is not None:
            # PTR trade rows carry no party; backfill from the roster/Voteview
            # member profile, but never overwrite a party already on the trades.
            if not row.get("party") and m.get("party"):
                row["party"] = m.get("party")
            row["ideology"] = m.get("ideology")
            row["policy_areas"] = list(m.get("policy_areas") or [])
            row["sponsored"] = m.get("sponsored")
        out.append(row)
    out.sort(key=lambda p: (-p["est_volume_high"], p["politician"]))
    return out


def aggregate_by_sector(trades):
    """Aggregate non-null sectors only (null-sector rows stay in `trades`)."""
    acc = OrderedDict()
    for t in trades:
        sec = t.get("sector")
        if sec in (None, ""):
            continue
        a = acc.get(sec)
        if a is None:
            a = {
                "sector": sec,
                "n_trades": 0,
                "n_buys": 0,
                "n_sells": 0,
                "est_volume_low": 0,
                "est_volume_high": 0,
                "_pols": set(),
            }
            acc[sec] = a
        a["n_trades"] += 1
        if _is_buy(t["txn_type"]):
            a["n_buys"] += 1
        elif _is_sell(t["txn_type"]):
            a["n_sells"] += 1
        a["est_volume_low"] += _amount_low(t)
        a["est_volume_high"] += _amount_high(t)
        a["_pols"].add(t.get("politician"))

    out = []
    for a in acc.values():
        out.append({
            "sector": a["sector"],
            "n_trades": a["n_trades"],
            "n_buys": a["n_buys"],
            "n_sells": a["n_sells"],
            "est_volume_low": a["est_volume_low"],
            "est_volume_high": a["est_volume_high"],
            "n_politicians": len(a["_pols"]),
        })
    out.sort(key=lambda s: (-s["est_volume_high"], s["sector"]))
    return out


def compute_totals(trades, inputs, conflict_doc=None, member_doc=None):
    dates = [_parse_us_date(t.get("txn_date")) for t in trades]
    dates = [d for d in dates if d is not None]
    sectors = {t.get("sector") for t in trades if t.get("sector") not in (None, "")}
    n_skipped = 0
    for inp in inputs:
        prov = inp.get("provenance") or {}
        v = prov.get("scanned_skipped")
        if isinstance(v, (int, float)):
            n_skipped += int(v)
    totals = {
        "n_trades": len(trades),
        "n_politicians": len({t.get("politician") for t in trades}),
        "n_tickers": len({t.get("ticker") for t in trades if t.get("ticker")}),
        "n_sectors": len(sectors),
        "date_min": min(dates).isoformat() if dates else None,
        "date_max": max(dates).isoformat() if dates else None,
        "n_scanned_skipped": n_skipped,
        "est_volume_low": sum(_amount_low(t) for t in trades),
        "est_volume_high": sum(_amount_high(t) for t in trades),
    }
    if conflict_doc is not None:
        # n_conflict_flagged: trades carrying a (correlational) conflict_signal.
        # n_politicians_matched: traded members resolved to a roster bioguide
        # AND present in this trade set.
        index = _conflict_index(conflict_doc)
        traded = {t.get("politician") for t in trades}
        totals["n_conflict_flagged"] = sum(
            1 for t in trades if t.get("conflict_signal") is not None)
        totals["n_politicians_matched"] = len(
            traded & set(index.keys()))
    if member_doc is not None:
        # party_breakdown: count traded politicians by their (roster/Voteview)
        # party; members with no profile entry are 'unknown' (never fabricated).
        # n_with_ideology: traded members carrying an ideology object.
        # bills_enabled: whether the sponsored-legislation layer was populated.
        member_index = _member_index(member_doc)
        breakdown = {"Democrat": 0, "Republican": 0, "Independent": 0, "unknown": 0}
        n_with_ideology = 0
        for name in {t.get("politician") for t in trades}:
            m = member_index.get(name)
            party = (m or {}).get("party")
            if party in breakdown:
                breakdown[party] += 1
            else:
                breakdown["unknown"] += 1
            if m is not None and m.get("ideology") is not None:
                n_with_ideology += 1
        totals["party_breakdown"] = breakdown
        totals["n_with_ideology"] = n_with_ideology
        totals["bills_enabled"] = bool(member_doc.get("bills_enabled"))
    return totals


def _carry_disclaimer(*inputs):
    for inp in inputs:
        d = (inp.get("provenance") or {}).get("disclaimer")
        if d:
            return d
    return ""


def _carry_source(*inputs):
    srcs = []
    for inp in inputs:
        s = (inp.get("provenance") or {}).get("source")
        if s:
            srcs.append(s)
    return " | ".join(srcs) if srcs else "https://disclosures-clerk.house.gov/"


def build(*inputs, conflict_doc=None, member_doc=None):
    """Pure: merge inputs into the page-ready congress.json dict.

    When ``conflict_doc`` (the parsed conflict_signals.json) is supplied, the
    strictly-correlational committee/sector overlay is merged in: per-trade
    `conflict_signal`, by_politician `committees`/`jurisdiction_sectors`, and
    totals `n_conflict_flagged`/`n_politicians_matched`. Absent -> unchanged.

    When ``member_doc`` (the parsed member_profiles.json) is supplied, the
    additive member-profile overlay is merged in: by_politician gains `ideology`
    (a statistical measure of voting patterns, not a judgment), `policy_areas`
    (committee jurisdiction / public record), and `sponsored`; totals gains
    `party_breakdown`/`n_with_ideology`/`bills_enabled`; the top level gains
    `ideology_note`/`committee_policy_map`/`committee_policy_map_note`/
    `member_source`/`member_match_coverage`. Absent -> unchanged.
    """
    trades = merge_trades(*inputs)
    if conflict_doc is not None:
        attach_conflict_signals(trades, conflict_doc)
    out = {
        "generated_at": _utc_now_iso(),
        "source": _carry_source(*inputs),
        "source_class": "filing",
        "disclaimer": _carry_disclaimer(*inputs),
        "totals": compute_totals(trades, inputs, conflict_doc=conflict_doc,
                                 member_doc=member_doc),
        "by_politician": aggregate_by_politician(trades, conflict_doc=conflict_doc,
                                                 member_doc=member_doc),
        "by_sector": aggregate_by_sector(trades),
        "trades": trades,
    }
    if conflict_doc is not None:
        # surface the curated map + its provenance/caveat for the page.
        out["committee_sector_map"] = conflict_doc.get("committee_sector_map") or []
        out["committee_sector_map_note"] = conflict_doc.get("committee_sector_map_note")
        out["conflict_source"] = conflict_doc.get("source")
        out["conflict_match_coverage"] = conflict_doc.get("match_coverage")
    if member_doc is not None:
        # surface the ideology note + curated committee->policy map (APPROXIMATE,
        # public-record jurisdiction) + provenance/coverage for the page.
        out["ideology_note"] = member_doc.get("ideology_note")
        out["committee_policy_map"] = member_doc.get("committee_policy_map") or []
        out["committee_policy_map_note"] = member_doc.get("committee_policy_map_note")
        out["member_source"] = member_doc.get("source")
        out["member_match_coverage"] = member_doc.get("match_coverage")
    return out


def _load_conflict_doc():
    """Read data/congress/conflict_signals.json if present, else None."""
    if not os.path.exists(CONFLICT_PATH):
        return None
    with open(CONFLICT_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _load_member_doc():
    """Read data/congress/member_profiles.json if present, else None."""
    if not os.path.exists(MEMBER_PATH):
        return None
    with open(MEMBER_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    inputs = []
    for year in (2025, 2026):
        path = os.path.join(IN_DIR, f"house_{year}.json")
        with open(path, encoding="utf-8") as fh:
            inputs.append(json.load(fh))
    conflict_doc = _load_conflict_doc()
    member_doc = _load_member_doc()
    out = build(*inputs, conflict_doc=conflict_doc, member_doc=member_doc)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(OUT_PATH)
    print(f"wrote {OUT_PATH}")
    print(f"trades={out['totals']['n_trades']} bytes={size}")
    if conflict_doc is None:
        print("conflict overlay: ABSENT (conflict_signals.json not found)")
    else:
        print(f"conflict overlay: MERGED "
              f"(n_conflict_flagged={out['totals'].get('n_conflict_flagged')} "
              f"n_politicians_matched={out['totals'].get('n_politicians_matched')})")
    if member_doc is None:
        print("member overlay: ABSENT (member_profiles.json not found)")
    else:
        print(f"member overlay: MERGED "
              f"(n_with_ideology={out['totals'].get('n_with_ideology')} "
              f"bills_enabled={out['totals'].get('bills_enabled')} "
              f"party_breakdown={out['totals'].get('party_breakdown')})")
    print("totals=" + json.dumps(out["totals"]))
    print("sample by_politician=" + json.dumps(out["by_politician"][:2]))
    print("sample by_sector=" + json.dumps(out["by_sector"][:2]))


if __name__ == "__main__":
    main()
