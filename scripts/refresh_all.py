"""Daily refresh: re-pull the cheap/fast data, recompute, rebuild the site, redeploy to Vercel.

Cheap DAILY tier (no gated GuruFocus / no AI-narrative re-runs):
  prices (Yahoo 5y) -> backtests -> graph analysis (fresh FRED macro) -> site export
  -> Next build -> `vercel deploy --prod`.
Heavy tier (per-stock fundamentals/factsheets + AI narratives + the gated fundamental
series) changes slowly — refresh those on a weekly cadence, not here.

Usage:  python refresh_all.py            # refresh + redeploy
        python refresh_all.py --no-deploy
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

SCR = pathlib.Path(__file__).resolve().parent
WEB = SCR.parent / "web"
PY = sys.executable


def run(cmd, cwd=SCR):
    print(f"\n$ {cmd}   (cwd={cwd})", flush=True)
    r = subprocess.run(cmd, cwd=str(cwd), shell=True)
    if r.returncode:
        raise SystemExit(f"STEP FAILED ({r.returncode}): {cmd}")


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    deploy = "--no-deploy" not in argv
    run(f'"{PY}" pull_prices.py')          # 5y daily prices (ungated)
    run(f'"{PY}" run_backtest.py')         # recompute strategy backtests on fresh prices
    run(f'"{PY}" run_graph_analysis.py')   # recompute health + fresh FRED macro snapshot
    run(f'"{PY}" export_site.py')          # rebuild site.json (fresh returns, leak-checked)
    run("npm run build", cwd=WEB)          # static rebuild
    if deploy:
        run("vercel deploy --prod --yes", cwd=WEB)
        print("\n[ok] refreshed + redeployed to production.")
    else:
        print("\n[ok] refreshed + rebuilt (skipped deploy).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
