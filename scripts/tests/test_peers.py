"""RED tests for peers.py — cross-sectional benchmarking (pure logic, no network)."""
from aiinvest import peers


# --- benchmark(): summary stats of a value vs a peer distribution ---

def test_benchmark_median_quartiles_on_known_list():
    b = peers.benchmark(50.0, [10.0, 20.0, 50.0, 90.0])
    assert b["n"] == 4
    assert b["median"] == 35.0  # mean of 20 and 50
    assert b["p25"] == 17.5     # linear interpolation
    assert b["p75"] == 60.0


def test_benchmark_percentile_pct_le_value():
    # 3 of 4 peers (10,20,50) are <= 50 -> 75.0%
    b = peers.benchmark(50.0, [10.0, 20.0, 50.0, 90.0])
    assert b["percentile"] == 75.0


def test_benchmark_percentile_all_below():
    b = peers.benchmark(100.0, [10.0, 20.0, 50.0, 90.0])
    assert b["percentile"] == 100.0


def test_benchmark_percentile_all_above():
    b = peers.benchmark(5.0, [10.0, 20.0, 50.0, 90.0])
    assert b["percentile"] == 0.0


def test_benchmark_ignores_none_peers():
    b = peers.benchmark(50.0, [10.0, None, 50.0, None, 90.0])
    assert b["n"] == 3
    assert b["median"] == 50.0


def test_benchmark_none_value_has_no_percentile_but_keeps_stats():
    b = peers.benchmark(None, [10.0, 20.0, 50.0])
    assert b["n"] == 3
    assert b["percentile"] is None
    assert b["median"] == 20.0


def test_benchmark_empty_peers_returns_dict_with_n_zero():
    b = peers.benchmark(50.0, [])
    assert b["n"] == 0
    assert b["median"] is None
    assert b["p25"] is None
    assert b["p75"] is None
    assert b["percentile"] is None


def test_benchmark_all_none_peers_returns_n_zero():
    b = peers.benchmark(50.0, [None, None])
    assert b["n"] == 0
    assert b["median"] is None
    assert b["percentile"] is None


# --- peer_stats(): per-metric benchmarking over tradingview-shaped records ---

def _rec(symbol, **metrics):
    return {
        "symbol": symbol,
        "ticker": "NASDAQ:" + symbol,
        "metrics": {k: {"value": v} for k, v in metrics.items()},
    }


PEERS = [
    _rec("NVDA", price_earnings_ttm=32.0, return_on_equity=90.0),
    _rec("AMD", price_earnings_ttm=40.0, return_on_equity=10.0),
    _rec("INTC", price_earnings_ttm=20.0, return_on_equity=5.0),
    _rec("AVGO", price_earnings_ttm=60.0, return_on_equity=50.0),
]


def test_peer_stats_returns_entry_per_metric():
    out = peers.peer_stats(
        {"price_earnings_ttm": 32.0, "return_on_equity": 90.0},
        PEERS,
        ["price_earnings_ttm", "return_on_equity"],
    )
    assert set(out) == {"price_earnings_ttm", "return_on_equity"}


def test_peer_stats_carries_target_value_and_n():
    out = peers.peer_stats(
        {"price_earnings_ttm": 32.0},
        PEERS,
        ["price_earnings_ttm"],
    )
    pe = out["price_earnings_ttm"]
    assert pe["value"] == 32.0
    # target (NVDA, 32.0) is excluded from peers -> 3 peers remain
    assert pe["n"] == 3


def test_peer_stats_excludes_target_own_value():
    # peers PE without NVDA's 32.0: [40,20,60] -> median 40
    out = peers.peer_stats(
        {"price_earnings_ttm": 32.0},
        PEERS,
        ["price_earnings_ttm"],
    )
    assert out["price_earnings_ttm"]["median"] == 40.0


def test_peer_stats_percentile_against_excluded_peers():
    # value 32 vs peers [40,20,60]: 1 of 3 <= 32 -> 33.33%
    out = peers.peer_stats(
        {"price_earnings_ttm": 32.0},
        PEERS,
        ["price_earnings_ttm"],
    )
    assert round(out["price_earnings_ttm"]["percentile"], 2) == 33.33


def test_peer_stats_handles_metric_missing_in_some_peers():
    recs = [
        _rec("A", price_earnings_ttm=10.0),       # has it
        _rec("B"),                                 # missing metric entirely
        _rec("C", price_earnings_ttm=30.0),
    ]
    out = peers.peer_stats({"price_earnings_ttm": 20.0}, recs, ["price_earnings_ttm"])
    pe = out["price_earnings_ttm"]
    assert pe["n"] == 2  # only A and C contribute
    assert pe["median"] == 20.0


def test_peer_stats_target_value_none_when_absent():
    out = peers.peer_stats({}, PEERS, ["price_earnings_ttm"])
    assert out["price_earnings_ttm"]["value"] is None
