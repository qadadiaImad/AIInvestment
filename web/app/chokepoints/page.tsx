import type { Metadata } from "next";
import Link from "next/link";
import { getSiteData, getChokepointsData } from "@/lib/data";
import ChokepointBoard from "@/components/ChokepointBoard";

export const metadata: Metadata = {
  title: "Supply-Chain Chokepoints · AI STACK",
  description:
    "Single points of failure in the AI value chain's physical supply chain — foundry concentration, EUV lithography, HBM memory, advanced packaging, export controls, grid & power constraints. Every claim labeled fact / reported / rumored with a source. Educational only, not investment advice.",
};

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-sm border border-term-border bg-term-panel px-2.5 py-2">
      <div className="text-[9.5px] uppercase tracking-wider text-term-muted">{label}</div>
      <div className="mt-0.5 text-[20px] font-semibold text-zinc-100 tnum">{value}</div>
    </div>
  );
}

export default function ChokepointsPage() {
  const data = getChokepointsData();

  // Header/eyebrow + methodology banner render unconditionally so a
  // pre-pipeline deployment still shows a coherent page, never a 500 or a
  // blank screen — the empty state below replaces only the stat row + grid.
  const header = (
    <div>
      <h1 className="text-base font-bold tracking-tight">Supply-Chain Chokepoints</h1>
      <p className="mt-0.5 text-[11px] text-term-muted">
        Single points of failure in the physical AI supply chain — one fab, one lithography
        machine, one export-control memo away from the whole stack slowing down.
      </p>
    </div>
  );

  const methodologyBanner = (
    <div className="rounded-sm border border-amber-500/50 bg-amber-500/10 px-3 py-2 text-[11.5px] text-amber-200 leading-relaxed">
      <span className="font-semibold uppercase tracking-wider text-amber-300">
        Fact / reported / rumored.
      </span>{" "}
      Every claim on this page is individually labeled: <strong>fact</strong> (primary/
      regulatory/filing source), <strong>reported</strong> (credible secondary/trade-press
      source, not independently re-verified here), or <strong>rumored</strong> (explicitly
      unconfirmed by its own source). Claims flagged &ldquo;needs verification&rdquo; rely on a
      secondary/aggregator source where the primary document could not be reached. This is{" "}
      <strong>indicative, not investment advice</strong> — severity scores are curated analyst
      judgment, not a computed probability.
    </div>
  );

  if (!data) {
    return (
      <div className="px-3 py-4 max-w-5xl mx-auto flex flex-col gap-6">
        {header}
        {methodologyBanner}
        <div className="rounded-sm border border-term-border bg-term-panel px-4 py-8 text-center">
          <p className="text-[12px] text-zinc-300 font-semibold">
            Chokepoint data has not been generated yet on this deployment.
          </p>
          <p className="mt-1 text-[11px] text-term-muted">
            Run <code className="text-zinc-400">scripts/build_chokepoints.py</code> to produce{" "}
            <code className="text-zinc-400">web/public/data/chokepoints.json</code>, then reload
            this page.
          </p>
        </div>
      </div>
    );
  }

  const site = getSiteData();
  const knownSymbols = Object.keys(site.stocks);

  const criticalCount = data.chokepoints.filter((cp) => cp.severity_score >= 75).length;
  const distinctLayers = new Set(data.chokepoints.flatMap((cp) => cp.layers)).size;

  return (
    <div className="px-3 py-4 max-w-5xl mx-auto flex flex-col gap-6">
      {header}
      {methodologyBanner}

      {/* stat row */}
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <Stat label="Chokepoints tracked" value={String(data.summary.n_entries)} />
        <Stat label="Critical (severity ≥75)" value={String(criticalCount)} />
        <Stat label="Fact-class claims" value={String(data.summary.n_fact)} />
        <Stat label="Layers touched" value={String(distinctLayers)} />
      </section>

      {/* board */}
      <ChokepointBoard data={data} knownSymbols={knownSymbols} />

      {/* footer */}
      <section className="border-t border-term-border pt-3 space-y-1.5">
        <p className="text-term-muted text-[11px] leading-relaxed">
          {data.disclaimer}
        </p>
        <p className="text-term-muted text-[11px] leading-relaxed">
          Generated {data.generated_at} from{" "}
          <code className="text-zinc-500">chokepoints_source.json</code> cross-referenced
          against the capital web graph. See these chokepoints highlighted on the{" "}
          <Link href="/map" className="text-sky-400 hover:text-sky-300 hover:underline">
            interactive capital web map ↗
          </Link>{" "}
          (toggle &ldquo;⛓ Chokepoints&rdquo;). Educational / research only — not investment
          advice.
        </p>
      </section>
    </div>
  );
}
