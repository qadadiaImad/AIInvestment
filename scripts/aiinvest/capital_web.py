"""Capital & relationship web (Part C) — who invests in / leases compute from whom.

Module is authoritative: nodes are built from the `ai_stack` universe plus curated
PRIVATE_NODES; edges are the curated, provenance-stamped EDGES below. `build_graph()`
assembles them; `capital_web.json` is a serialized snapshot (build_capital_web.py).
Facts + queries only — the "who has pricing power" interpretation is the analyst layer.
"""
from __future__ import annotations

import json

from . import ai_stack

VALID_CERTAINTY = {"filed", "reported", "rumored"}
VALID_EDGE_TYPES = {"equity_stake", "compute_commitment", "customer",
                    "voting_power", "subsidiary", "infra_partner"}

# Private / pre-IPO / non-ticker entities (not on the america scanner).
PRIVATE_NODES = [
    {"id": "openai", "name": "OpenAI", "type": "private", "ticker": None, "layer": "private-lab", "note": "IPO reported Q4 2026"},
    {"id": "anthropic", "name": "Anthropic", "type": "private", "ticker": None, "layer": "private-lab", "note": "IPO reported ~Oct 2026"},
    {"id": "xai", "name": "xAI", "type": "subsidiary", "ticker": None, "layer": "private-lab", "note": "folded into SpaceX"},
    {"id": "mistral", "name": "Mistral", "type": "private", "ticker": None, "layer": "private-lab", "note": ""},
    {"id": "cohere", "name": "Cohere", "type": "private", "ticker": None, "layer": "private-lab", "note": ""},
    {"id": "spacex", "name": "SpaceX", "type": "private", "ticker": None, "layer": "L2-infra", "note": "Colossus / Starlink"},
    {"id": "crusoe", "name": "Crusoe", "type": "private", "ticker": None, "layer": "L2-infra", "note": "neocloud"},
    {"id": "lambda", "name": "Lambda", "type": "private", "ticker": None, "layer": "L2-infra", "note": "neocloud"},
    {"id": "musk", "name": "Elon Musk", "type": "private", "ticker": None, "layer": "private-lab", "note": "control person"},
]

# Curated relationships from brief Part C. Each edge carries provenance + certainty.
_SRC = "brief Part C (late May 2026)"
_TS = "2026-05-30T12:00:00Z"


def _e(src, dst, etype, attrs, certainty="reported"):
    return {"src": src, "dst": dst, "type": etype, "attrs": attrs,
            "certainty": certainty, "source_class": "news-html",
            "source_url": _SRC, "as_of": "2026-05", "retrieved_at": _TS}


EDGES = [
    # Anthropic's multi-sourced compute stack + equity
    _e("GOOGL", "anthropic", "equity_stake", {"pct": 14, "cap_pct": 15}),
    _e("anthropic", "GOOGL", "compute_commitment", {"usd": 200e9, "power_gw": 1, "tpus": 1_000_000}),
    _e("AMZN", "anthropic", "equity_stake", {"usd": 13e9}),
    _e("anthropic", "AMZN", "compute_commitment", {"usd": 100e9, "power_gw": 5, "duration": "~decade"}),
    _e("anthropic", "spacex", "compute_commitment",
       {"usd_per_month": 1.25e9, "until": "2029-05", "power_mw": 300, "gpus": 220_000, "termination_days": 90}),
    _e("anthropic", "NVDA", "compute_commitment", {"note": "Nvidia capacity"}),
    _e("anthropic", "MSFT", "compute_commitment", {"note": "Microsoft capacity"}),
    # OpenAI
    _e("MSFT", "openai", "equity_stake", {"note": "equity + Azure"}),
    _e("MSFT", "openai", "infra_partner", {"note": "Azure compute"}),
    _e("ORCL", "openai", "infra_partner", {"note": "Stargate build-out"}),
    # SpaceX / xAI
    _e("xai", "spacex", "subsidiary", {"note": "wholly-owned; ~$250B implied"}),
    _e("musk", "spacex", "voting_power", {"pct": 85}),
    # --- Supply chain: leading-edge foundry (TSMC) ---
    _e("NVDA", "TSM", "customer", {"note": "leading-edge foundry"}),
    _e("AMD", "TSM", "customer", {"note": "leading-edge foundry"}),
    _e("AVGO", "TSM", "customer", {"note": "leading-edge foundry"}),
    _e("ARM", "TSM", "customer", {"note": "leading-edge foundry (licensed cores)"}),
    # --- HBM / memory ---
    _e("NVDA", "MU", "customer", {"note": "HBM"}),
    # --- Fab equipment: supplier -> customer (TSMC) ---
    _e("ASML", "TSM", "infra_partner", {"note": "EUV litho; supplier->customer"}),
    _e("AMAT", "TSM", "infra_partner", {"note": "fab equipment; supplier->customer"}),
    _e("LRCX", "TSM", "infra_partner", {"note": "fab equipment; supplier->customer"}),
    _e("KLAC", "TSM", "infra_partner", {"note": "process control; supplier->customer"}),
    # --- GPU buyers: hyperscalers & neoclouds purchase NVDA accelerators ---
    _e("MSFT", "NVDA", "customer", {"note": "GPU purchases"}),
    _e("AMZN", "NVDA", "customer", {"note": "GPU purchases"}),
    _e("GOOGL", "NVDA", "customer", {"note": "GPU purchases"}),
    _e("META", "NVDA", "customer", {"note": "GPU purchases"}),
    _e("ORCL", "NVDA", "customer", {"note": "GPU purchases"}),
    _e("CRWV", "NVDA", "customer", {"note": "GPU purchases"}),
    _e("NBIS", "NVDA", "customer", {"note": "GPU purchases"}),
    _e("IREN", "NVDA", "customer", {"note": "GPU purchases"}),
    # --- AI servers built on NVDA ---
    _e("DELL", "NVDA", "customer", {"note": "NVDA-based AI servers"}),
    _e("SMCI", "NVDA", "customer", {"note": "NVDA-based AI servers"}),
    _e("HPE", "NVDA", "customer", {"note": "NVDA-based AI servers"}),
    # --- Custom AI silicon / networking (Broadcom-designed ASICs) ---
    _e("GOOGL", "AVGO", "infra_partner", {"note": "custom AI accelerator (TPU) / networking"}),
    _e("META", "AVGO", "infra_partner", {"note": "custom AI accelerator (MTIA) / networking"}),
]


