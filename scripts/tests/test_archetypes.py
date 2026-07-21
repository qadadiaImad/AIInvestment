"""Hand-computable fixtures for aiinvest.archetypes — every expected number/verdict is
derived in a comment (mirrors the style of tests/test_risk.py). See
docs/superpowers/specs/2026-07-14-archetypes-design.md §8 for the binding test plan this
file implements.

Design notes on criteria whose "comparator/threshold" can't literally encode a two-sided
rule (a known, documented pattern already used by G6/B5's `0<=x<=cap` and L4's
`0<x<=cap` in the spec's own JSON example): `pass` is always computed by the REAL rule
(range check / custom logic), independent of what's displayed in comparator/threshold for
UI purposes. G4 (earnings_stability) stores `actual` = number of EPS points evaluated
(not loss-year count) so the sentence templates can render "{n} annual EPS reports"
directly from the row with no extra out-of-band context.
"""
import math

import pytest

from aiinvest import archetypes as arche


# --------------------------------------------------------------------------- fixture builder


def _stock(layer="L1-chips", valuation=None, fundamentals=None, history=None,
           as_of="2026-07-14", symbol="TEST"):
    return {
        "symbol": symbol,
        "layer": layer,
        "as_of": as_of,
        "valuation": valuation or {},
        "fundamentals": fundamentals or {},
        "performance": {},
        "history": history or {},
    }


def _row(stock, archetype, key):
    result = arche.evaluate_stock(stock)
    rows = {r["key"]: r for r in result["archetypes"][archetype]["criteria"]}
    return rows[key]


def _spec(archetype, key):
    return next(s for s in arche.CRITERIA[archetype] if s["key"] == key)


# --------------------------------------------------------------------------- extraction / dirty values


def test_missing_field_is_not_evaluable():
    stock = _stock(fundamentals={})
    row = _row(stock, "graham", "earnings_positive")
    assert row["evaluable"] is False
    assert row["pass"] is None
    assert row["actual"] is None


@pytest.mark.parametrize("dirty", ["", ".", "-", "--", "n/a", "N/A", "na", "NONE", "null"])
def test_dirty_strings_are_not_evaluable_not_a_crash(dirty):
    stock = _stock(fundamentals={"net_margin": dirty})
    row = _row(stock, "graham", "earnings_positive")
    assert row["evaluable"] is False
    assert row["pass"] is None


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_floats_are_not_evaluable(bad):
    stock = _stock(fundamentals={"net_margin": bad})
    row = _row(stock, "graham", "earnings_positive")
    assert row["evaluable"] is False


def test_negative_pe_is_not_evaluable_not_cheap():
    # A negative P/E means unprofitable, not "a bargain" -- must not evaluate to pass.
    stock = _stock(valuation={"pe": -5.0})
    row = _row(stock, "graham", "moderate_pe")
    assert row["evaluable"] is False
    assert row["pass"] is None


# --------------------------------------------------------------------------- Graham boundaries


def test_g1_earnings_positive_boundary():
    fail = _row(_stock(fundamentals={"net_margin": 0.0}), "graham", "earnings_positive")
    passed = _row(_stock(fundamentals={"net_margin": 0.01}), "graham", "earnings_positive")
    assert fail["pass"] is False
    assert passed["pass"] is True


def test_g2_moderate_pe_boundary():
    passed = _row(_stock(valuation={"pe": 15.0}), "graham", "moderate_pe")
    fail = _row(_stock(valuation={"pe": 15.01}), "graham", "moderate_pe")
    assert passed["pass"] is True
    assert fail["pass"] is False


def test_g3_pb_ps_fallback_pb_absent_uses_ps():
    stock = _stock(fundamentals={"ps": 2.0})
    row = _row(stock, "graham", "moderate_value_multiple")
    assert row["evaluable"] is True
    assert row["pass"] is True
    assert row["field"] == "fundamentals.ps"
    assert row["actual"] == pytest.approx(2.0)
    assert row["note"] == "P/B unavailable — used P/S <= 2.0"


