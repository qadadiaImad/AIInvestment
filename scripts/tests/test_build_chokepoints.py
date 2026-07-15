"""File-based fixture tests for build_chokepoints.py + aiinvest.chokepoints — no HTTP
mocking needed, this pipeline is network-free (mirrors tests/test_build_risk.py's fixture
style, adapted for the chokepoints_source.json -> chokepoints.json pipeline).

Written FIRST per CLAUDE.md rule #1 (superpowers:test-driven-development) — implementation
in aiinvest/chokepoints.py and build_chokepoints.py follows this file.

Covers the 19 cases from docs/superpowers/specs/2026-07-15-chokepoints-design.md §2, plus
a couple of bonus integration checks for the hard-fail-abort contract.
"""
from __future__ import annotations

import datetime
import json

import pytest

import build_chokepoints
from aiinvest import chokepoints as cp


# --------------------------------------------------------------------------- fixture builders


def _claim(**overrides):
    base = {
        "text": "Example verifiable claim about a supply-chain chokepoint.",
        "class": "reported",
        "source_name": "Example Source",
        "source_url": "https://example.com/article",
        "source_class": "html",
        "retrieved_at": "2026-07-15T16:00:00Z",
        "needs_verification": False,
    }
    base.update(overrides)
    return base


def _entry(**overrides):
    base = {
        "id": "test-chokepoint",
        "name": "Test Chokepoint",
        "category": "fab_concentration",
        "layers": ["L1-chips"],
        "severity_score": 80,
        "severity_rationale": "Because no qualified alternative exists at volume.",
        "summary": "A short summary under 140 characters.",
        "card_tagline": "TEST TAGLINE",
        "description": "A longer factual description of the single-point mechanism.",
        "node_ids": ["TSM"],
        "external_entities": [],
        "tickers": ["NVDA"],
        "claims": [_claim()],
        "mitigation_watch": ["Watch this project."],
        "last_reviewed": "2026-07-15",
    }
    base.update(overrides)
    return base


def _source_doc(entries):
    return {"schema_version": "chokepoints-source-v1", "chokepoints": entries}


def _capital_web(ids):
    return {"nodes": [{"id": i, "name": i, "type": "public", "ticker": i,
                        "layer": "L1-chips", "note": ""} for i in ids],
            "edges": []}


def _graph_analysis(nodes):
    """nodes: list of {"id", "is_articulation", "betweenness"}."""
    return {"nodes": nodes}


_NOW = datetime.datetime(2026, 7, 16, tzinfo=datetime.timezone.utc)


# --------------------------------------------------------------------------- 1. valid entry


def test_valid_entry_passes_schema_validation():
    doc = _source_doc([_entry()])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert issues == []


# --------------------------------------------------------------------------- 2. missing required fields


@pytest.mark.parametrize("field", ["id", "name", "category", "layers", "description", "claims"])
def test_missing_required_field_fails(field):
    entry = _entry()
    del entry[field]
    doc = _source_doc([entry])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert any(f"'{field}'" in i and "missing required field" in i for i in issues), issues


# --------------------------------------------------------------------------- 3. category enum


def test_unknown_category_enum_rejected():
    doc = _source_doc([_entry(category="not-a-real-category")])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert any("category" in i for i in issues)


# --------------------------------------------------------------------------- 4. layer enum


def test_unknown_layer_code_rejected():
    doc = _source_doc([_entry(layers=["L9-nonexistent"])])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert any("layer" in i.lower() for i in issues)


# --------------------------------------------------------------------------- 5. severity_score range


@pytest.mark.parametrize("bad", [-1, 101, 150, -50])
def test_severity_score_out_of_range_rejected(bad):
    doc = _source_doc([_entry(severity_score=bad)])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert any("severity_score" in i for i in issues)


def test_severity_score_boundary_values_accepted():
    for ok in (0, 100, 50.5):
        doc = _source_doc([_entry(severity_score=ok)])
        issues = cp.validate_dataset(doc, now=_NOW)
        assert issues == [], (ok, issues)


# --------------------------------------------------------------------------- 6. claim class enum


def test_claim_class_enum_enforced():
    doc = _source_doc([_entry(claims=[_claim(**{"class": "speculative"})])])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert any("class" in i for i in issues)


# --------------------------------------------------------------------------- 7. claim source_url


