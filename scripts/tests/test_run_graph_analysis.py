"""Tests for run_graph_analysis — integration runner that writes graph_analysis.json.

TDD: these tests are written FIRST (RED) and drive the implementation.
They validate the output JSON structure and required keys without a network call
(macro snapshot falls back to baselines when FRED is unavailable).
Educational/research only — not investment advice.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RUNNER = pathlib.Path(__file__).parent.parent / "run_graph_analysis.py"
OUTPUT_PATH = (
    pathlib.Path(__file__).parent.parent.parent
    / "web" / "public" / "data" / "graph_analysis.json"
)


def _load_output() -> dict:
    """Load graph_analysis.json and return as dict. Raises if missing."""
    assert OUTPUT_PATH.exists(), f"graph_analysis.json not found at {OUTPUT_PATH}"
    with OUTPUT_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Runner exists
# ---------------------------------------------------------------------------

class TestRunnerExists:
    def test_runner_script_exists(self):
        assert RUNNER.exists(), f"run_graph_analysis.py not found at {RUNNER}"


# ---------------------------------------------------------------------------
# Run the script (once, slow) and validate output
# We run it via subprocess so it behaves exactly as the task description requires.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def analysis_output():
    """Run the script and return the parsed JSON output (cached for the module)."""
    result = subprocess.run(
        [sys.executable, str(RUNNER)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"run_graph_analysis.py exited with {result.returncode}\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
    return _load_output()


# ---------------------------------------------------------------------------
# Top-level structure
# ---------------------------------------------------------------------------

class TestTopLevelKeys:
    """The JSON must have all required top-level keys."""

    REQUIRED = {
        "generated_at",
        "disclaimer",
        "graph",
        "nodes",
        "layers",
        "overall_health",
        "top_spofs",
        "macro",
        "edge_stress",
        "cascades",
    }

    def test_all_required_keys_present(self, analysis_output):
        missing = self.REQUIRED - analysis_output.keys()
        assert not missing, f"Missing top-level keys: {missing}"

    def test_disclaimer_contains_educational(self, analysis_output):
        d = analysis_output["disclaimer"].lower()
        assert "educational" in d or "not financial advice" in d

    def test_generated_at_is_iso_string(self, analysis_output):
        ga = analysis_output["generated_at"]
        assert isinstance(ga, str) and len(ga) >= 10, f"generated_at looks wrong: {ga!r}"


# ---------------------------------------------------------------------------
# graph sub-object
# ---------------------------------------------------------------------------

class TestGraphSubObject:
    REQUIRED = {
        "n_nodes", "n_edges", "articulation_points", "bridges",
        "largest_scc_size", "fragility_ratio", "assortativity",
    }

    def test_graph_has_required_keys(self, analysis_output):
        g = analysis_output["graph"]
        missing = self.REQUIRED - g.keys()
        assert not missing, f"graph missing keys: {missing}"

    def test_n_nodes_positive(self, analysis_output):
        assert analysis_output["graph"]["n_nodes"] > 0

    def test_n_edges_positive(self, analysis_output):
        assert analysis_output["graph"]["n_edges"] > 0

    def test_articulation_points_is_list(self, analysis_output):
        assert isinstance(analysis_output["graph"]["articulation_points"], list)

    def test_bridges_is_list(self, analysis_output):
        assert isinstance(analysis_output["graph"]["bridges"], list)

    def test_fragility_ratio_non_negative(self, analysis_output):
        fr = analysis_output["graph"]["fragility_ratio"]
        assert isinstance(fr, float) and fr >= 0.0

    def test_largest_scc_size_positive(self, analysis_output):
        assert analysis_output["graph"]["largest_scc_size"] > 1


# ---------------------------------------------------------------------------
# nodes list
# ---------------------------------------------------------------------------

class TestNodesList:
    NODE_KEYS = {
        "id", "name", "layer", "health", "components", "ens", "flags",
        "pagerank", "betweenness", "in_scc", "is_articulation",
        "in_degree", "out_degree",
    }

    def test_nodes_is_list(self, analysis_output):
        assert isinstance(analysis_output["nodes"], list)

    def test_nodes_non_empty(self, analysis_output):
        assert len(analysis_output["nodes"]) > 0

    def test_each_node_has_required_keys(self, analysis_output):
        for node in analysis_output["nodes"]:
            missing = self.NODE_KEYS - node.keys()
            assert not missing, f"Node {node.get('id')} missing keys: {missing}"

    def test_nodes_sorted_by_pagerank_desc(self, analysis_output):
        prs = [n["pagerank"] for n in analysis_output["nodes"]]
        assert prs == sorted(prs, reverse=True), "nodes not sorted by pagerank desc"

    def test_pagerank_values_are_floats(self, analysis_output):
        for node in analysis_output["nodes"]:
            assert isinstance(node["pagerank"], float), (
                f"Node {node['id']}: pagerank should be float"
            )

    def test_betweenness_values_non_negative(self, analysis_output):
        for node in analysis_output["nodes"]:
            assert node["betweenness"] >= 0.0

    def test_health_is_float_or_none(self, analysis_output):
        for node in analysis_output["nodes"]:
            h = node["health"]
            assert h is None or isinstance(h, (int, float)), (
                f"Node {node['id']}: health should be float or None, got {type(h)}"
            )

    def test_in_scc_is_bool(self, analysis_output):
        for node in analysis_output["nodes"]:
            assert isinstance(node["in_scc"], bool)

    def test_is_articulation_is_bool(self, analysis_output):
        for node in analysis_output["nodes"]:
            assert isinstance(node["is_articulation"], bool)


# ---------------------------------------------------------------------------
# layers
# ---------------------------------------------------------------------------

class TestLayers:
    def test_layers_is_dict(self, analysis_output):
        assert isinstance(analysis_output["layers"], dict)

    def test_layers_non_empty(self, analysis_output):
        assert len(analysis_output["layers"]) > 0

    def test_layer_entries_have_mean(self, analysis_output):
        for layer, data in analysis_output["layers"].items():
            assert "mean" in data, f"Layer {layer!r} missing 'mean'"


# ---------------------------------------------------------------------------
# overall_health
# ---------------------------------------------------------------------------

class TestOverallHealth:
    def test_overall_health_is_float_or_none(self, analysis_output):
        oh = analysis_output["overall_health"]
        assert oh is None or isinstance(oh, (int, float))

    def test_overall_health_in_range_when_set(self, analysis_output):
        oh = analysis_output["overall_health"]
        if oh is not None:
            assert 0.0 <= oh <= 100.0


# ---------------------------------------------------------------------------
# top_spofs
# ---------------------------------------------------------------------------

class TestTopSpofs:
    def test_top_spofs_is_list(self, analysis_output):
        assert isinstance(analysis_output["top_spofs"], list)

    def test_top_spofs_entries_are_dicts_with_id(self, analysis_output):
        for spof in analysis_output["top_spofs"]:
            assert "id" in spof, f"SPOF entry missing 'id': {spof}"


# ---------------------------------------------------------------------------
# macro
# ---------------------------------------------------------------------------

class TestMacro:
    def test_macro_has_snapshot_key(self, analysis_output):
        assert "snapshot" in analysis_output["macro"]

    def test_macro_has_scenario_note(self, analysis_output):
        assert "scenario_note" in analysis_output["macro"]

    def test_snapshot_has_dff_and_dgs10(self, analysis_output):
        snap = analysis_output["macro"]["snapshot"]
        assert "dff" in snap
        assert "dgs10" in snap


# ---------------------------------------------------------------------------
# edge_stress
# ---------------------------------------------------------------------------

class TestEdgeStress:
    def test_edge_stress_is_list(self, analysis_output):
        assert isinstance(analysis_output["edge_stress"], list)


# ---------------------------------------------------------------------------
# cascades
# ---------------------------------------------------------------------------

class TestCascades:
    CASCADE_KEYS = {"scenario", "seeds", "direction", "affected_count", "reach"}

    def test_cascades_is_list(self, analysis_output):
        assert isinstance(analysis_output["cascades"], list)

    def test_cascades_has_three_scenarios(self, analysis_output):
        assert len(analysis_output["cascades"]) == 3, (
            f"Expected 3 cascade scenarios, got {len(analysis_output['cascades'])}"
        )

    def test_each_cascade_has_required_keys(self, analysis_output):
        for c in analysis_output["cascades"]:
            missing = self.CASCADE_KEYS - c.keys()
            assert not missing, f"Cascade missing keys: {missing}"

    def test_cascade_scenario_names_match_expected(self, analysis_output):
        names = {c["scenario"] for c in analysis_output["cascades"]}
        expected = {"tsm_disruption", "hyperscaler_capex_cut", "energy_bridge_loss"}
        assert names == expected, f"Cascade scenarios mismatch: {names}"

    def test_cascade_affected_count_non_negative(self, analysis_output):
        for c in analysis_output["cascades"]:
            assert c["affected_count"] >= 0

    def test_cascade_reach_in_0_1(self, analysis_output):
        for c in analysis_output["cascades"]:
            assert 0.0 <= c["reach"] <= 1.0, (
                f"Scenario {c['scenario']}: reach {c['reach']} out of [0,1]"
            )

    def test_tsm_disruption_direction_forward(self, analysis_output):
        tsm = next(c for c in analysis_output["cascades"] if c["scenario"] == "tsm_disruption")
        assert tsm["direction"] == "forward"

    def test_hyperscaler_capex_cut_direction_reverse(self, analysis_output):
        hyp = next(
            c for c in analysis_output["cascades"] if c["scenario"] == "hyperscaler_capex_cut"
        )
        assert hyp["direction"] == "reverse"
