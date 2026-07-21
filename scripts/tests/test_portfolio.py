"""Hand-computable fixtures for aiinvest.portfolio + build_portfolio.py (mirrors the style
of tests/test_risk.py / tests/test_build_risk.py). Every expected number derived in a
comment. See docs/superpowers/specs/2026-07-15-portfolio-design.md §8 for the fixture plan.
"""
import json
import math

import pytest

from aiinvest import portfolio
from aiinvest import risk


# =========================================================================================
# Fixture A — the 2-position + cash worked example (spec §3)
#
#   NVDA: qty=10, cost=400/sh -> cost_basis_total=4000; price 500->550 (day +10%)
#     mv = 10*550 = 5500; pnl = 5500-4000 = 1500 -> 1500/4000*100 = 37.5%
#     day_chg_usd = 10*(550-500) = 500; day_chg_pct = (550-500)/500*100 = 10.0
#   MSFT: qty=20, cost=250/sh -> cost_basis_total=5000; price 300->294 (day -2%)
#     mv = 20*294 = 5880; pnl = 5880-5000 = 880 -> 880/5000*100 = 17.6%
#     day_chg_usd = 20*(294-300) = -120; day_chg_pct = (294-300)/300*100 = -2.0
#   cash = 1000
#   total_value = 5500+5880+1000 = 12380; invested = 11380
#   weight NVDA = 5500/12380*100 = 44.42649...  weight MSFT = 5880/12380*100 = 47.49596...
#   cash_weight = 1000/12380*100 = 8.077544...
#   total_cost_basis = 9000; total_unrealized_pnl = 2380 -> 2380/9000*100 = 26.4444...
#   day_pnl = 500-120 = 380 -> 380/(12380-380)*100 = 380/12000*100 = 3.1666...
#   top1 = 5880/11380*100 = 51.6696...  top3 = 100.0 (only 2 positions)
#   hhi = (5500/11380)^2 + (5880/11380)^2 = 0.233567...+0.266980... = 0.500548...
# =========================================================================================


def _nvda_merged():
    return {"symbol": "NVDA", "quantity": 10.0, "lots_merged": 1,
            "cost_basis_per_share": 400.0, "acquired_date": "2024-01-10",
            "note": "core position", "warnings": []}


def _nvda_price_info():
    return {"last_price": 550.0, "price_as_of": "2026-07-14", "price_source": "prices_file",
            "prev_close": 500.0}


def _msft_merged():
    return {"symbol": "MSFT", "quantity": 20.0, "lots_merged": 1,
            "cost_basis_per_share": 250.0, "acquired_date": "2024-02-01",
            "note": None, "warnings": []}


def _msft_price_info():
    return {"last_price": 294.0, "price_as_of": "2026-07-14", "price_source": "prices_file",
            "prev_close": 300.0}


TOTAL_VALUE_A = 12380.0


def _fixture_a_positions():
    nvda = portfolio.compute_position(_nvda_merged(), _nvda_price_info(), "L1-chips",
                                       TOTAL_VALUE_A)
    msft = portfolio.compute_position(_msft_merged(), _msft_price_info(), "L2-infra",
                                       TOTAL_VALUE_A)
    return [nvda, msft]


def test_compute_position_nvda_matches_hand_calc():
    nvda = _fixture_a_positions()[0]
    assert nvda["market_value_usd"] == pytest.approx(5500.0)
    assert nvda["cost_basis_total_usd"] == pytest.approx(4000.0)
    assert nvda["unrealized_pnl_usd"] == pytest.approx(1500.0)
    assert nvda["unrealized_pnl_pct"] == pytest.approx(37.5)
    assert nvda["day_change_pct"] == pytest.approx(10.0)
    assert nvda["day_change_usd"] == pytest.approx(500.0)
    assert nvda["weight_pct"] == pytest.approx(44.4265, abs=1e-3)
    assert nvda["warnings"] == []


