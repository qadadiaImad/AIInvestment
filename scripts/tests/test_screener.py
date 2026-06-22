"""RED tests for the whole-stack screener."""
from aiinvest import screener


def _dossier(sym, layer, price, pe, gf, stale=False, lab=False, cat_date=None):
    metrics = {"current_price": {"value": price, "stale": stale},
               "price_earnings_ttm": {"value": pe, "stale": False},
               "gf_value": {"value": gf, "stale": False}}
    cats = [{"id": f"{sym}-e", "date": cat_date, "title": f"{sym} earnings"}] if cat_date else []
    rel = {"lab_exposure": [{"lab": "anthropic", "pct": 14}] if lab else []}
    return {"symbol": sym, "layer": layer, "metrics": metrics, "catalysts": cats, "relationships": rel}


DOSSIERS = [
    _dossier("NVDA", "L1-chips", 211.14, 32.33, 334.32, cat_date="2026-08-26"),       # disc 36.8
    _dossier("VST", "L0-energy", 160.0, 26.7, 160.0, cat_date="2026-07-01"),          # disc 0.0
    _dossier("PLTR", "L4-application", 156.0, 176.0, None, stale=True, lab=True),     # disc None
]


def test_screen_returns_exact_row_keys():
    rows = screener.screen(DOSSIERS)
    assert set(rows[0].keys()) == {"symbol", "layer", "price", "pe", "gf_discount_pct",
                                   "lab_exposure", "next_catalyst", "verify_live"}


def test_gf_discount_pct_computed():
    rows = {r["symbol"]: r for r in screener.screen(DOSSIERS)}
    assert rows["NVDA"]["gf_discount_pct"] == 36.8
    assert rows["VST"]["gf_discount_pct"] == 0.0


def test_sorted_by_discount_desc_none_last():
    rows = screener.screen(DOSSIERS)
    assert [r["symbol"] for r in rows] == ["NVDA", "VST", "PLTR"]


def test_next_catalyst_and_flags():
    rows = {r["symbol"]: r for r in screener.screen(DOSSIERS)}
    assert rows["NVDA"]["next_catalyst"]["date"] == "2026-08-26"
    assert rows["PLTR"]["lab_exposure"] is True
    assert rows["PLTR"]["verify_live"] is True
    assert rows["VST"]["lab_exposure"] is False


def test_to_screener_html_is_self_contained():
    html = screener.to_screener_html(screener.screen(DOSSIERS))
    assert html.strip().lower().startswith("<!doctype html")
    for sym in ("NVDA", "VST", "PLTR"):
        assert sym in html
    assert "not financial advice" in html.lower()
