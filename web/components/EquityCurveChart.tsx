"use client";

import { useEffect, useMemo, useRef, useState } from "react";

export interface EquityLine {
  name: string;
  color: string;
  equity: [string, number][];
}

interface CleanPoint {
  t: number; // epoch ms
  v: number;
}

const GRID_COLOR = "#1b2433";
const AXIS_COLOR = "#6b7280";
const TARGET_POINTS = 300;
const CHART_H = 360;

function parse(equity: [string, number][]): CleanPoint[] {
  const out: CleanPoint[] = [];
  for (const [date, value] of equity) {
    if (typeof value !== "number" || !Number.isFinite(value)) continue;
    const t = Date.parse(date);
    if (!Number.isFinite(t)) continue;
    out.push({ t, v: value });
  }
  out.sort((a, b) => a.t - b.t);
  return out;
}

function downsample(pts: CleanPoint[], target = TARGET_POINTS): CleanPoint[] {
  if (pts.length <= target) return pts;
  const stride = Math.ceil(pts.length / target);
  const out: CleanPoint[] = [];
  for (let i = 0; i < pts.length; i += stride) out.push(pts[i]);
  const last = pts[pts.length - 1];
  if (out[out.length - 1]?.t !== last.t) out.push(last);
  return out;
}

function fmtMult(v: number): string {
  return `$${v.toFixed(v >= 10 ? 1 : 2)}`;
}

function fmtDate(t: number): string {
  return new Date(t).toISOString().slice(0, 10);
}

