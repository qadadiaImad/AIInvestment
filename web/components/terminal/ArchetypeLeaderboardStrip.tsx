import Link from "next/link";
import type { ArchetypeKey, ArchetypeTopEntry } from "@/lib/archetypes";
import {
  ARCHETYPE_COLORS,
  ARCHETYPE_LABELS,
  ARCHETYPE_SUBTITLES,
  ARCHETYPE_ORDER,
  archetypeScoreTextClass,
} from "@/lib/format";

const SHOWN = 8; // of the up-to-15 entries in top[archetype]

function LeaderboardColumn({
  archetype,
  entries,
}: {
  archetype: ArchetypeKey;
  entries: ArchetypeTopEntry[];
}) {
  const accent = ARCHETYPE_COLORS[archetype];
  return (
    <div className="flex-1 min-w-[220px] flex flex-col gap-2 rounded-sm border border-term-border bg-[#0e131d] p-3">
      <div className="flex flex-col gap-0.5">
        <span
          className="text-[12px] font-bold uppercase tracking-wide"
          style={{ color: accent }}
        >
          {ARCHETYPE_LABELS[archetype]}
        </span>
        <span className="text-[9.5px] text-term-muted">
          {ARCHETYPE_SUBTITLES[archetype]} — top fits
        </span>
      </div>
      {entries.length === 0 ? (
        <span className="text-[10.5px] text-term-muted">No strong/partial fits yet.</span>
      ) : (
        <ol className="flex flex-col gap-1">
          {entries.slice(0, SHOWN).map((e, i) => (
            <li key={e.symbol} className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-1.5 min-w-0">
                <span className="text-[9.5px] text-term-muted tnum w-4 shrink-0">
                  {i + 1}
                </span>
                <Link
                  href={`/stocks/${e.symbol}`}
                  className="text-[11.5px] font-semibold text-zinc-200 hover:text-emerald-400 truncate"
                >
                  {e.symbol}
                </Link>
              </span>
              <span className={`text-[11px] tnum font-semibold ${archetypeScoreTextClass(e.score)}`}>
                {Math.round(e.score)}
              </span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

// Three side-by-side ranked lists (Graham/Buffett/Lynch), each pre-sorted
// upstream by archetypes.json's `top` block (score desc, strong/partial fit
// only, ties -> symbol asc). Purely presentational — no client-side
// resorting here, that's the sortable table below it.
export default function ArchetypeLeaderboardStrip({
  top,
}: {
  top: Record<ArchetypeKey, ArchetypeTopEntry[]>;
}) {
  return (
    <div className="flex flex-wrap gap-3">
      {ARCHETYPE_ORDER.map((key) => (
        <LeaderboardColumn key={key} archetype={key} entries={top[key] ?? []} />
      ))}
    </div>
  );
}
