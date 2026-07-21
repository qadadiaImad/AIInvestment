"""Thin integration tests for pull_ta.py — Yahoo GETs mocked, no real network."""
import datetime
import json

import pytest
import requests

import pull_ta
from aiinvest import ta


def _daily_payload(closes, start="2025-07-15"):
    """Build a Yahoo v8 chart JSON payload with `len(closes)` ascending daily bars."""
    start_date = datetime.date.fromisoformat(start)
    timestamps, opens, highs, lows, cs = [], [], [], [], []
    for i, c in enumerate(closes):
        d = start_date + datetime.timedelta(days=i)
        ts = int(datetime.datetime(d.year, d.month, d.day, tzinfo=datetime.timezone.utc).timestamp())
        timestamps.append(ts)
        opens.append(c - 0.5)
        highs.append(c + 1.0)
        lows.append(c - 1.0)
        cs.append(c)
    return {"chart": {"result": [{
        "timestamp": timestamps,
        "indicators": {"quote": [{"open": opens, "high": highs, "low": lows, "close": cs}]},
    }]}}


def _intraday_payload(closes, day="2026-07-14"):
    timestamps, opens, highs, lows, cs = [], [], [], [], []
    base = datetime.datetime.fromisoformat(f"{day}T00:00:00+00:00")
    for i, c in enumerate(closes):
        ts = int((base + datetime.timedelta(hours=i)).timestamp())
        timestamps.append(ts)
        opens.append(c - 0.1)
        highs.append(c + 0.2)
        lows.append(c - 0.2)
        cs.append(c)
    return {"chart": {"result": [{
        "timestamp": timestamps,
        "indicators": {"quote": [{"open": opens, "high": highs, "low": lows, "close": cs}]},
    }]}}


class _FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


def _install_fake_get(monkeypatch, daily_by_symbol, intraday_by_symbol, raise_for=()):
    """Route GETs by which yahoo_symbol + interval appear in the URL."""
    def fake_get(url, headers=None, timeout=None):
        for sym in raise_for:
            if f"chart/{sym}" in url:
                raise requests.ConnectionError(f"simulated failure for {sym}")
        for sym, payload in daily_by_symbol.items():
            if f"chart/{sym}" in url and "interval=1d" in url:
                return _FakeResp(payload)
        for sym, payload in intraday_by_symbol.items():
            if f"chart/{sym}" in url and "interval=60m" in url:
                return _FakeResp(payload)
        raise AssertionError(f"unexpected URL in test: {url}")

    monkeypatch.setattr(requests, "get", fake_get)


CONTRACT_TOP_KEYS = {"generated_at", "schema_version", "source", "source_class",
                      "disclaimer", "groups", "instruments"}
CONTRACT_INSTRUMENT_KEYS = {
    "symbol", "display_name", "asset_class", "group", "yahoo_symbol", "tv_symbol",
    "retrieved_at", "source_url_daily", "source_url_intraday", "price", "trend",
    "rsi14", "atr14", "levels", "nearest_level", "sessions", "sparkline", "warnings",
}


def test_output_matches_contract_shape(tmp_path, monkeypatch):
    closes = [100.0 + i * 0.1 for i in range(260)]  # plenty of daily history
    intraday_closes = [100.0 + i * 0.01 for i in range(48)]
    _install_fake_get(
        monkeypatch,
        {"EURUSD=X": _daily_payload(closes)},
        {"EURUSD=X": _intraday_payload(intraday_closes)},
    )
    out = tmp_path / "ta_desk.json"
    rc = pull_ta.main(["--symbols", "EURUSD", "--out", str(out)])
    assert rc == 0

    bundle = json.loads(out.read_text())
    assert set(bundle.keys()) == CONTRACT_TOP_KEYS
    assert bundle["schema_version"] == "ta-desk-v1"
    assert bundle["groups"] == ["FX", "METALS", "ENERGY", "INDEX"]
    assert isinstance(bundle["instruments"], list)
    assert len(bundle["instruments"]) == 1

    inst = bundle["instruments"][0]
    assert set(inst.keys()) == CONTRACT_INSTRUMENT_KEYS
    assert "weekly_pivots" not in inst["levels"]
    assert set(inst["levels"].keys()) == {"daily_pivots", "previous_day_ohlc", "fifty_two_week"}
    # no leftover per-leaf envelope fields (value/raw/unit/dirty/...) anywhere
    assert "raw" not in json.dumps(inst)
    assert "dirty" not in json.dumps(inst)


def test_warning_present_on_missing_sma200(tmp_path, monkeypatch):
    closes = [100.0 + i * 0.1 for i in range(30)]  # < 200 daily bars
    _install_fake_get(
        monkeypatch,
        {"EURUSD=X": _daily_payload(closes)},
        {"EURUSD=X": _intraday_payload([100.0])},
    )
    out = tmp_path / "ta_desk.json"
    pull_ta.main(["--symbols", "EURUSD", "--out", str(out)])
    inst = json.loads(out.read_text())["instruments"][0]
    assert inst["trend"]["sma200"] is None
    assert any("sma200" in w for w in inst["warnings"])


def test_partial_universe_via_symbols_flag(tmp_path, monkeypatch):
    closes = [100.0 + i * 0.1 for i in range(260)]
    _install_fake_get(
        monkeypatch,
        {"EURUSD=X": _daily_payload(closes), "GC=F": _daily_payload(closes)},
        {"EURUSD=X": _intraday_payload([100.0]), "GC=F": _intraday_payload([100.0])},
    )
    out = tmp_path / "ta_desk.json"
    pull_ta.main(["--symbols", "EURUSD,GOLD", "--out", str(out)])
    bundle = json.loads(out.read_text())
    symbols = {i["symbol"] for i in bundle["instruments"]}
    assert symbols == {"EURUSD", "GOLD"}


def test_failed_fetch_reported_not_silently_dropped(tmp_path, monkeypatch, capsys):
    closes = [100.0 + i * 0.1 for i in range(260)]
    _install_fake_get(
        monkeypatch,
        {"EURUSD=X": _daily_payload(closes), "GC=F": _daily_payload(closes)},
        {"EURUSD=X": _intraday_payload([100.0]), "GC=F": _intraday_payload([100.0])},
        raise_for=("EURUSD=X",),
    )
    out = tmp_path / "ta_desk.json"
    pull_ta.main(["--symbols", "EURUSD,GOLD", "--out", str(out)])
    captured = capsys.readouterr()
    assert "EURUSD" in captured.out
    assert "failed" in captured.out.lower()

    bundle = json.loads(out.read_text())
    symbols = {i["symbol"] for i in bundle["instruments"]}
    assert symbols == {"GOLD"}  # GOLD still succeeds despite EURUSD failing


def test_instruments_is_array_not_dict(tmp_path, monkeypatch):
    closes = [100.0 + i * 0.1 for i in range(260)]
    _install_fake_get(
        monkeypatch,
        {"EURUSD=X": _daily_payload(closes)},
        {"EURUSD=X": _intraday_payload([100.0])},
    )
    out = tmp_path / "ta_desk.json"
    pull_ta.main(["--symbols", "EURUSD", "--out", str(out)])
    assert isinstance(json.loads(out.read_text())["instruments"], list)


def test_validate_instrument_flags_out_of_range_rsi():
    inst = {"symbol": "X", "rsi14": {"value": 150.0, "state": "overbought"},
            "levels": {"fifty_two_week": {"position_pct": 50.0}}}
    problems = pull_ta.validate_instrument(inst)
    assert any("rsi14" in p for p in problems)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
