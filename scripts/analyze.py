"""One-command data pipeline for a ticker: dossier -> fact sheet (live).

    python analyze.py NVDA [--gf-text-file path]

Runs the live pulls (TradingView + Yahoo + EDGAR + peers + multi-year history) and writes
the fact sheet. The reasoning/dashboard step is agentic: ask Claude Code to "analyze <SYM>"
(it follows skills/analyst/SKILL.md, writes a narrative, then runs render_dashboard.py).
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_factsheet  # noqa: E402
import pull_dossier  # noqa: E402


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv:
        print("usage: python analyze.py SYMBOL [--gf-text-file path]")
        return 2
    sym = argv[0].upper()
    rc = pull_dossier.main([sym] + argv[1:])
    if rc:
        return rc
    rc = build_factsheet.main([sym])
    if rc:
        return rc
    print()
    print(f"[ok] Live data ready for {sym}.")
    print(f"  Next (agentic): in Claude Code say  analyze {sym}")
    print(f"  or render directly:  python render_dashboard.py {sym} --narrative <narrative.json>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
