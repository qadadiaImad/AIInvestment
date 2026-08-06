// PeepTrader — the retail trader on the studio monitor, built from Open
// Peeps (Pablo Stanley, CC0 1.0, remixed via the DiceBear API; provenance in
// public/characters/peeps/provenance.json).
//
// WHY THIS EXISTS. Ep.5's whole argument is that the retail buyer and the
// market maker watch the same screen and the structure still decides. An
// abstract curve says it; a person watching that curve with a falling face
// SHOWS it. Open Peeps ships the same character in thirty expressions as
// separate CC0 vectors — an expression system with no generation, no
// identity risk and no legal review, which is exactly the gap our
// generated cast needed a whole inpainting pipeline to fill.
//
// The expression walks calm → concerned → fear as `progress` rises (the
// same 0..1 that drives the decay curve), so the face and the mechanism
// are ONE clock — the lesson of this week, applied on arrival.
import React from "react";
import {Img, staticFile} from "remotion";

const LADDER = ["calm", "serious", "concerned", "concernedFear", "fear"];

export const PeepTrader: React.FC<{
  /** 0..1 — how far along the decay this beat is */
  progress: number;
  x: number;
  y: number;
  size: number;
  /** small idle so he never reads as a still */
  f: number;
}> = ({progress, x, y, size, f}) => {
  const idx = Math.min(
    LADDER.length - 1,
    Math.floor(Math.max(0, Math.min(0.999, progress)) * LADDER.length),
  );
  const bob = Math.sin(f / 14) * size * 0.006;
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y + bob,
        width: size,
        height: size,
      }}
    >
      <Img
        src={staticFile(`characters/peeps/trader__${LADDER[idx]}.svg`)}
        style={{position: "absolute", inset: 0, width: "100%", height: "100%"}}
      />
    </div>
  );
};
