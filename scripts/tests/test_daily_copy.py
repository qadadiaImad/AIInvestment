# scripts/tests/test_daily_copy.py — key cases (use the real bundle when present)
import json, pathlib, pytest
from aiinvest import daily_copy, heroes
from build_reel_props import DISCLAIMER
import build_reel_props
from aiinvest.halal_lint import DISCLAIMER as SPOKEN_DISCLAIMER, lint_editorial

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
        # on-screen sub mirrors the spoken company line, not the generic hook
        # sub — task-3 appends the dramatize shock line as a second sentence
        # so the hero has something to show under the hook.
        sub = d[variant]["beats"][0]["sub"]
        assert sub.startswith("NVDA — the company that makes the chips that train AI.")
        assert sub == f"NVDA — the company that makes the chips that train AI. {daily_copy.dramatize(daily_copy.screen_card_data(BUNDLE['verdicts'], 'NVDA'))}"


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


# --- task-3: dramatize + shocking intro + lint_editorial + hero + company_def --

def _wkey_card():
    return daily_copy.screen_card_data(BUNDLE["verdicts"], "WKEY")


def test_dramatize_wkey_owes_multiple_of_company_worth():
    line = daily_copy.dramatize(_wkey_card())
    # WKEY's binding row (AAOIFI interest-bearing deposits & securities /
    # market cap) is ~561% of market cap against a 30% limit -> >=3x severity,
    # mcap-relative -> the "owes N times what the company is worth" template.
    assert "times what the whole company is worth" in line
    assert "5." in line  # ~5.6x — the real ratio, not ratio/threshold (~18.7x)
    assert "isn't close" in line


def test_dramatize_no_banned_word_no_verdict_token():
    line = daily_copy.dramatize(_wkey_card())
    assert lint_editorial([line]) == []
    low = line.lower()
    for bad in ("pass", "fail", "review"):
        assert bad not in low


def test_dramatize_passes_lint_visceral():
    from aiinvest.halal_lint import lint_visceral
    line = daily_copy.dramatize(_wkey_card())
    assert lint_visceral([line]) == []


def test_dramatize_under_limit_case_has_no_banned_or_verdict_word():
    card = {"standards_rows": [
        {"name": "AAOIFI", "binding_label": "Interest-bearing debt / market cap",
         "ratio": "12.0%", "threshold": "30.0%", "margin": "+18.0pt"},
    ]}
    line = daily_copy.dramatize(card)
    assert line == "Every debt line lands under the limit."
    assert lint_editorial([line]) == []


def test_dramatize_moderate_severity_uses_generic_template():
    card = {"standards_rows": [
        {"name": "FTSE", "binding_label": "Debt / total assets",
         "ratio": "45.0%", "threshold": "30.0%", "margin": "-15.0pt"},
    ]}
    line = daily_copy.dramatize(card)
    assert "45.0%" in line and "30.0%" in line
    assert "limit" in line
    assert lint_editorial([line]) == []
    assert lint_visceral_ok(line)


def lint_visceral_ok(line):
    from aiinvest.halal_lint import lint_visceral
    return lint_visceral([line]) == []


def test_dramatize_handles_none_or_empty_card_without_crashing():
    assert daily_copy.dramatize(None) == "Every debt line lands under the limit."
    assert daily_copy.dramatize({}) == "Every debt line lands under the limit."
    assert daily_copy.dramatize({"standards_rows": []}) == "Every debt line lands under the limit."


def test_lint_editorial_flags_and_wkey_line_stays_clean():
    assert lint_editorial(["This is dangerous leverage."])
    assert lint_editorial(["It's a debt trap."])
    assert lint_editorial([daily_copy.dramatize(_wkey_card())]) == []


def test_hero_src_on_wkey_props():
    d = daily_copy.build_daily("WKEY", BUNDLE, None, "2026-07-22")
    assert d["props_a"]["heroSrc"] == "heroes/Q4-security.jpg"
    assert d["props_b"]["heroSrc"] == "heroes/Q4-security.jpg"
    assert d["props_a"]["heroSrc"] == heroes.hero_for_layer(
        BUNDLE["verdicts"]["WKEY"]["layer"])


def test_company_def_in_kit_fields():
    d = daily_copy.build_daily("WKEY", BUNDLE, None, "2026-07-22")
    assert d["kit_fields"]["company_def"] == "the company that makes digital-security chips and keys"


def test_wkey_hook_a_no_double_ticker_and_no_greeting():
    d = daily_copy.build_daily("WKEY", BUNDLE, None, "2026-07-22")
    vo0 = d["props_a"]["vo"][0]
    assert vo0.startswith("WKEY — the company that makes digital-security chips and keys.")
    assert "But here's the shock:" in vo0
    # no double-ticker seam: "WKEY" appears exactly once
    assert vo0.count("WKEY") == 1
    assert "assalamu" not in vo0.lower()


def test_wkey_hook_b_no_double_ticker():
    d = daily_copy.build_daily("WKEY", BUNDLE, None, "2026-07-22")
    vo0 = d["props_b"]["vo"][0]
    assert vo0.count("WKEY") == 1


def test_a_b_still_differ_only_beats0_vo0_with_hero_and_dramatize():
    d = daily_copy.build_daily("WKEY", BUNDLE, None, "2026-07-22")
    a, b = d["props_a"], d["props_b"]
    assert a["beats"][0] != b["beats"][0] and a["vo"][0] != b["vo"][0]
    assert a["beats"][1:] == b["beats"][1:] and a["vo"][1:] == b["vo"][1:]
    assert a["heroSrc"] == b["heroSrc"]


