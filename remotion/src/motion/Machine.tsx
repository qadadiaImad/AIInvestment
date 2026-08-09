// THE MACHINE — two code-drawn diagrams that carry episode 3's whole thesis.
//
// These are code rather than generated art for the usual reason (the labels
// are words, and image models cannot draw words) and one more: they have to
// ASSEMBLE. The argument of the episode is that four ordinary parts only
// become a crash when they line up together, so the graphic has to show
// them arriving one at a time and only then turning as one. A still image
// of four icons asserts the conclusion; this one earns it.
//
// MachineParts is used twice — once while Sol names the four parts, and
// again at the turn where he says they were pointed the same way at once.
// Same component, different beat clock, so the second appearance is the
// same object remembered rather than a new graphic to decode.
import React from "react";

const INK = "#0A1020";
const PAPER = "#F4F1E6";
const AMBER = "#E8A33D";
const BURG = "#C0426A";
const TEAL = "#3FD2C7";

const ease = (t: number) => 1 - Math.pow(1 - Math.max(0, Math.min(1, t)), 3);
const clamp01 = (t: number) => Math.max(0, Math.min(1, t));

const PARTS = [
  {label: "CHEAP MONEY", sub: "borrowing costs almost nothing"},
  {label: "A STORY", sub: "a reason the price makes sense"},
  {label: "LEVERAGE", sub: "borrowed money on borrowed money"},
  {label: "SOMEONE SELLS", sub: "and they have no choice"},
];

/** A coin, a speech bubble, a stack and a down-arrow — drawn, not glyphs,
 *  so nothing here depends on a font shipping with the renderer. */
const Icon: React.FC<{i: number; s: number; on: number}> = ({i, s, on}) => {
  const c = on > 0.5 ? INK : "#9AA3B4";
  const st = {stroke: c, strokeWidth: 4, fill: "none",
    strokeLinecap: "round" as const, strokeLinejoin: "round" as const};
  return (
    <svg width={s} height={s} viewBox="0 0 48 48">
      {i === 0 ? (
        <>
          <circle cx="24" cy="24" r="15" {...st} />
          <path d="M24 14v20M19 19h8a4 4 0 010 8h-6a4 4 0 000 8h8" {...st} />
        </>
      ) : i === 1 ? (
        <path d="M8 12h32v22H26l-9 8v-8H8z" {...st} />
      ) : i === 2 ? (
        <>
          <rect x="10" y="30" width="28" height="8" {...st} />
          <rect x="14" y="20" width="20" height="8" {...st} />
          <rect x="18" y="10" width="12" height="8" {...st} />
        </>
      ) : (
        <path d="M24 10v24M14 26l10 10 10-10" {...st} />
      )}
    </svg>
  );
};

export const MachineParts: React.FC<{
  since: number; w: number; h: number;
}> = ({since, w, h}) => {
  const cw = w / 4;
  // Each part arrives 16 frames after the last; all four then pulse
  // together. The convergence used to start at frame 90 and take 24, which
  // the FIRST appearance (134 frames) reached and the second (102) did not
  // - so the reprise showed a half-faded conclusion. The last part is fully
  // in at 66, so the turn begins there.
  const together = clamp01((since - 70) / 18);
  // The belt sat at 60% of the panel and nothing lived under it, so the
  // graphic spent two fifths of the wall on empty paper. The stems below
  // it are not decoration filling that space: the episode's whole claim is
  // that four ordinary parts only matter when they point the same way at
  // once, and until now the graphic said "here are four parts" and left
  // the "at once" to the footer in 15px grey.
  const yBelt = h * 0.56;
  const yRail = yBelt + 68;
  const yJoin = yRail + 66;
  const hot = together > 0.3;
  const arrived = PARTS.filter((_, i) => ease((since - i * 16) / 18) > 0.5).length;
  return (
    <div style={{position: "absolute", inset: 0, background: PAPER,
      overflow: "hidden"}}>
      <div style={{position: "absolute", left: 30, top: 22,
        fontFamily: "Impact, Arial", fontSize: 34, letterSpacing: 1,
        color: INK}}>EVERY BUBBLE, THE SAME FOUR PARTS</div>

      {/* the belt they sit on, drawn left to right as the parts arrive */}
      <div style={{position: "absolute", left: 0, top: yBelt,
        height: 6, background: "#D8D2C0",
        width: w * ease(Math.min(1, since / 70))}} />

      <svg width={w} height={h} style={{position: "absolute", inset: 0,
        pointerEvents: "none"}}>
        {/* Each part feeds a common rail. Two earlier shapes were wrong for
            the same reason - they were ambiguous. Four curves ending in
            mid-air read as stray swooshes; four VERTICAL drops onto a rail
            read as a table, because the belt above and the rail below close
            them into boxes. Slanting them makes it a funnel, and a funnel
            is the claim: these four go to one place. */}
        {PARTS.map((p, i) => {
          const t = ease((since - i * 16) / 18);
          if (t <= 0) return null;
          const xi = (i + 0.5) * cw;
          const xe = w / 2 + (xi - w / 2) * 0.22;
          return (
            <line key={p.label} x1={xi} y1={yBelt + 8}
              x2={xi + (xe - xi) * t} y2={yBelt + 8 + (yRail - yBelt - 8) * t}
              opacity={0.9} stroke={hot ? BURG : "#9AA3B4"}
              strokeWidth={hot ? 5 : 3} strokeLinecap="round" />
          );
        })}
        {arrived > 1 ? (
          <line y1={yRail} y2={yRail}
            x1={w / 2 + (0.5 * cw - w / 2) * 0.22}
            x2={w / 2 + ((arrived - 0.5) * cw - w / 2) * 0.22}
            stroke={hot ? BURG : "#9AA3B4"} strokeWidth={hot ? 5 : 3}
            strokeLinecap="round" />
        ) : null}
        {together > 0.1 ? (
          <g opacity={clamp01((together - 0.1) / 0.25)}>
            <line x1={w / 2} x2={w / 2} y1={yRail} y2={yJoin}
              stroke={BURG} strokeWidth={6} strokeLinecap="round" />
            <path d={`M${w / 2 - 16},${yJoin - 16} l16,16 16,-16`} fill="none"
              stroke={BURG} strokeWidth={6} strokeLinecap="round"
              strokeLinejoin="round" />
            <text x={w / 2} y={yJoin + 62} textAnchor="middle" fill={BURG}
              fontFamily="Impact, Arial" fontSize={46} letterSpacing={2}>
              ALL FOUR, AT ONCE
            </text>
          </g>
        ) : null}
      </svg>

      {PARTS.map((p, i) => {
        const t = ease((since - i * 16) / 18);
        if (t <= 0) return null;
        const pulse = together > 0 ? 1 + Math.sin(since / 5 + i) * 0.03 * together : 1;
        return (
          <div key={p.label} style={{position: "absolute", left: i * cw,
            top: h * 0.17, width: cw, textAlign: "center",
            opacity: t, transform:
              `translateY(${(1 - t) * 26}px) scale(${pulse})`}}>
            <div style={{display: "flex", justifyContent: "center"}}>
              <Icon i={i} s={112} on={t} />
            </div>
            <div style={{fontFamily: "Impact, Arial", fontSize: 30,
              color: hot ? BURG : INK, marginTop: 8,
              letterSpacing: 0.5}}>{p.label}</div>
            <div style={{fontFamily: "Arial", fontSize: 16, color: "#6B7488",
              marginTop: 6, padding: "0 16px", lineHeight: 1.3}}>{p.sub}</div>
          </div>
        );
      })}

      <div style={{position: "absolute", left: 30, right: 30, bottom: 16,
        fontFamily: "Arial", fontSize: 15, color: "#6B7488",
        opacity: together}}>
        pointed the same direction, at the same time
      </div>
    </div>
  );
};

