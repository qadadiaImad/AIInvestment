"""News processing core — Playwright MCP fetches the pages; this layer processes them.

Serves brief Rule #5 (label filed / reported / rumored, never launder a rumor into a fact)
and Parts C/D (deals, catalysts). The fetch step is a Playwright Mode-A task (see
providers/README.md "News" row); these pure functions tag, classify, and dedupe the result.
"""
from __future__ import annotations

import datetime as _dt
import re
import xml.etree.ElementTree as _ET
from email.utils import parsedate_to_datetime as _parsedate

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


# Tickers that are also common English words, or too short to match reliably
# against free-text headlines. These are filtered OUT of the cross-text name
# index (the queried ticker is still tagged directly in pull_news). Without this,
# e.g. "AI" (C3.ai) / "ON" (ON Semi) / "SO" (Southern) false-tag almost every
# headline and explode the candidate-edge queue.
COMMON_WORD_TICKERS = frozenset({
    "now", "net", "arm", "app", "all", "are", "one", "new", "key", "car",
    "cash", "gold", "well", "real", "love", "life", "open", "core", "edge",
    "flow", "data", "tech", "info", "the", "and", "for", "you", "out", "own",
    "its", "his", "her", "see", "set", "big", "buy", "pay", "run", "top",
    "team", "fig", "leu", "play", "work", "fun", "band", "jobs", "bill", "hood",
})


def is_safe_alias(alias):
    """Whether ``alias`` is safe to match against free-text news.

    Rejects very short (<=2 char) symbols and common-English-word tickers that
    would false-tag (e.g. 'AI', 'ON', 'SO', 'NOW', 'ARM'). Multi-token or dotted
    company names (e.g. 'Arm Holdings', 'c3.ai') are always safe.
    """
    if not alias:
        return False
    a = alias.strip()
    if not a:
        return False
    if " " in a or "." in a:   # multi-token / dotted company name -> safe
        return True
    if len(a) <= 2:
        return False
    return a.lower() not in COMMON_WORD_TICKERS


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


def bare_symbol(ticker):
    """Strip an exchange prefix (``NYSE:VST`` -> ``VST``) and upper-case.

    Tolerates None / whitespace. Both Finnhub and Yahoo take bare symbols.
    """
    s = (ticker or "").strip()
    if ":" in s:
        s = s.split(":", 1)[1]
    return s.strip().upper()


def _epoch_to_iso(epoch):
    """Unix epoch seconds -> ISO-8601 UTC ('...Z'), or None on bad input."""
    if not isinstance(epoch, (int, float)) or isinstance(epoch, bool):
        return None
    try:
        d = _dt.datetime.fromtimestamp(epoch, tz=_dt.timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_finnhub(items):
    """Finnhub company-news rows -> list of raw{title,url,source,published(ISO),summary}.

    Finnhub returns ``datetime`` as Unix epoch seconds; normalize to ISO-8601 UTC.
    Tolerates a non-list payload (401/error bodies) and missing fields.
    """
    if not isinstance(items, list):
        return []
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        out.append({
            "title": it.get("headline"),
            "url": it.get("url"),
            "source": it.get("source"),
            "published": _epoch_to_iso(it.get("datetime")),
            "summary": it.get("summary"),
        })
    return out


def _rfc822_to_iso(s):
    """RFC-822 pubDate (e.g. 'Sun, 01 Jun 2025 12:30:00 GMT') -> ISO-8601 UTC, or None."""
    if not s or not isinstance(s, str):
        return None
    try:
        d = _parsedate(s)
    except (TypeError, ValueError):
        return None
    if d is None:
        return None
    if d.tzinfo is not None:
        d = d.astimezone(_dt.timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def _text_or_none(elem):
    if elem is None:
        return None
    t = (elem.text or "").strip()
    return t or None


def parse_yahoo_rss(xml_text):
    """Yahoo headline RSS 2.0 -> list of raw{title,url,source,published(ISO),summary}.

    Uses the stdlib ``xml.etree`` and tolerates missing fields and unparseable XML
    (returns [] rather than raising). ``source`` is stamped as 'Yahoo Finance' since
    the feed itself carries no per-item source field.
    """
    if not xml_text or not isinstance(xml_text, str):
        return []
    try:
        root = _ET.fromstring(xml_text)
    except _ET.ParseError:
        return []
    out = []
    for item in root.iter("item"):
        out.append({
            "title": _text_or_none(item.find("title")),
            "url": _text_or_none(item.find("link")),
            "source": "Yahoo Finance",
            "published": _rfc822_to_iso(_text_or_none(item.find("pubDate"))),
            "summary": _text_or_none(item.find("description")),
        })
    return out
