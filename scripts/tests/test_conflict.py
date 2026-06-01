"""RED tests for the committee/sector conflict-overlap signal (aiinvest.conflict).

PURE FUNCTIONS ONLY — no network.

LEGAL/HONESTY RAILS (highest-risk feature in the repo):
- The signal is STRICTLY CORRELATIONAL. It joins exactly two verifiable facts:
  (1) the member factually serves on Committee X (official roster), and
  (2) the traded stock is in Sector Y, where Committee X has a curated/approximate
  jurisdiction over Sector Y.
- certainty is HARD-CODED to the single allowed value 'correlational'.
- BANNED: any causal/accusatory language anywhere (because, insider, corrupt, ...).
- Required rationale template (no other phrasing):
  "Serves on the {committee} Committee, which has jurisdiction over the {sector}
   sector. This is a correlational overlap only — not evidence of wrongdoing,
   insider trading, or any improper conduct."
- A validator MUST reject any signal whose rationale deviates or whose
  certainty != 'correlational'. Called inside build_conflict_signal.
"""
import json
import os

import pytest

from aiinvest import conflict

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "congress")


def _read_json(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return json.load(fh)


# The curated jurisdiction map (recon JURISDICTION MAP), keyed by short committee
# name as it appears after stripping the "House Committee on " prefix.
JURISDICTION_MAP = [
    {"committee": "Financial Services", "sectors": ["Finance"]},
    {"committee": "Energy and Commerce",
     "sectors": ["Energy Minerals", "Utilities", "Health Technology",
                 "Communications", "Consumer Services"]},
    {"committee": "Natural Resources",
     "sectors": ["Energy Minerals", "Non-Energy Minerals"]},
    {"committee": "Transportation and Infrastructure",
     "sectors": ["Transportation", "Industrial Services"]},
    {"committee": "Science, Space, and Technology",
     "sectors": ["Technology Services", "Electronic Technology"]},
    {"committee": "Agriculture",
     "sectors": ["Process Industries", "Consumer Non-Durables"]},
]


# --------------------------------------------------------------------------
# normalize_name(s)
# --------------------------------------------------------------------------

def test_normalize_name_lowercases_and_collapses_whitespace():
    assert conflict.normalize_name("  Nancy   Pelosi ") == "nancy pelosi"


def test_normalize_name_strips_punctuation_and_titles_noise():
    # commas/periods removed so "Donald S. Beyer, Jr." normalizes cleanly
    assert conflict.normalize_name("Donald S. Beyer, Jr.") == "donald s beyer jr"


def test_normalize_name_none_returns_empty():
    assert conflict.normalize_name(None) == ""


# --------------------------------------------------------------------------
# match_member(name, state_dst, roster) -> bioguide | None
# --------------------------------------------------------------------------

def _roster():
    # roster-slice.json is a list of {bioguide, name{}, current_term{state,district}}
    return _read_json("roster-slice.json")


def test_match_member_by_state_district_primary_key():
    roster = _roster()
    # Terri A. Sewell, AL-07 -> S001185
    assert conflict.match_member("Terri A. Sewell", "AL07", roster) == "S001185"


def test_match_member_state_district_wins_even_if_name_differs():
    roster = _roster()
    # state+district is the primary key; a slightly different display name
    # must still resolve via AR02 -> H001072 (J. French Hill).
    assert conflict.match_member("James French Hill", "AR02", roster) == "H001072"


def test_match_member_at_large_district_00_maps_to_01():
    roster = _roster()
    # at-large fallback: DC00 should match a rep stored with district 0/1.
    # Eleanor Holmes Norton is N000147 at DC00.
    assert conflict.match_member("Eleanor Holmes Norton", "DC00", roster) == "N000147"


def test_match_member_name_fallback_when_state_dst_missing():
    roster = _roster()
    # No state_dst -> fall back to unique normalized name.
    assert conflict.match_member("Robert B. Aderholt", None, roster) == "A000055"


def test_match_member_unmatched_returns_none():
    roster = _roster()
    assert conflict.match_member("Nobody McNobody", "ZZ99", roster) is None


# --------------------------------------------------------------------------
# member_committees(bioguide, membership) -> [committee names]
# --------------------------------------------------------------------------

def _linkage():
    return _read_json("member-committee-linkage.json")


def test_member_committees_returns_committee_names():
    linkage = _linkage()
    # H001072 (J. French Hill): Intelligence + Financial Services (Chair)
    names = conflict.member_committees("H001072", linkage)
    assert "House Committee on Financial Services" in names
    assert "House Permanent Select Committee on Intelligence" in names


def test_member_committees_unknown_bioguide_returns_empty():
    assert conflict.member_committees("Z999999", _linkage()) == []


# --------------------------------------------------------------------------
# committee_sector_overlap(committees, committee_sector_map) -> set of sectors
# --------------------------------------------------------------------------

def test_committee_sector_overlap_financial_services_to_finance():
    overlap = conflict.committee_sector_overlap(
        ["House Committee on Financial Services"], JURISDICTION_MAP)
    assert overlap == {"Finance"}


def test_committee_sector_overlap_unmapped_committee_yields_nothing():
    # Ways and Means is deliberately unmapped (too broad).
    overlap = conflict.committee_sector_overlap(
        ["House Committee on Ways and Means"], JURISDICTION_MAP)
    assert overlap == set()


def test_committee_sector_overlap_unions_multiple_committees():
    overlap = conflict.committee_sector_overlap(
        ["House Committee on Financial Services",
         "House Committee on Science, Space, and Technology"],
        JURISDICTION_MAP)
    assert overlap == {"Finance", "Technology Services", "Electronic Technology"}


# --------------------------------------------------------------------------
# build_conflict_signal(trade, committees, committee_sector_map) -> signal|None
# --------------------------------------------------------------------------

def test_build_signal_financial_services_member_trading_finance():
    committees = ["House Committee on Financial Services"]
    trade = {"sector": "Finance", "ticker": "JPM"}
    sig = conflict.build_conflict_signal(trade, committees, JURISDICTION_MAP)
    assert sig is not None
    assert sig["certainty"] == "correlational"
    assert sig["sector"] == "Finance"
    assert sig["committees"] == ["Financial Services"]
    assert sig["rationale"] == (
        "Serves on the Financial Services Committee, which has jurisdiction over "
        "the Finance sector. This is a correlational overlap only — not evidence "
        "of wrongdoing, insider trading, or any improper conduct."
    )


def test_build_signal_returns_none_when_sector_not_in_overlap():
    committees = ["House Committee on Financial Services"]
    trade = {"sector": "Utilities", "ticker": "NEE"}
    assert conflict.build_conflict_signal(trade, committees, JURISDICTION_MAP) is None


def test_build_signal_returns_none_for_member_with_no_mapped_committee():
    committees = ["House Committee on Ways and Means"]
    trade = {"sector": "Finance", "ticker": "JPM"}
    assert conflict.build_conflict_signal(trade, committees, JURISDICTION_MAP) is None


def test_build_signal_lists_only_the_matching_committee():
    # member sits on two mapped committees but trade only overlaps one
    committees = ["House Committee on Financial Services",
                  "House Committee on Science, Space, and Technology"]
    trade = {"sector": "Finance"}
    sig = conflict.build_conflict_signal(trade, committees, JURISDICTION_MAP)
    assert sig["committees"] == ["Financial Services"]
    assert "Financial Services Committee" in sig["rationale"]
    # only one committee named in the rationale
    assert "Science" not in sig["rationale"]


def test_build_signal_realistic_case_from_fixtures():
    # J. French Hill (H001072) chairs Financial Services; trade a Finance stock.
    linkage = _linkage()
    committees = conflict.member_committees("H001072", linkage)
    trade = {"sector": "Finance", "ticker": "GS"}
    sig = conflict.build_conflict_signal(trade, committees, JURISDICTION_MAP)
    assert sig is not None
    assert sig["certainty"] == "correlational"
    assert sig["committees"] == ["Financial Services"]


def test_build_signal_passes_validator():
    committees = ["House Committee on Financial Services"]
    trade = {"sector": "Finance"}
    sig = conflict.build_conflict_signal(trade, committees, JURISDICTION_MAP)
    # must not raise
    conflict.validate_signal(sig)


# --------------------------------------------------------------------------
# validate_signal(sig) -> raises on deviation
# --------------------------------------------------------------------------

def _good_signal():
    return {
        "certainty": "correlational",
        "sector": "Finance",
        "committees": ["Financial Services"],
        "rationale": (
            "Serves on the Financial Services Committee, which has jurisdiction "
            "over the Finance sector. This is a correlational overlap only — not "
            "evidence of wrongdoing, insider trading, or any improper conduct."
        ),
    }


def test_validate_signal_accepts_good_signal():
    conflict.validate_signal(_good_signal())  # no raise


def test_validate_signal_rejects_wrong_certainty():
    sig = _good_signal()
    sig["certainty"] = "causal"
    with pytest.raises(ValueError):
        conflict.validate_signal(sig)


def test_validate_signal_rejects_deviant_rationale():
    sig = _good_signal()
    sig["rationale"] = "Serves on Financial Services and trades Finance stocks."
    with pytest.raises(ValueError):
        conflict.validate_signal(sig)


@pytest.mark.parametrize("banned", [
    "because", "due to", "used", "exploited", "profited",
    "insider", "corrupt", "benefited from", "influence-peddling",
])
def test_validate_signal_rejects_banned_causal_words(banned):
    sig = _good_signal()
    # Inject a banned word while keeping it superficially template-like.
    sig["rationale"] = (
        "Serves on the Financial Services Committee, which has jurisdiction over "
        f"the Finance sector. The member {banned} their position."
    )
    with pytest.raises(ValueError):
        conflict.validate_signal(sig)


def test_validate_signal_rejects_missing_certainty():
    sig = _good_signal()
    del sig["certainty"]
    with pytest.raises(ValueError):
        conflict.validate_signal(sig)
