# scripts/tests/test_daily_copy.py — key cases (use the real bundle when present)
import json, pathlib, pytest
from aiinvest import daily_copy
from build_reel_props import DISCLAIMER
import build_reel_props
from aiinvest.halal_lint import DISCLAIMER as SPOKEN_DISCLAIMER

BUNDLE = json.loads((pathlib.Path(__file__).resolve().parents[2]
                     / "web/public/data/halal.json").read_text(encoding="utf-8"))

_LEAK_WORDS = ("pass", "fail", "review")


def _first_not_halal_ticker_that_builds():
    """First `verdicts` entry with overall == "not_halal" that `build_daily`
    can actually build a reel for (skipping InsufficientDataError entries —
    the task asks for "the first not_halal entry", but that entry must also
    be buildable to exercise the leak gate end-to-end)."""
    for tk, v in BUNDLE["verdicts"].items():
        if v.get("overall") != "not_halal":
            continue
        try:
            daily_copy.build_daily(tk, BUNDLE, None, "2026-07-22")
        except daily_copy.InsufficientDataError:
            continue
        return tk
    raise AssertionError("no buildable not_halal ticker found in the live bundle")


def _first_ticker_with_shape(shape):
    for tk, v in BUNDLE["verdicts"].items():
        try:
            props = build_reel_props.build_props(tk, BUNDLE, story=None)
        except build_reel_props.InsufficientDataError:
            continue
        bars_beat = next((b for b in props["beats"] if b["kind"] == "bars"), None)
        bars = bars_beat["bars"] if bars_beat else []
        overall = v.get("overall")
        if daily_copy._shape_for(bars, overall) == shape:
            return tk
    raise AssertionError(f"no ticker with shape {shape!r} found in the live bundle")

def test_a_b_differ_only_in_hook():
    d = daily_copy.build_daily("WULF", BUNDLE, None, "2026-07-22")
    a, b = d["props_a"], d["props_b"]
    assert a["beats"][0] != b["beats"][0] and a["vo"][0] != b["vo"][0]
    assert a["beats"][1:] == b["beats"][1:] and a["vo"][1:] == b["vo"][1:]

def test_verdict_withheld_until_stamp():
    d = daily_copy.build_daily("GEV", BUNDLE, None, "2026-07-22")
    kinds = [bt["kind"] for bt in d["props_a"]["beats"]]
    stamp_i = kinds.index("stamp")
    assert stamp_i == len(kinds) - 2                      # stamp is second-to-last
    joined_before = " ".join(d["props_a"]["vo"][:stamp_i]).lower()
    for word in ("pass", "fail", "review"):
        assert word not in joined_before                  # no early verdict leak

def test_caption_rules():
    d = daily_copy.build_daily("ETN", BUNDLE, None, "2026-07-22")
    cap = d["caption"]
    assert cap.count("#") == 5 and "halal" in cap.lower() and "Send this" in cap

def test_all_texts_lint_clean_across_bundle():
    ok, skipped = 0, 0
    for sym in list(BUNDLE["verdicts"])[:40]:
        try:
            daily_copy.build_daily(sym, BUNDLE, None, "2026-07-22"); ok += 1
        except daily_copy.InsufficientDataError:
            skipped += 1
    assert ok >= 20 and ok + skipped == 40   # lint errors would raise LintError

def test_flip_story_changes_hook():
    story = {"symbol": "WULF", "kind": "flip", "headline_fact": "WULF flipped questionable -> not_halal",
             "verdict": "not_halal", "numbers": []}
    d = daily_copy.build_daily("WULF", BUNDLE, story, "2026-07-22")
    assert "changed" in d["props_a"]["beats"][0]["headline"].lower()


# --- task-3 review fixes -----------------------------------------------------

def test_caption_footer_has_verbatim_plan_disclaimer_and_spoken_phrase():
    d = daily_copy.build_daily("ETN", BUNDLE, None, "2026-07-22")
    cap = d["caption"]
    assert DISCLAIMER in cap                          # verbatim plan footer constant
    assert SPOKEN_DISCLAIMER in cap.lower()            # lint_halal_script's spoken phrase


def test_fail_shape_ticker_no_pre_stamp_verdict_leak_either_variant():
    sym = _first_not_halal_ticker_that_builds()
    d = daily_copy.build_daily(sym, BUNDLE, None, "2026-07-22")
    for variant in ("props_a", "props_b"):
        props = d[variant]
        kinds = [b["kind"] for b in props["beats"]]
        stamp_i = kinds.index("stamp")
        joined = " ".join(props["vo"][:stamp_i]).lower()
        for bad in _LEAK_WORDS:
            assert bad not in joined, f"{sym} {variant} leaks {bad!r} pre-stamp: {joined!r}"


