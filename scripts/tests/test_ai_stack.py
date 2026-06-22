"""RED tests for the AI-stack ticker universe (from references/investing-brief.md)."""
from aiinvest import ai_stack


EXPECTED_LAYERS = {"L0-energy", "L1-chips", "L2-infra", "L3-models", "L4-application"}


def test_layers_cover_the_five_stack_levels():
    assert set(ai_stack.LAYERS.keys()) == EXPECTED_LAYERS


def test_every_ticker_is_exchange_prefixed():
    # TradingView america scanner needs EXCHANGE:SYMBOL (e.g. "NASDAQ:NVDA").
    for t in ai_stack.all_tickers():
        assert ":" in t, f"{t} missing exchange prefix"


def test_all_tickers_are_unique():
    tickers = ai_stack.all_tickers()
    assert len(tickers) == len(set(tickers))


def test_nvda_is_in_chips():
    assert "NASDAQ:NVDA" in ai_stack.LAYERS["L1-chips"]


def test_vst_is_in_energy():
    assert "NYSE:VST" in ai_stack.LAYERS["L0-energy"]


def test_hyperscaler_msft_in_infra():
    assert "NASDAQ:MSFT" in ai_stack.LAYERS["L2-infra"]


def test_palantir_in_application():
    assert "NASDAQ:PLTR" in ai_stack.LAYERS["L4-application"]


def test_layer_of_returns_the_layer_key():
    assert ai_stack.layer_of("NASDAQ:NVDA") == "L1-chips"


def test_layer_of_unknown_ticker_is_none():
    assert ai_stack.layer_of("NYSE:ZZZZ") is None
