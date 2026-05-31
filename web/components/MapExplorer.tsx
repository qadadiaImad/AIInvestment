"use client";

import { useMemo, useState } from "react";
import type { CapitalWeb, ResiliencyNode } from "@/lib/data";
import { LAYER_LABELS, LAYER_ORDER } from "@/lib/format";
import CapitalGraph, { type ColorMode } from "@/components/CapitalGraph";
import NodeDetailPanel from "@/components/NodeDetailPanel";
import StressControls, { STRESS_ZERO, type StressState } from "@/components/StressControls";

function layerSortKey(layer?: string): number {
  if (!layer) return LAYER_ORDER.length + 1;
  const i = LAYER_ORDER.indexOf(layer);
  return i === -1 ? LAYER_ORDER.length : i;
}

export default function MapExplorer({
  web,
  resiliency,
  dffBase,
}: {
  web: CapitalWeb;
  resiliency?: ResiliencyNode[];
  dffBase: number;
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [colorMode, setColorMode] = useState<ColorMode>("layer");
  const [shock, setShock] = useState<StressState>(STRESS_ZERO);
  const stressActive = shock.dRateBps !== 0 || shock.dElecPct !== 0;

  // Build <optgroup>s grouped & ordered by layer.
  const groups = useMemo(() => {
    const byLayer = new Map<string, CapitalWeb["nodes"]>();
    for (const n of web.nodes) {
      const key = n.layer ?? "other";
      const arr = byLayer.get(key) ?? [];
      arr.push(n);
      byLayer.set(key, arr);
    }
    return [...byLayer.entries()]
      .sort((a, b) => layerSortKey(a[0]) - layerSortKey(b[0]))
      .map(([layer, nodes]) => ({
        layer,
        label: LAYER_LABELS[layer] ?? layer.toUpperCase(),
        nodes: [...nodes].sort((a, b) =>
          (a.name || a.id).localeCompare(b.name || b.id),
        ),
      }));
  }, [web.nodes]);

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* selector bar */}
      <div className="flex flex-wrap items-center gap-2 px-3 py-2 border-b border-term-border">
        <label
          htmlFor="node-select"
          className="text-[10.5px] uppercase tracking-wider text-term-muted"
        >
          Drill into node
        </label>
        <select
          id="node-select"
          value={selectedId ?? ""}
          onChange={(e) => setSelectedId(e.target.value || null)}
          className="bg-[#0b0f17] border border-term-border rounded-sm px-2 py-1 text-[11px] text-zinc-200 font-mono max-w-[280px] focus:outline-none focus:border-zinc-500"
        >
          <option value="">— select a node —</option>
          {groups.map((g) => (
            <optgroup key={g.layer} label={g.label}>
              {g.nodes.map((n) => (
                <option key={n.id} value={n.id}>
                  {(n.name || n.id) + (n.layer ? ` — ${n.layer}` : "")}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
        {selectedId && (
          <button
            type="button"
            onClick={() => setSelectedId(null)}
            className="text-[10.5px] text-zinc-500 hover:text-zinc-300 underline"
          >
            clear
          </button>
        )}

        {/* Color-by toggle: Layer | Health */}
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[10.5px] uppercase tracking-wider text-term-muted">
            Color nodes by
          </span>
          <div className="inline-flex rounded-sm border border-term-border overflow-hidden">
            {(["layer", "health"] as ColorMode[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setColorMode(m)}
                className={`px-2 py-1 text-[10.5px] uppercase tracking-wider transition-colors ${
                  colorMode === m
                    ? "bg-emerald-500/20 text-emerald-300"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* macro-stress slider bar (compact) */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 px-3 py-2 border-b border-term-border bg-[#0a0d14]">
        <span className="text-[9.5px] uppercase tracking-wider text-emerald-300/80">
          Macro stress
        </span>
        <StressControls value={shock} onChange={setShock} compact />
        <span className="text-[9px] text-term-muted ml-auto basis-full sm:basis-auto">
          {stressActive
            ? "Edges colored by live stress — green resilient → red stressed."
            : "Sliders at 0 / 0 — edges use default styling."}{" "}
          Illustrative client-side recompute (mirrors the Python model);
          indicative, not a dollar-loss. Not financial advice.
        </span>
      </div>

      {/* graph + detail panel */}
      <div className="flex flex-col lg:flex-row flex-1 min-h-0">
        <div className="relative flex-1 min-h-[55vh] lg:min-h-0 bg-[#0b0f17]">
          <CapitalGraph
            web={web}
            resiliency={resiliency}
            colorMode={colorMode}
            selectedId={selectedId}
            onSelect={setSelectedId}
            stress={{
              dRateBps: shock.dRateBps,
              dElecPct: shock.dElecPct,
              dffBase,
            }}
          />
        </div>
        <aside className="lg:w-[360px] shrink-0 border-t lg:border-t-0 lg:border-l border-term-border bg-[#0a0d14] min-h-[40vh] lg:min-h-0 lg:h-auto flex flex-col">
          <NodeDetailPanel
            web={web}
            selectedId={selectedId}
            resiliency={resiliency}
          />
        </aside>
      </div>
    </div>
  );
}
