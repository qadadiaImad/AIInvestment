"""TDD tests for scripts/build_reel_props.py — the live-data SlideStoryReel props
builder (docs/superpowers/plans/2026-07-21-reel-factory-unification.md Task 3).
"""
import json

import pytest

import build_reel_props as brp
from build_reel_props import InsufficientDataError, build_props


def _test(id_, ratio, threshold, margin, status="fail"):
    return {"id": id_, "label": id_, "ratio": ratio, "threshold": threshold,
            "margin": margin, "status": status}


WULF_BUNDLE = {
    "generated_at": "2026-07-21T14:21:52Z",
    "verdicts": {
        "WULF": {
            "symbol": "WULF",
            "overall": "questionable",
            "overall_basis": "AAOIFI",
            "layer": "L1-chips",
            "inputs_asof": "2026-07-21T12:12:54Z",
            "standards": {
                "AAOIFI": {"status": "fail", "tests": [
                    _test("aaoifi_debt", 0.5686, 0.30, -0.2686),
                    _test("aaoifi_cash", 0.3024, 0.30, -0.0024),
                ]},
                "FTSE": {"status": "fail", "tests": [
                    _test("ftse_debt", 0.7582, 0.3333, -0.4249),
                    _test("ftse_cash", 0.4032, 0.3333, -0.0699),
                    _test("ftse_receivables", 0.4034, 0.50, 0.0966, status="pass"),
                ]},
                "MSCI": {"status": "fail", "tests": [
                    _test("msci_debt", 0.7582, 0.3333, -0.4249),
                    _test("msci_cash", 0.4032, 0.3333, -0.0699),
                    _test("msci_receivables", 0.4034, 0.70, 0.2966, status="pass"),
                ]},
            },
            "business": {
                "status": "questionable",
                "impermissible_revenue_pct": {
                    "value": 38.2,
                    "basis": "Digital asset mining revenue / total revenue, Q1 2026 10-Q.",
                },
            },
            "purification": {"per_share": 0.132, "status": "computed"},
        },
    },
}

# A verdict with no numeric ratio anywhere and no business revenue split —
# nothing decisive to visualize.
INSUFFICIENT_BUNDLE = {
    "verdicts": {
        "ZZZ": {
            "symbol": "ZZZ",
            "overall": "insufficient_data",
            "layer": "L1-chips",
            "inputs_asof": "2026-07-21T12:00:00Z",
            "standards": {
                "AAOIFI": {"status": "unknown", "tests": [
                    {"id": "aaoifi_debt", "label": "Interest-bearing debt / market cap",
                     "ratio": None, "threshold": 0.30, "margin": None, "status": "unknown"},
                ]},
            },
            "business": {"status": "unknown", "impermissible_revenue_pct": None},
            "purification": {"per_share": None, "status": "insufficient_data"},
        },
    },
}


# --- build_props: shape ---------------------------------------------------

def test_wulf_shaped_bundle_produces_five_beats():
    props = build_props("WULF", WULF_BUNDLE)
    assert [b["kind"] for b in props["beats"]] == ["hook", "bars", "donut", "stamp", "endcard"]
    assert len(props["beats"]) == 5


def test_props_match_slide_story_props_schema_fields():
    props = build_props("WULF", WULF_BUNDLE)
    assert set(props.keys()) == {
        "ticker", "tickerSub", "badge", "beats", "vo", "bubbleClips", "captions", "disclaimer",
    }
    assert props["ticker"] == "WULF"
    assert isinstance(props["tickerSub"], str) and props["tickerSub"]
    assert isinstance(props["badge"], str) and props["badge"]
    assert props["bubbleClips"] == []
    assert props["captions"] == []
    assert props["disclaimer"] == "Computed methodology result — not a fatwa · not financial advice"


def test_bars_beat_has_binding_test_per_standard():
    props = build_props("WULF", WULF_BUNDLE)
    bars_beat = next(b for b in props["beats"] if b["kind"] == "bars")
    labels = [b["label"] for b in bars_beat["bars"]]
    assert labels == ["AAOIFI", "FTSE", "MSCI"]
    # binding test = tightest margin per standard (data.ts's `binding()` port)
    aaoifi = next(b for b in bars_beat["bars"] if b["label"] == "AAOIFI")
    assert aaoifi["ratio"] == pytest.approx(56.9, abs=0.1)
    assert aaoifi["threshold"] == pytest.approx(30.0, abs=0.1)
    assert aaoifi["status"] in {"pass", "fail", "unknown"}


def test_donut_beat_carries_business_revenue_pct():
    props = build_props("WULF", WULF_BUNDLE)
    donut_beat = next(b for b in props["beats"] if b["kind"] == "donut")
    assert donut_beat["pct"] == pytest.approx(38.2)
    assert donut_beat["tone"] in {"pass", "fail", "warn"}


