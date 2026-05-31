"""Shock-propagation models for the AI capital web.

Implements Independent Cascade Model (ICM) and Linear Threshold Model (LTM)
over the directed graph_dict structure used throughout this package.

Transmission-probability map (certainty → prob):
    filed    → 0.85
    reported → 0.60
    rumored  → 0.25
    fallback → 0.10  (any unrecognised certainty value)

direction="forward"  — follow edges in their natural direction (supply shock:
    a disrupted supplier propagates downstream to its customers).
direction="reverse"  — follow edges backward (demand shock: a customer pulling
    back hurts its supplier; activate SRC when DST is shocked).

Educational/research only — not investment advice.
"""
from __future__ import annotations

from typing import Any

import networkx as nx
import numpy as np

# ---------------------------------------------------------------------------
# Certainty → transmission probability
# ---------------------------------------------------------------------------

_DEFAULT_PROBS: dict[str, float] = {
    "filed": 0.85,
    "reported": 0.60,
    "rumored": 0.25,
}
_FALLBACK_PROB = 0.10

# ---------------------------------------------------------------------------
# Pre-defined scenario seeds (spec §5 / CLAUDE.md task brief)
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, dict[str, Any]] = {
    "tsm_disruption": {
        "seeds": ["TSM"],
        "direction": "forward",
    },
    "hyperscaler_capex_cut": {
        "seeds": ["MSFT", "AMZN", "GOOGL", "META"],
        "direction": "reverse",
    },
    "energy_bridge_loss": {
        "seeds": ["GEV"],
        "direction": "forward",
    },
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_digraph(graph_dict: dict) -> nx.DiGraph:
    """Build a networkx DiGraph from graph_dict (deduplicates parallel edges)."""
    G = nx.DiGraph()
    for node in graph_dict.get("nodes", []):
        G.add_node(node["id"], **node)
    for edge in graph_dict.get("edges", []):
        src, dst = edge["src"], edge["dst"]
        certainty = edge.get("certainty", "")
        # DiGraph: last edge wins on same (src, dst) pair — store certainty.
        G.add_edge(src, dst, certainty=certainty, type=edge.get("type", ""))
    return G


def _prob(certainty: str, override: dict[str, float] | None) -> float:
    """Return transmission probability for a certainty label."""
    table = override if override is not None else _DEFAULT_PROBS
    return table.get(certainty, _FALLBACK_PROB)


def _neighbors_in_direction(G: nx.DiGraph, node: str, direction: str) -> list[str]:
    """Return neighbors to attempt transmission to, based on direction.

    forward  — node's successors (out-edges)
    reverse  — node's predecessors (in-edges)
    """
    if direction == "forward":
        return list(G.successors(node))
    return list(G.predecessors(node))


def _edge_certainty(G: nx.DiGraph, src: str, dst: str, direction: str) -> str:
    """Return the certainty label for the edge being traversed."""
    if direction == "forward":
        return G.edges[src, dst].get("certainty", "")
    # reverse: traversing from dst back to src; the edge is (src, dst) in G
    return G.edges[src, dst].get("certainty", "")


# ---------------------------------------------------------------------------
# Independent Cascade Model
# ---------------------------------------------------------------------------

def independent_cascade(
    graph_dict: dict,
    seeds: list[str],
    direction: str = "reverse",
    trials: int = 200,
    rng_seed: int = 0,
    _prob_override: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Run the Independent Cascade Model over graph_dict.

    Parameters
    ----------
    graph_dict:
        Canonical ``{"nodes": [...], "edges": [...]}`` dict.
    seeds:
        List of node ids to shock (the initial active set).
    direction:
        ``"forward"`` — follow edges outward (supply shock).
        ``"reverse"`` — follow edges backward (demand shock). Default per spec.
    trials:
        Number of Monte-Carlo trials. Results averaged. Default 200.
    rng_seed:
        Seed for numpy RNG; guarantees reproducibility.
    _prob_override:
        Internal testing hook — replace the certainty→prob table entirely.
        Pass ``{"filed": 1.0, "reported": 1.0, "rumored": 1.0}`` to force
        deterministic full propagation in tests.

    Returns
    -------
    dict with:
        ``"affected"`` — list of node ids that activated (mean across trials,
            only nodes activated in **every** trial when P=1.0; more precisely,
            nodes with mean activation > 0 — reported as the union across
            trials weighted by reach).
        ``"reach"``    — mean fraction of non-seed nodes activated per trial.
    """
    G = _build_digraph(graph_dict)
    all_nodes = set(G.nodes())
    seed_set = set(seeds) & all_nodes  # ignore seeds not in graph

    non_seed_nodes = all_nodes - seed_set
    n_non_seed = len(non_seed_nodes)

    if n_non_seed == 0 or not seed_set:
        return {"affected": [], "reach": 0.0}

    rng = np.random.default_rng(rng_seed)

    # Track activation counts per node across trials
    activation_counts: dict[str, int] = {n: 0 for n in non_seed_nodes}
    total_activated_sum = 0

    for _ in range(trials):
        # One ICM trial
        active = set(seed_set)
        newly_active = set(seed_set)

        while newly_active:
            next_wave: set[str] = set()
            for node in newly_active:
                for neighbor in _neighbors_in_direction(G, node, direction):
                    if neighbor in active:
                        continue
                    # Get certainty of the traversed edge
                    if direction == "forward":
                        cert = G.edges[node, neighbor].get("certainty", "")
                    else:
                        # reverse: node is dst in G, neighbor is src
                        cert = G.edges[neighbor, node].get("certainty", "")
                    p = _prob(cert, _prob_override)
                    if rng.random() < p:
                        next_wave.add(neighbor)
            active |= next_wave
            newly_active = next_wave

        activated_this_trial = active - seed_set
        total_activated_sum += len(activated_this_trial)
        for n in activated_this_trial:
            activation_counts[n] += 1

    mean_reach = total_activated_sum / (trials * n_non_seed)

    # "affected" = nodes activated in at least 1 trial (mean fraction > 0)
    # Sorted for determinism in output
    affected = sorted(n for n, cnt in activation_counts.items() if cnt > 0)

    return {"affected": affected, "reach": float(mean_reach)}


# ---------------------------------------------------------------------------
# Linear Threshold Model
# ---------------------------------------------------------------------------

def linear_threshold(
    graph_dict: dict,
    seeds: list[str],
    direction: str = "forward",
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Run the deterministic Linear Threshold Model over graph_dict.

    A non-seed node activates when the weighted share of its active
    in/out-neighbors (by certainty weight) **strictly exceeds** ``threshold``.

    Certainty weights: filed→0.85, reported→0.60, rumored→0.25, else→0.10.

    Parameters
    ----------
    graph_dict:
        Canonical ``{"nodes": [...], "edges": [...]}`` dict.
    seeds:
        List of node ids to shock (the initial active set).
    direction:
        ``"forward"`` — a node activates when active fraction of its
            in-neighbors exceeds threshold (classic LTM on directed graph).
        ``"reverse"`` — a node activates when active fraction of its
            out-neighbors exceeds threshold.
    threshold:
        Activation threshold (strict >). Default 0.5.

    Returns
    -------
    dict with:
        ``"affected"`` — list of non-seed node ids that activated, in
            activation order (deterministic).
    """
    G = _build_digraph(graph_dict)
    all_nodes = set(G.nodes())
    seed_set = set(seeds) & all_nodes

    active = set(seed_set)
    changed = True

    while changed:
        changed = False
        for node in list(all_nodes - active):
            # Determine the "influence neighbors" based on direction
            if direction == "forward":
                # Node activates based on fraction of its in-neighbors active
                influence_neighbors = list(G.predecessors(node))
                edge_weight = lambda nb: _prob(G.edges[nb, node].get("certainty", ""), None)
            else:
                # Reverse: node activates based on fraction of its out-neighbors active
                influence_neighbors = list(G.successors(node))
                edge_weight = lambda nb: _prob(G.edges[node, nb].get("certainty", ""), None)

            if not influence_neighbors:
                continue

            total_weight = sum(edge_weight(nb) for nb in influence_neighbors)
            active_weight = sum(edge_weight(nb) for nb in influence_neighbors if nb in active)

            if total_weight == 0:
                continue

            fraction = active_weight / total_weight
            if fraction > threshold:
                active.add(node)
                changed = True

    affected = sorted(active - seed_set)
    return {"affected": affected}
