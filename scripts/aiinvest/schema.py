"""Data-schema helpers — the stamped envelope + value cleaning/parsing.

Mirrors references/data-schema.md. The point of `clean`/`parse_number` is to NOT repeat
GuruTrade's bug of storing dirty values like current_ratio: "." — junk becomes None and
the envelope is flagged ``dirty: true`` for inspection instead of silently trusted.
"""
from __future__ import annotations

_DIRTY = {"", ".", "-", "--", "n/a", "na", "none", "null"}

_SUFFIX = {"k": 1e3, "m": 1e6, "b": 1e9, "t": 1e12}


def clean(raw):
    """Return a trimmed string, or None for dirty sentinels / empties."""
    if raw is None:
        return None
    s = str(raw).strip()
    if s.lower() in _DIRTY:
        return None
    return s


def parse_number(raw):
    """Parse a financial number string to float, or None if unparseable.

    Handles commas, a leading ``$``, a trailing ``%``, and magnitude suffixes
    K/M/B/T (e.g. ``"5.11T"`` -> 5.11e12).
    """
    s = clean(raw)
    if s is None:
        return None
    s = s.replace(",", "").replace("$", "").strip()
    if s.endswith("%"):
        s = s[:-1].strip()
    mult = 1.0
    if s and s[-1].lower() in _SUFFIX:
        mult = _SUFFIX[s[-1].lower()]
        s = s[:-1].strip()
    try:
        return float(s) * mult
    except (ValueError, TypeError):
        return None


def make_envelope(value, raw, unit, source, source_url, source_class, retrieved_at,
                  dirty=None):
    """Build a per-metric envelope. Infers ``dirty`` when not given.

    dirty == True means: a raw value was present but could not be parsed/validated.
    A genuinely-absent field (raw is None) is NOT dirty.
    """
    if dirty is None:
        dirty = raw is not None and value is None
    return {
        "value": value,
        "raw": raw,
        "unit": unit,
        "dirty": dirty,
        "retrieved_at": retrieved_at,
        "source": source,
        "source_url": source_url,
        "source_class": source_class,
    }
