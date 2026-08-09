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

  // the span bracket lives above the plot, so a series carrying one needs
  // its own strip of ceiling — otherwise the bracket's end ticks land on
  // exactly the two peak labels it is bracketing.
  // The ceiling is not just frame padding: a peak's callout is drawn ABOVE
  // the peak, and at 74 that callout landed across the title. The plot
  // starts below the title band, and lower again when a span bracket has
  // to fit between the two.
  const PAD = {l: 78, r: 34, t: s.span ? 112 : 100, b: 62};
  const iw = w - PAD.l - PAD.r, ih = h - PAD.t - PAD.b;
  const xs = s.points.map((p) => Date.parse(p[0]));
  const ys = s.points.map((p) => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  const lo = Math.min(...ys), hi = Math.max(...ys);
  // Headroom is ASYMMETRIC on purpose. Every trough here is annotated, a
  // trough label reads best under the point, and 6% of range is not enough
  // floor to put one there — it lands on the baseline instead.
  const rng = (hi - lo) || 1;
  const padHi = rng * 0.06, padLo = rng * 0.14;
  const px = (t: number) => PAD.l + ((t - x0) / (x1 - x0 || 1)) * iw;
  const py = (v: number) =>
    PAD.t + ih - ((v - (lo - padLo)) / ((hi + padHi) - (lo - padLo))) * ih;

  const t = ease(since / draw);
  const shown = Math.max(2, Math.round(t * s.points.length));
  const pts = s.points.slice(0, shown);
  const peakI = ys.indexOf(hi);

  const path = pts.map((p, i) =>
    `${i ? "L" : "M"}${px(Date.parse(p[0])).toFixed(1)},${py(p[1]).toFixed(1)}`
  ).join(" ");
  // The post-peak leg, drawn in burgundy so the fall reads as the event —
  // but only when there IS a fall. On the dot-com chart the high is the
  // 2015 recovery itself, and colouring its last two points burgundy put a
  // red "decline" tick on the exact frame that says it got back to even.
  const hasFall = ys.length - peakI > ys.length * 0.12;
  const fall = fallTone && hasFall && shown > peakI + 1
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
          const at = Date.parse(m.at);
          const mx = px(at), my = py(m.v);

          // Which side the label goes is a question about the SHAPE of the
          // line here, not about where the point sits in the frame. The old
          // rule ("high in the plot -> label below") put every trough label
          // inside the V it was annotating. Compare the marked value with
          // its neighbours instead: a trough gets its label underneath, a
          // peak gets it on top, and neither crosses the line.
          let near = 0;
          for (let i = 1; i < s.points.length; i++) {
            if (Math.abs(Date.parse(s.points[i][0]) - at) <
                Math.abs(Date.parse(s.points[near][0]) - at)) near = i;
          }
          const win = s.points.slice(Math.max(0, near - 3), near + 4);
          const mean = win.reduce((a, p) => a + p[1], 0) / (win.length || 1);
          const trough = m.v <= mean;

          // never into the title band, and never into the span bracket
          const topLim = s.span ? PAD.t - 12 : 78;
          const botLim = PAD.t + ih - 6;
          let ly = trough ? my + 44 : my - 22;
          if (ly > botLim) ly = my - 22;
          if (ly < topLim) ly = my + 44;

          // Keep the whole label inside the plot. Clamping the CENTRE (what
          // this did before) only works if the label is narrower than the
          // guess; "BACK TO EVEN" is not, and ran off the panel. Switching
          // the anchor at the edge bounds it whatever the estimate says.
          const FS = 31;
          const halfW = m.label.length * FS * 0.26;
          const lft = PAD.l + 4, rgt = w - PAD.r - 4;
          const anchor = mx + halfW > rgt ? "end"
            : mx - halfW < lft ? "start" : "middle";
          const lx = anchor === "end" ? rgt : anchor === "start" ? lft : mx;

          return (
            <g key={m.at}>
              <circle cx={mx} cy={my} r={8} fill={PAPER}
                stroke={BURG} strokeWidth={4} />
              {/* a paper halo, so where a label must sit near the line the
                  line gives way to the words rather than running through
                  them */}
              <text x={lx} y={ly} textAnchor={anchor} fill={INK}
                fontFamily="Impact, Arial" fontSize={FS}
                stroke={PAPER} strokeWidth={9} strokeLinejoin="round"
                paintOrder="stroke">{m.label}</text>
              <text x={lx} y={ly} textAnchor={anchor} fill={INK}
                fontFamily="Impact, Arial" fontSize={FS}>{m.label}</text>
            </g>
          );
        })}

        {/* the span bracket: how long it took to get back to even */}
        {s.span && t > 0.92 ? (() => {
          const a = px(Date.parse(s.span!.a)), b = px(Date.parse(s.span!.b));
          const y = PAD.t - 46;
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
