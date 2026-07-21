"""RED tests for the halal ruleset engine (pure computation, no I/O)."""
from aiinvest import halal


def _env(value, retrieved_at="2026-07-21T14:00:00Z"):
    return {"value": value, "raw": value, "unit": "usd", "dirty": False,
            "retrieved_at": retrieved_at, "source": "tradingview",
            "source_url": "u", "source_class": "api"}


# NVDA live values from the 2026-07-21 field probe (workflow wf_b855afce-b1a).
NVDA_METRICS = {
    "close": _env(200.0),
    "market_cap_basic": _env(4919375940781.0),
    "total_assets_fq": _env(259474000000.0),
    "total_debt_fq": _env(12814000000.0),
    "cash_n_short_term_invest_fq": _env(80572000000.0),
    "total_revenue_ttm": _env(253491000000.0),
    "total_revenue_fy": _env(215938000000.0),
    "receivables_turnover_fy": _env(7.0188),
}


def test_standards_registry_shape():
    keys = [s["key"] for s in halal.STANDARDS]
    assert keys == ["AAOIFI", "FTSE", "MSCI"]
    for s in halal.STANDARDS:
        assert s["activity_threshold_pct"] == 5.0
        for t in s["tests"]:
            assert t["citation"], f"{t['id']} missing citation"
            assert 0 < t["threshold"] < 1


def test_aaoifi_thresholds_are_30pct_of_market_cap():
    aaoifi = halal.STANDARDS[0]
    assert [t["threshold"] for t in aaoifi["tests"]] == [0.30, 0.30]
    assert all(t["denominator"] == "market_cap" for t in aaoifi["tests"])


def test_ftse_msci_use_total_assets_denominator():
    for s in halal.STANDARDS[1:]:
        assert all(t["denominator"] == "total_assets" for t in s["tests"])


def test_inputs_from_metrics_extracts_and_derives():
    inp = halal.inputs_from_metrics(NVDA_METRICS)
    assert inp["total_debt"] == 12814000000.0
    assert inp["market_cap"] == 4919375940781.0
    # receivables proxy = revenue_fy / turnover_fy  (≈ 30.77B for NVDA)
    assert abs(inp["receivables"] - 215938000000.0 / 7.0188) < 1e6
    assert inp["inputs_asof"] == "2026-07-21T14:00:00Z"


def test_inputs_missing_turnover_gives_none_receivables():
    m = dict(NVDA_METRICS)
    del m["receivables_turnover_fy"]
    assert halal.inputs_from_metrics(m)["receivables"] is None


def test_compute_test_nvda_aaoifi_debt_passes_with_margin():
    aaoifi_debt = halal.STANDARDS[0]["tests"][0]
    r = halal.compute_test(aaoifi_debt, halal.inputs_from_metrics(NVDA_METRICS))
    assert r["status"] == "pass"
    assert abs(r["ratio"] - 0.0026) < 0.0005          # ≈0.26%, golden from live probe
    assert abs(r["margin"] - (0.30 - r["ratio"])) < 1e-9


def test_compute_test_missing_input_is_unknown_never_pass():
    aaoifi_debt = halal.STANDARDS[0]["tests"][0]
    inp = halal.inputs_from_metrics(NVDA_METRICS)
    inp["total_debt"] = None
    r = halal.compute_test(aaoifi_debt, inp)
    assert r["status"] == "unknown"
    assert r["ratio"] is None


def test_compute_test_zero_denominator_is_unknown():
    aaoifi_debt = halal.STANDARDS[0]["tests"][0]
    inp = halal.inputs_from_metrics(NVDA_METRICS)
    inp["market_cap"] = 0.0
    assert halal.compute_test(aaoifi_debt, inp)["status"] == "unknown"


def test_utility_debt_load_fails_aaoifi_debt_test():
    # Structural expectation from the spec: heavy-leverage utility profile.
    # Synthetic values shaped like SO: debt ~60B vs mcap ~90B -> 66% > 30%.
    inp = {"total_debt": 60e9, "market_cap": 90e9, "cash": 1e9,
           "receivables": 3e9, "total_assets": 140e9, "revenue_ttm": 27e9,
           "close": 80.0, "inputs_asof": "2026-07-21T14:00:00Z"}
    r = halal.compute_test(halal.STANDARDS[0]["tests"][0], inp)
    assert r["status"] == "fail"
    assert r["margin"] < 0