def test_claim_missing_source_url_rejected():
    claim = _claim()
    del claim["source_url"]
    doc = _source_doc([_entry(claims=[claim])])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert any("source_url" in i for i in issues)


def test_claim_source_url_not_starting_with_http_rejected():
    doc = _source_doc([_entry(claims=[_claim(source_url="ftp://example.com/x")])])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert any("source_url" in i for i in issues)


# --------------------------------------------------------------------------- 8. claim retrieved_at missing


def test_claim_missing_retrieved_at_rejected():
    claim = _claim()
    del claim["retrieved_at"]
    doc = _source_doc([_entry(claims=[claim])])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert any("retrieved_at" in i for i in issues)


# --------------------------------------------------------------------------- 9. retrieved_at parses as UTC ISO8601


def test_claim_retrieved_at_must_parse_as_utc_iso8601():
    doc = _source_doc([_entry(claims=[_claim(retrieved_at="not-a-date")])])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert any("retrieved_at" in i for i in issues)


def test_claim_retrieved_at_valid_iso8601_accepted():
    doc = _source_doc([_entry(claims=[_claim(retrieved_at="2026-07-15T16:00:00Z")])])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert issues == []


# --------------------------------------------------------------------------- 10. duplicate id


def test_duplicate_id_rejected():
    doc = _source_doc([_entry(id="dup-id"), _entry(id="dup-id", name="Second")])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert any("duplicate id" in i for i in issues)


# --------------------------------------------------------------------------- 11. dirty sentinel strings


@pytest.mark.parametrize("dirty", ["", ".", "-", "--", "n/a", "na", "none", "null", "N/A", "NONE"])
def test_dirty_sentinel_string_rejected(dirty):
    doc = _source_doc([_entry(severity_rationale=dirty)])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert any("dirty sentinel" in i for i in issues), issues


# --------------------------------------------------------------------------- 12/13. node crossref warn-not-fail


def test_node_crossref_known_id_produces_no_warning():
    entry = _entry(node_ids=["TSM"])
    warnings = cp.crossref_node_ids(entry, {"TSM", "ASML"})
    assert warnings == []


def test_node_crossref_unknown_id_produces_warning_not_failure():
    entry = _entry(node_ids=["FOOBAR"])
    doc = _source_doc([entry])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert issues == []  # unknown node_ids never a hard schema failure
    warnings = cp.crossref_node_ids(entry, {"TSM"})
    assert len(warnings) == 1
    assert "FOOBAR" in warnings[0]


# --------------------------------------------------------------------------- 14. needs_verification rollup


def test_needs_verification_rolls_up_from_any_claim():
    entry_true = _entry(claims=[_claim(needs_verification=False), _claim(needs_verification=True)])
    assert cp.rollup_needs_verification(entry_true) is True

    entry_false = _entry(claims=[_claim(needs_verification=False), _claim(needs_verification=False)])
    assert cp.rollup_needs_verification(entry_false) is False


# --------------------------------------------------------------------------- 15/16. graph_crossref join


def test_graph_crossref_joins_betweenness_and_articulation_when_present():
    entry = _entry(node_ids=["TSM"])
    lookup = cp.build_graph_lookup(
        _graph_analysis([{"id": "TSM", "is_articulation": True, "betweenness": 0.041}]))
    result = cp.join_graph_crossref(entry, lookup)
    assert result == {"source_class": "computed", "is_articulation": True, "betweenness": 0.041}


def test_graph_crossref_takes_max_betweenness_and_or_of_articulation_across_node_ids():
    entry = _entry(node_ids=["TSM", "AMKR"])
    lookup = cp.build_graph_lookup(_graph_analysis([
        {"id": "TSM", "is_articulation": False, "betweenness": 0.01},
        {"id": "AMKR", "is_articulation": True, "betweenness": 0.05},
    ]))
    result = cp.join_graph_crossref(entry, lookup)
    assert result == {"source_class": "computed", "is_articulation": True, "betweenness": 0.05}


def test_graph_crossref_degrades_gracefully_when_graph_analysis_missing():
    entry = _entry(node_ids=["TSM"])
    lookup = cp.build_graph_lookup(None)
    result = cp.join_graph_crossref(entry, lookup)
    assert result == {"source_class": "computed", "is_articulation": False, "betweenness": 0.0}


