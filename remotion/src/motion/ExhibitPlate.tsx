// ExhibitPlate — a generated caricature, ANIMATED, on the video wall.
//
// WHY THIS EXISTS. The wall only ever carried charts and text cards, and
// the owner's note was that a chart cannot explain what Sol is SAYING:
// "add caricatures portraying politicians and big corpo shaking hands and
// combining political and economic ambitions". A candlestick cannot show a
// bargain being struck.
//
// WHY IT MOVES RATHER THAN CUTS. A still image on a screen behind two
// talking characters reads as a slideshow - the exact note the owner gave
// about the cast months ago, and it is just as true of the wall. So every
// plate is given the same four things a broadcast graphics package gives
// its stills:
//
//   * a PUSH that never stops (slow, sub-perceptual scale + drift, so the
//     frame is alive even when nothing is happening);
//   * an ENTRANCE wipe that reveals the artwork rather than fading it,
//     because a fade reads as a transition and a wipe reads as an
//     assertion;
//   * a SPOTLIGHT that ramps up under the entrance, so the plate appears
//     to be lit rather than switched on;
//   * an optional CALLOUT ring that draws itself around one point of the
//     picture on a delay - the "look here" beat that lands on the word.
//
// All of it is a pure function of the beat clock (`since`), so it is
// deterministic and re-renders identically.
import React from "react";
import {Img, staticFile} from "remotion";

const ease = (t: number) => 1 - Math.pow(1 - Math.max(0, Math.min(1, t)), 3);

export type Callout = {
  /** 0..1 of the plate's width / height */
  x: number;
  y: number;
  /** beat frame at which the ring starts drawing */
  at?: number;
  label?: string;
};

export const ExhibitPlate: React.FC<{
  /** file stem in public/characters/cast_ep1/exhibits */
  name: string;
  /** frames since the beat started */
  since: number;
  w: number;
  h: number;
  callout?: Callout;
  /** push direction, so consecutive plates do not drift identically */
  dir?: 1 | -1;
}> = ({name, since, w, h, callout, dir = 1}) => {
  // ENTRANCE. 18 frames, wipe from the left, artwork already at full
  // opacity behind it — the picture is uncovered, not faded up.
  const wipe = ease(since / 18);
  // THE PUSH never finishes. 1.0 -> 1.06 over 12s and still creeping at
  // the cut; a push that lands makes the rest of the beat feel frozen.
  const k = 1 + 0.06 * Math.min(1, since / 360);
  const dx = dir * 14 * Math.min(1, since / 360);
  // the light comes up just behind the wipe
  const lit = ease((since - 4) / 26);

  const cal = callout && since >= (callout.at ?? 26);
  const calT = cal ? ease((since - (callout.at ?? 26)) / 16) : 0;
  const R = Math.min(w, h) * 0.17;

  return (
    <div style={{position: "absolute", inset: 0, overflow: "hidden",
      background: "#070C16"}}>
      <div style={{position: "absolute", inset: 0,
        transform: `scale(${k}) translateX(${dx}px)`,
        transformOrigin: "50% 50%",
        clipPath: `inset(0 ${(1 - wipe) * 100}% 0 0)`,
        filter: `brightness(${0.55 + 0.45 * lit}) saturate(${0.8 + 0.2 * lit})`}}>
        <Img src={staticFile(`characters/cast_ep1/exhibits/${name}.png`)}
          style={{position: "absolute", inset: 0, width: "100%",
            height: "100%", objectFit: "cover"}} />
      </div>

      {/* the leading edge of the wipe, so the reveal has a hard light on it */}
      {wipe < 1 ? (
        <div style={{position: "absolute", top: 0, bottom: 0,
          left: `${wipe * 100}%`, width: 3,
          background: "rgba(140,230,175,0.85)",
          boxShadow: "0 0 26px rgba(120,224,158,0.75)"}} />
      ) : null}

      {/* CALLOUT. Draws itself with strokeDashoffset so the ring is seen
          being placed; a ring that simply appears reads as a UI element. */}
      {cal ? (
        <svg width={w} height={h} style={{position: "absolute", inset: 0}}>
          <circle cx={callout!.x * w} cy={callout!.y * h} r={R}
            fill="none" stroke="#7CE0A2" strokeWidth={4}
            strokeDasharray={2 * Math.PI * R}
            strokeDashoffset={(1 - calT) * 2 * Math.PI * R}
            opacity={0.9} />
        </svg>
      ) : null}

      {/* CALLOUT LABEL, on its own dark plate. It used to be bare SVG text
          in pale mint, which is invisible the moment the artwork behind it
          is light — "45 DAYS" over the cream calendar was unreadable. It is
          HTML rather than <text> so the plate sizes itself to the string
          instead of guessing Impact's metrics, and it flips below the ring
          when there is no room above it. */}
      {cal && callout!.label ? (() => {
        const above = callout!.y * h - R - 14;
        const below = callout!.y * h + R + 14;
        const flip = above < 46;
        return (
          <div style={{position: "absolute",
            left: callout!.x * w, top: flip ? below : above,
            transform: `translate(-50%, ${flip ? "0%" : "-100%"})`,
            padding: "3px 12px 5px", borderRadius: 4,
            background: "rgba(6,10,18,0.9)",
            border: "2px solid rgba(124,224,162,0.85)",
            boxShadow: "0 6px 18px rgba(0,0,0,0.5)",
            color: "#CFF6DF", fontFamily: "Impact, Arial",
            fontSize: 30, lineHeight: 1.05, letterSpacing: 0.5,
            whiteSpace: "nowrap", opacity: calT}}>
            {callout!.label}
          </div>
        );
      })() : null}

      {/* a soft vignette so the plate sits INSIDE the wall rather than
          looking like a browser window pasted onto it */}
      <div style={{position: "absolute", inset: 0, pointerEvents: "none",
        boxShadow: "inset 0 0 120px rgba(0,0,0,0.62)"}} />
    </div>
  );
};