def test_g3_pb_present_takes_priority_over_ps_even_when_ps_would_pass():
    # pb=1.6 fails Graham's 1.5 cap; ps=1.0 would have passed the 2.0 cap, but pb wins.
    stock = _stock(fundamentals={"pb": 1.6, "ps": 1.0})
    row = _row(stock, "graham", "moderate_value_multiple")
    assert row["field"] == "fundamentals.pb"
    assert row["actual"] == pytest.approx(1.6)
    assert row["pass"] is False
    assert row["note"] is None


def test_g3_both_absent_not_evaluable():
    row = _row(_stock(), "graham", "moderate_value_multiple")
    assert row["evaluable"] is False
    assert row["note"] is None


def test_g4_earnings_stability_needs_3_points():
    history = {"annualDilutedEPS": [{"date": "2024", "value": 1.0}, {"date": "2025", "value": 2.0}]}
    row = _row(_stock(history=history), "graham", "earnings_stability")
    assert row["evaluable"] is False
    assert row["pass"] is None


def test_g4_earnings_stability_3_points_all_positive_pass():
    history = {"annualDilutedEPS": [
        {"date": "2023", "value": 1.0}, {"date": "2024", "value": 2.0},
        {"date": "2025", "value": 3.0}]}
    row = _row(_stock(history=history), "graham", "earnings_stability")
    assert row["evaluable"] is True
    assert row["pass"] is True
    assert row["actual"] == 3  # n points evaluated, used by the "{n} annual EPS reports" template


def test_g4_earnings_stability_one_loss_year_fails():
    history = {"annualDilutedEPS": [
        {"date": "2023", "value": 1.0}, {"date": "2024", "value": -0.5},
        {"date": "2025", "value": 3.0}]}
    row = _row(_stock(history=history), "graham", "earnings_stability")
    assert row["evaluable"] is True
    assert row["pass"] is False
    assert row["actual"] == 3


def test_g5_current_ratio_boundary():
    passed = _row(_stock(fundamentals={"current_ratio": 2.0}), "graham", "current_ratio")
    fail = _row(_stock(fundamentals={"current_ratio": 1.99}), "graham", "current_ratio")
    assert passed["pass"] is True
    assert fail["pass"] is False


def test_g6_low_leverage_boundary_and_zero_debt():
    passed = _row(_stock(fundamentals={"debt_to_equity": 0.5}), "graham", "low_leverage")
    fail = _row(_stock(fundamentals={"debt_to_equity": 0.51}), "graham", "low_leverage")
    zero = _row(_stock(fundamentals={"debt_to_equity": 0.0}), "graham", "low_leverage")
    assert passed["pass"] is True
    assert fail["pass"] is False
    assert zero["pass"] is True


def test_g7_margin_of_safety_boundary():
    passed = _row(_stock(valuation={"fundamental_discount_pct": 25.0}), "graham", "margin_of_safety")
    fail = _row(_stock(valuation={"fundamental_discount_pct": 24.99}), "graham", "margin_of_safety")
    neg = _row(_stock(valuation={"fundamental_discount_pct": -5.0}), "graham", "margin_of_safety")
    assert passed["pass"] is True
    assert fail["pass"] is False
    assert neg["pass"] is False


# --------------------------------------------------------------------------- Buffett boundaries


def test_b1_high_roe_boundary():
    passed = _row(_stock(fundamentals={"roe": 15.0}), "buffett", "high_roe")
    fail = _row(_stock(fundamentals={"roe": 14.99}), "buffett", "high_roe")
    assert passed["pass"] is True
    assert fail["pass"] is False


def test_b2_high_roic_boundary():
    passed = _row(_stock(fundamentals={"roic": 12.0}), "buffett", "high_roic")
    fail = _row(_stock(fundamentals={"roic": 11.99}), "buffett", "high_roic")
    assert passed["pass"] is True
    assert fail["pass"] is False


