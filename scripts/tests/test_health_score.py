"""Tests for health_score — Tier-1 Topology Score for the AI capital web.

TDD: tests written FIRST (RED), drive implementation in health_score.py.
All fixtures are synthetic, deterministic — no network calls.
Educational/research only — not investment advice.
"""
from __future__ import annotations

import math
import pytest

# ---------------------------------------------------------------------------
# Shared helpers (mirrors test_graph_metrics.py style)
# ---------------------------------------------------------------------------

def _node(nid: str, layer: str = "L1-chips") -> dict:
    return {"id": nid, "name": nid, "type": "public", "ticker": None, "layer": layer}


def _edge(
    src: str,
    dst: str,
    etype: str = "customer",
    certainty: str = "reported",
) -> dict:
    return {
        "src": src,
        "dst": dst,
        "type": etype,
        "attrs": {},
        "certainty": certainty,
        "origin": "curated",
        "source_url": "test",
        "retrieved_at": "2026-05-31T00:00:00Z",
    }


# ---------------------------------------------------------------------------
# Fixture A — single inbound edge (floor guardrail + topology-estimate flag)
#   one_in:  single supplier supplying "receiver"
#   receiver: has exactly 1 inbound edge => floor at 40, flagged
# ---------------------------------------------------------------------------

def _single_inbound_graph() -> dict:
    nodes = [_node("supplier"), _node("receiver")]
    edges = [_edge("supplier", "receiver")]
    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Fixture B — isolated node (no edges at all)
#   isolated, connected_a, connected_b form a graph where "isolated" is degree-0
# ---------------------------------------------------------------------------

def _isolated_node_graph() -> dict:
    nodes = [_node("isolated"), _node("connected_a"), _node("connected_b")]
    edges = [_edge("connected_a", "connected_b")]
    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Fixture C — diversified vs concentrated (same layer; different HHI)
#   concentrated: receives 3 edges all from "single_sup"
#   diversified:  receives 3 edges from 3 different suppliers
# ---------------------------------------------------------------------------

def _diversity_graph() -> dict:
    nodes = [
        _node("single_sup"),
        _node("sup_a"),
        _node("sup_b"),
        _node("sup_c"),
        _node("concentrated"),
        _node("diversified"),
    ]
    # concentrated receives 3 edges from single_sup (HHI = 10000)
    edges_conc = [_edge("single_sup", "concentrated") for _ in range(3)]
    # diversified receives one edge from each of three different suppliers (HHI = 3333)
    edges_div = [
        _edge("sup_a", "diversified"),
        _edge("sup_b", "diversified"),
        _edge("sup_c", "diversified"),
    ]
    return {"nodes": nodes, "edges": edges_conc + edges_div}


# ---------------------------------------------------------------------------
# Fixture D — SCC cap (cycle => largest SCC; members should be capped at 85)
# ---------------------------------------------------------------------------

def _scc_cycle_graph() -> dict:
    nodes = [_node(f"n{i}") for i in range(4)]
    edges = [
        _edge("n0", "n1"), _edge("n1", "n2"),
        _edge("n2", "n3"), _edge("n3", "n0"),
    ]
    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Fixture E — multi-layer graph to check layer aggregates
# ---------------------------------------------------------------------------

def _multi_layer_graph() -> dict:
    nodes = [
        _node("chip_a", "L1-chips"),
        _node("chip_b", "L1-chips"),
        _node("app_a", "L4-app"),
    ]
    edges = [
        _edge("chip_a", "chip_b", certainty="filed"),
        _edge("chip_b", "chip_a", certainty="filed"),
        _edge("chip_a", "app_a", certainty="reported"),
    ]
    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Import module under test
# ---------------------------------------------------------------------------

from aiinvest import health_score as hs  # noqa: E402


# ---------------------------------------------------------------------------
# 1. Return shape
# ---------------------------------------------------------------------------

