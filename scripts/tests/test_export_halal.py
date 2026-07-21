"""RED tests for the halal.json export (pure build; no I/O)."""
import pytest
import export_halal
from aiinvest import halal


def _env(v):
    return {"value": v, "raw": v, "unit": "usd", "dirty": False,
            "retrieved_at": "2026-07-21T14:00:00Z", "source": "tradingview",
            "source_url": "u", "source_class": "api"}


BATCH = {"batch_metadata": {"batch_timestamp": "2026-07-21T14:00:00Z"},
         "financial_data": {"NVDA": {"symbol": "NVDA", "ticker": "NASDAQ:NVDA",
                                     "as_of": "2026-07-21T14:00:00Z",
                                     "metrics": {
             "close": _env(200.0), "market_cap_basic": _env(4919375940781.0),
             "total_assets_fq": _env(259474000000.0),
             "total_debt_fq": _env(12814000000.0),
             "cash_n_short_term_invest_fq": _env(80572000000.0),
             "total_revenue_ttm": _env(253491000000.0),
             "total_revenue_fy": _env(215938000000.0),
             "receivables_turnover_fy": _env(7.0188)}}}}

ACTIVITY = {"NVDA": {"ticker": "NVDA", "status": "clean", "categories": [],
                     "impermissible_revenue_pct": None, "evidence": None,
                     "methodology_notes": {}, "note": None,
                     "confidence": "high", "last_reviewed": "2026-07-21"}}


def test_build_produces_verdict_with_conventions_and_disclaimer():
    bundle = export_halal.build(BATCH, ACTIVITY)
    assert bundle["conventions"] == halal.CONVENTIONS
    assert "not financial" in bundle["disclaimer"].lower()
    assert "sharia board" in bundle["disclaimer"].lower()
    v = bundle["verdicts"]["NVDA"]
    assert v["overall"] == "halal"
    assert v["layer"] == "L1-chips"
    assert v["standards"]["AAOIFI"]["tests"][0]["ratio"] < 0.01


def test_build_symbol_missing_from_activity_is_insufficient_data():
    bundle = export_halal.build(BATCH, {})
    assert bundle["verdicts"]["NVDA"]["overall"] == "insufficient_data"


def test_build_never_emits_gurufocus_terms():
    import json
    s = json.dumps(export_halal.build(BATCH, ACTIVITY)).lower()
    for term in ("guru", "gf value", "gf_value", "gf score"):
        assert term not in s


def test_write_history_snapshot(tmp_path):
    bundle = export_halal.build(BATCH, ACTIVITY)
    out = export_halal.write_history_snapshot(bundle, tmp_path, "2026-07-21")
    assert out == tmp_path / "halal" / "history" / "halal_2026-07-21.json"
    import json
    assert json.loads(out.read_text(encoding="utf-8"))["verdicts"].keys() == bundle["verdicts"].keys()


# ---------------------------------------------------------------------------
# Task 12: diff_bundles + update_alerts
# ---------------------------------------------------------------------------

def _make_bundle(nvda_overall, nvda_ratio):
    """Build a minimal bundle with NVDA at the given overall verdict + ratio."""
    return {
        "generated_at": "2026-07-21T14:00:00Z",
        "verdicts": {
            "NVDA": {
                "overall": nvda_overall,
                "standards": {
                    "AAOIFI": {
                        "tests": [
                            {"id": "aaoifi_debt", "label": "debt/mcap",
                             "ratio": nvda_ratio, "threshold": 0.30,
                             "status": "pass" if nvda_ratio < 0.30 else "fail"}
                        ]
                    }
                },
                "inputs_asof": "2026-07-21T14:00:00Z",
            },
            "WKEY": {
                "overall": "not_halal",
                "standards": {
                    "AAOIFI": {
                        "tests": [
                            {"id": "aaoifi_cash", "label": "cash/mcap",
                             "ratio": 5.84, "threshold": 0.30, "status": "fail"}
                        ]
                    }
                },
                "inputs_asof": "2026-07-21T14:00:00Z",
            },
        },
    }


PREV_BUNDLE = _make_bundle("halal", 0.29)       # NVDA passes
CURR_BUNDLE = _make_bundle("not_halal", 0.31)   # NVDA flips


def test_diff_bundles_detects_overall_flip():
    alerts = export_halal.diff_bundles(PREV_BUNDLE, CURR_BUNDLE, "2026-07-22")
    # NVDA overall flip + aaoifi_debt status flip => at least 1 alert
    assert any(a["symbol"] == "NVDA" for a in alerts)
    nvda_alerts = [a for a in alerts if a["symbol"] == "NVDA"]
    # overall flip alert
    overall = [a for a in nvda_alerts if a["driver_test"] == "overall"]
    assert overall, f"No overall-flip alert; got {nvda_alerts}"
    assert overall[0]["from"] == "halal"
    assert overall[0]["to"] == "not_halal"
    assert overall[0]["date"] == "2026-07-22"


