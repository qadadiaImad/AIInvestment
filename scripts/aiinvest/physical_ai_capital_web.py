"""Physical-AI / magnet-chain capital & relationship web (mirrors quantum_capital_web.py).

Reuses capital_web's validate/query helpers. Nodes = screener tickers (bare symbols) +
GIANT_NODES (graph-only bridges) + PRIVATE_NODES (watch-list) + a few extra counterparties
referenced only by edges. Edges = curated, provenance-stamped relationships — every edge
below cites the page it was read from on 2026-09-22 (the explainer-doc research); nothing
is recalled from memory. Direction follows the repo convention: customer = src buys from
dst; supplier = src supplies dst; equity_stake = src invests in dst; infra_partner = src
supplies capacity/manufacturing to dst.

Educational/research only — not investment advice. build_graph() must pass validate().
"""
from __future__ import annotations

from . import physical_ai_stack as pas
from . import capital_web as _cw
from .capital_web import (  # noqa: F401
    validate, edges_from, edges_to, investors_of, investees_of, counterparty_concentration,
)

NEW_EDGE_TYPES = {"supplier"}
_cw.VALID_EDGE_TYPES |= NEW_EDGE_TYPES

_TS = "2026-09-22T00:00:00Z"

_MP = ("https://mpmaterials.com/news/mp-materials-announces-transformational-public-private-"
       "partnership-with-the-department-of-defense-to-accelerate-u-s-rare-earth-magnet-independence/")
_REX_CN = "https://rareearthexchanges.com/news/china-rare-earth-magnet-ecosystem/"
_NEO_IN = ("https://investornews.com/critical-minerals-rare-earths/neo-performance-materials-opens-"
           "europes-largest-magnet-facility-europes-landmark-critical-minerals-project/")
_NEO_EE = "https://www.neomaterials.com/estonia/"
_VULCAN = "https://en.wikipedia.org/wiki/Vulcan_Elements"
_USAR = "https://en.wikipedia.org/wiki/USA_Rare_Earth"
_NOVEON = "https://rare-earth-mining.com/noveon-magnetics/"
_KOID = "https://kraneshares.com/humanoid-robotics-etf-top-performing-stocks-in-the-koid-portfolio/"
_EF_DA = "https://discoveryalert.com/energy-fuels-white-mesa-heavy-rare-earth-expansion-2026/"


def _pe(src, dst, etype, attrs, source_url, certainty="reported", as_of="2026-09",
        source_class="news-html"):
    return {"src": src, "dst": dst, "type": etype, "attrs": attrs, "certainty": certainty,
            "source_class": source_class, "source_url": source_url, "as_of": as_of,
            "retrieved_at": _TS}


# Counterparties that appear only on edges.
EXTRA_NODES = [
    {"id": "USGOV", "name": "US Government (Commerce / OSC)", "type": "giant", "layer": "P2-magnets",
     "note": "equity + loans into USAR and Vulcan"},
    {"id": "sanctuary", "name": "Sanctuary AI", "type": "private", "layer": "P4-robots", "note": "Phoenix humanoid"},
    {"id": "donald_project", "name": "Donald Project JV (Australia)", "type": "private", "layer": "P0-upstream",
     "note": "monazite concentrate to White Mesa"},
    {"id": "LG", "name": "LG Electronics", "type": "giant", "layer": "P3-actuators", "note": "Noveon closed-loop recycling"},
    {"id": "ABB", "name": "ABB Motion", "type": "giant", "layer": "P3-actuators", "note": "Noveon motor customer"},
]

EDGES = [
    # US Department of Defense <-> MP Materials (July 2025 package)
    _pe("DOD", "MP", "equity_stake", {"usd": 400e6, "note": "convertible preferred at $30.03; ~15% as-converted"},
        _MP, certainty="filed", as_of="2025-07"),
    _pe("DOD", "MP", "customer", {"note": "100% of 10X magnet output for 10 years; $110/kg NdPr floor"},
        _MP, certainty="filed", as_of="2025-07"),
    # Shenghe Resources holds ~3% of MP
    _pe("600392", "MP", "equity_stake", {"pct": 3}, _REX_CN, as_of="2026-09"),
    # Neo Narva feedstock and offtake
    _pe("LYC", "NEO", "supplier", {"note": "light rare-earth feedstock for Narva"}, _NEO_IN, as_of="2025-10"),
    _pe("MP", "NEO", "supplier", {"note": "feedstock source named by Neo"}, _NEO_IN, as_of="2025-10"),
    _pe("BOSCH", "NEO", "customer", {"note": "multi-year MoU, Narva traction-motor magnets"}, _NEO_EE, as_of="2025-09"),
    # Vulcan Elements supply chain and funding
    _pe("UUUU", "vulcan", "supplier", {"note": "rare-earth materials"}, _VULCAN, as_of="2025-11"),
    _pe("AREC", "vulcan", "supplier", {"note": "ReElement Technologies recycled rare earths"}, _VULCAN, as_of="2025-11"),
    _pe("USGOV", "vulcan", "equity_stake", {"usd": 50e6, "note": "Commerce CHIPS-funded equity; plus $620M OSC loan"},
        _VULCAN, as_of="2025-11"),
    # USA Rare Earth: US government stake
    _pe("USGOV", "USAR", "equity_stake", {"usd": 1.6e9, "pct": 10, "note": "debt and equity, January 2026"},
        _USAR, as_of="2026-01"),
    # Noveon customers
    _pe("GM", "noveon", "customer", {"note": "EV magnets"}, _NOVEON),
    _pe("ABB", "noveon", "customer", {"note": "motors"}, _NOVEON),
    _pe("6594", "noveon", "customer", {"note": "Nidec Motor Corporation"}, _NOVEON),
    _pe("LG", "noveon", "infra_partner", {"note": "closed-loop magnet recycling from Jan 2026"}, _NOVEON, as_of="2026-01"),
    # Magna x Sanctuary AI
    _pe("MGA", "sanctuary", "infra_partner", {"note": "humanoid deployment partnership"}, _KOID),
    # Energy Fuels feedstock
    _pe("donald_project", "UUUU", "supplier", {"note": "8,500 to 9,500 tpa monazite concentrate"}, _EF_DA),
]


def build_graph():
    nodes, seen = [], set()

    def _add(node):
        if node["id"] not in seen:
            seen.add(node["id"])
            nodes.append(node)

    for full in pas.all_tickers():
        sym = full.split(":")[-1]
        _add({"id": sym, "name": sym, "type": "public", "ticker": full,
              "layer": pas.layer_of(full), "note": ""})
    for g in pas.GIANT_NODES:
        _add({"id": g["id"], "name": g["name"], "type": "giant", "ticker": None,
              "layer": g["layer"], "note": g.get("note", "")})
    for n in pas.PRIVATE_NODES:
        _add({"id": n["id"], "name": n["name"], "type": "private", "ticker": None,
              "layer": n["layer"], "note": n.get("note", "")})
    for n in EXTRA_NODES:
        _add({"id": n["id"], "name": n["name"], "type": n["type"], "ticker": None,
              "layer": n["layer"], "note": n.get("note", "")})
    return {"nodes": nodes, "edges": list(EDGES)}
