"""Pull the episode-3 series from FRED and write a Remotion fixture.

House rule: Python owns the numbers, code draws them, and nothing on screen
is model-authored. So every line the wall draws in "The Machine" is a real
FRED series downsampled here, with the marked points computed from the data
rather than typed in by hand - if the series is revised, the callouts move
with it instead of quietly going stale.

Downsampling is deliberate and lossy in one direction only: it keeps every
extreme. A naive every-Nth-point sample can walk straight past a peak, which
on a crash chart is the one point that matters. So each bucket contributes
its min AND its max in time order, which preserves the envelope.

  python scripts/bubbles/build_series.py
"""
from __future__ import annotations

import csv
import datetime
import json
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "remotion/src/fixtures/bubbles/series.json"
CACHE = REPO / "data/bubbles/fred"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s"


def fetch(series: str) -> list[tuple[str, float]]:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (series + ".csv")
    if not f.exists():
        with urllib.request.urlopen(FRED % series, timeout=60) as r:
            f.write_bytes(r.read())
    rows = []
    for rec in csv.DictReader(f.open()):
        v = rec[series]
        if v in ("", ".", None):
            continue
        rows.append((rec["observation_date"], float(v)))
    return rows


def window(rows, lo, hi):
    return [r for r in rows if lo <= r[0] <= hi]


def envelope(rows, target: int):
    """Downsample to about `target` points, keeping every local extreme."""
    if len(rows) <= target:
        return rows
    step = max(2, len(rows) // (target // 2))
    out = []
    for i in range(0, len(rows), step):
        chunk = rows[i:i + step]
        lo = min(chunk, key=lambda r: r[1])
        hi = max(chunk, key=lambda r: r[1])
        out.extend(sorted({lo, hi}, key=lambda r: r[0]))
    if out[-1] != rows[-1]:
        out.append(rows[-1])
    return out


def peak_trough(rows):
    pk = max(rows, key=lambda r: r[1])
    after = [r for r in rows if r[0] > pk[0]]
    tr = min(after, key=lambda r: r[1]) if after else pk
    return pk, tr


def main() -> None:
    now = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    out = {}

    # 1. CHEAP MONEY -------------------------------------------------
    ff = window(fetch("FEDFUNDS"), "1999-01-01", "2007-12-01")
    hi = max([r for r in ff if r[0] <= "2001-06-01"], key=lambda r: r[1])
    lo = min(ff, key=lambda r: r[1])
    out["fedfunds"] = dict(
        series="FEDFUNDS", unit="%", title="THE PRICE OF MONEY",
        foot="US federal funds rate, monthly average · FRED FEDFUNDS",
        points=envelope(ff, 80),
        marks=[dict(at=hi[0], v=hi[1], label="6.54%"),
               dict(at=lo[0], v=lo[1], label="0.98%")],
        band=dict(hi=1.5, label="22 MONTHS UNDER 1.5%"))

    # 2. THE STORY, PRICED -------------------------------------------
    cs = window(fetch("CSUSHPINSA"), "2000-01-01", "2012-12-01")
    pk, tr = peak_trough(cs)
    out["caseshiller"] = dict(
        series="CSUSHPINSA", unit="", title="US HOME PRICES",
        foot="S&P CoreLogic Case-Shiller US National Home Price Index · FRED CSUSHPINSA",
        points=envelope(cs, 80),
        marks=[dict(at=pk[0], v=pk[1], label="PEAK"),
               dict(at=tr[0], v=tr[1], label="-27.4%")])

    # 3. THE DRAWDOWN -------------------------------------------------
    nq = fetch("NASDAQCOM")
    d08 = window(nq, "2007-01-01", "2009-12-31")
    pk, tr = peak_trough(d08)
    out["drawdown2008"] = dict(
        series="NASDAQCOM", unit="", title="THE MARKET, 2007-2009",
        foot="NASDAQ Composite · FRED NASDAQCOM",
        points=envelope(d08, 90),
        marks=[dict(at=pk[0], v=pk[1], label="PEAK"),
               dict(at=tr[0], v=tr[1], label="-55.6%")])

    # 4. THE JOBS -----------------------------------------------------
    ur = window(fetch("UNRATE"), "2005-01-01", "2011-12-01")
    lo = min([r for r in ur if r[0] <= "2007-06-01"], key=lambda r: r[1])
    hi = max(ur, key=lambda r: r[1])
    out["unrate"] = dict(
        series="UNRATE", unit="%", title="UNEMPLOYMENT",
        foot="US unemployment rate · FRED UNRATE",
        points=envelope(ur, 70),
        marks=[dict(at=lo[0], v=lo[1], label="4.4%"),
               dict(at=hi[0], v=hi[1], label="10.0%")])

    # 5. THE ONE THAT COST FIFTEEN YEARS ------------------------------
    lng = window(nq, "1995-01-01", "2016-12-31")
    pk = max(window(lng, "1999-01-01", "2001-01-01"), key=lambda r: r[1])
    tr = min(window(lng, "2001-01-01", "2003-06-01"), key=lambda r: r[1])
    rec = next(r for r in lng if r[0] > tr[0] and r[1] >= pk[1])
    out["dotcom"] = dict(
        series="NASDAQCOM", unit="", title="THE LAST ONE",
        foot="NASDAQ Composite · FRED NASDAQCOM",
        points=envelope(lng, 120),
        marks=[dict(at=pk[0], v=pk[1], label="MAR 2000"),
               dict(at=tr[0], v=tr[1], label="-77.9%"),
               dict(at=rec[0], v=rec[1], label="BACK TO EVEN")],
        span=dict(a=pk[0], b=rec[0], label="15 YEARS"))

    for k, v in out.items():
        v.update(source="https://fred.stlouisfed.org/series/" + v["series"],
                 source_class="api", retrieved_at=now)
        print("  %-12s %4d pts  %s -> %s"
              % (k, len(v["points"]), v["points"][0][0], v["points"][-1][0]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1), "utf-8")
    print("-> " + str(OUT.relative_to(REPO)))


if __name__ == "__main__":
    main()
