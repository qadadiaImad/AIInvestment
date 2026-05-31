"""Fetch one ticker's fundamental (intrinsic) value with a FRESH browser per run.

    python fundamental_fetch.py NVDA

A fresh, state-wiped Chromium per invocation is the gate-dodge (the GuruTrade method) — the
free-view counter never accrues. Reuses the tested extraction; writes a GENERIC record
(field is `fundamental_value`, source is generic) to data/fundamental/<SYM>.json. The
valuation tag is computed downstream from our own price, not taken from the source.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import sys

from aiinvest import fundamental, gurufocus  # extraction regex + chart-JSON parser

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
_STEALTH = ("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
            "Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]});"
            "window.chrome={runtime:{}};")
_URL = "https://www.gurufocus.com/stock/{sym}/valuation"


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_value(text):
    """Pull the fundamental (intrinsic) value via the validated extraction; None if absent."""
    metrics = gurufocus.extract_metrics(text, "", _now())
    return metrics["gf_value"]["value"]


# Note: GuruFocus shows a "free trial / subscribe" PROMO banner on every page — that text is
# NOT a wall and must not cause us to discard a value. A genuine block = the value can't be
# read at all; we detect that by `value is None` and rotate to a fresh instance (owner's rule).
# (The separate chart-data API endpoint can be 403-throttled independently; that only costs us
# the historical series, not the current value, which the page server-renders.)


def fetch(symbol, attempts=3):
    """Fresh browser per attempt; navigate and INTERCEPT the page's own valuation-chart
    response (fundamental value + margin of safety + historical fundamental-value series).
    Rotates on a trial wall or a missing value (owner's rule). innerText regex is the fallback.
    """
    from playwright.sync_api import sync_playwright
    url = _URL.format(sym=symbol)
    parsed, value, text = {}, None, ""
    for _ in range(attempts):
        holder = {}
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox",
                      "--disable-dev-shm-usage"])
            ctx = browser.new_context(user_agent=_UA, viewport={"width": 1440, "height": 900},
                                      ignore_https_errors=True)
            ctx.add_init_script(_STEALTH)
            page = ctx.new_page()

            def _on_resp(resp):
                u = resp.url
                if "/reader/_api/chart/" in u and "valuation" in u and "payload" not in holder:
                    try:
                        holder["payload"] = resp.json()
                    except Exception:  # noqa: BLE001
                        pass
            page.on("response", _on_resp)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(6000)
                text = page.evaluate("() => document.body.innerText")
            except Exception:  # noqa: BLE001
                text = ""
            finally:
                browser.close()  # destroy state -> next attempt is a fresh instance (rotation)
        chart = holder.get("payload")
        parsed = fundamental.parse_valuation_chart(chart) if chart else {}
        # Natural rendering is the reliable path for the value (the page server-renders it);
        # the "free trial/subscribe" promo text is NOT a wall, so we do NOT discard on it.
        value = parsed.get("fundamental_value")
        if value is None:
            value = _extract_value(text)  # innerText (natural inspection) — primary
        if value is not None:
            break  # got a real value; the historical series is included only if the API was 200
        # value genuinely absent => blocked => rotate to a fresh instance (owner's rule)
    return {"symbol": symbol, "fundamental_value": value,
            "margin_of_safety_pct": parsed.get("margin_of_safety_pct"),
            "fundamental_value_series": parsed.get("fundamental_value_series", []),
            "retrieved_at": _now(), "source": "fundamental-model"}


def save(sym, rec):
    """Write the record, but NEVER downgrade: keep an existing value/series if the new
    fetch came back empty (e.g. a 403 on the chart API). Makes backfills safe to re-run."""
    repo = pathlib.Path(__file__).resolve().parent.parent
    out_dir = repo / "data" / "fundamental"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{sym}.json"
    if path.exists():
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
            if rec.get("fundamental_value") is None and old.get("fundamental_value") is not None:
                rec["fundamental_value"] = old.get("fundamental_value")
                if rec.get("margin_of_safety_pct") is None:
                    rec["margin_of_safety_pct"] = old.get("margin_of_safety_pct")
            if not rec.get("fundamental_value_series") and old.get("fundamental_value_series"):
                rec["fundamental_value_series"] = old.get("fundamental_value_series")
        except Exception:  # noqa: BLE001
            pass
    path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return path


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv:
        print("usage: python fundamental_fetch.py SYMBOL")
        return 2
    sym = argv[0].upper()
    rec = fetch(sym)
    save(sym, rec)
    n = len(rec.get("fundamental_value_series") or [])
    print(f"{sym}: fundamental_value={rec['fundamental_value']} series={n} -> data/fundamental/{sym}.json")
    return 0 if rec["fundamental_value"] is not None else 1


if __name__ == "__main__":
    sys.exit(main())