def test_compute_position_msft_matches_hand_calc():
    msft = _fixture_a_positions()[1]
    assert msft["market_value_usd"] == pytest.approx(5880.0)
    assert msft["cost_basis_total_usd"] == pytest.approx(5000.0)
    assert msft["unrealized_pnl_usd"] == pytest.approx(880.0)
    assert msft["unrealized_pnl_pct"] == pytest.approx(17.6)
    assert msft["day_change_pct"] == pytest.approx(-2.0)
    assert msft["day_change_usd"] == pytest.approx(-120.0)
    assert msft["weight_pct"] == pytest.approx(47.4959, abs=1e-3)
    assert msft["warnings"] == []


def test_compute_aggregates_totals():
    agg = portfolio.compute_aggregates(_fixture_a_positions(), cash_usd=1000.0)
    assert agg["total_value_usd"] == pytest.approx(12380.0)
    assert agg["invested_value_usd"] == pytest.approx(11380.0)
    assert agg["cash_weight_pct"] == pytest.approx(8.0775, abs=1e-3)
    assert agg["total_cost_basis_usd"] == pytest.approx(9000.0)
    assert agg["total_unrealized_pnl_usd"] == pytest.approx(2380.0)
    assert agg["total_unrealized_pnl_pct"] == pytest.approx(26.4444, abs=1e-3)
    assert agg["day_pnl_usd"] == pytest.approx(380.0)
    assert agg["day_pnl_pct"] == pytest.approx(3.1667, abs=1e-3)
    assert agg["n_positions"] == 2
    assert agg["n_positions_priced"] == 2
    assert agg["n_positions_unpriced"] == 0


def test_compute_aggregates_concentration():
    agg = portfolio.compute_aggregates(_fixture_a_positions(), cash_usd=1000.0)
    c = agg["concentration"]
    assert c["top1_weight_pct"] == pytest.approx(51.6696, abs=1e-3)
    assert c["top3_weight_pct"] == pytest.approx(100.0, abs=1e-6)
    assert c["hhi"] == pytest.approx(0.50055, abs=1e-4)
    assert c["basis"] == "invested_value_excluding_cash"


def test_layer_exposure_buckets_sum_to_100():
    agg = portfolio.compute_aggregates(_fixture_a_positions(), cash_usd=1000.0)
    by_layer = {e["layer"]: e for e in agg["layer_exposure"]}
    assert by_layer["L1-chips"]["weight_pct"] == pytest.approx(44.4265, abs=1e-3)
    assert by_layer["L2-infra"]["weight_pct"] == pytest.approx(47.4959, abs=1e-3)
    assert by_layer["cash"]["weight_pct"] == pytest.approx(8.0775, abs=1e-3)
    assert by_layer["unclassified"]["weight_pct"] == pytest.approx(0.0)
    assert by_layer["L0-energy"]["weight_pct"] == pytest.approx(0.0)
    assert by_layer["L3-models"]["weight_pct"] == pytest.approx(0.0)
    assert by_layer["L4-application"]["weight_pct"] == pytest.approx(0.0)
    total_pct = sum(e["weight_pct"] for e in agg["layer_exposure"])
    assert total_pct == pytest.approx(100.0, abs=1e-2)


# =========================================================================================
# Fixture B — validation / merge rules (§1)
# =========================================================================================


def test_validate_positions_drops_nonpositive_quantity():
    raw = [{"symbol": "AAA", "quantity": 0}, {"symbol": "BBB", "quantity": -5},
           {"symbol": "CCC", "quantity": 10}]
    clean, warnings = portfolio.validate_positions(raw)
    assert [r["symbol"] for r in clean] == ["CCC"]
    assert any("AAA" in w and "dropped" in w for w in warnings)
    assert any("BBB" in w and "dropped" in w for w in warnings)


