"""File-based fixture tests for build_risk.py — no HTTP mocking needed since this
pipeline is network-free (mirrors tests/test_pull_ta.py's fixture style, adapted for
local-file input instead of mocked Yahoo GETs)."""
import datetime
import json
import math

import pytest

import build_risk
from aiinvest import risk


# --------------------------------------------------------------------------- fixture builders


def _closes(n, base=100.0, drift=0.07, amp=3.0, phase=0.0):
    """Deterministic, always-positive, non-constant synthetic close series."""
    return [round(base + i * drift + amp * math.sin((i + phase) / 5.0), 4) for i in range(n)]


def _price_series(closes, start="2024-01-01"):
    start_date = datetime.date.fromisoformat(start)
    return [{"date": (start_date + datetime.timedelta(days=i)).isoformat(), "close": c}
            for i, c in enumerate(closes)]


def _write_price_file(prices_dir, symbol, closes, retrieved_at="2026-07-14T06:00:04Z",
                       start="2024-01-01"):
    series = _price_series(closes, start)
    rec = {"symbol": symbol, "retrieved_at": retrieved_at, "series": series,
           "returns": {"1y": None, "3y": None, "5y": None}}
    (prices_dir / f"{symbol}.json").write_text(json.dumps(rec), encoding="utf-8")
    return series


def _stock_rec(layer, market_cap=None):
    return {"symbol": None, "layer": layer, "valuation": {"market_cap": market_cap},
            "fundamentals": {}, "performance": {}}


def _write_site(data_dir, stocks, layers):
    site = {
        "generated_at": "2026-07-14T09:00:00Z",
        "disclaimer": "test",
        "sources": [],
        "layers": layers,
        "stocks": stocks,
        "capital_web": {"nodes": [], "edges": []},
        "screener": [],
    }
    (data_dir / "site.json").write_text(json.dumps(site), encoding="utf-8")


def _full_layers_map(overrides=None):
    m = {"L0-energy": [], "L1-chips": [], "L2-infra": [], "L3-models": [], "L4-application": []}
    if overrides:
        m.update(overrides)
    return m


def _args(data_dir, out_path, **overrides):
    ap = build_risk.argparse.Namespace(
        data=str(data_dir), out=str(out_path), rf_annual=0.04, window=252, min_bars=60,
        correlation_top_n=15)
    for k, v in overrides.items():
        setattr(ap, k, v)
    return ap


# --------------------------------------------------------------------------- per-stock cases


def test_per_stock_null_when_price_file_missing(tmp_path):
    data_dir = tmp_path / "data"
    prices_dir = data_dir / "prices"
    prices_dir.mkdir(parents=True)
    stocks = {"XYZ": _stock_rec("L1-chips", market_cap=1e9)}
    _write_site(data_dir, stocks, _full_layers_map({"L1-chips": ["XYZ"]}))

    bundle = build_risk.build_bundle(_args(data_dir, tmp_path / "risk.json"))
    entry = next(e for e in bundle["per_stock"] if e["symbol"] == "XYZ")
    assert entry["vol_annualized_pct"] is None
    assert entry["day_change_pct"] is None
    assert entry["market_cap"] == 1e9
    assert "no price history file found for XYZ" in entry["warnings"]


def test_per_stock_ipo_partial_history_nulls_stats_keeps_day_change(tmp_path):
    data_dir = tmp_path / "data"
    prices_dir = data_dir / "prices"
    prices_dir.mkdir(parents=True)
    closes = _closes(40)  # 40 bars -> 39 return bars, < MIN_BARS=60
    _write_price_file(prices_dir, "NEWCO", closes)
    stocks = {"NEWCO": _stock_rec("L4-application")}
    _write_site(data_dir, stocks, _full_layers_map({"L4-application": ["NEWCO"]}))

    bundle = build_risk.build_bundle(_args(data_dir, tmp_path / "risk.json"))
    entry = next(e for e in bundle["per_stock"] if e["symbol"] == "NEWCO")
    assert entry["n_returns_window"] == 39
    assert entry["vol_annualized_pct"] is None
    assert entry["var95_1d_pct"] is None
    assert entry["var99_1d_pct"] is None
    assert entry["sharpe_1y"] is None
    assert entry["max_drawdown_1y_pct"] is None
    assert entry["beta_vs_spy"] is None
    assert entry["day_change_pct"] is not None  # independent of MIN_BARS
    assert any("only 39 return bars, need >=60" in w for w in entry["warnings"])


