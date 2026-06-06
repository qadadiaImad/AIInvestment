"""Merge-protect semantics of fundamental_fetch.save + save_series_batch value-only saves."""
import json

import fundamental_fetch as ff
import save_series_batch


def test_save_preserves_extra_keys_from_old_record(tmp_path):
    """Keys the new record doesn't carry (e.g. quantum `history`) must survive a re-save."""
    out = tmp_path / "fundamental"
    out.mkdir()
    (out / "IONQ.json").write_text(json.dumps({
        "symbol": "IONQ", "fundamental_value": 1.0, "fundamental_value_series": [["2025-01-01", 1.0]],
        "history": {"2024": {"revenue": 43.1}},
    }), encoding="utf-8")
    ff.save("IONQ", {"symbol": "IONQ", "fundamental_value": 2.0,
                     "fundamental_value_series": [["2026-01-01", 2.0]]}, out_dir=out)
    new = json.loads((out / "IONQ.json").read_text(encoding="utf-8"))
    assert new["fundamental_value"] == 2.0                      # fresh value wins
    assert new["history"] == {"2024": {"revenue": 43.1}}        # extra key preserved


def test_save_still_backfills_value_and_series(tmp_path):
    out = tmp_path / "fundamental"
    out.mkdir()
    (out / "X.json").write_text(json.dumps({
        "symbol": "X", "fundamental_value": 5.0, "margin_of_safety_pct": 10.0,
        "fundamental_value_series": [["2025-01-01", 5.0]],
    }), encoding="utf-8")
    ff.save("X", {"symbol": "X", "fundamental_value": None}, out_dir=out)
    new = json.loads((out / "X.json").read_text(encoding="utf-8"))
    assert new["fundamental_value"] == 5.0
    assert new["fundamental_value_series"] == [["2025-01-01", 5.0]]


def test_series_batch_saves_value_only_entries(tmp_path, monkeypatch):
    """A payload with gf_value but no medps must still update the current value."""
    saved = {}
    monkeypatch.setattr(ff, "save", lambda sym, rec, out_dir=None: saved.setdefault(sym, rec))
    batch = tmp_path / "b.json"
    batch.write_text(json.dumps({
        "TLN": {"gf_value": 300.5, "ms": -12.0, "medps": None},       # value-only
        "NVDA": {"gf_value": 338.52, "ms": 39.41,
                 "medps": [["2025-01-31", 100.0], ["2026-01-31", 200.0]]},  # value+series
        "K": {"status": 404},                                          # miss -> skipped
    }), encoding="utf-8")
    save_series_batch.main([str(batch)])
    assert saved["TLN"]["fundamental_value"] == 300.5
    assert "fundamental_value_series" not in saved["TLN"] or not saved["TLN"]["fundamental_value_series"]
    assert saved["NVDA"]["fundamental_value_series"]
    assert "K" not in saved
