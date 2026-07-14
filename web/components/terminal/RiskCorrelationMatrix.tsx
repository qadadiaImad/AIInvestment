"use client";

import { useState } from "react";
import type { RiskLayerCorrelationBlock, RiskTopStocksBlock } from "@/lib/risk";
import { DASH, contrastText, correlationColor, layerLabel } from "@/lib/format";

type View = "layers" | "stocks";

const CELL = 56;
const LABEL_COL = 90;
const LABEL_ROW = 26;

function Matrix({
  order,
  matrix,
  labelFor,
}: {
  order: string[];
  matrix: (number | null)[][];
  labelFor: (raw: string) => string;
}) {
  const n = order.length;
  const width = LABEL_COL + n * CELL;
  const height = LABEL_ROW + n * CELL;

  if (n === 0) {
    return (
      <div className="text-[11px] text-term-muted px-2 py-4">
        Not enough overlapping history to build this matrix yet.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <svg width={width} height={height} role="img" aria-label="Correlation matrix">
        {/* column labels */}
        {order.map((sym, c) => (
          <text
            key={`col-${sym}`}
            x={LABEL_COL + c * CELL + CELL / 2}
            y={LABEL_ROW - 8}
            textAnchor="middle"
            fontSize={10}
            fontWeight={600}
            fill="#9ca3af"
          >
            {labelFor(sym)}
          </text>
        ))}
        {/* row labels */}
        {order.map((sym, r) => (
          <text
            key={`row-${sym}`}
            x={LABEL_COL - 8}
            y={LABEL_ROW + r * CELL + CELL / 2 + 4}
            textAnchor="end"
            fontSize={10}
            fontWeight={600}
            fill="#9ca3af"
          >
            {labelFor(sym)}
          </text>
        ))}
        {/* cells */}
        {order.map((rowSym, r) =>
          order.map((colSym, c) => {
            const v = matrix[r]?.[c] ?? null;
            const bg = correlationColor(v);
            const fg = contrastText(bg);
            const x = LABEL_COL + c * CELL;
            const y = LABEL_ROW + r * CELL;
            return (
              <g key={`${rowSym}-${colSym}`}>
                <rect
                  x={x}
                  y={y}
                  width={CELL - 2}
                  height={CELL - 2}
                  fill={bg}
                  stroke="#0b0f17"
                  strokeWidth={1}
                  rx={2}
                />
                <text
                  x={x + (CELL - 2) / 2}
                  y={y + (CELL - 2) / 2 + 4}
                  textAnchor="middle"
                  fontSize={11}
                  fontWeight={600}
                  fontFamily="var(--font-jetbrains-mono), ui-monospace, monospace"
                  fill={fg}
                >
                  {v == null ? DASH : v.toFixed(2)}
                </text>
              </g>
            );
          }),
        )}
      </svg>
    </div>
  );
}

// Toggle between the 5(+SPY) layer matrix and the top-N-by-market-cap stock
// matrix. Renders whatever order[] actually contains — never hardcodes 6 or
// 15, since either matrix can shrink when a series fails the >=60-bar
// diagonal rule.
export default function RiskCorrelationMatrix({
  layers,
  topStocks,
}: {
  layers: RiskLayerCorrelationBlock;
  topStocks: RiskTopStocksBlock;
}) {
  const [view, setView] = useState<View>("layers");

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-1.5">
        <button
          type="button"
          onClick={() => setView("layers")}
          className={
            view === "layers"
              ? "px-2.5 py-1 text-[10.5px] font-semibold uppercase tracking-wider rounded-sm border border-emerald-500/60 text-emerald-400 bg-emerald-500/10"
              : "px-2.5 py-1 text-[10.5px] font-semibold uppercase tracking-wider rounded-sm border border-term-border text-term-muted hover:text-zinc-200"
          }
        >
          Layers ({layers.order.length}×{layers.order.length})
        </button>
        <button
          type="button"
          onClick={() => setView("stocks")}
          className={
            view === "stocks"
              ? "px-2.5 py-1 text-[10.5px] font-semibold uppercase tracking-wider rounded-sm border border-emerald-500/60 text-emerald-400 bg-emerald-500/10"
              : "px-2.5 py-1 text-[10.5px] font-semibold uppercase tracking-wider rounded-sm border border-term-border text-term-muted hover:text-zinc-200"
          }
        >
          Top {topStocks.order.length} stocks
        </button>
      </div>

      {view === "layers" ? (
        <>
          <Matrix
            order={layers.order}
            matrix={layers.matrix}
            labelFor={(sym) => (sym === "SPY" ? "SPY" : layerLabel(sym))}
          />
          {layers.l3_models_note && (
            <p className="text-[10px] text-term-muted leading-relaxed px-1">
              {layers.l3_models_note}
            </p>
          )}
        </>
      ) : (
        <>
          <p className="text-[10px] text-term-muted px-1">
            Top {topStocks.order.length} by market cap, AI-stack only.
          </p>
          <Matrix order={topStocks.order} matrix={topStocks.matrix} labelFor={(s) => s} />
        </>
      )}
    </div>
  );
}
