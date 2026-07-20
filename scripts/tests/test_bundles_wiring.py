"""Tests for wiring bundle verification into the refresh drivers.

Each driver must verify only the artifacts IT is responsible for. Verifying
all 14 from refresh_ta.py would report congress.json as missing on a machine
that simply hasn't run the monthly congress job yet - a false alarm that
trains people to ignore the output, which is exactly the failure mode this
whole mechanism exists to prevent.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from aiinvest import bundles


NOW = "2026-07-20T12:00:00Z"

DRIVERS = ("refresh_daily.py", "refresh_ta.py", "refresh_congress.py")


def _write(root: pathlib.Path, rel: str, generated_at=NOW, pad=4000):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"generated_at": generated_at, "pad": "x" * pad}),
                 encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# ownership
# ---------------------------------------------------------------------------

def test_every_bundle_names_an_owning_driver_or_is_explicitly_manual():
    for name, b in bundles.BUNDLES.items():
        assert b.driver is None or b.driver in DRIVERS, (
            f"{name} has driver={b.driver!r}, which is neither None (manual) "
            f"nor one of {DRIVERS}"
        )


def test_for_driver_returns_only_that_drivers_bundles():
    for d in DRIVERS:
        got = bundles.for_driver(d)
        assert got, f"{d} owns no bundles - the mapping is probably wrong"
        assert all(b.driver == d for b in got)


def test_drivers_partition_bundles_without_overlap():
    """No bundle may be owned by two drivers - it would be built twice."""
    seen = {}
    for d in DRIVERS:
        for b in bundles.for_driver(d):
            assert b.name not in seen, (
                f"{b.name} claimed by both {seen[b.name]} and {d}")
            seen[b.name] = d


def test_ta_driver_owns_ta_desk_only():
    names = {b.name for b in bundles.for_driver("refresh_ta.py")}
    assert names == {"ta_desk.json"}


def test_congress_driver_does_not_own_daily_bundles():
    names = {b.name for b in bundles.for_driver("refresh_congress.py")}
    assert "site.json" not in names
    assert "congress.json" in names


def test_daily_driver_owns_the_core_site_bundles():
    names = {b.name for b in bundles.for_driver("refresh_daily.py")}
    for core in ("site.json", "news.json", "risk.json", "archetypes.json"):
        assert core in names


# ---------------------------------------------------------------------------
# render_verification - what the drivers actually print
# ---------------------------------------------------------------------------

def test_render_returns_lines_and_failure_count(tmp_path):
    lines, n_failed = bundles.render_verification(tmp_path, driver="refresh_ta.py",
                                                  now=NOW)
    assert isinstance(lines, list) and lines
    assert n_failed == 1  # ta_desk.json missing and required


def test_render_scoped_to_driver_ignores_other_bundles(tmp_path):
    """congress.json absent must NOT make the TA driver fail."""
    _write(tmp_path, "web/public/data/ta_desk.json", pad=30_000)
    lines, n_failed = bundles.render_verification(tmp_path, driver="refresh_ta.py",
                                                  now=NOW)
    assert n_failed == 0
    assert not any("congress" in ln for ln in lines)


def test_render_unscoped_checks_everything(tmp_path):
    _write(tmp_path, "web/public/data/ta_desk.json", pad=30_000)
    _, n_failed = bundles.render_verification(tmp_path, driver=None, now=NOW)
    assert n_failed > 1  # everything else still missing


def test_render_names_the_fix_for_each_failure(tmp_path):
    lines, _ = bundles.render_verification(tmp_path, driver="refresh_daily.py",
                                           now=NOW)
    body = "\n".join(lines)
    assert "export_site.py" in body, "failure output must name the producing script"


def test_render_reports_clean_state_without_noise(tmp_path):
    _write(tmp_path, "web/public/data/ta_desk.json", pad=30_000)
    lines, n_failed = bundles.render_verification(tmp_path, driver="refresh_ta.py",
                                                  now=NOW)
    assert n_failed == 0
    assert len(lines) <= 3, "a clean run should stay quiet, not print a wall of text"


def test_render_is_ascii_only(tmp_path):
    """Windows consoles are cp1252; non-ASCII renders as mojibake."""
    lines, _ = bundles.render_verification(tmp_path, driver="refresh_daily.py",
                                           now=NOW)
    for ln in lines:
        ln.encode("ascii")  # raises if a stray em-dash creeps back in


def test_stale_bundle_does_not_count_as_driver_failure(tmp_path):
    """Policy: stale warns, only missing/corrupt fails."""
    _write(tmp_path, "web/public/data/ta_desk.json",
           generated_at="2026-07-01T12:00:00Z", pad=30_000)
    lines, n_failed = bundles.render_verification(tmp_path, driver="refresh_ta.py",
                                                  now=NOW)
    assert n_failed == 0
    assert any("stale" in ln.lower() or "WARN" in ln for ln in lines)
