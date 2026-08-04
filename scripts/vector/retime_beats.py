"""Recompute every beat's start frame from the MEASURED audio.

Beat boundaries used to be hand-arithmetic, and hand-arithmetic is what
put Sol's closing line 27 frames under its own length so Rex talked over
the top of him. A line's duration is a fact on disk; the schedule should
be derived from it, not re-typed.

What it guarantees:
  * every beat is at least (VO_DELAY + its longest line) frames long, so
    nobody is ever interrupted
  * the director's PACING is preserved — each beat keeps its existing
    share of the slack, so a reaction beat that was written to hold stays
    holding and a brisk exchange stays brisk
  * the episode still lands on exactly TOTAL frames

  python scripts/vector/retime_beats.py [--write]
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COMP = REPO / "remotion" / "src" / "compositions" / "FairMarketEp1.tsx"
VO = REPO / "remotion" / "public" / "audio" / "fairmarket"
FFPROBE = (REPO / "remotion" / "node_modules" / "@remotion"
           / "compositor-win32-x64-msvc" / "ffprobe.exe")
FPS = 30
VO_DELAY = 6
TOTAL = 5100          # 170s (2:50) — owner chose to run long rather than
                      # trim the both-sides beats for the closing argument
MIN_TAIL = 14          # never let a line end flush with the cut
MIN_SILENT = 66        # a title/outro card with no dialogue still needs
                       # time to be read; proportional sharing alone
                       # squeezed the outro to 1.2s


def dur(stem: str) -> int:
    p = VO / f"{stem}.wav"
    if not p.exists():
        sys.exit(f"missing VO: {p}")
    out = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True).stdout.strip()
    return int(round(float(out) * FPS))


def parse(src: str):
    i = src.index("= [", src.index("const BEATS: Beat[] = [")) + 2
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "[":
            depth += 1
        elif src[j] == "]":
            depth -= 1
            if depth == 0:
                body = src[i + 1:j]
                break
    clean = re.sub(r"//.*", "", body)
    beats, depth, cur = [], 0, ""
    for ch in clean:
        if ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        cur += ch
        if depth == 0 and ch == "}":
            beats.append(cur)
            cur = ""
    out = []
    for b in beats:
        at = re.search(r"\bat:\s*(\d+)", b)
        if not at:
            continue
        vo = re.search(r'\bvo:\s*"([a-z0-9_]+)"', b)
        vo2 = re.search(r'\bvo2:\s*"([a-z0-9_]+)"', b)
        at2 = re.search(r"\bat2:\s*(\d+)", b)
        out.append({"at": int(at.group(1)),
                    "vo": vo.group(1) if vo else None,
                    "vo2": vo2.group(1) if vo2 else None,
                    "at2": int(at2.group(1)) if at2 else 0})
    return sorted(out, key=lambda r: r["at"])


def main() -> None:
    src = COMP.read_text("utf-8")
    beats = parse(src)
    for k, b in enumerate(beats):
        nxt = beats[k + 1]["at"] if k + 1 < len(beats) else TOTAL
        b["was"] = nxt - b["at"]
        need = 0
        if b["vo"]:
            need = max(need, VO_DELAY + dur(b["vo"]))
        if b["vo2"]:
            need = max(need, b["at2"] + VO_DELAY + dur(b["vo2"]))
        b["need"] = need
        b["floor"] = need + MIN_TAIL if need else MIN_SILENT

    floor = sum(b["floor"] for b in beats)
    if floor > TOTAL:
        sys.exit(f"lines alone need {floor}f > {TOTAL}f — the episode must "
                 f"get longer or lose a line")
    # hand the surplus out in proportion to the slack each beat ALREADY had,
    # so the existing pacing survives rather than being flattened
    slack = [max(0, b["was"] - b["floor"]) for b in beats]
    pool = TOTAL - floor
    tot = sum(slack)
    if tot:
        extra = [round(pool * s / tot) for s in slack]
    else:
        extra = [pool // len(beats)] * len(beats)
    extra[-1] += pool - sum(extra)

    at = 0
    print(f"{'old':>6}{'new':>6}{'len':>6}{'need':>6}  line")
    for b, e in zip(beats, extra):
        b["new"] = at
        ln = b["floor"] + e
        print(f"{b['at']:6d}{at:6d}{ln:6d}{b['need']:6d}  {b['vo'] or '(title)'}"
              + ("  <-- MOVED" if at != b["at"] else ""))
        at += ln
    assert at == TOTAL, at

    if "--write" not in sys.argv:
        print("\ndry run — pass --write to apply")
        return
    # rewrite each `at:` in place, walking backwards so earlier edits do
    # not shift the offsets of later ones
    out = src
    for b in sorted(beats, key=lambda r: -r["at"]):
        pat = re.compile(r"(\{at:\s*)" + str(b["at"]) + r"(\s*,)")
        out, n = pat.subn(lambda m: f"{m.group(1)}{b['new']}{m.group(2)}",
                          out, count=1)
        if n != 1:
            sys.exit(f"could not rewrite beat at {b['at']}")
    COMP.write_text(out, "utf-8")
    print(f"\nwrote {len(beats)} beat starts to {COMP.name}; total {TOTAL}f")


if __name__ == "__main__":
    main()
