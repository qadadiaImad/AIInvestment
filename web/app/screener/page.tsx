import type { Metadata } from "next";
import { getSiteData } from "@/lib/data";
import ScreenerTable from "@/components/ScreenerTable";

export const metadata: Metadata = {
  title: "Screener · AI STACK",
  description:
    "Sortable fundamentals screener across the AI value chain. Educational research only — not financial advice.",
};

export default function ScreenerPage() {
  const data = getSiteData();

  // Detect whether the merged dataset includes any Quantum-tagged rows.
  const hasQuantum = data.screener.some((r) => {
    const row = r as typeof r & { sector?: string | null; sectors?: string[] | null };
    return (
      row.sector === "Quantum" ||
      (Array.isArray(row.sectors) && row.sectors.includes("Quantum"))
    );
  });
  const scopeLabel = hasQuantum ? "AI + Quantum" : "AI";

  return (
    <div className="flex flex-col px-3 py-3 gap-2">
      <div className="flex items-center justify-between">
        <h1 className="text-[12px] font-semibold uppercase tracking-wider text-zinc-300">
          {scopeLabel} Screener — {data.screener.length} names
        </h1>
        <span className="text-[10.5px] text-term-muted">
          Click any column header to sort · click a symbol for the full sheet
        </span>
      </div>
      <ScreenerTable
        rows={data.screener}
        caption={`${scopeLabel} screener`}
      />
      <p className="text-[10px] text-term-muted mt-1">
        Metrics are date-stamped point-in-time figures derived from public
        sources and decay over time. Null values render as —.
      </p>
    </div>
  );
}