def test_b3_gross_margin_moat_boundary():
    passed = _row(_stock(fundamentals={"gross_margin": 40.0}), "buffett", "gross_margin_moat")
    fail = _row(_stock(fundamentals={"gross_margin": 39.99}), "buffett", "gross_margin_moat")
    assert passed["pass"] is True
    assert fail["pass"] is False


def test_b4_operating_efficiency_boundary():
    passed = _row(_stock(fundamentals={"operating_margin": 15.0}), "buffett", "operating_efficiency")
    fail = _row(_stock(fundamentals={"operating_margin": 14.99}), "buffett", "operating_efficiency")
    assert passed["pass"] is True
    assert fail["pass"] is False


def test_b5_low_debt_boundary():
    passed = _row(_stock(fundamentals={"debt_to_equity": 1.0}), "buffett", "low_debt")
    fail = _row(_stock(fundamentals={"debt_to_equity": 1.01}), "buffett", "low_debt")
    assert passed["pass"] is True
    assert fail["pass"] is False


def test_b6_fcf_yield_negative_pfcf_not_evaluable_never_scored_as_fail():
    row = _row(_stock(fundamentals={"pfcf": -10.0}), "buffett", "fcf_yield")
    assert row["evaluable"] is False
    assert row["pass"] is None


def test_b6_fcf_yield_boundary():
    passed = _row(_stock(fundamentals={"pfcf": 25.0}), "buffett", "fcf_yield")
    fail = _row(_stock(fundamentals={"pfcf": 25.01}), "buffett", "fcf_yield")
    assert passed["pass"] is True
    assert fail["pass"] is False


def test_b7_fair_price_boundary():
    passed = _row(_stock(valuation={"fundamental_discount_pct": -10.0}), "buffett", "fair_price")
    fail = _row(_stock(valuation={"fundamental_discount_pct": -10.01}), "buffett", "fair_price")
    assert passed["pass"] is True
    assert fail["pass"] is False


# --------------------------------------------------------------------------- Lynch boundaries


def test_l1_peg_negative_growth_not_evaluable():
    stock = _stock(valuation={"pe": 15.0}, fundamentals={"eps_growth_yoy": -5.0})
    row = _row(stock, "lynch", "peg")
    assert row["evaluable"] is False
    assert row["pass"] is None


def test_l1_peg_boundary():
    # PEG = pe / eps_growth_yoy
    passed = _row(_stock(valuation={"pe": 15.0}, fundamentals={"eps_growth_yoy": 10.0}),
                  "lynch", "peg")
    assert passed["actual"] == pytest.approx(1.5)
    assert passed["pass"] is True

    fail = _row(_stock(valuation={"pe": 15.15}, fundamentals={"eps_growth_yoy": 10.0}),
                "lynch", "peg")
    assert fail["actual"] == pytest.approx(1.515)
    assert fail["pass"] is False


def test_l2_growth_band_boundaries():
    below = _row(_stock(fundamentals={"rev_growth_yoy": 14.99}), "lynch", "growth_band")
    floor = _row(_stock(fundamentals={"rev_growth_yoy": 15.0}), "lynch", "growth_band")
    ceiling = _row(_stock(fundamentals={"rev_growth_yoy": 50.0}), "lynch", "growth_band")
    above = _row(_stock(fundamentals={"rev_growth_yoy": 50.01}), "lynch", "growth_band")
    assert below["pass"] is False
    assert floor["pass"] is True
    assert ceiling["pass"] is True
    assert above["pass"] is False


def test_l3_avoid_hot_story_boundary():
    passed = _row(_stock(fundamentals={"ps": 10.0}), "lynch", "avoid_hot_story")
    fail = _row(_stock(fundamentals={"ps": 10.01}), "lynch", "avoid_hot_story")
    assert passed["pass"] is True
    assert fail["pass"] is False


