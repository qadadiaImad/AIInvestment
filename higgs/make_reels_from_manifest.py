"""Assemble every reel in reels_manifest.json — the scriptable Phase-2 of the reel engine.

The reel pipeline is a 2-phase hybrid (see README_reels.md):
  Phase 1 (MCP, orchestrator/Claude): generate the animated hero + AI voice per story and
           write their URLs into reels_manifest.json. NOT scriptable — gated MCP resource.
  Phase 2 (no gate, scriptable): assemble each reel from those URLs via make_reel.py.

This is Phase 2 as a plain serial CLI, suitable for the Studio "Make reels" button. The
PARALLEL variant is higgs/_workflow_make_reels.js (run via the Workflow tool, not a shell).
Entries whose hero/voice are still placeholders (Phase 1 not done) are skipped with a notice,
so the button never fires a broken command.

Usage:
    python higgs/make_reels_from_manifest.py [manifest.json]   # default: higgs/reels_manifest.json

Note: the congress reel uses its own builder (_build_reel_congress.py) and is not in the manifest.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HIGGS = ROOT / "higgs"
PY = sys.executable
DEFAULT_MANIFEST = HIGGS / "reels_manifest.json"


def is_placeholder(url) -> bool:
    """True if the URL is missing or a literal placeholder (e.g. <hero_url>) — i.e. Phase 1
    hasn't filled it in. A real asset URL contains a scheme separator (://)."""
    if not url:
        return True
    s = str(url).strip()
    return s.startswith("<") or "://" not in s


def build_jobs(manifest):
    """Turn a manifest into (jobs, skipped). Pure — no subprocess.

    jobs    = [[PY, <make_reel.py>, TK, hero, voice], ...] for entries with real URLs.
    skipped = [(tk, reason), ...] for entries missing a ticker or carrying placeholder URLs.
    Accepts either {"reels": [...]} or a bare list of entries.
    """
    reels = manifest.get("reels", []) if isinstance(manifest, dict) else (manifest or [])
    jobs, skipped = [], []
    for r in reels:
        tk = (r.get("tk") or "").upper()
        hero, voice = r.get("hero"), r.get("voice")
        if not tk:
            skipped.append(("?", "missing ticker"))
            continue
        if tk == "CONG":
            skipped.append((tk, "congress reel uses its own builder (_build_reel_congress.py) — not the stock pipeline"))
            continue
        if is_placeholder(hero) or is_placeholder(voice):
            skipped.append((tk, "placeholder/missing hero or voice URL — run Phase-1 (MCP) first"))
            continue
        jobs.append([PY, str(HIGGS / "make_reel.py"), tk, hero, voice])
    return jobs, skipped


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    mpath = pathlib.Path(argv[0]) if argv else DEFAULT_MANIFEST
    if not mpath.exists():
        print(f"manifest not found: {mpath}")
        return 2

    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    jobs, skipped = build_jobs(manifest)
    n_reels = len(manifest.get("reels", [])) if isinstance(manifest, dict) else len(manifest or [])
    print(f"manifest: {mpath.name}  date={manifest.get('date', '?') if isinstance(manifest, dict) else '?'}  "
          f"reels={n_reels}")
    for tk, why in skipped:
        print(f"  SKIP {tk}: {why}")
    if not jobs:
        print("nothing to assemble — populate hero/voice URLs via Phase-1 (MCP), then re-run.")
        return 1

    ok = 0
    for cmd in jobs:
        tk = cmd[2]
        print(f"\n=== assembling {tk} ===")
        print(f"$ {' '.join(cmd)}", flush=True)
        rc = subprocess.run(cmd, cwd=str(ROOT)).returncode
        print(f"  -> exit {rc}", flush=True)
        if rc == 0:
            ok += 1

    print(f"\ndone: {ok}/{len(jobs)} reels assembled; {len(skipped)} skipped.")
    return 0 if ok == len(jobs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
