"""Resumable downloader for the model manifest.

Windows' bundled curl.exe with -C - (resume). Sequential on purpose:
polite to HF, and disk/net is the bottleneck anyway.

CLI (run from scripts/):
    python -m comfy.download --list
    python -m comfy.download --group video-5b
    python -m comfy.download                # everything
"""
from __future__ import annotations

import argparse
import subprocess
import sys

from .manifest import ResolvedFile, resolve


def run_curl(url: str, part) -> int:
    cmd = ["curl.exe", "-L", "--fail", "--retry", "3", "-C", "-",
           "-o", str(part), url]
    return subprocess.call(cmd)


def fetch(rf: ResolvedFile, runner=run_curl) -> str:
    dest = rf.dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size == rf.size:
        return "present"
    part = dest.with_suffix(dest.suffix + ".part")
    rc = runner(rf.url, part)
    if rc != 0:
        raise RuntimeError(f"curl exited {rc} for {rf.url}")
    got = part.stat().st_size
    if got != rf.size:
        raise RuntimeError(
            f"size mismatch for {dest.name}: got {got}, HF says {rf.size} "
            f"(.part kept; rerun to resume)")
    part.replace(dest)
    return "downloaded"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default=None)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    files = [f for f in resolve() if args.group in (None, f.group)]
    print(f"{len(files)} files, {sum(f.size for f in files)/1e9:.1f} GB total")
    if args.list:
        for f in files:
            print(f"  [{f.group}] {f.size/1e9:6.2f} GB  {f.dest}")
        return 0
    for f in files:
        print(f"-> {f.dest.name}", flush=True)
        print(f"   {fetch(f)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
