"""Build the capital web: write the JSON snapshot + the interactive HTML.

Usage:  python build_capital_web.py [--out <repo_root>]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from aiinvest import capital_web as cw
from aiinvest import enrich


def main(argv=None):
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(repo_root), help="Output directory (default: repo root).")
    ap.add_argument("--enriched", default=str(repo_root / "capital_web_enriched.json"),
                    help="AI-extracted edge store to merge in (if present).")
    args = ap.parse_args(argv)

    graph = cw.build_graph()
    enriched = enrich.load_store(args.enriched)
    if enriched:
        graph["edges"] = enrich.merge_enriched(graph["edges"], enriched)
        print(f"  merged {len(enriched)} ai-extracted edge(s) from {args.enriched}")
    issues = cw.validate(graph)
    if issues:
        print("VALIDATION FAILED:")
        for i in issues:
            print("  -", i)
        return 1

    out = pathlib.Path(args.out)
    json_path = out / "capital_web.json"
    html_path = out / "capital_web.html"
    json_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    html_path.write_text(cw.to_html(graph), encoding="utf-8")

    n_edges = len(graph["edges"])
    n_nodes = len(graph["nodes"])
    print(f"OK  nodes={n_nodes} edges={n_edges}")
    print(f"  wrote {json_path}")
    print(f"  wrote {html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