class TestReturnShape:
    """score() must return the canonical output dict."""

    def setup_method(self):
        self.result = hs.score(_single_inbound_graph())

    def test_has_nodes_key(self):
        assert "nodes" in self.result

    def test_has_layers_key(self):
        assert "layers" in self.result

    def test_has_overall_key(self):
        assert "overall" in self.result

    def test_nodes_keyed_by_id(self):
        assert "receiver" in self.result["nodes"]
        assert "supplier" in self.result["nodes"]

    def test_node_entry_has_score(self):
        node = self.result["nodes"]["receiver"]
        assert "score" in node

    def test_node_entry_has_components(self):
        node = self.result["nodes"]["receiver"]
        assert "components" in node
        comps = node["components"]
        for key in ("concentration", "spof", "redundancy", "certainty"):
            assert key in comps, f"Missing component: {key}"

    def test_node_entry_has_ens(self):
        node = self.result["nodes"]["receiver"]
        assert "ens" in node

    def test_node_entry_has_flags(self):
        node = self.result["nodes"]["receiver"]
        assert "flags" in node
        assert isinstance(node["flags"], list)


# ---------------------------------------------------------------------------
# 2. Isolated node — no-data + excluded from aggregates
# ---------------------------------------------------------------------------

class TestIsolatedNode:
    """Isolated node => score=None, flags=['no-data'], excluded from aggregates."""

    def setup_method(self):
        self.result = hs.score(_isolated_node_graph())

    def test_isolated_score_is_none(self):
        assert self.result["nodes"]["isolated"]["score"] is None

    def test_isolated_flag_no_data(self):
        assert "no-data" in self.result["nodes"]["isolated"]["flags"]

    def test_isolated_excluded_from_layer_aggregate(self):
        # 'isolated' shares layer L1-chips with connected_a and connected_b.
        # The aggregate n count should be the number of connected nodes in that layer,
        # not the isolated node.
        layer = self.result["layers"].get("L1-chips", {})
        # isolated is excluded; connected_a has out_degree=1 and connected_b has in_degree=1
        # connected_a: out-degree>0 but in_degree=0 (isolated from incoming)
        # connected_b: in_degree=1
        # Both connected nodes have total degree > 0 so they are NOT isolated,
        # but isolated has degree 0, so n should be < 3
        n = layer.get("n", 0)
        assert n < 3, f"Isolated node should be excluded; n={n}"

    def test_overall_excludes_isolated(self):
        # Overall must be a number (from connected nodes only), not None.
        # Even if connected nodes have low scores, overall should be a float.
        assert self.result["overall"] is not None


# ---------------------------------------------------------------------------
# 3. Single-inbound floor at 40 + topology-estimate flag
# ---------------------------------------------------------------------------

class TestSingleInboundFloor:
    """Nodes with exactly one inbound edge: score >= 40 and flagged 'topology-estimate'."""

    def setup_method(self):
        self.result = hs.score(_single_inbound_graph())
        self.receiver = self.result["nodes"]["receiver"]

    def test_receiver_score_at_least_40(self):
        s = self.receiver["score"]
        assert s is not None
        assert s >= 40, f"Single-inbound node should be floored at 40, got {s}"

    def test_receiver_flagged_topology_estimate(self):
        assert "topology-estimate" in self.receiver["flags"]

    def test_supplier_not_flagged_topology_estimate(self):
        # 'supplier' has in_degree=0 (no inbound edges) — it is an isolated-from-incoming
        # node but has out-degree=1 so total degree > 0.
        # It should either have no-data OR if we treat it as connected (degree>0) it
        # won't have the topology-estimate flag (which is specifically for in_degree==1).
        supplier = self.result["nodes"]["supplier"]
        # supplier has 0 inbound edges; it is not in the "exactly 1 inbound" bucket
        assert "topology-estimate" not in supplier["flags"]


# ---------------------------------------------------------------------------
# 4. Diversified > concentrated (same layer, same certainty)
# ---------------------------------------------------------------------------

