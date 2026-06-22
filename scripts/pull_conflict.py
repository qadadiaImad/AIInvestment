"""Pull the live 119th-Congress roster + committee membership -> a CORRELATIONAL
committee/sector overlap file (data/congress/conflict_signals.json).

REST-first per CLAUDE.md, Mode A (static HTTPS JSON assets, ungated). Pulls the
public, machine-readable @unitedstates/congress-legislators datasets:

    legislators-current.json              roster (bioguide, name, terms)
    committees-current.json               committee code -> official name
    committee-membership-current.json     committee code -> [members{bioguide}]

then, using aiinvest.conflict (PURE functions), resolves each politician seen in
the already-pulled PTR data to a bioguide, lists their committees, and computes
the set of sectors those committees have CURATED/APPROXIMATE jurisdiction over.

THE HIGHEST-RISK FEATURE IN THE REPO. Read the rails before touching this file.
The output is STRICTLY CORRELATIONAL. It states only two verifiable facts joined
by a stated heuristic: (1) the member FACTUALLY serves on Committee X (official
roster), and (2) the traded stock is in Sector Y, where Committee X has a curated
jurisdiction over Sector Y. It is NOT evidence of insider trading, influence,
benefit, or any wrongdoing. The committee_sector_map is clearly labelled
APPROXIMATE. No causal/accusatory language anywhere. certainty (applied later in
export_congress.py via aiinvest.conflict.build_conflict_signal) is hard-coded
'correlational' and validated.

Honesty rails (CLAUDE.md + LEGAL/HONESTY RAILS):
- Today is 2026-05-31; current Congress is the 119th (2025-2026).
- Amounts (downstream) remain reported range buckets; ~45-day lag; self-reported
  unverified filings. Educational/research only -- not investment advice; not an
  accusation of wrongdoing against any individual.
- If coverage is low, it is reported honestly -- never fabricated.

Output schema (data/congress/conflict_signals.json):
    {
      "generated_at": <UTC ISO-8601>,
      "source": <the three source URLs, joined>,
      "source_class": "filing",
      "match_coverage": {n_politicians, n_matched, coverage_pct, n_unmatched,
                         unmatched: [...]},
      "committee_sector_map": [ {committee, sectors:[...]} ],   # APPROXIMATE
      "committee_sector_map_note": "...approximate...",
      "by_politician": {
        <politician> -> {bioguide, committees:[...], jurisdiction_sectors:[...]}
      }
    }

Usage:
    python pull_conflict.py
    python pull_conflict.py --years 2025 2026
    python pull_conflict.py --out ../data
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib

import requests

from aiinvest import conflict

_UA = ("AIInvestment-research/1.0 (educational; data-acquisition; "
       "contact easyresumeai@outlook.fr)")

_BASE = "https://unitedstates.github.io/congress-legislators"
_LEGISLATORS_URL = f"{_BASE}/legislators-current.json"
_COMMITTEES_URL = f"{_BASE}/committees-current.json"
_MEMBERSHIP_URL = f"{_BASE}/committee-membership-current.json"

_DISCLAIMER = (
    "Educational/research only -- not investment advice. The committee/sector "
    "overlap is STRICTLY CORRELATIONAL: it joins two verifiable facts (a member "
    "serves on a committee; a traded stock is in a sector that committee has "
    "approximate jurisdiction over). It is NOT evidence of insider trading, "
    "influence, benefit, or any wrongdoing, and is not an accusation against any "
    "individual. The committee_sector_map below is a curated APPROXIMATION."
)

_MAP_NOTE = (
    "APPROXIMATE / curated heuristic mapping of House committees to TradingView "
    "sector labels. Committees with broad or cross-cutting jurisdiction (e.g. "
    "Ways and Means, Appropriations, Oversight, Rules) are intentionally omitted "
    "to avoid over-broad overlaps. Not a legal statement of jurisdiction."
)

# ---------------------------------------------------------------------------
# The curated, APPROXIMATE committee -> sector jurisdiction map.
# Keyed by SHORT committee name (after stripping "House Committee on ").
# Sector labels match the TradingView sector taxonomy used by the PTR pull.
# Deliberately conservative: only committees with a reasonably specific sector
# nexus are mapped; broad fiscal/procedural committees are left out.
# ---------------------------------------------------------------------------
COMMITTEE_SECTOR_MAP = [
    {"committee": "Financial Services", "sectors": ["Finance"]},
    {"committee": "Energy and Commerce",
     "sectors": ["Energy Minerals", "Utilities", "Health Technology",
                 "Health Services", "Communications", "Consumer Services"]},
    {"committee": "Natural Resources",
     "sectors": ["Energy Minerals", "Non-Energy Minerals"]},
    {"committee": "Transportation and Infrastructure",
     "sectors": ["Transportation", "Industrial Services"]},
    {"committee": "Science, Space, and Technology",
     "sectors": ["Technology Services", "Electronic Technology"]},
    {"committee": "Agriculture",
     "sectors": ["Process Industries", "Consumer Non-Durables"]},
    {"committee": "Armed Services",
     "sectors": ["Producer Manufacturing"]},
]


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


# ---------------------------------------------------------------------------
# Network layer (thin; matching/overlap lives in aiinvest.conflict)
# ---------------------------------------------------------------------------

def _get_json(url, session=None, timeout=60):
    http = session or requests
    resp = http.get(url, headers={"User-Agent": _UA}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_roster(session=None):
    """Fetch legislators-current.json -> roster the matcher understands.

    Each row: {bioguide, name{first,last,official_full,...}, current_term{...}}.
    current_term is the member's most recent term (the active one). House and
    Senate members are both included; the (state, district) matcher only resolves
    House reps, which is what the House PTR data contains.
    """
    raw = _get_json(_LEGISLATORS_URL, session=session)
    roster = []
    for m in raw:
        ident = m.get("id") or {}
        terms = m.get("terms") or []
        if not ident.get("bioguide") or not terms:
            continue
        roster.append({
            "bioguide": ident.get("bioguide"),
            "name": m.get("name") or {},
            "current_term": terms[-1],
        })
    return roster


def fetch_membership_linkage(session=None):
    """Build {bioguide -> [{committee_code, committee_name, title}]} (House only).

    Joins committee-membership-current.json (code -> [members{bioguide,title}])
    with committees-current.json (code -> {name, type}). Only House committees
    are kept, matching the House PTR universe.
    """
    committees = _get_json(_COMMITTEES_URL, session=session)
    code_to_name = {}
    for c in committees:
        if c.get("type") != "house":
            continue
        code = c.get("thomas_id")
        name = c.get("name")
        if code and name:
            code_to_name[code] = name

    membership = _get_json(_MEMBERSHIP_URL, session=session)
    linkage = {}
    for code, members in membership.items():
        name = code_to_name.get(code)
        if not name:
            continue  # not a (top-level) House committee
        for mem in members or []:
            bio = mem.get("bioguide")
            if not bio:
                continue
            linkage.setdefault(bio, []).append({
                "committee_code": code,
                "committee_name": name,
                "title": mem.get("title") or "",
            })
    return linkage


# ---------------------------------------------------------------------------
# Politicians seen in the already-pulled PTR data
# ---------------------------------------------------------------------------

def load_traded_politicians(out_root, years):
    """Read the pulled house_{year}.json files -> [{politician, state_dst}].

    The PTR trade rows carry the member display name and a state+district token
    (in the 'state' field, e.g. 'MO04'). De-duped, order-stable. Missing input
    files are skipped (reported by the caller via the returned count).
    """
    seen = {}
    for year in years:
        path = pathlib.Path(out_root) / "congress" / f"house_{year}.json"
        if not path.exists():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        for t in doc.get("trades", []):
            name = t.get("politician")
            if not name:
                continue
            # the PTR pull stores the state+district token in 'state'
            state_dst = t.get("state_dst") or t.get("state")
            if name not in seen:
                seen[name] = state_dst
    return [{"politician": n, "state_dst": sd} for n, sd in seen.items()]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Pull 119th-Congress roster+committees -> correlational "
                    "committee/sector overlap (Mode A, REST).")
    ap.add_argument("--years", type=int, nargs="+", default=[2025, 2026],
                    help="PTR years whose politicians to resolve (default 2025 2026).")
    ap.add_argument("--out", default=str(
        pathlib.Path(__file__).resolve().parent.parent / "data"),
        help="Data root directory (default: ../data).")
    args = ap.parse_args(argv)

    now = _utc_now()
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    session = requests.Session()

    print(f"Fetching roster + committee membership from {_BASE} ...")
    roster = fetch_roster(session=session)
    linkage = fetch_membership_linkage(session=session)
    print(f"  roster: {len(roster)} members; "
          f"{len(linkage)} members with House committee assignments.")

    politicians = load_traded_politicians(args.out, args.years)
    print(f"Resolving {len(politicians)} distinct PTR politicians "
          f"(years={args.years}) ...")

    by_politician = {}
    unmatched = []
    n_matched = 0
    for p in politicians:
        name = p["politician"]
        bioguide = conflict.match_member(name, p.get("state_dst"), roster)
        if bioguide is None:
            unmatched.append(name)
            continue
        n_matched += 1
        committees = conflict.member_committees(bioguide, linkage)
        sectors = sorted(conflict.committee_sector_overlap(
            committees, COMMITTEE_SECTOR_MAP))
        by_politician[name] = {
            "bioguide": bioguide,
            "committees": committees,
            "jurisdiction_sectors": sectors,
        }

    n_total = len(politicians)
    coverage_pct = round(100.0 * n_matched / n_total, 1) if n_total else 0.0

    out_dir = pathlib.Path(args.out) / "congress"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "conflict_signals.json"
    doc = {
        "generated_at": stamp,
        "source": " | ".join([_LEGISLATORS_URL, _COMMITTEES_URL, _MEMBERSHIP_URL]),
        "source_class": "filing",
        "congress": 119,
        "match_coverage": {
            "n_politicians": n_total,
            "n_matched": n_matched,
            "coverage_pct": coverage_pct,
            "n_unmatched": len(unmatched),
            "unmatched": sorted(unmatched),
        },
        "committee_sector_map": COMMITTEE_SECTOR_MAP,
        "committee_sector_map_note": _MAP_NOTE,
        "disclaimer": _DISCLAIMER,
        "by_politician": by_politician,
    }
    out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"  politicians={n_total} matched={n_matched} "
          f"coverage={coverage_pct}% unmatched={len(unmatched)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
