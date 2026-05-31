"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { FundamentalValuePoint } from "@/lib/data";

interface PricePoint {
  date: string;
  close: number | null;
}

interface PriceFile {
  symbol: string;
  series: PricePoint[];
}

interface CleanPoint {
  t: number; // epoch ms
  v: number;
}

const PRICE_COLOR = "#e5e7eb";
const FUND_COLOR = "#f59e0b";
const GRID_COLOR = "#1b2433";
const AXIS_COLOR = "#6b7280";
const TARGET_POINTS = 260;

// Fixed plot height in CSS px — keeps the chart compact and consistent.
const CHART_H = 320;

function parsePoints(
  raw: { date: string; value?: number | null; close?: number | null }[],
  field: "value" | "close"
): CleanPoint[] {
  const out: CleanPoint[] = [];
  for (const p of raw) {
    const val = field === "value" ? p.value : p.close;
    if (typeof val !== "number" || !Number.isFinite(val)) continue;
    const t = Date.parse(p.date);
    if (!Number.isFinite(t)) continue;
    out.push({ t, v: val });
  }
  out.sort((a, b) => a.t - b.t);
  return out;
}

// Downsample by striding to keep ~TARGET_POINTS, always keep last point.
function downsample(pts: CleanPoint[], target = TARGET_POINTS): CleanPoint[] {
  if (pts.length <= target) return pts;
  const stride = Math.ceil(pts.length / target);
  const out: CleanPoint[] = [];
  for (let i = 0; i < pts.length; i += stride) out.push(pts[i]);
  const last = pts[pts.length - 1];
  if (out[out.length - 1]?.t !== last.t) out.push(last);
  return out;
}

function fmtPrice(v: number): string {
  const digits = v >= 1000 ? 0 : 2;
  return `$${v.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`;
}

function fmtDate(t: number): string {
  return new Date(t).toISOString().slice(0, 10);
}

