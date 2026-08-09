"""Detect a stray consonant at the HEAD of a line.

The owner: "still hearing some T pronunciation ... usually at the start of
some sentences".

A word-initial consonant belongs to the first word and runs straight into
its vowel. A STRAY one is different in shape: a short burst, then a gap,
then the real speech starts. That gap is the tell, and it is measurable
without listening.

The prime suspect is the PERFORM tags, because they are the only thing
prepended to the spoken text - "[clear_throat] ", "[sigh] " and friends.
If Chatterbox is partially VOCALISING a tag rather than interpreting it,
the artefact lands exactly where the owner says it does: at the start, on
some lines and not others. So this splits the episode by tagged vs untagged
and compares.

  python scripts/vector/leading_burst.py b
"""
from __future__ import annotations

import math
import re
import struct
import sys
import wave
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DIRS = {"b": ("fairmarket_bubbles", "Bubbles"),
        "s": ("fairmarket_bshort", "BubblesShort"),
        "1": ("fairmarket", "FairMarketEp1")}
WIN = 0.01          # 10 ms - fine enough to see a plosive
LOOK = 0.60         # only the head of the line matters


def head_env(p: Path):
    with wave.open(str(p), "rb") as w:
        sr, ch = w.getframerate(), w.getnchannels()
        raw = w.readframes(int(sr * LOOK))
    d = struct.unpack("<%dh" % (len(raw) // 2), raw)
    if ch == 2:
        d = [(d[i] + d[i + 1]) / 2 for i in range(0, len(d) - 1, 2)]
    step = max(1, int(sr * WIN))
    return [math.sqrt(sum(x * x for x in d[i:i + step]) / step)
            for i in range(0, len(d) - step, step)]


def stray(env) -> tuple[bool, str]:
    """A burst, then a dip back near silence, then speech = stray onset."""
    if not env:
        return False, ""
    pk = max(env) or 1.0
    hi = [i for i, v in enumerate(env) if v > pk * 0.30]
    if not hi or hi[0] > 25:
        return False, ""
    first = hi[0]
    # find where that first burst ends
    end = first
    while end < len(env) and env[end] > pk * 0.18:
        end += 1
    # a real word-initial consonant does not stop; a stray one does
    gap = 0
    j = end
    while j < len(env) and env[j] < pk * 0.12:
        gap += 1
        j += 1
    burst = end - first
    if gap >= 4 and burst <= 12 and j < len(env):
        return True, "burst %dms, gap %dms, speech at %dms" % (
            burst * 10, gap * 10, j * 10)
    return False, ""


def main() -> None:
    ep = next((a for a in sys.argv[1:] if a in DIRS), "b")
    d, comp = DIRS[ep]
    src = (REPO / "remotion/src/compositions" / (comp + ".tsx")).read_text(
        "utf-8", errors="replace")
    stems = re.findall(r'vo: "([a-z_0-9]+)"', src)

    vo_src = (REPO / "scripts/vector/make_all_vo_local.py").read_text("utf-8")
    blk = vo_src[vo_src.index("PERFORM = {"):
                 vo_src.index("\n}", vo_src.index("PERFORM = {"))]
    tags = dict(re.findall(r'"([a-z_0-9]+)":\s*"\[([a-z_]+)\]', blk))

    hits = {"tagged": [], "untagged": []}
    for s in stems:
        p = REPO / "remotion/public/audio" / d / (s + ".wav")
        if not p.exists():
            continue
        bad, why = stray(head_env(p))
        key = "tagged" if s in tags else "untagged"
        if bad:
            hits[key].append((s, tags.get(s, "-"), why))

    tot_t = sum(1 for s in stems if s in tags)
    tot_u = len(stems) - tot_t
    print("%s: %d lines (%d tagged, %d untagged)" % (comp, len(stems), tot_t, tot_u))
    for k, n in (("tagged", tot_t), ("untagged", tot_u)):
        r = hits[k]
        print("\n  %-9s stray-onset on %d/%d (%d%%)"
              % (k, len(r), n, (len(r) * 100 // n) if n else 0))
        for s, tag, why in r[:12]:
            print("     %-24s [%s]  %s" % (s, tag, why))


if __name__ == "__main__":
    main()
