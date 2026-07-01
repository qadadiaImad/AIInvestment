"""Tests for the kit-driven carousel builder (higgs/_build_v4.py).

build_slides is the pure assembly step: kit md + bundle stocks -> {filename: html}. No
Playwright, no file reads here (hero/logo maps are injected). Importing _build_v4 must be
side-effect-free (no render on import).
"""
import sys
import json
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_HIGGS = _ROOT / "higgs"
if str(_HIGGS) not in sys.path:
    sys.path.insert(0, str(_HIGGS))
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

import _build_v4 as bv  # noqa: E402  (must import without rendering)

KIT = (_HIGGS / "reels_2026-06-27_kit.md").read_text(encoding="utf-8")
SITE = json.loads((_ROOT / "web" / "public" / "data" / "site.json").read_text(encoding="utf-8"))["stocks"]
QUANT = json.loads((_ROOT / "web" / "public" / "data" / "quantum.json").read_text(encoding="utf-8"))["stocks"]


def _slides():
    return bv.build_slides(KIT, SITE, QUANT, hero_map={}, logo_map={}, date="2026-06-27")


def test_build_slides_emits_expected_filenames():
    sl = _slides()
    for name in ("v4_team_1_hook.png", "v4_team_2_data.png", "v4_team_3_takeaway.png",
                 "v4_qbts_1_hook.png", "v4_qbts_2_data.png", "v4_qbts_3_takeaway.png",
                 "v4_cong_1_hook.png", "v4_cong_2_card.png", "v4_cong_3_takeaway.png"):
        assert name in sl, f"missing {name}"
        assert sl[name].lstrip().lower().startswith("<!doctype"), f"{name} not full HTML"


def test_team_hook_and_takeaway_carry_kit_copy():
    sl = _slides()
    assert "software" in sl["v4_team_1_hook.png"].lower()
    # takeaway big from the kit ("72%")
    assert "72" in sl["v4_team_3_takeaway.png"]


def test_team_data_slide_fills_rows_from_bundle():
    sl = _slides()
    html = sl["v4_team_2_data.png"]
    # row labels are the kit tickers; values are filled from site.json discount %
    for tk in ("TEAM", "DUOL", "INTU", "ADBE", "WDAY"):
        assert tk in html


def test_quantum_data_slide_uses_mult_rows():
    sl = _slides()
    html = sl["v4_qbts_2_data.png"]
    for tk in ("RGTI", "QBTS", "QUBT", "IONQ"):
        assert tk in html
    assert "x" in html  # multiple labels like "18.2x"


def test_congress_card_uses_pelosi_from_kit():
    sl = _slides()
    assert "Pelosi" in sl["v4_cong_2_card.png"]
    for tk in ("NVDA", "GOOGL", "AMZN", "VST", "TEM"):
        assert tk in sl["v4_cong_2_card.png"]


def test_missing_hero_does_not_crash_uses_fallback():
    # hero_map empty -> no background image url, but slides still render
    sl = _slides()
    assert "v4_team_1_hook.png" in sl  # built despite no hero art


def test_pick_kit_selects_newest(tmp_path):
    (tmp_path / "reels_2026-06-22_kit.md").write_text("old", encoding="utf-8")
    (tmp_path / "reels_2026-06-27_kit.md").write_text("new", encoding="utf-8")
    (tmp_path / "reels_2026-06-23_kit.md").write_text("mid", encoding="utf-8")
    assert bv.pick_kit(tmp_path).name == "reels_2026-06-27_kit.md"
