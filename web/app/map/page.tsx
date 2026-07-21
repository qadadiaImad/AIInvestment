import type { Metadata } from "next";
import { getSiteData, getGraphAnalysis, getChokepointsData } from "@/lib/data";
import MapExplorer from "@/components/MapExplorer";

export const metadata: Metadata = {
  title: "Capital Web Map · AI STACK",
  description:
    "Interactive relationship graph of the AI value chain — equity stakes, compute commitments, customer and infrastructure links. Educational only.",
};

export default function MapPage() {
  const data = getSiteData();
  const analysis = getGraphAnalysis();
  // Guarded per lib/chokepoints.ts contract — may legitimately be null on a
  // fresh clone / pre-pipeline Vercel build; MapExplorer degrades the
  // overlay toggle to "hidden" in that case, never a runtime error.
  const chokepointsData = getChokepointsData();
  const { nodes, edges } = data.capital_web;

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 border-b border-term-border">
        <h1 className="text-[12px] font-semibold uppercase tracking-wider text-zinc-300">
          Capital Web — interactive relationship map
        </h1>
        <span className="text-[10.5px] text-term-muted tnum">
          {nodes.length} nodes · {edges.length} edges · drag, click a node, or
          use the dropdown to drill in
        </span>
      </div>
      <MapExplorer
        web={data.capital_web}
        resiliency={analysis.nodes}
        dffBase={analysis.macro.snapshot.dff}
        chokepointsData={chokepointsData}
      />
      <p className="px-3 py-2 border-t border-term-border text-[9.5px] text-term-muted">
        Relationships are reported / filed / rumored as labeled; AI-extracted
        edges quote their source. Educational / research only — not investment
        advice.
      </p>
    </div>
  );
}
