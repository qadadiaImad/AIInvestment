"use client";

import { useState } from "react";
import type { Chokepoint, ChokepointCategory, ChokepointsData } from "@/lib/chokepoints";
import { categoryColor, categoryLabel, groupByCategory } from "@/lib/chokepoints";
import ChokepointCard from "@/components/ChokepointCard";

// Category filter pills + card grid, grouped by category (severity-descending
// within each group via groupByCategory()). Client component only for the
// filter interaction — the data itself is server-fetched and passed down.
export default function ChokepointBoard({
  data,
  knownSymbols,
}: {
  data: ChokepointsData;
  knownSymbols: string[];
}) {
  const [filter, setFilter] = useState<ChokepointCategory | "all">("all");
  const groups = groupByCategory(data);
  const symbolSet = new Set(knownSymbols);

  const visibleGroups =
    filter === "all" ? groups : groups.filter((g) => g.category === filter);

  return (
    <div className="flex flex-col gap-4">
      {/* category filter pills */}
      <div className="flex flex-wrap gap-1.5">
        <button
          type="button"
          onClick={() => setFilter("all")}
          className={`px-2 py-1 text-[10.5px] uppercase tracking-wider rounded-sm border transition-colors ${
            filter === "all"
              ? "border-emerald-500/60 bg-emerald-500/15 text-emerald-300"
              : "border-term-border text-zinc-400 hover:text-zinc-200"
          }`}
        >
          All ({data.summary.n_entries})
        </button>
        {groups.map((g) => {
          const color = categoryColor(g.category);
          const active = filter === g.category;
          return (
            <button
              key={g.category}
              type="button"
              onClick={() => setFilter(active ? "all" : g.category)}
              className={`px-2 py-1 text-[10.5px] uppercase tracking-wider rounded-sm border transition-colors ${
                active ? "" : "border-term-border text-zinc-400 hover:text-zinc-200"
              }`}
              style={active ? { borderColor: color, backgroundColor: `${color}26`, color } : undefined}
            >
              {categoryLabel(g.category)} ({g.items.length})
            </button>
          );
        })}
      </div>

      {/* card grid, grouped by category */}
      <div className="flex flex-col gap-6">
        {visibleGroups.map((g) => (
          <section key={g.category}>
            <h2 className="text-[13px] font-semibold uppercase tracking-wider text-zinc-300 mb-2 flex items-center gap-2">
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: categoryColor(g.category) }}
              />
              {categoryLabel(g.category)}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {g.items.map((cp: Chokepoint) => (
                <ChokepointCard key={cp.id} cp={cp} knownSymbols={symbolSet} />
              ))}
            </div>
          </section>
        ))}
        {visibleGroups.length === 0 && (
          <p className="text-[11px] text-term-muted">No chokepoints in this category.</p>
        )}
      </div>
    </div>
  );
}
