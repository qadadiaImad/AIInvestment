import datetime as dt
from aiinvest import daily_pick

def _bundle(**verdicts):
    return {"verdicts": {s: {"overall": o, "standards": {}, "business": {}}
                         for s, o in verdicts.items()}}

NOW = dt.datetime(2026, 7, 22, tzinfo=dt.timezone.utc)

def test_verdict_map():
    assert daily_pick.verdict_map(_bundle(WULF="questionable")) == {"WULF": "questionable"}

def test_first_run_no_flips():
    assert daily_pick.detect_flips(None, _bundle(WULF="halal")) == []

def test_flip_detected_and_shaped():
    flips = daily_pick.detect_flips({"WULF": "questionable"}, _bundle(WULF="not_halal"))
    assert flips == [{"symbol": "WULF", "from": "questionable", "to": "not_halal",
                      "old_value": None, "new_value": None}]

def test_unchanged_and_new_symbols_do_not_flip():
    flips = daily_pick.detect_flips({"WULF": "halal"}, _bundle(WULF="halal", GEV="halal"))
    assert flips == []

def test_flip_outranks_everything_even_recently_posted():
    bundle = _bundle(WULF="not_halal", GEV="halal")
    posted = [{"symbol": "WULF", "date": "2026-07-20", "folder": "x"}]
    ranked = daily_pick.rank_candidates(bundle, {"WULF": "questionable"}, None, posted, NOW)
    assert ranked[0]["symbol"] == "WULF" and "flip" in ranked[0]["reason"]

def test_rotation_penalty_demotes_recent_post():
    # two identical extreme-ratio stories; the recently-posted one must rank lower
    v = {"overall": "not_halal", "business": {},
         "standards": {"AAOIFI": {"tests": [{"label": "debt/mcap", "status": "fail",
                                             "ratio": 0.9, "threshold": 0.3, "margin": -0.6}]}}}
    bundle = {"verdicts": {"AAA": v, "BBB": v}}
    posted = [{"symbol": "AAA", "date": "2026-07-10", "folder": "x"}]
    ranked = daily_pick.rank_candidates(bundle, None, None, posted, NOW)
    assert ranked[0]["symbol"] == "BBB"

def test_rank_candidates_dedupes_symbol_with_flip_and_ratio_story():
    # AAA both flips (alert) AND independently qualifies for an extreme-ratio
    # story from its own verdict standards -- halal_stories.pick_stories emits
    # two story dicts for AAA. rank_candidates must keep only AAA's
    # highest-scoring story (the flip) so the top-3 stays three distinct
    # symbols instead of AAA occupying two slots and bumping BBB out.
    ratio_test = {"label": "debt/mcap", "status": "fail",
                  "ratio": 0.9, "threshold": 0.3, "margin": -0.6}
    v = {"business": {}, "standards": {"AAOIFI": {"tests": [ratio_test]}}}
    bundle = {"verdicts": {
        "AAA": {**v, "overall": "not_halal"},
        "BBB": {**v, "overall": "not_halal"},
    }}
    prev_map = {"AAA": "questionable"}
    ranked = daily_pick.rank_candidates(bundle, prev_map, None, [], NOW)
    symbols = [c["symbol"] for c in ranked]
    assert len(symbols) == len(set(symbols)), f"top-3 must be distinct symbols, got {symbols}"
    assert "BBB" in symbols

def test_news_heat_recency_weighting():
    news = {"items": [
        {"tickers": ["GEV"], "published_at": "2026-07-21T12:00:00Z", "title": "x"},
        {"tickers": ["GEV"], "published_at": "2026-06-01T12:00:00Z", "title": "y"}]}
    heat = daily_pick.news_heat(news, {"GEV"}, NOW)
    assert heat["GEV"] == 1.3

def test_history_roundtrip(tmp_path):
    daily_pick.save_snapshot(tmp_path, "2026-07-21", {"WULF": "halal"})
    prev, prev_date = daily_pick.load_history(tmp_path)
    assert prev == {"WULF": "halal"} and prev_date == "2026-07-21"

def test_load_history_empty_dir(tmp_path):
    assert daily_pick.load_history(tmp_path) == (None, None)
