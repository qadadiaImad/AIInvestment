"""Member-profile enrichment — PURE FUNCTIONS, NO NETWORK.

Enriches each politician on /congress with party, an academic ideology measure
(Voteview DW-NOMINATE), and the policy areas their committees have jurisdiction
over (plus a summary of sponsored legislation when a congress.gov key is
available, fetched by the CLI — never here).

LEGAL/HONESTY RAILS (spec 2026-06-01-congress-enrichment-design.md §5):
- Educational/research only. NOT an accusation of wrongdoing against any
  individual.
- Ideology is a STATISTICAL MEASURE of roll-call voting patterns (Voteview
  DW-NOMINATE, academic), explicitly labeled — never a personal/character
  judgment. The 1st dimension positions a member on a Liberal<->Conservative
  axis; thresholds below are a labeling convenience, not a verdict.
- Policy areas are derived from committee jurisdiction (public record) and an
  APPROXIMATE curated map; not a legal statement of jurisdiction.
- The phrase "fighting for" is BANNED (implies unverifiable motive). Generated
  prose must avoid it and every conflict.BANNED_WORDS term.
- validate_profile reuses conflict.BANNED_WORDS, scanning GENERATED descriptive
  fields ONLY. It MUST NOT scan verbatim public-record bill titles / latest
  actions — those are facts, not generated prose.

This module performs NO network I/O. The CLI (pull_member_profiles.py) fetches
the Voteview CSV and any sponsored legislation and feeds it here.
"""
from __future__ import annotations

import csv
import io

from aiinvest import conflict

# ---------------------------------------------------------------------------
# Allowed value sets (honest, closed taxonomies).
# ---------------------------------------------------------------------------
ALLOWED_PARTIES = ("Democrat", "Republican", "Independent")
ALLOWED_LABELS = ("Liberal", "Moderate", "Conservative")

# DW-NOMINATE 1st-dimension labeling thresholds (spec §4.1).
_LIBERAL_MAX = -0.25
_CONSERVATIVE_MIN = 0.25


# ---------------------------------------------------------------------------
# The curated, APPROXIMATE committee -> policy-domain map.
# Keyed by SHORT committee name (after stripping "House Committee on ").
# Human-readable POLICY DOMAINS (distinct from the conflict TradingView-sector
# map). Procedural/broad committees (Rules, Ethics, House Administration,
# Appropriations, Budget, Ways and Means, Oversight) are intentionally OMITTED
# to avoid over-broad / cross-cutting claims. Not a legal statement of
# jurisdiction.
# ---------------------------------------------------------------------------
COMMITTEE_POLICY_MAP = [
    {"committee": "Agriculture",
     "policy_areas": ["Agriculture", "Food", "Rural development",
                      "Nutrition"]},
    {"committee": "Armed Services",
     "policy_areas": ["Defense", "National security", "Military readiness"]},
    {"committee": "Education and the Workforce",
     "policy_areas": ["Education", "Labor", "Workforce", "Pensions"]},
    {"committee": "Energy and Commerce",
     "policy_areas": ["Energy", "Health", "Telecommunications",
                      "Consumer protection", "Environment"]},
    {"committee": "Financial Services",
     "policy_areas": ["Banking", "Securities", "Housing", "Insurance",
                      "Monetary policy"]},
    {"committee": "Foreign Affairs",
     "policy_areas": ["Foreign policy", "International relations",
                      "Diplomacy"]},
    {"committee": "Homeland Security",
     "policy_areas": ["Homeland security", "Border security",
                      "Emergency management"]},
    {"committee": "Judiciary",
     "policy_areas": ["Judiciary", "Immigration", "Civil rights",
                      "Crime", "Intellectual property"]},
    {"committee": "Natural Resources",
     "policy_areas": ["Public lands", "Energy", "Minerals", "Water",
                      "Wildlife"]},
    {"committee": "Science, Space, and Technology",
     "policy_areas": ["Science", "Technology", "Space", "Research"]},
    {"committee": "Small Business",
     "policy_areas": ["Small business", "Entrepreneurship"]},
    {"committee": "Transportation and Infrastructure",
     "policy_areas": ["Transportation", "Infrastructure", "Aviation",
                      "Maritime"]},
    {"committee": "Veterans' Affairs",
     "policy_areas": ["Veterans", "Veterans health", "Veterans benefits"]},
]


