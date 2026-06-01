"""The Congress-trading universe: the TOP 300 most-traded CONGRESS-ONLY tickers.

Derives a screener universe purely from disclosed House STOCK Act trades
(web/public/data/congress.json): count trades per ticker, EXCLUDE any name already
covered by the AI stack (ai_stack) or the Quantum stack (quantum_stack) so this slice
is strictly the *congress-only* tail, then take the TOP 300 by trade count
(tie-break alphabetical).

Congress tickers are BARE symbols (no exchange prefix), exactly as parsed from the
PTR PDFs. The TradingView /america scanner resolves bare symbols via ``name in_range``
(see pull_congress.py's sector join + pull_congress_stocks.py's resolver) — so the
downstream pull/export reuse that approach rather than guessing an exchange.

Pure ``rank_top_congress_tickers`` is unit-tested. ``top_tickers`` is the thin loader
that feeds it the live congress.json + the covered set from the other two stacks.

Educational/research only — not investment advice. Self-reported, unverified filings.
"""
from __future__ import annotations

import json
import pathlib

from . import ai_stack, quantum_stack

SECTOR = "Congress"

# web/public/data/congress.json relative to this file (scripts/aiinvest/ -> repo root).
_REPO = pathlib.Path(__file__).resolve().parent.parent.parent
_CONGRESS_JSON = _REPO / "web" / "public" / "data" / "congress.json"


def covered_tickers():
    """Bare symbols already covered by the AI stack + the Quantum stack (to EXCLUDE)."""
    out = set()
    for t in ai_stack.all_tickers() + quantum_stack.all_tickers():
        out.add(t.split(":")[-1])
    return out


def load_congress_doc(path=None):
    """Load the published congress trade bundle (web/public/data/congress.json)."""
    p = pathlib.Path(path) if path else _CONGRESS_JSON
    return json.loads(p.read_text(encoding="utf-8"))


def rank_top_congress_tickers(congress_doc, covered, n=300):
    """Top-N most-traded CONGRESS-ONLY bare tickers (pure; unit-tested).

    Counts one per trade row in ``congress_doc['trades']`` keyed on the BARE ticker,
    drops empty/None tickers, EXCLUDES anything in ``covered`` (bare-symbol compare),
    then returns the top ``n`` by descending trade count, tie-broken alphabetically.
    Deterministic for a given input.
    """
    covered = {c.split(":")[-1] for c in (covered or set())}
    counts = {}
    for tr in (congress_doc or {}).get("trades", []) or []:
        tk = tr.get("ticker")
        if not tk:
            continue
        tk = str(tk).split(":")[-1].strip()
        if not tk or tk in covered:
            continue
        counts[tk] = counts.get(tk, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [tk for tk, _ in ranked[:n]]


def top_tickers(n=300, path=None):
    """Top-N most-traded congress-only BARE symbols from the live congress.json."""
    doc = load_congress_doc(path)
    return rank_top_congress_tickers(doc, covered_tickers(), n=n)
