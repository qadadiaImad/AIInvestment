"""Tests for the kit-driven carousel builder (higgs/_build_v4.py).

build_slides is the pure assembly step: kit md + bundle stocks -> {filename: html}. No
Playwright, no file reads here (hero/logo maps are injected). Importing _build_v4 must be
side-effect-free (no render on import).
"""
import re
import sys
import json
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_HIGGS = _ROOT / "higgs"
if str(_HIGGS) not in sys.path:
    sys.path.insert(0, str(_HIGGS))
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

import pytest  # noqa: E402
import _build_v4 as bv  # noqa: E402  (must import without rendering)

# The kit md and the site/quantum bundles are generated, gitignored data — absent in a
# clean checkout (fresh clone / CI). Skip the whole module when they are missing rather
# than aborting collection with a FileNotFoundError; run the real assertions when present.
_KIT_F = _HIGGS / "reels_2026-06-27_kit.md"
_SITE_F = _ROOT / "web" / "public" / "data" / "site.json"
_QUANT_F = _ROOT / "web" / "public" / "data" / "quantum.json"
if not (_KIT_F.exists() and _SITE_F.exists() and _QUANT_F.exists()):
    pytest.skip("carousel data bundles not present (generated/gitignored)",
                allow_module_level=True)

KIT = _KIT_F.read_text(encoding="utf-8")
SITE = json.loads(_SITE_F.read_text(encoding="utf-8"))["stocks"]
QUANT = json.loads(_QUANT_F.read_text(encoding="utf-8"))["stocks"]


def _syms(bundle):
    # site/quantum "stocks" is a {ticker: {...}} dict — symbols are its keys; tolerate a
    # list-of-dicts shape too.
    if isinstance(bundle, dict):
        return set(bundle)
    return {(r.get("symbol") or r.get("ticker")) for r in bundle if isinstance(r, dict)}


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
    # The data slide renders the kit's configured rows, each value pulled from the bundle.
    # Assert the hero renders and every ticker shown is one the bundle actually carries (no
    # phantom rows) — rather than hard-coding a peer list that drifts with the kit config.
    site_syms = _syms(SITE)
    assert "TEAM" in html and "TEAM" in site_syms
    shown = set(re.findall(r">([A-Z]{2,5})<", html))
    assert shown, "data slide rendered no ticker rows"
    assert shown <= site_syms, f"slide shows tickers absent from the bundle: {shown - site_syms}"
    assert "%" in html  # disc mode → percent-below-fundamental-value figures


def test_quantum_data_slide_uses_mult_rows():
    sl = _slides()
    html = sl["v4_qbts_2_data.png"]
    quant_syms = _syms(QUANT)
    assert "QBTS" in html and "QBTS" in quant_syms
    shown = set(re.findall(r">([A-Z]{2,5})<", html))
    assert shown, "quantum data slide rendered no ticker rows"
    assert shown <= quant_syms, f"slide shows tickers absent from the bundle: {shown - quant_syms}"
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
