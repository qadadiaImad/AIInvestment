"""Build the whole-stack screener HTML from the latest dossier per ticker.

Usage:  python build_screener.py        # uses every dossier found under data/
"""
from __future__ import annotations

import argparse
import glob
import json
import pathlib
import re
import sys

from aiinvest import screener


def _latest_per_symbol(data_root):
    by_sym = {}
    for path in sorted(glob.glob(str(data_root / "*" / "dossier_*.json"))):
        m = re.search(r"dossier_([A-Z0-9]+)_", pathlib.Path(path).name)
        if m:
            by_sym[m.group(1)] = path  # sorted asc -> last wins = latest
    return [json.loads(pathlib.Path(p).read_text(encoding="utf-8")) for p in by_sym.values()]


def main(argv=None):
    repo = pathlib.Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(repo / "data"))
    ap.add_argument("--out", default=str(repo / "stack_screener.html"))
    args = ap.parse_args(argv)

    dossiers = _latest_per_symbol(pathlib.Path(args.data))
    if not dossiers:
        print("No dossiers found. Run pull_dossier.py for some tickers first.")
        return 1
    rows = screener.screen(dossiers)
    pathlib.Path(args.out).write_text(screener.to_screener_html(rows), encoding="utf-8")
    print(f"Screener ({len(rows)} names) -> {args.out}")
    for r in rows:
        print(f"  {r['symbol']:6} [{r['layer']}] disc={r['gf_discount_pct']} pe={r['pe']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
