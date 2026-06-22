"""AI edge-enrichment safety gate (deterministic).

The `edge-enricher` agent reads unstructured sources and emits candidate relationship
edges. This module is the gate between that AI output and the graph: it REJECTS any edge
that isn't quote-backed, node-resolved, and properly labelled — honoring the brief's Rule #5
(never launder a rumor into a fact). Accepted edges land in a separate ai-extracted store.
"""
from __future__ import annotations

import json

from . import capital_web

VALID_EDGE_TYPES = capital_web.VALID_EDGE_TYPES
VALID_CERTAINTY = capital_web.VALID_CERTAINTY


def validate_extracted_edge(edge, node_ids):
    """Return a list of rejection reasons (empty == accept)."""
    issues = []
    src, dst = edge.get("src"), edge.get("dst")
    if src not in node_ids:
        issues.append(f"unknown node (src): {src}")
    if dst not in node_ids:
        issues.append(f"unknown node (dst): {dst}")
    if src and src == dst:
        issues.append("self-loop (src == dst)")
    if edge.get("type") not in VALID_EDGE_TYPES:
        issues.append(f"invalid type: {edge.get('type')}")
    if edge.get("certainty") not in VALID_CERTAINTY:
        issues.append(f"invalid certainty: {edge.get('certainty')}")
    if not (edge.get("source_url") or "").strip():
        issues.append("missing source_url")
    if not (edge.get("quote") or "").strip():
        issues.append("missing quote (no quote -> no edge)")
    return issues


def accept_edges(edges, node_ids):
    """Split AI-emitted edges into (accepted, rejected). Rejected carry their reasons."""
    accepted, rejected = [], []
    for e in edges or []:
        reasons = validate_extracted_edge(e, node_ids)
        if reasons:
            rejected.append({**e, "reasons": reasons})
        else:
            accepted.append(e)
    return accepted, rejected


def resolve_node(name, name_index):
    """Map a company name to a node id via a name->id index (case-insensitive). None if unknown."""
    if not name:
        return None
    return name_index.get(str(name).strip().lower())


def build_name_index(graph, extra_aliases=None):
    """Build {name_lower: id} from graph nodes (id + name) plus optional aliases."""
    idx = {}
    for n in graph.get("nodes", []):
        idx[n["id"].lower()] = n["id"]
        if n.get("name"):
            idx[n["name"].lower()] = n["id"]
    for alias, nid in (extra_aliases or {}).items():
        idx[alias.lower()] = nid
    return idx


def merge_enriched(curated, enriched):
    """Combine curated + ai-extracted edges; tag origin; dedupe by (src,dst,type), curated wins."""
    out, seen = [], set()
    for e in curated:
        e = {**e, "origin": e.get("origin", "curated")}
        out.append(e)
        seen.add((e["src"], e["dst"], e["type"]))
    for e in enriched:
        key = (e["src"], e["dst"], e["type"])
        if key in seen:
            continue
        out.append({**e, "origin": e.get("origin", "ai-extracted")})
        seen.add(key)
    return out


def load_store(path):
    """Load the ai-extracted edge store (list); [] if absent."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return []


def save_store(path, edges):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(edges, fh, indent=2)
