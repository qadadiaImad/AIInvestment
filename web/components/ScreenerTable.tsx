"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { ScreenerRow } from "@/lib/data";
import LayerChip from "@/components/LayerChip";

// Optional sector tagging added by the merged AI + Quantum loader. AI-only data
// carries neither field, so both are optional and the UI degrades gracefully.
type SectorRow = ScreenerRow & {
  sector?: string | null;
  sectors?: string[] | null;
};

// Normalize a row to the set of sectors it belongs to (deduped, order-stable).
function rowSectors(r: SectorRow): string[] {
  const out: string[] = [];
  if (Array.isArray(r.sectors)) {
    for (const s of r.sectors) {
      if (s && !out.includes(s)) out.push(s);
    }
  }
  if (r.sector && !out.includes(r.sector)) out.push(r.sector);
  return out;
}

type SectorFilter = "All" | "AI" | "Quantum";

const SECTOR_FILTERS: SectorFilter[] = ["All", "AI", "Quantum"];

function SectorChip({ sectors }: { sectors: string[] }) {
  if (sectors.length === 0) return <span className="text-term-muted">{DASH}</span>;
  return (
    <span className="inline-flex gap-1 align-middle">
      {sectors.map((s) => {
        const color = s === "Quantum" ? "#a855f7" : "#22d3ee";
        return (
          <span
            key={s}
            className="inline-block px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm"
            style={{
              color,
              border: `1px solid ${color}`,
              backgroundColor: `${color}1a`,
            }}
          >
            {s}
          </span>
        );
      })}
    </span>
  );
}
import {
  price as fmtPrice,
  ratio,
  pct,
  signedPct,
  dateOnly,
  DASH,
  LAYER_ORDER,
} from "@/lib/format";

type SortKey =
  | "symbol"
  | "layer"
  | "price"
  | "pe"
  | "net_margin"
  | "roe"
  | "rev_growth_yoy"
  | "perf_1y"
  | "ret_1y"
  | "ret_5y"
  | "fundamental_value"
  | "fundamental_discount_pct"
  | "next_catalyst";

type Dir = "asc" | "desc";

const COLS: { key: SortKey; label: string; num: boolean }[] = [
  { key: "symbol", label: "Symbol", num: false },
  { key: "layer", label: "Layer", num: false },
  { key: "price", label: "Price", num: true },
  { key: "pe", label: "P/E", num: true },
  { key: "net_margin", label: "Net margin", num: true },
  { key: "roe", label: "ROE", num: true },
  { key: "rev_growth_yoy", label: "Rev YoY", num: true },
  { key: "perf_1y", label: "1Y", num: true },
  { key: "ret_1y", label: "1Y %", num: true },
  { key: "ret_5y", label: "5Y %", num: true },
  { key: "fundamental_value", label: "Fund. val", num: true },
  { key: "fundamental_discount_pct", label: "vs Price %", num: true },
  { key: "next_catalyst", label: "Next catalyst", num: false },
];

function cmp(a: ScreenerRow, b: ScreenerRow, key: SortKey): number {
  if (key === "symbol") return a.symbol.localeCompare(b.symbol);
  if (key === "layer") {
    return LAYER_ORDER.indexOf(a.layer) - LAYER_ORDER.indexOf(b.layer);
  }
  if (key === "next_catalyst") {
    const av = a.next_catalyst ?? "";
    const bv = b.next_catalyst ?? "";
    return av.localeCompare(bv);
  }
  const av = a[key];
  const bv = b[key];
  const an = typeof av === "number" && Number.isFinite(av);
  const bn = typeof bv === "number" && Number.isFinite(bv);
  if (!an && !bn) return 0;
  if (!an) return 1; // nulls last
  if (!bn) return -1;
  return (av as number) - (bv as number);
}

