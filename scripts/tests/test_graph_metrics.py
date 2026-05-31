"""Tests for graph_metrics — structural/topology analysis of the AI capital web.

TDD: these tests are written FIRST (RED) and drive the implementation.
All fixtures are deterministic synthetic graphs — no network calls.
Educational/research only — not investment advice.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Helpers to build synthetic graph_dicts
# ---------------------------------------------------------------------------

def _node(nid, layer="L1-chips"):
    return {"id": nid, "name": nid, "type": "public", "ticker": None, "layer": layer}


def _edge(src, dst, etype="customer", certainty="reported"):
    return {
        "src": src, "dst": dst, "type": etype, "attrs": {},
        "certainty": certainty, "origin": "curated",
        "source_url": "test", "retrieved_at": "2026-05-31T00:00:00Z",
    }


# ---------------------------------------------------------------------------
# Fixture 1 — Hub-and-spoke (5 nodes: hub → 4 spokes; spokes only connect via hub)
# Hub is the only articulation point; removing it disconnects the graph.
# hub has highest in-degree & pagerank.
# ---------------------------------------------------------------------------

def _hub_spoke_graph():
    nodes = [_node("hub")] + [_node(f"spoke{i}") for i in range(1, 5)]
    edges = [
        # hub points to all spokes
        _edge("hub", "spoke1"),
        _edge("hub", "spoke2"),
        _edge("hub", "spoke3"),
        _edge("hub", "spoke4"),
        # spokes also point back to hub so hub appears as articulation point
        # in the undirected projection (spoke-hub-spoke paths go through hub)
        _edge("spoke1", "hub"),
        _edge("spoke2", "hub"),
        _edge("spoke3", "hub"),
        _edge("spoke4", "hub"),
    ]
    return {"nodes": nodes, "edges": edges}


# Fixture 2 — 3-cycle (A→B→C→A): yields one non-trivial SCC of size 3
def _cycle_graph():
    nodes = [_node("A"), _node("B"), _node("C")]
    edges = [_edge("A", "B"), _edge("B", "C"), _edge("C", "A")]
    return {"nodes": nodes, "edges": edges}


# Fixture 3 — Star (hub→spokes only, no back-edges, 20 leaves):
# Targeted removal always hits center (highest degree); random removal only
# picks center with probability 1/21 per trial.  Fragility ratio >> 1.
def _star_graph():
    nodes = [_node("center")] + [_node(f"leaf{i}") for i in range(1, 21)]
    edges = [_edge("center", f"leaf{i}") for i in range(1, 21)]
    return {"nodes": nodes, "edges": edges}


# Fixture 4 — Minimal graph (single edge A→B)
def _minimal_graph():
    return {
        "nodes": [_node("A"), _node("B")],
        "edges": [_edge("A", "B")],
    }


# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------

from aiinvest import graph_metrics as gm  # noqa: E402


# ---------------------------------------------------------------------------
# compute() — return shape / keys
# ---------------------------------------------------------------------------

class TestComputeReturnShape:
    """compute() must return a dict with 'nodes' and 'graph' keys."""

    def test_returns_nodes_and_graph_keys(self):
        result = gm.compute(_minimal_graph())
        assert "nodes" in result
        assert "graph" in result

    def test_nodes_keyed_by_id(self):
        result = gm.compute(_minimal_graph())
        assert "A" in result["nodes"]
        assert "B" in result["nodes"]

    def test_node_entry_has_required_keys(self):
        result = gm.compute(_minimal_graph())
        node = result["nodes"]["A"]
        required = {"in_degree", "out_degree", "pagerank", "betweenness",
                    "eigenvector", "kcore", "in_scc", "is_articulation"}
        assert required.issubset(node.keys()), f"Missing keys: {required - node.keys()}"

    def test_graph_entry_has_required_keys(self):
        result = gm.compute(_minimal_graph())
        g = result["graph"]
        required = {
            "n_nodes", "n_edges", "articulation_points", "bridges",
            "sccs", "largest_scc_size", "assortativity", "fragility_ratio",
        }
        assert required.issubset(g.keys()), f"Missing keys: {required - g.keys()}"

    def test_n_nodes_and_n_edges_correct(self):
        g = _hub_spoke_graph()
        result = gm.compute(g)
        assert result["graph"]["n_nodes"] == 5
        assert result["graph"]["n_edges"] == 8

    def test_in_scc_is_bool(self):
        result = gm.compute(_cycle_graph())
        for nid, data in result["nodes"].items():
            assert isinstance(data["in_scc"], bool), f"{nid}: in_scc should be bool"

    def test_is_articulation_is_bool(self):
        result = gm.compute(_hub_spoke_graph())
        for nid, data in result["nodes"].items():
            assert isinstance(data["is_articulation"], bool), f"{nid}: is_articulation should be bool"


# ---------------------------------------------------------------------------
# Hub-and-spoke fixture assertions
# ---------------------------------------------------------------------------

class TestHubAndSpoke:
    """Hub-and-spoke: hub should dominate structural metrics."""

    def setup_method(self):
        self.result = gm.compute(_hub_spoke_graph())

    def test_hub_is_articulation_point(self):
        # In the undirected projection hub is the central node —
        # removing it disconnects spokes from each other.
        assert self.result["nodes"]["hub"]["is_articulation"] is True

    def test_spokes_are_not_articulation_points(self):
        for i in range(1, 5):
            assert self.result["nodes"][f"spoke{i}"]["is_articulation"] is False

    def test_hub_has_highest_pagerank(self):
        prs = {nid: d["pagerank"] for nid, d in self.result["nodes"].items()}
        assert prs["hub"] == max(prs.values())

    def test_hub_has_highest_out_degree(self):
        out_degrees = {nid: d["out_degree"] for nid, d in self.result["nodes"].items()}
        assert out_degrees["hub"] == max(out_degrees.values())

    def test_articulation_points_list_contains_hub(self):
        assert "hub" in self.result["graph"]["articulation_points"]

    def test_kcore_values_are_non_negative_ints(self):
        for nid, d in self.result["nodes"].items():
            assert isinstance(d["kcore"], int)
            assert d["kcore"] >= 0


# ---------------------------------------------------------------------------
# 3-cycle fixture: SCC
# ---------------------------------------------------------------------------

class TestCycleGraph:
    """3-cycle A→B→C→A: all 3 nodes in one non-trivial SCC."""

    def setup_method(self):
        self.result = gm.compute(_cycle_graph())

    def test_all_nodes_in_scc(self):
        for nid in ("A", "B", "C"):
            assert self.result["nodes"][nid]["in_scc"] is True

    def test_sccs_has_one_nontrivial_component(self):
        sccs = self.result["graph"]["sccs"]
        # non-trivial = size > 1
        assert len(sccs) >= 1
        sizes = [len(s) for s in sccs]
        assert 3 in sizes

    def test_largest_scc_size_is_3(self):
        assert self.result["graph"]["largest_scc_size"] == 3

    def test_pagerank_sums_to_approximately_one(self):
        total = sum(d["pagerank"] for d in self.result["nodes"].values())
        assert abs(total - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# fragility_ratio
# ---------------------------------------------------------------------------

class TestFragilityRatio:
    """Targeted-vs-random percolation: star graph must be targeted-fragile (ratio > 1)."""

    def test_star_graph_fragility_ratio_greater_than_one(self):
        result = gm.compute(_star_graph())
        assert result["graph"]["fragility_ratio"] > 1.0, (
            f"Star graph should be targeted-fragile, got {result['graph']['fragility_ratio']}"
        )

    def test_fragility_ratio_is_float(self):
        result = gm.compute(_hub_spoke_graph())
        assert isinstance(result["graph"]["fragility_ratio"], float)

    def test_fragility_ratio_non_negative(self):
        result = gm.compute(_minimal_graph())
        assert result["graph"]["fragility_ratio"] >= 0.0


# ---------------------------------------------------------------------------
# Eigenvector convergence guard
# ---------------------------------------------------------------------------

class TestEigenvector:
    """Eigenvector is computed on undirected projection; must never raise."""

    def test_eigenvector_returns_float_or_none(self):
        result = gm.compute(_hub_spoke_graph())
        for nid, d in result["nodes"].items():
            val = d["eigenvector"]
            assert val is None or isinstance(val, float), (
                f"{nid}: eigenvector must be float or None, got {type(val)}"
            )

    def test_eigenvector_hub_not_less_than_spokes(self):
        result = gm.compute(_hub_spoke_graph())
        hub_ev = result["nodes"]["hub"]["eigenvector"]
        spoke_evs = [result["nodes"][f"spoke{i}"]["eigenvector"] for i in range(1, 5)]
        if hub_ev is not None and all(v is not None for v in spoke_evs):
            assert hub_ev >= max(spoke_evs)


# ---------------------------------------------------------------------------
# Assortativity
# ---------------------------------------------------------------------------

class TestAssortativity:
    """assortativity is float or None (None for degenerate graphs)."""

    def test_assortativity_is_float_or_none(self):
        result = gm.compute(_hub_spoke_graph())
        val = result["graph"]["assortativity"]
        assert val is None or isinstance(val, float)

    def test_assortativity_in_valid_range_when_not_none(self):
        result = gm.compute(_hub_spoke_graph())
        val = result["graph"]["assortativity"]
        if val is not None:
            assert -1.0 <= val <= 1.0

    def test_minimal_graph_assortativity_none_or_float(self):
        result = gm.compute(_minimal_graph())
        val = result["graph"]["assortativity"]
        assert val is None or isinstance(val, float)


# ---------------------------------------------------------------------------
# Bridges
# ---------------------------------------------------------------------------

class TestBridges:
    """Bridges returned as list of [u, v] pairs."""

    def test_bridges_is_list(self):
        result = gm.compute(_hub_spoke_graph())
        assert isinstance(result["graph"]["bridges"], list)

    def test_cycle_has_no_bridges(self):
        result = gm.compute(_cycle_graph())
        assert result["graph"]["bridges"] == []

    def test_bridges_are_pairs(self):
        result = gm.compute(_hub_spoke_graph())
        for b in result["graph"]["bridges"]:
            assert len(b) == 2


# ---------------------------------------------------------------------------
# Betweenness
# ---------------------------------------------------------------------------

class TestBetweenness:
    """Betweenness centrality: hub/center must dominate in star-like structures."""

    def test_hub_highest_betweenness(self):
        result = gm.compute(_hub_spoke_graph())
        bcs = {nid: d["betweenness"] for nid, d in result["nodes"].items()}
        assert bcs["hub"] == max(bcs.values())

    def test_betweenness_non_negative(self):
        result = gm.compute(_hub_spoke_graph())
        for nid, d in result["nodes"].items():
            assert d["betweenness"] >= 0.0


# ---------------------------------------------------------------------------
# load_graph() smoke test (no network; just checks structure)
# ---------------------------------------------------------------------------

class TestLoadGraph:
    """load_graph() must return a valid graph_dict without network calls."""

    def test_load_graph_returns_nodes_and_edges(self):
        g = gm.load_graph()
        assert "nodes" in g
        assert "edges" in g

    def test_load_graph_nodes_have_required_keys(self):
        g = gm.load_graph()
        for node in g["nodes"]:
            assert "id" in node
            assert "layer" in node

    def test_load_graph_edges_have_required_keys(self):
        g = gm.load_graph()
        for edge in g["edges"]:
            assert "src" in edge
            assert "dst" in edge
            assert "type" in edge

    def test_load_graph_has_nonzero_nodes_and_edges(self):
        g = gm.load_graph()
        assert len(g["nodes"]) > 0
        assert len(g["edges"]) > 0
