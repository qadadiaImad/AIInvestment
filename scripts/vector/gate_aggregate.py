"""Aggregate vision-gate workflow verdicts into picks + regen failures.

Usage (from scripts/):
  python -m vector.gate_aggregate <journal.jsonl> <round-tag>
Writes gate_<tag>.json / picks_<tag>.json / failures_<tag>.json into the
visemes work dir. picks merge later rounds over earlier ones downstream.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from vector.visemes_ep1 import VIS


def main(journal: str, tag: str) -> None:
    results = []
    for line in Path(journal).read_text("utf-8").splitlines():
        rec = json.loads(line)
        if (rec.get("type") == "result" and isinstance(rec.get("result"), dict)
                and "pose" in rec["result"]):
            results.append(rec["result"])
    print(f"agents: {len(results)}")
    picks: dict[str, dict[str, str]] = {}
    failures = []
    for r in sorted(results, key=lambda x: x["pose"]):
        pose = r["pose"]
        npass = sum(1 for v in r["verdicts"] if v["pass"])
        picks[pose] = {}
        for vis, cand in (r["best"] or {}).items():
            if cand:
                picks[pose][vis] = f"{pose}__{cand}"
            elif not (vis == "closed" and pose.startswith("sol")):
                failures.append({"pose": pose, "viseme": vis})
        best = {k: (v or "-") for k, v in (r["best"] or {}).items()}
        print(f"{pose}: {npass}/{len(r['verdicts'])} pass, best={best}")
    (VIS / f"gate_{tag}.json").write_text(json.dumps(results, indent=1),
                                          "utf-8")
    (VIS / f"picks_{tag}.json").write_text(json.dumps(picks, indent=1),
                                           "utf-8")
    (VIS / f"failures_{tag}.json").write_text(
        json.dumps(failures, indent=1), "utf-8")
    print(f"\nFAILED TARGETS ({len(failures)}): "
          + json.dumps(failures))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
