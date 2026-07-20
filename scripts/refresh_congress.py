"""Monthly congress-trading refresh orchestrator.

The Congress (STOCK Act PTR) data updates on a MONTHLY cadence, not daily. This driver
re-pulls the full House PTR set per year, (optionally) recomputes conflict-of-interest
overlays, and rebuilds the page-ready bundle.

Ordered pipeline:

    1. pull_congress.py --year 2025 --limit 99999 --delay <D>   (full year pull)
    2. pull_congress.py --year 2026 --limit 99999 --delay <D>   (full year pull)
       ... one pull per --years entry (default [2025, 2026]).
    3. pull_conflict.py            (OPTIONAL — only if the file exists; skipped with a notice)
    4. pull_member_profiles.py     (OPTIONAL — only if the file exists; party/ideology/policy areas)
    5. export_congress.py          merge years -> web/public/data/congress.json

Usage:
    python refresh_congress.py --dry-run             # print the ordered plan, run nothing
    python refresh_congress.py                       # full monthly congress refresh
    python refresh_congress.py --years 2024 2025 2026
    python refresh_congress.py --delay 1.0           # be gentler between PDF downloads
    python refresh_congress.py --deploy              # rebuild + `vercel --prod --yes` in web/
    python refresh_congress.py --keep-going          # don't abort on a step failure

Educational/research only — not investment advice. Not an accusation of wrongdoing
against any individual.
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

_FULL_LIMIT = "99999"          # "full" pull: don't cap PTRs
_CONFLICT_CLI = "pull_conflict.py"  # may not exist yet — guarded
_MEMBER_CLI = "pull_member_profiles.py"  # may not exist yet — guarded


def build_plan(args):
    """Return the ordered list of steps for the monthly congress pipeline.

    Each step is a dict: {"label", "cmd" (list[str]), "cwd" (str)}.
    Pure — no subprocess, no I/O. The conflict step is included only when
    scripts/pull_conflict.py exists on disk (guarded here so callers/tests can see it).
    """
    steps = []
    delay = str(args.delay)

    def add(label, cmd, cwd=str(SCRIPTS)):
        steps.append({"label": label, "cmd": cmd, "cwd": cwd})

    for year in args.years:
        add(f"pull congress PTRs {year} (full)",
            [PY, "pull_congress.py", "--year", str(year),
             "--limit", _FULL_LIMIT, "--delay", delay])

    if os.path.exists(str(SCRIPTS / _CONFLICT_CLI)):
        add("pull conflict-of-interest overlay", [PY, _CONFLICT_CLI])

    if os.path.exists(str(SCRIPTS / _MEMBER_CLI)):
        add("pull member profiles (party/ideology/policy areas)", [PY, _MEMBER_CLI])

    add("export congress.json", [PY, "export_congress.py"])

    if args.deploy:
        add("deploy to Vercel (prod)", ["vercel", "--prod", "--yes"], cwd=str(WEB))

    return steps


def _fmt_cmd(step):
    return f"{' '.join(step['cmd'])}   (cwd={step['cwd']})"


def _parse_args(argv):
    ap = argparse.ArgumentParser(description="Monthly AIInvestment congress refresh orchestrator.")
    ap.add_argument("--years", type=int, nargs="+", default=[2025, 2026],
                    help="Years to pull (default: 2025 2026).")
    ap.add_argument("--delay", type=float, default=0.4,
                    help="Seconds between PTR PDF downloads (politeness; default 0.4).")
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
        print("MONTHLY CONGRESS REFRESH PLAN (dry-run — nothing will execute):")
        print(f"  years={args.years}  delay={args.delay}  deploy={args.deploy}  "
              f"keep_going={args.keep_going}")
        conflict_present = os.path.exists(str(SCRIPTS / _CONFLICT_CLI))
        print(f"  pull_conflict.py present: {conflict_present} "
              f"({'included' if conflict_present else 'skipped — file absent'})")
        for i, step in enumerate(steps, 1):
            print(f"  {i:2d}. {step['label']}")
            print(f"      $ {_fmt_cmd(step)}")
        print(f"\n{len(steps)} step(s) planned.")
        return 0

    results = []
    failures = []
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
    print("MONTHLY CONGRESS REFRESH SUMMARY")
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

    lines, n_failed = bundles.render_verification(
        SCRIPTS.parent, driver=bundles.DRV_CONGRESS)
    for line in lines:
        print(line)
    return n_failed


if __name__ == "__main__":
    raise SystemExit(main())
