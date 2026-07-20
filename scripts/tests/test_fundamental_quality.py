"""Tests for the fundamental-store quality checks.

The invariant that matters: GuruFocus's two retrieval paths fail
independently, so a gated chart XHR (margin/series empty) must NOT be
reported the same way as a broken innerText path (no GF values at all).
Conflating them would either cry wolf every night or hide a real outage.
"""
from __future__ import annotations

import json
import pathlib

from aiinvest import fundamental_quality as fq


def _store(tmp_path) -> pathlib.Path:
    d = tmp_path / fq.STORE
    d.mkdir(parents=True, exist_ok=True)
    return d


def _rec(sym, value=100.0, margin=None, series=None):
    return {"symbol": sym, "fundamental_value": value,
            "margin_of_safety_pct": margin,
            "fundamental_value_series": series or [],
            "retrieved_at": "2026-07-20T10:00:00Z", "source": "fundamental-model"}


def _write(tmp_path, records):
    d = _store(tmp_path)
    for r in records:
        (d / f"{r['symbol']}.json").write_text(json.dumps(r), encoding="utf-8")


# ---------------------------------------------------------------------------
# the real-world state: values present, chart fields gated
# ---------------------------------------------------------------------------

def test_gated_chart_is_a_warning_not_a_failure(tmp_path):
    """Exactly tonight's state: 128 GF values, zero margin/series."""
    _write(tmp_path, [_rec(f"S{i}") for i in range(20)])
    lines, n_failed = fq.check(tmp_path)
    assert n_failed == 0, "a gated XHR must not fail the run"
    body = "\n".join(lines)
    assert "WARN" in body
    assert "chart XHR" in body


def test_gated_chart_is_detected(tmp_path):
    _write(tmp_path, [_rec(f"S{i}") for i in range(10)])
    cov = fq.assess(*fq.load_records(tmp_path))
    assert cov.chart_blocked
    assert cov.value_pct == 1.0
    assert cov.margin_pct == 0.0
    assert cov.ok


def test_healthy_store_with_chart_data_does_not_warn(tmp_path):
    _write(tmp_path, [_rec(f"S{i}", margin=12.5, series=[1, 2, 3]) for i in range(10)])
    lines, n_failed = fq.check(tmp_path)
    assert n_failed == 0
    assert "WARN" not in "\n".join(lines)


# ---------------------------------------------------------------------------
# the real outage: the innerText path breaks
# ---------------------------------------------------------------------------

def test_missing_gf_values_is_a_failure(tmp_path):
    """If GuruFocus blocks the rendered page too, that IS an outage."""
    _write(tmp_path, [_rec(f"S{i}", value=None) for i in range(10)])
    lines, n_failed = fq.check(tmp_path)
    assert n_failed >= 1
    body = "\n".join(lines)
    assert "FAIL" in body
    assert "fundamental_backfill.py" in body, "must name the fix"


def test_partial_coverage_below_threshold_fails(tmp_path):
    recs = [_rec(f"S{i}") for i in range(7)] + [_rec(f"X{i}", value=None) for i in range(13)]
    _write(tmp_path, recs)
    cov = fq.assess(*fq.load_records(tmp_path))
    assert cov.value_pct < fq.MIN_VALUE_COVERAGE
    assert not cov.ok
    assert fq.check(tmp_path)[1] >= 1


def test_coverage_just_above_threshold_passes(tmp_path):
    recs = [_rec(f"S{i}") for i in range(9)] + [_rec("X0", value=None)]
    _write(tmp_path, recs)
    cov = fq.assess(*fq.load_records(tmp_path))
    assert cov.value_pct == 0.9
    assert cov.ok
    assert fq.check(tmp_path)[1] == 0


# ---------------------------------------------------------------------------
# structural faults
# ---------------------------------------------------------------------------

def test_empty_store_fails_and_names_the_fix(tmp_path):
    _store(tmp_path)
    lines, n_failed = fq.check(tmp_path)
    assert n_failed == 1
    assert "fundamental_backfill.py" in "\n".join(lines)


def test_absent_store_fails(tmp_path):
    lines, n_failed = fq.check(tmp_path)
    assert n_failed == 1


def test_corrupt_record_is_reported(tmp_path):
    _write(tmp_path, [_rec(f"S{i}") for i in range(10)])
    (tmp_path / fq.STORE / "BAD.json").write_text("{not json", encoding="utf-8")
    records, bad = fq.load_records(tmp_path)
    assert bad == ["BAD.json"]
    lines, n_failed = fq.check(tmp_path)
    assert n_failed >= 1
    assert "unreadable" in "\n".join(lines)


def test_output_is_ascii_only(tmp_path):
    """cp1252 consoles: a stray em-dash becomes mojibake."""
    _write(tmp_path, [_rec(f"S{i}", value=None) for i in range(5)])
    for ln in fq.check(tmp_path)[0]:
        ln.encode("ascii")


def test_load_records_tolerates_non_dict_payloads(tmp_path):
    d = _store(tmp_path)
    (d / "LIST.json").write_text("[1,2,3]", encoding="utf-8")
    cov = fq.assess(*fq.load_records(tmp_path))
    assert cov.n_records == 1
    assert cov.n_value == 0
