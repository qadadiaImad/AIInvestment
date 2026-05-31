"""News processing core — Playwright MCP fetches the pages; this layer processes them.

Serves brief Rule #5 (label filed / reported / rumored, never launder a rumor into a fact)
and Parts C/D (deals, catalysts). The fetch step is a Playwright Mode-A task (see
providers/README.md "News" row); these pure functions tag, classify, and dedupe the result.
"""
from __future__ import annotations

import re

_FILED = ("filed", "s-1", "10-k", "8-k", "prospectus", "sec filing", "registration statement")
_RUMOR = ("rumor", "rumored", "reportedly", "in talks", "could ", "may ", "is said to",
          "sources say", "weighing", "considering", "mulling", "explor")
_REPORTED = ("announced", "confirmed", "unveiled", "launched", "reported record", "posted")


def classify_certainty(text):
    """Map article text to one of: 'filed' | 'rumored' | 'reported' (default reported)."""
    t = (text or "").lower()
    if any(k in t for k in _FILED):
        return "filed"
    if any(k in t for k in _RUMOR):
        return "rumored"
    return "reported"


def build_name_index(aliases_map):
    """alias_map: {label: [aliases]} -> {alias_lower: label}."""
    index = {}
    for label, aliases in aliases_map.items():
        for a in aliases:
            index[a.lower()] = label
    return index


def tag_entities(text, name_index):
    """Return the sorted, de-duplicated labels whose alias appears (word-boundary) in text."""
    t = (text or "").lower()
    found = set()
    for alias, label in name_index.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", t):
            found.add(label)
    return sorted(found)


def normalize_article(raw, retrieved_at, name_index):
    """Stamp + enrich a raw extracted article with tags and certainty."""
    blob = f"{raw.get('title', '')} {raw.get('summary', '')}"
    return {
        "title": raw.get("title"),
        "url": raw.get("url"),
        "source": raw.get("source"),
        "published": raw.get("published"),
        "summary": raw.get("summary"),
        "tickers": tag_entities(blob, name_index),
        "certainty": classify_certainty(blob),
        "retrieved_at": retrieved_at,
        "source_class": "news-html",
    }


def dedupe(articles):
    """Keep the first article per URL, preserving order."""
    seen, out = set(), []
    for a in articles:
        u = a.get("url")
        if u not in seen:
            seen.add(u)
            out.append(a)
    return out
