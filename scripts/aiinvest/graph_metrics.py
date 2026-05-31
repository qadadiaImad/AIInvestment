"""Graph topology & resiliency metrics for the AI capital web.

Computes structural metrics (PageRank, betweenness, eigenvector centrality,
articulation points, bridges, SCCs, k-core, fragility ratio) from a
graph_dict — the canonical ``{"nodes": [...], "edges": [...]}`` shape used
throughout this package.

Directed DiGraph for flow/degree/PageRank/betweenness/SCC.
Undirected projection for eigenvector, articulation points, bridges, k-core.

Educational/research only — not investment advice.
"""
from __future__ import annotations

import random
from typing import Any

import networkx as nx

from . import capital_web, enrich

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = ["load_graph", "compute"]


def load_graph() -> dict:
    """Build and return a graph_dict from the curated capital_web + ai-extracted store.

    Reproduces the ~392-edge graph (before DiGraph dedup to ~342).
    Returns ``{"nodes": [...], "edges": [...]}``.
    """
    g = capital_web.build_graph()
    store = enrich.load_store(
        "C:/Users/imadq/AIInvestment/capital_web_enriched.json"
    )
    merged = enrich.merge_enriched(g["edges"], store)
    return {"nodes": g["nodes"], "edges": merged}


def compute(graph_dict: dict) -> dict:
    """Compute structural topology metrics from a graph_dict.

    Parameters
    ----------
    graph_dict:
        ``{"nodes": [{id, name, type, ticker, layer}, ...],
           "edges": [{src, dst, type, attrs, certainty, origin, source_url}, ...]}``

    Returns
    -------
    dict with two top-level keys:

    ``"nodes"`` — mapping ``node_id -> {in_degree, out_degree, pagerank,
        betweenness, eigenvector, kcore, in_scc, is_articulation}``

    ``"graph"`` — ``{n_nodes, n_edges, articulation_points, bridges, sccs,
        largest_scc_size, assortativity, fragility_ratio}``

    All metrics derived purely from graph_dict (no network calls).
    """
    nodes: list[dict] = graph_dict.get("nodes", [])
    edges: list[dict] = graph_dict.get("edges", [])

    node_ids = [n["id"] for n in nodes]

    # ------------------------------------------------------------------
    # Build directed DiGraph (deduplicates parallel edges automatically)
    # ------------------------------------------------------------------
    DG = nx.DiGraph()
    DG.add_nodes_from(node_ids)
    for e in edges:
        src, dst = e.get("src"), e.get("dst")
        if src and dst and src in DG and dst in DG:
            DG.add_edge(src, dst)

    # ------------------------------------------------------------------
    # Build undirected projection (for eigenvector, APs, bridges, k-core)
    # ------------------------------------------------------------------
    UG = nx.Graph()
    UG.add_nodes_from(node_ids)
    for u, v in DG.edges():
        UG.add_edge(u, v)

    # ------------------------------------------------------------------
    # Directed metrics
    # ------------------------------------------------------------------
    in_deg = dict(DG.in_degree())
    out_deg = dict(DG.out_degree())

    pagerank = nx.pagerank(DG, alpha=0.85) if DG.number_of_nodes() > 0 else {}
    betweenness = (
        nx.betweenness_centrality(DG, normalized=True)
        if DG.number_of_nodes() > 0
        else {}
    )

    # Strongly connected components — only non-trivial (size > 1) reported
    all_sccs = list(nx.strongly_connected_components(DG))
    nontrivial_sccs = [sorted(s) for s in all_sccs if len(s) > 1]
    in_scc_set: set[str] = set()
    for scc in nontrivial_sccs:
        in_scc_set.update(scc)

    largest_scc_size = max((len(s) for s in all_sccs), default=0)

    # ------------------------------------------------------------------
    # Undirected metrics
    # ------------------------------------------------------------------
    kcore = nx.core_number(UG) if UG.number_of_nodes() > 0 else {}

    # Eigenvector centrality with convergence guard
    eigenvector: dict[str, float | None] = {}
    try:
        ev = nx.eigenvector_centrality(UG, max_iter=1000, tol=1e-6)
        eigenvector = {n: float(v) for n, v in ev.items()}
    except (nx.PowerIterationFailedConvergence, nx.NetworkXException):
        try:
            # fallback: undirected projection again with more iterations
            ev = nx.eigenvector_centrality_numpy(UG)
            eigenvector = {n: float(v) for n, v in ev.items()}
        except Exception:
            eigenvector = {n: None for n in node_ids}  # type: ignore[assignment]

    # Articulation points (nodes whose removal increases connected components)
    ap_set: set[str] = set(nx.articulation_points(UG)) if UG.number_of_nodes() > 1 else set()

    # Bridges
    try:
        bridge_list = [[u, v] for u, v in nx.bridges(UG)]
    except nx.NetworkXError:
        bridge_list = []

    # Degree assortativity (can raise if < 2 edges or degenerate degree sequence)
    assortativity: float | None = None
    try:
        assortativity = float(nx.degree_assortativity_coefficient(DG))
    except (nx.NetworkXError, ZeroDivisionError, ValueError):
        assortativity = None

    # ------------------------------------------------------------------
    # Fragility ratio — targeted vs. random percolation
    # ------------------------------------------------------------------
    fragility_ratio = _fragility_ratio(UG, top_k=5, random_trials=20, seed=42)

    # ------------------------------------------------------------------
    # Assemble per-node output
    # ------------------------------------------------------------------
    node_metrics: dict[str, dict[str, Any]] = {}
    for nid in node_ids:
        node_metrics[nid] = {
            "in_degree": in_deg.get(nid, 0),
            "out_degree": out_deg.get(nid, 0),
            "pagerank": pagerank.get(nid, 0.0),
            "betweenness": betweenness.get(nid, 0.0),
            "eigenvector": eigenvector.get(nid),
            "kcore": kcore.get(nid, 0),
            "in_scc": nid in in_scc_set,
            "is_articulation": nid in ap_set,
        }

    graph_metrics: dict[str, Any] = {
        "n_nodes": DG.number_of_nodes(),
        "n_edges": DG.number_of_edges(),
        "articulation_points": sorted(ap_set),
        "bridges": bridge_list,
        "sccs": nontrivial_sccs,
        "largest_scc_size": largest_scc_size,
        "assortativity": assortativity,
        "fragility_ratio": fragility_ratio,
    }

    return {"nodes": node_metrics, "graph": graph_metrics}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _lcc_size(G: nx.Graph) -> int:
    """Return the size of the largest connected component of an undirected graph."""
    if G.number_of_nodes() == 0:
        return 0
    return max(len(c) for c in nx.connected_components(G))


