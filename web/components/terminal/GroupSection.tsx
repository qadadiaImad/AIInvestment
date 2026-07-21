import type { TaGroup, TaInstrument } from "@/lib/ta";
import { TA_GROUP_COLORS, TA_GROUP_LABELS } from "@/lib/format";
import InstrumentTile from "@/components/terminal/InstrumentTile";

export default function GroupSection({
  group,
  instruments,
}: {
  group: TaGroup;
  instruments: TaInstrument[];
}) {
  if (instruments.length === 0) return null;
  const color = TA_GROUP_COLORS[group] ?? "#6b7280";
  return (
    <section className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span
          className="inline-block w-1.5 h-1.5 rounded-full"
          style={{ backgroundColor: color }}
          aria-hidden="true"
        />
        <h2 className="text-[10.5px] font-semibold uppercase tracking-wider text-term-muted">
          {TA_GROUP_LABELS[group] ?? group}
        </h2>
        <span className="text-[10px] text-term-muted">
          {instruments.length}
        </span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
        {instruments.map((inst) => (
          <InstrumentTile key={inst.symbol} instrument={inst} />
        ))}
      </div>
    </section>
  );
}
