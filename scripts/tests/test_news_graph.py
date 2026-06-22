"""RED tests for news->graph linkage (pure).

Honesty rails (spec 5):
- graph_edges reflect the CURATED edge's own certainty + source_url (never upgraded from news).
- candidate_edges fire ONLY with >=2 distinct tagged entities + a deal keyword + NO existing
  curated edge for that pair; always unverified=true; never asserts a relationship.
"""
from aiinvest import news_graph


# A small curated edge set mirroring capital_web.edges shape.
EDGES = [
    {"src": "anthropic", "dst": "GOOGL", "type": "compute_commitment",
     "attrs": {"usd": 40000000000.0}, "certainty": "reported",
     "source_url": "brief Part C", "as_of": "2026-05"},
    {"src": "GOOGL", "dst": "anthropic", "type": "equity_stake",
     "attrs": {"pct": 14}, "certainty": "reported",
     "source_url": "brief Part C", "as_of": "2026-05"},
    {"src": "AMZN", "dst": "anthropic", "type": "equity_stake",
     "attrs": {"usd": 13000000000.0}, "certainty": "reported",
     "source_url": "brief Part C", "as_of": "2026-05"},
]


# --- build_edge_index(): undirected pair lookup + directed map ---

def test_build_edge_index_groups_pairs_undirected():
    idx = news_graph.build_edge_index(EDGES)
    key = frozenset({"anthropic", "GOOGL"})
    assert key in idx.undirected
    # both directions for the GOOGL/anthropic pair land in the same bucket
    assert len(idx.undirected[key]) == 2


def test_build_edge_index_has_directed_lookup():
    idx = news_graph.build_edge_index(EDGES)
    assert ("AMZN", "anthropic") in idx.directed
    assert ("anthropic", "AMZN") not in idx.directed


def test_build_edge_index_handles_empty():
    idx = news_graph.build_edge_index([])
    assert idx.undirected == {} or len(idx.undirected) == 0


# --- link_article(): tagged entities -> curated graph_edge refs ---

def test_link_article_returns_curated_refs_for_tagged_pair():
    idx = news_graph.build_edge_index(EDGES)
    refs = news_graph.link_article(["anthropic", "GOOGL"], idx)
    types = sorted(r["type"] for r in refs)
    assert types == ["compute_commitment", "equity_stake"]
    # certainty carried verbatim from the curated edge, NOT upgraded
    for r in refs:
        assert r["certainty"] == "reported"
        assert r["source_url"] == "brief Part C"
        assert "attrs" in r and "as_of" in r


def test_link_article_no_pair_no_refs():
    idx = news_graph.build_edge_index(EDGES)
    assert news_graph.link_article(["NVDA", "MSFT"], idx) == []


def test_link_article_single_entity_no_refs():
    idx = news_graph.build_edge_index(EDGES)
    assert news_graph.link_article(["anthropic"], idx) == []


# --- detect_candidate_edges(): the review-queue gate ---

def test_candidate_fires_with_two_entities_keyword_and_no_existing_edge():
    idx = news_graph.build_edge_index(EDGES)
    cands = news_graph.detect_candidate_edges(
        ["NVDA", "OpenAI"],
        "Nvidia announces a multi-billion compute supply deal with OpenAI",
        idx,
    )
    assert len(cands) == 1
    c = cands[0]
    assert {c["src"], c["dst"]} == {"NVDA", "OpenAI"}
    assert c["unverified"] is True
    assert c["certainty"] in ("reported", "rumored")
    assert c["evidence_title"]
    assert c["detected_at"]


def test_candidate_suppressed_when_curated_edge_exists():
    idx = news_graph.build_edge_index(EDGES)
    # anthropic/GOOGL already have curated edges -> no candidate even with a keyword
    cands = news_graph.detect_candidate_edges(
        ["anthropic", "GOOGL"],
        "Anthropic deepens its compute partnership and investment with Google",
        idx,
    )
    assert cands == []


def test_candidate_suppressed_without_deal_keyword():
    idx = news_graph.build_edge_index(EDGES)
    cands = news_graph.detect_candidate_edges(
        ["NVDA", "OpenAI"],
        "Nvidia and OpenAI executives spoke at a conference today",
        idx,
    )
    assert cands == []


def test_candidate_suppressed_with_one_entity():
    idx = news_graph.build_edge_index(EDGES)
    cands = news_graph.detect_candidate_edges(
        ["NVDA"], "Nvidia signs a huge supply deal", idx)
    assert cands == []


def test_candidate_rumor_language_marks_rumored():
    idx = news_graph.build_edge_index(EDGES)
    cands = news_graph.detect_candidate_edges(
        ["NVDA", "OpenAI"],
        "Nvidia is reportedly in talks for a supply deal with OpenAI",
        idx,
    )
    assert cands[0]["certainty"] == "rumored"


# --- annotate(): article gains graph_edges + candidate_edges ---

def test_annotate_adds_both_keys():
    idx = news_graph.build_edge_index(EDGES)
    article = {
        "title": "Anthropic compute commitment with Google expands",
        "summary": "",
        "tickers": ["anthropic", "GOOGL"],
    }
    out = news_graph.annotate(article, idx)
    assert "graph_edges" in out and "candidate_edges" in out
    # curated pair -> graph_edges present, candidate suppressed
    assert len(out["graph_edges"]) == 2
    assert out["candidate_edges"] == []


def test_annotate_surfaces_candidate_for_new_pair():
    idx = news_graph.build_edge_index(EDGES)
    article = {
        "title": "Microsoft strikes a multi-year supply agreement with OpenAI",
        "summary": "",
        "tickers": ["MSFT", "OpenAI"],
    }
    out = news_graph.annotate(article, idx)
    assert out["graph_edges"] == []
    assert len(out["candidate_edges"]) == 1
    assert out["candidate_edges"][0]["unverified"] is True


def test_deal_keyword_is_word_boundary_not_substring():
    idx = news_graph.build_edge_index(EDGES)
    # 'background' contains 'back', 'fundamental' contains 'fund' -> must NOT fire.
    out = news_graph.detect_candidate_edges(
        ["AAPL", "DELL"],
        "Dell unveils a laptop; background and fundamental details only",
        idx)
    assert out == []
    # a real, word-boundary deal verb DOES fire.
    out2 = news_graph.detect_candidate_edges(
        ["AAPL", "DELL"], "Apple and Dell announce a supply partnership", idx)
    assert len(out2) == 1
    assert out2[0]["unverified"] is True
