"""Committee/sector conflict-overlap signal — PURE FUNCTIONS, NO NETWORK.

THE HIGHEST-RISK FEATURE IN THE REPO. Read the rails before touching this file.

What this is (and is NOT):
- The signal is STRICTLY CORRELATIONAL. It joins exactly two verifiable facts:
    (1) a member FACTUALLY serves on Committee X (from official roster data), and
    (2) the traded stock is in Sector Y, where Committee X has a curated/approximate
        jurisdiction over Sector Y (a heuristic mapping, not a legal one).
- It is NOT, and must never be presented as, evidence of insider trading, corruption,
  influence, wrongdoing, or any improper conduct. The overlap is correlational only.

Hard rails enforced in code:
- ``certainty`` is HARD-CODED to the single allowed value ``'correlational'``.
- The rationale MUST match the exact template (filled braces only):
    "Serves on the {committee} Committee, which has jurisdiction over the {sector}
     sector. This is a correlational overlap only — not evidence of wrongdoing,
     insider trading, or any improper conduct."
- ``validate_signal`` rejects any signal whose certainty != 'correlational', whose
  rationale deviates from the template, or whose rationale contains any banned
  causal/accusatory word. It is called inside ``build_conflict_signal``.

Caveats carried by every downstream consumer: amounts are reported range buckets;
~45-day disclosure lag; self-reported, unverified filings. Educational/research
only — not investment advice, not evidence of any wrongdoing.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Constants: the single allowed certainty + the exact rationale template.
# ---------------------------------------------------------------------------
CERTAINTY = "correlational"

# NOTE: the em dash (—) is intentional and load-bearing — the template must match
# byte-for-byte after brace substitution.
RATIONALE_TEMPLATE = (
    "Serves on the {committee} Committee, which has jurisdiction over the "
    "{sector} sector. This is a correlational overlap only — not evidence of "
    "wrongdoing, insider trading, or any improper conduct."
)

# Words/phrases that imply causation, benefit, or wrongdoing. The fixed template
# legitimately contains "wrongdoing", "insider trading", and "evidence"; the
# validator checks rationales ONLY by exact-template equality plus this banned
# scan applied to any deviation, so these never produce false positives on the
# canonical string.
BANNED_WORDS = (
    "because",
    "due to",
    "used",
    "exploited",
    "profited",
    "insider trading",  # only legitimate inside the fixed template phrasing
    "insider",
    "corrupt",
    "benefited from",
    "benefitted from",
    "influence-peddling",
    "influence peddling",
    "conflict of interest",
    "took advantage",
    "leveraged",
    "front-ran",
    "front ran",
    "tipped off",
)

_COMMITTEE_PREFIX_RE = re.compile(
    r"^House\s+(?:Permanent\s+Select\s+|Select\s+)?Committee\s+on\s+(?:the\s+)?",
    re.IGNORECASE,
)


def _short_committee(name):
    """Strip the 'House Committee on ' (and select-committee) prefix.

    Returns the bare subject name used as the key into the jurisdiction map and
    in the rationale, e.g. 'House Committee on Financial Services' ->
    'Financial Services'.
    """
    if name is None:
        return ""
    return _COMMITTEE_PREFIX_RE.sub("", str(name)).strip()


# ---------------------------------------------------------------------------
# normalize_name
# ---------------------------------------------------------------------------

def normalize_name(s):
    """Lowercase, strip punctuation, collapse whitespace. None -> ''."""
    if s is None:
        return ""
    s = str(s).lower()
    s = re.sub(r"[.,]", " ", s)          # drop periods/commas
    s = re.sub(r"[^a-z0-9 ]", " ", s)    # drop any other punctuation
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ---------------------------------------------------------------------------
# match_member
# ---------------------------------------------------------------------------

_STATE_DST_RE = re.compile(r"^([A-Z]{2})(\d{1,2})$")


def _roster_state_dst(member):
    term = member.get("current_term") or {}
    state = term.get("state")
    district = term.get("district")
    if state is None or district is None:
        return None
    return state, int(district)


def match_member(name, state_dst, roster):
    """Resolve a member to a bioguide id.

    Primary key: (state, district) parsed from ``state_dst`` (e.g. 'AL07').
    At-large fallback: district 00 <-> 01. Name fallback: unique normalized
    full/official name when state_dst is missing or unmatched. Returns the
    bioguide string or None.
    """
    # --- primary: state + district ---
    if state_dst:
        m = _STATE_DST_RE.match(str(state_dst).strip().upper())
        if m:
            state = m.group(1)
            district = int(m.group(2))
            # exact match
            for member in roster:
                sd = _roster_state_dst(member)
                if sd == (state, district):
                    return member.get("bioguide")
            # at-large fallback: 00 <-> 01
            if district in (0, 1):
                alt = 1 if district == 0 else 0
                for member in roster:
                    sd = _roster_state_dst(member)
                    if sd == (state, alt):
                        return member.get("bioguide")

    # --- fallback: unique normalized name ---
    target = normalize_name(name)
    if not target:
        return None
    matches = []
    for member in roster:
        nm = member.get("name") or {}
        candidates = {
            normalize_name(nm.get("official_full")),
            normalize_name(
                " ".join(x for x in [nm.get("first"), nm.get("last")] if x)
            ),
        }
        candidates.discard("")
        if target in candidates:
            matches.append(member.get("bioguide"))
    if len(set(matches)) == 1:
        return matches[0]
    return None


# ---------------------------------------------------------------------------
# member_committees
# ---------------------------------------------------------------------------

def member_committees(bioguide, membership):
    """Return the list of full committee names a member serves on.

    ``membership`` is the bioguide -> [{committee_code, committee_name, title}]
    linkage. Unknown bioguide -> []. Preserves order, de-dupes.
    """
    entries = membership.get(bioguide) or []
    names = []
    for e in entries:
        cn = e.get("committee_name")
        if cn and cn not in names:
            names.append(cn)
    return names


# ---------------------------------------------------------------------------
# committee_sector_overlap
# ---------------------------------------------------------------------------

def _map_lookup(committee_sector_map):
    """Build short-committee-name -> set(sectors) from the curated map."""
    lookup = {}
    for row in committee_sector_map:
        key = _short_committee(row.get("committee"))
        lookup.setdefault(key, set()).update(row.get("sectors") or [])
    return lookup


def committee_sector_overlap(committees, committee_sector_map):
    """Set of sectors the member has curated jurisdiction over.

    ``committees`` may be full names ('House Committee on Financial Services')
    or already-short names ('Financial Services'); both resolve. Unmapped
    committees contribute nothing.
    """
    lookup = _map_lookup(committee_sector_map)
    out = set()
    for c in committees:
        short = _short_committee(c)
        if short in lookup:
            out |= lookup[short]
    return out


# ---------------------------------------------------------------------------
# build_conflict_signal
# ---------------------------------------------------------------------------

def build_conflict_signal(trade, committees, committee_sector_map):
    """Build a correlational overlap signal, or None.

    Returns a signal ONLY if ``trade['sector']`` falls within the member's
    curated jurisdiction overlap. The signal lists ONLY the committee(s) whose
    jurisdiction actually covers the traded sector. certainty is hard-coded
    'correlational' and the rationale uses the exact required template. The
    signal is validated before return (validate_signal raises on any deviation).
    """
    sector = (trade or {}).get("sector")
    if not sector:
        return None

    lookup = _map_lookup(committee_sector_map)

    # find the matching committee(s): those whose jurisdiction covers `sector`.
    matching = []
    for c in committees:
        short = _short_committee(c)
        if short in lookup and sector in lookup[short]:
            if short not in matching:
                matching.append(short)

    if not matching:
        return None

    # rationale names the matching committee(s); join with ' and ' if several.
    committee_phrase = " and ".join(matching)
    rationale = RATIONALE_TEMPLATE.format(committee=committee_phrase, sector=sector)

    signal = {
        "certainty": CERTAINTY,
        "sector": sector,
        "committees": matching,
        "rationale": rationale,
    }
    validate_signal(signal)
    return signal


# ---------------------------------------------------------------------------
# validate_signal — the hard rail
# ---------------------------------------------------------------------------

def _allowed_rationales_for(signal):
    """Every rationale string that is legitimate for this signal's fields.

    A valid rationale is the template filled with the signal's own sector and a
    committee phrase made from its own committees list (single or ' and '-joined).
    """
    sector = signal.get("sector")
    committees = signal.get("committees") or []
    phrases = set()
    if committees:
        phrases.add(" and ".join(committees))
    allowed = set()
    for phrase in phrases:
        allowed.add(RATIONALE_TEMPLATE.format(committee=phrase, sector=sector))
    return allowed


def validate_signal(signal):
    """Raise ValueError unless the signal obeys every honesty rail.

    Checks: certainty == 'correlational'; rationale exactly equals the template
    filled from the signal's own committees+sector; rationale contains no banned
    causal/accusatory word beyond the fixed template phrasing.
    """
    if not isinstance(signal, dict):
        raise ValueError("signal must be a dict")

    if signal.get("certainty") != CERTAINTY:
        raise ValueError(
            f"certainty must be {CERTAINTY!r}, got {signal.get('certainty')!r}"
        )

    rationale = signal.get("rationale")
    if not rationale:
        raise ValueError("signal missing rationale")

    allowed = _allowed_rationales_for(signal)
    if rationale not in allowed:
        raise ValueError(
            "rationale deviates from the required template: " + repr(rationale)
        )

    # Defense in depth: even though exact-match already constrains the string,
    # scan for banned words OUTSIDE the fixed template tail. The only legitimate
    # occurrences of 'wrongdoing'/'insider trading' are inside the template's
    # fixed closing sentence; the variable head (committee + sector) must be clean.
    head = rationale.split("This is a correlational overlap only", 1)[0].lower()
    for banned in BANNED_WORDS:
        if banned in head:
            raise ValueError(f"banned causal/accusatory term in rationale: {banned!r}")

    return True
