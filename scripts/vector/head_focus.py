"""Emit each pose's head focus point for the composition's punch-ins.

Reframing a drawing is how a static asset yields more than one shot: a
wide and a punch-in are two shots of the same pixels, so the cut gains
rhythm with no second generation and therefore no identity drift. A
punch-in has to scale about the HEAD though, not the canvas centre, or
the face slides out of frame -- the eye ellipses measured for the blink
masks already give that point, in the same normalized space the
composition uses.
"""
from __future__ import annotations

import json

from vector.visemes_ep1 import VIS, FIX


def main() -> None:
    ov = json.loads((VIS / "anchor_overrides.json").read_text("utf-8"))
    out = {}
    for pose, a in ov.items():
        if pose.startswith("_"):
            continue
        e = a["eyes"]
        # a touch below the eyes centres the face, not the forehead
        out[pose] = {"fx": round(e["cx"], 4),
                     "fy": round(e["cy"] + 0.35 * e["ry"], 4)}
    p = FIX / "head_focus.json"
    p.write_text(json.dumps(out, indent=1), "utf-8")
    print(f"wrote {p} ({len(out)} poses)")
    for k, v in out.items():
        print(f"  {k:16s} fx={v['fx']:.3f} fy={v['fy']:.3f}")


if __name__ == "__main__":
    main()
