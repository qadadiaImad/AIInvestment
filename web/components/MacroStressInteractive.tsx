"use client";

import { useMemo, useState } from "react";
import type { GraphEdge } from "@/lib/data";
import { layerLabel } from "@/lib/format";
import {
  buildLayerMap,
  networkStressIndex,
  scoreEdge,
  stressColor,
  type StressInputs,
} from "@/lib/stress";
import StressControls, { STRESS_ZERO, type StressState } from "@/components/StressControls";

// Plain-English labels for edge types.
const TYPE_LABELS: Record<string, string> = {
  compute_commitment: "Compute commitment",
  equity_stake: "Equity stake",
  voting_power: "Voting power",
  subsidiary: "Subsidiary",
  customer: "Customer",
  infra_partner: "Infra partner",
};

function typeLabel(t: string): string {
  return TYPE_LABELS[t] ?? t.replace(/[_-]+/g, " ");
}

function indexBand(idx: number): { label: string; color: string } {
  // Higher index = more stress. Mirror the green→amber→red ramp.
  if (idx < 15) return { label: "calm", color: "#10b981" };
  if (idx < 35) return { label: "elevated", color: "#f59e0b" };
  return { label: "stressed", color: "#ef4444" };
}

export default function MacroStressInteractive({
  edges,
  nodes,
  dffBase,
}: {
  edges: GraphEdge[];
  nodes: { id: string; layer?: string }[];
  dffBase: number;
}) {
  const [shock, setShock] = useState<StressState>(STRESS_ZERO);

  const layerById = useMemo(() => buildLayerMap(nodes), [nodes]);

  const inp: StressInputs = useMemo(
    () => ({
      dRateBps: shock.dRateBps,
      dElecPct: shock.dElecPct,
      dffBase,
      layerById,
    }),
    [shock.dRateBps, shock.dElecPct, dffBase, layerById],
  );

  const { index, stressedCount, typeDegrade } = useMemo(() => {
    const idx = networkStressIndex(edges, inp);
    let stressed = 0;
    // Track mean stress drop by type to surface which types degrade most.
    const agg = new Map<string, { sum: number; n: number }>();
    for (const e of edges) {
      const s = scoreEdge(e, inp);
      if (s < 0.7) stressed++;
      const cur = agg.get(e.type) ?? { sum: 0, n: 0 };
      cur.sum += 1 - s; // degradation: 0 = unstressed, 1 = fully stressed
      cur.n += 1;
      agg.set(e.type, cur);
    }
    const degrade = [...agg.entries()]
      .map(([type, { sum, n }]) => ({ type, mean: n ? sum / n : 0, n }))
      .filter((d) => d.mean > 0.0001)
      .sort((a, b) => b.mean - a.mean);
    return { index: idx, stressedCount: stressed, typeDegrade: degrade };
  }, [edges, inp]);

  const band = indexBand(index);
  const idxColor = stressColor(1 - index / 100);

  return (
    <section>
      <div className="flex items-center justify-between gap-2 mb-2">
        <h2 className="text-[13px] font-semibold uppercase tracking-wider text-zinc-300">
          Interactive macro stress
        </h2>
        <span className="text-[9px] uppercase tracking-wider text-emerald-300/80 border border-emerald-500/40 rounded-sm px-1.5 py-px">
          live recompute
        </span>
      </div>

      <div className="rounded-sm border border-term-border bg-term-panel px-3 py-3 flex flex-col gap-4">
        <p className="text-[10.5px] text-term-muted leading-relaxed">
          Drag the sliders to shock the network on top of the current snapshot
          (Fed funds {dffBase.toFixed(2)}%). Edge stress recomputes in your
          browser and recolors the{" "}
          <a href="/map" className="text-sky-400 hover:text-sky-300 underline">
            relationship map
          </a>
          &rsquo;s edges. <strong>0 / 0 = current snapshot.</strong>
        </p>

        {/* sliders */}
        <StressControls value={shock} onChange={setShock} />

        {/* live readouts */}
        <div className="grid grid-cols-1 sm:grid-cols-[200px_1fr] gap-4 pt-1">
          <div className="rounded-sm border border-term-border bg-[#0b0f17] px-4 py-4 flex flex-col items-center justify-center text-center">
            <span className="text-[10px] uppercase tracking-wider text-term-muted">
              Network Stress Index
            </span>
            <span
              className="mt-1 text-[40px] font-bold leading-none tnum"
              style={{ color: idxColor }}
            >
              {index.toFixed(1)}
            </span>
            <span className="text-[9px] text-zinc-600">/ 100</span>
            <span
              className="mt-1.5 inline-block px-2 py-px text-[10px] font-semibold uppercase tracking-wider rounded-sm border"
              style={{ color: band.color, borderColor: band.color }}
            >
              {band.label}
            </span>
          </div>

          <div className="flex flex-col gap-3">
            <div className="rounded-sm border border-term-border bg-[#0b0f17] px-3 py-2.5">
              <div className="text-[9.5px] uppercase tracking-wider text-term-muted">
                Edges stressed (score &lt; 0.7)
              </div>
              <div className="mt-0.5 text-[18px] font-semibold tnum text-zinc-100">
                {stressedCount}
                <span className="text-[11px] text-zinc-500"> / {edges.length}</span>
              </div>
            </div>

            <div className="rounded-sm border border-term-border bg-[#0b0f17] px-3 py-2.5">
              <div className="text-[9.5px] uppercase tracking-wider text-term-muted mb-1.5">
                Edge types degrading most
              </div>
              {typeDegrade.length === 0 ? (
                <div className="text-[11px] text-zinc-500">
                  No degradation — sliders at 0 / 0 (current snapshot).
                </div>
              ) : (
                <ul className="flex flex-col gap-1.5">
                  {typeDegrade.slice(0, 4).map((d) => (
                    <li key={d.type} className="flex items-center gap-2">
                      <span className="text-[11px] text-zinc-300 w-[150px] shrink-0">
                        {typeLabel(d.type)}
                      </span>
                      <span className="flex-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                        <span
                          className="block h-full rounded-full"
                          style={{
                            width: `${Math.min(100, d.mean * 100)}%`,
                            backgroundColor: stressColor(1 - d.mean),
                          }}
                        />
                      </span>
                      <span className="tnum text-[10px] text-zinc-500 w-[64px] text-right">
                        −{(d.mean * 100).toFixed(1)}%
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>

        <p className="text-[9.5px] text-term-muted leading-relaxed border-t border-term-border pt-2">
          Illustrative client-side stress recompute (mirrors the Python model);
          betas are analyst priors; indicative ordinal signal, not a dollar-loss.
          Not financial advice.
        </p>
      </div>
    </section>
  );
}
