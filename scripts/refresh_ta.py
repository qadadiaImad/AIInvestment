"""TA-desk refresh runner — thin sibling of refresh_daily.py.

One real step (pull_ta.py -> web/public/data/ta_desk.json), optionally followed by a
Vercel prod deploy. `build_plan()` is pure (no subprocess calls) so it is unit-testable
in isolation, same pattern as test_refresh.py exercises for refresh_daily/refresh_congress.

Usage:
    python refresh_ta.py --dry-run   # print the plan, run nothing
    python refresh_ta.py             # pull_ta.py only
    python refresh_ta.py --deploy    # pull_ta.py, then `vercel --prod --yes` in web/
    python refresh_ta.py --keep-going
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
    """Return the ordered list of steps for the TA-desk refresh.

    Each step is a dict: {"label", "cmd" (list[str]), "cwd" (str)}. Pure — no
    subprocess, no I/O. `args` is the parsed argparse namespace.
    """
    steps = []

    def add(label, cmd, cwd=str(SCRIPTS)):
        steps.append({"label": label, "cmd": cmd, "cwd": cwd})

    add("pull TA-desk data", [PY, "pull_ta.py"])

    if args.deploy:
        add("deploy to Vercel (prod)", ["vercel", "--prod", "--yes"], cwd=str(WEB))

    return steps


def _fmt_cmd(step):
    return f"{' '.join(step['cmd'])}   (cwd={step['cwd']})"


def _parse_args(argv):
    ap = argparse.ArgumentParser(description="TA-desk refresh runner.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the ordered plan and exit 0 without running anything.")
    ap.add_argument("--deploy", action="store_true",
                    help="After a successful pull, run `vercel --prod --yes` in web/.")
    ap.add_argument("--keep-going", action="store_true",
                    help="Continue on step failure; collect errors and report at the end.")
    return ap.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    steps = build_plan(args)

    if args.dry_run:
        print("TA-DESK REFRESH PLAN (dry-run — nothing will execute):")
        print(f"  deploy={args.deploy}  keep_going={args.keep_going}")
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
    print("TA-DESK REFRESH SUMMARY")
    print("#" * 70)
    for label, rc, elapsed in results:
        mark = "ok " if rc == 0 else "FAIL"
        print(f"  [{mark}] {label:40s} {elapsed:7.1f}s  (exit {rc})")
    print(f"  steps run: {len(results)}")
    if aborted:
        print(f"  ABORTED at: {aborted} (use --keep-going to continue past failures)")
    if failures:
        print(f"  failures: {len(failures)} -> "
              + ", ".join(f"{l} (exit {rc})" for l, rc in failures))
    else:
        print("  failures: none")


if __name__ == "__main__":
    raise SystemExit(main())
