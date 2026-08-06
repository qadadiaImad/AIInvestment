// RigAnatomy — what the rig actually IS, laid out flat.
//
// One drawing, one file: sol_point.svg, 162 vtracer paths. Every path carries
// its own transform="translate(x,y)", so each one has a real position on the
// canvas. Group them by that position and the drawing becomes a puppet.
//
// Left: the six groups, each re-emitted as its own SVG with the SAME header
// and viewBox — which is why they stay perfectly registered when stacked.
// The dot on each is its MEASURED pivot: the point where that part meets the
// body. Right: all six stacked back together = the original drawing, intact.
import React from "react";
import {AbsoluteFill, Img, staticFile} from "remotion";
import rigParts from "../fixtures/cast_ep1/rig_parts.json";
import {CharRig, type Rig} from "../motion/CharRig";

export const RIGANATOMY_FRAMES = 1;

const RIG = rigParts as unknown as Record<string, Rig>;
const POSE = "sol_point";

// The body ships as ONE piece of artwork and is drawn three times, each
// clipped to a different band, because vtracer emitted the whole silhouette
// as a single path and no amount of sorting can split one path.
const PARTS: {src: string; pivot: string; label: string; note: string}[] = [
  {src: "head", pivot: "head", label: "head", note: "78 paths - pivot: neck"},
  {src: "armL", pivot: "armL", label: "armL", note: "21 paths - pivot: L shoulder"},
  {src: "armR", pivot: "armR", label: "armR", note: "5 paths - pivot: R shoulder"},
  {src: "body", pivot: "torso", label: "body -> torso", note: "clipped above the cut"},
  {src: "body", pivot: "legL", label: "body -> foot L", note: "clipped below, left"},
  {src: "body", pivot: "legR", label: "body -> foot R", note: "clipped below, right"},
];

export const RigAnatomy: React.FC = () => {
  const rig = RIG[POSE];
  if (!rig) return <AbsoluteFill style={{background: "#fff"}} />;
  const cellH = 300;
  const cellW = cellH * (rig.w / rig.h);

  return (
    <AbsoluteFill style={{background: "#F4F6FA", fontFamily: "Arial"}}>
      <div
        style={{
          position: "absolute",
          top: 22,
          left: 40,
          fontFamily: "Impact, Arial",
          fontSize: 34,
          letterSpacing: 1,
          color: "#16203A",
        }}
      >
        sol_point.svg — 162 paths → 4 artworks, drawn as 6 independent pieces
      </div>

      {PARTS.map((p, i) => {
        const src = rig.parts[p.src];
        const [px, py] = rig.pivots[p.pivot] ?? [0.5, 0.5];
        const cut = rig.legCut ?? 0.9;
        const fm = rig.footMid ?? 0.5;
        const pcv = (v: number) => `${(v * 100).toFixed(2)}%`;
        const clip =
          p.label === "body -> torso"
            ? `inset(0% 0% ${pcv(1 - (cut + 0.075))} 0%)`
            : p.label === "body -> foot L"
              ? `inset(${pcv(cut)} ${pcv(1 - fm)} 0% 0%)`
              : p.label === "body -> foot R"
                ? `inset(${pcv(cut)} 0% 0% ${pcv(fm)})`
                : undefined;
        const x = 60 + (i % 3) * (cellW + 40);
        const y = 90 + Math.floor(i / 3) * (cellH + 74);
        return (
          <div key={p.label} style={{position: "absolute", left: x, top: y}}>
            <div
              style={{
                position: "relative",
                width: cellW,
                height: cellH,
                background: "#fff",
                border: "1px solid #C9D3E2",
                borderRadius: 6,
              }}
            >
              {src ? (
                <div style={{position: "absolute", inset: 0, clipPath: clip}}>
                  <Img
                    src={staticFile(src)}
                    style={{
                      position: "absolute",
                      inset: 0,
                      width: "100%",
                      height: "100%",
                    }}
                  />
                </div>
              ) : null}
              {/* the measured pivot — this is what the part rotates about */}
              <div
                style={{
                  position: "absolute",
                  left: px * cellW - 7,
                  top: py * cellH - 7,
                  width: 14,
                  height: 14,
                  borderRadius: 7,
                  background: "#E5484D",
                  border: "2px solid #fff",
                  boxShadow: "0 0 0 1px #E5484D",
                }}
              />
            </div>
            <div style={{fontSize: 17, color: "#16203A", marginTop: 7}}>
              <b>{p.label}</b>
            </div>
            <div style={{fontSize: 15, color: "#7A879B"}}>
              {p.note} ({px.toFixed(3)}, {py.toFixed(3)})
            </div>
          </div>
        );
      })}

      {/* stacked back together, with one turn applied so the z-order swap is
          visible: the far arm has gone behind the torso */}
      {[
        {label: "STACKED — turn 0 (the original drawing)", turn: 0},
        {label: "STACKED — turn 45°, far arm behind torso", turn: 1},
      ].map((s, i) => (
        <div
          key={s.label}
          style={{position: "absolute", right: 70 + (1 - i) * 430, top: 130}}
        >
          <div
            style={{
              position: "relative",
              width: 420 * (rig.w / rig.h),
              height: 420,
              background: "#fff",
              border: "1px solid #C9D3E2",
              borderRadius: 6,
            }}
          >
            <CharRig rig={rig} pose={{turn: s.turn}} />
          </div>
          <div style={{fontSize: 16, color: "#16203A", marginTop: 8, width: 300}}>
            {s.label}
          </div>
        </div>
      ))}

      <div
        style={{
          position: "absolute",
          left: 60,
          bottom: 26,
          fontSize: 17,
          color: "#65748C",
          lineHeight: 1.5,
        }}
      >
        vtracer emitted the whole silhouette as ONE path (97% of the frame), so
        legs cannot be sorted out of it. Instead the body artwork is drawn three
        times, each clipped to a different band and transformed on its own; the
        torso draw overlaps the cut so the straight edge never shows. Motion =
        per-frame rotate/translate/scale about the red dots. Nothing generated.
      </div>
    </AbsoluteFill>
  );
};