class TestDiversityOrderPreserved:
    """Diversified supplier base must score higher than a concentrated one."""

    def setup_method(self):
        self.result = hs.score(_diversity_graph())

    def test_diversified_scores_higher_than_concentrated(self):
        s_div = self.result["nodes"]["diversified"]["score"]
        s_con = self.result["nodes"]["concentrated"]["score"]
        # Both must be present
        assert s_div is not None, "diversified node should have a score"
        assert s_con is not None, "concentrated node should have a score"
        assert s_div > s_con, (
            f"diversified ({s_div:.1f}) should exceed concentrated ({s_con:.1f})"
        )

    def test_diversified_higher_concentration_component(self):
        c_div = self.result["nodes"]["diversified"]["components"]["concentration"]
        c_con = self.result["nodes"]["concentrated"]["components"]["concentration"]
        assert c_div > c_con, (
            f"diversified concentration ({c_div:.3f}) should exceed concentrated ({c_con:.3f})"
        )


# ---------------------------------------------------------------------------
# 5. SCC cap — members of the largest SCC capped at 85
# ---------------------------------------------------------------------------

class TestSCCCap:
    """Nodes inside the largest SCC must have score <= 85."""

    def setup_method(self):
        self.result = hs.score(_scc_cycle_graph())

    def test_scc_members_capped_at_85(self):
        for nid in ("n0", "n1", "n2", "n3"):
            s = self.result["nodes"][nid]["score"]
            assert s is not None
            assert s <= 85, f"SCC member {nid} should be capped at 85, got {s}"


# ---------------------------------------------------------------------------
# 6. Layer aggregates
# ---------------------------------------------------------------------------

class TestLayerAggregates:
    """layers dict must contain mean, min, max, n per layer."""

    def setup_method(self):
        self.result = hs.score(_multi_layer_graph())

    def test_layers_has_L1_chips(self):
        assert "L1-chips" in self.result["layers"]

    def test_layers_has_L4_app(self):
        assert "L4-app" in self.result["layers"]

    def test_layer_entry_has_required_keys(self):
        for layer, data in self.result["layers"].items():
            for key in ("mean", "min", "max", "n"):
                assert key in data, f"Layer {layer!r} missing key {key!r}"

    def test_layer_mean_within_min_max(self):
        for layer, data in self.result["layers"].items():
            if data["n"] > 0:
                assert data["min"] <= data["mean"] <= data["max"], (
                    f"Layer {layer!r}: mean {data['mean']:.1f} not in "
                    f"[{data['min']:.1f}, {data['max']:.1f}]"
                )

    def test_layer_n_excludes_isolated_nodes(self):
        # No node in multi_layer_graph is isolated (all have degree>0), so n == node count per layer
        assert self.result["layers"]["L1-chips"]["n"] == 2
        assert self.result["layers"]["L4-app"]["n"] == 1


# ---------------------------------------------------------------------------
# 7. Score range
# ---------------------------------------------------------------------------

class TestScoreRange:
    """All non-None scores must be in [0, 100]."""

    @pytest.mark.parametrize("graph_fn", [
        _single_inbound_graph,
        _isolated_node_graph,
        _diversity_graph,
        _scc_cycle_graph,
        _multi_layer_graph,
    ])
    def test_all_scores_in_range(self, graph_fn):
        result = hs.score(graph_fn())
        for nid, data in result["nodes"].items():
            s = data["score"]
            if s is not None:
                assert 0.0 <= s <= 100.0, f"Node {nid}: score {s} out of [0,100]"


# ---------------------------------------------------------------------------
# 8. ENS correctness
# ---------------------------------------------------------------------------

