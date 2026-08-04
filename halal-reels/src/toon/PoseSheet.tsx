import React from "react";
import { AbsoluteFill } from "remotion";
import { Character } from "./rig";
import { DEFAULT } from "./defaults";
import { merge } from "./merge";
import { POSES, EXPR } from "./poses";

const CELL = 300;
const COLS = 6;

export const PoseSheet: React.FC = () => {
  const items = [
    ...Object.entries(POSES).map(([k, v]) => ({ label: k, params: merge(DEFAULT, v.patch, EXPR.deadpan.patch) })),
    ...Object.entries(EXPR).map(([k, v]) => ({ label: k, params: merge(DEFAULT, v.patch) })),
  ];
  const rows = Math.ceil(items.length / COLS);
  return (
    <AbsoluteFill style={{ background: "#8A97A6" }}>
      <svg width={COLS * CELL} height={rows * CELL} viewBox={`0 0 ${COLS * CELL} ${rows * CELL}`}>
        {items.map((it, i) => {
          const x = (i % COLS) * CELL;
          const y = Math.floor(i / COLS) * CELL;
          return (
            <g key={it.label} transform={`translate(${x} ${y})`}>
              <rect x={2} y={2} width={CELL - 4} height={CELL - 4} fill="#B7A6AE" stroke="#1A1A1A" strokeWidth={2} />
              <g transform={`translate(30 -80) scale(0.45)`}>
                <Character p={it.params} />
              </g>
              <text x={CELL / 2} y={CELL - 14} textAnchor="middle" fontFamily="monospace" fontSize={20} fill="#141414">
                {it.label}
              </text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
