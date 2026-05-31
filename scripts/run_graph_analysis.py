"""Integration runner — Graph Health & Resiliency Analysis.

Loads the merged AI capital web graph, computes structural metrics, health
scores, macro stress overlay, and runs the 3 pre-defined contagion scenarios.
Writes results to web/public/data/graph_analysis.json.

Usage::

    cd scripts
    python run_graph_analysis.py

Educational/research only — not investment advice.
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Ensure scripts/ is on the path when run from any CWD
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = pathlib.Path(__file__).parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from aiinvest import graph_metrics as gm
from aiinvest import health_score as hs
from aiinvest import macro_stress as ms
from aiinvest import contagion

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OUTPUT_PATH = (
    _SCRIPTS_DIR.parent / "web" / "public" / "data" / "graph_analysis.json"
)

_DISCLAIMER = (
    "Educational/research only - not financial advice. "
    "Structural/indicative; not a dollar-loss estimate."
)

_DEFAULT_MACRO_BASELINES: dict[str, float] = {
    "dff": 4.50,
    "dgs10": 4.25,
    "elec": 0.142,
}

_MACRO_SCENARIO_NOTE = (
    "Unit scenario +100bps; headline +200bps / +30% elec. "
    "Betas are analyst priors, not regressed. Indicative ordinal signal only."
)

_MAX_EDGE_STRESS_ROWS = 50  # cap for the JSON payload


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def run() -> None:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ------------------------------------------------------------------
    # 1. Load graph
    # ------------------------------------------------------------------
    print("Loading graph...")
    graph_dict = gm.load_graph()
    nodes_raw = graph_dict["nodes"]
    edges_raw = graph_dict["edges"]
    print(f"  {len(nodes_raw)} nodes, {len(edges_raw)} edges (before DiGraph dedup)")

    # ------------------------------------------------------------------
    # 2. Compute structural metrics
    # ------------------------------------------------------------------
    print("Computing graph metrics...")
    metrics = gm.compute(graph_dict)
    gm_nodes = metrics["nodes"]
    gm_graph = metrics["graph"]

    # Articulation point set (for quick lookup)
    ap_set = set(gm_graph["articulation_points"])

    # ------------------------------------------------------------------
    # 3. Compute health scores
    # ------------------------------------------------------------------
    print("Computing health scores...")
    health = hs.score(graph_dict)
    hs_nodes = health["nodes"]
    layers_out = health["layers"]
    overall_health = health["overall"]

    # ------------------------------------------------------------------
    # 4. Fetch macro snapshot (network — wrap in try/except)
    # ------------------------------------------------------------------
    print("Fetching macro snapshot from FRED...")
    macro_note_extra = ""
    try:
        snapshot = ms.fetch_macro_snapshot()
        print(
            f"  DFF={snapshot['dff']:.2f}%  DGS10={snapshot['dgs10']:.2f}%  "
            f"ELEC=${snapshot['elec']:.4f}/kWh"
        )
    except Exception as exc:
        print(f"  FRED unavailable ({exc}); using baseline values.")
        macro_note_extra = " FRED unavailable — baseline values used."
        snapshot = {
            **_DEFAULT_MACRO_BASELINES,
            "retrieved_at": generated_at,
        }

    # ------------------------------------------------------------------
    # 5. Stress graph
    # ------------------------------------------------------------------
    print("Stressing graph with macro overlay...")
    stress_result = ms.stress_graph(graph_dict, snapshot, _DEFAULT_MACRO_BASELINES)
    stressed_edges = stress_result["edges"]

    # Summarise edge stress — top rows sorted by lowest stress_score (most stressed)
    edge_stress_summary = sorted(
        stressed_edges, key=lambda e: e["stress_score"]
    )[:_MAX_EDGE_STRESS_ROWS]

    # ------------------------------------------------------------------
    # 6. Contagion — 3 scenarios
    # ------------------------------------------------------------------
    print("Running contagion scenarios...")
    cascades_out: list[dict] = []
    for scenario_name, scenario_cfg in contagion.SCENARIOS.items():
        seeds = scenario_cfg["seeds"]
        direction = scenario_cfg["direction"]
        result = contagion.independent_cascade(
            graph_dict,
            seeds=seeds,
            direction=direction,
            trials=200,
            rng_seed=0,
        )
        cascades_out.append(
            {
                "scenario": scenario_name,
                "seeds": seeds,
                "direction": direction,
                "affected_count": len(result["affected"]),
                "reach": result["reach"],
            }
        )
        print(
            f"  {scenario_name}: seeds={seeds}, direction={direction}, "
            f"affected={len(result['affected'])}, reach={result['reach']:.3f}"
        )

    # ------------------------------------------------------------------
    # 7. Assemble per-node output (sorted by pagerank desc)
    # ------------------------------------------------------------------
    node_id_map = {n["id"]: n for n in nodes_raw}

    nodes_list = []
    for nid, nm in gm_nodes.items():
        raw_node = node_id_map.get(nid, {})
        hs_entry = hs_nodes.get(nid, {})
        nodes_list.append(
            {
                "id": nid,
                "name": raw_node.get("name", nid),
                "layer": raw_node.get("layer", "unknown"),
                "health": hs_entry.get("score"),
                "components": hs_entry.get("components", {}),
                "ens": hs_entry.get("ens"),
                "flags": hs_entry.get("flags", []),
                "pagerank": nm["pagerank"],
                "betweenness": nm["betweenness"],
                "in_scc": nm["in_scc"],
                "is_articulation": nm["is_articulation"],
                "in_degree": nm["in_degree"],
                "out_degree": nm["out_degree"],
            }
        )

    nodes_list.sort(key=lambda n: n["pagerank"], reverse=True)

    # ------------------------------------------------------------------
    # 8. Top SPOFs (articulation points, ordered by betweenness desc)
    # ------------------------------------------------------------------
    top_spofs = [
        {
            "id": nid,
            "name": node_id_map.get(nid, {}).get("name", nid),
            "layer": node_id_map.get(nid, {}).get("layer", "unknown"),
            "betweenness": gm_nodes[nid]["betweenness"],
        }
        for nid in gm_graph["articulation_points"]
        if nid in gm_nodes
    ]
    top_spofs.sort(key=lambda x: x["betweenness"], reverse=True)

    # ------------------------------------------------------------------
    # 9. Print summary
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Overall health:  {overall_health:.1f}/100" if overall_health is not None else "Overall health: N/A")
    print(f"SPOFs (APs):     {len(gm_graph['articulation_points'])}")
    print(f"Bridges:         {len(gm_graph['bridges'])}")
    print(f"Fragility ratio: {gm_graph['fragility_ratio']:.3f}")
    print(f"Largest SCC:     {gm_graph['largest_scc_size']} nodes")
    print(f"Assortativity:   {gm_graph['assortativity']}")
    print()
    print("Top-3 by PageRank:")
    for node in nodes_list[:3]:
        print(f"  {node['id']:12s}  PR={node['pagerank']:.4f}  health={node['health']}")
    print()
    print("Cascade reaches:")
    for c in cascades_out:
        print(f"  {c['scenario']:30s}  affected={c['affected_count']:3d}  reach={c['reach']:.3f}")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 10. Build output JSON
    # ------------------------------------------------------------------
    output = {
        "generated_at": generated_at,
        "disclaimer": _DISCLAIMER,
        "graph": {
            "n_nodes": gm_graph["n_nodes"],
            "n_edges": gm_graph["n_edges"],
            "articulation_points": gm_graph["articulation_points"],
            "bridges": gm_graph["bridges"],
            "largest_scc_size": gm_graph["largest_scc_size"],
            "fragility_ratio": gm_graph["fragility_ratio"],
            "assortativity": gm_graph["assortativity"],
        },
        "nodes": nodes_list,
        "layers": layers_out,
        "overall_health": overall_health,
        "top_spofs": top_spofs,
        "macro": {
            "snapshot": {
                k: v
                for k, v in snapshot.items()
            },
            "scenario_note": _MACRO_SCENARIO_NOTE + macro_note_extra,
        },
        "edge_stress": edge_stress_summary,
        "cascades": cascades_out,
    }

    # ------------------------------------------------------------------
    # 11. Write JSON
    # ------------------------------------------------------------------
    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, default=str)

    print(f"\ngraph_analysis.json written to: {_OUTPUT_PATH}")


if __name__ == "__main__":
    run()
