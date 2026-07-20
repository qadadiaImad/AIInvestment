"""One-off driver: build dossier + factsheet for every AI-stack ticker.

Generates data/<date>/dossier_<SYM>_*.json and factsheet_<SYM>_*.json so
export_site.py can assemble the AI stocks into site.json. REST-only
(TradingView/Yahoo/EDGAR); GuruFocus is skipped gracefully.
"""
import sys

import pull_dossier
import build_factsheet
from aiinvest import ai_stack

syms = [t.split(":")[-1] for t in ai_stack.all_tickers()]
ok, fail = 0, []
for i, s in enumerate(syms, 1):
    try:
        pull_dossier.main([s])
        rc = build_factsheet.main([s])
        if rc == 0:
            ok += 1
        else:
            fail.append(s)
        print(f"[{i}/{len(syms)}] {s} fs_rc={rc}", flush=True)
    except Exception as e:  # noqa: BLE001
        fail.append(s)
        print(f"[{i}/{len(syms)}] {s} ERROR {type(e).__name__}: {e}", flush=True)

print(f"DONE ok={ok} fail={len(fail)} failed={fail}", flush=True)
sys.exit(0)
