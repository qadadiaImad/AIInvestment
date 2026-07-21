"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { HalalVerdict, HalalOverall } from "@/lib/halal";
import { overallLabel, overallTone, fmtRatioPct } from "@/lib/halal";
import LayerChip from "@/components/LayerChip";
import { DASH, LAYER_ORDER } from "@/lib/format";

// ---- Types ----------------------------------------------------------------

type OverallFilter =
  | "All"
  | "Halal"
  | "Not halal"
  | "Questionable"
  | "Insufficient data";

const OVERALL_FILTERS: OverallFilter[] = [
  "All",
  "Halal",
  "Not halal",
  "Questionable",
  "Insufficient data",
];

const OVERALL_TO_KEY: Record<OverallFilter, HalalOverall | null> = {
  All: null,
  Halal: "halal",
  "Not halal": "not_halal",
  Questionable: "questionable",
  "Insufficient data": "insufficient_data",
};

// ---- Badge helpers --------------------------------------------------------

function OverallBadge({ overall }: { overall: HalalOverall }) {
  const tone = overallTone(overall);
  const label = overallLabel(overall);
  const colors: Record<string, { fg: string; border: string; bg: string }> = {
    pass: { fg: "#10b981", border: "#10b981", bg: "#10b9811a" },
    fail: { fg: "#ef4444", border: "#ef4444", bg: "#ef44441a" },
    warn: { fg: "#f59e0b", border: "#f59e0b", bg: "#f59e0b1a" },
    muted: { fg: "#6b7280", border: "#6b7280", bg: "#6b72801a" },
  };
  const c = colors[tone];
  return (
    <span
      className="inline-block px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm whitespace-nowrap"
      style={{ color: c.fg, border: `1px solid ${c.border}`, backgroundColor: c.bg }}
    >
      {label}
    </span>
  );
}

function StatusChip({
  status,
  label,
}: {
  status: "pass" | "fail" | "unknown";
  label: string;
}) {
  const colors: Record<string, { fg: string; border: string; bg: string }> = {
    pass: { fg: "#10b981", border: "#10b981", bg: "#10b9811a" },
    fail: { fg: "#ef4444", border: "#ef4444", bg: "#ef44441a" },
    unknown: { fg: "#6b7280", border: "#6b7280", bg: "#6b72801a" },
  };
  const c = colors[status] ?? colors.unknown;
  return (
    <span
      className="inline-block px-1 py-px text-[8.5px] font-semibold uppercase tracking-wider rounded-sm"
      style={{ color: c.fg, border: `1px solid ${c.border}`, backgroundColor: c.bg }}
    >
      {label}
    </span>
  );
}

// ---- Margin bar ----------------------------------------------------------
// Shows AAOIFI debt-ratio margin: positive (room left) = green bar;
// negative (over threshold) = red bar. Bar is proportional to ±30% range.

function MarginBar({ verdict }: { verdict: HalalVerdict }) {
  const aaoifi = verdict.standards["AAOIFI"];
  const debtTest = aaoifi?.tests?.find((t) => t.id === "aaoifi_debt");
  if (!debtTest || debtTest.margin === null) {
    return <span className="text-term-muted text-[10px]">{DASH}</span>;
  }
  const margin = debtTest.margin;
  const ratio = debtTest.ratio;
  const threshold = debtTest.threshold;
  // Cap bar at ±threshold width
  const barPct = Math.min(Math.abs(margin) / threshold, 1) * 100;
  const isPass = margin >= 0;
  return (
    <div className="flex items-center gap-1 min-w-[80px]">
      <div className="flex-1 h-1.5 bg-term-border rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{
            width: `${barPct}%`,
            backgroundColor: isPass ? "#10b981" : "#ef4444",
          }}
        />
      </div>
      <span
        className={`text-[9.5px] tnum font-mono ${isPass ? "text-emerald-400" : "text-red-400"}`}
      >
        {fmtRatioPct(ratio)}
      </span>
    </div>
  );
}

// ---- Sort ----------------------------------------------------------------

type SortKey = "symbol" | "layer" | "overall" | "aaoifi_margin";
type Dir = "asc" | "desc";

const OVERALL_ORDER: HalalOverall[] = [
  "halal",
  "questionable",
  "insufficient_data",
  "not_halal",
];

