"""Tests for contagion — Independent Cascade & Linear Threshold models.

TDD: written FIRST (RED), drive the implementation in aiinvest/contagion.py.
All fixtures are deterministic synthetic graphs — no network calls.
Educational/research only — not investment advice.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Synthetic graph helpers (match repo style from test_graph_metrics.py)
# ---------------------------------------------------------------------------

def _node(nid, layer="L1-chips"):
    return {"id": nid, "name": nid, "type": "public", "ticker": nid, "layer": layer}


def _edge(src, dst, etype="customer", certainty="filed", attrs=None):
    return {
        "src": src,
        "dst": dst,
        "type": etype,
        "attrs": attrs or {},
        "certainty": certainty,
        "origin": "curated",
        "source_url": "test",
    }


# Fixture A: linear chain  A -> B -> C -> D
# With P=1.0 (filed edges): seeding A forward should reach B, C, D.
# Seeding D reverse should reach C, B, A.
def _chain_graph():
    nodes = [_node(n) for n in ("A", "B", "C", "D")]
    edges = [_edge("A", "B"), _edge("B", "C"), _edge("C", "D")]
    return {"nodes": nodes, "edges": edges}


# Fixture B: isolated pair + separate node
# E -> F  (filed)   G (isolated)
# Seeding E forward reaches F; G never touched.
def _isolated_graph():
    nodes = [_node("E"), _node("F"), _node("G")]
    edges = [_edge("E", "F")]
    return {"nodes": nodes, "edges": edges}


# Fixture C: 3-node fan-in  X -> Z, Y -> Z
# For LTM with threshold=0.5: if only X is seeded (1/2 = 0.5, not > 0.5) Z stays off;
# if both X and Y are seeded Z activates (2/2 = 1.0 > 0.5).
def _fan_in_graph():
    nodes = [_node("X"), _node("Y"), _node("Z")]
    edges = [_edge("X", "Z"), _edge("Y", "Z")]
    return {"nodes": nodes, "edges": edges}


# Fixture D: rumored-only edges (P=0.25)
# Used to verify rng_seed reproducibility across two ICM runs.
def _rumored_chain():
    nodes = [_node(n) for n in ("P", "Q", "R")]
    edges = [_edge("P", "Q", certainty="rumored"), _edge("Q", "R", certainty="rumored")]
    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Import module under test
# ---------------------------------------------------------------------------

from aiinvest import contagion  # noqa: E402


# ---------------------------------------------------------------------------
# SCENARIOS dict
# ---------------------------------------------------------------------------

class TestScenariosDict:
    """SCENARIOS must be a dict with the three required keys and correct structure."""

    def test_scenarios_is_dict(self):
        assert isinstance(contagion.SCENARIOS, dict)

    def test_scenarios_has_required_keys(self):
        required = {"tsm_disruption", "hyperscaler_capex_cut", "energy_bridge_loss"}
        assert required.issubset(contagion.SCENARIOS.keys()), (
            f"Missing scenario keys: {required - contagion.SCENARIOS.keys()}"
        )

    def test_tsm_disruption_seeds(self):
        s = contagion.SCENARIOS["tsm_disruption"]
        assert "TSM" in s["seeds"]
        assert s["direction"] == "forward"

    def test_hyperscaler_capex_cut_seeds(self):
        s = contagion.SCENARIOS["hyperscaler_capex_cut"]
        for ticker in ("MSFT", "AMZN", "GOOGL", "META"):
            assert ticker in s["seeds"], f"{ticker} missing from hyperscaler_capex_cut seeds"
        assert s["direction"] == "reverse"

    def test_energy_bridge_loss_seeds(self):
        s = contagion.SCENARIOS["energy_bridge_loss"]
        assert "GEV" in s["seeds"]
        assert s["direction"] == "forward"

    def test_each_scenario_has_seeds_and_direction(self):
        for name, s in contagion.SCENARIOS.items():
            assert "seeds" in s, f"{name} missing 'seeds'"
            assert "direction" in s, f"{name} missing 'direction'"
            assert isinstance(s["seeds"], list), f"{name} seeds must be list"
            assert s["direction"] in ("forward", "reverse"), f"{name} invalid direction"


# ---------------------------------------------------------------------------
# independent_cascade — return shape
# ---------------------------------------------------------------------------

class TestICMReturnShape:
    """independent_cascade must return {"affected": [...], "reach": float}."""

    def test_returns_dict_with_affected_and_reach(self):
        result = contagion.independent_cascade(_chain_graph(), seeds=["A"])
        assert "affected" in result
        assert "reach" in result

    def test_affected_is_list(self):
        result = contagion.independent_cascade(_chain_graph(), seeds=["A"])
        assert isinstance(result["affected"], list)

    def test_reach_is_float(self):
        result = contagion.independent_cascade(_chain_graph(), seeds=["A"])
        assert isinstance(result["reach"], float)

    def test_reach_between_0_and_1(self):
        result = contagion.independent_cascade(_chain_graph(), seeds=["A"])
        assert 0.0 <= result["reach"] <= 1.0

    def test_seeds_not_in_affected(self):
        """affected should list non-seed nodes; seeds are the source, not the spread."""
        result = contagion.independent_cascade(_chain_graph(), seeds=["A"])
        assert "A" not in result["affected"]

    def test_affected_contains_only_valid_node_ids(self):
        g = _chain_graph()
        valid_ids = {n["id"] for n in g["nodes"]}
        result = contagion.independent_cascade(g, seeds=["A"])
        for nid in result["affected"]:
            assert nid in valid_ids, f"Unknown node id '{nid}' in affected"


# ---------------------------------------------------------------------------
# independent_cascade — forward direction (supply shock)
# ---------------------------------------------------------------------------

class TestICMForward:
    """Forward cascade: seeding A reaches downstream B, C, D when P=1.0 (filed edges)."""

    def test_full_chain_reached_with_filed_edges_forward(self):
        # filed -> P=0.85; with 200 trials the mean should reliably reach downstream
        # Use P override to guarantee determinism: filed -> 1.0
        result = contagion.independent_cascade(
            _chain_graph(), seeds=["A"], direction="forward",
            trials=200, rng_seed=0,
            _prob_override={"filed": 1.0, "reported": 1.0, "rumored": 1.0},
        )
        assert set(result["affected"]) == {"B", "C", "D"}, (
            f"Expected {{B,C,D}}, got {set(result['affected'])}"
        )

    def test_reach_is_1_when_all_reachable_forward(self):
        result = contagion.independent_cascade(
            _chain_graph(), seeds=["A"], direction="forward",
            trials=200, rng_seed=0,
            _prob_override={"filed": 1.0, "reported": 1.0, "rumored": 1.0},
        )
        assert result["reach"] == pytest.approx(1.0), f"reach={result['reach']}"

    def test_isolated_node_not_reached_forward(self):
        result = contagion.independent_cascade(
            _isolated_graph(), seeds=["E"], direction="forward",
            trials=100, rng_seed=0,
            _prob_override={"filed": 1.0},
        )
        assert "G" not in result["affected"]
        assert "F" in result["affected"]

    def test_seeding_middle_node_only_reaches_downstream(self):
        # Seeding B forward: only C and D should be reachable, not A.
        result = contagion.independent_cascade(
            _chain_graph(), seeds=["B"], direction="forward",
            trials=100, rng_seed=0,
            _prob_override={"filed": 1.0},
        )
        assert "A" not in result["affected"]
        assert "C" in result["affected"]
        assert "D" in result["affected"]


# ---------------------------------------------------------------------------
# independent_cascade — reverse direction (demand shock)
# ---------------------------------------------------------------------------

class TestICMReverse:
    """Reverse cascade: seeding D backward reaches C, B, A (suppliers) when P=1.0."""

    def test_full_chain_reached_reverse(self):
        result = contagion.independent_cascade(
            _chain_graph(), seeds=["D"], direction="reverse",
            trials=200, rng_seed=0,
            _prob_override={"filed": 1.0, "reported": 1.0, "rumored": 1.0},
        )
        assert set(result["affected"]) == {"A", "B", "C"}, (
            f"Expected {{A,B,C}}, got {set(result['affected'])}"
        )

    def test_reach_is_1_reverse(self):
        result = contagion.independent_cascade(
            _chain_graph(), seeds=["D"], direction="reverse",
            trials=200, rng_seed=0,
            _prob_override={"filed": 1.0, "reported": 1.0, "rumored": 1.0},
        )
        assert result["reach"] == pytest.approx(1.0)

    def test_seeding_middle_node_reverse_only_reaches_upstream(self):
        result = contagion.independent_cascade(
            _chain_graph(), seeds=["C"], direction="reverse",
            trials=100, rng_seed=0,
            _prob_override={"filed": 1.0},
        )
        assert "D" not in result["affected"]
        assert "B" in result["affected"]
        assert "A" in result["affected"]


# ---------------------------------------------------------------------------
# independent_cascade — default direction is "reverse" (spec §2)
# ---------------------------------------------------------------------------

class TestICMDefaultDirection:
    def test_default_direction_is_reverse(self):
        # Without specifying direction, seeding D should reach upstream nodes (reverse).
        result = contagion.independent_cascade(
            _chain_graph(), seeds=["D"],
            trials=100, rng_seed=0,
            _prob_override={"filed": 1.0},
        )
        # In reverse, A/B/C are reachable from D; forward would give nothing.
        assert len(result["affected"]) > 0, "Default direction should propagate (reverse)"


# ---------------------------------------------------------------------------
# independent_cascade — rng_seed reproducibility
# ---------------------------------------------------------------------------

class TestICMReproducibility:
    """Same rng_seed must produce identical results across two runs."""

    def test_same_seed_same_result(self):
        g = _rumored_chain()
        r1 = contagion.independent_cascade(g, seeds=["P"], trials=200, rng_seed=42)
        r2 = contagion.independent_cascade(g, seeds=["P"], trials=200, rng_seed=42)
        assert r1["reach"] == r2["reach"]
        assert sorted(r1["affected"]) == sorted(r2["affected"])

    def test_different_seeds_may_differ(self):
        # With low-P rumored edges, different rng_seeds should sometimes differ.
        # We just check neither raises and both return valid shapes.
        g = _rumored_chain()
        r1 = contagion.independent_cascade(g, seeds=["P"], trials=500, rng_seed=1)
        r2 = contagion.independent_cascade(g, seeds=["P"], trials=500, rng_seed=999)
        assert 0.0 <= r1["reach"] <= 1.0
        assert 0.0 <= r2["reach"] <= 1.0

    def test_reach_with_zero_prob_override_is_zero(self):
        result = contagion.independent_cascade(
            _chain_graph(), seeds=["A"], direction="forward",
            trials=200, rng_seed=0,
            _prob_override={"filed": 0.0, "reported": 0.0, "rumored": 0.0},
        )
        assert result["reach"] == pytest.approx(0.0)
        assert result["affected"] == []


# ---------------------------------------------------------------------------
# independent_cascade — certainty transmission probabilities
# ---------------------------------------------------------------------------

class TestICMCertaintyProbs:
    """filed > reported > rumored in expected reach over many trials."""

    def _reach(self, certainty):
        nodes = [_node(n) for n in ("S", "T")]
        edges = [_edge("S", "T", certainty=certainty)]
        g = {"nodes": nodes, "edges": edges}
        return contagion.independent_cascade(
            g, seeds=["S"], direction="forward", trials=500, rng_seed=0
        )["reach"]

    def test_filed_reach_greater_than_rumored(self):
        assert self._reach("filed") > self._reach("rumored")

    def test_reported_reach_greater_than_rumored(self):
        assert self._reach("reported") > self._reach("rumored")

    def test_filed_reach_greater_than_reported(self):
        assert self._reach("filed") > self._reach("reported")

    def test_unknown_certainty_uses_fallback_prob(self):
        # Unknown certainty should not raise; uses flat 0.1 fallback.
        nodes = [_node("S"), _node("T")]
        edges = [_edge("S", "T", certainty="unknown_xyz")]
        g = {"nodes": nodes, "edges": edges}
        result = contagion.independent_cascade(
            g, seeds=["S"], direction="forward", trials=300, rng_seed=7
        )
        assert 0.0 <= result["reach"] <= 1.0


# ---------------------------------------------------------------------------
# linear_threshold — return shape
# ---------------------------------------------------------------------------

class TestLTMReturnShape:
    """linear_threshold must return {"affected": [...]}."""

    def test_returns_dict_with_affected(self):
        result = contagion.linear_threshold(_chain_graph(), seeds=["A"])
        assert "affected" in result

    def test_affected_is_list(self):
        result = contagion.linear_threshold(_chain_graph(), seeds=["A"])
        assert isinstance(result["affected"], list)

    def test_seeds_not_in_affected(self):
        result = contagion.linear_threshold(_chain_graph(), seeds=["A"])
        assert "A" not in result["affected"]

    def test_affected_only_valid_ids(self):
        g = _chain_graph()
        valid_ids = {n["id"] for n in g["nodes"]}
        result = contagion.linear_threshold(g, seeds=["A"])
        for nid in result["affected"]:
            assert nid in valid_ids


# ---------------------------------------------------------------------------
# linear_threshold — forward direction (default per spec)
# ---------------------------------------------------------------------------

class TestLTMForward:
    """With threshold=0.5 and filed edges (w=0.85), LTM propagates along the chain."""

    def test_chain_propagates_forward(self):
        # A→B→C→D: seed A, all downstream should activate with threshold=0.5
        # Each node has exactly one in-neighbor which is active → fraction = 1.0 > 0.5
        result = contagion.linear_threshold(
            _chain_graph(), seeds=["A"], direction="forward", threshold=0.5
        )
        assert set(result["affected"]) == {"B", "C", "D"}

    def test_isolated_node_not_reached(self):
        result = contagion.linear_threshold(
            _isolated_graph(), seeds=["E"], direction="forward", threshold=0.5
        )
        assert "G" not in result["affected"]
        assert "F" in result["affected"]


# ---------------------------------------------------------------------------
# linear_threshold — threshold behaviour (fan-in fixture)
# ---------------------------------------------------------------------------

class TestLTMThreshold:
    """Fan-in X->Z, Y->Z: Z activates only when both X and Y are seeded."""

    def test_single_seed_below_threshold_does_not_activate_z(self):
        # Only X seeded: Z has 1 active / 2 total in-neighbors = 0.5, not > 0.5
        result = contagion.linear_threshold(
            _fan_in_graph(), seeds=["X"], direction="forward", threshold=0.5
        )
        assert "Z" not in result["affected"], (
            "Z should NOT activate when only 1 of 2 neighbors is active (0.5 not > 0.5)"
        )

    def test_both_seeds_above_threshold_activates_z(self):
        # X and Y seeded: Z has 2 active / 2 total = 1.0 > 0.5
        result = contagion.linear_threshold(
            _fan_in_graph(), seeds=["X", "Y"], direction="forward", threshold=0.5
        )
        assert "Z" in result["affected"], "Z should activate when both neighbors are active"

    def test_high_threshold_blocks_propagation(self):
        # threshold=1.0 requires ALL in-neighbors active; chain with single path:
        # B has exactly 1 in-neighbor (A) which is active → fraction=1.0=threshold
        # The spec says "exceeds threshold" (strictly >), so B should NOT activate.
        result = contagion.linear_threshold(
            _chain_graph(), seeds=["A"], direction="forward", threshold=1.0
        )
        assert "B" not in result["affected"], (
            "With threshold=1.0 (strict >), a node with 1/1 active neighbor should NOT activate"
        )

    def test_low_threshold_allows_full_propagation(self):
        result = contagion.linear_threshold(
            _chain_graph(), seeds=["A"], direction="forward", threshold=0.01
        )
        assert set(result["affected"]) == {"B", "C", "D"}


# ---------------------------------------------------------------------------
# linear_threshold — reverse direction
# ---------------------------------------------------------------------------

class TestLTMReverse:
    """Reverse direction: seed D, propagate upstream through chain."""

    def test_reverse_reaches_upstream(self):
        result = contagion.linear_threshold(
            _chain_graph(), seeds=["D"], direction="reverse", threshold=0.5
        )
        assert set(result["affected"]) == {"A", "B", "C"}

    def test_default_direction_is_forward(self):
        # Seeding A without direction: forward gives {B,C,D}; reverse would give nothing.
        result = contagion.linear_threshold(_chain_graph(), seeds=["A"])
        assert "B" in result["affected"], "Default direction should be forward"


# ---------------------------------------------------------------------------
# linear_threshold — determinism
# ---------------------------------------------------------------------------

class TestLTMDeterminism:
    """linear_threshold is deterministic (no randomness)."""

    def test_two_runs_same_result(self):
        g = _chain_graph()
        r1 = contagion.linear_threshold(g, seeds=["A"])
        r2 = contagion.linear_threshold(g, seeds=["A"])
        assert sorted(r1["affected"]) == sorted(r2["affected"])


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Empty seeds, all seeds, single-node graph."""

    def test_empty_seeds_icm_no_affected(self):
        result = contagion.independent_cascade(_chain_graph(), seeds=[], trials=10, rng_seed=0)
        assert result["affected"] == []
        assert result["reach"] == pytest.approx(0.0)

    def test_empty_seeds_ltm_no_affected(self):
        result = contagion.linear_threshold(_chain_graph(), seeds=[])
        assert result["affected"] == []

    def test_all_nodes_seeded_icm(self):
        g = _chain_graph()
        all_ids = [n["id"] for n in g["nodes"]]
        result = contagion.independent_cascade(g, seeds=all_ids, trials=10, rng_seed=0)
        assert result["affected"] == []
        assert result["reach"] == pytest.approx(0.0)

    def test_single_node_graph_icm(self):
        g = {"nodes": [_node("solo")], "edges": []}
        result = contagion.independent_cascade(g, seeds=["solo"], trials=10, rng_seed=0)
        assert result["affected"] == []
        assert result["reach"] == pytest.approx(0.0)

    def test_single_node_graph_ltm(self):
        g = {"nodes": [_node("solo")], "edges": []}
        result = contagion.linear_threshold(g, seeds=["solo"])
        assert result["affected"] == []

    def test_seed_not_in_graph_icm(self):
        # Seeds that don't exist in nodes should not raise; just no propagation.
        result = contagion.independent_cascade(
            _chain_graph(), seeds=["NONEXISTENT"], trials=10, rng_seed=0
        )
        assert isinstance(result["affected"], list)

    def test_seed_not_in_graph_ltm(self):
        result = contagion.linear_threshold(_chain_graph(), seeds=["NONEXISTENT"])
        assert isinstance(result["affected"], list)
