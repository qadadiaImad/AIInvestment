import React from "react";
import { RigParams, Arm } from "./types";

const L1 = 70; // upper arm
const L2 = 62; // forearm
const RAD = Math.PI / 180;

function armGeom(ox: number, oy: number, a: Arm) {
  const ex = ox + L1 * Math.sin(a.shoulder * RAD);
  const ey = oy + L1 * Math.cos(a.shoulder * RAD);
  const hx = ex + L2 * Math.sin((a.shoulder + a.elbow) * RAD);
  const hy = ey + L2 * Math.cos((a.shoulder + a.elbow) * RAD);
  return { ex, ey, hx, hy };
}

const Brow: React.FC<{ x: number; kind: string; o: string }> = ({ x, kind, o }) => {
  const y = 150;
  const d =
    kind === "raise" ? `M${x - 20} ${y - 8} q20 -10 40 0`
      : kind === "furrow" ? `M${x - 20} ${y + 4} l40 -8`
      : kind === "sad" ? `M${x - 20} ${y - 6} l40 8`
      : `M${x - 20} ${y} l40 0`;
  return <path d={d} stroke={o} strokeWidth={8} fill="none" strokeLinecap="round" />;
};

const Eyes: React.FC<{ kind: string; o: string }> = ({ kind, o }) => {
  if (kind === "blink" || kind === "dead")
    return (
      <>
        <line x1={222} y1={196} x2={252} y2={196} stroke={o} strokeWidth={8} strokeLinecap="round" />
        <line x1={288} y1={196} x2={318} y2={196} stroke={o} strokeWidth={8} strokeLinecap="round" />
      </>
    );
  const r = kind === "wide" ? 19 : 14;
  const dx = kind === "sideL" ? -6 : kind === "sideR" ? 6 : 0;
  return (
    <>
      <circle cx={237 + dx} cy={196} r={r} fill={o} />
      <circle cx={303 + dx} cy={196} r={r} fill={o} />
    </>
  );
};

const Mouth: React.FC<{ kind: string; o: string }> = ({ kind, o }) => {
  switch (kind) {
    case "open": return <ellipse cx={270} cy={252} rx={20} ry={15} fill={o} />;
    case "o": return <circle cx={270} cy={252} r={13} fill={o} />;
    case "smile": return <path d="M244 248 q26 26 52 0" stroke={o} strokeWidth={7} fill="none" strokeLinecap="round" />;
    case "frown": return <path d="M244 258 q26 -26 52 0" stroke={o} strokeWidth={7} fill="none" strokeLinecap="round" />;
    case "grimace": return <rect x={244} y={246} width={52} height={14} rx={4} fill="none" stroke={o} strokeWidth={6} />;
    default: return <line x1={242} y1={252} x2={298} y2={252} stroke={o} strokeWidth={7} strokeLinecap="round" />;
  }
};

const Prop: React.FC<{ kind: string; x: number; y: number; o: string }> = ({ kind, x, y, o }) => {
  if (kind === "paper") return <rect x={x - 22} y={y - 28} width={44} height={56} rx={3} fill="#FFF6E9" stroke={o} strokeWidth={5} />;
  if (kind === "phone") return <rect x={x - 12} y={y - 24} width={24} height={48} rx={5} fill="#2B2F36" stroke={o} strokeWidth={5} />;
  if (kind === "pointer") return <line x1={x} y1={y} x2={x + 60} y2={y - 40} stroke={o} strokeWidth={7} strokeLinecap="round" />;
  if (kind === "fiddle") return <ellipse cx={x} cy={y} rx={16} ry={26} fill="#B5651D" stroke={o} strokeWidth={5} />;
  return null;
};

export const Character: React.FC<{ p: RigParams }> = ({ p }) => {
  const o = p.skin.outline;
  const L = armGeom(215, 360, p.armL);
  const R = armGeom(325, 360, p.armR);
  return (
    <g transform={`translate(0 ${p.bob}) rotate(${p.lean} 270 400)`}>
      <line x1={270} y1={300} x2={270} y2={360} stroke={o} strokeWidth={9} />
      <path d="M150 520 C150 400 205 350 270 350 C335 350 390 400 390 520 Z" fill={p.skin.shirtFill} stroke={o} strokeWidth={9} />
      {/* arms */}
      <path d={`M215 360 L${L.ex} ${L.ey} L${L.hx} ${L.hy}`} fill="none" stroke={o} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round" />
      <path d={`M325 360 L${R.ex} ${R.ey} L${R.hx} ${R.hy}`} fill="none" stroke={o} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round" />
      <g transform={`rotate(${p.armL.wrist} ${L.hx} ${L.hy})`}>
        <circle cx={L.hx} cy={L.hy} r={13} fill={p.skin.skinFill} stroke={o} strokeWidth={8} />
      </g>
      <g transform={`rotate(${p.armR.wrist} ${R.hx} ${R.hy})`}>
        <circle cx={R.hx} cy={R.hy} r={13} fill={p.skin.skinFill} stroke={o} strokeWidth={8} />
        <Prop kind={p.prop} x={R.hx} y={R.hy} o={o} />
      </g>
      {/* head */}
      <g transform={`translate(${p.headTurn} 0)`}>
        <circle cx={270} cy={200} r={115} fill={p.skin.skinFill} stroke={o} strokeWidth={10} />
        <Brow x={232} kind={p.brows.l} o={o} />
        <Brow x={308} kind={p.brows.r} o={o} />
        <Eyes kind={p.eyes} o={o} />
        <Mouth kind={p.mouth} o={o} />
        {p.sweat && <path d="M355 175 q10 20 0 34 q-10 -14 0 -34" fill="#8FD3FF" stroke={o} strokeWidth={3} />}
      </g>
    </g>
  );
};