export default function EquityCurveChart({ lines }: { lines: EquityLine[] }) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState<number>(760);
  const [hoverX, setHoverX] = useState<number | null>(null);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width;
      if (w && w > 0) setWidth(w);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const series = useMemo(
    () =>
      lines.map((l) => ({
        name: l.name,
        color: l.color,
        pts: downsample(parse(l.equity)),
      })),
    [lines]
  );

  const valid = series.filter((s) => s.pts.length >= 2);
  if (valid.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-term-muted text-[11px]"
        style={{ height: CHART_H }}
      >
        No equity data available.
      </div>
    );
  }

  // --- geometry (real pixels) ---
  const W = Math.max(320, Math.round(width));
  const H = CHART_H;
  const padL = 52;
  const padR = 14;
  const padT = 14;
  const padB = 26;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const allT: number[] = [];
  const allV: number[] = [];
  for (const s of valid) {
    for (const p of s.pts) {
      allT.push(p.t);
      allV.push(p.v);
    }
  }
  const minT = Math.min(...allT);
  const maxT = Math.max(...allT);
  let minV = Math.min(...allV);
  let maxV = Math.max(...allV);
  const vPad = (maxV - minV || 1) * 0.06;
  minV -= vPad;
  maxV += vPad;
  // Keep $1 baseline in view.
  if (minV > 1) minV = 1 - vPad;
  const tRange = maxT - minT || 1;
  const vRange = maxV - minV || 1;

  const x = (t: number) => padL + ((t - minT) / tRange) * plotW;
  const y = (v: number) => padT + (1 - (v - minV) / vRange) * plotH;

  const linePath = (pts: CleanPoint[]) =>
    pts
      .map((p, i) => `${i === 0 ? "M" : "L"}${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`)
      .join(" ");

  // y-axis ticks (5 lines)
  const tickCount = 5;
  const ticks = Array.from(
    { length: tickCount },
    (_, i) => minV + (vRange * i) / (tickCount - 1)
  );
  // x-axis year labels
  const yearTicks: { t: number; label: string }[] = [];
  const startYear = new Date(minT).getUTCFullYear();
  const endYear = new Date(maxT).getUTCFullYear();
  for (let yr = startYear; yr <= endYear; yr++) {
    const t = Date.UTC(yr, 0, 1);
    if (t >= minT && t <= maxT) yearTicks.push({ t, label: String(yr) });
  }

  // baseline ($1) gridline if in range
  const baselineY = 1 >= minV && 1 <= maxV ? y(1) : null;

  // --- hover crosshair: snap to nearest x across the first series' time grid ---
  const ref = valid[0].pts;
  let hover:
    | { px: number; readouts: { name: string; color: string; v: number }[]; t: number }
    | null = null;
  if (hoverX != null) {
    const t = minT + ((hoverX - padL) / plotW) * tRange;
    let nearest = ref[0];
    let best = Infinity;
    for (const p of ref) {
      const d = Math.abs(p.t - t);
      if (d < best) {
        best = d;
        nearest = p;
      }
    }
    const readouts = valid.map((s) => {
      let bv = s.pts[0];
      let bd = Infinity;
      for (const p of s.pts) {
        const d = Math.abs(p.t - nearest.t);
        if (d < bd) {
          bd = d;
          bv = p;
        }
      }
      return { name: s.name, color: s.color, v: bv.v };
    });
    hover = { px: x(nearest.t), readouts, t: nearest.t };
  }

  function onMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * W;
    if (px >= padL && px <= W - padR) setHoverX(px);
    else setHoverX(null);
  }

  const boxW = 168;
  const boxH = 16 + valid.length * 12;

  return (
    <div className="flex flex-col gap-2.5">
      <div ref={wrapRef} className="w-full overflow-hidden" style={{ height: CHART_H }}>
        <svg
          width="100%"
          height={H}
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          style={{ width: "100%", height: H }}
          className="block select-none"
          role="img"
          aria-label="Backtest equity curves: growth of $1 for each strategy and the benchmark"
          onMouseMove={onMove}
          onMouseLeave={() => setHoverX(null)}
        >
          {/* horizontal grid + y labels */}
          {ticks.map((tv, i) => {
            const yy = y(tv);
            return (
              <g key={i}>
                <line
                  x1={padL}
                  x2={W - padR}
                  y1={yy}
                  y2={yy}
                  stroke={GRID_COLOR}
                  strokeWidth={1}
                  shapeRendering="crispEdges"
                />
                <text
                  x={padL - 8}
                  y={yy + 3}
                  textAnchor="end"
                  fontSize={10}
                  fill={AXIS_COLOR}
                  style={{ fontVariantNumeric: "tabular-nums" }}
                >
                  {fmtMult(tv)}
                </text>
              </g>
            );
          })}

          {/* $1 baseline emphasis */}
          {baselineY != null && (
            <line
              x1={padL}
              x2={W - padR}
              y1={baselineY}
              y2={baselineY}
              stroke="#3a4456"
              strokeWidth={1}
              strokeDasharray="3 3"
              shapeRendering="crispEdges"
            />
          )}

          {/* x year ticks + labels */}
          {yearTicks.map((yt) => (
            <g key={yt.label}>
              <line
                x1={x(yt.t)}
                x2={x(yt.t)}
                y1={H - padB}
                y2={H - padB + 4}
                stroke={AXIS_COLOR}
                strokeWidth={1}
                shapeRendering="crispEdges"
              />
              <text
                x={x(yt.t)}
                y={H - 8}
                textAnchor="middle"
                fontSize={10}
                fill={AXIS_COLOR}
                style={{ fontVariantNumeric: "tabular-nums" }}
              >
                {yt.label}
              </text>
            </g>
          ))}

          {/* lines */}
          {valid.map((s) => (
            <path
              key={s.name}
              d={linePath(s.pts)}
              fill="none"
              stroke={s.color}
              strokeWidth={1.5}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          ))}

          {/* hover crosshair */}
          {hover && (
            <g>
              <line
                x1={hover.px}
                x2={hover.px}
                y1={padT}
                y2={H - padB}
                stroke="#6b7280"
                strokeWidth={1}
                strokeDasharray="2 2"
                shapeRendering="crispEdges"
              />
              {hover.readouts.map((r) => (
                <circle
                  key={r.name}
                  cx={hover!.px}
                  cy={y(r.v)}
                  r={2.6}
                  fill={r.color}
                />
              ))}
              {(() => {
                const flip = hover.px + boxW + 12 > W - padR;
                const bx = flip ? hover.px - boxW - 8 : hover.px + 8;
                return (
                  <g>
                    <rect
                      x={bx}
                      y={padT + 2}
                      width={boxW}
                      height={boxH}
                      rx={2}
                      fill="#0b0f17"
                      stroke={GRID_COLOR}
                      strokeWidth={1}
                    />
                    <text x={bx + 8} y={padT + 14} fontSize={10} fill={AXIS_COLOR}>
                      {fmtDate(hover.t)}
                    </text>
                    {hover.readouts.map((r, i) => (
                      <text
                        key={r.name}
                        x={bx + 8}
                        y={padT + 26 + i * 12}
                        fontSize={10}
                        fill={r.color}
                        style={{ fontVariantNumeric: "tabular-nums" }}
                      >
                        {r.name}: {fmtMult(r.v)}
                      </text>
                    ))}
                  </g>
                );
              })()}
            </g>
          )}
        </svg>
      </div>

      {/* legend */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[10.5px] text-term-muted">
        {valid.map((s) => (
          <span key={s.name} className="inline-flex items-center gap-1.5">
            <span
              className="inline-block w-4 h-[2px]"
              style={{ background: s.color }}
            />
            {s.name}
          </span>
        ))}
        <span className="ml-auto tnum">
          {fmtDate(minT)} → {fmtDate(maxT)} · growth of $1
        </span>
      </div>
    </div>
  );
}
