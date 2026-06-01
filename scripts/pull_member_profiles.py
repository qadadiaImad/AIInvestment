"""Pull member-profile enrichment for /congress politicians -> a profiles file
(data/congress/member_profiles.json). REST-first, Mode A (public/academic JSON
and CSV assets, ungated).

Enriches every politician seen in the already-pulled PTR data with:
  - party / state / district / bioguide  (legislators-current.json, reused via
    pull_conflict.fetch_roster)
  - ideology   (Voteview DW-NOMINATE H119_members.csv — a STATISTICAL MEASURE of
    roll-call voting patterns, academic; never a personal judgment)
  - policy areas (committee jurisdiction, public record, via
    pull_conflict.fetch_membership_linkage + aiinvest.member_profile's curated
    APPROXIMATE COMMITTEE_POLICY_MAP)
  - sponsored legislation (public record) ONLY when CONGRESS_GOV_API_KEY is set
    in the environment; otherwise sponsored=null and bills_enabled=false.

LEGAL/HONESTY RAILS (spec 2026-06-01-congress-enrichment-design.md §5):
- Educational/research only -- not investment advice. NOT an accusation of
  wrongdoing against any individual.
- Ideology is an academic measurement of voting patterns (Voteview), explicitly
  labeled -- never a character judgment. The phrase "fighting for" is banned;
  fields are "Policy areas (committee jurisdiction)" and "Sponsored legislation
  (public record)."
- Coverage is reported honestly; values are never fabricated (null when absent).
- This script runs cleanly with NO key present (sponsored=null,
  bills_enabled=false).

Usage:
    python pull_member_profiles.py
    python pull_member_profiles.py --years 2025 2026
    python pull_member_profiles.py --out ../data --delay 0.5
    python pull_member_profiles.py --limit-members 10        # debug
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import time

import requests

from aiinvest import conflict, member_profile
import pull_conflict

_UA = ("AIInvestment-research/1.0 (educational; data-acquisition; "
       "contact easyresumeai@outlook.fr)")

_VOTEVIEW_URL = "https://voteview.com/static/data/out/members/H119_members.csv"
_CONGRESS_GOV_BASE = "https://api.congress.gov/v3"

_DISCLAIMER = (
    "Educational/research only -- not investment advice. This is NOT an "
    "accusation of wrongdoing against any individual. Ideology is a statistical "
    "measure of roll-call voting patterns (Voteview DW-NOMINATE, academic), not "
    "a personal judgment. Policy areas are derived from committee jurisdiction "
    "(public record) via a curated APPROXIMATE mapping; sponsored legislation, "
    "when shown, is verbatim public record."
)

_IDEOLOGY_NOTE = (
    "DW-NOMINATE 1st dimension is a statistical measure of roll-call voting "
    "patterns (Voteview/academic), not a personal judgment."
)

_MAP_NOTE = (
    "APPROXIMATE curated mapping of House committees to policy domains; not a "
    "legal statement of jurisdiction. Procedural/broad committees (Rules, "
    "Ethics, House Administration, Appropriations, Budget, Ways and Means, "
    "Oversight) are intentionally omitted."
)


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


# ---------------------------------------------------------------------------
# Network layer (thin; pure logic lives in aiinvest.member_profile)
# ---------------------------------------------------------------------------

def fetch_dwnominate(session=None, timeout=60):
    """Fetch the Voteview H119 members CSV -> {bioguide: {dim1,dim2,party_code}}."""
    http = session or requests
    resp = http.get(_VOTEVIEW_URL, headers={"User-Agent": _UA}, timeout=timeout)
    resp.raise_for_status()
    return member_profile.parse_dwnominate(resp.text)


def fetch_sponsored(bioguide, api_key, session=None, timeout=60, top_n=5):
    """Fetch sponsored legislation for one member from congress.gov.

    Returns a list of normalized bill dicts (newest first). Network/parse errors
    or an empty record yield an empty list (caller summarizes). Titles and
    latest actions are kept VERBATIM (public record).
    """
    http = session or requests
    url = f"{_CONGRESS_GOV_BASE}/member/{bioguide}/sponsored-legislation"
    params = {"api_key": api_key, "format": "json", "limit": 50}
    try:
        resp = http.get(url, params=params, headers={"User-Agent": _UA},
                        timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError):
        return []

    raw = payload.get("sponsoredLegislation") or []
    bills = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        latest = item.get("latestAction") or {}
        policy = item.get("policyArea") or {}
        bills.append({
            "number": item.get("number"),
            "type": item.get("type"),
            "title": item.get("title"),
            "policy_area": policy.get("name"),
            "introduced_date": item.get("introducedDate"),
            "latest_action": latest.get("text"),
            # internal sort key only; not emitted
            "_sort": item.get("introducedDate") or "",
        })
    # newest first by introduced date; summarize_sponsored caps recent at top_n.
    bills.sort(key=lambda b: b.get("_sort") or "", reverse=True)
    for b in bills:
        b.pop("_sort", None)
    return bills


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Pull member-profile enrichment (party, Voteview ideology, "
                    "committee policy areas; sponsored bills if a key is set) "
                    "for /congress politicians (Mode A, REST).")
    ap.add_argument("--years", type=int, nargs="+", default=[2025, 2026],
                    help="PTR years whose politicians to resolve (default 2025 2026).")
    ap.add_argument("--out", default=str(
        pathlib.Path(__file__).resolve().parent.parent / "data"),
        help="Data root directory (default: ../data).")
    ap.add_argument("--delay", type=float, default=0.5,
                    help="Polite delay (s) between sponsored-legislation calls.")
    ap.add_argument("--limit-members", type=int, default=None,
                    help="Debug: cap the number of matched members processed.")
    args = ap.parse_args(argv)

    now = _utc_now()
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    session = requests.Session()

    api_key = os.environ.get("CONGRESS_GOV_API_KEY")
    bills_enabled = bool(api_key)

    print(f"Fetching roster + committee membership from "
          f"{pull_conflict._BASE} ...")
    roster = pull_conflict.fetch_roster(session=session)
    linkage = pull_conflict.fetch_membership_linkage(session=session)
    print(f"  roster: {len(roster)} members; "
          f"{len(linkage)} members with House committee assignments.")

    print(f"Fetching Voteview DW-NOMINATE from {_VOTEVIEW_URL} ...")
    dwnom = fetch_dwnominate(session=session)
    print(f"  ideology rows (House, keyed on bioguide): {len(dwnom)}")

    # Roster party lookup (authoritative over DW party_code).
    roster_party = {}
    for m in roster:
        term = m.get("current_term") or {}
        bio = m.get("bioguide")
        if bio:
            roster_party[bio] = term.get("party")

    politicians = pull_conflict.load_traded_politicians(args.out, args.years)
    print(f"Resolving {len(politicians)} distinct PTR politicians "
          f"(years={args.years}) ...")
    if bills_enabled:
        print("  CONGRESS_GOV_API_KEY present -> sponsored-legislation layer ON.")
    else:
        print("  No CONGRESS_GOV_API_KEY -> sponsored=null, bills_enabled=false.")

    by_politician = {}
    unmatched = []
    n_matched = 0
    processed = 0
    for p in politicians:
        name = p["politician"]
        bioguide = conflict.match_member(name, p.get("state_dst"), roster)
        if bioguide is None:
            unmatched.append(name)
            continue
        n_matched += 1
        if args.limit_members is not None and processed >= args.limit_members:
            continue
        processed += 1

        committees = conflict.member_committees(bioguide, linkage)
        # roster party authoritative; fall back to DW party_code.
        dwnom_row = dwnom.get(bioguide)
        party = member_profile.normalize_party(roster_party.get(bioguide))
        if party is None and dwnom_row is not None:
            party = member_profile.normalize_party(dwnom_row.get("party_code"))

        sponsored = None
        if bills_enabled:
            bills = fetch_sponsored(bioguide, api_key, session=session)
            sponsored = member_profile.summarize_sponsored(bills)
            if args.delay:
                time.sleep(args.delay)

        profile = member_profile.build_member_profile(
            name=name, bioguide=bioguide, party=party, committees=committees,
            dwnom_row=dwnom_row, policy_map=member_profile.COMMITTEE_POLICY_MAP,
            sponsored=sponsored)
        member_profile.validate_profile(profile)
        by_politician[name] = profile

    n_total = len(politicians)
    coverage_pct = round(100.0 * n_matched / n_total, 1) if n_total else 0.0

    source_parts = [_VOTEVIEW_URL, pull_conflict._LEGISLATORS_URL,
                    pull_conflict._COMMITTEES_URL, pull_conflict._MEMBERSHIP_URL]
    if bills_enabled:
        source_parts.append(_CONGRESS_GOV_BASE + "/member/{bioguide}/"
                            "sponsored-legislation")

    out_dir = pathlib.Path(args.out) / "congress"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "member_profiles.json"
    doc = {
        "generated_at": stamp,
        "source": " | ".join(source_parts),
        "source_class": "api",
        "congress": 119,
        "disclaimer": _DISCLAIMER,
        "ideology_note": _IDEOLOGY_NOTE,
        "committee_policy_map": member_profile.COMMITTEE_POLICY_MAP,
        "committee_policy_map_note": _MAP_NOTE,
        "bills_enabled": bills_enabled,
        "match_coverage": {
            "n_politicians": n_total,
            "n_matched": n_matched,
            "coverage_pct": coverage_pct,
            "n_unmatched": len(unmatched),
            "unmatched": sorted(unmatched),
        },
        "by_politician": by_politician,
    }
    out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"  politicians={n_total} matched={n_matched} "
          f"coverage={coverage_pct}% unmatched={len(unmatched)} "
          f"bills_enabled={bills_enabled}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