def test_l4_room_to_grow_absent_not_evaluable_and_doesnt_affect_other_criteria():
    stock = _stock(valuation={"pe": 10.0}, fundamentals={"net_margin": 5.0})
    row = _row(stock, "lynch", "room_to_grow")
    assert row["evaluable"] is False
    assert row["pass"] is None
    other = _row(stock, "lynch", "earnings_backed")
    assert other["evaluable"] is True  # not poisoned by the missing market_cap


def test_l4_room_to_grow_boundary():
    passed = _row(_stock(valuation={"market_cap": 200_000_000_000}), "lynch", "room_to_grow")
    fail = _row(_stock(valuation={"market_cap": 200_000_000_001}), "lynch", "room_to_grow")
    assert passed["pass"] is True
    assert fail["pass"] is False


def test_l5_earnings_backed_boundary():
    fail = _row(_stock(fundamentals={"net_margin": 0.0}), "lynch", "earnings_backed")
    passed = _row(_stock(fundamentals={"net_margin": 0.01}), "lynch", "earnings_backed")
    assert fail["pass"] is False
    assert passed["pass"] is True


# --------------------------------------------------------------------------- scoring / verdict


def test_score_hand_computed_weighted_average():
    # Graham weights: earnings_positive=10, moderate_pe=15, moderate_value_multiple=15,
    # earnings_stability=15, current_ratio=15, low_leverage=15, margin_of_safety=15 (sum 100)
    # Make ALL 7 evaluable; pass: earnings_positive(10), current_ratio(15), low_leverage(15)
    # fail: moderate_pe(15), moderate_value_multiple(15), earnings_stability(15),
    #       margin_of_safety(15)
    # passing weight = 10+15+15 = 40; evaluable weight = 100 -> score = round(100*40/100) = 40
    stock = _stock(
        valuation={"pe": 99.0, "fundamental_discount_pct": -50.0},
        fundamentals={"net_margin": 5.0, "pb": 99.0, "current_ratio": 3.0,
                       "debt_to_equity": 0.1},
        history={"annualDilutedEPS": [
            {"date": "2023", "value": -1.0}, {"date": "2024", "value": 2.0},
            {"date": "2025", "value": 3.0}]},
    )
    result = arche.evaluate_stock(stock)["archetypes"]["graham"]
    assert result["n_evaluable"] == 7
    assert result["n_total"] == 7
    assert result["evaluable_weight_pct"] == 100
    assert result["n_pass"] == 3
    assert result["score"] == 40
    assert result["verdict"] == "poor_fit"


def test_score_renormalizes_when_criterion_missing_does_not_dilute():
    # Only current_ratio(15, evaluable+pass) and low_leverage(15, evaluable+pass) and
    # earnings_positive(10, evaluable+pass) are evaluable; everything else missing.
    # evaluable_weight = 10+15+15 = 40 (< 50% of 100) -> not_evaluable regardless of the
    # fact that all 3 pass. This also covers the "< 50% evaluable weight" verdict gate.
    stock = _stock(fundamentals={"net_margin": 5.0, "current_ratio": 3.0,
                                  "debt_to_equity": 0.1})
    result = arche.evaluate_stock(stock)["archetypes"]["graham"]
    assert result["n_evaluable"] == 3
    assert result["evaluable_weight_pct"] == 40
    assert result["score"] is None
    assert result["verdict"] == "not_evaluable"


def test_only_2_evaluable_even_high_weight_not_evaluable():
    # Buffett: only high_roe(20) + high_roic(20) evaluable = 40 weight, 2 criteria.
    # Fails BOTH the n_evaluable>=3 gate and (incidentally) the >=50% weight gate.
    stock = _stock(fundamentals={"roe": 99.0, "roic": 99.0})
    result = arche.evaluate_stock(stock)["archetypes"]["buffett"]
    assert result["n_evaluable"] == 2
    assert result["score"] is None
    assert result["verdict"] == "not_evaluable"


