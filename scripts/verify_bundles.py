"""Verify that every data bundle the site needs is present, valid and fresh.

Why this exists: the refresh drivers report per-step exit codes, not whether
the artifacts landed. A guarded step that silently produces nothing still
exits 0, so a run can print ``failures: none`` while pages 500. This checks
the *artifacts*.

Usage:
  python verify_bundles.py                 # status table; exit 1 if anything failed
  python verify_bundles.py --fix           # rerun the producer for each FAILED bundle
  python verify_bundles.py --fix --stale   # also rerun producers for STALE bundles
  python verify_bundles.py --only site.json ta_desk.json
  python verify_bundles.py --json          # machine-readable, for the studio app

Policy: missing/corrupt required bundle -> exit 1. Stale -> loud warning, exit 0.
"""
from __future__ import annotations

import argparse
import json as _json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from aiinvest import bundles, fundamental_quality  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"

_MARK = {
    bundles.OK: "ok  ",
    bundles.STALE: "WARN",
    bundles.MISSING: "MISS",
    bundles.TOO_SMALL: "FAIL",
    bundles.UNPARSEABLE: "FAIL",
}


def _fmt_size(n):
    if n is None:
        return "        -"
    for unit in ("B", "K", "M"):
        if n < 1024 or unit == "M":
            return f"{n:>7.0f}{unit}" if unit == "B" else f"{n:>7.1f}{unit}"
        n /= 1024.0


def _fmt_age(r):
    if r.age_h is None:
        return "     -"
    return f"{r.age_h:>5.1f}h"


def _print_table(results):
    print("=" * 78)
    print(f"{'BUNDLE':<24}{'STATUS':<7}{'AGE':>7}{'SIZE':>10}   LIMIT")
    print("=" * 78)
    for r in results:
        limit = f"{r.bundle.max_age_h}h"
        opt = "" if r.bundle.required else "  (optional)"
        print(f"{r.bundle.name:<24}{_MARK[r.status]:<7}{_fmt_age(r):>7}"
              f"{_fmt_size(r.size):>10}   {limit}{opt}")
    print("=" * 78)


def _report_problems(results):
    """Explain every problem and name the command that fixes it."""
    fails = bundles.failures(results)
    warns = bundles.warnings(results)

    if fails:
        print(f"\nFAILED ({len(fails)}) - the site will break on these:")
        for r in fails:
            print(f"  {r.bundle.name}")
            print(f"      why: {r.detail}")
            print(f"      fix: cd scripts && {r.fix_command}")
            if r.bundle.note:
                print(f"     note: {r.bundle.note}")

    if warns:
        print(f"\nWARNINGS ({len(warns)}) - usable, but past cadence or absent:")
        for r in warns:
            print(f"  {r.bundle.name}")
            print(f"      why: {r.detail}")
            print(f"      fix: cd scripts && {r.fix_command}")

    if not fails and not warns:
        print("\nAll bundles present, valid and within cadence.")


def _rerun(results, include_stale):
    """Rerun the producing script for each problem bundle, de-duplicated."""
    targets = list(bundles.failures(results))
    if include_stale:
        targets += bundles.warnings(results)

    # Several bundles can share one producer — run each script once.
    scripts, seen = [], set()
    for r in targets:
        s = r.bundle.produced_by
        if s not in seen:
            seen.add(s)
            scripts.append((s, r.bundle.name))

    if not scripts:
        print("\nNothing to rerun.")
        return 0

    print(f"\nRerunning {len(scripts)} producer script(s):")
    rc_total = 0
    for script, because in scripts:
        path = SCRIPTS / script
        if not path.is_file():
            print(f"  SKIP {script} — not found at {path}")
            rc_total = 1
            continue
        print(f"\n  $ python {script}   (for {because})")
        proc = subprocess.run([sys.executable, script], cwd=str(SCRIPTS))
        print(f"  -> exit {proc.returncode}")
        rc_total = rc_total or proc.returncode
    return rc_total


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fix", action="store_true",
                    help="rerun the producing script for each FAILED bundle")
    ap.add_argument("--stale", action="store_true",
                    help="with --fix, also rerun producers for STALE bundles")
    ap.add_argument("--only", nargs="+", metavar="BUNDLE",
                    help="check only these bundles")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON instead of a table")
    ap.add_argument("--now", help="override 'now' (ISO-8601 UTC) for testing")
    args = ap.parse_args(argv)

    names = None
    if args.only:
        unknown = [n for n in args.only if n not in bundles.BUNDLES]
        if unknown:
            print(f"unknown bundle(s): {', '.join(unknown)}", file=sys.stderr)
            print(f"known: {', '.join(sorted(bundles.BUNDLES))}", file=sys.stderr)
            return 2
        names = args.only

    results = bundles.check_all(REPO, args.now, names)

    if args.json:
        print(_json.dumps([{
            "bundle": r.bundle.name,
            "status": r.status,
            "required": r.bundle.required,
            "detail": r.detail,
            "age_h": r.age_h,
            "age_source": r.age_source,
            "size": r.size,
            "path": r.path,
            "max_age_h": r.bundle.max_age_h,
            "produced_by": r.bundle.produced_by,
            "fix_command": r.fix_command,
            "is_failure": r.is_failure,
            "is_warning": r.is_warning,
        } for r in results], indent=2))
        return 1 if bundles.failures(results) else 0

    _print_table(results)
    _report_problems(results)

    if args.fix:
        rc = _rerun(results, include_stale=args.stale)
        print("\nRe-verifying after rerun...\n")
        results = bundles.check_all(REPO, args.now, names)
        _print_table(results)
        _report_problems(results)
        if rc:
            print(f"\n(one or more producer scripts exited non-zero: rc={rc})")

    print("\nFUNDAMENTAL STORE (GuruFocus)")
    q_lines, q_failed = fundamental_quality.check(REPO)
    for line in q_lines:
        print(line)

    fails = bundles.failures(results)
    warns = bundles.warnings(results)
    print(f"\nsummary: {len(results)} checked, {len(fails) + q_failed} failed, "
          f"{len(warns)} warned")
    if fails and not args.fix:
        print("hint: rerun the producers automatically with  python verify_bundles.py --fix")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
