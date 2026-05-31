"""One-ticker dossier — the data-side capstone.

Composes the merged cross-source metrics, the ticker's filings, its catalysts, and its
relationship-web edges into a single provenance-stamped object. Pure assembly here;
`pull_dossier.py` does the live fetching.
"""
from __future__ import annotations

from . import capital_web, catalysts as cal, merge


def _layer_of(graph, symbol):
    for n in graph.get("nodes", []):
        if n["id"] == symbol:
            return n.get("layer")
    return None


def build_dossier(symbol, source_records, filings, catalysts_all, graph, now):
    """Assemble a dossier for one bare-symbol ticker (e.g. "NVDA")."""
    merged = merge.merge_symbol(symbol, source_records, now=now)
    return {
        "symbol": symbol,
        "layer": _layer_of(graph, symbol),
        "as_of": now,
        "metrics": merged["metrics"],
        "filings": list(filings or []),
        "catalysts": cal.by_entity(catalysts_all, symbol),
        "relationships": {
            "edges_from": capital_web.edges_from(graph, symbol),
            "edges_to": capital_web.edges_to(graph, symbol),
            "lab_exposure": capital_web.exposure_to_labs(graph, symbol),
        },
        "provenance": {"sources": sorted(source_records.keys())},
    }
