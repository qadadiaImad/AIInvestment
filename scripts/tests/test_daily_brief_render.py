from aiinvest.daily_brief import build_brief, render_post, rail_check

def _pulse():
    mk = lambda p, c: {"price": p, "change_pct": c}
    return {"sp500": mk(5000, 0.6), "nasdaq": mk(16000, 0.9),
            "vix": mk(13.0, -2.0), "ten_year": mk(4.2, 0.0)}

def test_render_has_sections_and_passes_rails():
    picks = {"ai": {"ticker": "NVDA", "perf_1y": 26.3, "rev_growth_yoy": 70.7},
             "quantum": {"ticker": "RGTI", "perf_1y": 72.7, "rev_growth_yoy": 8.8}}
    brief = build_brief("2026-07-02", _pulse(), picks, ["a jobs print", "earnings from X"])
    post = render_post(brief)
    assert "NVDA" in post and "RGTI" in post
    assert "#" in post                       # hashtags present
    assert rail_check(post) == []            # rail-clean by construction
