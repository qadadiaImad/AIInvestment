"""Build a deterministic fact sheet from the latest dossier for a ticker.

Usage:  python build_factsheet.py NVDA
Run `pull_dossier.py <SYMBOL>` first if no dossier exists yet.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import pathlib
import sys

from aiinvest import analyst


def _latest_dossier(data_root, sym):
    hits = sorted(glob.glob(str(data_root / "*" / f"dossier_{sym}_*.json")))
    return hits[-1] if hits else None


def main(argv=None):
    repo = pathlib.Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("--data", default=str(repo / "data"))
    args = ap.parse_args(argv)
    sym = args.symbol.upper()
    data_root = pathlib.Path(args.data)

    path = _latest_dossier(data_root, sym)
    if not path:
        print(f"No dossier for {sym}. Run:  python pull_dossier.py {sym}")
        return 1
    dossier = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fs = analyst.fact_sheet(dossier, now)

    out_dir = data_root / now[:10]
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"factsheet_{sym}_{now.replace(':', '').replace('-', '')}.json"
    out.write_text(json.dumps(fs, indent=2), encoding="utf-8")
    v = fs["valuation"]
    print(f"Fact sheet {sym} [{fs['layer']}] -> {out}")
    print(f"  price={v['price']} gf_value={v['gf_value']} disc={v['discount_pct']}% "
          f"pe={v['pe']} | {v['profitability']}")
    print(f"  bottleneck: {fs['constraint']['physical_bottleneck'][:80]}")
    print(f"  risk_flags: {fs['risk_flags']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