def test_leak_gate_raises_lint_error_on_doctored_hook_b_template(monkeypatch):
    sym = _first_ticker_with_shape("fail")
    doctored = dict(daily_copy._HOOK_B)
    doctored["fail"] = (
        "Everyone assumes this one fails.",
        "Assalamu alaykum. {ticker}. Everyone assumes this one fails the screen.",
    )
    monkeypatch.setattr(daily_copy, "_HOOK_B", doctored)
    with pytest.raises(daily_copy.LintError) as exc:
        daily_copy.build_daily(sym, BUNDLE, None, "2026-07-22")
    assert any("props_b" in v and "fail" in v for v in exc.value.violations)


# --- task-9 review fixes: plain-words company intro replaces greeting -----

def test_no_assalamu_anywhere_in_vo_or_caption_across_several_tickers():
    for sym in ("WULF", "GEV", "ETN", "NVDA", "PLTR", "WKEY"):
        try:
            d = daily_copy.build_daily(sym, BUNDLE, None, "2026-07-22")
        except daily_copy.InsufficientDataError:
            continue
        for variant in ("props_a", "props_b"):
            joined = " ".join(d[variant]["vo"]).lower()
            assert "assalamu" not in joined, f"{sym} {variant} still greets: {joined!r}"
        assert "assalamu" not in d["caption"].lower()


def test_vo0_starts_with_company_line_for_mapped_ticker():
    d = daily_copy.build_daily("NVDA", BUNDLE, None, "2026-07-22")
    for variant in ("props_a", "props_b"):
        vo0 = d[variant]["vo"][0]
        assert vo0.startswith("NVDA — the company that"), vo0
        assert "assalamu" not in vo0.lower()
        # on-screen sub mirrors the spoken company line, not the generic hook sub
        sub = d[variant]["beats"][0]["sub"]
        assert sub == "NVDA — the company that makes the chips that train AI."


def test_fallback_descriptor_for_unmapped_ticker_never_crashes_or_empty():
    synthetic_bundle = {
        "verdicts": {
            "ZZZZ": {
                "overall": "questionable",
                "layer": "L1-chips",
                "inputs_asof": "2026-07-22T00:00:00Z",
                "standards": {
                    "AAOIFI": {
                        "status": "fail",
                        "tests": [
                            {"label": "Interest-bearing debt / market cap",
                             "margin": -0.05, "ratio": 35.0, "threshold": 30.0, "status": "fail"},
                        ]
                    }
                },
                "business": {},
            }
        }
    }
    d = daily_copy.build_daily("ZZZZ", synthetic_bundle, None, "2026-07-22")
    vo0 = d["props_a"]["vo"][0]
    assert vo0.startswith("ZZZZ — the company")
    assert vo0.strip() != "ZZZZ — ."   # never an empty descriptor
    assert "assalamu" not in vo0.lower()
    sub = d["props_a"]["beats"][0]["sub"]
    assert sub and sub.startswith("ZZZZ — the company")


def test_a_b_still_differ_only_in_hook_after_company_intro():
    d = daily_copy.build_daily("WULF", BUNDLE, None, "2026-07-22")
    a, b = d["props_a"], d["props_b"]
    assert a["beats"][0] != b["beats"][0] and a["vo"][0] != b["vo"][0]
    assert a["beats"][1:] == b["beats"][1:] and a["vo"][1:] == b["vo"][1:]


def test_no_assalamu_and_lint_clean_across_full_bundle():
    ok, skipped = 0, 0
    for sym in BUNDLE["verdicts"]:
        try:
            d = daily_copy.build_daily(sym, BUNDLE, None, "2026-07-22")
        except daily_copy.InsufficientDataError:
            skipped += 1
            continue
        ok += 1
        for variant in ("props_a", "props_b"):
            joined = " ".join(d[variant]["vo"]).lower()
            assert "assalamu" not in joined, f"{sym} {variant} still greets"
        assert "assalamu" not in d["caption"].lower()
    assert ok + skipped == len(BUNDLE["verdicts"]) == 128
    assert ok >= 100  # lint/insufficient-data errors would raise, not silently skip


def test_hook_a_no_numeric_ratio_no_donut_raises_insufficient_data():
    synthetic_bundle = {
        "verdicts": {
            "ZZZZ": {
                "overall": "questionable",
                "layer": "L1-chips",
                "inputs_asof": "2026-07-22T00:00:00Z",
                "standards": {
                    "AAOIFI": {
                        "tests": [
                            {"margin": 0.05, "status": "unknown"},
                        ]
                    }
                },
                "business": {},
            }
        }
    }
    # Sanity check on the fixture shape this test relies on: build_reel_props
    # itself must NOT reject this shape (it only aborts when bars is empty
    # AND there's no donut split) — the non-numeric-ratio-bar case slips
    # through to daily_copy, which is exactly the gap this test guards.
    props = build_reel_props.build_props("ZZZZ", synthetic_bundle, story=None)
    assert props["beats"][1]["kind"] == "bars"
    assert props["beats"][1]["bars"][0]["ratio"] is None

    with pytest.raises(daily_copy.InsufficientDataError):
        daily_copy.build_daily("ZZZZ", synthetic_bundle, None, "2026-07-22")