def test_layer_day_change_survives_zero_metrics_shortcircuit(tmp_path):
    # Regression (adversarial review R2 finding 1): a layer whose constituents all
    # have < MIN_BARS history still has valid day_change_pct; the n_with_metrics==0
    # short-circuit must not null it (it feeds headline.worst_layer + the layer strip).
    data_dir = tmp_path / "data"
    prices_dir = data_dir / "prices"
    prices_dir.mkdir(parents=True)
    _write_price_file(prices_dir, "TINY1", _closes(5))
    _write_price_file(prices_dir, "TINY2", _closes(5))
    stocks = {"TINY1": _stock_rec("L4-application"), "TINY2": _stock_rec("L4-application")}
    _write_site(data_dir, stocks, _full_layers_map({"L4-application": ["TINY1", "TINY2"]}))

    bundle = build_risk.build_bundle(_args(data_dir, tmp_path / "risk.json"))
    layer = next(e for e in bundle["per_layer"] if e["layer"] == "L4-application")
    assert layer["n_with_metrics"] == 0
    assert layer["vol_equal_weighted_pct"] is None          # metrics still null
    assert layer["day_change_pct"] is not None              # but day change survives
    assert layer["day_change_basis"] in ("market_cap", "equal_weighted_fallback")
    assert any("no constituents have usable risk metrics" in w for w in layer["warnings"])


def test_beta_vs_spy_null_without_spy_history(tmp_path):
    data_dir = tmp_path / "data"
    prices_dir = data_dir / "prices"
    prices_dir.mkdir(parents=True)
    _write_price_file(prices_dir, "NVDA", _closes(260))
    stocks = {"NVDA": _stock_rec("L1-chips")}
    _write_site(data_dir, stocks, _full_layers_map({"L1-chips": ["NVDA"]}))
    # deliberately no prices/SPY.json

    bundle = build_risk.build_bundle(_args(data_dir, tmp_path / "risk.json"))
    entry = next(e for e in bundle["per_stock"] if e["symbol"] == "NVDA")
    assert entry["beta_vs_spy"] is None
    assert any("SPY price history unavailable or insufficient" in w for w in entry["warnings"])
    assert any("SPY" in w and "prices/SPY.json not found" in w for w in bundle["warnings"])


# --------------------------------------------------------------------------- per-layer cases


def test_l3_models_layer_entry_no_public_tickers(tmp_path):
    data_dir = tmp_path / "data"
    prices_dir = data_dir / "prices"
    prices_dir.mkdir(parents=True)
    stocks = {"NVDA": _stock_rec("L1-chips")}
    _write_price_file(prices_dir, "NVDA", _closes(260))
    _write_site(data_dir, stocks, _full_layers_map({"L1-chips": ["NVDA"]}))

    bundle = build_risk.build_bundle(_args(data_dir, tmp_path / "risk.json"))
    l3 = next(e for e in bundle["per_layer"] if e["layer"] == "L3-models")
    assert l3["n_constituents"] == 0
    assert l3["n_with_metrics"] == 0
    assert l3["day_change_pct"] is None
    assert l3["vol_cap_weighted_pct"] is None
    assert l3["warnings"] == [
        "L3-models has no public tickers in the AI-stack universe "
        "(private labs only) — no risk aggregate possible"
    ]
    assert len(bundle["per_layer"]) == 5
    assert [e["layer"] for e in bundle["per_layer"]] == [
        "L0-energy", "L1-chips", "L2-infra", "L3-models", "L4-application"]


