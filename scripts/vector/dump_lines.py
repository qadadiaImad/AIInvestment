"""Dump an episode's dialogue as SPEAKER | line, in order.

Used to hand a shipped episode to a rewrite as a voice reference. A summary
of the tone is useless for this; the model needs the actual exchanges, in
sequence, to hear the rhythm of Rex being wrong and Sol landing on him.

  python scripts/vector/dump_lines.py FairMarketEp1
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BEAT = re.compile(r"\n  \{at: (\d+)")
LINE = re.compile(r'line: "((?:[^"\\]|\\.)*)"')
SPK = re.compile(r'speaker: "([A-Z]+)"')
VO = re.compile(r'vo: "([a-z_0-9]+)"')


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "FairMarketEp1"
    src = (REPO / "remotion/src/compositions" / (name + ".tsx")).read_text(
        "utf-8", errors="replace")
    body = src[src.index("const BEATS"):]
    parts = BEAT.split(body)
    out = []
    for i in range(1, len(parts), 2):
        at, blk = int(parts[i]), parts[i + 1].split("\n  {at:")[0]
        ln, sp, vo = LINE.search(blk), SPK.search(blk), VO.search(blk)
        if not ln:
            continue
        out.append(dict(at=at, speaker=sp.group(1) if sp else "?",
                        vo=vo.group(1) if vo else "", line=ln.group(1)))
    for b in out:
        print("%-4s | %s" % (b["speaker"], b["line"]))
    (REPO / "data/bubbles").mkdir(parents=True, exist_ok=True)
    (REPO / "data/bubbles" / (name + "_lines.json")).write_text(
        json.dumps(out, indent=1), "utf-8")


if __name__ == "__main__":
    main()