def test_validate_positions_drops_missing_symbol():
    raw = [{"quantity": 10}, {"symbol": "", "quantity": 5}, {"symbol": "GOOD", "quantity": 1}]
    clean, warnings = portfolio.validate_positions(raw)
    assert [r["symbol"] for r in clean] == ["GOOD"]
    assert len([w for w in warnings if "missing/empty symbol" in w]) == 2


def test_validate_positions_keeps_row_with_missing_cost_basis():
    raw = [{"symbol": "NOCOST", "quantity": 5}]
    clean, warnings = portfolio.validate_positions(raw)
    assert len(clean) == 1
    row = clean[0]
    assert row["cost_basis_per_share"] is None
    assert any("cost_basis_per_share" in w for w in row["warnings"])
    # not a drop reason, so it should NOT show up in the batch-level drop warnings
    assert not any("NOCOST" in w for w in warnings)


def test_merge_lots_weighted_average_cost_basis():
    clean = [
        {"symbol": "NVDA", "quantity": 5.0, "cost_basis_per_share": 400.0,
         "acquired_date": "2024-03-01", "note": None, "warnings": []},
        {"symbol": "NVDA", "quantity": 5.0, "cost_basis_per_share": 500.0,
         "acquired_date": "2024-01-10", "note": None, "warnings": []},
    ]
    merged = portfolio.merge_lots(clean)
    assert len(merged) == 1
    m = merged[0]
    assert m["quantity"] == pytest.approx(10.0)
    # (5*400 + 5*500) / 10 = 450.0 exactly
    assert m["cost_basis_per_share"] == pytest.approx(450.0)
    assert m["lots_merged"] == 2
    assert any("2 lots merged" in w for w in m["warnings"])


def test_merge_lots_earliest_acquired_date_wins():
    clean = [
        {"symbol": "NVDA", "quantity": 5.0, "cost_basis_per_share": 400.0,
         "acquired_date": "2024-03-01", "note": None, "warnings": []},
        {"symbol": "NVDA", "quantity": 5.0, "cost_basis_per_share": 500.0,
         "acquired_date": "2024-01-10", "note": None, "warnings": []},
    ]
    merged = portfolio.merge_lots(clean)
    assert merged[0]["acquired_date"] == "2024-01-10"


def test_unknown_symbol_never_dropped():
    # No site.json entry, no price file -> resolve_price returns all-None PriceInfo.
    unknown_merged = {"symbol": "ZZZZ", "quantity": 3.0, "lots_merged": 1,
                       "cost_basis_per_share": 10.0, "acquired_date": None, "note": None,
                       "warnings": []}
    price_info = portfolio.resolve_price("ZZZZ", None, None)
    pos = portfolio.compute_position(unknown_merged, price_info, None, TOTAL_VALUE_A)
    assert pos["last_price"] is None
    assert pos["market_value_usd"] is None
    assert pos["weight_pct"] is None
    assert pos["layer"] is None
    assert any("no price data available" in w for w in pos["warnings"])

    # excluded from every dollar aggregate -> aggregates equal Fixture A's values exactly
    positions_with_unknown = _fixture_a_positions() + [pos]
    agg = portfolio.compute_aggregates(positions_with_unknown, cash_usd=1000.0)
    agg_baseline = portfolio.compute_aggregates(_fixture_a_positions(), cash_usd=1000.0)
    assert agg["total_value_usd"] == pytest.approx(agg_baseline["total_value_usd"])
    assert agg["invested_value_usd"] == pytest.approx(agg_baseline["invested_value_usd"])
    assert agg["n_positions"] == 3
    assert agg["n_positions_priced"] == 2
    assert agg["n_positions_unpriced"] == 1


def test_resolve_price_prices_file_tier():
    prices_json = {"series": [{"date": "2026-07-13", "close": 500.0},
                               {"date": "2026-07-14", "close": 550.0}]}
    info = portfolio.resolve_price("NVDA", prices_json, {"valuation": {"price": 999.0},
                                                          "as_of": "2026-07-01"})
    assert info["last_price"] == pytest.approx(550.0)
    assert info["prev_close"] == pytest.approx(500.0)
    assert info["price_source"] == "prices_file"
    assert info["price_as_of"] == "2026-07-14"


