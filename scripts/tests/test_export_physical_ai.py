import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import export_physical_ai as ex


def _batch():
    def env(v):
        return {"value": v}
    return {"batch_metadata": {"fx": {"rates": {"GBP": 0.75}}}, "financial_data": {
        "RSW": {"symbol": "RSW", "ticker": "LSE:RSW", "stack_layer": "P3-actuators", "market": "uk",
                "country": "GB", "currency": "GBX", "as_of": "t",
                "metrics": {"description": env("Renishaw plc"), "close": env(5535.0),
                            "market_cap_usd": env(5e9), "Perf.Y": env(52.7)}},
        "MP": {"symbol": "MP", "ticker": "NYSE:MP", "stack_layer": "P1-refining", "market": "america",
               "country": "US", "currency": "USD", "as_of": "t",
               "metrics": {"description": env("MP Materials"), "close": env(49.72), "market_cap_usd": env(8.85e9)}},
    }}


def test_pence_price_is_normalised_to_pounds_before_discount():
    assert ex.local_price(5535.0, "GBX") == (55.35, "GBP")
    bundle = ex.build(_batch(), {"LSE_RSW": {"fundamental_value": 42.63}, "MP": {"fundamental_value": 46.53}})
    rsw = bundle["stocks"]["RSW"]["valuation"]
    assert rsw["price"] == 55.35 and rsw["currency"] == "GBP"
    assert -40 < rsw["fundamental_discount_pct"] < -20  # 42.63 vs 55.35, not vs 5535
    mp = bundle["stocks"]["MP"]["valuation"]
    assert mp["fundamental_value"] == 46.53 and mp["currency"] == "USD"


def test_fundamentals_are_looked_up_by_namespaced_key():
    # a bare "RSW" record must NOT be attached to LSE:RSW
    bundle = ex.build(_batch(), {"RSW": {"fundamental_value": 1.0}})
    assert "fundamental_value" not in bundle["stocks"]["RSW"]["valuation"]


def test_screener_rows_carry_country_currency_and_sector():
    bundle = ex.build(_batch(), {})
    row = next(r for r in bundle["screener"] if r["symbol"] == "RSW")
    assert row["country"] == "GB" and row["currency"] == "GBP" and row["sector"] == "PhysicalAI"
