"""Whole-stack screener — rank/compare the universe in one sortable HTML table.

`screen(dossiers)` -> ranked rows; `to_screener_html(rows)` -> standalone page. Pure
functions. Ranks by price-vs-GF-Value discount (most undervalued first), undated/unknown
last. Always carries the "not financial advice" disclaimer.
"""
from __future__ import annotations

import html as _html

_LAYER_COLOR = {
    "L0-energy": "#f59e0b", "L1-chips": "#10b981", "L2-infra": "#3b82f6",
    "L3-models": "#8b5cf6", "L4-application": "#ec4899", "private-lab": "#ef4444",
}


def _val(metrics, name):
    return (metrics.get(name) or {}).get("value")


def _row(dossier):
    m = dossier.get("metrics", {})
    price = _val(m, "current_price")
    gf = _val(m, "gf_value")
    disc = None
    if isinstance(price, (int, float)) and isinstance(gf, (int, float)) and gf:
        disc = round((gf - price) / gf * 100, 1)
    dated = [c for c in dossier.get("catalysts", []) if c.get("date")]
    nxt = min(dated, key=lambda c: c["date"]) if dated else None
    verify = any((mm or {}).get("stale") for mm in m.values())
    return {
        "symbol": dossier.get("symbol"),
        "layer": dossier.get("layer"),
        "price": price,
        "pe": _val(m, "price_earnings_ttm"),
        "gf_discount_pct": disc,
        "lab_exposure": bool(dossier.get("relationships", {}).get("lab_exposure")),
        "next_catalyst": nxt,
        "verify_live": verify,
    }


def screen(dossiers):
    rows = [_row(d) for d in dossiers]
    # discount desc; None last; tie-break by symbol asc.
    rows.sort(key=lambda r: (r["gf_discount_pct"] is None,
                             -(r["gf_discount_pct"] or 0.0),
                             r["symbol"] or ""))
    return rows


def _esc(x):
    return _html.escape(str(x)) if x is not None else "—"


def to_screener_html(rows, title="AI-Stack Screener"):
    body = []
    for r in rows:
        color = _LAYER_COLOR.get(r["layer"], "#9ca3af")
        nc = r["next_catalyst"]
        nc_txt = f"{nc.get('date')} {nc.get('title') or nc.get('id', '')}" if nc else "—"
        body.append(
            "<tr>"
            f"<td>{_esc(r['symbol'])}</td>"
            f"<td><span style='background:{color};color:#0b0f17;padding:1px 8px;border-radius:6px'>{_esc(r['layer'])}</span></td>"
            f"<td>{_esc(r['price'])}</td>"
            f"<td>{_esc(r['pe'])}</td>"
            f"<td>{_esc(r['gf_discount_pct'])}</td>"
            f"<td>{'✓' if r['lab_exposure'] else ''}</td>"
            f"<td>{_esc(nc_txt)}</td>"
            f"<td>{'⚠' if r['verify_live'] else ''}</td>"
            "</tr>")
    rows_html = "".join(body)
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
  body {{ margin:0; font-family:system-ui,sans-serif; background:#0b0f17; color:#e5e7eb; }}
  .wrap {{ max-width:1000px; margin:0 auto; padding:24px; }}
  h1 {{ font-size:20px; }}
  table {{ border-collapse:collapse; width:100%; font-size:14px; }}
  th,td {{ text-align:left; padding:6px 10px; border-bottom:1px solid #1f2937; }}
  th {{ color:#93c5fd; cursor:pointer; }}
  footer {{ margin-top:24px; color:#6b7280; font-size:12px; border-top:1px solid #1f2937; padding-top:12px; }}
</style></head>
<body><div class="wrap">
  <h1>{title} <span style="font-size:12px;color:#9ca3af">— sorted by price vs GF Value (most undervalued first)</span></h1>
  <table id="t">
    <thead><tr><th>Symbol</th><th>Layer</th><th>Price</th><th>P/E</th><th>GF Disc %</th>
    <th>Lab Exp</th><th>Next Catalyst</th><th>Verify</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  <footer>Educational research only — <b>not financial advice</b>. No buy/sell recommendation.
  Figures are date-stamped and decay; verify live before acting.</footer>
  <script>
    // tiny click-to-sort on any column
    document.querySelectorAll('#t th').forEach((th, i) => th.addEventListener('click', () => {{
      const tb = document.querySelector('#t tbody');
      const rows = [...tb.rows];
      const num = v => {{ const n = parseFloat(v.replace(/[^0-9.\\-]/g, '')); return isNaN(n) ? -Infinity : n; }};
      rows.sort((a, b) => num(b.cells[i].innerText) - num(a.cells[i].innerText));
      rows.forEach(r => tb.appendChild(r));
    }}));
  </script>
</div></body></html>"""
