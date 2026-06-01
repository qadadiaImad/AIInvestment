"""RED tests for member-profile enrichment (aiinvest.member_profile).

PURE FUNCTIONS ONLY — no network.

LEGAL/HONESTY RAILS (spec 2026-06-01-congress-enrichment-design.md §5):
- Educational/research only; NOT an accusation of wrongdoing against any individual.
- The phrase "fighting for" is BANNED in generated data + UI.
- Ideology = a statistical measure of roll-call voting patterns (Voteview
  DW-NOMINATE), explicitly labeled, NEVER a personal/character judgment.
- validate_profile reuses conflict.BANNED_WORDS, scanning GENERATED prose ONLY —
  it must NOT reject a banned substring that appears inside a verbatim
  public-record bill title (those are facts, not generated prose).
"""
import pytest

from aiinvest import member_profile as mp
from aiinvest import conflict


# Real Voteview H119_members.csv shape (verified live 2026-06-01). The first
# data row is the non-House President row (blank bioguide_id) which MUST be
# filtered out; House rows are keyed on bioguide_id.
SAMPLE_CSV = (
    "congress,chamber,icpsr,state_icpsr,district_code,state_abbrev,party_code,"
    "occupancy,last_means,bioname,bioguide_id,born,died,nominate_dim1,"
    "nominate_dim2,nominate_log_likelihood,nominate_geo_mean_probability,"
    "nominate_number_of_votes,nominate_number_of_errors,conditional,"
    "nokken_poole_dim1,nokken_poole_dim2\n"
    '119,President,99912,99,0,USA,200,0,0,"TRUMP, Donald John",,1946.0,,'
    "0.403,0.162,,,,,,,\n"
    '119,House,20301,41,3,AL,200,,,"ROGERS, Mike Dennis",R000575,1958.0,,'
    "0.379,0.377,-10.38159,0.97759,458,4,,0.369,0.399\n"
    '119,House,21102,41,7,AL,100,,,"SEWELL, Terri",S001185,1965.0,,'
    "-0.402,0.394,-31.92188,0.93282,459,16,,-0.382,0.348\n"
    # a House row with a blank bioguide_id -> must be skipped
    '119,House,99999,99,9,ZZ,328,,,"NOBODY, Test",,1900.0,,0.1,0.1,,,,,,,\n'
)


# --------------------------------------------------------------------------
# parse_dwnominate
# --------------------------------------------------------------------------

def test_parse_dwnominate_house_only_and_keys_on_bioguide():
    rows = mp.parse_dwnominate(SAMPLE_CSV)
    # President row filtered out (chamber != House); blank-bioguide House row skipped
    assert set(rows.keys()) == {"R000575", "S001185"}


def test_parse_dwnominate_extracts_dims_and_party_code():
    rows = mp.parse_dwnominate(SAMPLE_CSV)
    rogers = rows["R000575"]
    assert rogers["dim1"] == pytest.approx(0.379)
    assert rogers["dim2"] == pytest.approx(0.377)
    assert rogers["party_code"] == "200"


def test_parse_dwnominate_skips_president_row():
    rows = mp.parse_dwnominate(SAMPLE_CSV)
    # Trump's blank bioguide must never appear as a key
    assert "" not in rows
    assert None not in rows


# --------------------------------------------------------------------------
# ideology_label
# --------------------------------------------------------------------------

def test_ideology_label_liberal():
    assert mp.ideology_label(-0.402) == "Liberal"


def test_ideology_label_conservative():
    assert mp.ideology_label(0.379) == "Conservative"


def test_ideology_label_moderate():
    assert mp.ideology_label(0.0) == "Moderate"
    assert mp.ideology_label(-0.25) == "Moderate"
    assert mp.ideology_label(0.25) == "Moderate"


def test_ideology_label_none():
    assert mp.ideology_label(None) is None


# --------------------------------------------------------------------------
# ideology_position
# --------------------------------------------------------------------------

def test_ideology_position_midpoint():
    assert mp.ideology_position(0.0) == pytest.approx(0.5)


def test_ideology_position_clamped():
    assert mp.ideology_position(-3.0) == 0.0
    assert mp.ideology_position(3.0) == 1.0