function cmp(
  a: HalalVerdict,
  b: HalalVerdict,
  key: SortKey,
): number {
  if (key === "symbol") return a.symbol.localeCompare(b.symbol);
  if (key === "layer") {
    const ai = LAYER_ORDER.indexOf(a.layer ?? "");
    const bi = LAYER_ORDER.indexOf(b.layer ?? "");
    const av = ai === -1 ? 999 : ai;
    const bv = bi === -1 ? 999 : bi;
    return av - bv;
  }
  if (key === "overall") {
    return OVERALL_ORDER.indexOf(a.overall) - OVERALL_ORDER.indexOf(b.overall);
  }
  if (key === "aaoifi_margin") {
    const am =
      a.standards["AAOIFI"]?.tests?.find((t) => t.id === "aaoifi_debt")
        ?.margin ?? null;
    const bm =
      b.standards["AAOIFI"]?.tests?.find((t) => t.id === "aaoifi_debt")
        ?.margin ?? null;
    if (am === null && bm === null) return 0;
    if (am === null) return 1;
    if (bm === null) return -1;
    return am - bm;
  }
  return 0;
}

// ---- Layer dropdown -------------------------------------------------------

function layerOptions(verdicts: HalalVerdict[]): string[] {
  const seen = new Set<string>();
  for (const v of verdicts) {
    if (v.layer) seen.add(v.layer);
  }
  return ["All", ...LAYER_ORDER.filter((l) => seen.has(l)), ...
    [...seen].filter((l) => !LAYER_ORDER.includes(l)).sort()];
}

// ---- Date age badge -------------------------------------------------------

function AgeBadge({ iso }: { iso: string | null }) {
  if (!iso) return <span className="text-term-muted">{DASH}</span>;
  // Show just the date part
  const date = iso.split("T")[0] ?? iso;
  return <span className="text-[9.5px] tnum text-term-muted">{date}</span>;
}

// ---- Main component -------------------------------------------------------