def test_stamp_beat_verdict_is_a_valid_enum_member():
    props = build_props("WULF", WULF_BUNDLE)
    stamp_beat = next(b for b in props["beats"] if b["kind"] == "stamp")
    assert stamp_beat["verdict"] in {"halal", "not_halal", "questionable", "insufficient_data"}
    assert stamp_beat["verdict"] == "questionable"


# --- copy rails ------------------------------------------------------------

def test_hook_copy_never_uses_haram_as_accusation():
    props = build_props("WULF", WULF_BUNDLE)
    hook = props["beats"][0]
    assert hook["kind"] == "hook"
    assert "haram" not in hook["headline"].lower()
    assert "haram" not in hook["sub"].lower()


def test_no_beat_or_vo_line_ever_uses_the_word_haram():
    props = build_props("WULF", WULF_BUNDLE)
    for beat in props["beats"]:
        for value in beat.values():
            if isinstance(value, str):
                assert "haram" not in value.lower()
    for line in props["vo"]:
        assert "haram" not in line.lower()


def test_disclaimer_always_present_and_matches_wulf_footer():
    props = build_props("WULF", WULF_BUNDLE)
    assert "not a fatwa" in props["disclaimer"].lower()
    assert "not financial advice" in props["disclaimer"].lower()


# --- durations / vo ----------------------------------------------------------

def test_durations_sum_positive():
    props = build_props("WULF", WULF_BUNDLE)
    total = sum(b["durationInFrames"] for b in props["beats"])
    assert total > 0
    assert all(b["durationInFrames"] > 0 for b in props["beats"])


def test_vo_length_matches_beats_length():
    props = build_props("WULF", WULF_BUNDLE)
    assert len(props["vo"]) == len(props["beats"])


# --- story param (--auto ranking hook) -------------------------------------

def test_story_headline_fact_seeds_the_hook_when_provided():
    story = {"symbol": "WULF", "kind": "extreme_ratio",
             "headline_fact": "WULF: Interest-bearing debt / market cap at 56.9% vs a 30.0% limit",
             "numbers": [], "verdict": "questionable"}
    props = build_props("WULF", WULF_BUNDLE, story=story)
    assert props["beats"][0]["headline"] == story["headline_fact"]


# --- abort paths -------------------------------------------------------------

def test_unknown_ticker_raises_insufficient_data_error():
    with pytest.raises(InsufficientDataError):
        build_props("NOPE", WULF_BUNDLE)


def test_verdict_with_no_ratio_and_no_business_data_raises_insufficient_data_error():
    with pytest.raises(InsufficientDataError):
        build_props("ZZZ", INSUFFICIENT_BUNDLE)


def test_cli_aborts_with_exit_code_2_on_insufficient_data(tmp_path):
    bundle_path = tmp_path / "halal.json"
    bundle_path.write_text(json.dumps(INSUFFICIENT_BUNDLE), encoding="utf-8")
    out_path = tmp_path / "out.json"

    with pytest.raises(SystemExit) as excinfo:
        brp.main(["ZZZ", "--bundle", str(bundle_path), "--out", str(out_path)])

    assert excinfo.value.code == 2
    assert not out_path.exists()


def test_cli_aborts_with_exit_code_2_on_unreadable_bundle(tmp_path):
    out_path = tmp_path / "out.json"
    with pytest.raises(SystemExit) as excinfo:
        brp.main(["WULF", "--bundle", str(tmp_path / "missing.json"), "--out", str(out_path)])
    assert excinfo.value.code == 2
    assert not out_path.exists()


def test_cli_aborts_with_exit_code_2_when_no_ticker_and_no_auto(tmp_path):
    bundle_path = tmp_path / "halal.json"
    bundle_path.write_text(json.dumps(WULF_BUNDLE), encoding="utf-8")
    out_path = tmp_path / "out.json"
    with pytest.raises(SystemExit) as excinfo:
        brp.main(["--bundle", str(bundle_path), "--out", str(out_path)])
    assert excinfo.value.code == 2


# --- CLI success path ---------------------------------------------------------

def test_cli_writes_valid_props_json(tmp_path):
    bundle_path = tmp_path / "halal.json"
    bundle_path.write_text(json.dumps(WULF_BUNDLE), encoding="utf-8")
    out_path = tmp_path / "generated_wulf.json"

    rc = brp.main(["WULF", "--bundle", str(bundle_path), "--out", str(out_path)])

    assert rc == 0
    assert out_path.exists()
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written == build_props("WULF", WULF_BUNDLE)
