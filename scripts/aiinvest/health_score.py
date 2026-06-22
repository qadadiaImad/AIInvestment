"""Tier-1 Topology Health Score for the AI capital web.

Computes a structural health score [0, 100] per connected node from a
graph_dict — the canonical ``{"nodes": [...], "edges": [...]}`` shape.

Formula (from the graph-resiliency feasibility spec):
    Score_topo(node) =
        30 * Concentration   # 1 - HHI_indegree / 10000
      + 30 * SPOF            # 1.0 if NOT articulation point; else max(0, 1-5*BC_norm)
      + 25 * Redundancy      # log1p(in_degree) / log1p(max_in_degree_in_layer)
      + 15 * Certainty       # mean incident-edge certainty weight

Each sub-component normalized to [0, 1] within the node's layer, then ×100.

Guardrails:
  - Nodes in the largest SCC are capped at 85.
  - Nodes with exactly 1 inbound edge are floored at 40 and flagged
    "topology-estimate".
  - Isolated nodes (total degree == 0) receive score=None, flags=["no-data"]
    and are excluded from layer / overall aggregates.

Certainty weights: filed=1.0, reported=0.7, rumored=0.3.
ENS (Effective Number of Suppliers) = 10000 / HHI (None when HHI=0).

Educational/research only — not investment advice.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import networkx as nx

from . import graph_metrics as gm

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CERTAINTY_WEIGHT: dict[str, float] = {
    "filed": 1.0,
    "reported": 0.7,
    "rumored": 0.3,
}
_DEFAULT_CERTAINTY = 0.7  # treat unknown as reported

_WEIGHTS = {
    "concentration": 30,
    "spof": 30,
    "redundancy": 25,
    "certainty": 15,
}
assert sum(_WEIGHTS.values()) == 100

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = ["score"]


def score(graph_dict: dict) -> dict:
    """Compute the Tier-1 Topology Score for every node.

    Parameters
    ----------
    graph_dict:
        ``{"nodes": [{id, name, type, ticker, layer}, ...],
           "edges": [{src, dst, type, attrs, certainty, origin, source_url}, ...]}``

    Returns
    -------
    dict:
        ``{
            "nodes":  { id: {score, components:{concentration,spof,redundancy,certainty},
                             ens, flags} },
            "layers": { layer: {mean, min, max, n} },
            "overall": <degree-weighted mean of connected nodes>
          }``
    """
    nodes: list[dict] = graph_dict.get("nodes", [])
    edges: list[dict] = graph_dict.get("edges", [])

    # ------------------------------------------------------------------
    # Build DiGraph for directed metrics
    # ------------------------------------------------------------------
    node_by_id = {n["id"]: n for n in nodes}
    node_ids = list(node_by_id)

    DG = nx.DiGraph()
    DG.add_nodes_from(node_ids)
    for e in edges:
        src, dst = e.get("src"), e.get("dst")
        if src and dst and src in DG and dst in DG:
            DG.add_edge(src, dst)

    # Undirected projection for articulation-point detection
    UG = nx.Graph()
    UG.add_nodes_from(node_ids)
    for u, v in DG.edges():
        UG.add_edge(u, v)

    # ------------------------------------------------------------------
    # Structural metrics from graph_metrics.compute()
    # ------------------------------------------------------------------
    gm_result = gm.compute(graph_dict)
    gm_nodes = gm_result["nodes"]

    # Largest SCC membership (for the cap guardrail)
    all_sccs = list(nx.strongly_connected_components(DG))
    largest_scc = max(all_sccs, key=len) if all_sccs else set()
    # Only cap if largest SCC has > 1 member (non-trivial)
    if len(largest_scc) <= 1:
        largest_scc = set()

    # Betweenness normalised (already normalised by networkx: 0..1)
    betweenness: dict[str, float] = {
        nid: gm_nodes[nid]["betweenness"] for nid in node_ids
    }

    # ------------------------------------------------------------------
    # Per-node inbound-edge collection (all edges, not deduplicated)
    # ------------------------------------------------------------------
    # We need the raw multi-edges for HHI and certainty calculations.
    inbound_edges: dict[str, list[dict]] = defaultdict(list)
    incident_edges: dict[str, list[dict]] = defaultdict(list)  # in OR out
    for e in edges:
        src, dst = e.get("src"), e.get("dst")
        if src and dst and src in node_by_id and dst in node_by_id:
            inbound_edges[dst].append(e)
            incident_edges[src].append(e)
            incident_edges[dst].append(e)

    # ------------------------------------------------------------------
    # Classify nodes: isolated (degree 0 in DiGraph) vs connected
    # ------------------------------------------------------------------
    total_degree = dict(DG.degree())

    def _is_isolated(nid: str) -> bool:
        return total_degree.get(nid, 0) == 0

    # ------------------------------------------------------------------
    # Per-layer: compute max in_degree (for Redundancy normalisation)
    # Only over connected nodes.
    # ------------------------------------------------------------------
    layer_of: dict[str, str] = {n["id"]: n.get("layer", "unknown") for n in nodes}
    in_degree = dict(DG.in_degree())

    layer_max_indegree: dict[str, int] = defaultdict(int)
    for nid in node_ids:
        if not _is_isolated(nid):
            layer = layer_of[nid]
            layer_max_indegree[layer] = max(
                layer_max_indegree[layer], in_degree.get(nid, 0)
            )

    # ------------------------------------------------------------------
    # Sub-component calculators
    # ------------------------------------------------------------------

    def _concentration(nid: str) -> tuple[float, float | None]:
        """Return (concentration_component, ens)."""
        in_edges = inbound_edges[nid]
        if not in_edges:
            # No inbound edges: concentration = 0 (maximally concentrated / no suppliers)
            return 0.0, None

        # HHI on edge COUNT shares by counterparty
        counterparty_counts: dict[str, int] = defaultdict(int)
        for e in in_edges:
            counterparty_counts[e["src"]] += 1
        total = sum(counterparty_counts.values())

        hhi = sum((cnt / total) ** 2 for cnt in counterparty_counts.values()) * 10000
        ens = 10000.0 / hhi if hhi > 0 else None
        concentration = 1.0 - hhi / 10000.0
        return concentration, ens

    def _spof(nid: str) -> float:
        """Return spof component (1.0 if not AP; else max(0, 1 - 5*betweenness_norm))."""
        is_ap = gm_nodes[nid]["is_articulation"]
        if not is_ap:
            return 1.0
        bc = betweenness.get(nid, 0.0)
        return max(0.0, 1.0 - 5.0 * bc)

    def _redundancy(nid: str) -> float:
        """Return redundancy component = log1p(in_degree) / log1p(max_in_degree_in_layer)."""
        layer = layer_of[nid]
        max_ind = layer_max_indegree.get(layer, 0)
        if max_ind == 0:
            return 0.0
        ind = in_degree.get(nid, 0)
        return math.log1p(ind) / math.log1p(max_ind)

    def _certainty(nid: str) -> float:
        """Return mean certainty weight of all incident edges."""
        inc = incident_edges[nid]
        if not inc:
            return _DEFAULT_CERTAINTY
        weights = [
            _CERTAINTY_WEIGHT.get(e.get("certainty", ""), _DEFAULT_CERTAINTY)
            for e in inc
        ]
        return sum(weights) / len(weights)

    # ------------------------------------------------------------------
    # Compute raw scores for all connected nodes
    # ------------------------------------------------------------------
    raw_scores: dict[str, dict] = {}

    for nid in node_ids:
        if _is_isolated(nid):
            raw_scores[nid] = {
                "score": None,
                "components": {
                    "concentration": 0.0,
                    "spof": 0.0,
                    "redundancy": 0.0,
                    "certainty": 0.0,
                },
                "ens": None,
                "flags": ["no-data"],
                "_isolated": True,
            }
            continue

        conc, ens = _concentration(nid)
        spof_v = _spof(nid)
        redund_v = _redundancy(nid)
        cert_v = _certainty(nid)

        raw = (
            _WEIGHTS["concentration"] * conc
            + _WEIGHTS["spof"] * spof_v
            + _WEIGHTS["redundancy"] * redund_v
            + _WEIGHTS["certainty"] * cert_v
        )

        flags: list[str] = []

        # Guardrail: SCC cap
        if nid in largest_scc:
            raw = min(raw, 85.0)

        # Guardrail: single-inbound floor + flag
        if in_degree.get(nid, 0) == 1:
            if raw < 40.0:
                raw = 40.0
            flags.append("topology-estimate")

        raw_scores[nid] = {
            "score": float(raw),
            "components": {
                "concentration": conc,
                "spof": spof_v,
                "redundancy": redund_v,
                "certainty": cert_v,
            },
            "ens": ens,
            "flags": flags,
            "_isolated": False,
        }

    # ------------------------------------------------------------------
    # Layer aggregates (exclude isolated nodes)
    # ------------------------------------------------------------------
    layer_node_scores: dict[str, list[float]] = defaultdict(list)
    for nid in node_ids:
        rs = raw_scores[nid]
        if not rs["_isolated"] and rs["score"] is not None:
            layer_node_scores[layer_of[nid]].append(rs["score"])

    layers: dict[str, dict] = {}
    for layer, sc_list in layer_node_scores.items():
        layers[layer] = {
            "mean": sum(sc_list) / len(sc_list),
            "min": min(sc_list),
            "max": max(sc_list),
            "n": len(sc_list),
        }

    # ------------------------------------------------------------------
    # Overall: degree-weighted mean of connected nodes
    # ------------------------------------------------------------------
    overall: float | None = None
    weighted_sum = 0.0
    weight_total = 0.0
    for nid in node_ids:
        rs = raw_scores[nid]
        if rs["_isolated"] or rs["score"] is None:
            continue
        deg = total_degree.get(nid, 0)
        w = float(deg)
        weighted_sum += w * rs["score"]
        weight_total += w

    if weight_total > 0:
        overall = weighted_sum / weight_total
    elif any(
        not raw_scores[nid]["_isolated"] and raw_scores[nid]["score"] is not None
        for nid in node_ids
    ):
        # All connected nodes have degree 0 after isolation filter (edge case)
        connected = [
            raw_scores[nid]["score"]
            for nid in node_ids
            if not raw_scores[nid]["_isolated"] and raw_scores[nid]["score"] is not None
        ]
        overall = sum(connected) / len(connected)

    # ------------------------------------------------------------------
    # Clean up internal key before returning
    # ------------------------------------------------------------------
    nodes_out: dict[str, dict[str, Any]] = {}
    for nid in node_ids:
        rs = raw_scores[nid]
        nodes_out[nid] = {
            "score": rs["score"],
            "components": rs["components"],
            "ens": rs["ens"],
            "flags": rs["flags"],
        }

    return {
        "nodes": nodes_out,
        "layers": layers,
        "overall": float(overall) if overall is not None else None,
    }
