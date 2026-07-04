import json, pathlib, sys, pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build_daily_brief import run

def _bundles(d):
    (d / "site.json").write_text(json.dumps({"rows": [{"ticker": "NVDA", "perf_1y": 26.3, "rev_growth_yoy": 70.7}]}))
    (d / "quantum.json").write_text(json.dumps({"rows": [{"ticker": "RGTI", "perf_1y": 72.7, "rev_growth_yoy": 8.8}]}))
    (d / "news.json").write_text(json.dumps([{"tickers": ["NVDA"]}]))
    prices = d / "prices"; prices.mkdir()
    (prices / "NVDA.json").write_text(json.dumps([["2026-06-01", 100], ["2026-06-02", 110]]))

_fake = lambda s: {"^GSPC": (5000, 4975), "^IXIC": (16000, 15840),
                   "^VIX": (13, 13.5), "^TNX": (42, 41.5)}[s]

def test_run_writes_artifacts_rail_clean(tmp_path):
    data = tmp_path / "data"; data.mkdir(); _bundles(data)
    out = tmp_path / "out"
    meta = run("2026-07-02", data_dir=str(data), out_dir=str(out), fetch=_fake)
    day = out / "2026-07-02"
    assert (day / "brief.md").exists() and (day / "meta.json").exists()
    assert meta["rails_passed"] is True
    assert "generated_at" in meta
    assert meta["generated_at"].endswith("Z")

def test_run_raises_on_none_ai_pick(tmp_path):
    data = tmp_path / "data"; data.mkdir()
    # site bundle has non-numeric perf_1y -> _hottest returns None
    (data / "site.json").write_text(json.dumps({"rows": [{"ticker": "NVDA", "perf_1y": "n/a", "rev_growth_yoy": 70.7}]}))
    (data / "quantum.json").write_text(json.dumps({"rows": [{"ticker": "RGTI", "perf_1y": 72.7, "rev_growth_yoy": 8.8}]}))
    (data / "news.json").write_text(json.dumps([{"tickers": ["NVDA"]}]))
    out = tmp_path / "out"
    with pytest.raises(RuntimeError, match="no usable mover for ai"):
        run("2026-07-02", data_dir=str(data), out_dir=str(out), fetch=_fake)
    day = out / "2026-07-02"
    assert not day.exists() or not (day / "brief.md").exists()

def test_run_raises_on_none_quantum_pick(tmp_path):
    data = tmp_path / "data"; data.mkdir()
    (data / "site.json").write_text(json.dumps({"rows": [{"ticker": "NVDA", "perf_1y": 26.3, "rev_growth_yoy": 70.7}]}))
    # quantum bundle has non-numeric perf_1y -> _hottest returns None
    (data / "quantum.json").write_text(json.dumps({"rows": [{"ticker": "RGTI", "perf_1y": "n/a", "rev_growth_yoy": 8.8}]}))
    (data / "news.json").write_text(json.dumps([{"tickers": ["NVDA"]}]))
    out = tmp_path / "out"
    with pytest.raises(RuntimeError, match="no usable mover for quantum"):
        run("2026-07-02", data_dir=str(data), out_dir=str(out), fetch=_fake)
    day = out / "2026-07-02"
    assert not day.exists() or not (day / "brief.md").exists()

def test_run_chart_error_branch(tmp_path, monkeypatch):
    data = tmp_path / "data"; data.mkdir(); _bundles(data)
    out = tmp_path / "out"
    import build_daily_brief
    monkeypatch.setattr(build_daily_brief, "write_chart_png", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("playwright unavailable")))
    meta = run("2026-07-02", data_dir=str(data), out_dir=str(out), fetch=_fake)
    day = out / "2026-07-02"
    assert (day / "brief.md").exists()
    assert (day / "meta.json").exists()
    assert meta["rails_passed"] is True
    assert meta["chart"] is None
    assert meta["chart_error"] and len(meta["chart_error"]) > 0
