"""Measure the VOCAL TEXTURE of a script against episode 1.

The owner's note on episode 3: ep.1 worked because "voices often reflect
emotions and well pronounced HA! and other words, characters queued well
their sentences to express the mood" - and ep.3 is "a little bit boring and
not funny, doesn't have pace, something is missing".

That is a real and measurable difference, not a vibe. Episode 1's dialogue
carries markers the model can actually hear:

  * ALL-CAPS words   - Chatterbox stresses them
  * ellipses         - it pauses on them
  * exclamations     - they change the contour
  * SHORT lines      - one idea per breath, so the delivery has somewhere
                       to put emphasis; a 3-clause line flattens into
                       narration no matter how it is performed
  * PERFORM tags     - [sigh] / [gasp] / [whisper] / [clear_throat], the
                       only four measured to actually render

This prints those counts per episode so a rewrite can be checked against
the target instead of argued about.

  python scripts/vector/voice_texture.py
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LINE = re.compile(r'line: "((?:[^"\\]|\\.)*)"')
VO = re.compile(r'vo: "([a-z_0-9]+)"')

EPISODES = [
    ("EP1 (target)", "FairMarketEp1.tsx"),
    ("EP2", "FairMarketEp2.tsx"),
    ("BUBBLES", "Bubbles.tsx"),
]


def caps_words(line: str) -> list[str]:
    out = []
    for w in line.split():
        core = w.strip('.,!?"—-…')
        if len(core) > 2 and core.isupper():
            out.append(core)
    return out


def report(label: str, path: Path, perform: set[str]):
    src = path.read_text("utf-8", errors="replace")
    body = src[src.index("const BEATS"):]
    lines = LINE.findall(body)
    stems = VO.findall(body)
    n = len(lines) or 1
    words = [len(l.split()) for l in lines]
    caps = sum(len(caps_words(l)) for l in lines)
    ell = sum(l.count("…") + l.count("...") for l in lines)
    exc = sum(l.count("!") for l in lines)
    short = sum(1 for w in words if w <= 6)
    tagged = sum(1 for s in stems if s in perform)
    print(f"{label:14s} beats {n:3d} | avg {sum(words)/n:4.1f} w/line "
          f"| longest {max(words):3d} w | short(<=6w) {short*100//n:3d}%")
    print(f"{'':14s} CAPS {caps:3d} ({caps/n:4.2f}/beat) | ellipsis {ell:2d} "
          f"| '!' {exc:3d} | PERFORM tags {tagged:2d}/{n}")
    return dict(caps_per_beat=caps / n, short_pct=short * 100 // n,
                avg_words=sum(words) / n, tagged=tagged, n=n,
                longest=max(words))


def main() -> None:
    vo_src = (REPO / "scripts/vector/make_all_vo_local.py").read_text("utf-8")
    block = vo_src[vo_src.index("PERFORM = {"):vo_src.index("\n}", vo_src.index("PERFORM = {"))]
    perform = set(re.findall(r'"([a-z_0-9]+)":', block))

    res = {}
    for label, f in EPISODES:
        res[label] = report(label, REPO / "remotion/src/compositions" / f, perform)
        print()

    t, b = res["EP1 (target)"], res["BUBBLES"]
    print("GAP TO TARGET")
    print(f"  CAPS/beat     {b['caps_per_beat']:.2f} vs {t['caps_per_beat']:.2f}"
          f"  -> need {max(0, round((t['caps_per_beat']-b['caps_per_beat'])*b['n']))} more emphasised words")
    print(f"  short lines   {b['short_pct']}% vs {t['short_pct']}%")
    print(f"  avg words     {b['avg_words']:.1f} vs {t['avg_words']:.1f}")
    print(f"  longest line  {b['longest']} w vs {t['longest']} w")
    print(f"  PERFORM tags  {b['tagged']} vs {t['tagged']}")


if __name__ == "__main__":
    main()