def test_per_layer_cap_weighted_fallback_when_coverage_thin(tmp_path):
    data_dir = tmp_path / "data"
    prices_dir = data_dir / "prices"
    prices_dir.mkdir(parents=True)
    syms = ["A", "B", "C", "D"]
    for i, s in enumerate(syms):
        _write_price_file(prices_dir, s, _closes(260, phase=i * 3))
    # only 1 of 4 (25%, <50%) has a market_cap -> cap-weighting falls back
    stocks = {
        "A": _stock_rec("L2-infra", market_cap=5e11),
        "B": _stock_rec("L2-infra", market_cap=None),
        "C": _stock_rec("L2-infra", market_cap=None),
        "D": _stock_rec("L2-infra", market_cap=None),
    }
    _write_site(data_dir, stocks, _full_layers_map({"L2-infra": syms}))

    bundle = build_risk.build_bundle(_args(data_dir, tmp_path / "risk.json"))
    layer = next(e for e in bundle["per_layer"] if e["layer"] == "L2-infra")
    assert layer["n_constituents"] == 4
    assert layer["n_with_metrics"] == 4
    assert layer["vol_cap_weighted_basis"] == "equal_weighted_fallback"
    assert layer["vol_cap_weighted_pct"] == pytest.approx(layer["vol_equal_weighted_pct"])
    assert layer["day_change_basis"] == "equal_weighted_fallback"
    assert any("equal_weighted_fallback" in w or "equal-weighted fallback" in w
               for w in layer["warnings"])


# --------------------------------------------------------------------------- correlations


def test_top_stocks_skip_and_fallthrough(tmp_path):
    data_dir = tmp_path / "data"
    prices_dir = data_dir / "prices"
    prices_dir.mkdir(parents=True)
    # BIGCAP ranks #1 by market cap but has insufficient history -> skipped, logged
    _write_price_file(prices_dir, "BIGCAP", _closes(40, phase=1))     # 39 return bars
    _write_price_file(prices_dir, "SMALLCAP", _closes(260, phase=2))  # full history
    stocks = {
        "BIGCAP": _stock_rec("L1-chips", market_cap=9e11),
        "SMALLCAP": _stock_rec("L1-chips", market_cap=1e9),
    }
    _write_site(data_dir, stocks, _full_layers_map({"L1-chips": ["BIGCAP", "SMALLCAP"]}))

    bundle = build_risk.build_bundle(_args(data_dir, tmp_path / "risk.json"))
    top = bundle["correlations"]["top_stocks"]
    assert top["ranked_by"] == "market_cap"
    assert top["order"] == ["SMALLCAP"]
    assert top["candidates_skipped"] == [
        {"symbol": "BIGCAP", "reason": "insufficient history (39 return bars, need >=60)"}
    ]


def test_correlation_layers_degrades_when_spy_missing(tmp_path):
    data_dir = tmp_path / "data"
    prices_dir = data_dir / "prices"
    prices_dir.mkdir(parents=True)
    _write_price_file(prices_dir, "NVDA", _closes(260, phase=1))
    stocks = {"NVDA": _stock_rec("L1-chips")}
    _write_site(data_dir, stocks, _full_layers_map({"L1-chips": ["NVDA"]}))
    # no SPY.json

    bundle = build_risk.build_bundle(_args(data_dir, tmp_path / "risk.json"))
    layers_block = bundle["correlations"]["layers"]
    assert "SPY" not in layers_block["order"]
    assert any("SPY" in w for w in layers_block["warnings"])


