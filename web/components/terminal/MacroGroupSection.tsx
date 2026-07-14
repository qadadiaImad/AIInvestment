import type { MacroGroup, MacroSeries } from "@/lib/macro";
import { MACRO_GROUP_COLORS, MACRO_GROUP_LABELS } from "@/lib/format";
import MacroPanel from "@/components/terminal/MacroPanel";

// Clone of GroupSection.tsx, retargeted at MacroSeries. grid-cols-1
// sm:grid-cols-2 lg:grid-cols-3 — one fewer tier than GroupSection's FX
// tiles, since a macro panel carries a full sparkline + longer display name
// and needs more width.
export default function MacroGroupSection({
  group,
  series,
}: {
  group: MacroGroup;
  series: MacroSeries[];
}) {
  if (series.length === 0) return null;
  const color = MACRO_GROUP_COLORS[group] ?? "#6b7280";
  return (
    <section className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span
          className="inline-block w-1.5 h-1.5 rounded-full"
          style={{ backgroundColor: color }}
          aria-hidden="true"
        />
        <h2 className="text-[10.5px] font-semibold uppercase tracking-wider text-term-muted">
          {MACRO_GROUP_LABELS[group] ?? group}
        </h2>
        <span className="text-[10px] text-term-muted">{series.length}</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {series.map((s) => (
          <MacroPanel key={s.series_id} series={s} />
        ))}
      </div>
    </section>
  );
}
