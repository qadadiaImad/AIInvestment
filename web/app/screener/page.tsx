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
  return (
    <div className="flex flex-col px-3 py-3 gap-2">
      <div className="flex items-center justify-between">
        <h1 className="text-[12px] font-semibold uppercase tracking-wider text-zinc-300">
          Screener — {data.screener.length} names
        </h1>
        <span className="text-[10.5px] text-term-muted">
          Click any column header to sort · click a symbol for the full sheet
        </span>
      </div>
      <ScreenerTable rows={data.screener} caption="AI-stack screener" />
      <p className="text-[10px] text-term-muted mt-1">
        Metrics are date-stamped point-in-time figures derived from public
        sources and decay over time. Null values render as —.
      </p>
    </div>
  );
}