def test_4_evaluable_but_under_50pct_weight_not_evaluable():
    # Lynch weights: peg=25, growth_band=20, avoid_hot_story=20, room_to_grow=15,
    # earnings_backed=20 (sum 100). Make growth_band(20) + avoid_hot_story(20) +
    # room_to_grow(15) + earnings_backed(20) NOT evaluable by omission, leaving only
    # peg(25) evaluable... that's only 1. Instead: evaluate growth_band(20) +
    # avoid_hot_story(20) + earnings_backed(20) --> 3 criteria/60 weight (>=50%, would
    # pass gate). To get 4 evaluable at <50% weight we need 4 criteria summing <50:
    # there is no such 4-subset here (min 4-subset sum is 20+20+15+20=75). So instead
    # verify the boundary via Buffett's finer-grained weights: high_roic(20) +
    # gross_margin_moat(10) + operating_efficiency(10) + fair_price(10) = 50 (>=50, NOT
    # under) -- adjust to 3 of those + a 4th under 50: high_roic(20) not included;
    # gross_margin_moat(10)+operating_efficiency(10)+fair_price(10)+low_debt(15)=45 (<50)
    # with 4 evaluable criteria.
    stock = _stock(
        valuation={"fundamental_discount_pct": -20.0},  # fair_price: fails (-20 < -10)
        fundamentals={"gross_margin": 10.0,   # fails (<40)
                       "operating_margin": 5.0,  # fails (<15)
                       "debt_to_equity": 5.0},  # fails (>1.0)
    )
    result = arche.evaluate_stock(stock)["archetypes"]["buffett"]
    assert result["n_evaluable"] == 4
    assert result["evaluable_weight_pct"] == 45
    assert result["score"] is None
    assert result["verdict"] == "not_evaluable"


def test_all_pass_score_100():
    stock = _stock(
        valuation={"pe": 10.0, "fundamental_discount_pct": 30.0},
        fundamentals={"net_margin": 10.0, "pb": 1.0, "current_ratio": 3.0,
                       "debt_to_equity": 0.1},
        history={"annualDilutedEPS": [
            {"date": "2023", "value": 1.0}, {"date": "2024", "value": 2.0},
            {"date": "2025", "value": 3.0}]},
    )
    result = arche.evaluate_stock(stock)["archetypes"]["graham"]
    assert result["n_evaluable"] == 7
    assert result["n_pass"] == 7
    assert result["score"] == 100
    assert result["verdict"] == "strong_fit"


def test_all_fail_but_evaluable_score_0_poor_fit_not_not_evaluable():
    stock = _stock(
        valuation={"pe": 99.0, "fundamental_discount_pct": -50.0},
        fundamentals={"net_margin": -5.0, "pb": 99.0, "current_ratio": 0.1,
                       "debt_to_equity": 9.0},
        history={"annualDilutedEPS": [
            {"date": "2023", "value": -1.0}, {"date": "2024", "value": -2.0},
            {"date": "2025", "value": -3.0}]},
    )
    result = arche.evaluate_stock(stock)["archetypes"]["graham"]
    assert result["n_evaluable"] == 7
    assert result["n_pass"] == 0
    assert result["score"] == 0
    assert result["verdict"] == "poor_fit"


def _synthetic_rows(n_pass, n_total, weight_each=1):
    """n_total evaluable rows of equal weight, first n_pass passing -> exact
    score = round(100 * n_pass / n_total) with weight_each=1 (integer percentages,
    sidesteps the fact that our real criteria weights are multiples of 5/10/15/20/25
    and can't hit every integer percentage exactly)."""
    rows = []
    for i in range(n_total):
        rows.append({"key": f"k{i}", "evaluable": True, "pass": i < n_pass,
                      "weight": weight_each})
    return rows