def test_l3_models_proxy_series_clears_diagonal_via_hyperscaler_basket(tmp_path):
    data_dir = tmp_path / "data"
    prices_dir = data_dir / "prices"
    prices_dir.mkdir(parents=True)
    # GOOGL/MSFT/AMZN/META all have full history -> L3-models proxy series should clear
    # the >=60-bar diagonal check even though layers["L3-models"] itself is [].
    for i, sym in enumerate(["GOOGL", "MSFT", "AMZN", "META"]):
        _write_price_file(prices_dir, sym, _closes(260, phase=i * 2))
    _write_price_file(prices_dir, "SPY", _closes(260, phase=9))
    stocks = {
        "GOOGL": _stock_rec("L2-infra"), "MSFT": _stock_rec("L2-infra"),
        "AMZN": _stock_rec("L2-infra"), "META": _stock_rec("L2-infra"),
    }
    _write_site(data_dir, stocks,
                _full_layers_map({"L2-infra": ["GOOGL", "MSFT", "AMZN", "META"]}))

    bundle = build_risk.build_bundle(_args(data_dir, tmp_path / "risk.json"))
    layers_block = bundle["correlations"]["layers"]
    assert "L3-models" in layers_block["order"]
    assert layers_block["l3_models_note"] == build_risk.L3_MODELS_NOTE


# --------------------------------------------------------------------------- headline (pure helpers)


def test_headline_worst_layer_ties_broken_alphabetically():
    per_layer = [
        {"layer": "L0-energy", "day_change_pct": -1.0},
        {"layer": "L1-chips", "day_change_pct": -3.0},
        {"layer": "L2-infra", "day_change_pct": -3.0},
        {"layer": "L3-models", "day_change_pct": None},
        {"layer": "L4-application", "day_change_pct": 2.0},
    ]
    worst = build_risk._headline_worst_layer(per_layer)
    assert worst == {"layer": "L1-chips", "day_change_pct": -3.0}


def test_headline_top_correlation_pair_excludes_spy_even_if_highest():
    layers_block = {
        "order": ["L1-chips", "L2-infra", "L3-models", "SPY"],
        "matrix": [
            [1.0, 0.55, 0.40, 0.99],   # SPY correlation with L1-chips is the highest raw value
            [0.55, 1.0, 0.71, 0.50],
            [0.40, 0.71, 1.0, 0.30],
            [0.99, 0.50, 0.30, 1.0],
        ],
    }
    pair = build_risk._headline_top_correlation_pair(layers_block)
    # highest off-diagonal among the 3 REAL layers only is L2-infra/L3-models = 0.71
    assert pair == {"a": "L2-infra", "b": "L3-models", "value": 0.71}
    assert "SPY" not in (pair["a"], pair["b"])


# --------------------------------------------------------------------------- empty / validation


