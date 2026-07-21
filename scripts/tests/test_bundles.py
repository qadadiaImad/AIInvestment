"""Tests for the data-bundle manifest and verifier.

The manifest declares every JSON artifact the web app requires. These tests
pin the two properties that make it useful:

1. A bundle that is missing / truncated / corrupt is reported as a FAILURE.
2. A bundle that exists but is past its cadence is reported as a WARNING —
   loud, but non-fatal (see docs: fail-on-missing, warn-on-stale).

The drift guard (manifest vs. what web/lib actually loads) lives in
test_bundles_drift.py.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from aiinvest import bundles


NOW = "2026-07-20T12:00:00Z"


def _write(root: pathlib.Path, rel: str, payload, generated_at=NOW):
    """Write a bundle fixture under ``root`` and return its path."""
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        p.write_text(payload, encoding="utf-8")
    else:
        body = dict(payload)
        if generated_at is not None:
            body["generated_at"] = generated_at
        p.write_text(json.dumps(body), encoding="utf-8")
    return p


@pytest.fixture
def repo(tmp_path):
    return tmp_path


def _bundle(**kw):
    base = dict(
        name="thing.json",
        root=bundles.PUBLIC,
        produced_by="build_thing.py",
        required=True,
        max_age_h=24,
        min_bytes=10,
    )
    base.update(kw)
    return bundles.Bundle(**base)


# ---------------------------------------------------------------------------
# existence
# ---------------------------------------------------------------------------

def test_missing_required_bundle_is_a_failure(repo):
    r = bundles.check_bundle(_bundle(), repo, NOW)
    assert r.status == bundles.MISSING
    assert r.is_failure
    assert not r.is_warning


def test_missing_optional_bundle_is_not_a_failure(repo):
    r = bundles.check_bundle(_bundle(required=False), repo, NOW)
    assert r.status == bundles.MISSING
    assert not r.is_failure


def test_present_fresh_bundle_is_ok(repo):
    _write(repo, "web/public/data/thing.json", {"a": 1} | {"pad": "x" * 200})
    r = bundles.check_bundle(_bundle(), repo, NOW)
    assert r.status == bundles.OK
    assert not r.is_failure and not r.is_warning


# ---------------------------------------------------------------------------
# integrity
# ---------------------------------------------------------------------------

def test_truncated_bundle_is_a_failure(repo):
    _write(repo, "web/public/data/thing.json", {"a": 1})
    r = bundles.check_bundle(_bundle(min_bytes=10_000), repo, NOW)
    assert r.status == bundles.TOO_SMALL
    assert r.is_failure


def test_unparseable_bundle_is_a_failure(repo):
    _write(repo, "web/public/data/thing.json", "{not json" + "x" * 200)
    r = bundles.check_bundle(_bundle(), repo, NOW)
    assert r.status == bundles.UNPARSEABLE
    assert r.is_failure


def test_corrupt_optional_bundle_is_still_a_failure(repo):
    """Optional means 'may be absent', NOT 'may be corrupt'."""
    _write(repo, "web/public/data/thing.json", "{not json" + "x" * 200)
    r = bundles.check_bundle(_bundle(required=False), repo, NOW)
    assert r.status == bundles.UNPARSEABLE
    assert r.is_failure


# ---------------------------------------------------------------------------
# freshness — warn, never fail
# ---------------------------------------------------------------------------

def test_stale_bundle_warns_but_does_not_fail(repo):
    _write(
        repo,
        "web/public/data/thing.json",
        {"pad": "x" * 200},
        generated_at="2026-07-01T12:00:00Z",  # 19 days old
    )
    r = bundles.check_bundle(_bundle(max_age_h=24), repo, NOW)
    assert r.status == bundles.STALE
    assert r.is_warning
    assert not r.is_failure


def test_age_is_reported_in_hours(repo):
    _write(
        repo,
        "web/public/data/thing.json",
        {"pad": "x" * 200},
        generated_at="2026-07-19T12:00:00Z",
    )
    r = bundles.check_bundle(_bundle(max_age_h=24), repo, NOW)
    assert r.age_h == pytest.approx(24.0, abs=0.1)


def test_cadence_is_per_bundle(repo):
    """A weekly bundle 3 days old is fine; a daily one is not."""
    _write(
        repo,
        "web/public/data/thing.json",
        {"pad": "x" * 200},
        generated_at="2026-07-17T12:00:00Z",  # 72h
    )
    assert bundles.check_bundle(_bundle(max_age_h=168), repo, NOW).status == bundles.OK
    assert bundles.check_bundle(_bundle(max_age_h=24), repo, NOW).status == bundles.STALE


def test_falls_back_to_mtime_when_no_generated_at(repo):
    _write(repo, "web/public/data/thing.json", {"pad": "x" * 200}, generated_at=None)
    r = bundles.check_bundle(_bundle(), repo, NOW)
    # mtime is "now" in real terms; the point is it must not crash and must
    # not silently report OK on an unknown age.
    assert r.status in (bundles.OK, bundles.STALE)
    assert r.age_source == "mtime"


def test_generated_at_is_preferred_over_mtime(repo):
    _write(
        repo,
        "web/public/data/thing.json",
        {"pad": "x" * 200},
        generated_at="2026-07-01T12:00:00Z",
    )
    r = bundles.check_bundle(_bundle(), repo, NOW)
    assert r.age_source == "generated_at"
    assert r.status == bundles.STALE


# ---------------------------------------------------------------------------
# the second root (portfolio.json is deliberately NOT public)
# ---------------------------------------------------------------------------

def test_webdata_root_is_resolved_separately(repo):
    _write(repo, "web/data/portfolio.json", {"pad": "x" * 200})
    r = bundles.check_bundle(
        _bundle(name="portfolio.json", root=bundles.WEBDATA), repo, NOW
    )
    assert r.status == bundles.OK


def test_webdata_bundle_not_found_in_public_root(repo):
    """Guards against a regression that would publish private portfolio data."""
    _write(repo, "web/public/data/portfolio.json", {"pad": "x" * 200})
    r = bundles.check_bundle(
        _bundle(name="portfolio.json", root=bundles.WEBDATA), repo, NOW
    )
    assert r.status == bundles.MISSING


# ---------------------------------------------------------------------------
# aggregation + diagnosis
# ---------------------------------------------------------------------------

def test_check_all_returns_one_result_per_manifest_entry(repo):
    results = bundles.check_all(repo, NOW)
    assert len(results) == len(bundles.BUNDLES)


def test_failures_and_warnings_partition(repo):
    _write(repo, "web/public/data/site.json", {"pad": "x" * 2_000_000})
    results = bundles.check_all(repo, NOW)
    fails = bundles.failures(results)
    warns = bundles.warnings(results)
    assert not (set(id(f) for f in fails) & set(id(w) for w in warns))


def test_every_result_explains_itself_and_names_its_fix(repo):
    """The user asked for 'why' + 'how to rerun' on every problem."""
    for r in bundles.check_all(repo, NOW):
        if r.is_failure or r.is_warning:
            assert r.detail, f"{r.bundle.name} has no explanation"
            assert r.fix_command, f"{r.bundle.name} has no rerun command"
            assert r.bundle.produced_by in r.fix_command


# ---------------------------------------------------------------------------
# manifest sanity
# ---------------------------------------------------------------------------

def test_manifest_is_not_empty():
    assert len(bundles.BUNDLES) >= 12


def test_manifest_entries_are_well_formed():
    for name, b in bundles.BUNDLES.items():
        assert b.name == name
        assert b.root in (bundles.PUBLIC, bundles.WEBDATA)
        assert b.produced_by.endswith(".py")
        assert b.max_age_h > 0
        assert b.min_bytes > 0


def test_portfolio_is_never_declared_public():
    """web/public/data is served statically — positions must never live there."""
    assert bundles.BUNDLES["portfolio.json"].root == bundles.WEBDATA