def test_verdict_band_edges_via_score_archetype_directly():
    # score_archetype is a pure function of (evaluable, pass, weight) -- test the exact
    # rounding/verdict boundary independent of real criteria weight granularity.
    r71 = arche.score_archetype(_synthetic_rows(71, 100))
    assert r71["score"] == 71
    assert r71["verdict"] == "strong_fit"

    r70 = arche.score_archetype(_synthetic_rows(70, 100))
    assert r70["score"] == 70
    assert r70["verdict"] == "partial_fit"

    r50 = arche.score_archetype(_synthetic_rows(50, 100))
    assert r50["score"] == 50
    assert r50["verdict"] == "partial_fit"

    r49 = arche.score_archetype(_synthetic_rows(49, 100))
    assert r49["score"] == 49
    assert r49["verdict"] == "poor_fit"


def test_verdict_strong_fit_sanity_check_with_real_criteria_weights():
    # Integration sanity check (real Graham weights): fail earnings_positive(10) +
    # moderate_pe(15) = 25 fail -> pass weight 75 -> score 75 (> 70 -> strong_fit).
    stock_75 = _stock(
        valuation={"pe": 99.0, "fundamental_discount_pct": 30.0},
        fundamentals={"net_margin": -1.0, "pb": 1.0, "current_ratio": 3.0,
                       "debt_to_equity": 0.1},
        history={"annualDilutedEPS": [
            {"date": "2023", "value": 1.0}, {"date": "2024", "value": 2.0},
            {"date": "2025", "value": 3.0}]},
    )
    r75 = arche.evaluate_stock(stock_75)["archetypes"]["graham"]
    assert r75["score"] == 75
    assert r75["verdict"] == "strong_fit"


# --------------------------------------------------------------------------- likes / concerns


def test_likes_and_concerns_exact_string_match():
    stock = _stock(fundamentals={"net_margin": 55.8}, valuation={"pe": 46.2})
    result = arche.evaluate_stock(stock)["archetypes"]["graham"]
    assert "Profitable on a trailing-twelve-month basis (net margin 55.8%)." in result["likes"]
    assert "P/E of 46.2 exceeds Graham's defensive ceiling of 15." in result["concerns"]


def test_margin_sort_worst_first_in_concerns():
    # 4 failing Buffett criteria with distinct margins, worst (most negative) first.
    # fair_price:         margin = (-50 - (-10)) / 10 = -4.0     (worst)
    # high_roe:           margin = (1 - 15) / 15       = -0.933
    # high_roic:          margin = (6 - 12) / 12        = -0.5
    # gross_margin_moat:  margin = (39 - 40) / 40        = -0.025 (least bad -> capped out)
    stock = _stock(
        valuation={"fundamental_discount_pct": -50.0},
        fundamentals={"roe": 1.0, "roic": 6.0, "gross_margin": 39.0},
    )
    result = arche.evaluate_stock(stock)["archetypes"]["buffett"]
    assert len(result["concerns"]) == 3  # capped at 3; gross_margin_moat (least bad) dropped
    assert result["concerns"][0].startswith("Priced")   # fair_price, worst margin, first
    assert result["concerns"][1].startswith("ROE")       # high_roe, second-worst
    assert result["concerns"][2].startswith("ROIC")      # high_roic, third-worst, last shown


def test_not_evaluable_criterion_produces_exact_warning_and_no_list_membership():
    stock = _stock(valuation={"pe": 10.0}, fundamentals={"net_margin": 5.0})
    result = arche.evaluate_stock(stock)
    lynch = result["archetypes"]["lynch"]
    assert "Room to grow" not in " ".join(lynch["likes"] + lynch["concerns"])
    assert "lynch.room_to_grow: valuation.market_cap unavailable — criterion skipped" \
        in result["warnings"]


# --------------------------------------------------------------------------- build_archetypes bundle


