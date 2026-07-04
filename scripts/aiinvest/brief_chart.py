def render_chart_html(ticker, series):
    ys = [float(p[1]) for p in series] or [0.0]
    lo, hi = min(ys), max(ys)
    span = (hi - lo) or 1.0
    W, H, pad = 1200, 1200, 120
    n = max(len(ys) - 1, 1)
    pts = " ".join(
        f"{pad + i*(W-2*pad)/n:.1f},{H-pad - (y-lo)/span*(H-2*pad):.1f}"
        for i, y in enumerate(ys))
    chg = (ys[-1]-ys[0])/ys[0]*100 if ys[0] else 0.0
    return f"""<!doctype html><html><head><meta charset='utf-8'>
<style>*{{margin:0}}.s{{width:{W}px;height:{H}px;background:#0A0D12;color:#E8EDF2;
font-family:Inter,system-ui;position:relative}}</style></head><body>
<div class='s'><div style='position:absolute;top:90px;left:100px;font-size:64px;font-weight:700'>{ticker}</div>
<div style='position:absolute;top:170px;left:100px;font-size:34px;color:#34D399'>{chg:+.1f}% shown</div>
<svg width='{W}' height='{H}'><polyline fill='none' stroke='#10B981' stroke-width='6' points='{pts}'/></svg>
<div style='position:absolute;bottom:70px;left:100px;font-size:22px;color:#5A6472'>Educational - not advice.</div>
</div></body></html>"""

def write_chart_png(html, out_path):
    import pathlib
    from playwright.sync_api import sync_playwright
    out = pathlib.Path(out_path).resolve()  # absolute — as_uri() requires it, and screenshot path
    tmp = out.with_suffix(".html")
    tmp.write_text(html, encoding="utf-8")
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1200, "height": 1200}, device_scale_factor=1)
            pg.goto(tmp.as_uri()); pg.wait_for_timeout(600)
            pg.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": 1200, "height": 1200})
            b.close()
    finally:
        tmp.unlink(missing_ok=True)
