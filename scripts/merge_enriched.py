"""Validate AI-extracted candidate edges (the safety gate) and merge accepted into the store.

    python merge_enriched.py            # processes data/enrich/*_edges.json
Accepted edges (quote-backed, node-resolved, valid certainty) append to capital_web_enriched.json;
rejected edges are printed with reasons. build_capital_web.py then renders them (dashed/violet).
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import pathlib
import sys

from aiinvest import capital_web, enrich


def main(argv=None):
    repo = pathlib.Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default=str(repo / "data" / "enrich"))
    ap.add_argument("--store", default=str(repo / "capital_web_enriched.json"))
    args = ap.parse_args(argv)

    node_ids = {n["id"] for n in capital_web.build_graph()["nodes"]}
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    store = enrich.load_store(args.store)
    seen = {(e["src"], e["dst"], e["type"]) for e in store}
    acc = rej = 0

    for f in sorted(glob.glob(str(pathlib.Path(args.candidates) / "*_edges.json"))):
        try:
            cands = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"  skip {f}: {e}")
            continue
        accepted, rejected = enrich.accept_edges(cands, node_ids)
        for e in accepted:
            key = (e["src"], e["dst"], e["type"])
            if key in seen:
                continue
            e = dict(e)
            e.setdefault("origin", "ai-extracted")
            e.setdefault("retrieved_at", now)
            e.setdefault("source_class", "news-html")
            store.append(e)
            seen.add(key)
            acc += 1
        rej += len(rejected)
        for r in rejected:
            print(f"  reject {r.get('src')}->{r.get('dst')} ({r.get('type')}): {r['reasons']}")

    enrich.save_store(args.store, store)
    print(f"accepted {acc} new, rejected {rej}; store now {len(store)} edges -> {args.store}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