def test_resolve_price_site_json_fallback_tier():
    info = portfolio.resolve_price("NVDA", None, {"valuation": {"price": 555.0},
                                                    "as_of": "2026-07-01"})
    assert info["last_price"] == pytest.approx(555.0)
    assert info["prev_close"] is None
    assert info["price_source"] == "site_json_fallback"
    assert info["price_as_of"] == "2026-07-01"


def test_resolve_price_none_tier():
    info = portfolio.resolve_price("ZZZZ", None, None)
    assert info == {"last_price": None, "price_as_of": None, "price_source": None,
                     "prev_close": None}


# =========================================================================================
# Fixture C — day-change $/% formula divergence (regression, §2 correctness note)
#
# Construct a case where market_value_usd * day_change_pct/100 != quantity*(last-prev).
# qty=100, prev=100 -> last=110 (day_change_pct = +10%). Suppose cost basis pushes
# market_value used for a NAIVE calc to be computed against a DIFFERENT total_value_usd
# denominator than "quantity*last" — but the real divergence is structural: mv is always
# priced at TODAY's close (last), while day_change_pct is relative to YESTERDAY's close
# (prev). The naive product mv*pct/100 = qty*last*(last-prev)/prev, which only equals
# qty*(last-prev) when last==prev (day_change_pct==0) or trivially matches by coincidence.
# Pick numbers where they clearly diverge:
#   qty=100, prev=100, last=150 (day +50%)
#   correct day_change_usd = 100*(150-100) = 5000
#   naive (WRONG) formula: mv*pct/100 = (100*150)*(50)/100 = 15000*0.5 = 7500 != 5000
# =========================================================================================


def test_day_change_usd_uses_prev_close_not_current_market_value():
    merged = {"symbol": "DIVX", "quantity": 100.0, "lots_merged": 1,
              "cost_basis_per_share": None, "acquired_date": None, "note": None,
              "warnings": []}
    price_info = {"last_price": 150.0, "price_as_of": "2026-07-14",
                  "price_source": "prices_file", "prev_close": 100.0}
    pos = portfolio.compute_position(merged, price_info, None, total_value_usd=15000.0)

    naive_wrong = pos["market_value_usd"] * pos["day_change_pct"] / 100
    assert pos["day_change_usd"] == pytest.approx(5000.0)
    assert naive_wrong == pytest.approx(7500.0)
    assert pos["day_change_usd"] != pytest.approx(naive_wrong)
    # sanity on the correct formula directly
    assert pos["day_change_usd"] == pytest.approx(100.0 * (150.0 - 100.0))


# =========================================================================================
# Fixture D — risk-series construction invariants (§4; mirrors test_risk.py's
# _alternating_60() style)
# =========================================================================================


def _dates(n, start="2024-01-01"):
    import datetime
    d0 = datetime.date.fromisoformat(start)
    return [(d0 + datetime.timedelta(days=i)).isoformat() for i in range(n)]


def _alternating_60_map(start="2024-01-01"):
    ds = _dates(60, start)
    return {d: (0.01 if i % 2 == 0 else -0.01) for i, d in enumerate(ds)}


def _drift_60_map(start="2024-01-01", base=0.001, amp=0.01):
    ds = _dates(60, start)
    return {d: round(base + amp * math.sin(i / 5.0), 6) for i, d in enumerate(ds)}


def _priced_position(symbol, mv, price_source="prices_file"):
    return {"symbol": symbol, "market_value_usd": mv, "price_source": price_source,
            "layer": None, "day_change_usd": None}


