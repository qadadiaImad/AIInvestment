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

def test_render_expansive_sections_from_extras():
    picks = {"ai": {"ticker": "NVDA", "perf_1y": 26.3, "rev_growth_yoy": 70.7},
             "quantum": {"ticker": "IONQ", "perf_1y": 19.3, "rev_growth_yoy": 334.6}}
    ai_rows = [
        {"ticker": "WDC", "perf_1y": 904.3, "rev_growth_yoy": -18.4,
         "price": 100.0, "fundamental_value": 20.0, "fundamental_discount_pct": -400.0},
        {"ticker": "NVDA", "perf_1y": 26.3, "rev_growth_yoy": 70.7,
         "price": 150.0, "fundamental_value": 200.0, "fundamental_discount_pct": 25.0},
        {"ticker": "MU", "perf_1y": 824.2, "rev_growth_yoy": 167.0,
         "price": 1154.0, "fundamental_value": 900.0, "fundamental_discount_pct": -28.0},
        {"ticker": "META", "perf_1y": -18.5, "rev_growth_yoy": 26.2,
         "price": 582.9, "fundamental_value": 813.6, "fundamental_discount_pct": 28.4},
    ]
    q_rows = [
        {"ticker": "IONQ", "perf_1y": 19.3, "rev_growth_yoy": 334.6},
        {"ticker": "RGTI", "perf_1y": 72.7, "rev_growth_yoy": 8.8},
        {"ticker": "QBTS", "perf_1y": 69.9, "rev_growth_yoy": -41.7},
        {"ticker": "QUBT", "perf_1y": -44.8, "rev_growth_yoy": 1025.7},
    ]
    brief = build_brief("2026-07-04", _pulse(), picks, ["a jobs print"],
                        extras={"ai_rows": ai_rows, "quantum_rows": q_rows})
    post = render_post(brief)
    assert "Board leaders" in post and "WDC +904%" in post          # top movers w/ figures
    assert "Value corner" in post and "META" in post                 # deepest discount named
    assert "28.4% below the model" in post                           # discount figure verbatim
    assert "WDC" in post.split("Value corner")[1].split("\n\n")[0]   # steepest premium named
    assert "RGTI +73% on +9% revenue" in post                        # quantum peer read
    assert rail_check(post) == []                                    # still rail-clean
