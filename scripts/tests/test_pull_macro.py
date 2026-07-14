"""Thin integration tests for pull_macro.py — FRED CSV GETs mocked, no real network.
Mirrors tests/test_pull_ta.py's `_install_fake_get` pattern."""
import datetime
import json

import pytest
import requests

import pull_macro
from aiinvest import macro


def _csv_text(rows):
    """rows: [(date, value_or_None)] -> fredgraph.csv text (header + DATE,VALUE lines).
    None -> FRED's "." missing-observation sentinel."""
    lines = ["DATE,VALUE"]
    for date, value in rows:
        v = "." if value is None else str(value)
        lines.append(f"{date},{v}")
    return "\n".join(lines) + "\n"


def _daily_rows(n=400, start="2025-06-10", base=4.0, step=0.001):
    d0 = datetime.date.fromisoformat(start)
    return [((d0 + datetime.timedelta(days=i)).isoformat(), round(base + i * step, 4))
            for i in range(n)]


def _weekly_rows(n=60, start="2024-01-03", base=7000000.0, step=1000.0):
    d0 = datetime.date.fromisoformat(start)
    return [((d0 + datetime.timedelta(weeks=i)).isoformat(), base + i * step)
            for i in range(n)]


def _monthly_rows(n=30, start="2024-01-01", base=310.0, step=0.3):
    rows = []
    d = datetime.date.fromisoformat(start)
    for i in range(n):
        month = ((d.month - 1 + i) % 12) + 1
        year = d.year + (d.month - 1 + i) // 12
        date = datetime.date(year, month, 1).isoformat()
        rows.append((date, round(base + i * step, 3)))
    return rows


def _all_series_rows():
    return {
        "DGS2": _daily_rows(base=3.5),
        "DGS10": _daily_rows(base=4.4),
        "DFF": _daily_rows(base=4.3),
        "T10Y2Y": _daily_rows(base=-0.1, step=0.0005),
        "CPIAUCSL": _monthly_rows(base=310.0),
        "WALCL": _weekly_rows(),
        "VIXCLS": _daily_rows(base=16.0, step=0.01),
        "APU000072610": _monthly_rows(base=0.16, step=0.0005),
    }


class _FakeResp:
    def __init__(self, text, status=200):
        self.text = text
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


def _install_fake_get(monkeypatch, rows_by_series, raise_for=()):
    def fake_get(url, timeout=None):
        for sid in raise_for:
            if f"id={sid}" in url:
                raise requests.ConnectionError(f"simulated failure for {sid}")
        for sid, rows in rows_by_series.items():
            if f"id={sid}" in url:
                return _FakeResp(_csv_text(rows))
        raise AssertionError(f"unexpected URL in test: {url}")

    monkeypatch.setattr(requests, "get", fake_get)


CONTRACT_TOP_KEYS = {"generated_at", "schema_version", "source", "source_class",
                      "disclaimer", "series", "regime", "warnings"}
CONTRACT_SERIES_KEYS = {
    "series_id", "symbol", "display_name", "group", "frequency", "unit", "unit_kind",
    "decimals", "transform", "last", "previous", "change_abs", "change_pct",
    "value_1y_ago", "change_1y_pct", "as_of", "history_window_days", "sparkline",
    "retrieved_at", "source", "source_class", "source_url", "warnings",
}
CONTRACT_CHIP_KEYS = {"key", "label", "state", "value", "value_label", "basis", "rule", "as_of"}
SERIES_ORDER = ["DGS2", "DGS10", "DFF", "T10Y2Y", "CPIAUCSL", "WALCL", "VIXCLS", "APU000072610"]


