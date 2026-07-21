import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "higgs"))
import _build_v4 as b4  # noqa: E402

CARD = {
    "overall": "questionable",
    "badge": {"text": "AAOIFI SCREEN: REVIEW", "color": "#E0A23B"},
    "standards_rows": [
        {"name": "AAOIFI", "ok": True, "binding_label": "debt / market cap",
         "ratio": "21.0%", "threshold": "30.0%", "margin": "+9.0pt"},
        {"name": "FTSE", "ok": True, "binding_label": "debt / total assets",
         "ratio": "28.0%", "threshold": "33.3%", "margin": "+5.3pt"},
    ],
    "business_line": "Business activity: crypto-mining — 38.2% impermissible (Q1-2026 revenue mix)",
    "purification_line": "Purification (estimated): ~$0.13/share",
    "inputs_asof": "2026-07-21T13:07:36Z",
}

KIT = '''"WULF":{ "hero":"hero_wulf.png", "logo":"logo_WULF.png", "ex":"NASDAQ",
 "kick":"HALAL SCREEN", "head":"H", "sub":"S", "data_kick":"DK", "data_title":"DT",
 "data_cap":"", "data_foot":"", "mode":"disc", "rows":[], "tk_kick":"TK", "big":"38",
 "unit":"%", "tk_label":"L", "tk_body":"B", "src":"site",
 "halal_script":"thirty-eight. Educational, not financial or religious advice." }'''
HALAL_MAP = {"WULF": CARD}

def test_header_badge_rendered():
    h = b4.header("WULF", "NASDAQ", badge=CARD["badge"])
    assert "AAOIFI SCREEN: REVIEW" in h and "#E0A23B" in h

def test_header_no_badge_backcompat():
    h = b4.header("NVDA", "NASDAQ")
    assert "AAOIFI" not in h

def test_screen_slide_contents():
    html = b4.slide_screen("", "<div/>", CARD)
    for needle in ("AAOIFI", "FTSE", "debt / market cap", "21.0%", "30.0%", "+9.0pt",
                   "38.2%", "~$0.13/share", "2026-07-21",
                   "not a fatwa"):
        assert needle in html

def test_build_slides_halal_swaps_slide2():
    out = b4.build_slides(KIT, {}, {}, {}, {}, "2026-07-21", halal_map=HALAL_MAP)
    assert "v4_wulf_2_data.png" in out
    assert "debt / market cap" in out["v4_wulf_2_data.png"]        # screen card, not bars
    assert "AAOIFI SCREEN: REVIEW" in out["v4_wulf_1_hook.png"]     # badge on every slide
    assert "not a fatwa" in out["v4_wulf_3_takeaway.png"]

def test_build_slides_no_halal_map_unchanged():
    out = b4.build_slides(KIT, {}, {}, {}, {}, "2026-07-21")
    assert "debt / market cap" not in out["v4_wulf_2_data.png"]     # ordinary bars slide

def test_halal_frames_names_and_size():
    frames = b4.build_halal_frames(KIT, {}, HALAL_MAP)
    assert set(frames) == {"reel_wulf_hook.png", "reel_wulf_data.png", "reel_wulf_takeaway.png"}
    assert "1920" in frames["reel_wulf_data.png"]                   # 9:16 sizing present
    assert "debt / market cap" in frames["reel_wulf_data.png"]


# --- Regression tests: final-review wave -------------------------------------

def test_business_line_bound_keeps_disclaimer_on_slide():
    # CRITICAL 1: an unbounded business_line (e.g. a 250+ char basis string, as
    # seen for real ticker IREN) must not be able to push the mandatory
    # "not a fatwa" disclaimer off the fixed-size slide.
    from aiinvest.halal_join import screen_card_data
    verdicts = {
        "IREN": {
            "overall": "questionable",
            "standards": {"AAOIFI": {"status": "pass", "tests": [
                {"id": "debt_mcap", "label": "debt / market cap", "ratio": 0.21,
                 "threshold": 0.30, "margin": 0.09, "status": "pass"}]}},
            "business": {"status": "questionable", "categories": ["crypto-mining", "misc"],
                "impermissible_revenue_pct": {"value": 38.2, "basis": "x" * 260}},
            "purification": {"status": "computed", "per_share": 0.13},
            "inputs_asof": "2026-07-21T13:07:36Z",
        }
    }
    card = screen_card_data(verdicts, "IREN")
    assert len(card["business_line"]) <= 200
    html = b4.slide_screen("", "<div/>", card)
    assert "not a fatwa" in html


def test_build_slides_halal_missing_from_loaded_bundle_skips_ticker():
    # IMPORTANT 4: bundle loaded (halal_map is a dict) but this ticker isn't in
    # it -> exclude entirely rather than falling through to a broken bars slide.
    out = b4.build_slides(KIT, {}, {}, {}, {}, "2026-07-21", halal_map={})
    assert not any(k.startswith("v4_wulf_") for k in out)


KIT_BADGE_ONLY = '''"GEV":{ "hero":"hero_gev.png", "logo":"logo_GEV.png", "ex":"NYSE",
 "kick":"K", "head":"H", "sub":"S", "data_kick":"DK", "data_title":"DT",
 "data_cap":"", "data_foot":"", "mode":"disc", "rows":[], "tk_kick":"TK", "big":"1",
 "unit":"x", "tk_label":"L", "tk_body":"B", "src":"site" }'''
GEV_CARD = {
    "overall": "halal",
    "badge": {"text": "AAOIFI SCREEN: PASS", "color": "#34D399"},
    "standards_rows": [],
    "business_line": "Business activity: clean",
    "purification_line": "Purification (estimated): $0.00/share",
    "inputs_asof": "2026-07-21T13:07:36Z",
}


def test_build_slides_badge_only_carries_disclaimer():
    # IMPORTANT 5: an ordinary (non-halal_script) post whose ticker still has a
    # verdict badge (card present) must carry the compliance footer on its
    # bars and takeaway slides too, not just the halal-script screen slide.
    out = b4.build_slides(KIT_BADGE_ONLY, {}, {}, {}, {}, "2026-07-21",
                           halal_map={"GEV": GEV_CARD})
    assert "not a fatwa" in out["v4_gev_2_data.png"]
    assert "not a fatwa" in out["v4_gev_3_takeaway.png"]