def _site(stocks, generated_at="2026-07-14T22:39:30Z"):
    return {
        "generated_at": generated_at,
        "stocks": stocks,
        "layers": {"L0-energy": [], "L1-chips": list(stocks.keys()), "L2-infra": [],
                   "L3-models": [], "L4-application": []},
    }


def test_build_archetypes_top_level_shape():
    stocks = {"NVDA": _stock(symbol="NVDA", fundamentals={"net_margin": 55.8},
                              valuation={"pe": 46.2})}
    bundle = arche.build_archetypes(_site(stocks), "2026-07-15T00:00:00Z")
    assert bundle["schema_version"] == "archetypes-v1"
    assert bundle["methodology_version"] == "graham-buffett-lynch-v1.0"
    assert bundle["source_class"] == "computed"
    assert bundle["source"] == {"name": "site.json", "path": "web/public/data/site.json",
                                 "generated_at": "2026-07-14T22:39:30Z"}
    assert bundle["min_evaluable_criteria"] == 3
    assert bundle["min_evaluable_weight_pct"] == 50
    assert bundle["universe"]["n_symbols"] == 1
    assert set(bundle["methodology"].keys()) == {"graham", "buffett", "lynch"}
    for key in ("graham", "buffett", "lynch"):
        assert bundle["methodology"][key]["excluded_criteria"]  # non-empty
    assert len(bundle["methodology"]["graham"]["criteria"]) == 7
    assert len(bundle["methodology"]["buffett"]["criteria"]) == 7
    assert len(bundle["methodology"]["lynch"]["criteria"]) == 5
    assert len(bundle["per_stock"]) == 1
    assert bundle["per_stock"][0]["symbol"] == "NVDA"


def test_build_archetypes_top_sorts_desc_symbol_asc_tiebreak_excludes_not_evaluable():
    # Two stocks tie at the same Graham score; a third is not_evaluable and excluded.
    strong_stock = dict(fundamentals={"net_margin": 10.0, "pb": 1.0, "current_ratio": 3.0,
                                       "debt_to_equity": 0.1},
                         valuation={"pe": 10.0, "fundamental_discount_pct": 30.0},
                         history={"annualDilutedEPS": [
                             {"date": "2023", "value": 1.0}, {"date": "2024", "value": 2.0},
                             {"date": "2025", "value": 3.0}]})
    stocks = {
        "AAA": _stock(symbol="AAA", **strong_stock),
        "ZZZ": _stock(symbol="ZZZ", **strong_stock),
        "SPARSE": _stock(symbol="SPARSE", fundamentals={"net_margin": 5.0}),
    }
    bundle = arche.build_archetypes(_site(stocks), "2026-07-15T00:00:00Z")
    graham_top = bundle["top"]["graham"]
    assert [e["symbol"] for e in graham_top[:2]] == ["AAA", "ZZZ"]  # tie -> alpha
    assert "SPARSE" not in [e["symbol"] for e in graham_top]


def test_build_archetypes_counts_sum_to_len_per_stock():
    stocks = {"A": _stock(symbol="A"), "B": _stock(symbol="B", fundamentals={"net_margin": 5.0})}
    bundle = arche.build_archetypes(_site(stocks), "2026-07-15T00:00:00Z")
    for key in ("graham", "buffett", "lynch"):
        assert sum(bundle["counts"][key].values()) == len(bundle["per_stock"]) == 2


def test_build_archetypes_empty_stocks_is_legitimately_sparse():
    bundle = arche.build_archetypes(_site({}), "2026-07-15T00:00:00Z")
    assert bundle["per_stock"] == []
    assert bundle["universe"]["n_symbols"] == 0
    for key in ("graham", "buffett", "lynch"):
        assert bundle["top"][key] == []
        assert bundle["counts"][key] == {"strong_fit": 0, "partial_fit": 0, "poor_fit": 0,
                                          "not_evaluable": 0}
    assert any("no stocks" in w for w in bundle["warnings"])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
