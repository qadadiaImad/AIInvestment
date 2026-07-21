"""Tests for the Python kit parser (aiinvest.kit_md), mirroring studio/src/main/kit.ts.

Parsed against the REAL higgs/reels_2026-06-27_kit.md so the carousel builder and the Studio
read the same authored kit. Unlike the Studio's display parser, this returns RAW field values
(inline HTML kept) because the carousel slides render HTML.
"""
import sys
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from aiinvest import kit_md  # noqa: E402

KIT = (_ROOT / "higgs" / "reels_2026-06-27_kit.md").read_text(encoding="utf-8")


def test_parse_cfg_team_core_fields():
    c = kit_md.parse_cfg(KIT, "TEAM")
    assert c is not None
    assert c["hero"] == "hero_software_2026-06-27.png"
    assert c["logo"] == "logo_TEAM.png"
    assert "AI APPLICATION" in c["ex"]
    assert c["src"] == "site"
    assert c["data"]["mode"] == "disc"
    assert c["data"]["rows"] == ["TEAM", "DUOL", "INTU", "ADBE", "WDAY"]
    assert c["takeaway"]["big"] == "72"
    assert c["takeaway"]["unit"] == "%"


def test_parse_cfg_keeps_raw_html_in_copy():
    c = kit_md.parse_cfg(KIT, "TEAM")
    # the carousel renders HTML, so <br>/<em> must survive (not be stripped)
    assert "<br>" in c["hook"]["head"]
    assert "<em" in c["hook"]["head"]
    assert "software" in c["hook"]["head"].lower()


def test_parse_cfg_quantum_mult_rows():
    c = kit_md.parse_cfg(KIT, "QBTS")
    assert c["src"] == "quantum"
    assert c["data"]["mode"] == "mult"
    assert c["data"]["rows"] == ["RGTI", "QBTS", "QUBT", "IONQ"]
    assert c["takeaway"]["big"] == "43"


def test_parse_cfg_absent_ticker_is_none():
    assert kit_md.parse_cfg(KIT, "NOPE") is None
    # congress section has no CFG block
    assert kit_md.parse_cfg(KIT, "CONGRESS") is None


def test_parse_congress_card():
    card = kit_md.parse_congress_card(KIT)
    assert card is not None
    assert card["name"] == "Rep. Nancy Pelosi"
    assert card["chips"] == ["NVDA", "GOOGL", "AMZN", "VST", "TEM"]
    assert card["big"] == "5"
    assert "not an accusation" in card["footer"]
    # meta rows present as (key, value) pairs
    meta = dict(card["meta"])
    assert any("Jan 16" in v for v in meta.values())