def test_graph_crossref_degrades_gracefully_when_node_ids_empty():
    entry = _entry(node_ids=[])
    lookup = cp.build_graph_lookup(_graph_analysis([{"id": "TSM", "is_articulation": True, "betweenness": 0.9}]))
    result = cp.join_graph_crossref(entry, lookup)
    assert result == {"source_class": "computed", "is_articulation": False, "betweenness": 0.0}


# --------------------------------------------------------------------------- 17. summary counts


def test_summary_counts_match_entry_counts():
    entries_raw = [
        _entry(id="a", category="fab_concentration", layers=["L1-chips"], node_ids=["TSM"]),
        _entry(id="b", category="memory", layers=["L0-energy", "L1-chips"], node_ids=["MU"]),
    ]
    doc = _source_doc(entries_raw)
    valid_ids = {"TSM"}
    entries, _warnings = cp.build_entries(doc, valid_ids, {})
    summary = cp.compute_summary(entries, valid_ids)

    assert summary["n_entries"] == 2
    assert sum(summary["by_category"].values()) == 2
    assert sum(summary["by_layer"].values()) == sum(len(e["layers"]) for e in entries)
    assert summary["n_claims"] == sum(len(e["claims"]) for e in entries)
    assert summary["n_node_ids_total"] == 2  # distinct: TSM, MU
    assert summary["n_node_ids_resolved"] == 1  # only TSM is in valid_ids
    assert summary["n_node_ids_unresolved"] == 1


# --------------------------------------------------------------------------- 18. integration: full write path


def test_build_writes_expected_json_path_and_schema_version(tmp_path):
    source_path = tmp_path / "chokepoints_source.json"
    source_path.write_text(json.dumps(_source_doc([_entry()])), encoding="utf-8")
    cw_path = tmp_path / "capital_web.json"
    cw_path.write_text(json.dumps(_capital_web(["TSM"])), encoding="utf-8")
    ga_path = tmp_path / "graph_analysis.json"  # deliberately absent -> graceful degrade
    out_path = tmp_path / "out" / "chokepoints.json"

    rc = build_chokepoints.main([
        "--source", str(source_path),
        "--capital-web", str(cw_path),
        "--graph-analysis", str(ga_path),
        "--out", str(out_path),
    ])

    assert rc == 0
    assert out_path.exists()
    bundle = json.loads(out_path.read_text(encoding="utf-8"))
    assert bundle["schema_version"] == "chokepoints-v1"
    assert bundle["source_class"] == "computed"
    assert bundle["validation"]["schema_ok"] is True
    assert len(bundle["chokepoints"]) == 1
    entry = bundle["chokepoints"][0]
    assert entry["needs_verification"] is False
    assert entry["graph_crossref"] == {"source_class": "computed", "is_articulation": False,
                                        "betweenness": 0.0}
    assert bundle["summary"]["n_entries"] == 1
    assert "generated_at" in bundle


def test_build_aborts_and_writes_nothing_on_hard_fail(tmp_path):
    bad_entry = _entry()
    bad_entry["category"] = "not-a-category"
    source_path = tmp_path / "chokepoints_source.json"
    source_path.write_text(json.dumps(_source_doc([bad_entry])), encoding="utf-8")
    cw_path = tmp_path / "capital_web.json"
    cw_path.write_text(json.dumps(_capital_web(["TSM"])), encoding="utf-8")
    out_path = tmp_path / "out" / "chokepoints.json"

    rc = build_chokepoints.main([
        "--source", str(source_path),
        "--capital-web", str(cw_path),
        "--graph-analysis", str(tmp_path / "missing.json"),
        "--out", str(out_path),
    ])

    assert rc == 1
    assert not out_path.exists()


# --------------------------------------------------------------------------- 19. last_reviewed not in future


def test_last_reviewed_not_in_future():
    future = (datetime.date(2026, 7, 16) + datetime.timedelta(days=30)).isoformat()
    doc = _source_doc([_entry(last_reviewed=future)])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert any("last_reviewed" in i and "future" in i for i in issues)


def test_last_reviewed_today_is_accepted():
    doc = _source_doc([_entry(last_reviewed="2026-07-16")])
    issues = cp.validate_dataset(doc, now=_NOW)
    assert issues == []
