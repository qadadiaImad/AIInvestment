"""Full-refresh orchestrator: fair value + daily AI/quantum/news + congress.

This is the "Refresh data" one-button pipeline for the Studio. It chains the three
refreshers in the ONE correct order:

    1. fair-value backfill (GuruFocus scalar, headless fresh-browser-per-ticker)
         -> writes data/fundamental/<SYM>.json
         -> MUST run BEFORE the export, because export_site.py folds these values
            into site.json/quantum.json and computes our valuation tag from live price.
    2. refresh_daily.py
         -> pull_ai_stack + prices + merge + capital web + graph + EXPORT (picks up the
            fresh fair values) + quantum + screener + news.
    3. refresh_congress.py --years <Y> --keep-going
         -> rebuilds web/public/data/congress.json (monthly-cadence source).

Fair value is a GATED source (GuruFocus). The headless path reliably gets the current
scalar VALUE (the historical series still needs the Playwright MCP, Mode B); saves are
merge-protected so a gated miss never downgrades an existing value. Backfilling the whole
universe is slow (fresh Chromium + gentle pacing per ticker) — expect tens of minutes. Use
--fundamentals none to skip it, or --fundamentals ai|quantum to narrow.

(Supersedes the old prices-only refresh_all; the canonical daily pipeline is refresh_daily.py,
which this calls as step 2.)

Usage:
    python refresh_all.py --dry-run                 # print the ordered plan, run nothing
    python refresh_all.py                           # full refresh (fundamentals=all, congress 2026)
    python refresh_all.py --fundamentals ai         # only AI-layer fair values
    python refresh_all.py --fundamentals none       # skip fair value (daily + congress only)
    python refresh_all.py --years 2025 2026         # also re-pull 2025 congress
    python refresh_all.py --keep-going              # continue past a failed step
    python refresh_all.py --deploy                  # rebuild + `vercel --prod --yes` in web/

Educational/research only — not investment advice.
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import time

SCRIPTS = pathlib.Path(__file__).resolve().parent
WEB = SCRIPTS.parent / "web"
PY = sys.executable


def build_plan(args):
    """Ordered list of steps: {"label", "cmd" (list[str]), "cwd"}. Pure — no I/O.

    fundamentals in {"all","ai","quantum","none"}; "none" omits the fair-value step.
    The congress step always gets --keep-going (a flaky PDF download must not abort it).
    """
    steps = []

    def add(label, cmd, cwd=str(SCRIPTS)):
        steps.append({"label": label, "cmd": cmd, "cwd": cwd})

    fundamentals = getattr(args, "fundamentals", "all")
    if fundamentals and fundamentals != "none":
        add(f"fair-value backfill (universe={fundamentals})",
            [PY, "fundamental_backfill.py", "--universe", fundamentals])

    add("daily AI/quantum/news refresh", [PY, "refresh_daily.py"])

    years = [str(y) for y in args.years]
    add("monthly congress refresh",
        [PY, "refresh_congress.py", "--years", *years, "--keep-going"])

    if getattr(args, "deploy", False):
        add("deploy to Vercel (prod)", ["vercel", "--prod", "--yes"], cwd=str(WEB))

    return steps


def _fmt_cmd(step):
    return f"{' '.join(step['cmd'])}   (cwd={step['cwd']})"


def _parse_args(argv):
    ap = argparse.ArgumentParser(description="Full AIInvestment refresh: fair value + daily + congress.")
    ap.add_argument("--fundamentals", choices=["all", "ai", "quantum", "none"], default="all",
                    help="Fair-value backfill scope (default: all). 'none' skips it.")
    ap.add_argument("--years", type=int, nargs="+", default=[2026],
                    help="Congress PTR years to pull (default: 2026; 2025 is stable/historical).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the ordered plan and exit 0 without running anything.")
    ap.add_argument("--deploy", action="store_true",
                    help="After a successful pipeline, run `vercel --prod --yes` in web/.")
    ap.add_argument("--keep-going", action="store_true",
                    help="Continue on step failure; collect errors and report at the end.")
    return ap.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    steps = build_plan(args)

    if args.dry_run:
        print("FULL REFRESH PLAN (dry-run — nothing will execute):")
        print(f"  fundamentals={args.fundamentals}  years={args.years}  "
              f"deploy={args.deploy}  keep_going={args.keep_going}")
        for i, step in enumerate(steps, 1):
            print(f"  {i:2d}. {step['label']}")
            print(f"      $ {_fmt_cmd(step)}")
        print(f"\n{len(steps)} step(s) planned.")
        return 0

    results = []
    failures = []

    for i, step in enumerate(steps, 1):
        print("\n" + "=" * 70)
        print(f"STEP {i}/{len(steps)}: {step['label']}")
        print(f"$ {_fmt_cmd(step)}")
        print("=" * 70, flush=True)
        t0 = time.time()
        try:
            proc = subprocess.run(step["cmd"], cwd=step["cwd"], text=True)
            rc = proc.returncode
        except FileNotFoundError as exc:
            rc = 127
            print(f"  [error] command not found: {exc}", flush=True)
        elapsed = time.time() - t0
        results.append((step["label"], rc, elapsed))
        print(f"  -> exit {rc} in {elapsed:.1f}s", flush=True)

        if rc != 0:
            failures.append((step["label"], rc))
            if not args.keep_going:
                _summary(results, failures, aborted=step["label"])
                return 1

    _summary(results, failures, aborted=None)
    return 1 if failures else 0


def _summary(results, failures, aborted):
    print("\n" + "#" * 70)
    print("FULL REFRESH SUMMARY")
    print("#" * 70)
    for label, rc, elapsed in results:
        mark = "ok " if rc == 0 else "FAIL"
        print(f"  [{mark}] {label:42s} {elapsed:7.1f}s  (exit {rc})")
    print(f"  steps run: {len(results)}")
    if aborted:
        print(f"  ABORTED at: {aborted} (use --keep-going to continue past failures)")
    print(f"  failures: {len(failures) if failures else 'none'}")


if __name__ == "__main__":
    raise SystemExit(main())