def _fragility_ratio(
    UG: nx.Graph,
    top_k: int = 5,
    random_trials: int = 5,
    seed: int = 42,
) -> float:
    """Compute fragility ratio = targeted_drop / mean_random_drop.

    Targeted: remove the top-k nodes by (undirected) degree; measure drop in LCC.
    Random: over ``random_trials`` seeded trials, remove k random nodes; average drop.

    >1 means the graph is more harmed by targeted attack than random failure.
    Returns 0.0 for degenerate graphs (< top_k+1 nodes or no drop possible).
    """
    n = UG.number_of_nodes()
    if n <= top_k:
        return 0.0

    baseline = _lcc_size(UG)
    if baseline == 0:
        return 0.0

    # Targeted removal: top-k by degree (ties broken by node id for determinism)
    degree_sorted = sorted(UG.nodes(), key=lambda v: (-UG.degree(v), v))
    targeted_nodes = degree_sorted[:top_k]
    targeted_G = UG.copy()
    targeted_G.remove_nodes_from(targeted_nodes)
    targeted_drop = baseline - _lcc_size(targeted_G)

    # Random removal: averaged over seeded trials
    rng = random.Random(seed)
    all_nodes = list(UG.nodes())
    random_drops = []
    for trial in range(random_trials):
        chosen = rng.sample(all_nodes, top_k)
        trial_G = UG.copy()
        trial_G.remove_nodes_from(chosen)
        random_drops.append(baseline - _lcc_size(trial_G))

    mean_random_drop = sum(random_drops) / len(random_drops) if random_drops else 0.0

    if mean_random_drop <= 0.0:
        # Targeted drop > 0 but random always 0 → extremely targeted-fragile
        return float(targeted_drop) if targeted_drop > 0 else 0.0

    return float(targeted_drop) / float(mean_random_drop)
