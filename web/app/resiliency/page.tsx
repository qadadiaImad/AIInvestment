import type { Metadata } from "next";
import Link from "next/link";
import { getSiteData, getGraphAnalysis } from "@/lib/data";
import type { Cascade } from "@/lib/data";
import MacroStressInteractive from "@/components/MacroStressInteractive";
import {
  healthColor,
  healthBand,
  healthTextClass,
  layerLabel,
  num,
} from "@/lib/format";

export const metadata: Metadata = {
  title: "Graph Resiliency · AI STACK",
  description:
    "Structural, indicative resiliency of the AI value-chain capital graph — single points of failure, fragility, bridges, macro stress, and cascade scenarios. Educational only; not a dollar-loss estimate.",
};

// Plain-English label for a cascade scenario.
const SCENARIO_LABELS: Record<string, string> = {
  tsm_disruption: "TSMC foundry disruption",
  hyperscaler_capex_cut: "Hyperscaler capex cut",
  energy_bridge_loss: "Energy bridge loss",
};

function scenarioTitle(s: string): string {
  return (
    SCENARIO_LABELS[s] ??
    s.replace(/[_-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

function cascadeSentence(c: Cascade, nNodes: number): string {
  const title = scenarioTitle(c.scenario);
  const shock =
    c.direction === "reverse"
      ? "reverse demand shock"
      : "forward supply shock";
  const pct = (c.reach * 100).toFixed(0);
  return `${title} (${shock}) propagates to ${c.affected_count} of ${nNodes} nodes (${pct}% reach).`;
}

export default function ResiliencyPage() {
  const site = getSiteData();
  const a = getGraphAnalysis();
  const g = a.graph;

  // Which ids have a public stock page.
  const stockSyms = new Set(Object.keys(site.stocks));
  // Resolve display names from analysis + capital web nodes.
  const nameById = new Map<string, string>();
  for (const n of a.nodes) nameById.set(n.id, n.name);
  for (const n of site.capital_web.nodes)
    if (!nameById.has(n.id)) nameById.set(n.id, n.name || n.id);
  const displayName = (id: string) => nameById.get(id) ?? id;

  const overallColor = healthColor(a.overall_health);
  const overallBand = healthBand(a.overall_health);

  const layerRows = Object.entries(a.layers).sort(
    (x, y) => y[1].mean - x[1].mean,
  );
  const cascades = [...a.cascades].sort(
    (x, y) => y.affected_count - x.affected_count,
  );

  function NodeLink({ id }: { id: string }) {
    const label = displayName(id);
    if (stockSyms.has(id)) {
      return (
        <Link
          href={`/stocks/${id}`}
          className="text-sky-400 hover:text-sky-300 hover:underline"
        >
          {label}
        </Link>
      );
    }
    return <span className="text-zinc-300">{label}</span>;
  }

  return (
    <div className="px-3 py-4 max-w-5xl flex flex-col gap-6">
      {/* page header */}
      <div>
        <h1 className="text-base font-bold tracking-tight">
          Graph Resiliency
        </h1>
        <p className="mt-0.5 text-[11px] text-term-muted">
          Structural fragility of the AI value-chain capital graph — where the
          network breaks, and what cascades when it does.
        </p>
      </div>

      {/* indicative disclaimer banner */}
      <div className="rounded-sm border border-amber-500/50 bg-amber-500/10 px-3 py-2 text-[11.5px] text-amber-200 leading-relaxed">
        <span className="font-semibold uppercase tracking-wider text-amber-300">
          Indicative / structural only.
        </span>{" "}
        {a.disclaimer} These scores are derived from a curated relationship
        graph that is survivorship-biased and incomplete. They are{" "}
        <strong>not a dollar-loss estimate</strong> and{" "}
        <strong>not investment advice</strong>.
      </div>

      {/* overall health + graph stats */}
      <section className="grid grid-cols-1 md:grid-cols-[220px_1fr] gap-4">
        <div className="rounded-sm border border-term-border bg-term-panel px-4 py-4 flex flex-col items-center justify-center text-center">
          <span className="text-[10px] uppercase tracking-wider text-term-muted">
            Overall network health
          </span>
          <span
            className="mt-1 text-[44px] font-bold leading-none tnum"
            style={{ color: overallColor }}
          >
            {a.overall_health.toFixed(1)}
          </span>
          <span
            className="mt-1 inline-block px-2 py-px text-[10px] font-semibold uppercase tracking-wider rounded-sm border"
            style={{ color: overallColor, borderColor: overallColor }}
          >
            {overallBand}
          </span>
          <span className="mt-2 text-[9.5px] text-zinc-500">
            Updated {a.generated_at}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 content-start">
          <Stat label="Nodes" value={String(g.n_nodes)} />
          <Stat label="Edges" value={String(g.n_edges)} />
          <Stat label="Largest SCC" value={String(g.largest_scc_size)} />
          <Stat
            label="Fragility ratio"
            value={`${num(g.fragility_ratio, 2)}×`}
          />
          <Stat label="Assortativity" value={num(g.assortativity, 3)} />
          <Stat
            label="Articulation pts"
            value={String(g.articulation_points.length)}
          />
          <div className="col-span-2 sm:col-span-3 rounded-sm border border-term-border bg-[#0b0f17] px-2.5 py-2 text-[10.5px] text-term-muted leading-relaxed">
            Targeted hub removal is{" "}
            <span className="text-zinc-200 font-semibold tnum">
              {num(g.fragility_ratio, 2)}×
            </span>{" "}
            more damaging than random failure — classic scale-free fragility.
          </div>
        </div>
      </section>

      {/* layer health table */}
      <section>
        <h2 className="text-[13px] font-semibold uppercase tracking-wider text-zinc-300 mb-2">
          Layer health
        </h2>
        <div className="overflow-x-auto rounded-sm border border-term-border">
          <table className="term">
            <thead>
              <tr>
                <th>Layer</th>
                <th className="numcell">Mean</th>
                <th className="numcell">Min</th>
                <th className="numcell">Max</th>
                <th className="numcell">N</th>
              </tr>
            </thead>
            <tbody>
              {layerRows.map(([layer, h]) => (
                <tr key={layer}>
                  <td>{layerLabel(layer)}</td>
                  <td className={`numcell font-semibold ${healthTextClass(h.mean)}`}>
                    {h.mean.toFixed(1)}
                  </td>
                  <td className="numcell text-zinc-400">{h.min.toFixed(1)}</td>
                  <td className="numcell text-zinc-400">{h.max.toFixed(1)}</td>
                  <td className="numcell text-zinc-400">{h.n}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* top SPOFs + bridges */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <h2 className="text-[13px] font-semibold uppercase tracking-wider text-zinc-300 mb-2">
            Top single points of failure
          </h2>
          <p className="text-[10px] text-term-muted mb-2">
            Nodes whose removal most fragments the network (by betweenness
            centrality).
          </p>
          <ul className="flex flex-col gap-1">
            {a.top_spofs.map((s) => (
              <li
                key={s.id}
                className="flex items-center justify-between gap-2 rounded-sm border border-term-border bg-[#0b0f17] px-2.5 py-1.5 text-[11px]"
              >
                <span className="flex items-center gap-2 min-w-0">
                  <span className="text-rose-400">⚠</span>
                  <NodeLink id={s.id} />
                  <span className="text-[9px] uppercase tracking-wider text-zinc-600">
                    {layerLabel(s.layer)}
                  </span>
                </span>
                <span className="text-zinc-400 tnum shrink-0">
                  bw {num(s.betweenness, 4)}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h2 className="text-[13px] font-semibold uppercase tracking-wider text-zinc-300 mb-2">
            Critical bridges
          </h2>
          <p className="text-[10px] text-term-muted mb-2">
            Edges whose loss disconnects part of the graph — single-link
            dependencies.
          </p>
          <ul className="flex flex-col gap-1">
            {g.bridges.map(([u, v], i) => (
              <li
                key={`${u}-${v}-${i}`}
                className="flex items-center gap-2 rounded-sm border border-term-border bg-[#0b0f17] px-2.5 py-1.5 text-[11px]"
              >
                <NodeLink id={u} />
                <span className="text-zinc-600">→</span>
                <NodeLink id={v} />
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* macro stress */}
      <section>
        <h2 className="text-[13px] font-semibold uppercase tracking-wider text-zinc-300 mb-2">
          Macro stress
        </h2>
        <div className="rounded-sm border border-term-border bg-term-panel px-3 py-3">
          <div className="flex flex-wrap gap-4">
            <MacroStat
              label="Fed funds"
              value={`${a.macro.snapshot.dff.toFixed(2)}%`}
            />
            <MacroStat
              label="10Y Treasury"
              value={`${a.macro.snapshot.dgs10.toFixed(2)}%`}
            />
            <MacroStat
              label="Electricity"
              value={`$${a.macro.snapshot.elec.toFixed(3)}/kWh`}
            />
          </div>
          <p className="mt-2 text-[9.5px] text-zinc-500">
            As of {a.macro.snapshot.retrieved_at}
          </p>
          <p className="mt-2 text-[10.5px] text-term-muted leading-relaxed">
            {a.macro.scenario_note}
          </p>
        </div>
      </section>

      {/* interactive macro stress (client-side recompute) */}
      <MacroStressInteractive
        edges={site.capital_web.edges}
        nodes={site.capital_web.nodes}
        dffBase={a.macro.snapshot.dff}
      />

      {/* cascade scenarios */}
      <section>
        <h2 className="text-[13px] font-semibold uppercase tracking-wider text-zinc-300 mb-2">
          Cascade scenarios
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {cascades.map((c) => (
            <div
              key={`${c.scenario}-${c.direction}`}
              className="rounded-sm border border-term-border bg-[#0b0f17] px-3 py-3 flex flex-col gap-2"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-[12px] font-semibold text-zinc-200">
                  {scenarioTitle(c.scenario)}
                </span>
                <span className="text-[9px] uppercase tracking-wider text-zinc-500 border border-term-border rounded-sm px-1.5 py-px">
                  {c.direction}
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                {cascadeSentence(c, g.n_nodes)}
              </p>
              <div className="mt-auto flex items-center gap-2 text-[10px]">
                <span className="text-zinc-600 uppercase tracking-wider">
                  seeds
                </span>
                <span className="flex flex-wrap gap-1.5">
                  {c.seeds.map((s) => (
                    <span key={s} className="inline-flex">
                      <NodeLink id={s} />
                    </span>
                  ))}
                </span>
              </div>
              <div className="text-[10px] text-zinc-500 tnum">
                {c.affected_count} affected · {(c.reach * 100).toFixed(0)}%
                reach
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* footer disclaimer */}
      <section className="border-t border-term-border pt-3">
        <p className="text-term-muted text-[11px] leading-relaxed">
          {a.disclaimer} Resiliency scores are structural and indicative,
          derived from a curated, survivorship-biased relationship graph — they
          do not estimate dollar losses or probabilities. Educational /
          research only — not investment advice.
        </p>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-sm border border-term-border bg-term-panel px-2.5 py-2">
      <div className="text-[9.5px] uppercase tracking-wider text-term-muted">
        {label}
      </div>
      <div className="mt-0.5 text-[15px] font-semibold text-zinc-100 tnum">
        {value}
      </div>
    </div>
  );
}

function MacroStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[9.5px] uppercase tracking-wider text-term-muted">
        {label}
      </div>
      <div className="mt-0.5 text-[16px] font-semibold text-zinc-100 tnum">
        {value}
      </div>
    </div>
  );
}