def test_portfolio_series_equals_shared_series_when_holdings_identical():
    shared = _drift_60_map()
    per_symbol_full_ret = {"AAA": dict(shared), "BBB": dict(shared)}
    positions = [_priced_position("AAA", 5000.0), _priced_position("BBB", 5000.0)]

    window_vals, dates, included, coverage_pct = portfolio.build_portfolio_return_series(
        positions, per_symbol_full_ret, window=252, min_bars=60)

    assert set(included) == {"AAA", "BBB"}
    assert coverage_pct == pytest.approx(100.0)
    assert dates == sorted(shared.keys())
    for d, v in zip(dates, window_vals):
        assert v == pytest.approx(shared[d])


def test_portfolio_series_cancels_to_zero_for_offsetting_equal_weight_holdings():
    ds = _dates(60)
    up = {d: 0.01 for d in ds}
    down = {d: -0.01 for d in ds}
    per_symbol_full_ret = {"UP": up, "DOWN": down}
    positions = [_priced_position("UP", 5000.0), _priced_position("DOWN", 5000.0)]

    window_vals, dates, included, coverage_pct = portfolio.build_portfolio_return_series(
        positions, per_symbol_full_ret, window=252, min_bars=60)

    assert len(window_vals) == 60
    for v in window_vals:
        assert v == pytest.approx(0.0, abs=1e-12)
    # proof this glue feeds risk.py correctly: zero-variance -> sharpe_ratio is None
    assert risk.sharpe_ratio(window_vals) is None
    # vol is well-defined (0.0) since n>=MIN_BARS
    assert risk.annualized_vol_pct(window_vals) == pytest.approx(0.0, abs=1e-9)


def test_beta_is_one_when_portfolio_series_equals_spy_series():
    shared = _drift_60_map()
    per_symbol_full_ret = {"AAA": dict(shared)}
    positions = [_priced_position("AAA", 10000.0)]

    risk_dict = portfolio.compute_risk(positions, per_symbol_full_ret, spy_full_ret=shared,
                                        rf_annual=0.04, window=252, min_bars=60)
    assert risk_dict["beta_vs_spy"] == pytest.approx(1.0, abs=1e-9)


def test_max_pairwise_correlation_is_one_for_identical_top2_holdings():
    shared = _drift_60_map()
    per_symbol_full_ret = {"AAA": dict(shared), "BBB": dict(shared)}
    included_by_weight = ["BBB", "AAA"]  # BBB heavier weight, sorted desc by caller
    result = portfolio.top_pairwise_correlation(included_by_weight, per_symbol_full_ret,
                                                 top_n=5, window=252, min_bars=60)
    assert result is not None
    assert result["value"] == pytest.approx(1.0, abs=1e-9)
    assert {result["a"], result["b"]} == {"AAA", "BBB"}
    # tie-break alphabetical: a < b
    assert result["a"] < result["b"]


def test_series_excludes_holding_below_min_bars():
    good = _drift_60_map()
    thin_ds = _dates(40)
    thin = {d: 0.001 for d in thin_ds}
    per_symbol_full_ret = {"GOOD": good, "THIN": thin}
    positions = [_priced_position("GOOD", 9000.0), _priced_position("THIN", 1000.0)]

    risk_dict = portfolio.compute_risk(positions, per_symbol_full_ret, spy_full_ret=None,
                                        rf_annual=0.04, window=252, min_bars=60)
    coverage = risk_dict["series_coverage"]
    assert coverage["n_holdings_included"] == 1
    assert coverage["n_holdings_total_priced"] == 2
    # weight_coverage_pct = 9000/10000*100 = 90.0
    assert coverage["weight_coverage_pct"] == pytest.approx(90.0)
    excluded_syms = {e["symbol"]: e["reason"] for e in coverage["excluded"]}
    assert "THIN" in excluded_syms
    assert "insufficient history (40 bars, need >=60)" in excluded_syms["THIN"]