export default function HalalTable({
  verdicts,
}: {
  verdicts: HalalVerdict[];
}) {
  const [overallFilter, setOverallFilter] = useState<OverallFilter>("All");
  const [layerFilter, setLayerFilter] = useState<string>("All");
  const [sortKey, setSortKey] = useState<SortKey>("overall");
  const [dir, setDir] = useState<Dir>("asc");

  const layers = useMemo(() => layerOptions(verdicts), [verdicts]);

  const filtered = useMemo(() => {
    let rows = verdicts;
    const oKey = OVERALL_TO_KEY[overallFilter];
    if (oKey !== null) {
      rows = rows.filter((v) => v.overall === oKey);
    }
    if (layerFilter !== "All") {
      rows = rows.filter((v) => v.layer === layerFilter);
    }
    return rows;
  }, [verdicts, overallFilter, layerFilter]);

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
      setDir(key === "aaoifi_margin" ? "desc" : "asc");
    }
  }

  const arrow = (key: SortKey) =>
    key === sortKey ? (dir === "asc" ? " ▲" : " ▼") : "";

  return (
    <div className="flex flex-col gap-2">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Overall filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] uppercase tracking-wider text-term-muted">
            Verdict
          </span>
          <div className="inline-flex border border-term-border rounded-sm overflow-hidden">
            {OVERALL_FILTERS.map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setOverallFilter(f)}
                aria-pressed={overallFilter === f}
                className={`px-2 py-px text-[10px] font-semibold uppercase tracking-wider ${
                  overallFilter === f
                    ? "bg-emerald-500/20 text-emerald-300"
                    : "text-term-muted hover:text-zinc-200"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
        {/* Layer filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] uppercase tracking-wider text-term-muted">
            Layer
          </span>
          <select
            value={layerFilter}
            onChange={(e) => setLayerFilter(e.target.value)}
            className="bg-[#0e131d] border border-term-border rounded-sm text-[10px] text-zinc-200 px-1.5 py-px"
          >
            {layers.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </div>
        <span className="text-[10px] text-term-muted">
          {sorted.length} of {verdicts.length}
        </span>
      </div>

      {/* Legend */}
      <p className="text-[9.5px] text-term-muted leading-snug">
        Halal = passes all ratio and activity screens under the selected
        standard. Not halal = fails one or more screens. Questionable =
        scholar-split or indeterminate business activity; it takes precedence
        over passing or failing ratios. Insufficient data = missing inputs.
      </p>

      {/* Table */}
      <div className="overflow-x-auto border border-term-border rounded-sm">
        <table className="term">
          <caption className="sr-only">Halal screening results</caption>
          <thead className="bg-[#0e131d] sticky top-0 z-10">
            <tr>
              <th
                className="cursor-pointer hover:text-zinc-200"
                onClick={() => onSort("symbol")}
                aria-sort={
                  sortKey === "symbol"
                    ? dir === "asc"
                      ? "ascending"
                      : "descending"
                    : "none"
                }
              >
                Symbol<span className="text-emerald-400">{arrow("symbol")}</span>
              </th>
              <th
                className="cursor-pointer hover:text-zinc-200"
                onClick={() => onSort("layer")}
                aria-sort={
                  sortKey === "layer"
                    ? dir === "asc"
                      ? "ascending"
                      : "descending"
                    : "none"
                }
              >
                Layer<span className="text-emerald-400">{arrow("layer")}</span>
              </th>
              <th
                className="cursor-pointer hover:text-zinc-200"
                onClick={() => onSort("overall")}
                aria-sort={
                  sortKey === "overall"
                    ? dir === "asc"
                      ? "ascending"
                      : "descending"
                    : "none"
                }
              >
                Overall<span className="text-emerald-400">{arrow("overall")}</span>
              </th>
              <th>AAOIFI</th>
              <th>FTSE</th>
              <th>MSCI</th>
              <th>S&amp;P</th>
              <th>DJIM</th>
              <th>Business</th>
              <th
                className="cursor-pointer hover:text-zinc-200"
                onClick={() => onSort("aaoifi_margin")}
                aria-sort={
                  sortKey === "aaoifi_margin"
                    ? dir === "asc"
                      ? "ascending"
                      : "descending"
                    : "none"
                }
              >
                AAOIFI debt{" "}
                <span className="text-emerald-400">{arrow("aaoifi_margin")}</span>
              </th>
              <th>Data as of</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((v) => {
              const aaoifiStatus =
                (v.standards["AAOIFI"]?.status ?? "unknown") as
                  | "pass"
                  | "fail"
                  | "unknown";
              const ftseStatus =
                (v.standards["FTSE"]?.status ?? "unknown") as
                  | "pass"
                  | "fail"
                  | "unknown";
              const msciStatus =
                (v.standards["MSCI"]?.status ?? "unknown") as
                  | "pass"
                  | "fail"
                  | "unknown";
              const spStatus =
                (v.standards["SP"]?.status ?? "unknown") as
                  | "pass"
                  | "fail"
                  | "unknown";
              const djimStatus =
                (v.standards["DJIM"]?.status ?? "unknown") as
                  | "pass"
                  | "fail"
                  | "unknown";
              const bizStatus = v.business?.status ?? "unknown";
              return (
                <tr key={v.symbol}>
                  <td>
                    <Link
                      href={`/stocks/${v.symbol}`}
                      className="font-semibold text-emerald-400 hover:text-emerald-300"
                    >
                      {v.symbol}
                    </Link>
                  </td>
                  <td>
                    <LayerChip layer={v.layer} />
                  </td>
                  <td>
                    <OverallBadge overall={v.overall} />
                  </td>
                  <td>
                    <StatusChip status={aaoifiStatus} label={aaoifiStatus} />
                  </td>
                  <td>
                    <StatusChip status={ftseStatus} label={ftseStatus} />
                  </td>
                  <td>
                    <StatusChip status={msciStatus} label={msciStatus} />
                  </td>
                  <td>
                    <StatusChip status={spStatus} label={spStatus} />
                  </td>
                  <td>
                    <StatusChip status={djimStatus} label={djimStatus} />
                  </td>
                  <td>
                    <span
                      className={`text-[10px] font-medium ${
                        bizStatus === "clean"
                          ? "text-emerald-400"
                          : bizStatus === "prohibited"
                            ? "text-red-400"
                            : bizStatus === "questionable"
                              ? "text-amber-400"
                              : "text-term-muted"
                      }`}
                    >
                      {bizStatus}
                    </span>
                  </td>
                  <td>
                    <MarginBar verdict={v} />
                  </td>
                  <td>
                    <AgeBadge iso={v.inputs_asof} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
