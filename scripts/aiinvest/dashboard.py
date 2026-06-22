"""Per-ticker HTML dashboard renderer (Part A output style).

`to_html(fact_sheet, narrative)` returns a self-contained styled page. Deterministic and
pure: the facts come from `analyst.fact_sheet`; the `narrative` dict (valuation_take,
bottleneck_rationale, scenarios, risks, synthesis) is supplied on demand by the LLM
(analyst skill). Always carries a "not financial advice" disclaimer.
"""
from __future__ import annotations

import html as _html

_LAYER_COLOR = {
    "L0-energy": "#f59e0b", "L1-chips": "#10b981", "L2-infra": "#3b82f6",
    "L3-models": "#8b5cf6", "L4-application": "#ec4899", "private-lab": "#ef4444",
}


def _esc(x):
    return _html.escape(str(x)) if x is not None else "—"


def _ul(items):
    items = [i for i in (items or [])]
    if not items:
        return "<p style='color:#6b7280'>—</p>"
    return "<ul>" + "".join(f"<li>{_esc(i)}</li>" for i in items) + "</ul>"


def _sparkline(points, w=150, h=34, color="#10b981"):
    """Return an inline SVG sparkline for a list of numbers (or {'value':...} dicts). '' if empty."""
    vals = [(p.get("value") if isinstance(p, dict) else p) for p in (points or [])]
    vals = [v for v in vals if isinstance(v, (int, float))]
    if not vals:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    n = len(vals)
    step = w / (n - 1) if n > 1 else 0.0
    pad = 3
    coords = []
    for i, v in enumerate(vals):
        x = round(i * step, 1)
        y = round(pad + (h - 2 * pad) * (1 - (v - lo) / span), 1)
        coords.append(f"{x},{y}")
    pts = " ".join(coords)
    last_x, last_y = coords[-1].split(",")
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{pts}"/>'
            f'<circle cx="{last_x}" cy="{last_y}" r="2.5" fill="{color}"/></svg>')