def test_ideology_position_none():
    assert mp.ideology_position(None) is None


# --------------------------------------------------------------------------
# normalize_party
# --------------------------------------------------------------------------

def test_normalize_party_roster_strings():
    assert mp.normalize_party("Democrat") == "Democrat"
    assert mp.normalize_party("D") == "Democrat"
    assert mp.normalize_party("Republican") == "Republican"
    assert mp.normalize_party("R") == "Republican"
    assert mp.normalize_party("Independent") == "Independent"
    assert mp.normalize_party("I") == "Independent"


def test_normalize_party_dw_codes():
    assert mp.normalize_party("100") == "Democrat"
    assert mp.normalize_party(100) == "Democrat"
    assert mp.normalize_party("200") == "Republican"
    assert mp.normalize_party(200) == "Republican"
    assert mp.normalize_party("328") == "Independent"


def test_normalize_party_unknown_is_none():
    assert mp.normalize_party(None) is None
    assert mp.normalize_party("") is None
    assert mp.normalize_party("Whig") is None


# --------------------------------------------------------------------------
# committee_policy_areas
# --------------------------------------------------------------------------

def test_committee_policy_areas_sorted_unique():
    pm = [
        {"committee": "Energy and Commerce",
         "policy_areas": ["Energy", "Health", "Telecommunications"]},
        {"committee": "Financial Services", "policy_areas": ["Finance", "Health"]},
    ]
    out = mp.committee_policy_areas(
        ["House Committee on Energy and Commerce", "Financial Services"], pm)
    assert out == ["Energy", "Finance", "Health", "Telecommunications"]


def test_committee_policy_areas_unmapped_contributes_nothing():
    pm = [{"committee": "Agriculture", "policy_areas": ["Agriculture"]}]
    assert mp.committee_policy_areas(["House Committee on Rules"], pm) == []


# --------------------------------------------------------------------------
# summarize_sponsored
# --------------------------------------------------------------------------

def _bill(num, area, title="A bill", date="2025-01-01", action="Referred"):
    return {
        "number": num, "type": "HR", "title": title,
        "policy_area": area, "introduced_date": date, "latest_action": action,
    }


def test_summarize_sponsored_counts_and_top_areas():
    bills = [
        _bill("1", "Energy"), _bill("2", "Energy"),
        _bill("3", "Health"), _bill("4", "Energy"),
    ]
    s = mp.summarize_sponsored(bills)
    assert s["n"] == 4
    # Energy (3) before Health (1)
    assert s["top_policy_areas"][0] == {"area": "Energy", "n": 3}
    assert {"area": "Health", "n": 1} in s["top_policy_areas"]


def test_summarize_sponsored_caps_recent_at_top_n():
    bills = [_bill(str(i), "Energy") for i in range(20)]
    s = mp.summarize_sponsored(bills, top_n=5)
    assert len(s["recent"]) == 5


def test_summarize_sponsored_empty():
    s = mp.summarize_sponsored([])
    assert s["n"] == 0
    assert s["top_policy_areas"] == []
    assert s["recent"] == []


# --------------------------------------------------------------------------
# build_member_profile
# --------------------------------------------------------------------------

POLICY_MAP = [
    {"committee": "Energy and Commerce",
     "policy_areas": ["Energy", "Health", "Telecommunications"]},
]


def test_build_member_profile_shape():
    dwnom = {"dim1": -0.31, "dim2": 0.12, "party_code": "100"}
    prof = mp.build_member_profile(
        name="Doe, Jane", bioguide="A000370", party="Democrat",
        committees=["House Committee on Energy and Commerce"],
        dwnom_row=dwnom, policy_map=POLICY_MAP, sponsored=None)
    assert prof["bioguide"] == "A000370"
    assert prof["party"] == "Democrat"
    assert prof["ideology"]["dim1"] == pytest.approx(-0.31)
    assert prof["ideology"]["dim2"] == pytest.approx(0.12)
    assert prof["ideology"]["label"] == "Liberal"
    assert 0.0 <= prof["ideology"]["position"] <= 1.0
    assert prof["committees"] == ["House Committee on Energy and Commerce"]
    assert prof["policy_areas"] == ["Energy", "Health", "Telecommunications"]
    assert prof["sponsored"] is None