export default function ScreenerTable({
  rows,
  caption,
}: {
  rows: ScreenerRow[];
  caption?: string;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("perf_1y");
  const [dir, setDir] = useState<Dir>("desc");
  const [sectorFilter, setSectorFilter] = useState<SectorFilter>("All");

  // Sector tagging only exists once Quantum data is merged in. If no row carries
  // a sector, hide the filter control and the chip column entirely.
  const hasSectors = useMemo(
    () => (rows as SectorRow[]).some((r) => rowSectors(r).length > 0),
    [rows],
  );

  const filtered = useMemo(() => {
    if (!hasSectors || sectorFilter === "All") return rows;
    return (rows as SectorRow[]).filter((r) =>
      rowSectors(r).includes(sectorFilter),
    );
  }, [rows, hasSectors, sectorFilter]);

  const sorted = useMemo(() => {
    const out = [...filtered].sort((a, b) => cmp(a, b, sortKey));
    if (dir === "desc") out.reverse();
    return out;
  }, [filtered, sortKey, dir]);

  function onSort(key: SortKey) {
    if (key === sortKey) {
      setDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      // numeric defaults desc, text asc
      const col = COLS.find((c) => c.key === key);
      setDir(col?.num ? "desc" : "asc");
    }
  }

  const arrow = (key: SortKey) =>
    key === sortKey ? (dir === "asc" ? " ▲" : " ▼") : "";

  return (
    <div className="flex flex-col gap-2">
      {hasSectors && (
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] uppercase tracking-wider text-term-muted">
            Sector
          </span>
          <div className="inline-flex border border-term-border rounded-sm overflow-hidden">
            {SECTOR_FILTERS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSectorFilter(s)}
                aria-pressed={sectorFilter === s}
                className={`px-2 py-px text-[10.5px] font-semibold uppercase tracking-wider ${
                  sectorFilter === s
                    ? "bg-emerald-500/20 text-emerald-300"
                    : "text-term-muted hover:text-zinc-200"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
          <span className="text-[10px] text-term-muted">
            {sorted.length} of {rows.length}
          </span>
        </div>
      )}
      <div className="overflow-x-auto border border-term-border rounded-sm">
      <table className="term">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead className="bg-[#0e131d] sticky top-0 z-10">
          <tr>
            {COLS.map((c) => (
              <th
                key={c.key}
                className={`cursor-pointer hover:text-zinc-200 ${
                  c.num ? "numcell" : ""
                }`}
                onClick={() => onSort(c.key)}
                aria-sort={
                  c.key === sortKey
                    ? dir === "asc"
                      ? "ascending"
                      : "descending"
                    : "none"
                }
              >
                {c.label}
                <span className="text-emerald-400">{arrow(c.key)}</span>
              </th>
            ))}
            {hasSectors && <th>Sector</th>}
          </tr>
        </thead>
        <tbody>
          {sorted.map((r) => {
            const p1y = signedPct(r.perf_1y);
            const ret1 = signedPct(r.ret_1y);
            const ret5 = signedPct(r.ret_5y);
            const hasRet1 =
              typeof r.ret_1y === "number" && Number.isFinite(r.ret_1y);
            const hasRet5 =
              typeof r.ret_5y === "number" && Number.isFinite(r.ret_5y);
            const rev = signedPct(r.rev_growth_yoy);
            const fdisc = signedPct(r.fundamental_discount_pct);
            const hasFdisc =
              typeof r.fundamental_discount_pct === "number" &&
              Number.isFinite(r.fundamental_discount_pct);
            return (
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
                <td className="numcell tnum">{fmtPrice(r.price)}</td>
                <td className="numcell tnum">{ratio(r.pe, 1)}</td>
                <td className="numcell tnum">{pct(r.net_margin)}</td>
                <td className="numcell tnum">{pct(r.roe)}</td>
                <td className={`numcell tnum ${rev.cls}`}>{rev.text}</td>
                <td className={`numcell tnum ${p1y.cls}`}>{p1y.text}</td>
                <td className={`numcell tnum ${hasRet1 ? ret1.cls : ""}`}>
                  {hasRet1 ? ret1.text : DASH}
                </td>
                <td className={`numcell tnum ${hasRet5 ? ret5.cls : ""}`}>
                  {hasRet5 ? ret5.text : DASH}
                </td>
                <td className="numcell tnum">{fmtPrice(r.fundamental_value)}</td>
                <td className={`numcell tnum ${hasFdisc ? fdisc.cls : ""}`}>
                  {hasFdisc ? fdisc.text : DASH}
                </td>
                <td className="tnum text-term-muted">
                  {r.next_catalyst ? dateOnly(r.next_catalyst) : DASH}
                </td>
                {hasSectors && (
                  <td>
                    <SectorChip sectors={rowSectors(r as SectorRow)} />
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
      </div>
    </div>
  );
}
