"""Make GRAPHICS holdable, as part of generating the composition.

This lived as a hand edit on Bubbles.tsx and was silently destroyed the
first time build_composition.py regenerated the file from ep.2 - which is
the whole hazard of generating a composition from another one. It is a
build step now, so it cannot be lost again.

WHAT IT FIXES. A beat with no wall content of its own holds what it is
reacting to. The ep.2 version only held image EXHIBITS, so a reaction beat
following a code-drawn PANEL fell through to the candlestick tape. In the
first cut of the Shorts version both "Fifteen YEARS?!" and "So who's the
villain?" followed a panel, so both cut back to the tape - reintroducing
exactly the repetition the previous two episodes spent their time removing.

Holding a panel just means letting its own clock keep running past the beat
that started it. Every panel here settles rather than loops, so it simply
stays on its final state.

  imported by build_composition.py
"""
from __future__ import annotations

OLD_FN_HEAD = "const heldExhibitAt = (i: number): {name: string; start: number} | null => {"

NEW_FN = '''type Held =
  | {kind: "exhibit"; name: string; start: number}
  | {kind: "graphic"; name: string; start: number};

// Holds GRAPHICS as well as exhibits - see scripts/bubbles/patch_hold.py
// for why the exhibit-only version was a bug, and why the RUN below is the
// second one.
const heldAt = (i: number): Held | null => {
  for (let k = i; k >= 0; k--) {
    const b = BEATS[k];
    if (b.exhibit)
      return {kind: "exhibit", name: b.exhibit, start: b.at + exhibitFromOf(b)};
    if (b.graphic) {
      // Walk back over an UNBROKEN RUN of the same graphic and report the
      // start of the run, not of this beat. Two consecutive beats naming
      // the same chart are one continuous shot of that chart; restarting
      // its clock wipes a line the viewer just watched draw and draws it
      // again from nothing.
      let j = k;
      while (j > 0) {
        const p = BEATS[j - 1];
        if (p.graphic === b.graphic) { j--; continue; }
        if (!p.graphic && !p.exhibit && p.wall !== "chart" && !p.card
            && !p.title) { j--; continue; }
        break;
      }
      return {kind: "graphic", name: b.graphic, start: BEATS[j].at};
    }
    if (b.wall === "chart" || b.card || b.title) return null;
  }
  return null;
};'''

OLD_WALLEX = '''  const wallEx = cur.exhibit
    ? {name: cur.exhibit, start: cur.at + exhibitFromOf(cur)}
    : cur.wall === "chart" ? null
    : heldExhibitAt(idx);'''

NEW_WALLEX = '''  const held = cur.wall === "chart" ? null : heldAt(idx);
  const wallEx = cur.exhibit
    ? {name: cur.exhibit, start: cur.at + exhibitFromOf(cur)}
    : held && held.kind === "exhibit" ? held : null;
  // The graphic actually on the wall, and the clock it runs on. BOTH come
  // from heldAt, which already covers this beat - the earlier version used
  // `cur.graphic ? since` here, so a beat that re-declared the graphic
  // already on screen reset it to frame zero.
  const gName = held && held.kind === "graphic" ? held.name : undefined;
  const gSince = held && held.kind === "graphic" ? frame - held.start : 0;'''


def apply(src: str) -> str:
    a = src.index(OLD_FN_HEAD)
    b = src.index("\n};", a) + 3
    src = src[:a] + NEW_FN + src[b:]

    assert OLD_WALLEX in src, "wallEx block not found - did ep.2 change?"
    src = src.replace(OLD_WALLEX, NEW_WALLEX, 1)

    # the graphic chain reads the effective graphic and its own clock
    for g in ("machine_parts", "machine_loop", "wealth"):
        src = src.replace('cur.graphic === "%s" ?' % g, 'gName === "%s" ?' % g)
    src = src.replace(
        ') : cur.graphic ? (\n              <SeriesExhibit name={cur.graphic as never}\n'
        '                since={since} w={WALL.w} h={WALL.h} />',
        ') : gName ? (\n              <SeriesExhibit name={gName as never}\n'
        '                since={gSince} w={WALL.w} h={WALL.h} />')
    for comp in ("MachineParts", "MachineLoop"):
        src = src.replace("<%s since={since} w={WALL.w} h={WALL.h} />" % comp,
                          "<%s since={gSince} w={WALL.w} h={WALL.h} />" % comp)
    src = src.replace("<BigNumberExhibit since={since} w={WALL.w} h={WALL.h}",
                      "<BigNumberExhibit since={gSince} w={WALL.w} h={WALL.h}")
    assert "heldExhibitAt" not in src
    return src
