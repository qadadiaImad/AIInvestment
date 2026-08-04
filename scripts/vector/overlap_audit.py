"""Detect characters occluding each other, from real ink bounds.

Canvas bounds lie: every pose PNG has transparent padding, so two
drawings whose canvases overlap may not actually touch — and two whose
canvases look clear can still collide. This measures the INK bbox of each
pose, maps it through the exact staging maths the composition uses, and
reports the horizontal gap between the two figures in a beat.

Owner rule: no character may hide another.

Usage:  python -m vector.overlap_audit
"""
from __future__ import annotations

import json
from functools import lru_cache

import numpy as np
from PIL import Image

from vector.visemes_ep1 import RENDERS, FIX

W, H = 1080, 1920
FLOOR_Y = 1900
REX_H, SOL_H = 1430, 1165

# (beat, [(pose, kind, x, h), ...], label) — the two-shot beats only
BEATS = [
    (110,  [("rex_eager", "full", 327, 717),
            ("sol_point_v1", "full", 831, 629)], "REX asks SOL"),
    (195,  [("rex_skeptic", "full", 309, 710),
            ("sol_laugh", "full", 814, 622)], "SOL laughs"),
    (255,  [("rex_listen", "full", 236, 659),
            ("sol_finger", "full", 840, 578)], "politics 2-shot"),
    (895,  [("rex_eager", "full", 312, 679),
            ("sol_smug_v1", "bust", 812, 596)], "A2 copy"),
    (995,  [("rex_skeptic", "full", 298, 681),
            ("sol_finger", "full", 834, 597)], "A2 six weeks"),
    (1410, [("rex_listen", "full", 236, 659),
            ("sol_finger", "full", 840, 578)], "A2 map"),
    (1565, [("rex_eager", "full", 312, 679),
            ("sol_smug_v1", "bust", 812, 596)], "closer"),
]


@lru_cache(maxsize=64)
def ink_frac(pose: str) -> tuple[float, float]:
    """Ink left/right as a fraction of canvas width."""
    a = np.asarray(Image.open(
        RENDERS / f"_{pose}_rgba.png").convert("RGBA"))[..., 3]
    xs = np.nonzero((a > 0).any(axis=0))[0]
    w = a.shape[1]
    return float(xs.min()) / w, float(xs.max() + 1) / w


def screen_span(pose: str, kind: str, x: int, h: int, anchors: dict):
    d = anchors[pose]
    scale = (h / d["ink_h"]) if kind == "full" else (h / d["h"])
    w0 = d["w"] * scale
    left0 = x - d["anchor"][0] * w0 if kind == "full" else x - w0 / 2
    f0, f1 = ink_frac(pose)
    return left0 + f0 * w0, left0 + f1 * w0


def width_per_height(pose: str, kind: str, anchors: dict) -> float:
    """On-screen INK width for one px of staged height."""
    l, r = screen_span(pose, kind, 0, 1000, anchors)
    return (r - l) / 1000.0


def suggest(anchors: dict, margin: int = 44, gap: int = 78,
            rex_bias: float = 1.14) -> None:
    """Solve each two-shot for heights and x positions that fit.

    Two full figures must share 1080px. Widths are driven by height, so
    the only way both fit with a real gap is to stage the two-shot
    SMALLER than a solo — which is correct anyway: a two-shot is a wider
    shot. Rex keeps a height advantage (rex_bias) so he stays the taller
    of the two, per the owner's rule.
    """
    avail = W - 2 * margin - gap
    print("\nSUGGESTED two-shot staging (no overlap, both fully in frame):")
    for at, actors, label in BEATS:
        rex = next(a for a in actors if a[0].startswith("rex"))
        sol = next(a for a in actors if a[0].startswith("sol"))
        wr = width_per_height(rex[0], rex[1], anchors)
        ws = width_per_height(sol[0], sol[1], anchors)
        # solve: hr*wr + hs*ws = avail, with hr = rex_bias * hs
        hs = avail / (rex_bias * wr + ws)
        hr = rex_bias * hs
        rw, sw = hr * wr, hs * ws
        # place: rex left, sol right, equal margins
        rex_left, sol_left = margin, margin + rw + gap
        # convert an ink-left back to the actor x the composition wants
        def x_for(pose, kind, h, want_left):
            l, _ = screen_span(pose, kind, 0, h, anchors)
            return round(want_left - l)
        xr = x_for(rex[0], rex[1], hr, rex_left)
        xs = x_for(sol[0], sol[1], hs, sol_left)
        print(f"  beat {at:>4} {label:18s} "
              f"{rex[0]:>13s} x={xr:<5d} h={round(hr):<5d} (w {rw:.0f})   "
              f"{sol[0]:>13s} x={xs:<5d} h={round(hs):<5d} (w {sw:.0f})")


def main() -> None:
    anchors = json.loads((FIX / "pose_anchors.json").read_text("utf-8"))
    print(f"{'beat':>5} {'label':18s} {'left figure':>26s} "
          f"{'right figure':>26s} {'gap':>7s}")
    bad = 0
    for at, actors, label in BEATS:
        spans = [(p, *screen_span(p, k, x, h, anchors))
                 for p, k, x, h in actors]
        spans.sort(key=lambda s: s[1])
        (pa, la, ra), (pb, lb, rb) = spans
        gap = lb - ra
        flag = ""
        if gap < 0:
            bad += 1
            flag = f"  OVERLAP {-gap:.0f}px"
        elif gap < 30:
            flag = "  tight"
        print(f"{at:>5} {label:18s} {pa:>14s}[{la:5.0f},{ra:5.0f}] "
              f"{pb:>14s}[{lb:5.0f},{rb:5.0f}] {gap:7.0f}{flag}")
        for p, l, r in spans:
            if l < -20 or r > W + 20:
                print(f"        {p} runs off frame: [{l:.0f},{r:.0f}] "
                      f"vs 0..{W}")
    print(f"\n{bad}/{len(BEATS)} two-shots have one character occluding "
          f"the other")
    suggest(anchors)


if __name__ == "__main__":
    main()
