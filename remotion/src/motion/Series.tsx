// SERIES EXHIBIT — draws a real FRED series as a line that builds.
//
// Every other code-drawn exhibit in this series takes its numbers as props
// typed into the composition. That was fine for a single figure; this
// episode needs five time series, and typing 100 points by hand is exactly
// where invented numbers creep in. So this reads the fixture written by
// scripts/bubbles/build_series.py, which pulls FRED and computes the marked
// points FROM the data — if a series is revised, the callouts move with it.
//
// The line DRAWS rather than fades: a chart that appears has no argument in
// it, a chart that is still being drawn makes the viewer wait for where it
// goes. The marks land only once the line has reached them, so a callout
// can never announce a fall before the fall is on screen — the audio
// equivalent of that rule cost this repo a re-render once already.
import React from "react";
import series from "../fixtures/bubbles/series.json";

type Pt = [string, number];
type Mark = {at: string; v: number; label: string};
export type SeriesKey = keyof typeof series;

const INK = "#0A1020";
const AMBER = "#E8A33D";
const TEAL = "#3FD2C7";
const BURG = "#C0426A";
const PAPER = "#F4F1E6";

const ease = (t: number) => 1 - Math.pow(1 - Math.max(0, Math.min(1, t)), 3);

export const SeriesExhibit: React.FC<{
  name: SeriesKey; since: number; w: number; h: number;
  /** frames the line takes to draw itself */
  draw?: number;
  /** highlight the fall in burgundy once the line passes its peak */
  fallTone?: boolean;
}> = ({name, since, w, h, draw = 70, fallTone = true}) => {
  // JSON widens [string, number] to (string|number)[], so the fixture is
  // read through `unknown` and the pairs are narrowed once, here, rather
  // than every component pretending the tuple survived the import.
  const raw = series[name] as unknown as {
    title: string; foot: string; unit: string;
    points: (string | number)[][]; marks?: Mark[];
    band?: {hi: number; label: string};
    span?: {a: string; b: string; label: string};
  };
  const s = {...raw,
    points: raw.points.map((p) => [String(p[0]), Number(p[1])] as Pt)};

  const PAD = {l: 78, r: 34, t: 74, b: 62};
  const iw = w - PAD.l - PAD.r, ih = h - PAD.t - PAD.b;
  const xs = s.points.map((p) => Date.parse(p[0]));
  const ys = s.points.map((p) => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  const lo = Math.min(...ys), hi = Math.max(...ys);
  // a flat 6% of range as headroom, so a peak never touches the frame edge
  const pad = (hi - lo) * 0.06 || 1;
  const px = (t: number) => PAD.l + ((t - x0) / (x1 - x0 || 1)) * iw;
  const py = (v: number) =>
    PAD.t + ih - ((v - (lo - pad)) / ((hi + pad) - (lo - pad))) * ih;

  const t = ease(since / draw);
  const shown = Math.max(2, Math.round(t * s.points.length));
  const pts = s.points.slice(0, shown);
  const peakI = ys.indexOf(hi);

  const path = pts.map((p, i) =>
    `${i ? "L" : "M"}${px(Date.parse(p[0])).toFixed(1)},${py(p[1]).toFixed(1)}`
  ).join(" ");
  // the post-peak leg, drawn in burgundy so the fall reads as the event
  const fall = fallTone && shown > peakI + 1
    ? s.points.slice(peakI, shown).map((p, i) =>
        `${i ? "L" : "M"}${px(Date.parse(p[0])).toFixed(1)},${py(p[1]).toFixed(1)}`
      ).join(" ")
    : "";

  const head = pts[pts.length - 1];

  return (
    <div style={{position: "absolute", inset: 0, background: PAPER,
      overflow: "hidden"}}>
      <svg width={w} height={h} style={{position: "absolute", inset: 0}}>
        {/* the band: the stretch of a rate series that sat below a level */}
        {s.band ? (
          <g opacity={Math.min(1, Math.max(0, (since - 24) / 16))}>
            <rect x={PAD.l} y={py(s.band.hi)} width={iw}
              height={Math.max(0, PAD.t + ih - py(s.band.hi))}
              fill={AMBER} opacity={0.16} />
            <line x1={PAD.l} x2={PAD.l + iw} y1={py(s.band.hi)} y2={py(s.band.hi)}
              stroke={AMBER} strokeWidth={2} strokeDasharray="7 6" />
            <text x={PAD.l + 12} y={py(s.band.hi) + 26} fill="#8A6A2A"
              fontFamily="Arial" fontWeight={700} fontSize={19}
              letterSpacing={1}>{s.band.label}</text>
          </g>
        ) : null}

        {/* baseline + frame */}
        <line x1={PAD.l} x2={PAD.l + iw} y1={PAD.t + ih} y2={PAD.t + ih}
          stroke="#3A4358" strokeWidth={2} />

        <path d={path} fill="none" stroke={INK} strokeWidth={4}
          strokeLinejoin="round" strokeLinecap="round" />
        {fall ? (
          <path d={fall} fill="none" stroke={BURG} strokeWidth={5}
            strokeLinejoin="round" strokeLinecap="round" />
        ) : null}

        {/* the live head of the line, so the eye has something to follow */}
        {head && t < 1 ? (
          <circle cx={px(Date.parse(head[0]))} cy={py(head[1])} r={7}
            fill={AMBER} stroke={INK} strokeWidth={3} />
        ) : null}

        {/* marks appear only once the line has actually reached them */}
        {(s.marks ?? []).map((m) => {
          const reached = pts.length > 0 &&
            Date.parse(pts[pts.length - 1][0]) >= Date.parse(m.at);
          if (!reached) return null;
          const mx = px(Date.parse(m.at)), my = py(m.v);
          const below = my < PAD.t + ih * 0.45;
          return (
            <g key={m.at}>
              <circle cx={mx} cy={my} r={8} fill={PAPER}
                stroke={BURG} strokeWidth={4} />
              <text x={Math.min(w - 96, Math.max(PAD.l, mx))}
                y={below ? my + 40 : my - 20}
                textAnchor="middle" fill={INK} fontFamily="Impact, Arial"
                fontSize={31}>{m.label}</text>
            </g>
          );
        })}

        {/* the span bracket: how long it took to get back to even */}
        {s.span && t > 0.92 ? (() => {
          const a = px(Date.parse(s.span!.a)), b = px(Date.parse(s.span!.b));
          const y = PAD.t + 18;
          const o = Math.min(1, (t - 0.92) / 0.08);
          return (
            <g opacity={o}>
              <line x1={a} x2={b} y1={y} y2={y} stroke={TEAL} strokeWidth={4} />
              <line x1={a} x2={a} y1={y - 11} y2={y + 11} stroke={TEAL} strokeWidth={4} />
              <line x1={b} x2={b} y1={y - 11} y2={y + 11} stroke={TEAL} strokeWidth={4} />
              <text x={(a + b) / 2} y={y - 18} textAnchor="middle" fill="#1B7F76"
                fontFamily="Impact, Arial" fontSize={34}>{s.span!.label}</text>
            </g>
          );
        })() : null}
      </svg>

      <div style={{position: "absolute", left: 30, top: 22,
        fontFamily: "Impact, Arial", fontSize: 34, letterSpacing: 1,
        color: INK}}>{s.title}</div>
      <div style={{position: "absolute", left: 30, right: 30, bottom: 16,
        fontFamily: "Arial", fontSize: 15, color: "#6B7488"}}>{s.foot}</div>
    </div>
  );
};
