"""News -> capital-web graph linkage (pure).

Two jobs, both strictly honest (spec section 5):

1. ``link_article`` — when a news item tags two entities that ALREADY share a
   curated capital-web edge, attach a badge that carries the CURATED edge's own
   ``certainty`` + ``source_url`` (verbatim). News NEVER upgrades curated certainty.

2. ``detect_candidate_edges`` — when a news item tags >=2 distinct entities AND
   uses a deal keyword AND those entities have NO curated edge between them, surface
   a *candidate* for the /map review queue. Candidates are ALWAYS ``unverified=true``,
   carry certainty 'reported'|'rumored', and NEVER assert a relationship. They are
   never auto-added to the graph.

Pure functions only — no I/O. The certainty wording comes from aiinvest.news.
"""
from __future__ import annotations

import datetime as _dt
import re

from aiinvest import news as _news


# Deal-language triggers for candidate detection. Matched on WORD BOUNDARIES
# (not substrings) so "background" never triggers "back" and "fundamental"
# never triggers "fund". Kept tight to limit false positives in the /map queue.
DEAL_KEYWORDS = (
    "supply", "supplies", "supplied", "invest", "invests", "invested",
    "investment", "stake", "partner", "partners", "partnership", "contract",
    "agreement", "acquire", "acquires", "acquired", "acquisition", "merger",
    "merges", "commitment", "joint venture", "funding", "backs", "purchase",
)

_DEAL_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(k) for k in DEAL_KEYWORDS) + r")\b")


def _has_deal_language(text):
    return bool(_DEAL_RE.search((text or "").lower()))


class EdgeIndex:
    """Lookup over curated capital-web edges.

    - ``undirected``: {frozenset({src, dst}): [edge, ...]} for pair membership.
    - ``directed``: {(src, dst): [edge, ...]} to preserve badge direction.
    """

    __slots__ = ("undirected", "directed")

    def __init__(self, undirected, directed):
        self.undirected = undirected
        self.directed = directed


def build_edge_index(edges):
    """Build an :class:`EdgeIndex` from curated capital-web edges.

    Edges with a missing/empty src or dst are skipped.
    """
    undirected = {}
    directed = {}
    for e in edges or []:
        src = e.get("src")
        dst = e.get("dst")
        if not src or not dst:
            continue
        undirected.setdefault(frozenset({src, dst}), []).append(e)
        directed.setdefault((src, dst), []).append(e)
    return EdgeIndex(undirected, directed)


def _edge_ref(edge):
    """Project a curated edge onto the badge ref shape (certainty NOT upgraded)."""
    return {
        "src": edge.get("src"),
        "dst": edge.get("dst"),
        "type": edge.get("type"),
        "attrs": edge.get("attrs") or {},
        "certainty": edge.get("certainty"),
        "source_url": edge.get("source_url"),
        "as_of": edge.get("as_of"),
    }


def link_article(tagged_entities, edge_index):
    """Return curated graph-edge refs for every pair of tagged entities that
    already share a curated edge. Certainty/source_url carried verbatim.
    """
    ents = sorted(set(tagged_entities or []))
    refs = []
    seen = set()
    for i in range(len(ents)):
        for j in range(i + 1, len(ents)):
            key = frozenset({ents[i], ents[j]})
            for edge in edge_index.undirected.get(key, []):
                marker = (edge.get("src"), edge.get("dst"), edge.get("type"))
                if marker in seen:
                    continue
                seen.add(marker)
                refs.append(_edge_ref(edge))
    return refs


def detect_candidate_edges(tagged_entities, title_summary, edge_index):
    """Surface candidate NEW deals for the /map review queue.

    Fires for an entity pair ONLY when ALL hold:
      - >=2 distinct entities are tagged,
      - a deal keyword is present in ``title_summary``,
      - NO curated edge already exists for that pair.

    Each candidate is ``unverified=True`` and never asserts a relationship.
    Certainty is 'rumored' when the text uses rumor language, else 'reported'.
    """
    ents = sorted(set(tagged_entities or []))
    if len(ents) < 2:
        return []
    text = (title_summary or "")
    if not _has_deal_language(text):
        return []
    certainty = _news.classify_certainty(text)
    if certainty == "filed":
        certainty = "reported"
    detected_at = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    out = []
    for i in range(len(ents)):
        for j in range(i + 1, len(ents)):
            a, b = ents[i], ents[j]
            if frozenset({a, b}) in edge_index.undirected:
                continue  # already curated -> not a candidate
            out.append({
                "src": a,
                "dst": b,
                "type_guess": "possible_deal",
                "evidence_title": text.strip(),
                "certainty": certainty,
                "url": None,
                "detected_at": detected_at,
                "unverified": True,
            })
    return out


def annotate(article, edge_index):
    """Return ``article`` plus ``graph_edges`` (curated links) and ``candidate_edges``.

    ``candidate_edges`` carry the article's ``url`` for provenance. The article's
    own ``tickers`` (from :func:`aiinvest.news.tag_entities`) are the tagged entities.
    """
    tagged = article.get("tickers") or []
    blob = f"{article.get('title', '')} {article.get('summary', '')}"
    out = dict(article)
    out["graph_edges"] = link_article(tagged, edge_index)
    candidates = detect_candidate_edges(tagged, blob, edge_index)
    for c in candidates:
        c["url"] = article.get("url")
    out["candidate_edges"] = candidates
    return out