def to_html(fact_sheet, narrative):
    fs = fact_sheet or {}
    n = narrative or {}
    sym = fs.get("symbol", "?")
    layer = fs.get("layer")
    color = _LAYER_COLOR.get(layer, "#9ca3af")
    val = fs.get("valuation", {})
    con = fs.get("constraint", {})
    rel = fs.get("relationships", {})
    verify = fs.get("verify_live", []) or []

    badge = ("<span style='background:#7c2d12;color:#fde68a;padding:2px 8px;border-radius:6px;"
             "font-size:12px'>⚠ verify live: " + _esc(", ".join(verify)) + "</span>") if verify else ""

    cps = "".join(
        f"<tr><td>{_esc(c.get('node'))}</td><td>{_esc(c.get('type'))}</td>"
        f"<td>{_esc(c.get('usd'))}</td></tr>"
        for c in rel.get("counterparties", []))
    cps_tbl = (f"<table><tr><th>counterparty</th><th>type</th><th>$</th></tr>{cps}</table>"
               if cps else "<p style='color:#6b7280'>none recorded</p>")

    cats = "".join(
        f"<tr><td>{_esc(c.get('date'))}</td><td>{_esc(c.get('title') or c.get('id'))}</td>"
        f"<td>{_esc(c.get('type'))}</td></tr>"
        for c in fs.get("catalysts", []))
    cats_tbl = (f"<table><tr><th>date</th><th>event</th><th>type</th></tr>{cats}</table>"
                if cats else "<p style='color:#6b7280'>none upcoming</p>")

    scf = rel.get("single_counterparty_flags", [])
    all_risks = list(fs.get("risk_flags", [])) + list(n.get("risks", [])) + list(scf)

    # --- enriched sections: fundamentals, performance, peer comparison ---
    fund = fs.get("fundamentals", {}) or {}
    perf = fs.get("performance", {}) or {}
    peer = fs.get("peer_comparison", {}) or {}

    def _fmt(v, suf=""):
        if v is None:
            return "—"
        if isinstance(v, (int, float)):
            return f"{v:,.2f}{suf}"
        return _esc(v)

    fund_html = ""
    if any(v is not None for v in fund.values()):
        fund_html = (
            f'<h2>Fundamentals <span style="color:#6b7280;font-size:12px">'
            f'{_esc(fund.get("sector"))} · {_esc(fund.get("industry"))}</span></h2>'
            '<div class="kpi">'
            f'<div><b>{_fmt(fund.get("gross_margin"), "%")}</b><span>gross margin</span></div>'
            f'<div><b>{_fmt(fund.get("operating_margin"), "%")}</b><span>op margin</span></div>'
            f'<div><b>{_fmt(fund.get("net_margin"), "%")}</b><span>net margin</span></div>'
            f'<div><b>{_fmt(fund.get("fcf_margin"), "%")}</b><span>FCF margin</span></div>'
            '</div><div class="kpi">'
            f'<div><b>{_fmt(fund.get("roe"), "%")}</b><span>ROE</span></div>'
            f'<div><b>{_fmt(fund.get("roa"), "%")}</b><span>ROA</span></div>'
            f'<div><b>{_fmt(fund.get("roic"), "%")}</b><span>ROIC</span></div>'
            f'<div><b>{_fmt(fund.get("debt_to_equity"))}</b><span>D/E</span></div>'
            f'<div><b>{_fmt(fund.get("current_ratio"))}</b><span>current ratio</span></div>'
            '</div><div class="kpi">'
            f'<div><b>{_fmt(fund.get("rev_growth_yoy"), "%")}</b><span>revenue YoY</span></div>'
            f'<div><b>{_fmt(fund.get("eps_growth_yoy"), "%")}</b><span>EPS YoY</span></div>'
            f'<div><b>{_fmt(fund.get("ps"))}</b><span>P/S</span></div>'
            f'<div><b>{_fmt(fund.get("pb"))}</b><span>P/B</span></div>'
            f'<div><b>{_fmt(fund.get("pfcf"))}</b><span>P/FCF</span></div>'
            '</div>')

    perf_html = ""
    if any(v is not None for v in perf.values()):
        perf_html = (
            '<h2>Performance</h2><div class="kpi">'
            f'<div><b>{_fmt(perf.get("perf_1y"), "%")}</b><span>1Y</span></div>'
            f'<div><b>{_fmt(perf.get("perf_ytd"), "%")}</b><span>YTD</span></div>'
            f'<div><b>{_fmt(perf.get("beta"))}</b><span>beta (1y)</span></div></div>')

    peer_rows = ""
    for scope, stats in peer.items():
        for metric, s in (stats or {}).items():
            peer_rows += (
                f"<tr><td>{_esc(scope)}</td><td>{_esc(metric)}</td>"
                f"<td>{_fmt((s or {}).get('value'))}</td><td>{_fmt((s or {}).get('median'))}</td>"
                f"<td><b>{_fmt((s or {}).get('percentile'))}</b> pct</td>"
                f"<td>{_esc((s or {}).get('n'))}</td></tr>")
    peer_html = ""
    if peer_rows:
        peer_html = ("<h2>Peer comparison (vs industry &amp; AI-stack layer)</h2>"
                     "<table><tr><th>scope</th><th>metric</th><th>value</th><th>median</th>"
                     f"<th>percentile</th><th>n</th></tr>{peer_rows}</table>")

    # --- multi-year history sparklines ---
    hist = fs.get("history", {}) or {}

    def _hfmt(v):
        if not isinstance(v, (int, float)):
            return "—"
        a = abs(v)
        if a >= 1e9:
            return f"{v / 1e9:,.1f}B"
        if a >= 1e6:
            return f"{v / 1e6:,.1f}M"
        return f"{v:,.2f}"

    hist_rows = ""
    for key, label in (("annualTotalRevenue", "Revenue"), ("annualNetIncome", "Net income"),
                       ("annualGrossProfit", "Gross profit"), ("annualFreeCashFlow", "Free cash flow"),
                       ("annualDilutedEPS", "Diluted EPS")):
        pts = hist.get(key) or []
        if not pts:
            continue
        first, last = pts[0].get("value"), pts[-1].get("value")
        growth = ""
        if isinstance(first, (int, float)) and isinstance(last, (int, float)) and first:
            growth = f"{(last / first - 1) * 100:,.0f}% / {len(pts)}y"
        hist_rows += (f"<tr><td>{_esc(label)}</td><td>{_sparkline(pts)}</td>"
                      f"<td>{_hfmt(last)}</td><td>{_esc(growth)}</td></tr>")
    hist_html = ""
    if hist_rows:
        hist_html = ("<h2>History (annual, multi-year)</h2>"
                     "<table><tr><th>metric</th><th>trend</th><th>latest</th>"
                     f"<th>change</th></tr>{hist_rows}</table>")

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{_esc(sym)} — AI-stack dashboard</title>
<style>
  body {{ margin:0; font-family:system-ui,sans-serif; background:#0b0f17; color:#e5e7eb; line-height:1.5; }}
  .wrap {{ max-width:900px; margin:0 auto; padding:24px; }}
  h1 {{ margin:0 0 4px; }} h2 {{ margin:24px 0 8px; font-size:16px; color:#93c5fd; border-bottom:1px solid #1f2937; padding-bottom:4px; }}
  .chip {{ background:{color}; color:#0b0f17; font-weight:700; padding:2px 10px; border-radius:8px; font-size:13px; }}
  .meta {{ color:#9ca3af; font-size:13px; }}
  table {{ border-collapse:collapse; width:100%; font-size:14px; }}
  th,td {{ text-align:left; padding:6px 10px; border-bottom:1px solid #1f2937; }}
  .kpi {{ display:flex; gap:24px; flex-wrap:wrap; margin:8px 0; }}
  .kpi div b {{ font-size:20px; }} .kpi div span {{ color:#9ca3af; font-size:12px; display:block; }}
  footer {{ margin-top:32px; color:#6b7280; font-size:12px; border-top:1px solid #1f2937; padding-top:12px; }}
</style></head>
<body><div class="wrap">
  <h1>{_esc(sym)} <span class="chip">{_esc(layer)}</span></h1>
  <div class="meta">live as of {_esc(fs.get('as_of'))} &nbsp; {badge}</div>

  <h2>Valuation — {_esc(val.get('verdict'))}</h2>
  <div class="kpi">
    <div><b>{_esc(val.get('price'))}</b><span>price</span></div>
    <div><b>{_esc(val.get('gf_value'))}</b><span>GF Value</span></div>
    <div><b>{_esc(val.get('discount_pct'))}%</b><span>price vs GF Value</span></div>
    <div><b>{_esc(val.get('pe'))}</b><span>P/E ttm</span></div>
  </div>
  <p>{_esc(val.get('profitability'))}</p>
  <p>{_esc(n.get('valuation_take'))}</p>

  {fund_html}
  {perf_html}
  {hist_html}
  {peer_html}

  <h2>The one bottleneck that matters</h2>
  <p><b>Physical:</b> {_esc(con.get('physical_bottleneck'))}</p>
  <p><b>Regulatory:</b> {_esc(con.get('regulatory_bottleneck'))}</p>
  <p><b>Lead time:</b> {_esc(con.get('lead_time_note'))}</p>
  <p>{_esc(n.get('bottleneck_rationale'))}</p>

  <h2>Key counterparties</h2>
  {cps_tbl}

  <h2>Catalyst calendar</h2>
  {cats_tbl}

  <h2>Scenarios</h2>
  {_ul(n.get('scenarios'))}

  <h2>Risks</h2>
  {_ul(all_risks)}

  <h2>Synthesis</h2>
  <p>{_esc(n.get('synthesis'))}</p>

  <footer>Educational research only — <b>not financial advice</b>. No buy/sell recommendation.
  Figures are date-stamped and decay; verify live before acting.</footer>
</div></body></html>"""
