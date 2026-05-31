"""GuruFocus extraction + gate detection (Mode-B, Playwright).

The browser fetch is a Playwright MCP task (validated live 2026-05-30: NVDA GF Value
$334.32, "Possible Value Trap"). This module is the *processing* core: run validated
regex over the page innerText into stamped envelopes (no dirty "." junk — fixes the
GuruTrade bug), and decide when the gate has tripped so the orchestrator rotates the
instance. See references/anti-gating-cookbook.md and providers/README.md (GuruFocus).
"""
from __future__ import annotations

import re

from . import schema

SOURCE = "gurufocus"

# name -> (regex with one capture group, unit, kind)
_PATTERNS = {
    "gf_value": (r"GF Value[^$\d]*\$?\s*([\d,]+\.?\d*)", "usd", "num"),
    "gf_score": (r"GF Score[:\s]*(\d+)\s*/\s*100", "score", "num"),
    "pe_ratio": (r"PE Ratio[:\s]*([\d,]+\.?\d*)", "ratio", "num"),
    "price": (r"\$\s*([\d,]+\.\d{2})", "usd", "num"),
    "valuation_verdict": (
        r"(Significantly Overvalued|Modestly Overvalued|Significantly Undervalued|"
        r"Modestly Undervalued|Fairly Valued|Possible Value Trap|Overvalued|Undervalued)",
        "text", "text"),
}

_GATE_TEXT = ("subscribe to premium", "sign in", "log in", "you have reached",
              "upgrade to premium", "register to continue", "unlock", "start free trial")
_GATE_STATUS = {402, 403, 429}


def extract_metrics(text, source_url, retrieved_at):
    """Run validated regex over page innerText -> {name: stamped envelope}."""
    out = {}
    for name, (pattern, unit, kind) in _PATTERNS.items():
        m = re.search(pattern, text, re.IGNORECASE)
        raw = m.group(1) if m else None
        value = (schema.parse_number(raw) if kind == "num" else schema.clean(raw))
        out[name] = schema.make_envelope(
            value=value, raw=raw, unit=unit, source=SOURCE,
            source_url=source_url, source_class="innertext-regex",
            retrieved_at=retrieved_at,
        )
    return out


def to_record(text, symbol, source_url, retrieved_at):
    """Wrap extracted metrics into a merge-ready record (see merge.merge_symbol)."""
    return {"symbol": symbol,
            "metrics": extract_metrics(text, source_url, retrieved_at)}


def detect_gate(text, status_codes=()):
    """Decide whether the gate tripped (rotate the instance). Returns {gated, reasons}."""
    reasons = []
    low = (text or "").lower()
    for sig in _GATE_TEXT:
        if sig in low:
            reasons.append(f"text:{sig}")
    bad = _GATE_STATUS.intersection(status_codes or ())
    for code in sorted(bad):
        reasons.append(f"http:{code}")
    return {"gated": bool(reasons), "reasons": reasons}