def test_build_risk_no_site_json_writes_minimal_bundle_and_returns_0(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    out = tmp_path / "risk.json"
    rc = build_risk.main(["--data", str(data_dir), "--out", str(out)])
    assert rc == 0
    bundle = json.loads(out.read_text())
    assert bundle["per_stock"] == []
    assert len(bundle["per_layer"]) == 5
    assert bundle["correlations"]["layers"]["order"] == []
    assert bundle["correlations"]["top_stocks"]["order"] == []
    assert "site.json not found — risk universe empty" in bundle["warnings"]


def test_validator_rejects_dirty_sentinel_strings_and_non_finite_floats_by_path():
    bad = {"per_stock": [{"symbol": "X", "vol_annualized_pct": float("nan")},
                          {"symbol": "Y", "market_cap": "n/a"}]}
    problems = build_risk.validate_bundle(bad)
    assert any("non-finite float" in p and "vol_annualized_pct" in p for p in problems)
    assert any("dirty sentinel string" in p and "market_cap" in p for p in problems)


# --------------------------------------------------------------------------- full contract shape


TOP_LEVEL_KEYS = {
    "generated_at", "schema_version", "source_class", "disclaimer", "params",
    "prices_source", "benchmark_symbol", "universe", "warnings", "per_stock",
    "per_layer", "correlations", "headline",
}
PER_STOCK_KEYS = {
    "symbol", "layer", "prices_retrieved_at", "last_price_date", "n_bars_total",
    "n_returns_window", "day_change_pct", "vol_annualized_pct", "var95_1d_pct",
    "var99_1d_pct", "sharpe_1y", "max_drawdown_1y_pct", "beta_vs_spy", "market_cap",
    "warnings",
}
PER_LAYER_KEYS = {
    "layer", "n_constituents", "n_with_metrics", "day_change_pct", "day_change_basis",
    "vol_equal_weighted_pct", "vol_cap_weighted_pct", "vol_cap_weighted_basis",
    "median_var95_1d_pct", "median_var99_1d_pct", "worst_var95_1d_pct",
    "worst_var95_symbol", "best_sharpe_symbol", "best_sharpe_1y", "worst_sharpe_symbol",
    "worst_sharpe_1y", "worst_drawdown_symbol", "worst_drawdown_1y_pct", "warnings",
}


def test_contract_shape_matches_schema_end_to_end(tmp_path):
    data_dir = tmp_path / "data"
    prices_dir = data_dir / "prices"
    prices_dir.mkdir(parents=True)

    for i, sym in enumerate(["NVDA", "GOOGL", "AMZN"]):
        _write_price_file(prices_dir, sym, _closes(260, phase=i * 4))
    _write_price_file(prices_dir, "SPY", _closes(260, phase=9))

    stocks = {
        "NVDA": _stock_rec("L1-chips", market_cap=3.1e12),
        "GOOGL": _stock_rec("L2-infra", market_cap=2.2e12),
        "AMZN": _stock_rec("L2-infra", market_cap=2.0e12),
    }
    layers = _full_layers_map({"L1-chips": ["NVDA"], "L2-infra": ["GOOGL", "AMZN"]})
    _write_site(data_dir, stocks, layers)

    ga = {"macro": {"snapshot": {"dff": 4.33, "dgs10": 4.25, "elec": 0.14,
                                  "retrieved_at": "2026-07-14T00:00:00Z"}}}
    (data_dir / "graph_analysis.json").write_text(json.dumps(ga), encoding="utf-8")

    out = tmp_path / "risk.json"
    rc = build_risk.main(["--data", str(data_dir), "--out", str(out)])
    assert rc == 0

    bundle = json.loads(out.read_text())
    assert set(bundle.keys()) == TOP_LEVEL_KEYS
    assert bundle["schema_version"] == "risk-desk-v1"
    assert bundle["source_class"] == "computed"
    assert bundle["benchmark_symbol"] == "SPY"
    assert bundle["params"]["risk_free_rate_annual"] == pytest.approx(0.0433)
    assert bundle["params"]["risk_free_source"] == "graph_analysis.json:macro.snapshot.dff"
    assert bundle["universe"]["n_symbols_total"] == 3

    assert len(bundle["per_stock"]) == 3
    for entry in bundle["per_stock"]:
        assert set(entry.keys()) == PER_STOCK_KEYS

    assert len(bundle["per_layer"]) == 5
    for entry in bundle["per_layer"]:
        assert set(entry.keys()) == PER_LAYER_KEYS

    corr = bundle["correlations"]
    assert set(corr.keys()) == {"layers", "top_stocks"}
    assert set(corr["layers"].keys()) == {
        "order", "matrix", "l3_models_note", "window_trading_days", "min_overlap_days",
        "warnings"}
    assert set(corr["top_stocks"].keys()) == {
        "order", "ranked_by", "matrix", "window_trading_days", "min_overlap_days",
        "candidates_considered", "candidates_skipped", "warnings"}

    assert set(bundle["headline"].keys()) == {
        "worst_layer", "universe_var95_1d_pct", "top_correlation_pair"}

    dumped = json.dumps(bundle)
    assert '"raw"' not in dumped
    assert '"dirty"' not in dumped


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