def test_diff_bundles_detects_test_status_flip():
    alerts = export_halal.diff_bundles(PREV_BUNDLE, CURR_BUNDLE, "2026-07-22")
    nvda_alerts = [a for a in alerts if a["symbol"] == "NVDA"]
    test_flip = [a for a in nvda_alerts if a["driver_test"] == "aaoifi_debt"]
    assert test_flip, f"No test-level flip; got {nvda_alerts}"
    assert test_flip[0]["old_value"] == pytest.approx(0.29)
    assert test_flip[0]["new_value"] == pytest.approx(0.31)
    assert test_flip[0]["threshold"] == pytest.approx(0.30)


def test_diff_bundles_unchanged_symbol_produces_no_alert():
    alerts = export_halal.diff_bundles(PREV_BUNDLE, CURR_BUNDLE, "2026-07-22")
    wkey_alerts = [a for a in alerts if a["symbol"] == "WKEY"]
    assert not wkey_alerts, f"WKEY unchanged but got alerts: {wkey_alerts}"


def test_diff_bundles_empty_prev_gives_no_alerts():
    """First-run: prev has no verdicts — no diffs."""
    alerts = export_halal.diff_bundles({"verdicts": {}}, CURR_BUNDLE, "2026-07-22")
    assert alerts == []


def test_update_alerts_prepends_and_drops_old_entries(tmp_path):
    alerts_path = tmp_path / "halal_alerts.json"
    old_entry = {"symbol": "OLD", "date": "2026-03-01",  # 142 days before 2026-07-21
                 "from": "halal", "to": "not_halal",
                 "driver_test": "overall", "old_value": None, "new_value": None,
                 "threshold": None, "inputs_asof": "2026-03-01T00:00:00Z"}
    existing = {"generated_at": "2026-03-01T00:00:00Z", "alerts": [old_entry]}
    import json
    alerts_path.write_text(json.dumps(existing), encoding="utf-8")

    new_entry = {"symbol": "NVDA", "date": "2026-07-21",
                 "from": "halal", "to": "not_halal",
                 "driver_test": "overall", "old_value": None, "new_value": None,
                 "threshold": None, "inputs_asof": "2026-07-21T14:00:00Z"}
    result = export_halal.update_alerts(alerts_path, [new_entry], keep_days=90)

    # new entry is present, old entry (>90 days) is dropped
    assert any(a["symbol"] == "NVDA" for a in result["alerts"])
    assert not any(a["symbol"] == "OLD" for a in result["alerts"])
    # persisted to disk
    saved = json.loads(alerts_path.read_text(encoding="utf-8"))
    assert "generated_at" in saved
    assert saved["alerts"] == result["alerts"]


def test_update_alerts_creates_file_if_absent(tmp_path):
    alerts_path = tmp_path / "halal_alerts.json"
    result = export_halal.update_alerts(alerts_path, [], keep_days=90)
    assert result["alerts"] == []
    assert "generated_at" in result


def test_main_no_prev_snapshot_writes_empty_alerts(tmp_path, monkeypatch):
    """First-run path: no prior snapshot exists → halal_alerts.json has empty alerts."""
    import json
    # Write a mock halal batch
    batch_dir = tmp_path / "halal" / "2026-07-21"
    batch_dir.mkdir(parents=True)
    (batch_dir / "tradingview_halal_2026-07-21.json").write_text(
        json.dumps(BATCH), encoding="utf-8")

    # Write current snapshot manually (simulating Task 1's write_history_snapshot)
    hist_dir = tmp_path / "halal" / "history"
    hist_dir.mkdir(parents=True)
    bundle = export_halal.build(BATCH, ACTIVITY)
    (hist_dir / "halal_2026-07-21.json").write_text(
        json.dumps(bundle), encoding="utf-8")

    alerts_out = tmp_path / "halal_alerts.json"

    # Patch load_business_activity and validate to avoid file I/O
    monkeypatch.setattr("aiinvest.halal.load_business_activity", lambda: ACTIVITY)
    monkeypatch.setattr("aiinvest.halal.validate_business_activity", lambda a, u: [])

    import sys
    monkeypatch.setattr(sys, "argv", [
        "export_halal.py",
        "--data", str(tmp_path),
        "--out", str(tmp_path / "halal.json"),
        "--alerts-out", str(alerts_out),
    ])
    rc = export_halal.main()
    assert rc == 0
    assert alerts_out.exists()
    saved = json.loads(alerts_out.read_text(encoding="utf-8"))
    assert saved["alerts"] == []


def test_same_day_rerun_produces_no_false_alerts(tmp_path, monkeypatch):
    """Second run on the same day: previous-day snapshot uses identical data → no alerts.

    Builds the prev snapshot via diff_bundles against itself — same bundle means
    no flips regardless of what SP/DJIM tests compute.
    """
    import json

    # Use diff_bundles directly: comparing a bundle to itself must yield no alerts.
    bundle = export_halal.build(BATCH, ACTIVITY)
    alerts = export_halal.diff_bundles(bundle, bundle, "2026-07-21")
    assert alerts == [], f"diff_bundles(bundle, bundle) produced alerts: {alerts}"
