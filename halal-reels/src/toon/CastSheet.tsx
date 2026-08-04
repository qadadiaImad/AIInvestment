import React from "react";
import { AbsoluteFill } from "remotion";
import { Character } from "./rig";
import { DEFAULT } from "./defaults";
import { merge } from "./merge";
import { POSES, EXPR } from "./poses";
import { CHARACTERS } from "./characters";

const CELL = 400;
const COLS = 3;

export const CastSheet: React.FC = () => {
  const items = Object.entries(CHARACTERS).map(([label, skin]) => ({
    label,
    params: merge(DEFAULT, { skin }, POSES.rest.patch, EXPR.deadpan.patch),
  }));
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
              <g transform={`translate(58 14) scale(0.53)`}>
                <Character p={it.params} />
              </g>
              <text x={CELL / 2} y={CELL - 20} textAnchor="middle" fontFamily="monospace" fontSize={28} fill="#141414">
                {it.label}
              </text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
