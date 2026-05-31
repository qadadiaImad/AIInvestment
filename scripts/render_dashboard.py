"""Render a per-ticker HTML dashboard from the latest fact sheet + a narrative JSON.

This is the final step of the analyst-skill flow:
    pull_dossier.py SYM  ->  build_factsheet.py SYM  ->  (write narrative.json)  ->  render_dashboard.py SYM --narrative narrative.json

Usage:  python render_dashboard.py NVDA --narrative nvda_narrative.json
The narrative JSON has keys: valuation_take, bottleneck_rationale, scenarios[], risks[], synthesis.
"""
from __future__ import annotations

import argparse
import glob
import json
import pathlib
import sys

from aiinvest import dashboard


def main(argv=None):
    repo = pathlib.Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("--narrative", help="Path to narrative JSON (optional).")
    ap.add_argument("--data", default=str(repo / "data"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    sym = args.symbol.upper()

    hits = sorted(glob.glob(str(pathlib.Path(args.data) / "*" / f"factsheet_{sym}_*.json")))
    if not hits:
        print(f"No fact sheet for {sym}. Run:  python build_factsheet.py {sym}")
        return 1
    fs = json.loads(pathlib.Path(hits[-1]).read_text(encoding="utf-8"))
    narrative = {}
    if args.narrative:
        narrative = json.loads(pathlib.Path(args.narrative).read_text(encoding="utf-8"))

    out = pathlib.Path(args.out) if args.out else (repo / f"{sym.lower()}_dashboard.html")
    out.write_text(dashboard.to_html(fs, narrative), encoding="utf-8")
    print(f"Dashboard {sym} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