def build_graph():
    """Assemble the full graph: universe nodes (bare tickers) + private nodes + curated edges."""
    nodes = []
    for full in ai_stack.all_tickers():
        nodes.append({
            "id": full.split(":")[-1], "name": full.split(":")[-1],
            "type": "public", "ticker": full, "layer": ai_stack.layer_of(full), "note": "",
        })
    nodes.extend(PRIVATE_NODES)
    return {"nodes": nodes, "edges": list(EDGES)}


def load(path=None):
    """Load the serialized snapshot; falls back to build_graph() if no file given."""
    if path is None:
        return build_graph()
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _ids(graph):
    return {n["id"] for n in graph["nodes"]}


def validate(graph):
    """Return a list of integrity issues (empty == valid)."""
    ids = _ids(graph)
    issues = []
    for e in graph["edges"]:
        if e["src"] not in ids:
            issues.append(f"edge references undefined node (src): {e['src']}")
        if e["dst"] not in ids:
            issues.append(f"edge references undefined node (dst): {e['dst']}")
        if e.get("certainty") not in VALID_CERTAINTY:
            issues.append(f"invalid certainty: {e.get('certainty')} ({e['src']}->{e['dst']})")
        if e.get("type") not in VALID_EDGE_TYPES:
            issues.append(f"invalid edge type: {e.get('type')}")
        for field in ("source_class", "source_url", "retrieved_at"):
            if not e.get(field):
                issues.append(f"edge missing provenance '{field}' ({e['src']}->{e['dst']})")
    return issues


def edges_from(graph, node_id):
    return [e for e in graph["edges"] if e["src"] == node_id]


def edges_to(graph, node_id):
    return [e for e in graph["edges"] if e["dst"] == node_id]


def investors_of(graph, node_id):
    return [e["src"] for e in edges_to(graph, node_id) if e["type"] == "equity_stake"]


def investees_of(graph, node_id):
    return [e["dst"] for e in edges_from(graph, node_id) if e["type"] == "equity_stake"]


def exposure_to_labs(graph, ticker):
    """A public node's direct equity stakes in private labs."""
    priv = {n["id"] for n in graph["nodes"] if n["type"] in ("private", "subsidiary")}
    out = []
    for e in edges_from(graph, ticker):
        if e["type"] == "equity_stake" and e["dst"] in priv:
            out.append({"lab": e["dst"], "pct": e["attrs"].get("pct"),
                        "usd": e["attrs"].get("usd"), "certainty": e["certainty"]})
    return out


def termination_risk(graph, max_days=180):
    """compute_commitment edges with a short termination clause (single-counterparty exit risk)."""
    risky = []
    for e in graph["edges"]:
        if e["type"] == "compute_commitment":
            td = e["attrs"].get("termination_days")
            if td is not None and td <= max_days:
                risky.append(e)
    return risky


def counterparty_concentration(graph, node_id):
    """Group every edge touching node_id by the counterparty, summing dollar exposure."""
    conc = {}
    for e in edges_from(graph, node_id) + edges_to(graph, node_id):
        other = e["dst"] if e["src"] == node_id else e["src"]
        slot = conc.setdefault(other, {"usd": 0.0, "types": []})
        slot["types"].append(e["type"])
        for k in ("usd", "usd_per_month"):
            if isinstance(e["attrs"].get(k), (int, float)):
                slot["usd"] += e["attrs"][k]
    return conc


