"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { ArchetypeKey, ArchetypeStockRecord } from "@/lib/archetypes";
import LayerChip from "@/components/LayerChip";
import {
  ARCHETYPE_LABELS,
  ARCHETYPE_ORDER,
  DASH,
  archetypeScoreTextClass,
  archetypeVerdictLabel,
  LAYER_ORDER,
} from "@/lib/format";

type SortKey = "symbol" | "layer" | "graham" | "buffett" | "lynch";
type Dir = "asc" | "desc";

const COLS: { key: SortKey; label: string; num: boolean }[] = [
  { key: "symbol", label: "Symbol", num: false },
  { key: "layer", label: "Layer", num: false },
  { key: "graham", label: "Graham", num: true },
  { key: "buffett", label: "Buffett", num: true },
  { key: "lynch", label: "Lynch", num: true },
];

function scoreOf(r: ArchetypeStockRecord, key: ArchetypeKey): number | null {
  return r.archetypes[key]?.score ?? null;
}

function cmp(a: ArchetypeStockRecord, b: ArchetypeStockRecord, key: SortKey): number {
  if (key === "symbol") return a.symbol.localeCompare(b.symbol);
  if (key === "layer") return LAYER_ORDER.indexOf(a.layer) - LAYER_ORDER.indexOf(b.layer);
  const av = scoreOf(a, key);
  const bv = scoreOf(b, key);
  const an = typeof av === "number" && Number.isFinite(av);
  const bn = typeof bv === "number" && Number.isFinite(bv);
  if (!an && !bn) return 0;
  if (!an) return 1; // nulls (not_evaluable) last
  if (!bn) return -1;
  return (av as number) - (bv as number);
}

function ScoreCell({ rec, archetype }: { rec: ArchetypeStockRecord; archetype: ArchetypeKey }) {
  const card = rec.archetypes[archetype];
  if (!card) return <td className="numcell tnum text-term-muted">{DASH}</td>;
  return (
    <td className="numcell tnum">
      <span className={`font-semibold ${archetypeScoreTextClass(card.score)}`}>
        {card.score != null ? Math.round(card.score) : DASH}
      </span>
      <span className="text-term-muted"> · {archetypeVerdictLabel(card.verdict)}</span>
    </td>
  );
}

// Client component (sort state) — same shape/conventions as ScreenerTable.tsx
// (site-wide fundamentals screener). Sorts the FULL universe from
// archetypes.json's per_stock array; the leaderboard strip above it stays a
// separate, non-resortable component (pre-ranked top-N per archetype).
export default function ArchetypeScreenerTable({
  rows,
}: {
  rows: ArchetypeStockRecord[];
}) {
  const [sortKey, setSortKey] = useState<SortKey>("graham");
  const [dir, setDir] = useState<Dir>("desc");

  const sorted = useMemo(() => {
    const out = [...rows].sort((a, b) => cmp(a, b, sortKey));
    if (dir === "desc") out.reverse();
    return out;
  }, [rows, sortKey, dir]);

  function onSort(key: SortKey) {
    if (key === sortKey) {
      setDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      const col = COLS.find((c) => c.key === key);
      setDir(col?.num ? "desc" : "asc");
    }
  }

  const arrow = (key: SortKey) => (key === sortKey ? (dir === "asc" ? " ▲" : " ▼") : "");

  return (
    <div className="overflow-x-auto border border-term-border rounded-sm">
      <table className="term">
        <caption className="sr-only">Investor archetype scorecards — full universe</caption>
        <thead className="bg-[#0e131d] sticky top-0 z-10">
          <tr>
            {COLS.map((c) => (
              <th
                key={c.key}
                className={`cursor-pointer hover:text-zinc-200 ${c.num ? "numcell" : ""}`}
                onClick={() => onSort(c.key)}
                aria-sort={c.key === sortKey ? (dir === "asc" ? "ascending" : "descending") : "none"}
              >
                {c.key in ARCHETYPE_LABELS ? ARCHETYPE_LABELS[c.key as ArchetypeKey] : c.label}
                <span className="text-emerald-400">{arrow(c.key)}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((r) => (
            <tr key={r.symbol}>
              <td>
                <Link
                  href={`/stocks/${r.symbol}`}
                  className="font-semibold text-emerald-400 hover:text-emerald-300"
                >
                  {r.symbol}
                </Link>
              </td>
              <td>
                <LayerChip layer={r.layer} />
              </td>
              {ARCHETYPE_ORDER.map((key) => (
                <ScoreCell key={key} rec={r} archetype={key} />
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
