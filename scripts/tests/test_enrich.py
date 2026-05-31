"""RED tests for the AI edge-enrichment safety gate (deterministic)."""
from aiinvest import enrich

NODE_IDS = {"NVDA", "TSM", "MSFT", "anthropic"}


def _edge(**kw):
    base = {"src": "MSFT", "dst": "NVDA", "type": "customer",
            "attrs": {"transactions": [{"date": "2025-Q3", "amount": 1e9, "note": "GPU order"}]},
            "certainty": "reported", "source_class": "news-html",
            "source_url": "https://example.com/a", "quote": "Microsoft bought $1B of Nvidia GPUs."}
    base.update(kw)
    return base


# --- validate_extracted_edge ---

def test_accepts_well_formed_edge():
    assert enrich.validate_extracted_edge(_edge(), NODE_IDS) == []


def test_rejects_missing_quote():
    issues = enrich.validate_extracted_edge(_edge(quote="  "), NODE_IDS)
    assert any("quote" in i.lower() for i in issues)


def test_rejects_unknown_node():
    issues = enrich.validate_extracted_edge(_edge(dst="ZZZZ"), NODE_IDS)
    assert any("node" in i.lower() for i in issues)


def test_rejects_bad_certainty():
    issues = enrich.validate_extracted_edge(_edge(certainty="fact"), NODE_IDS)
    assert any("certainty" in i.lower() for i in issues)


def test_rejects_self_loop():
    issues = enrich.validate_extracted_edge(_edge(src="NVDA", dst="NVDA"), NODE_IDS)
    assert any("self" in i.lower() or "src" in i.lower() for i in issues)


def test_rejects_missing_source_url():
    issues = enrich.validate_extracted_edge(_edge(source_url=""), NODE_IDS)
    assert any("source" in i.lower() for i in issues)


# --- accept_edges ---

def test_accept_edges_splits_accepted_and_rejected():
    edges = [_edge(), _edge(quote="")]
    accepted, rejected = enrich.accept_edges(edges, NODE_IDS)
    assert len(accepted) == 1
    assert len(rejected) == 1
    assert rejected[0]["reasons"]


# --- resolve_node ---

def test_resolve_node_maps_name_to_id():
    idx = {"microsoft": "MSFT", "nvidia": "NVDA"}
    assert enrich.resolve_node("Microsoft", idx) == "MSFT"
    assert enrich.resolve_node("  nvidia ", idx) == "NVDA"


def test_resolve_node_unknown_is_none():
    assert enrich.resolve_node("Acme", {"microsoft": "MSFT"}) is None


# --- merge_enriched ---

def test_merge_tags_origin_and_dedupes_curated_winning():
    curated = [{"src": "MSFT", "dst": "NVDA", "type": "customer", "attrs": {}}]
    enriched = [
        {"src": "MSFT", "dst": "NVDA", "type": "customer", "attrs": {"note": "dup"}},  # dup -> dropped
        {"src": "TSM", "dst": "NVDA", "type": "customer", "attrs": {}},                # new -> kept
    ]
    merged = enrich.merge_enriched(curated, enriched)
    keys = [(e["src"], e["dst"], e["type"], e["origin"]) for e in merged]
    assert ("MSFT", "NVDA", "customer", "curated") in keys
    assert ("TSM", "NVDA", "customer", "ai-extracted") in keys
    assert len(merged) == 2  # dup not added twice
