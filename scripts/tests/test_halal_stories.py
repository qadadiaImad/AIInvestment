"""Story picker: ranks halal verdicts into content-worthy stories. Pure, no I/O."""
from aiinvest import halal_stories


def _v(sym, overall, business, tests):
    return {"symbol": sym, "overall": overall, "overall_basis": "AAOIFI",
            "standards": {"AAOIFI": {"status": "pass" if all(t[1] == "pass" for t in tests) else "fail",
                                     "tests": [{"id": f"aaoifi_{i}", "label": lbl, "ratio": r,
                                                "threshold": 0.30, "margin": 0.30 - (r or 0),
                                                "status": st} for i, (lbl, st, r) in enumerate(tests)],
                                     "activity_status": "pass", "activity_threshold_pct": 5.0}},
            "business": {"status": business}, "purification": {"per_share": None},
            "inputs_asof": "2026-07-21T14:00:00Z"}


BUNDLE = {"verdicts": {
    # WKEY-pattern: extreme cash ratio (5.84x vs 0.30 threshold)
    "WKEY": _v("WKEY", "not_halal", "clean", [("cash/mcap", "fail", 5.84)]),
    # INTU-pattern: ratios pass, business prohibited
    "INTU": _v("INTU", "not_halal", "prohibited", [("debt/mcap", "pass", 0.086)]),
    # boring pass
    "NVDA": _v("NVDA", "halal", "clean", [("debt/mcap", "pass", 0.0026)]),
    # near-threshold squeeze (margin < 0.05)
    "AKAM": _v("AKAM", "not_halal", "clean", [("debt/mcap", "fail", 0.328)]),
}}


def test_extreme_ratio_outranks_squeeze_and_boring():
    stories = halal_stories.pick_stories(BUNDLE, top=4)
    kinds = {s["symbol"]: s["kind"] for s in stories}
    assert kinds["WKEY"] == "extreme_ratio"
    assert kinds["INTU"] == "business_override"
    assert kinds["AKAM"] == "margin_squeeze"
    assert stories[0]["symbol"] in ("WKEY", "INTU")   # big stories first
    assert "NVDA" not in [s["symbol"] for s in stories[:3]]


def test_flip_from_alerts_ranks_first():
    alerts = [{"symbol": "NVDA", "from": "halal", "to": "not_halal",
               "driver_test": "aaoifi_debt", "old_value": 0.29, "new_value": 0.31}]
    stories = halal_stories.pick_stories(BUNDLE, alerts=alerts, top=3)
    assert stories[0]["symbol"] == "NVDA" and stories[0]["kind"] == "flip"


def test_numbers_are_render_ready_strings():
    s = [x for x in halal_stories.pick_stories(BUNDLE, top=4) if x["symbol"] == "WKEY"][0]
    assert any("5.8" in n["value"] or "584" in n["value"] for n in s["numbers"])
    assert s["headline_fact"]


def test_empty_bundle_gives_empty_list():
    assert halal_stories.pick_stories({"verdicts": {}}) == []
