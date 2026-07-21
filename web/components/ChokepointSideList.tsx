"use client";

import type { Chokepoint } from "@/lib/chokepoints";
import { categoryColor, categoryLabel, severityColor } from "@/lib/chokepoints";

// Severity-ordered flat list of chokepoints for the /map aside. Mobile
// horizontal-scroll (a vertical stack of 13 cards would push NodeDetailPanel
// far below the fold on phones); desktop wraps to a vertical list via the
// lg: breakpoint override in the parent. Selecting an entry drives the same
// activeChokepointId focus state as clicking a member node's ring on canvas.
export default function ChokepointSideList({
  chokepoints,
  activeId,
  onSelect,
}: {
  chokepoints: Chokepoint[];
  activeId: string | null;
  onSelect: (id: string | null) => void;
}) {
  if (chokepoints.length === 0) return null;

  const sorted = [...chokepoints].sort((a, b) => b.severity_score - a.severity_score);

  return (
    <div className="border-b border-term-border shrink-0">
      <div className="px-2.5 pt-2 pb-1 flex items-center justify-between">
        <h3 className="text-[9.5px] font-semibold uppercase tracking-wider text-zinc-500">
          ⛓ Chokepoints ({sorted.length})
        </h3>
        {activeId && (
          <button
            type="button"
            onClick={() => onSelect(null)}
            className="text-[9.5px] text-zinc-500 hover:text-zinc-300 underline"
          >
            clear
          </button>
        )}
      </div>
      <div className="flex lg:flex-col gap-1.5 px-2.5 pb-2 overflow-x-auto lg:overflow-x-visible [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
        {sorted.map((cp) => {
          const active = cp.id === activeId;
          const color = categoryColor(cp.category);
          return (
            <button
              key={cp.id}
              type="button"
              onClick={() => onSelect(active ? null : cp.id)}
              className={`shrink-0 lg:shrink w-[190px] lg:w-auto text-left rounded-sm border px-2 py-1.5 transition-colors ${
                active
                  ? "border-emerald-500/60 bg-emerald-500/10"
                  : "border-term-border bg-[#0b0f17] hover:border-zinc-600"
              }`}
              style={active ? undefined : { borderLeftColor: color, borderLeftWidth: 3 }}
            >
              <div className="flex items-center justify-between gap-1.5">
                <span className="text-[10.5px] font-semibold text-zinc-200 truncate">
                  {cp.name}
                </span>
                <span
                  className="shrink-0 text-[9px] font-bold tnum"
                  style={{ color: severityColor(cp.severity_score) }}
                >
                  {cp.severity_score}
                </span>
              </div>
              <div className="mt-0.5 flex items-center gap-1 text-[9px] uppercase tracking-wider text-zinc-500">
                <span style={{ color }}>{categoryLabel(cp.category)}</span>
                {cp.graph_crossref?.is_articulation && (
                  <span className="text-rose-400">· ⚠ SPOF</span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
