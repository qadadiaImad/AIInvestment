"""Convert an episode composition to the panel-desk format.

The six mechanical edits proved on ep.5, applied by script so the episodes
cannot drift apart: the giant wall replaces the monitor, the cast is seated
at fixed places on the round table, the authored punch-ins become SCENE
camera moves about the speaker's seat, the table and its curved crawl draw
over everything, and the captions get a scrim (the desk's rim is a curve, so
it crosses the caption zone at the wings wherever the text sits).

  python scripts/vector/_panelize.py 1
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

BACKDROP = '''        <Room dark={shot?.mood === "dark"} />
        {/* the painted studio plate over the flat room: generated anime
            background (provenance beside the file), cover-fit and dimmed so
            the drawn wall, cast and table sit ON it */}
        <Img src={staticFile("characters/cast_ep1/studio_bg.png")}
          style={{position: "absolute", inset: 0, width: "100%",
            height: "100%", objectFit: "cover",
            opacity: shot?.mood === "dark" ? 0.35 : 0.55,
            filter: "saturate(0.9) brightness(0.75)"}} />'''


def panelize(ep: str) -> None:
    p = REPO / f"remotion/src/compositions/FairMarketEp{ep}.tsx"
    s = p.read_text("utf-8")

    def sub(old: str, new: str, what: str) -> None:
        nonlocal s
        if old not in s:
            raise SystemExit(f"ep{ep}: MISS {what}")
        s = s.replace(old, new, 1)

    # 1 ── imports
    sub('import {FLOOR_Y, Room, TVFrame, TVGlass, TV_SCREEN, H as STAGE_H} from "../motion/Set";',
        'import {FLOOR_Y, NewsBand, PANEL_FLOOR, Room, RoundDesk, SEATS, '
        'WALL, WallFrame, H as STAGE_H} from "../motion/Set";',
        "imports")

    # 2 ── the monitor becomes the video wall
    sub('        <TVFrame glow={(!!cur.card || !!shot?.tvPose) && !shot?.hideCard} />\n'
        '        <div style={{position: "absolute", left: TV_SCREEN.x, top: TV_SCREEN.y,\n'
        '          width: TV_SCREEN.w, height: TV_SCREEN.h, overflow: "hidden",\n'
        '          borderRadius: 4}}>',
        '        <WallFrame glow={(!!cur.card || !!shot?.tvPose) && !shot?.hideCard} />\n'
        '        <div style={{position: "absolute", left: WALL.x, top: WALL.y,\n'
        '          width: WALL.w, height: WALL.h, overflow: "hidden",\n'
        '          borderRadius: 6}}>',
        "wall frame")
    s = s.replace("TV_SCREEN.w", "WALL.w").replace("TV_SCREEN.h", "WALL.h")

    # 3 ── glass over the wall
    sub("        <TVGlass />",
        '        <div style={{position: "absolute", left: WALL.x, top: WALL.y,\n'
        '          width: WALL.w, height: WALL.h, pointerEvents: "none",\n'
        '          background: "linear-gradient(118deg, rgba(255,255,255,0.08) 0%,"\n'
        '            + " rgba(255,255,255,0.02) 26%, rgba(255,255,255,0) 46%)",\n'
        '          boxShadow: "inset 0 0 90px rgba(0,0,0,0.5)"}} />',
        "wall glass")

    # 4 ── scene camera values
    sub("  const {shot, shotSince, shotLen} = shotAt(cur.shots, since, hold);",
        "  const {shot, shotSince, shotLen} = shotAt(cur.shots, since, hold);\n"
        "  // scene-camera values: the authored punch-ins become lens moves\n"
        "  // centred on the active speaker's seat\n"
        "  const camK0 = Math.min(1.3, shot?.k ?? 1);\n"
        "  const camK1 = shot?.kEnd === undefined ? camK0 : Math.min(1.3, shot.kEnd);\n"
        "  const camK = camK0 + (camK1 - camK0)\n"
        "    * Math.min(1, shotSince / Math.max(1, shotLen));\n"
        '  const camSeat = SEATS[(sub2 ? cur.speaker2 : cur.speaker) === "SOL"\n'
        '    ? "sol" : "rex"];\n'
        "  const camX = shot?.tx ?? camSeat.x;\n"
        "  const camY = Math.min(1420, shot?.ty ?? 1240);",
        "camera values")

    sub("      <div style={{position: \"absolute\", inset: 0,\n"
        "        transform: `translate(${k.x}px, ${k.y * 0.4}px) "
        "scale(${1 + 0.03 * Math.max(0, 1 - since / 10) * nrg})`,\n"
        '        transformOrigin: "50% 45%"}}>',
        "      {/* THE SCENE CAMERA. The panel holds still and the LENS does the\n"
        "          work, like a match-analysis broadcast: the per-beat k/kEnd\n"
        "          that used to punch into one drawing now zooms the whole\n"
        "          studio about the speaker's seat, desk and wall included. */}\n"
        "      <div style={{position: \"absolute\", inset: 0,\n"
        "        transform: `translate(${k.x}px, ${k.y * 0.4}px) `\n"
        "          + `scale(${(1 + 0.03 * Math.max(0, 1 - since / 10) * nrg) * camK})`,\n"
        "        transformOrigin: `${camX}px ${camY}px`}}>",
        "camera transform")

    # 5 ── seat the cast
    sub("          const other = visible.find(({j}) => j !== i)?.o;\n"
        "          return <Char key={i} a={a} since={since} frame={frame} "
        "speaking={speaking}",
        "          const other = visible.find(({j}) => j !== i)?.o;\n"
        "          // THE PANEL. Seats are fixed per character - a desk show's\n"
        "          // talent does not wander - and the beat's authored staging is\n"
        "          // overridden wholesale. The table, drawn over the actors,\n"
        "          // hides everything below the chest, which is what makes a\n"
        "          // standing drawing read as seated.\n"
        '          const seat = SEATS[isSol ? "sol" : "rex"];\n'
        '          const aSeat = {...a, kind: "full" as const, x: seat.x,\n'
        "                         y: PANEL_FLOOR, h: seat.h, moves: undefined,\n"
        "                         turns: undefined};\n"
        "          // the CAMERA zooms, the characters do not\n"
        "          const shotSeat = shot ? {...shot, k: 1, kEnd: undefined,\n"
        "                                   tx: undefined, ty: undefined} : shot;\n"
        "          return <Char key={i} a={aSeat} since={since} frame={frame} "
        "speaking={speaking}",
        "seating")
    sub("                       shot={shot} shotSince={shotSince} shotLen={shotLen}",
        "                       shot={shotSeat} shotSince={shotSince} shotLen={shotLen}",
        "shot pass-through")

    # 5b ── the painted studio plate behind everything
    sub('        <Room dark={shot?.mood === "dark"} />',
        BACKDROP, "studio backdrop")

    # 6 ── the table, over the cast
    sub("        {(cur.flicks ?? []).map((f, i) => (",
        '        <RoundDesk dark={shot?.mood === "dark"} />\n'
        "        {(cur.flicks ?? []).map((f, i) => (",
        "round desk")

    # 7 ── the curved crawl
    sub("      <Vignette strength={0.28} />",
        '      <NewsBand frame={frame} dark={shot?.mood === "dark"} />\n'
        "      <Vignette strength={0.28} />",
        "news band")

    # 8 ── captions: scrim + clear of the crawl
    sub('const Subtitle: React.FC<{speaker: string; line: string}> = '
        '({speaker, line}) => (\n'
        '  <div style={{position: "absolute", left: 60, right: 60, bottom: 90, '
        'textAlign: "center"}}>',
        'const Subtitle: React.FC<{speaker: string; line: string}> = '
        '({speaker, line}) => (\n'
        "  <>\n"
        "    {/* SCRIM. The desk's rim is a curve, so it crosses the caption\n"
        "        zone at the wings no matter where the text sits. */}\n"
        '    <div style={{position: "absolute", left: 0, right: 0, bottom: 150,\n'
        '      height: 300, pointerEvents: "none",\n'
        '      background: "linear-gradient(180deg, rgba(6,10,18,0) 0%,"\n'
        '        + " rgba(6,10,18,0.55) 34%, rgba(6,10,18,0.72) 70%,"\n'
        '        + " rgba(6,10,18,0.55) 100%)"}} />\n'
        '  <div style={{position: "absolute", left: 60, right: 60, bottom: 196, '
        'textAlign: "center"}}>',
        "subtitle scrim")
    sub("      {line}\n    </div>\n  </div>\n);",
        "      {line}\n    </div>\n  </div>\n  </>\n);",
        "subtitle close")

    # 9 ── the footer tucks under the crawl
    s = s.replace(
        '<div style={{position: "absolute", left: 0, right: 0, bottom: 20, '
        'textAlign: "center",\n          fontFamily: "Arial", fontSize: 22, '
        'color: "#6C7FA6"}}>',
        '<div style={{position: "absolute", left: 0, right: 0, bottom: 6, '
        'textAlign: "center",\n          fontFamily: "Arial", fontSize: 20, '
        'color: "#6C7FA6"}}>', 1)

    p.write_text(s, "utf-8")
    print(f"ep{ep}: panelized")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        panelize(a)