_LAYER_COLOR = {
    "L0-energy": "#f59e0b", "L1-chips": "#10b981", "L2-infra": "#3b82f6",
    "L3-models": "#8b5cf6", "L4-application": "#ec4899", "private-lab": "#ef4444",
}


def _edge_label(e):
    a = e["attrs"]
    bits = [e["type"].replace("_", " ")]
    if a.get("pct") is not None:
        bits.append(f"{a['pct']}%")
    if a.get("usd"):
        bits.append(f"${a['usd'] / 1e9:.0f}B")
    if a.get("usd_per_month"):
        bits.append(f"${a['usd_per_month'] / 1e9:.2f}B/mo")
    if a.get("termination_days"):
        bits.append(f"{a['termination_days']}d exit")
    return " · ".join(bits)


def to_html(graph, title="AI Capital & Relationship Web", include_all_nodes=True):
    """Return a standalone interactive HTML (vis-network) string.

    include_all_nodes=True (default) renders the whole field: every node in the
    graph, clustered/colored by layer, with edges overlaid. Edgeless nodes still
    appear (sized small). include_all_nodes=False keeps the legacy edge-only view.
    """
    by_id = {n["id"]: n for n in graph["nodes"]}
    touched = set()
    for e in graph["edges"]:
        touched.add(e["src"])
        touched.add(e["dst"])
    deg = {}
    for e in graph["edges"]:
        deg[e["src"]] = deg.get(e["src"], 0) + 1
        deg[e["dst"]] = deg.get(e["dst"], 0) + 1

    if include_all_nodes:
        render_ids = [n["id"] for n in graph["nodes"]]
    else:
        render_ids = sorted(touched)

    vis_nodes = []
    for nid in sorted(render_ids):
        n = by_id.get(nid, {"id": nid, "name": nid, "layer": "private-lab"})
        layer = n.get("layer")
        # Edgeless nodes get value 1 (small dot); connected nodes scale by degree.
        vis_nodes.append({
            "id": nid, "label": n.get("name", nid),
            "color": _LAYER_COLOR.get(layer, "#9ca3af"),
            "value": deg.get(nid, 1),
            "group": layer or "?",
            "title": f"{n.get('name', nid)} ({layer or '?'})",
        })
    vis_edges = []
    for e in graph["edges"]:
        ai = e.get("origin") == "ai-extracted"
        a = e.get("attrs", {}) or {}
        txns = a.get("transactions") or []
        txn_txt = "; ".join(
            (f"{t.get('date', '?')}: {t.get('amount', '')} {t.get('note', '')}").strip()
            for t in txns)
        title = f"{e['type']} · {e['certainty']} · {e.get('source_url', '')}"
        if txn_txt:
            title += f" · txns: {txn_txt}"
        if e.get("quote"):
            title += f" · quote: {e['quote']}"
        edge = {
            "from": e["src"], "to": e["dst"], "label": _edge_label(e),
            "arrows": "to",
            "dashes": ai or (e["certainty"] == "rumored"),
            "title": title,
        }
        if ai:
            edge["color"] = {"color": "#a78bfa", "opacity": 0.6}  # ai-extracted: dimmer violet
        vis_edges.append(edge)

    legend = " ".join(
        f"<span style='color:{c}'>●</span> {k}" for k, c in _LAYER_COLOR.items())
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  body {{ margin:0; font-family:system-ui,sans-serif; background:#0b0f17; color:#e5e7eb; }}
  #h {{ padding:10px 16px; }} #h b {{ font-size:18px; }}
  #legend {{ font-size:12px; color:#9ca3af; }}
  #net {{ width:100vw; height:calc(100vh - 64px); }}
</style></head>
<body>
  <div id="h"><b>{title}</b> &nbsp; <span style="font-size:12px;color:#9ca3af">
    solid = filed/reported · dashed = rumored · arrow = direction of money/control</span>
    <div id="legend">{legend}</div></div>
  <div id="net"></div>
<script>
  const nodes = new vis.DataSet({json.dumps(vis_nodes)});
  const edges = new vis.DataSet({json.dumps(vis_edges)});
  new vis.Network(document.getElementById('net'), {{nodes, edges}}, {{
    nodes: {{ shape:'dot', scaling:{{min:8,max:40}}, font:{{color:'#e5e7eb'}} }},
    edges: {{ font:{{color:'#9ca3af',size:10,strokeWidth:0}}, color:{{color:'#6b7280',highlight:'#fbbf24'}}, smooth:{{type:'dynamic'}} }},
    physics: {{ stabilization:true, barnesHut:{{gravitationalConstant:-8000,springLength:160}} }},
    interaction: {{ hover:true, tooltipDelay:120 }},
  }});
</script></body></html>"""
