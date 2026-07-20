"""Quality checks for the GuruFocus fundamental store (data/fundamental/*.json).

The bundle manifest catches a missing *file*. This catches a present file
whose *fields* are empty - the next layer of the same failure mode.

Concretely, on 2026-07-20 the fair-value backfill ran for 49 minutes and
reported "requested=108 ok=108 failed=[]" while every record came back with
margin_of_safety_pct=null and an empty fundamental_value_series. Nothing
surfaced that, because "ok" counted files written, not fields populated.

GuruFocus is retrieved two ways and they fail independently:

  fundamental_value       <- server-rendered innerText   (reliable)
  margin_of_safety_pct    <- intercepted chart XHR       (gated)
  fundamental_value_series<- intercepted chart XHR       (gated)

So a healthy store still has ~100% coverage of fundamental_value while the
chart-derived fields may be at 0% when the XHR endpoint is walled. Treating
those two as one number would either cry wolf nightly or hide a real outage,
which is why they are reported and thresholded separately.

Educational/research only - not investment advice.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib

__all__ = ["Coverage", "load_records", "assess", "check", "STORE"]

STORE = "data/fundamental"

#: Below this share of records carrying a GF value, the primary (innerText)
#: path is considered broken - that is a real outage worth failing on.
MIN_VALUE_COVERAGE = 0.80

#: The chart XHR is gated and frequently unavailable. Its absence is
#: reported, never fatal: failing nightly on a known wall trains people to
#: ignore the output.
MIN_CHART_COVERAGE = 0.0


@dataclasses.dataclass
class Coverage:
    n_records: int = 0
    n_value: int = 0
    n_margin: int = 0
    n_series: int = 0
    unreadable: list[str] = dataclasses.field(default_factory=list)

    def _pct(self, n):
        return 0.0 if not self.n_records else n / self.n_records

    @property
    def value_pct(self):
        return self._pct(self.n_value)

    @property
    def margin_pct(self):
        return self._pct(self.n_margin)

    @property
    def series_pct(self):
        return self._pct(self.n_series)

    @property
    def ok(self) -> bool:
        """True when the primary path is healthy. Chart gaps never fail."""
        if self.n_records == 0 or self.unreadable:
            return False
        return self.value_pct >= MIN_VALUE_COVERAGE

    @property
    def chart_blocked(self) -> bool:
        return self.n_records > 0 and self.margin_pct <= MIN_CHART_COVERAGE


def load_records(repo_root) -> tuple[list[dict], list[str]]:
    """Load every record in the store. Returns ``(records, unreadable_names)``."""
    d = pathlib.Path(repo_root) / STORE
    if not d.is_dir():
        return ([], [])
    records, bad = [], []
    for p in sorted(d.glob("*.json")):
        try:
            with p.open(encoding="utf-8") as fh:
                records.append(json.load(fh))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            bad.append(p.name)
    return (records, bad)


def assess(records, unreadable=()) -> Coverage:
    cov = Coverage(n_records=len(records), unreadable=list(unreadable))
    for r in records:
        if not isinstance(r, dict):
            continue
        if r.get("fundamental_value") is not None:
            cov.n_value += 1
        if r.get("margin_of_safety_pct") is not None:
            cov.n_margin += 1
        if r.get("fundamental_value_series"):
            cov.n_series += 1
    return cov


def check(repo_root) -> tuple[list[str], int]:
    """Render report lines and a failure count, matching bundles.render_verification."""
    records, bad = load_records(repo_root)
    cov = assess(records, bad)

    if cov.n_records == 0:
        return ([f"  fundamentals: STORE EMPTY at {STORE}",
                 "         fix: cd scripts && python fundamental_backfill.py --universe all"], 1)

    lines = [f"  fundamentals: {cov.n_records} records - "
             f"value {cov.n_value} ({cov.value_pct:.0%}), "
             f"margin {cov.n_margin} ({cov.margin_pct:.0%}), "
             f"series {cov.n_series} ({cov.series_pct:.0%})"]

    n_failed = 0
    if cov.unreadable:
        n_failed += 1
        lines.append(f"    FAIL {len(cov.unreadable)} unreadable record(s): "
                     f"{', '.join(cov.unreadable[:5])}")
    if cov.value_pct < MIN_VALUE_COVERAGE:
        n_failed += 1
        lines.append(f"    FAIL GF value coverage {cov.value_pct:.0%} is below "
                     f"{MIN_VALUE_COVERAGE:.0%} - the innerText path is broken, "
                     "not just the gated XHR")
        lines.append("         fix: cd scripts && python fundamental_backfill.py --universe all")
    if cov.chart_blocked:
        lines.append("    WARN margin_of_safety/series are empty - GuruFocus chart XHR "
                     "is gated; the headline GF value is unaffected")

    return (lines, n_failed)
