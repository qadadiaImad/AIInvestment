"""RED tests for the quantum-sector ticker universe (mirrors test_ai_stack.py)."""
from aiinvest import quantum_stack as qs


EXPECTED_LAYERS = {"Q1-hardware", "Q3-software", "Q4-security", "Q5-applications"}


def test_sector_is_quantum():
    assert qs.SECTOR == "Quantum"


def test_layers_cover_the_quantum_screener_levels():
    assert set(qs.LAYERS.keys()) == EXPECTED_LAYERS


def test_every_ticker_is_exchange_prefixed():
    for t in qs.all_tickers():
        assert ":" in t, f"{t} missing exchange prefix"


def test_all_tickers_are_unique():
    tickers = qs.all_tickers()
    assert len(tickers) == len(set(tickers))


def test_ionq_is_in_hardware():
    assert "NYSE:IONQ" in qs.LAYERS["Q1-hardware"]


def test_horizon_quantum_in_software():
    assert "NASDAQ:HQ" in qs.LAYERS["Q3-software"]


def test_security_layer_has_laes_and_wkey():
    assert "NASDAQ:LAES" in qs.LAYERS["Q4-security"]
    assert "NASDAQ:WKEY" in qs.LAYERS["Q4-security"]


def test_applications_layer_has_demand_side_names():
    assert "NYSE:JPM" in qs.LAYERS["Q5-applications"]
    assert "NASDAQ:MRNA" in qs.LAYERS["Q5-applications"]


def test_layer_of_returns_the_layer_key():
    assert qs.layer_of("NYSE:IONQ") == "Q1-hardware"


def test_layer_of_unknown_ticker_is_none():
    assert qs.layer_of("NYSE:ZZZZ") is None


def test_pending_quantinuum_not_pulled_until_it_lists():
    # Quantinuum (QNT) IPO pending — "QNT" maps to a different issuer on the data
    # source, so it must be neither in PENDING-pull nor in the live universe yet.
    assert not any("QNT" in t for t in qs.all_tickers())
    assert isinstance(qs.PENDING, list)


# --- screener vs graph-only node separation ---

def _node_ids(nodes):
    return {n["id"] for n in nodes}


def test_giant_nodes_are_graph_only_not_in_screener():
    screener_syms = {t.split(":")[-1] for t in qs.all_tickers()}
    for n in qs.GIANT_NODES:
        assert n["id"] not in screener_syms, f"giant {n['id']} leaked into screener"


def test_giant_nodes_have_required_fields():
    for n in qs.GIANT_NODES:
        assert n["id"] and n["name"] and n["layer"]
        assert "note" in n


def test_private_and_foreign_nodes_are_not_screener_tickers():
    screener_syms = {t.split(":")[-1] for t in qs.all_tickers()}
    for n in qs.PRIVATE_NODES + qs.FOREIGN_NODES:
        assert n["id"] not in screener_syms
        assert n["id"] and n["name"] and n["layer"]
        assert "note" in n


def test_at_least_twenty_private_plus_foreign_nodes():
    assert len(qs.PRIVATE_NODES) + len(qs.FOREIGN_NODES) >= 20


def test_no_overlap_between_node_categories():
    giant = _node_ids(qs.GIANT_NODES)
    priv = _node_ids(qs.PRIVATE_NODES)
    foreign = _node_ids(qs.FOREIGN_NODES)
    assert giant.isdisjoint(priv)
    assert giant.isdisjoint(foreign)
    assert priv.isdisjoint(foreign)