export default function PriceChart({
  symbol,
  fundamentalSeries,
}: {
  symbol: string;
  fundamentalSeries?: FundamentalValuePoint[] | null;
}) {
  const [price, setPrice] = useState<CleanPoint[] | null>(null);
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
  // Captured client-side (in async callback) to split historical vs projected.
  const [nowMs, setNowMs] = useState<number>(0);

  // Responsive width: render the SVG at real pixel dimensions for crisp 1:1
  // strokes (no aspect-ratio distortion). Height is fixed at CHART_H.
  const wrapRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState<number>(760);
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

  // Hover crosshair (index into the merged x-domain via price series).
  const [hoverX, setHoverX] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`/data/prices/${symbol.toUpperCase()}.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<PriceFile>;
      })
      .then((data) => {
        if (cancelled) return;
        setNowMs(Date.now());
        setPrice(downsample(parsePoints(data.series ?? [], "close")));
        setStatus("ok");
      })
      .catch(() => {
        if (cancelled) return;
        setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [symbol]);

  const fund = useMemo(
    () => downsample(parsePoints(fundamentalSeries ?? [], "value")),
    [fundamentalSeries]
  );

  if (status === "loading") {
    return (
      <div
        className="flex items-center justify-center text-term-muted text-[11px]"
        style={{ height: CHART_H }}
      >
        Loading price history…
      </div>
    );
  }
  if (status === "error" || !price || price.length < 2) {
    return (
      <div
        className="flex items-center justify-center text-term-muted text-[11px]"
        style={{ height: CHART_H }}
      >
        Price history unavailable for {symbol}.
      </div>
    );
  }

  const hasFund = fund.length >= 2;

  // --- geometry (real pixels) ---
  const W = Math.max(320, Math.round(width));
  const H = CHART_H;
  const padL = 56;
  const padR = 14;
  const padT = 14;
  const padB = 26;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const allT = [...price.map((p) => p.t), ...fund.map((p) => p.t)];
  const allV = [...price.map((p) => p.v), ...fund.map((p) => p.v)];
  const minT = Math.min(...allT);
  const maxT = Math.max(...allT);
  let minV = Math.min(...allV);
  let maxV = Math.max(...allV);
  // pad the value axis a touch so the top/bottom lines aren't flush to edges
  const vPad = (maxV - minV || 1) * 0.06;
  minV -= vPad;
  maxV += vPad;
  const tRange = maxT - minT || 1;
  const vRange = maxV - minV || 1;

  const x = (t: number) => padL + ((t - minT) / tRange) * plotW;
  const y = (v: number) => padT + (1 - (v - minV) / vRange) * plotH;

  const linePath = (pts: CleanPoint[]) =>
    pts
      .map((p, i) => `${i === 0 ? "M" : "L"}${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`)
      .join(" ");

  const pricePath = linePath(price);
  // subtle area fill under the price line
  const priceArea =
    pricePath +
    ` L${x(price[price.length - 1].t).toFixed(1)},${(H - padB).toFixed(1)}` +
    ` L${x(price[0].t).toFixed(1)},${(H - padB).toFixed(1)} Z`;

  // Split fundamental series into historical (<= today) and projected (> today).
  const fundHist = hasFund ? fund.filter((p) => p.t <= nowMs) : [];
  const fundProj = hasFund ? fund.filter((p) => p.t > nowMs) : [];
  // Bridge: include the last historical point at the start of projected for continuity.
  const fundProjPath =
    fundProj.length > 0
      ? linePath(
          fundHist.length > 0
            ? [fundHist[fundHist.length - 1], ...fundProj]
            : fundProj
        )
      : "";
  const fundHistPath = fundHist.length >= 2 ? linePath(fundHist) : "";

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

  const todayX = nowMs >= minT && nowMs <= maxT ? x(nowMs) : null;

  // --- hover crosshair: find nearest price point to cursor x ---
  let hover: { px: number; pt: CleanPoint; fv: number | null } | null = null;
  if (hoverX != null) {
    const t = minT + ((hoverX - padL) / plotW) * tRange;
    let nearest = price[0];
    let best = Infinity;
    for (const p of price) {
      const d = Math.abs(p.t - t);
      if (d < best) {
        best = d;
        nearest = p;
      }
    }
    // nearest fundamental value (if any)
    let fv: number | null = null;
    if (hasFund) {
      let bf = Infinity;
      for (const p of fund) {
        const d = Math.abs(p.t - nearest.t);
        if (d < bf) {
          bf = d;
          fv = p.v;
        }
      }
    }
    hover = { px: x(nearest.t), pt: nearest, fv };
  }

  function onMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    // map client px → viewBox units (preserveAspectRatio="none" scales x by W/rect.width)
    const px = ((e.clientX - rect.left) / rect.width) * W;
    if (px >= padL && px <= W - padR) setHoverX(px);
    else setHoverX(null);
  }

  return (
    <div className="flex flex-col gap-2.5">
      <div
        ref={wrapRef}
        className="w-full overflow-hidden"
        style={{ height: CHART_H }}
      >
        <svg
          width="100%"
          height={H}
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          style={{ width: "100%", height: H }}
          className="block select-none"
          role="img"
          aria-label={`${symbol} daily closing price${
            hasFund ? " with fundamental value overlay" : ""
          }`}
          onMouseMove={onMove}
          onMouseLeave={() => setHoverX(null)}
        >
          <defs>
            <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={PRICE_COLOR} stopOpacity={0.12} />
              <stop offset="100%" stopColor={PRICE_COLOR} stopOpacity={0} />
            </linearGradient>
          </defs>

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
                  {fmtPrice(tv)}
                </text>
              </g>
            );
          })}

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

          {/* today divider when projected portion exists */}
          {todayX != null && fundProj.length > 0 && (
            <g>
              <line
                x1={todayX}
                x2={todayX}
                y1={padT}
                y2={H - padB}
                stroke="#5b6675"
                strokeWidth={1}
                strokeDasharray="2 3"
                shapeRendering="crispEdges"
              />
              <text x={todayX + 4} y={padT + 10} fontSize={9} fill={AXIS_COLOR}>
                today
              </text>
            </g>
          )}

          {/* price area fill */}
          <path d={priceArea} fill="url(#priceFill)" stroke="none" />

          {/* fundamental value: historical (solid) */}
          {fundHistPath && (
            <path
              d={fundHistPath}
              fill="none"
              stroke={FUND_COLOR}
              strokeWidth={1.6}
              strokeLinejoin="round"
            />
          )}
          {/* fundamental value: projected (dashed) */}
          {fundProjPath && (
            <path
              d={fundProjPath}
              fill="none"
              stroke={FUND_COLOR}
              strokeWidth={1.6}
              strokeDasharray="4 3"
              opacity={0.9}
              strokeLinejoin="round"
            />
          )}

          {/* price line (drawn on top) */}
          <path
            d={pricePath}
            fill="none"
            stroke={PRICE_COLOR}
            strokeWidth={1.4}
            strokeLinejoin="round"
            strokeLinecap="round"
          />

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
              <circle
                cx={hover.px}
                cy={y(hover.pt.v)}
                r={2.8}
                fill={PRICE_COLOR}
              />
              {hover.fv != null && (
                <circle
                  cx={hover.px}
                  cy={y(hover.fv)}
                  r={2.8}
                  fill={FUND_COLOR}
                />
              )}
              {/* readout box, flips side near the right edge */}
              {(() => {
                const boxW = hover.fv != null ? 150 : 124;
                const boxH = hover.fv != null ? 40 : 28;
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
                    <text
                      x={bx + 8}
                      y={padT + 15}
                      fontSize={10}
                      fill={AXIS_COLOR}
                    >
                      {fmtDate(hover.pt.t)}
                    </text>
                    <text
                      x={bx + 8}
                      y={padT + 27}
                      fontSize={10.5}
                      fill={PRICE_COLOR}
                      style={{ fontVariantNumeric: "tabular-nums" }}
                    >
                      {fmtPrice(hover.pt.v)}
                    </text>
                    {hover.fv != null && (
                      <text
                        x={bx + 8}
                        y={padT + 39}
                        fontSize={10.5}
                        fill={FUND_COLOR}
                        style={{ fontVariantNumeric: "tabular-nums" }}
                      >
                        {fmtPrice(hover.fv)}
                      </text>
                    )}
                  </g>
                );
              })()}
            </g>
          )}
        </svg>
      </div>

      {/* legend */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[10.5px] text-term-muted">
        <span className="inline-flex items-center gap-1.5">
          <span
            className="inline-block w-4 h-[2px]"
            style={{ background: PRICE_COLOR }}
          />
          Price (daily close)
        </span>
        {hasFund ? (
          <>
            <span className="inline-flex items-center gap-1.5">
              <span
                className="inline-block w-4 h-[2px]"
                style={{ background: FUND_COLOR }}
              />
              Fundamental value
            </span>
            {fundProj.length > 0 && (
              <span className="inline-flex items-center gap-1.5">
                <span
                  className="inline-block w-4 h-0 border-t-2 border-dashed"
                  style={{ borderColor: FUND_COLOR }}
                />
                Projected
              </span>
            )}
          </>
        ) : (
          <span className="text-term-muted/80 italic">
            No fundamental-value series for {symbol} yet — price only.
          </span>
        )}
        <span className="ml-auto tnum">
          {fmtDate(price[0].t)} → {fmtDate(price[price.length - 1].t)}
        </span>
      </div>

      <p className="text-[9.5px] leading-snug text-term-muted">
        Fundamental value is a third-party intrinsic estimate (historical +
        projected); educational only.
      </p>
    </div>
  );
}
