"""CLI wiring tests for build_archetypes.py -- mirrors tests/test_build_risk.py's
file-based fixture style (network-free pipeline, no HTTP mocking needed)."""
import json

import pytest

import build_archetypes


def _write_site(path, stocks, generated_at="2026-07-14T22:39:30Z"):
    site = {
        "generated_at": generated_at,
        "stocks": stocks,
        "layers": {"L0-energy": [], "L1-chips": list(stocks.keys()), "L2-infra": [],
                   "L3-models": [], "L4-application": []},
    }
    path.write_text(json.dumps(site), encoding="utf-8")


def _stock(symbol="NVDA", **overrides):
    base = {
        "symbol": symbol, "layer": "L1-chips", "as_of": "2026-07-14",
        "valuation": {"pe": 46.2, "fundamental_discount_pct": -5.0},
        "fundamentals": {"net_margin": 55.8, "pb": 28.4, "current_ratio": 3.5,
                          "debt_to_equity": 0.3},
        "performance": {}, "history": {},
    }
    base.update(overrides)
    return base


def test_missing_site_json_exits_1_and_writes_nothing(tmp_path):
    site_path = tmp_path / "site.json"  # deliberately not written
    out_path = tmp_path / "archetypes.json"
    rc = build_archetypes.main(["--site", str(site_path), "--out", str(out_path)])
    assert rc == 1
    assert not out_path.exists()


def test_unparseable_site_json_exits_1_and_writes_nothing(tmp_path):
    site_path = tmp_path / "site.json"
    site_path.write_text("{not valid json", encoding="utf-8")
    out_path = tmp_path / "archetypes.json"
    rc = build_archetypes.main(["--site", str(site_path), "--out", str(out_path)])
    assert rc == 1
    assert not out_path.exists()


def test_valid_fixture_round_trips_through_evaluate_stock(tmp_path):
    site_path = tmp_path / "site.json"
    out_path = tmp_path / "archetypes.json"
    _write_site(site_path, {"NVDA": _stock("NVDA")})

    rc = build_archetypes.main(["--site", str(site_path), "--out", str(out_path)])
    assert rc == 0
    assert out_path.exists()

    bundle = json.loads(out_path.read_text())
    assert bundle["schema_version"] == "archetypes-v1"
    assert bundle["source"]["generated_at"] == "2026-07-14T22:39:30Z"
    assert len(bundle["per_stock"]) == 1
    entry = bundle["per_stock"][0]
    assert entry["symbol"] == "NVDA"
    assert entry["layer"] == "L1-chips"

    # round-trip check: re-running evaluate_stock directly on the same stock dict
    # produces the identical graham criteria list written to disk.
    from aiinvest import archetypes as arche
    direct = arche.evaluate_stock(_stock("NVDA"))
    assert entry["archetypes"]["graham"]["criteria"] == direct["archetypes"]["graham"]["criteria"]
    assert entry["archetypes"]["graham"]["score"] == direct["archetypes"]["graham"]["score"]


def test_empty_stocks_writes_sparse_bundle_and_exits_0(tmp_path):
    site_path = tmp_path / "site.json"
    out_path = tmp_path / "archetypes.json"
    _write_site(site_path, {})

    rc = build_archetypes.main(["--site", str(site_path), "--out", str(out_path)])
    assert rc == 0
    bundle = json.loads(out_path.read_text())
    assert bundle["per_stock"] == []
    assert bundle["universe"]["n_symbols"] == 0
    assert any("no stocks" in w for w in bundle["warnings"])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