/** The loop that closes: borrow, price falls, lender wants cash, you sell
 *  into the fall — which pushes the price down again. Drawn as a ring so
 *  the viewer can see it has no exit. */
export const MachineLoop: React.FC<{
  since: number; w: number; h: number;
}> = ({since, w, h}) => {
  const cx = w / 2, cy = h * 0.56, R = Math.min(w, h) * 0.30;
  const STEPS = ["BORROW TO BUY", "THE PRICE DROPS",
                 "THE LENDER WANTS CASH", "YOU SELL INTO IT"];
  const t = ease(since / 64);
  const arc = 2 * Math.PI * R;
  return (
    <div style={{position: "absolute", inset: 0, background: PAPER,
      overflow: "hidden"}}>
      <div style={{position: "absolute", left: 30, top: 22,
        fontFamily: "Impact, Arial", fontSize: 34, letterSpacing: 1,
        color: INK}}>AND THEN IT CLOSES</div>
      <svg width={w} height={h} style={{position: "absolute", inset: 0}}>
        <circle cx={cx} cy={cy} r={R} fill="none" stroke={BURG}
          strokeWidth={5} strokeDasharray={arc}
          strokeDashoffset={(1 - t) * arc}
          transform={`rotate(-90 ${cx} ${cy})`} strokeLinecap="round" />
        {STEPS.map((s, i) => {
          const a = -Math.PI / 2 + (i / 4) * Math.PI * 2;
          const on = clamp01((t - i / 4) * 6);
          if (on <= 0) return null;
          const x = cx + Math.cos(a) * R, y = cy + Math.sin(a) * R;
          return (
            <g key={s} opacity={on}>
              <circle cx={x} cy={y} r={11} fill={PAPER} stroke={INK}
                strokeWidth={4} />
              <text x={x} y={y + (Math.sin(a) > 0.1 ? 42 : -24)}
                textAnchor="middle" fill={INK}
                fontFamily="Impact, Arial" fontSize={27}>{s}</text>
            </g>
          );
        })}
        {t > 0.98 ? (
          <text x={cx} y={cy + 10} textAnchor="middle" fill={TEAL}
            fontFamily="Impact, Arial" fontSize={40}
            opacity={clamp01((t - 0.98) * 50)}>NO EXIT</text>
        ) : null}
      </svg>
      <div style={{position: "absolute", left: 30, right: 30, bottom: 16,
        fontFamily: "Arial", fontSize: 15, color: "#6B7488"}}>
        forced selling pushes the price down, which forces more selling
      </div>
      <div style={{position: "absolute", right: 30, top: 26,
        fontFamily: "Arial", fontSize: 15, color: "#6B7488",
        opacity: 0.9}} />
      <span style={{display: "none"}}>{AMBER}</span>
    </div>
  );
};