class TestENS:
    """ENS = 10000 / HHI; None for isolated/no-inbound nodes."""

    def test_concentrated_ens_is_one(self):
        # 3 edges all from single_sup → HHI = 10000 → ENS = 1.0
        result = hs.score(_diversity_graph())
        ens = result["nodes"]["concentrated"]["ens"]
        assert ens is not None
        assert abs(ens - 1.0) < 0.01, f"Concentrated ENS should be ~1.0, got {ens}"

    def test_diversified_ens_is_three(self):
        # 3 edges each from different suppliers → HHI = 3333.33 → ENS ≈ 3.0
        result = hs.score(_diversity_graph())
        ens = result["nodes"]["diversified"]["ens"]
        assert ens is not None
        assert abs(ens - 3.0) < 0.1, f"Diversified ENS should be ~3.0, got {ens}"

    def test_zero_inbound_ens_is_none(self):
        # isolated node has no inbound edges
        result = hs.score(_isolated_node_graph())
        ens = result["nodes"]["isolated"]["ens"]
        assert ens is None


# ---------------------------------------------------------------------------
# 9. Component value ranges
# ---------------------------------------------------------------------------

class TestComponentRanges:
    """Each sub-component (before weighting) must be in [0, 1]."""

    @pytest.mark.parametrize("graph_fn", [
        _single_inbound_graph,
        _diversity_graph,
        _scc_cycle_graph,
        _multi_layer_graph,
    ])
    def test_component_values_in_0_1(self, graph_fn):
        result = hs.score(graph_fn())
        for nid, data in result["nodes"].items():
            if data["score"] is None:
                continue
            for comp_name, comp_val in data["components"].items():
                assert 0.0 <= comp_val <= 1.0, (
                    f"Node {nid} component {comp_name!r} = {comp_val} not in [0,1]"
                )


# ---------------------------------------------------------------------------
# 10. Certainty component weights
# ---------------------------------------------------------------------------

class TestCertaintyWeights:
    """Certainty component reflects edge certainty: filed > reported > rumored."""

    def _graph_with_certainty(self, cert: str) -> dict:
        nodes = [_node("src"), _node("dst")]
        edges = [_edge("src", "dst", certainty=cert)]
        return {"nodes": nodes, "edges": edges}

    def test_filed_certainty_component_highest(self):
        r_filed = hs.score(self._graph_with_certainty("filed"))
        r_reported = hs.score(self._graph_with_certainty("reported"))
        r_rumored = hs.score(self._graph_with_certainty("rumored"))

        c_filed = r_filed["nodes"]["dst"]["components"]["certainty"]
        c_reported = r_reported["nodes"]["dst"]["components"]["certainty"]
        c_rumored = r_rumored["nodes"]["dst"]["components"]["certainty"]

        assert c_filed >= c_reported >= c_rumored, (
            f"filed {c_filed} >= reported {c_reported} >= rumored {c_rumored} violated"
        )

    def test_filed_certainty_value_is_one(self):
        r = hs.score(self._graph_with_certainty("filed"))
        c = r["nodes"]["dst"]["components"]["certainty"]
        assert abs(c - 1.0) < 1e-9, f"filed certainty component should be 1.0, got {c}"

    def test_rumored_certainty_value_is_03(self):
        r = hs.score(self._graph_with_certainty("rumored"))
        c = r["nodes"]["dst"]["components"]["certainty"]
        assert abs(c - 0.3) < 1e-9, f"rumored certainty component should be 0.3, got {c}"


# ---------------------------------------------------------------------------
# 11. Overall is degree-weighted mean
# ---------------------------------------------------------------------------

class TestOverall:
    """Overall score must be a float > 0 for any graph with connected nodes."""

    @pytest.mark.parametrize("graph_fn", [
        _single_inbound_graph,
        _diversity_graph,
        _scc_cycle_graph,
        _multi_layer_graph,
    ])
    def test_overall_is_float(self, graph_fn):
        result = hs.score(graph_fn())
        assert isinstance(result["overall"], float), (
            f"overall should be float, got {type(result['overall'])}"
        )

    @pytest.mark.parametrize("graph_fn", [
        _single_inbound_graph,
        _diversity_graph,
        _scc_cycle_graph,
        _multi_layer_graph,
    ])
    def test_overall_in_range(self, graph_fn):
        result = hs.score(graph_fn())
        o = result["overall"]
        assert 0.0 <= o <= 100.0, f"overall {o} out of [0,100]"