def test_build_member_profile_no_dwnom_null_ideology():
    prof = mp.build_member_profile(
        name="Doe, Jane", bioguide="A000370", party="Democrat",
        committees=[], dwnom_row=None, policy_map=POLICY_MAP, sponsored=None)
    assert prof["ideology"]["dim1"] is None
    assert prof["ideology"]["dim2"] is None
    assert prof["ideology"]["label"] is None
    assert prof["ideology"]["position"] is None


# --------------------------------------------------------------------------
# validate_profile — the hard rail
# --------------------------------------------------------------------------

def test_validate_profile_accepts_clean_profile():
    prof = mp.build_member_profile(
        name="Doe, Jane", bioguide="A000370", party="Republican",
        committees=["House Committee on Energy and Commerce"],
        dwnom_row={"dim1": 0.5, "dim2": 0.0, "party_code": "200"},
        policy_map=POLICY_MAP, sponsored=None)
    assert mp.validate_profile(prof) is True


def test_validate_profile_rejects_bad_label():
    prof = {
        "bioguide": "A000370", "party": "Democrat",
        "ideology": {"dim1": -0.1, "dim2": 0.0, "label": "Far-Left",
                     "position": 0.45},
        "committees": [], "policy_areas": [], "sponsored": None,
    }
    with pytest.raises(ValueError):
        mp.validate_profile(prof)


def test_validate_profile_rejects_bad_party():
    prof = {
        "bioguide": "A000370", "party": "Socialist",
        "ideology": {"dim1": None, "dim2": None, "label": None,
                     "position": None},
        "committees": [], "policy_areas": [], "sponsored": None,
    }
    with pytest.raises(ValueError):
        mp.validate_profile(prof)


def test_validate_profile_rejects_banned_word_in_generated_prose():
    # A banned causal word appears in a GENERATED policy-area string -> reject.
    banned = conflict.BANNED_WORDS[0]  # e.g. "because"
    prof = {
        "bioguide": "A000370", "party": "Democrat",
        "ideology": {"dim1": None, "dim2": None, "label": None,
                     "position": None},
        "committees": [],
        "policy_areas": [f"Energy {banned} reasons"],
        "sponsored": None,
    }
    with pytest.raises(ValueError):
        mp.validate_profile(prof)


def test_validate_profile_accepts_banned_substring_in_verbatim_bill_title():
    # "insider" is a BANNED_WORD, but here it sits inside a VERBATIM public-record
    # bill title — a fact, not generated prose. It MUST be accepted.
    assert "insider" in conflict.BANNED_WORDS
    prof = {
        "bioguide": "A000370", "party": "Democrat",
        "ideology": {"dim1": None, "dim2": None, "label": None,
                     "position": None},
        "committees": [], "policy_areas": [],
        "sponsored": {
            "n": 1,
            "top_policy_areas": [{"area": "Finance", "n": 1}],
            "recent": [{
                "number": "1", "type": "HR",
                "title": "To prohibit insider trading by Members of Congress",
                "policy_area": "Finance",
                "introduced_date": "2025-01-01",
                "latest_action": "Referred to committee",
            }],
        },
    }
    assert mp.validate_profile(prof) is True


# --------------------------------------------------------------------------
# COMMITTEE_POLICY_MAP constant
# --------------------------------------------------------------------------

def test_committee_policy_map_present_and_clean():
    assert isinstance(mp.COMMITTEE_POLICY_MAP, list)
    assert len(mp.COMMITTEE_POLICY_MAP) > 0
    names = {r["committee"] for r in mp.COMMITTEE_POLICY_MAP}
    # procedural/broad committees omitted per spec §4.1
    assert "Rules" not in names
    assert "Ethics" not in names
    assert "House Administration" not in names
    for row in mp.COMMITTEE_POLICY_MAP:
        assert isinstance(row["policy_areas"], list) and row["policy_areas"]
        # no banned/forbidden phrasing in the curated domains
        for area in row["policy_areas"]:
            assert "fighting for" not in area.lower()
            for banned in conflict.BANNED_WORDS:
                assert banned not in area.lower()
