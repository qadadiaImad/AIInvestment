from aiinvest.market import fetch_market_pulse, INDEX_SYMBOLS

def test_pulse_shape_and_change_and_tnx_yield_direct():
    # Yahoo now quotes ^TNX as the yield directly (e.g. 4.5 = 4.5%), not yield*10.
    fake = {"^GSPC": (5000.0, 4975.0), "^IXIC": (16000.0, 15840.0),
            "^VIX": (13.0, 13.5), "^TNX": (4.5, 4.4)}
    pulse = fetch_market_pulse(fetch=lambda s: fake[s])
    assert set(pulse) == set(INDEX_SYMBOLS)
    assert pulse["sp500"]["change_pct"] == 0.5
    assert pulse["ten_year"]["price"] == 4.5          # yield used directly, no /10
    assert pulse["ten_year"]["change_pct"] == 0.1      # raw yield-point (bps) move, 4.5-4.4
    for v in pulse.values():
        assert v["source_class"] == "xhr-json" and v["retrieved_at"].endswith("Z")

def test_rejects_dirty_quote():
    import pytest
    with pytest.raises(ValueError):
        fetch_market_pulse(fetch=lambda s: (None, 4975.0))
