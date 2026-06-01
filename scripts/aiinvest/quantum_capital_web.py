"""Quantum capital & relationship web (mirrors capital_web.py).

Reuses capital_web's edge/validate/query helpers verbatim (imported, not duplicated).
Nodes = quantum screener tickers (as public) + GIANT_NODES (graph-only bridges) +
PRIVATE_NODES / FOREIGN_NODES (watch-list). Edges = curated, provenance-stamped
relationships from the quantum universe research (acquisitions, cloud partnerships,
suppliers, spinouts, equity stakes).

Educational/research only — not investment advice. Every edge carries source_url,
as_of and certainty (reported/filed/rumored). build_graph() must pass validate().
"""
from __future__ import annotations

from . import quantum_stack
# Reuse capital_web helpers directly — do not redefine them.
from .capital_web import (  # noqa: F401
    _e,
    validate,
    edges_from,
    edges_to,
    investors_of,
    investees_of,
    counterparty_concentration,
    load,
    to_html,
    VALID_EDGE_TYPES,
)
from . import capital_web as _cw

# New quantum edge types beyond the AI taxonomy. validate() reads VALID_EDGE_TYPES as a
# module global at call time, so registering here makes the new types valid without
# editing capital_web.py.
NEW_EDGE_TYPES = {"acquired", "cloud_on", "supplier", "spinout"}
_cw.VALID_EDGE_TYPES |= NEW_EDGE_TYPES

# Source provenance for the curated quantum seed (from the universe research doc).
_SRC = "quantum universe research (2026-06-01)"


def _qe(src, dst, etype, attrs, certainty="reported", as_of="2026-05", source_url=_SRC):
    """Quantum edge with explicit as_of/source_url (mirrors capital_web._e shape)."""
    return {"src": src, "dst": dst, "type": etype, "attrs": attrs,
            "certainty": certainty, "source_class": "news-html",
            "source_url": source_url, "as_of": as_of, "retrieved_at": "2026-06-01T00:00:00Z"}


# Cloud / QaaS endpoints (hyperscaler quantum clouds) as graph nodes.
CLOUD_NODES = [
    {"id": "AWS", "name": "AWS Braket", "layer": "Q2-cloud", "note": "Amazon quantum cloud (QaaS)"},
    {"id": "AZURE", "name": "Azure Quantum", "layer": "Q2-cloud", "note": "Microsoft quantum cloud (QaaS)"},
    {"id": "GCP", "name": "Google Cloud (Quantum AI)", "layer": "Q2-cloud", "note": "Google quantum cloud (QaaS)"},
]


EDGES = [
    # --- Acquisitions / subsidiaries (capital) ---
    _qe("IONQ", "oxford_ionics", "acquired", {"usd": 1.075e9}, certainty="reported", as_of="2025-09"),
    _qe("IONQ", "id_quantique", "subsidiary", {"note": "QKD/QRNG"}),
    _qe("IONQ", "lightsynq", "subsidiary", {"note": "quantum networking"}),
    _qe("QBTS", "quantum_circuits", "acquired", {"usd": 550e6}, certainty="reported", as_of="2026-01"),
    _qe("HON", "quantinuum", "subsidiary", {"note": "majority owner"}),
    _qe("WKEY", "LAES", "subsidiary", {"note": "WISeKey parent of SEALSQ"}),
    _qe("GOOGL", "sandboxaq", "spinout", {"note": "Alphabet 2022 spinout"}, as_of="2022-03"),
    # --- Cloud / QaaS (cloud_on: src offered on dst's quantum cloud) ---
    _qe("IONQ", "AWS", "cloud_on", {"note": "Braket"}),
    _qe("IONQ", "AZURE", "cloud_on", {"note": "Azure Quantum"}),
    _qe("IONQ", "GCP", "cloud_on", {"note": "Google Cloud"}),
    _qe("RGTI", "AWS", "cloud_on", {"note": "Braket"}),
    _qe("quera", "AWS", "cloud_on", {"note": "Braket"}),
    _qe("pasqal", "AZURE", "cloud_on", {"note": "Azure Quantum"}),
    _qe("atom_computing", "AZURE", "infra_partner", {"note": "Microsoft partnership"}),
    # --- Customers of native quantum clouds ---
    _qe("quantinuum", "JPM", "customer", {"note": "finance use-cases"}),
    _qe("quantinuum", "GS", "customer", {"note": "finance use-cases"}, certainty="reported"),
    # --- Compute / co-processing partnerships ---
    _qe("RGTI", "NVDA", "infra_partner", {"note": "NVQLink quantum-classical interconnect"}),
    # --- Equity stakes (invest) ---
    _qe("NVDA", "alice_bob", "equity_stake", {"note": "NVentures investment"}),
    _qe("BAH", "seeqc", "equity_stake", {"note": "Booz Allen strategic investment"}),
    # --- Suppliers (supplier: src supplies dst) ---
    _qe("nkt_photonics", "IONQ", "supplier", {"note": "lasers"}),
    _qe("bluefors", "RGTI", "supplier", {"note": "dilution refrigerators (cryo)"}),
    _qe("bluefors", "IBM", "supplier", {"note": "dilution refrigerators (cryo)"}),
    _qe("quantum_machines", "RGTI", "supplier", {"note": "qubit control hardware"}),
    _qe("quantum_machines", "QBTS", "supplier", {"note": "qubit control hardware"}),
]


# Supplier nodes referenced by edges that aren't already in the stack node lists.
_EXTRA_SUPPLIER_NODES = [
    {"id": "nkt_photonics", "name": "NKT Photonics", "layer": "Q0-enabling", "note": "lasers / photonic crystal fibre"},
]


def build_graph():
    """Assemble: screener tickers (public) + GIANT + PRIVATE/FOREIGN + cloud/supplier nodes + curated edges."""
    nodes = []
    seen = set()

    def _add(node):
        if node["id"] not in seen:
            seen.add(node["id"])
            nodes.append(node)

    # Screener tickers -> public nodes.
    for full in quantum_stack.all_tickers():
        sym = full.split(":")[-1]
        _add({
            "id": sym, "name": sym, "type": "public", "ticker": full,
            "layer": quantum_stack.layer_of(full), "note": "",
        })

    # Graph-only diversified giants/bridges.
    for g in quantum_stack.GIANT_NODES:
        _add({"id": g["id"], "name": g["name"], "type": "giant", "ticker": None,
              "layer": g["layer"], "note": g["note"]})

    # Hyperscaler quantum clouds.
    for c in CLOUD_NODES:
        _add({"id": c["id"], "name": c["name"], "type": "cloud", "ticker": None,
              "layer": c["layer"], "note": c["note"]})

    # Private / pre-IPO + foreign watch-list nodes.
    for n in quantum_stack.PRIVATE_NODES:
        _add({"id": n["id"], "name": n["name"], "type": "private", "ticker": None,
              "layer": n["layer"], "note": n["note"]})
    for n in quantum_stack.FOREIGN_NODES:
        _add({"id": n["id"], "name": n["name"], "type": "foreign", "ticker": None,
              "layer": n["layer"], "note": n["note"]})

    # Extra supplier nodes referenced only by edges.
    for n in _EXTRA_SUPPLIER_NODES:
        _add({"id": n["id"], "name": n["name"], "type": "private", "ticker": None,
              "layer": n["layer"], "note": n["note"]})

    return {"nodes": nodes, "edges": list(EDGES)}
