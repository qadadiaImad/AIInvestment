import argparse, json, pathlib
from aiinvest.market import fetch_market_pulse, _utcnow
from aiinvest.daily_brief import pick_movers, build_brief, render_post, rail_check
from aiinvest.brief_chart import render_chart_html, write_chart_png

def _load(data_dir, name):
    return json.loads((pathlib.Path(data_dir) / name).read_text(encoding="utf-8"))

def _rows(bundle):
    # Real bundles carry rows under "screener" keyed by "symbol"; test fixtures use
    # "rows" (or a bare list) keyed by "ticker". Normalize both to rows with "ticker".
    if isinstance(bundle, dict):
        raw = bundle.get("screener") or bundle.get("rows") or []
    else:
        raw = bundle
    out = []
    for r in raw:
        if isinstance(r, dict) and "ticker" not in r and "symbol" in r:
            r = {**r, "ticker": r["symbol"]}
        out.append(r)
    return out

def _articles(news):
    # Real news.json nests articles under "articles"; fixtures pass a bare list.
    return news.get("articles", []) if isinstance(news, dict) else news

def _price_series(raw, tail=180):
    # Real prices/<SYM>.json is {"series": [{"date","close"}, ...]}; fixtures pass a bare
    # list of [date, close] pairs. Normalize both to [[date, close], ...], last `tail` points.
    pts = raw.get("series", []) if isinstance(raw, dict) else raw
    out = []
    for p in pts:
        if isinstance(p, dict):
            date, close = p.get("date"), p.get("close")
        else:
            date, close = p[0], p[1]
        if close is None:  # a gap in the series would crash float() in the renderer
            continue
        out.append([date, close])
    return out[-tail:]

def run(date, data_dir, out_dir, fetch=None):
    pulse = fetch_market_pulse(fetch=fetch) if fetch else fetch_market_pulse()
    site, quantum, news = _load(data_dir, "site.json"), _load(data_dir, "quantum.json"), _load(data_dir, "news.json")
    # The quantum bundle's Q5-applications layer is incumbent ADOPTERS of quantum (banks,
    # pharma) — not frontier pure-plays. The "quantum & frontier" spotlight wants a pure-play,
    # so drop the adopter layer before ranking. (Fixtures carry no "layer" → unaffected.)
    quantum_rows = [r for r in _rows(quantum) if not (isinstance(r, dict) and r.get("layer") == "Q5-applications")]
    picks = pick_movers(_rows(site), quantum_rows, _articles(news))
    if picks["ai"] is None or picks["quantum"] is None:
        side = "ai" if picks["ai"] is None else "quantum"
        raise RuntimeError(f"no usable mover for {side}: bundle rows missing/non-numeric perf_1y")
    brief = build_brief(date, pulse, picks, catalysts=["the next major macro print", "AI-sector earnings"])
    post = render_post(brief)
    violations = rail_check(post)
    if violations:
        raise RuntimeError("rail_check failed: " + "; ".join(violations))
    day = pathlib.Path(out_dir) / date
    day.mkdir(parents=True, exist_ok=True)
    (day / "brief.md").write_text(post, encoding="utf-8")
    ai_sym = picks["ai"]["ticker"]
    chart_error = None
    try:
        series = _price_series(_load(data_dir, f"prices/{ai_sym}.json"))
        if not series:
            raise ValueError(f"no price series for {ai_sym}")
        write_chart_png(render_chart_html(ai_sym, series), str(day / "chart.png"))
        chart = "chart.png"
    except Exception as e:  # chart is best-effort; brief still ships, but record why it failed
        chart = None
        chart_error = str(e)
    meta = {"date": date, "generated_at": _utcnow(), "picks": {"ai": ai_sym, "quantum": picks["quantum"]["ticker"]},
            "market_pulse": pulse, "chart": chart, "chart_error": chart_error,
            "rails_passed": not violations,
            "sources": [v["source"] for v in pulse.values()]}
    (day / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta

if __name__ == "__main__":
    from datetime import datetime, timezone
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    help="brief date YYYY-MM-DD (default: today, UTC)")
    ap.add_argument("--data-dir", default="../web/public/data")
    ap.add_argument("--out-dir", default="../content/daily_brief")
    a = ap.parse_args()
    m = run(a.date, a.data_dir, a.out_dir)
    print(f"wrote brief for {m['date']}: AI={m['picks']['ai']} Q={m['picks']['quantum']} rails_passed={m['rails_passed']}")