def test_weight_coverage_warning_below_80pct():
    good = _drift_60_map()
    thin_ds = _dates(40)
    thin = {d: 0.001 for d in thin_ds}
    per_symbol_full_ret = {"GOOD": good, "THIN": thin}
    # GOOD only 70% of priced value -> coverage 70% < 80%
    positions = [_priced_position("GOOD", 7000.0), _priced_position("THIN", 3000.0)]

    risk_dict = portfolio.compute_risk(positions, per_symbol_full_ret, spy_full_ret=None,
                                        rf_annual=0.04, window=252, min_bars=60)
    assert risk_dict["series_coverage"]["weight_coverage_pct"] == pytest.approx(70.0)
    assert any("covers only" in w and "70.0%" in w for w in risk_dict["warnings"])


def test_risk_block_null_when_no_holding_qualifies():
    positions = [_priced_position("ZZZZ", 1000.0, price_source="site_json_fallback")]
    risk_dict = portfolio.compute_risk(positions, per_symbol_full_ret={}, spy_full_ret=None,
                                        rf_annual=0.04, window=252, min_bars=60)
    assert risk_dict["vol_annualized_pct"] is None
    assert risk_dict["var95_1d_pct"] is None
    assert risk_dict["sharpe_1y"] is None
    assert risk_dict["beta_vs_spy"] is None
    assert risk_dict["max_pairwise_correlation"] is None
    assert risk_dict["series_coverage"]["n_holdings_included"] == 0
    assert len(risk_dict["warnings"]) == 1
    assert "no holdings have sufficient price history" in risk_dict["warnings"][0]
    assert risk_dict["methodology_note"] == portfolio.METHODOLOGY_NOTE


def test_methodology_note_is_verbatim_and_mandatory():
    positions = [_priced_position("ZZZZ", 1000.0, price_source="site_json_fallback")]
    risk_dict = portfolio.compute_risk(positions, per_symbol_full_ret={}, spy_full_ret=None,
                                        rf_annual=0.04)
    assert "fixed-weight, as-if-held-at-current-composition" in risk_dict["methodology_note"]
    assert "weight_coverage_pct" in risk_dict["methodology_note"]


# =========================================================================================
# Fixture E — empty-state / degradation (build_portfolio.py integration)
# =========================================================================================


def test_build_portfolio_missing_positions_file_produces_empty_bundle(tmp_path):
    import build_portfolio

    data_dir = tmp_path / "data"
    (data_dir / "prices").mkdir(parents=True)
    (data_dir / "site.json").write_text(json.dumps({
        "generated_at": "2026-07-14T06:05:00Z", "stocks": {}, "layers": {},
    }), encoding="utf-8")

    args = build_portfolio.build_arg_namespace(
        positions=str(tmp_path / "nonexistent" / "positions.json"),
        data=str(data_dir), out=str(tmp_path / "out" / "portfolio.json"),
        rf_annual=0.04, window=252, min_bars=60, top_n_correlation=5,
    )
    bundle = build_portfolio.build_bundle(args)

    assert bundle["positions_source"]["found"] is False
    assert bundle["positions"] == []
    assert bundle["aggregates"] is None
    assert bundle["risk"] is None
    assert bundle["schema_version"] == "portfolio-v1"
    assert any("no positions file found" in w for w in bundle["warnings"])

    rc = build_portfolio.main([
        "--positions", str(tmp_path / "nonexistent" / "positions.json"),
        "--data", str(data_dir), "--out", str(tmp_path / "out" / "portfolio.json"),
    ])
    assert rc == 0
    written = json.loads((tmp_path / "out" / "portfolio.json").read_text(encoding="utf-8"))
    assert written["positions_source"]["found"] is False


def test_build_portfolio_writes_to_web_data_not_public():
    import build_portfolio
    default_out = build_portfolio._default_out_path()
    assert "web" + "/data" in default_out.replace("\\", "/")
    assert "web/public/data" not in default_out.replace("\\", "/")
    assert default_out.replace("\\", "/").endswith("web/data/portfolio.json")
