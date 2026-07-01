"""Parse a reel KIT markdown (``reels_<date>_kit.md``) on the Python side.

Mirrors studio/src/main/kit.ts so the carousel builder reads the SAME authored kit the
Studio Kit page shows. KEY DIFFERENCE: this returns RAW field values (inline HTML kept) —
the carousel slides render HTML, whereas the Studio display parser strips it.

Public API:
    parse_cfg(md, ticker)      -> dict | None   (a stock CFG block, structured)
    parse_congress_card(md)    -> dict | None   (the congress section's card fields)
"""
from __future__ import annotations

import re


def _balanced_span(s, open_idx, oc, cc):
    """Return s[open_idx:close+1] for the delimiter opened at s[open_idx], respecting
    double-quoted strings so a delimiter inside a value never closes early. None if unbalanced.
    Ported from kit.ts balancedSpan."""
    depth = 0
    in_str = False
    i = open_idx
    while i < len(s):
        c = s[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == oc:
            depth += 1
        elif c == cc:
            depth -= 1
            if depth == 0:
                return s[open_idx:i + 1]
        i += 1
    return None


def _cfg_block(md, ticker):
    """Inner content of the ``"TICKER":{ ... }`` CFG block (braces stripped); None if absent."""
    start = md.find('"%s":{' % ticker.upper())
    if start < 0:
        return None
    open_idx = md.find("{", start)
    if open_idx < 0:
        return None
    span = _balanced_span(md, open_idx, "{", "}")
    return None if span is None else span[1:-1]


def _unescape(s):
    # JSON-ish string body: only un-escape \" and \\ ; keep HTML/entities verbatim.
    return s.replace('\\"', '"').replace("\\\\", "\\")


def _field(block, name):
    m = re.search(r'"%s"\s*:\s*"((?:[^"\\]|\\.)*)"' % re.escape(name), block, re.S)
    return _unescape(m.group(1)) if m else None


def _rows_tickers(block):
    """Tickers from ``"rows":[("TEAM",None),...]`` -> ['TEAM', ...] (values filled downstream)."""
    m = re.search(r'"rows"\s*:\s*\[([^\]]*)\]', block, re.S)
    if not m:
        return []
    return re.findall(r'"([^"]+)"', m.group(1))


def parse_cfg(md, ticker):
    """Structured stock CFG block, or None. Field values keep inline HTML."""
    block = _cfg_block(md, ticker)
    if block is None:
        return None
    return {
        "hero": _field(block, "hero"),
        "logo": _field(block, "logo"),
        "ex": _field(block, "ex"),
        "src": _field(block, "src"),
        "hook": {
            "kick": _field(block, "kick"),
            "head": _field(block, "head"),
            "sub": _field(block, "sub"),
        },
        "data": {
            "kick": _field(block, "data_kick"),
            "title": _field(block, "data_title"),
            "cap": _field(block, "data_cap"),
            "foot": _field(block, "data_foot"),
            "mode": _field(block, "mode"),
            "rows": _rows_tickers(block),
        },
        "takeaway": {
            "kick": _field(block, "tk_kick"),
            "big": _field(block, "big"),
            "unit": _field(block, "unit"),
            "label": _field(block, "tk_label"),
            "body": _field(block, "tk_body"),
        },
    }


def _congress_section(md):
    """The ``## REEL n — CONGRESS ...`` section text, or None."""
    for sec in md.split("\n## "):
        first = sec.split("\n", 1)[0]
        if re.search(r"\bCONGRESS\b", first.upper()):
            return sec
    return None


def _bt(sec, label_re):
    """Value of a ``- <label>: `value``` bullet (backtick-wrapped), or None."""
    m = re.search(r"-\s*%s[^:`]*:\s*`([^`]*)`" % label_re, sec, re.I)
    return m.group(1) if m else None


def parse_congress_card(md):
    """The congress section's card fields, or None if there's no congress section."""
    sec = _congress_section(md)
    if sec is None or "Congress card fields" not in sec:
        return None
    fields = sec.split("Congress card fields", 1)[1]

    chips_raw = _bt(fields, r"Chips")
    chips = chips_raw.split() if chips_raw else []

    big = big_label = None
    mb = re.search(r"Takeaway big number:\s*`([^`]*)`\s*\(label:\s*`([^`]*)`\)", fields, re.I)
    if mb:
        big, big_label = mb.group(1), mb.group(2)

    # Meta rows: nested ``- <key> -> `value` `` lines (arrow may be → or ->).
    meta = re.findall(r"-\s*([^\n`]+?)\s*(?:→|->)\s*`([^`]*)`", fields)
    meta = [(k.strip(), v) for k, v in meta]

    return {
        "hook_head": _bt(fields, r"Hook head"),
        "hook_sub": _bt(fields, r"Hook sub"),
        "pill": _bt(fields, r"Pill"),
        "name": _bt(fields, r"Name"),
        "subhead": _bt(fields, r"Subhead"),
        "chips": chips,
        "meta": meta,
        "big": big,
        "big_label": big_label,
        "body": _bt(fields, r"Takeaway body"),
        "footer": _bt(fields, r"Footer"),
    }
