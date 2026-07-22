# scripts/tests/test_daily_copy.py — key cases (use the real bundle when present)
import json, pathlib, pytest
from aiinvest import daily_copy

BUNDLE = json.loads((pathlib.Path(__file__).resolve().parents[2]
                     / "web/public/data/halal.json").read_text(encoding="utf-8"))

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
