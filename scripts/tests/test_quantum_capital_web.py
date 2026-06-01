"""RED tests for the quantum capital/relationship web (mirrors test_capital_web.py)."""
from aiinvest import quantum_capital_web as qcw
from aiinvest import capital_web as cw


# --- reuse of capital_web helpers ---

def test_reuses_capital_web_validate_and_edge_helpers():
    # The module must import (reuse) the shared helpers, not redefine them.
    assert qcw.validate is cw.validate
    assert qcw.edges_from is cw.edges_from
    assert qcw.edges_to is cw.edges_to
    assert qcw._e is cw._e


def test_new_edge_types_registered_for_validation():
    for t in ("acquired", "cloud_on", "supplier", "spinout"):
        assert t in cw.VALID_EDGE_TYPES


# --- graph integrity ---

def test_build_graph_validates_clean():
    graph = qcw.build_graph()
    assert qcw.validate(graph) == []


def test_no_dangling_edges():
    graph = qcw.build_graph()
    ids = {n["id"] for n in graph["nodes"]}
    for e in graph["edges"]:
        assert e["src"] in ids, f"dangling src {e['src']}"
        assert e["dst"] in ids, f"dangling dst {e['dst']}"


def test_screener_tickers_present_as_public_nodes():
    graph = qcw.build_graph()
    by_id = {n["id"]: n for n in graph["nodes"]}
    assert by_id["IONQ"]["type"] == "public"
    assert by_id["IONQ"]["ticker"] == "NYSE:IONQ"
    assert by_id["IONQ"]["layer"] == "Q1-hardware"


def test_giant_and_bridge_nodes_present():
    graph = qcw.build_graph()
    ids = {n["id"] for n in graph["nodes"]}
    for g in ("IBM", "GOOGL", "NVDA", "HON", "AMZN", "MSFT"):
        assert g in ids


def test_private_and_foreign_nodes_present():
    graph = qcw.build_graph()
    ids = {n["id"] for n in graph["nodes"]}
    for n in ("quantinuum", "psiquantum", "bluefors", "sandboxaq"):
        assert n in ids


def test_at_least_18_edges():
    graph = qcw.build_graph()
    assert len(graph["edges"]) >= 18


# --- edge provenance ---

def test_every_edge_has_provenance_fields():
    graph = qcw.build_graph()
    for e in graph["edges"]:
        assert e.get("source_url"), f"{e['src']}->{e['dst']} missing source_url"
        assert e.get("as_of"), f"{e['src']}->{e['dst']} missing as_of"
        assert e.get("certainty") in {"filed", "reported", "rumored"}
        assert e.get("source_class")
        assert e.get("retrieved_at")


# --- curated relationships from spec section 3 ---

def _has(graph, src, dst, etype):
    return any(e["src"] == src and e["dst"] == dst and e["type"] == etype
               for e in graph["edges"])


def test_ionq_acquired_oxford_ionics():
    graph = qcw.build_graph()
    assert _has(graph, "IONQ", "oxford_ionics", "acquired")


def test_qbts_acquired_quantum_circuits():
    graph = qcw.build_graph()
    assert _has(graph, "QBTS", "quantum_circuits", "acquired")


def test_hon_owns_quantinuum():
    graph = qcw.build_graph()
    assert _has(graph, "HON", "quantinuum", "subsidiary")


def test_ionq_cloud_on_hyperscalers():
    graph = qcw.build_graph()
    for cloud in ("AWS", "AZURE", "GCP"):
        assert _has(graph, "IONQ", cloud, "cloud_on")


def test_rgti_partners_nvda():
    graph = qcw.build_graph()
    assert _has(graph, "RGTI", "NVDA", "infra_partner")


def test_alice_and_bob_funded_by_nvda():
    graph = qcw.build_graph()
    assert _has(graph, "NVDA", "alice_bob", "equity_stake")


def test_seeqc_funded_by_bah():
    graph = qcw.build_graph()
    assert _has(graph, "BAH", "seeqc", "equity_stake")


def test_ionq_supplier_nkt():
    graph = qcw.build_graph()
    assert _has(graph, "nkt_photonics", "IONQ", "supplier")


def test_builders_supplied_by_bluefors():
    graph = qcw.build_graph()
    assert any(e["src"] == "bluefors" and e["type"] == "supplier"
               for e in graph["edges"])


def test_sandboxaq_spinout_of_googl():
    graph = qcw.build_graph()
    assert _has(graph, "GOOGL", "sandboxaq", "spinout")


def test_wkey_owns_laes():
    graph = qcw.build_graph()
    assert _has(graph, "WKEY", "LAES", "subsidiary")