def test_128_ticker_sweep_lint_clean_under_all_lints_including_editorial():
    from aiinvest.halal_lint import lint_visceral
    total = ok = skipped = 0
    for sym in BUNDLE["verdicts"]:
        total += 1
        try:
            d = daily_copy.build_daily(sym, BUNDLE, None, "2026-07-22")
        except daily_copy.InsufficientDataError:
            skipped += 1
            continue
        ok += 1
        for variant in ("props_a", "props_b"):
            props = d[variant]
            assert props["heroSrc"] == heroes.hero_for_layer(
                BUNDLE["verdicts"][sym].get("layer"))
            joined = " ".join(props["vo"]).lower()
            for bad in ("pass", "fail", "review"):
                kinds = [bt["kind"] for bt in props["beats"]]
                stamp_i = kinds.index("stamp")
                pre = " ".join(props["vo"][:stamp_i]).lower()
                assert bad not in pre, f"{sym} {variant} pre-stamp leaks {bad!r}"
            assert lint_editorial(props["vo"]) == [], f"{sym} {variant} editorial-word violation"
        assert lint_editorial([d["caption"]]) == []
    assert total == 128
    assert ok + skipped == total
    assert ok >= 100


def test_verdict_withheld_holds_for_wkey():
    d = daily_copy.build_daily("WKEY", BUNDLE, None, "2026-07-22")
    for variant in ("props_a", "props_b"):
        props = d[variant]
        kinds = [b["kind"] for b in props["beats"]]
        stamp_i = kinds.index("stamp")
        pre = " ".join(props["vo"][:stamp_i]).lower()
        for bad in ("pass", "fail", "review"):
            assert bad not in pre


# --- review fixes: gated shock connective + factual extreme-multiple threshold --

def test_dramatize_duk_style_mcap_under_3x_uses_milder_tier_not_isnt_close():
    # DUK's binding row is 92.9% of market cap (0.9x) against a 30% limit —
    # over the limit but nowhere near "owes 3x+ what it's worth". Must route
    # to the plain ratio-vs-limit tier, never the extreme "isn't close" tier.
    card = daily_copy.screen_card_data(BUNDLE["verdicts"], "DUK")
    line = daily_copy.dramatize(card)
    assert "isn't close" not in line
    assert "owes" not in line.lower()
    assert "92.9%" in line and "30.0%" in line
    assert "limit" in line


def test_dramatize_et_and_laes_also_use_milder_tier():
    for sym in ("ET", "LAES"):
        card = daily_copy.screen_card_data(BUNDLE["verdicts"], sym)
        line = daily_copy.dramatize(card)
        assert "isn't close" not in line, f"{sym}: {line!r}"
        assert "owes" not in line.lower(), f"{sym}: {line!r}"


def test_dramatize_wkey_still_extreme_after_threshold_fix():
    # WKEY genuinely owes 5.6x its market cap — must still fire the extreme
    # "owes N times ... isn't close" branch after the threshold fix.
    line = daily_copy.dramatize(_wkey_card())
    assert "owes 5.6 times" in line
    assert "isn't close" in line


def test_is_shock_true_for_over_limit_false_for_clean_and_missing():
    assert daily_copy.is_shock(_wkey_card()) is True
    assert daily_copy.is_shock(
        daily_copy.screen_card_data(BUNDLE["verdicts"], "DUK")) is True
    assert daily_copy.is_shock(
        daily_copy.screen_card_data(BUNDLE["verdicts"], "ADBE")) is False
    assert daily_copy.is_shock({"standards_rows": []}) is False
    assert daily_copy.is_shock(None) is False


def test_clean_ticker_vo0_has_no_false_shock_connective():
    # ADBE is under every debt limit — "here's the shock: every debt line
    # lands under the limit" would be self-negating. vo[0] must not claim a
    # shock for a clean ticker, and must still be truthful/lint-clean.
    d = daily_copy.build_daily("ADBE", BUNDLE, None, "2026-07-22")
    vo0 = d["props_a"]["vo"][0]
    assert "shock" not in vo0.lower()
    assert "every debt line lands under the limit" in vo0.lower()
    assert lint_editorial([vo0]) == []


def test_no_vo0_self_negating_shock_every_debt_line_across_bundle():
    for sym in BUNDLE["verdicts"]:
        try:
            d = daily_copy.build_daily(sym, BUNDLE, None, "2026-07-22")
        except daily_copy.InsufficientDataError:
            continue
        vo0 = d["props_a"]["vo"][0].lower()
        assert "shock: every debt line" not in vo0, f"{sym} self-negating shock line: {vo0!r}"


def test_no_owes_line_with_multiple_under_3_across_bundle():
    import re as _re
    owes_re = _re.compile(r"owes ([\d.]+) times")
    for sym in BUNDLE["verdicts"]:
        try:
            d = daily_copy.build_daily(sym, BUNDLE, None, "2026-07-22")
        except daily_copy.InsufficientDataError:
            continue
        for variant in ("props_a", "props_b"):
            for line in d[variant]["vo"]:
                m = owes_re.search(str(line))
                if m:
                    assert float(m.group(1)) >= 3.0, f"{sym} {variant}: {line!r}"