def test_output_matches_contract_shape(tmp_path, monkeypatch):
    _install_fake_get(monkeypatch, _all_series_rows())
    out = tmp_path / "macro.json"
    rc = pull_macro.main(["--out", str(out)])
    assert rc == 0

    bundle = json.loads(out.read_text())
    assert set(bundle.keys()) == CONTRACT_TOP_KEYS
    assert bundle["schema_version"] == "macro-desk-v1"
    assert bundle["source"] == "fred"
    assert bundle["source_class"] == "api"

    assert [s["series_id"] for s in bundle["series"]] == SERIES_ORDER
    for s in bundle["series"]:
        assert set(s.keys()) == CONTRACT_SERIES_KEYS

    assert len(bundle["regime"]["chips"]) == 4
    assert [c["key"] for c in bundle["regime"]["chips"]] == ["curve", "real_rate", "liquidity", "vix"]
    for c in bundle["regime"]["chips"]:
        assert set(c.keys()) == CONTRACT_CHIP_KEYS
    assert isinstance(bundle["regime"]["headline"], str)

    # regime chips resolve to real (non-null) states given full mocked data
    for c in bundle["regime"]["chips"]:
        assert c["state"] is not None


def test_partial_failure_resilience_t10y2y_connection_error(tmp_path, monkeypatch):
    rows = _all_series_rows()
    _install_fake_get(monkeypatch, rows, raise_for=("T10Y2Y",))
    out = tmp_path / "macro.json"
    rc = pull_macro.main(["--out", str(out)])
    assert rc == 0

    bundle = json.loads(out.read_text())
    assert len(bundle["series"]) == 7
    assert "T10Y2Y" not in {s["series_id"] for s in bundle["series"]}
    assert any("T10Y2Y" in w for w in bundle["warnings"])

    chips_by_key = {c["key"]: c for c in bundle["regime"]["chips"]}
    assert len(bundle["regime"]["chips"]) == 4
    assert chips_by_key["curve"]["state"] is None
    assert any("curve" in w for w in bundle["warnings"])
    # unaffected chips still resolve
    assert chips_by_key["vix"]["state"] is not None


def test_series_subset_flag(tmp_path, monkeypatch):
    rows = _all_series_rows()
    _install_fake_get(monkeypatch, rows)
    out = tmp_path / "macro.json"
    rc = pull_macro.main(["--series", "DGS10,VIXCLS", "--out", str(out)])
    assert rc == 0

    bundle = json.loads(out.read_text())
    assert {s["series_id"] for s in bundle["series"]} == {"DGS10", "VIXCLS"}

    chips_by_key = {c["key"]: c for c in bundle["regime"]["chips"]}
    assert len(bundle["regime"]["chips"]) == 4
    # real_rate needs CPIAUCSL, which wasn't fetched -> null + warned, not crashed
    assert chips_by_key["real_rate"]["state"] is None
    assert any("real_rate" in w for w in bundle["warnings"])
    # vix needs only VIXCLS, which WAS fetched -> resolves
    assert chips_by_key["vix"]["state"] is not None


def test_dirty_value_rejection_never_reaches_bundle(tmp_path, monkeypatch):
    rows = _all_series_rows()
    # inject a "." (dirty/missing) observation into DGS10's raw feed
    dgs10 = list(rows["DGS10"])
    dgs10[10] = (dgs10[10][0], None)
    rows["DGS10"] = dgs10
    _install_fake_get(monkeypatch, rows)
    out = tmp_path / "macro.json"
    rc = pull_macro.main(["--out", str(out)])
    assert rc == 0

    raw_text = out.read_text()
    bundle = json.loads(raw_text)
    # the dirty sentinel itself never survives into the bundle as a string
    assert '"."' not in raw_text
    dgs10_series = next(s for s in bundle["series"] if s["series_id"] == "DGS10")
    assert dgs10_series["last"] is not None
    assert all(pt["v"] is not None for pt in dgs10_series["sparkline"])


def test_main_returns_zero_even_with_failures(tmp_path, monkeypatch):
    rows = _all_series_rows()
    _install_fake_get(monkeypatch, rows, raise_for=("DFF", "WALCL"))
    out = tmp_path / "macro.json"
    rc = pull_macro.main(["--out", str(out)])
    assert rc == 0
    bundle = json.loads(out.read_text())
    assert len(bundle["series"]) == 6
    assert len(bundle["regime"]["chips"]) == 4  # liquidity chip stays, goes null


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
