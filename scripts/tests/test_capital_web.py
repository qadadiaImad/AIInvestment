"""RED tests for the capital/relationship web (Part C)."""
from aiinvest import capital_web as cw


def _edge(src, dst, etype, attrs, certainty="reported"):
    return {"src": src, "dst": dst, "type": etype, "attrs": attrs,
            "certainty": certainty, "source_class": "news-html",
            "source_url": "x", "as_of": "2026-05", "retrieved_at": "2026-05-30T12:00:00Z"}


G = {
    "nodes": [
        {"id": "GOOGL", "name": "Alphabet", "type": "public", "ticker": "NASDAQ:GOOGL", "layer": "L2-infra"},
        {"id": "AMZN", "name": "Amazon", "type": "public", "ticker": "NASDAQ:AMZN", "layer": "L2-infra"},
        {"id": "anthropic", "name": "Anthropic", "type": "private", "ticker": None, "layer": "private-lab"},
        {"id": "spacex", "name": "SpaceX", "type": "private", "ticker": None, "layer": "L2-infra"},
    ],
    "edges": [
        _edge("GOOGL", "anthropic", "equity_stake", {"pct": 14, "cap_pct": 15}),
        _edge("AMZN", "anthropic", "equity_stake", {"usd": 13e9}),
        _edge("anthropic", "spacex", "compute_commitment", {"usd_per_month": 1.25e9, "termination_days": 90}),
    ],
}


# --- validate() ---

def test_validate_clean_graph_has_no_issues():
    assert cw.validate(G) == []


def test_validate_flags_dangling_edge():
    bad = {"nodes": G["nodes"], "edges": G["edges"] + [_edge("GOOGL", "ghost", "customer", {})]}
    issues = cw.validate(bad)
    assert any("ghost" in i for i in issues)


def test_validate_flags_bad_certainty():
    bad = {"nodes": G["nodes"], "edges": [_edge("GOOGL", "anthropic", "equity_stake", {}, certainty="fact")]}
    issues = cw.validate(bad)
    assert any("certainty" in i for i in issues)


# --- queries ---

def test_investors_of_returns_equity_holders():
    assert set(cw.investors_of(G, "anthropic")) == {"GOOGL", "AMZN"}


def test_exposure_to_labs_finds_googl_anthropic_stake():
    exp = cw.exposure_to_labs(G, "GOOGL")
    assert len(exp) == 1
    assert exp[0]["lab"] == "anthropic"
    assert exp[0]["pct"] == 14


def test_termination_risk_flags_short_exit_lease():
    risky = cw.termination_risk(G, max_days=180)
    assert len(risky) == 1
    assert risky[0]["src"] == "anthropic" and risky[0]["dst"] == "spacex"


def test_counterparty_concentration_groups_by_counterparty():
    conc = cw.counterparty_concentration(G, "anthropic")
    assert set(conc.keys()) == {"GOOGL", "AMZN", "spacex"}


# --- visualization ---

def test_to_html_is_self_contained_with_vis_network():
    html = cw.to_html(G)
    assert "vis-network" in html
    assert "anthropic" in html
    assert html.strip().lower().startswith("<!doctype html")


def test_to_html_renders_rumored_edge_dashed():
    rumored = {"nodes": G["nodes"],
               "edges": [_edge("GOOGL", "anthropic", "equity_stake", {}, certainty="rumored")]}
    html = cw.to_html(rumored)
    assert "dashes" in html and "true" in html


# --- real seed integrity ---

def test_real_graph_passes_validation():
    graph = cw.build_graph()
    assert cw.validate(graph) == []


def test_real_graph_includes_full_universe_plus_private_labs():
    graph = cw.build_graph()
    ids = {n["id"] for n in graph["nodes"]}
    assert "NVDA" in ids          # from ai_stack universe
    assert "anthropic" in ids     # private lab
    assert "openai" in ids


# --- expanded graph + whole-field rendering ---

def test_to_html_default_renders_edgeless_universe_node():
    """Default include_all_nodes=True must render even a node that touches no edge."""
    graph = cw.build_graph()
    # DUOL is in the universe but has no curated edge -> still must appear.
    assert all(e["src"] != "DUOL" and e["dst"] != "DUOL" for e in graph["edges"])
    html = cw.to_html(graph)
    assert '"DUOL"' in html or "'DUOL'" in html


def test_to_html_edge_only_mode_excludes_edgeless_node():
    graph = cw.build_graph()
    html = cw.to_html(graph, include_all_nodes=False)
    assert "DUOL" not in html
    assert "anthropic" in html  # touched by edges, still present


def test_expanded_graph_validates_clean():
    graph = cw.build_graph()
    assert cw.validate(graph) == []


def test_expanded_graph_has_supply_chain_edge():
    graph = cw.build_graph()
    assert any(e["src"] == "NVDA" and e["dst"] == "TSM" and e["type"] == "customer"
               for e in graph["edges"])


def test_to_html_marks_ai_extracted_edge_distinct():
    graph = {
        "nodes": [{"id": "MSFT", "name": "MSFT", "layer": "L2-infra"},
                  {"id": "NVDA", "name": "NVDA", "layer": "L1-chips"}],
        "edges": [{"src": "MSFT", "dst": "NVDA", "type": "customer",
                   "attrs": {"transactions": [{"date": "2025-Q3", "amount": 1e9, "note": "GPUs"}]},
                   "certainty": "reported", "source_url": "u", "origin": "ai-extracted",
                   "quote": "Microsoft bought GPUs"}],
    }
    html = cw.to_html(graph)
    assert "Microsoft bought GPUs" in html   # quote in tooltip
    assert "a78bfa" in html                   # ai-extracted violet styling
