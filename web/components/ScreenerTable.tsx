"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { ScreenerRow } from "@/lib/data";
import LayerChip from "@/components/LayerChip";
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
      // numeric defaults desc, text asc
      const col = COLS.find((c) => c.key === key);
      setDir(col?.num ? "desc" : "asc");
    }
  }

  const arrow = (key: SortKey) =>
    key === sortKey ? (dir === "asc" ? " ▲" : " ▼") : "";

  return (
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
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
