"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { ScreenerRow } from "@/lib/data";
import type { HalalOverall } from "@/lib/halal";
import { overallLabel, overallTone } from "@/lib/halal";
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

// Optional sector tagging added by the merged AI + Quantum loader. AI-only data
// carries neither field, so both are optional and the UI degrades gracefully.
type SectorRow = ScreenerRow & {
  sector?: string | null;
  sectors?: string[] | null;
  // Foreign listings (Physical-AI bundle) quote price in local currency.
  currency?: string | null;
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

type SectorFilter = "All" | "AI" | "Quantum" | "PhysicalAI" | "Congress";

const SECTOR_FILTERS: SectorFilter[] = ["All", "AI", "Quantum", "PhysicalAI", "Congress"];

function sectorColor(s: string): string {
  return s === "Quantum" ? "#a855f7" : s === "PhysicalAI" ? "#22e07e" : s === "Congress" ? "#f59e0b" : "#22d3ee";
}

function SectorChip({ sectors }: { sectors: string[] }) {
  if (sectors.length === 0) return <span className="text-term-muted">{DASH}</span>;
  return (
    <span className="inline-flex gap-1 align-middle">
      {sectors.map((s) => {
        const color = sectorColor(s);
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

// Phone card list: rows revealed in pages of this size (mobile audit, 2026-09-25).
const PHONE_PAGE = 25;

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

// Tone -> inline style colors for the halal badge (mirrors existing SectorChip idiom).
const HALAL_TONE_COLOR: Record<string, string> = {
  pass: "#4ade80",   // emerald-400 — halal
  fail: "#f87171",   // red-400     — not_halal
  warn: "#facc15",   // yellow-400  — questionable
  muted: "#71717a",  // zinc-500    — insufficient_data
};

function HalalBadge({
  symbol,
  overall,
  asLink = true,
}: {
  symbol: string;
  overall: HalalOverall;
  asLink?: boolean;
}) {
  const tone = overallTone(overall);
  const color = HALAL_TONE_COLOR[tone] ?? HALAL_TONE_COLOR.muted;
  const cls = "inline-block px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm no-underline";
  const style = { color, border: `1px solid ${color}`, backgroundColor: `${color}1a` };
  // Inside the phone card (itself a link) a nested anchor is invalid HTML, so the
  // badge degrades to a span there.
  if (!asLink) {
    return (
      <span className={cls} style={style}>
        {overallLabel(overall)}
      </span>
    );
  }
  return (
    <Link
      href="/halal"
      title={`${symbol} halal screening — ${overallLabel(overall)}`}
      className={cls}
      style={style}
    >
      {overallLabel(overall)}
    </Link>
  );
}

function priceCell(r: SectorRow) {
  const ccy = r.currency && r.currency !== "USD" ? r.currency : null;
  return (
    <>
      {fmtPrice(r.price)}
      {ccy ? <span className="text-term-muted text-[9px] ml-1">{ccy}</span> : null}
    </>
  );
}

// One screener row as a phone card: identity on top, the two numbers a reader
// opens the screener for (price, 1-year move) large, four secondary metrics in
// a 2x2 grid. The whole card is the link to the stock sheet.
function RowCard({
  r,
  hasSectors,
  halal,
}: {
  r: SectorRow;
  hasSectors: boolean;
  halal?: Record<string, HalalOverall>;
}) {
  const p1y = signedPct(r.perf_1y);
  const rev = signedPct(r.rev_growth_yoy);
  const fdisc = signedPct(r.fundamental_discount_pct);
  const hasFdisc =
    typeof r.fundamental_discount_pct === "number" && Number.isFinite(r.fundamental_discount_pct);
  return (
    <li>
      <Link
        href={`/stocks/${r.symbol}`}
        className="block px-3 py-3 border-b border-term-border active:bg-[#11192680]"
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-[15px] font-bold text-emerald-400">{r.symbol}</span>
          <LayerChip layer={r.layer} />
          {hasSectors && <SectorChip sectors={rowSectors(r)} />}
          {halal && halal[r.symbol] ? (
            <HalalBadge symbol={r.symbol} overall={halal[r.symbol]} asLink={false} />
          ) : null}
          <span className="ml-auto text-term-muted text-[12px]">›</span>
        </div>
        <div className="mt-1.5 flex items-baseline justify-between gap-3">
          <span className="text-[17px] font-semibold tnum">{priceCell(r)}</span>
          <span className={`text-[15px] font-semibold tnum ${p1y.cls}`}>
            {p1y.text} <span className="text-[10px] font-normal text-term-muted">1Y</span>
          </span>
        </div>
        <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-[12px]">
          <div className="flex justify-between">
            <dt className="text-term-muted">P/E</dt>
            <dd className="tnum">{ratio(r.pe, 1)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-term-muted">vs value</dt>
            <dd className={`tnum ${hasFdisc ? fdisc.cls : ""}`}>{hasFdisc ? fdisc.text : DASH}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-term-muted">Net margin</dt>
            <dd className="tnum">{pct(r.net_margin)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-term-muted">Rev YoY</dt>
            <dd className={`tnum ${rev.cls}`}>{rev.text}</dd>
          </div>
        </dl>
        {r.next_catalyst ? (
          <div className="mt-1.5 text-[11px] text-term-muted">
            Next catalyst {dateOnly(r.next_catalyst)}
          </div>
        ) : null}
      </Link>
    </li>
  );
}

export default function ScreenerTable({
  rows,
  caption,
  halal,
  compact = false,
}: {
  rows: ScreenerRow[];
  caption?: string;
  halal?: Record<string, HalalOverall>;
  // Preview mode (home page): no sector filter, no phone sort control.
  compact?: boolean;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("perf_1y");
  const [dir, setDir] = useState<Dir>("desc");
  const [sectorFilter, setSectorFilter] = useState<SectorFilter>("All");
  const [phoneShown, setPhoneShown] = useState(PHONE_PAGE);

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

  function selectSort(key: SortKey) {
    setSortKey(key);
    const col = COLS.find((c) => c.key === key);
    setDir(col?.num ? "desc" : "asc");
    setPhoneShown(PHONE_PAGE);
  }

  const arrow = (key: SortKey) =>
    key === sortKey ? (dir === "asc" ? " ▲" : " ▼") : "";

  const phoneRows = sorted.slice(0, phoneShown);

  return (
    <div className="flex flex-col gap-2">
      {hasSectors && !compact && (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[10px] uppercase tracking-wider text-term-muted">
            Sector
          </span>
          <div className="inline-flex flex-wrap border border-term-border rounded-sm overflow-hidden">
            {SECTOR_FILTERS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => {
                  setSectorFilter(s);
                  setPhoneShown(PHONE_PAGE);
                }}
                aria-pressed={sectorFilter === s}
                className={`px-2 py-px max-sm:min-h-[40px] max-sm:px-3 text-[10.5px] font-semibold uppercase tracking-wider ${
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

      {/* Phone: sort control + card list. The table below is hidden under sm. */}
      <div className="sm:hidden flex flex-col gap-2">
        {!compact && (
        <div className="flex items-center gap-2">
          <label className="text-[10px] uppercase tracking-wider text-term-muted" htmlFor="screener-sort">
            Sort
          </label>
          <select
            id="screener-sort"
            value={sortKey}
            onChange={(e) => selectSort(e.target.value as SortKey)}
            className="min-h-[44px] flex-1 bg-term-panel border border-term-border rounded-sm px-2 text-[12px] text-zinc-200"
          >
            {COLS.map((c) => (
              <option key={c.key} value={c.key}>
                {c.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => setDir((d) => (d === "asc" ? "desc" : "asc"))}
            aria-label={dir === "asc" ? "Sorted ascending, tap for descending" : "Sorted descending, tap for ascending"}
            className="min-h-[44px] min-w-[44px] border border-term-border rounded-sm text-emerald-400 text-[14px]"
          >
            {dir === "asc" ? "▲" : "▼"}
          </button>
        </div>
        )}
        <ul className="border border-term-border rounded-sm">
          {phoneRows.map((r) => (
            <RowCard key={r.symbol} r={r as SectorRow} hasSectors={hasSectors} halal={halal} />
          ))}
        </ul>
        {sorted.length > phoneShown ? (
          <button
            type="button"
            onClick={() => setPhoneShown((n) => n + PHONE_PAGE)}
            className="min-h-[44px] border border-term-border rounded-sm text-[11px] uppercase tracking-wider text-term-muted"
          >
            Show {Math.min(PHONE_PAGE, sorted.length - phoneShown)} more · {sorted.length - phoneShown} left
          </button>
        ) : null}
      </div>

      {/* Desktop: the dense sortable table. First column stays put while the
          rest scrolls sideways on narrow desktops/tablets. */}
      <div className="hidden sm:block overflow-x-auto border border-term-border rounded-sm">
      <table className="term">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead className="bg-[#0e131d] sticky top-0 z-10">
          <tr>
            {COLS.map((c, i) => (
              <th
                key={c.key}
                className={`cursor-pointer hover:text-zinc-200 ${
                  c.num ? "numcell" : ""
                } ${i === 0 ? "sticky left-0 z-20 bg-[#0e131d]" : ""}`}
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
            {halal && <th>Halal</th>}
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
                <td className="sticky left-0 bg-[#0b0f17]">
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
                <td className="numcell tnum">{priceCell(r as SectorRow)}</td>
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
                {halal && (
                  <td>
                    {halal[r.symbol] ? (
                      <HalalBadge symbol={r.symbol} overall={halal[r.symbol]} />
                    ) : (
                      <span className="text-term-muted">{DASH}</span>
                    )}
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