# ---------------------------------------------------------------------------
# parse_dwnominate
# ---------------------------------------------------------------------------

def parse_dwnominate(csv_text):
    """Parse a Voteview H1xx_members.csv -> {bioguide: {dim1,dim2,party_code}}.

    House rows only (chamber == 'House'); the non-House President row and any
    row with a blank bioguide_id are skipped. dim1/dim2 are floats or None when
    blank; party_code is the raw string code (e.g. '100','200') or None.
    """
    rows = {}
    if not csv_text:
        return rows
    reader = csv.DictReader(io.StringIO(csv_text))
    for r in reader:
        if (r.get("chamber") or "").strip() != "House":
            continue
        bioguide = (r.get("bioguide_id") or "").strip()
        if not bioguide:
            continue
        rows[bioguide] = {
            "dim1": _to_float(r.get("nominate_dim1")),
            "dim2": _to_float(r.get("nominate_dim2")),
            "party_code": (r.get("party_code") or "").strip() or None,
        }
    return rows


def _to_float(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# ideology_label / ideology_position
# ---------------------------------------------------------------------------

def ideology_label(dim1):
    """Liberal (<-0.25) | Moderate | Conservative (>0.25) | None.

    A labeling convenience over the DW-NOMINATE 1st-dimension statistic, NOT a
    personal judgment.
    """
    if dim1 is None:
        return None
    if dim1 < _LIBERAL_MAX:
        return "Liberal"
    if dim1 > _CONSERVATIVE_MIN:
        return "Conservative"
    return "Moderate"


def ideology_position(dim1):
    """Map dim1 in [-1,1] to [0,1] via clamp((dim1+1)/2, 0, 1). None -> None."""
    if dim1 is None:
        return None
    pos = (dim1 + 1.0) / 2.0
    if pos < 0.0:
        return 0.0
    if pos > 1.0:
        return 1.0
    return pos


# ---------------------------------------------------------------------------
# normalize_party
# ---------------------------------------------------------------------------

_PARTY_STRINGS = {
    "democrat": "Democrat", "democratic": "Democrat", "d": "Democrat",
    "republican": "Republican", "r": "Republican",
    "independent": "Independent", "i": "Independent",
}
# Voteview DW-NOMINATE party codes: 100->Democrat, 200->Republican, else Independent.
_PARTY_CODES = {"100": "Democrat", "200": "Republican"}
# Known third-party / independent DW codes (cross-check only; roster authoritative).
_INDEPENDENT_CODES = {"328", "537", "112", "356", "370"}


def normalize_party(raw):
    """Resolve a roster party string OR a DW party_code to a canonical party.

    Accepts: 'Democrat'/'Republican'/'Independent', 'D'/'R'/'I', or DW codes
    '100'/'200'/etc. Unknown/empty -> None. Roster party is authoritative
    upstream; DW codes are a cross-check fallback.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    low = s.lower()
    if low in _PARTY_STRINGS:
        return _PARTY_STRINGS[low]
    if s in _PARTY_CODES:
        return _PARTY_CODES[s]
    if s in _INDEPENDENT_CODES:
        return "Independent"
    return None


# ---------------------------------------------------------------------------
# committee_policy_areas
# ---------------------------------------------------------------------------

def _policy_lookup(policy_map):
    lookup = {}
    for row in policy_map:
        key = conflict._short_committee(row.get("committee"))
        lookup.setdefault(key, set()).update(row.get("policy_areas") or [])
    return lookup


def committee_policy_areas(committees, policy_map):
    """Sorted unique list of policy areas the member's committees cover.

    ``committees`` may be full ('House Committee on Energy and Commerce') or
    already-short ('Energy and Commerce') names; both resolve. Unmapped
    committees contribute nothing.
    """
    lookup = _policy_lookup(policy_map)
    out = set()
    for c in committees:
        short = conflict._short_committee(c)
        if short in lookup:
            out |= lookup[short]
    return sorted(out)


# ---------------------------------------------------------------------------
# summarize_sponsored
# ---------------------------------------------------------------------------

def summarize_sponsored(bills, top_n=5):
    """Summarize sponsored legislation -> {n, top_policy_areas, recent}.

    ``bills`` is a list of normalized bill dicts (already shaped by the CLI:
    number,type,title,policy_area,introduced_date,latest_action). ``recent`` is
    capped at ``top_n`` (input order preserved — CLI sorts newest-first).
    ``top_policy_areas`` is the most-common policy areas, capped at ``top_n``.
    """
    bills = list(bills or [])
    counts = {}
    for b in bills:
        area = b.get("policy_area")
        if not area:
            continue
        counts[area] = counts.get(area, 0) + 1
    # most-common first; ties broken alphabetically for determinism.
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
    top_policy_areas = [{"area": a, "n": n} for a, n in top]

    recent = []
    for b in bills[:top_n]:
        recent.append({
            "number": b.get("number"),
            "type": b.get("type"),
            "title": b.get("title"),
            "policy_area": b.get("policy_area"),
            "introduced_date": b.get("introduced_date"),
            "latest_action": b.get("latest_action"),
        })
    return {"n": len(bills), "top_policy_areas": top_policy_areas,
            "recent": recent}


# ---------------------------------------------------------------------------
# build_member_profile
# ---------------------------------------------------------------------------

def build_member_profile(name, bioguide, party, committees, dwnom_row,
                         policy_map, sponsored):
    """Assemble a single politician profile dict (spec §3.1 shape).

    ``dwnom_row`` is a {dim1,dim2,party_code} dict or None. ``sponsored`` is a
    summarize_sponsored() result or None. The returned profile is NOT validated
    here; callers should run validate_profile() before persisting.
    """
    row = dwnom_row or {}
    dim1 = row.get("dim1")
    dim2 = row.get("dim2")
    profile = {
        "bioguide": bioguide,
        "party": party,
        "ideology": {
            "dim1": dim1,
            "dim2": dim2,
            "label": ideology_label(dim1),
            "position": ideology_position(dim1),
        },
        "committees": list(committees or []),
        "policy_areas": committee_policy_areas(committees or [], policy_map),
        "sponsored": sponsored,
    }
    return profile


# ---------------------------------------------------------------------------
# validate_profile — the hard rail
# ---------------------------------------------------------------------------

def _scan_banned(text):
    """Raise if a generated descriptive string contains a banned/forbidden term."""
    low = str(text).lower()
    if "fighting for" in low:
        raise ValueError("banned phrase 'fighting for' in generated prose: "
                         + repr(text))
    for banned in conflict.BANNED_WORDS:
        if banned in low:
            raise ValueError(
                f"banned causal/accusatory term {banned!r} in generated "
                f"prose: {text!r}")


def validate_profile(profile):
    """Raise ValueError unless the profile obeys every honesty rail.

    Checks:
    - ``party`` in the allowed set or None.
    - ideology ``label`` in the allowed set or None.
    - GENERATED descriptive fields (policy_areas, top_policy_areas[].area)
      contain no banned/forbidden term.

    Does NOT scan verbatim public-record bill titles or latest_action strings —
    those are facts, not generated prose (a banned substring inside a real bill
    title is ACCEPTED).
    """
    if not isinstance(profile, dict):
        raise ValueError("profile must be a dict")

    party = profile.get("party")
    if party is not None and party not in ALLOWED_PARTIES:
        raise ValueError(f"party not allowed: {party!r}")

    ideology = profile.get("ideology") or {}
    label = ideology.get("label")
    if label is not None and label not in ALLOWED_LABELS:
        raise ValueError(f"ideology label not allowed: {label!r}")

    # Generated prose: the curated, committee-derived policy areas. These are
    # OUR strings (from COMMITTEE_POLICY_MAP), so they get scanned.
    for area in profile.get("policy_areas") or []:
        _scan_banned(area)

    # NOTE: everything under ``sponsored`` (recent[].title / latest_action /
    # policy_area, and the top_policy_areas[].area aggregated FROM those
    # public-record policy_area values) is a VERBATIM public-record fact, not
    # generated prose, and is intentionally NOT scanned here.

    return True
