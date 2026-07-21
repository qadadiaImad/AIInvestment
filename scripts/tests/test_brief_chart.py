from aiinvest.brief_chart import render_chart_html

def test_html_has_ticker_dims_and_polyline():
    series = [["2026-06-01", 100.0], ["2026-06-02", 110.0], ["2026-06-03", 105.0]]
    html = render_chart_html("NVDA", series)
    assert "NVDA" in html
    assert "1200" in html            # dimension present
    assert "<polyline" in html or "<path" in html
    assert "#10B981" in html         # brand emerald
