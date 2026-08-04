"""Verify the staging of every beat against the composition ITSELF.

Three owner rules, all of them invisible in a typecheck and all of them
shipped at least once before being caught by eye:

  1. no character may hide another
  2. nothing may hide the evidence — an actor may not cover the monitor
     on a shot that is showing an exhibit
  3. no figure may run off the frame edge

`overlap_audit.py` checked rule 1 from a HAND-COPIED beat list, which is
a second source of truth that silently goes stale — its FLOOR_Y still
says 1900 while the set moved to 1730. This parses the real BEATS array
out of FairMarketEp1.tsx, so it cannot drift from what renders.

Measurements use each pose's INK bbox, not its canvas: every drawing has
transparent padding, so canvas bounds both miss real collisions and
invent fake ones.

Usage:  python -m vector.stage_audit
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from vector.visemes_ep1 import RENDERS, FIX

REPO = Path(__file__).resolve().parent.parent.parent
COMP = REPO / "remotion" / "src" / "compositions" / "FairMarketEp1.tsx"

W, H = 1080, 1920
FLOOR_Y = 1730
TOTAL_FRAMES = 3600
VO_DELAY = 6
VO_DIR = REPO / "remotion" / "public" / "audio" / "fairmarket"
FFPROBE = (REPO / "remotion" / "node_modules" / "@remotion"
           / "compositor-win32-x64-msvc" / "ffprobe.exe")


@lru_cache(maxsize=64)
def vo_frames(stem: str) -> int:
    """Length of a VO track in frames. Decoded with ffprobe rather than
    read from the WAV header — some generators write a placeholder header
    that reports 44,739 seconds."""
    import subprocess
    p = VO_DIR / f"{stem}.wav"
    if not p.exists():
        return 0
    out = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True).stdout.strip()
    return int(round(float(out) * 30)) if out else 0
TV = {"x": 108, "y": 250, "w": 864, "h": 486}
TV_BOX = (TV["x"], TV["y"], TV["x"] + TV["w"], TV["y"] + TV["h"])
MAX_K = 1.9


@lru_cache(maxsize=128)
def ink_box(pose: str) -> tuple[float, float, float, float]:
    """Ink bounds as fractions of canvas (l, t, r, b)."""
    p = RENDERS / f"_{pose}_rgba.png"
    if not p.exists():
        return 0.0, 0.0, 1.0, 1.0
    a = np.asarray(Image.open(p).convert("RGBA"))[..., 3]
    ys, xs = np.nonzero(a > 0)
    h, w = a.shape
    return (float(xs.min()) / w, float(ys.min()) / h,
            float(xs.max() + 1) / w, float(ys.max() + 1) / h)


def parse_beats(src: str) -> list[dict]:
    """Pull the BEATS array out of the TSX. The literals are regular
    enough for this; anything it cannot read it reports rather than
    silently skipping."""
    # NB: index("[") after the declaration finds the `[]` in `Beat[]`, not
    # the array — which silently yielded an empty body and a PASSING audit
    # over zero beats. Anchor on the assignment instead.
    start = src.index("const BEATS: Beat[] = [")
    i = src.index("= [", start) + 2
    depth = 0
    body = ""
    for j in range(i, len(src)):
        if src[j] == "[":
            depth += 1
        elif src[j] == "]":
            depth -= 1
            if depth == 0:
                body = src[i + 1:j]
                break
    # Comments carry unbalanced brackets and apostrophes; drop them before
    # counting depth.
    body = re.sub(r"//[^\n]*", "", body)
    # split top-level beat objects (braces/brackets only — parens appear
    # unbalanced inside prose)
    beats, depth, cur = [], 0, ""
    for ch in body:
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
        actors = []
        for m in re.finditer(
                r'poses:\s*\["([a-z0-9_]+)"\][^}]*?kind:\s*"(\w+)"[^}]*?'
                r'x:\s*(-?\d+)[^}]*?y:\s*([A-Z_]+|-?\d+)[^}]*?h:\s*(\d+)', b):
            pose, kind, x, y, h = m.groups()
            actors.append({"pose": pose, "kind": kind, "x": int(x),
                           "y": FLOOR_Y if y == "FLOOR_Y" else int(y),
                           "h": int(h)})
        shots = []
        sm = re.search(r"shots:\s*\[(.*?)\],?\s*(?:\n\s*(?:vo|sfx|card|graphic|flicks|holdMouth|fx|title)\b|$)",
                       b, re.S)
        if sm:
            for s in re.finditer(r"\{([^{}]*)\}", sm.group(1)):
                t = s.group(1)
                g = lambda k, d=None: (
                    float(re.search(rf"\b{k}:\s*([\d.]+)", t).group(1))
                    if re.search(rf"\b{k}:\s*([\d.]+)", t) else d)
                shots.append({
                    "from": int(g("from", 0)), "k": g("k", 1.0),
                    "kEnd": g("kEnd"),
                    "only": (int(g("only")) if g("only") is not None else None),
                    "hideCard": "hideCard: true" in t,
                    "tvPose": bool(re.search(r'tvPose:\s*"', t)),
                })
        gm = re.search(r'\bgraphic:\s*"([a-z0-9_]+)"', b)
        vo = re.search(r'\bvo:\s*"([a-z0-9_]+)"', b)
        vo2 = re.search(r'\bvo2:\s*"([a-z0-9_]+)"', b)
        at2 = re.search(r"\bat2:\s*(\d+)", b)
        out.append({
            "at": int(at.group(1)), "actors": actors, "shots": shots,
            "graphic": gm.group(1) if gm else None,
            "vo": vo.group(1) if vo else None,
            "vo2": vo2.group(1) if vo2 else None,
            "at2": int(at2.group(1)) if at2 else 0,
            "exhibit": bool(re.search(r"\b(card|graphic):", b)),
        })
    # each beat's own length is the gap to the next one
    for i, b in enumerate(out):
        b["hold"] = (out[i + 1]["at"] - b["at"]) if i + 1 < len(out) else 200
    return out


def box(actor: dict, k: float, anchors: dict) -> tuple[float, float, float, float]:
    """On-screen INK box for an actor at reframe factor k, using the same
    maths the composition uses (scale by ink height for `full`, by canvas
    height otherwise; reframe about the head focus point)."""
    d = anchors[actor["pose"]]
    kind, h = actor["kind"], actor["h"]
    scale = (h / d["ink_h"]) if kind == "full" else (h / d["h"])
    w0, h0 = d["w"] * scale, d["h"] * scale
    left0 = (actor["x"] - d["anchor"][0] * w0 if kind == "full"
             else actor["x"] - w0 / 2)
    top0 = (actor["y"] - d["anchor"][1] * h0 if kind == "full"
            else actor["y"] - h0 / 2)
    hf = HF.get(actor["pose"], {"fx": 0.5, "fy": 0.32})
    k = min(k, MAX_K)
    hx, hy = left0 + hf["fx"] * w0, top0 + hf["fy"] * h0
    left, top = hx - hf["fx"] * w0 * k, hy - hf["fy"] * h0 * k
    il, it, ir, ib = ink_box(actor["pose"])
    return (left + il * w0 * k, top + it * h0 * k,
            left + ir * w0 * k, top + ib * h0 * k)


def overlaps(a, b) -> float:
    ox = min(a[2], b[2]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[1], b[1])
    return min(ox, oy) if ox > 0 and oy > 0 else 0.0


HF: dict = {}


def main() -> None:
    global HF
    anchors = json.loads((FIX / "pose_anchors.json").read_text("utf-8"))
    HF = json.loads((FIX / "head_focus.json").read_text("utf-8"))
    beats = parse_beats(COMP.read_text("utf-8"))
    if len(beats) < 5:
        raise SystemExit(f"parsed only {len(beats)} beats - the parser is "
                         f"broken, not the staging. A pass over zero beats "
                         f"is the failure this tool exists to prevent.")
    bad_pair = bad_tv = bad_edge = 0
    print(f"{len(beats)} beats parsed from {COMP.name}\n")
    for b in beats:
        shots = b["shots"] or [{"from": 0, "k": 1.0, "kEnd": None,
                                "only": None, "hideCard": False,
                                "tvPose": False}]
        for si, s in enumerate(shots):
            ks = [s["k"]] + ([s["kEnd"]] if s["kEnd"] else [])
            vis = ([b["actors"][s["only"]]]
                   if s["only"] is not None and s["only"] < len(b["actors"])
                   else b["actors"])
            for k in ks:
                boxes = [(a["pose"], box(a, k, anchors)) for a in vis]
                for i in range(len(boxes)):
                    for j in range(i + 1, len(boxes)):
                        ov = overlaps(boxes[i][1], boxes[j][1])
                        if ov > 0:
                            bad_pair += 1
                            print(f"  OCCLUSION  beat {b['at']:4d} shot {si} "
                                  f"k={k:.2f}  {boxes[i][0]} x {boxes[j][0]} "
                                  f"overlap {ov:.0f}px")
                showing = (b["exhibit"] or s["tvPose"]) and not s["hideCard"]
                # A TWO-SHOT must contain both figures — that is the whole
                # point of framing it wide. A SOLO push-in is allowed to
                # crop at the edges (that is what a push-in IS); what must
                # not happen there is losing the face, so the test on a
                # solo shot is on the head point, not the silhouette.
                solo = len(boxes) == 1
                if solo:
                    a = vis[0]
                    hf = HF.get(a["pose"], {"fx": 0.5, "fy": 0.32})
                    bx = boxes[0][1]
                    hx = bx[0] + (hf["fx"] - ink_box(a["pose"])[0]) * (
                        bx[2] - bx[0]) / max(1e-6, ink_box(a["pose"])[2]
                                             - ink_box(a["pose"])[0])
                    hy = bx[1] + hf["fy"] * (bx[3] - bx[1])
                    if not (60 <= hx <= W - 60 and 40 <= hy <= H * 0.85):
                        bad_edge += 1
                        print(f"  FACE OUT   beat {b['at']:4d} shot {si} "
                              f"k={k:.2f}  {boxes[0][0]} head at "
                              f"({hx:.0f},{hy:.0f})")
                for pose, bx in boxes:
                    if showing:
                        ov = overlaps(bx, TV_BOX)
                        if ov > 0:
                            bad_tv += 1
                            print(f"  COVERS TV  beat {b['at']:4d} shot {si} "
                                  f"k={k:.2f}  {pose} over the exhibit by "
                                  f"{ov:.0f}px")
                    if not solo and (bx[0] < -20 or bx[2] > W + 20):
                        bad_edge += 1
                        print(f"  OFF FRAME  beat {b['at']:4d} shot {si} "
                              f"k={k:.2f}  {pose} spans "
                              f"{bx[0]:.0f}..{bx[2]:.0f} of 0..{W}")
    # RULE 4: an exhibit must FINISH BUILDING while it is still on screen.
    # The timeline graphic shipped once running to frame 116 inside a beat
    # that cut away at 58 — the gap bracket and the share counter, which
    # ARE the payoff, were never once visible. These animations run on the
    # BEAT clock (`since`), not the shot clock, so what matters is the last
    # frame at which the exhibit is still un-hidden.
    completes = {"timeline_nvidia": 70, "counter_45days": 58,
                 "perf_2024": 64, "card": 60}
    bad_build = 0
    for b in beats:
        kind = b.get("graphic") or ("card" if b["exhibit"] else None)
        if not kind:
            continue
        need = completes.get(kind, 60)
        shots = b["shots"] or [{"from": 0, "hideCard": False}]
        visible_until = b["hold"]
        for i, sh in enumerate(shots):
            if sh["hideCard"] and all(x["hideCard"] for x in shots[i:]):
                visible_until = sh["from"]
                break
        if visible_until < need:
            bad_build += 1
            print(f"  UNFINISHED beat {b['at']:4d}  {kind} needs {need}f to "
                  f"build but is visible for only {visible_until}f")

    # RULE 5: NOBODY INTERRUPTS ANYBODY. A beat shorter than its own line
    # does not truncate the audio — the <Audio> keeps playing while the
    # NEXT beat starts its line over the top, so one character talks over
    # the other. Shipped once at the end of the episode: Sol's closing
    # advice needed 137 frames, had 110, and Rex's "read the filings!"
    # landed 27 frames early on top of him.
    bad_vo = 0
    for i, b in enumerate(beats):
        nxt = beats[i + 1]["at"] if i + 1 < len(beats) else TOTAL_FRAMES
        ln = nxt - b["at"]
        need = 0
        if b.get("vo"):
            need = max(need, VO_DELAY + vo_frames(b["vo"]))
        if b.get("vo2"):
            need = max(need, b.get("at2", 0) + VO_DELAY + vo_frames(b["vo2"]))
        if need > ln:
            bad_vo += 1
            print(f"  INTERRUPTED beat {b['at']:4d}  '{b.get('vo')}' needs "
                  f"{need}f but the next beat starts after {ln}f "
                  f"(talks over by {need - ln}f)")

    print(f"\nocclusions {bad_pair} · exhibit covered {bad_tv} · "
          f"off-frame {bad_edge} · unfinished exhibits {bad_build} · "
          f"interrupted lines {bad_vo}")
    if bad_pair or bad_tv or bad_edge or bad_build or bad_vo:
        raise SystemExit(1)
    print("staging clean")


if __name__ == "__main__":
    main()
