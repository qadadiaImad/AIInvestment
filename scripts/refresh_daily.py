"""Daily refresh orchestrator — re-pull fundamentals, recompute the graph/relationships,
rebuild the site bundle, and (optionally) redeploy to Vercel.

Ordered pipeline (each step a separate CLI, run via subprocess):

    1. pull_ai_stack.py        raw AI-stack fundamentals (TradingView REST)
    2. pull_prices.py          5y daily prices (Yahoo REST) -> web/public/data/prices/
    3. merge_enriched.py       validate + merge ai-extracted relationship edges
    4. build_capital_web.py    rebuild the capital-web graph (curated + enriched)
    5. run_graph_analysis.py   metrics/health/macro_stress/fed_path/vulnerability
                               -> web/public/data/graph_analysis.json
    6. run_backtest.py         (OPTIONAL, heavy) strategy backtests -> backtests.json
    7. export_site.py          assemble the public bundle -> web/public/data/site.json
    8. build_screener.py       rebuild the standalone screener HTML
    9. vercel --prod --yes     (OPTIONAL, --deploy) redeploy from web/

The graph_analysis + site export end up writing web/public/data/graph_analysis.json and
web/public/data/site.json (see step 5 + 7). Backtest is heavy/optional: skipped by default
(use --with-backtest to include it). Site export reads the prices/fundamental/factsheet
artifacts the earlier steps refresh.

Usage:
    python refresh_daily.py --dry-run         # print the ordered plan, run nothing
    python refresh_daily.py                   # full daily refresh (no backtest, no deploy)
    python refresh_daily.py --with-backtest   # include the heavy backtest step
    python refresh_daily.py --deploy          # refresh + `vercel --prod --yes` in web/
    python refresh_daily.py --keep-going      # don't abort on a step failure; report at end

Educational/research only — not financial advice.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
import time

from aiinvest import bundles

SCRIPTS = pathlib.Path(__file__).resolve().parent
WEB = SCRIPTS.parent / "web"
PY = sys.executable

_NEWS_CLI = "pull_news.py"  # may not exist yet — guarded

# A "step" is (label, cmd, cwd). cmd is a list of args; PY/"vercel" is element 0.
# build_plan() is a PURE function (no side effects) so it is unit-testable.


def build_plan(args):
    """Return the ordered list of steps for the daily pipeline.

    Each step is a dict: {"label", "cmd" (list[str]), "cwd" (str)}.
    Pure — no subprocess, no I/O. `args` is the parsed argparse namespace.
    """
    steps = []

    def add(label, cmd, cwd=str(SCRIPTS)):
        steps.append({"label": label, "cmd": cmd, "cwd": cwd})

    add("pull AI-stack fundamentals", [PY, "pull_ai_stack.py"])
    add("pull 5y prices", [PY, "pull_prices.py"])
    add("merge ai-extracted edges", [PY, "merge_enriched.py"])
    add("build capital web", [PY, "build_capital_web.py"])
    add("graph analysis (metrics/health/macro/fed/vuln)", [PY, "run_graph_analysis.py"])

    if os.path.exists(str(SCRIPTS / "build_chokepoints.py")):
        add("build chokepoint layer -> chokepoints.json", [PY, "build_chokepoints.py"])

    if args.with_backtest:
        add("backtest (heavy)", [PY, "run_backtest.py"])
    add("export site.json", [PY, "export_site.py"])

    if os.path.exists(str(SCRIPTS / "build_risk.py")):
        add("compute risk analytics -> risk.json", [PY, "build_risk.py"])

    if os.path.exists(str(SCRIPTS / "build_archetypes.py")):
        add("compute investor-archetype scorecards -> archetypes.json",
            [PY, "build_archetypes.py"])

    if os.path.exists(str(SCRIPTS / "build_portfolio.py")):
        add("compute portfolio -> web/data/portfolio.json", [PY, "build_portfolio.py"])

    if os.path.exists(str(SCRIPTS / "pull_macro.py")):
        add("pull macro dashboard -> macro.json", [PY, "pull_macro.py"])

    # Quantum sector vertical (OPTIONAL — only when the quantum CLIs exist). Runs AFTER
    # the AI export so the AI pipeline stays byte-identical: pull quantum fundamentals,
    # then export the quantum bundle (web/public/data/quantum.json).
    if os.path.exists(str(SCRIPTS / "pull_quantum.py")):
        add("pull quantum fundamentals", [PY, "pull_quantum.py"])
    if os.path.exists(str(SCRIPTS / "export_quantum.py")):
        add("export quantum.json", [PY, "export_quantum.py"])

    add("build screener", [PY, "build_screener.py"])

    # News pull (OPTIONAL — only when pull_news.py exists). Runs after the site +
    # screener are rebuilt so the universe (site.json) and curated edges are current.
    if os.path.exists(str(SCRIPTS / _NEWS_CLI)):
        add("pull news + graph linkage", [PY, _NEWS_CLI])

    if args.deploy:
        add("deploy to Vercel (prod)", ["vercel", "--prod", "--yes"], cwd=str(WEB))

    return steps


def _fmt_cmd(step):
    return f"{' '.join(step['cmd'])}   (cwd={step['cwd']})"


def _parse_args(argv):
    ap = argparse.ArgumentParser(description="Daily AIInvestment refresh orchestrator.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the ordered plan and exit 0 without running anything.")
    ap.add_argument("--with-backtest", action="store_true",
                    help="Include the heavy backtest step (skipped by default).")
    ap.add_argument("--deploy", action="store_true",
                    help="After a successful pipeline, run `vercel --prod --yes` in web/.")
    ap.add_argument("--keep-going", action="store_true",
                    help="Continue on step failure; collect errors and report at the end.")
    return ap.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    steps = build_plan(args)

    if args.dry_run:
        print("DAILY REFRESH PLAN (dry-run — nothing will execute):")
        print(f"  with_backtest={args.with_backtest}  deploy={args.deploy}  "
              f"keep_going={args.keep_going}")
        for i, step in enumerate(steps, 1):
            print(f"  {i:2d}. {step['label']}")
            print(f"      $ {_fmt_cmd(step)}")
        print(f"\n{len(steps)} step(s) planned.")
        return 0

    results = []   # (label, returncode, elapsed)
    failures = []  # (label, returncode)
    deploy_url = None

    for i, step in enumerate(steps, 1):
        print("\n" + "=" * 70)
        print(f"STEP {i}/{len(steps)}: {step['label']}")
        print(f"$ {_fmt_cmd(step)}")
        print("=" * 70, flush=True)
        t0 = time.time()
        try:
            proc = subprocess.run(step["cmd"], cwd=step["cwd"],
                                  capture_output=step["label"].startswith("deploy"),
                                  text=True)
            rc = proc.returncode
            if proc.stdout:
                print(proc.stdout, flush=True)
                for line in proc.stdout.splitlines():
                    s = line.strip()
                    if s.startswith("https://") and "vercel.app" in s:
                        deploy_url = s
        except FileNotFoundError as exc:
            rc = 127
            print(f"  [error] command not found: {exc}", flush=True)
        elapsed = time.time() - t0
        results.append((step["label"], rc, elapsed))
        print(f"  -> exit {rc} in {elapsed:.1f}s", flush=True)

        if rc != 0:
            failures.append((step["label"], rc))
            if not args.keep_going:
                _summary(results, failures, args, deploy_url, aborted=step["label"])
                return 1

    n_bundle_failed = _summary(results, failures, args, deploy_url, aborted=None)
    return 1 if (failures or n_bundle_failed) else 0


def _summary(results, failures, args, deploy_url, aborted):
    print("\n" + "#" * 70)
    print("DAILY REFRESH SUMMARY")
    print("#" * 70)
    for label, rc, elapsed in results:
        mark = "ok " if rc == 0 else "FAIL"
        print(f"  [{mark}] {label:50s} {elapsed:7.1f}s  (exit {rc})")
    print(f"  steps run: {len(results)}")
    if aborted:
        print(f"  ABORTED at: {aborted} (use --keep-going to continue past failures)")
    if failures:
        print(f"  failures: {len(failures)} -> "
              + ", ".join(f"{l} (exit {rc})" for l, rc in failures))
    else:
        print("  failures: none")
    if args.deploy:
        if deploy_url:
            print(f"  deployed: yes -> {deploy_url}")
        else:
            print("  deployed: attempted (no URL line captured / see step output)")
    else:
        print("  deployed: no (--deploy not set)")

    # Steps exiting 0 does not mean the artifacts landed: a guarded step that
    # skips writes nothing and still succeeds. Verify what is on disk.
    lines, n_failed = bundles.render_verification(
        SCRIPTS.parent, driver=bundles.DRV_DAILY)
    for line in lines:
        print(line)
    return n_failed


if __name__ == "__main__":
    raise SystemExit(main())
