"""Universe integrity for the Physical-AI / magnet chain (mirrors the quantum tests)."""
import re

from aiinvest import physical_ai_stack as pas

_TICKER = re.compile(r"^[A-Z]+:[A-Z0-9.]+$")


def test_every_ticker_well_formed_and_unique():
    ts = pas.all_tickers()
    assert ts, "universe must not be empty"
    assert len(ts) == len(set(ts))
    for t in ts:
        assert _TICKER.match(t), t


def test_every_exchange_maps_to_a_market_and_country():
    for t in pas.all_tickers():
        assert pas.market_of(t) in {"america", "china", "hongkong", "japan", "australia",
                                    "canada", "uk", "korea", "germany", "belgium"}
        assert len(pas.country_of(t)) == 2


def test_each_ticker_in_exactly_one_layer():
    for t in pas.all_tickers():
        hits = [k for k, v in pas.LAYERS.items() if t in v]
        assert hits == [pas.layer_of(t)], t


def test_layer_keys_are_the_five_chain_stages():
    assert list(pas.LAYERS) == ["P0-upstream", "P1-refining", "P2-magnets", "P3-actuators", "P4-robots"]


def test_by_market_partitions_the_universe():
    groups = pas.by_market()
    flat = [t for ts in groups.values() for t in ts]
    assert sorted(flat) == sorted(pas.all_tickers())
    assert "china" in groups and "america" in groups


def test_giants_are_not_screener_members():
    bare = {t.split(":")[-1] for t in pas.all_tickers()}
    for g in pas.GIANT_NODES:
        assert g["id"] not in bare, g["id"]
        assert g["layer"] in pas.LAYERS
    for p in pas.PRIVATE_NODES:
        assert p["layer"] in pas.LAYERS


def test_known_anchors_present_in_expected_layers():
    assert pas.layer_of("NYSE:MP") == "P1-refining"
    assert pas.layer_of("SZSE:300748") == "P2-magnets"
    assert pas.layer_of("TSE:6324") == "P3-actuators"
    assert pas.layer_of("HKEX:9880") == "P4-robots"
    assert pas.layer_of("ASX:ARU") == "P0-upstream"


def test_gf_symbol_spellings_match_live_conventions():
    assert pas.gf_symbol("SSE:600111") == "SHSE:600111"
    assert pas.gf_symbol("HKEX:6680") == "HKSE:06680"
    assert pas.gf_symbol("KRX:058610") == "XKRX:058610"
    assert pas.gf_symbol("XETR:SHA0") == "XTER:SHA0"
    assert pas.gf_symbol("EURONEXT:MELE") == "XBRU:MELE"
    assert pas.gf_symbol("OTC:REEMF") == "OTCPK:REEMF"
    assert pas.gf_symbol("NYSE:MP") == "MP"
    assert pas.gf_symbol("AMEX:UUUU") == "UUUU"


def test_fundamental_keys_namespace_foreign_listings():
    assert pas.fundamental_key("NYSE:MP") == "MP"
    assert pas.fundamental_key("ASX:LIN") == "ASX_LIN"
    assert pas.fundamental_key("HKEX:6680") == "HKEX_6680"
    keys = [pas.fundamental_key(t) for t in pas.all_tickers()]
    assert len(keys) == len(set(keys))
