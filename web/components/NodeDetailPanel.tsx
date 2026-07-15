"use client";

import Link from "next/link";
import type {
  CapitalWeb,
  GraphEdge,
  GraphNode,
  ResiliencyNode,
  Chokepoint,
} from "@/lib/data";
import { usd, titleCase, healthColor, healthBand, num } from "@/lib/format";
import { categoryColor, categoryLabel } from "@/lib/chokepoints";
import LayerChip from "@/components/LayerChip";

// ---- helpers ---------------------------------------------------------------

const TYPE_LABELS: Record<string, string> = {
  equity_stake: "equity stake",
  compute_commitment: "compute commitment",
  customer: "customer",
  infra_partner: "infra partner",
  voting_power: "voting power",
  subsidiary: "subsidiary",
};

function typeLabel(t: string): string {
  return TYPE_LABELS[t] ?? titleCase(t);
}

const CERTAINTY_ORDER: Record<string, number> = {
  filed: 0,
  reported: 1,
  rumored: 2,
};

function certaintyRank(c?: string): number {
  return c && c in CERTAINTY_ORDER ? CERTAINTY_ORDER[c] : 3;
}

function CertaintyChip({ certainty }: { certainty?: string }) {
  const c = certainty ?? "unknown";
  const map: Record<string, string> = {
    filed: "text-emerald-400 border-emerald-500/50 bg-emerald-500/10",
    reported: "text-amber-400 border-amber-500/50 bg-amber-500/10",
    rumored:
      "text-zinc-400 border-zinc-500/50 bg-zinc-500/10 border-dashed",
  };
  const cls = map[c] ?? "text-zinc-400 border-zinc-600 bg-zinc-700/20";
  return (
    <span
      className={`inline-block px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm border ${cls}`}
    >
      {c}
    </span>
  );
}

// Render an edge's attrs as readable chips.
function attrChips(e: GraphEdge): string[] {
  const a = e.attrs;
  if (!a) return [];
  const out: string[] = [];
  if (typeof a.usd === "number") out.push(usd(a.usd));
  if (typeof a.usd_per_month === "number")
    out.push(`${usd(a.usd_per_month)}/mo`);
  if (typeof a.pct === "number") out.push(`${a.pct}%`);
  if (typeof a.cap_pct === "number") out.push(`cap ${a.cap_pct}%`);
  if (typeof a.power_gw === "number") out.push(`${a.power_gw} GW`);
  if (typeof a.power_mw === "number") out.push(`${a.power_mw} MW`);
  if (typeof a.gpus === "number") out.push(`${a.gpus.toLocaleString()} GPUs`);
  if (typeof a.tpus === "number") out.push(`${a.tpus.toLocaleString()} TPUs`);
  if (typeof a.termination_days === "number")
    out.push(`${a.termination_days}-day exit`);
  if (a.duration != null) out.push(String(a.duration));
  if (a.until != null) out.push(`until ${a.until}`);
  if (a.term_through != null) out.push(`through ${a.term_through}`);
  if (a.note != null && String(a.note).length <= 60) out.push(String(a.note));
  return out;
}

interface Transaction {
  date?: string | null;
  amount?: number | null;
  note?: string | null;
}

function transactions(e: GraphEdge): Transaction[] {
  const raw = e.attrs?.transactions as unknown;
  if (Array.isArray(raw)) return raw as Transaction[];
  return [];
}

function isUrl(s?: string): boolean {
  return !!s && /^https?:\/\//i.test(s);
}

// ---- edge card -------------------------------------------------------------

function EdgeCard({
  edge,
  selfId,
  nodeMap,
}: {
  edge: GraphEdge;
  selfId: string;
  nodeMap: Map<string, GraphNode>;
}) {
  const outbound = edge.src === selfId;
  const counterpartyId = outbound ? edge.dst : edge.src;
  const counterparty = nodeMap.get(counterpartyId);
  const counterpartyName = counterparty?.name || counterpartyId;
  const counterpartyIsPublic = counterparty?.type === "public";

  const arrow = outbound ? "→" : "←";
  const dirLabel = `${edge.src} → ${edge.dst}: ${typeLabel(edge.type)}`;

  const chips = attrChips(edge);
  const txs = transactions(edge);
  const url = isUrl(edge.source_url);

  return (
    <div className="border border-term-border rounded-sm bg-[#0b0f17] px-2.5 py-2 text-[11px]">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="text-zinc-500 tnum">{arrow}</span>
          {counterpartyIsPublic ? (
            <Link
              href={`/stocks/${counterpartyId}`}
              className="text-sky-400 hover:text-sky-300 hover:underline font-semibold truncate"
            >
              {counterpartyName}
            </Link>
          ) : (
            <span className="text-zinc-200 font-semibold truncate">
              {counterpartyName}
            </span>
          )}
          {counterparty?.layer && <LayerChip layer={counterparty.layer} />}
        </div>
        <CertaintyChip certainty={edge.certainty} />
      </div>

      <div className="mt-1 text-[10px] text-term-muted">
        <span className="uppercase tracking-wider">{typeLabel(edge.type)}</span>
        <span className="mx-1 text-zinc-600">·</span>
        <span className="text-zinc-500">{dirLabel}</span>
      </div>

      {chips.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {chips.map((c, i) => (
            <span
              key={i}
              className="inline-block px-1.5 py-px text-[10px] rounded-sm bg-zinc-800/70 text-zinc-200 tnum"
            >
              {c}
            </span>
          ))}
        </div>
      )}

      {txs.length > 0 && (
        <ul className="mt-1.5 space-y-0.5 text-[10px] text-zinc-400">
          {txs.map((t, i) => (
            <li key={i} className="flex gap-1.5">
              <span className="text-zinc-500 tnum shrink-0">
                {t.date ?? "—"}
              </span>
              {t.amount != null && (
                <span className="text-zinc-200 tnum shrink-0">
                  {usd(t.amount)}
                </span>
              )}
              {t.note && <span className="text-zinc-400">{t.note}</span>}
            </li>
          ))}
        </ul>
      )}

      {edge.quote && url && (
        <blockquote className="mt-1.5 border-l-2 border-zinc-700 pl-2 text-[10px] italic text-zinc-400">
          “{edge.quote}”
        </blockquote>
      )}

      <div className="mt-1.5 text-[10px]">
        {url ? (
          <a
            href={edge.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sky-400 hover:text-sky-300 hover:underline"
          >
            source ↗
          </a>
        ) : (
          <span className="text-zinc-500">
            curated — {edge.source_url || "brief"}
          </span>
        )}
        {edge.origin && (
          <span className="ml-2 text-zinc-600">[{edge.origin}]</span>
        )}
      </div>
    </div>
  );
}

// ---- resiliency section ----------------------------------------------------

function ComponentBar({ label, value }: { label: string; value: number }) {
  const pctVal = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className="flex items-center gap-2">
      <span className="w-[78px] shrink-0 text-[9.5px] uppercase tracking-wider text-zinc-500">
        {label}
      </span>
      <div className="flex-1 h-1.5 rounded-sm bg-zinc-800 overflow-hidden">
        <div
          className="h-full rounded-sm bg-zinc-400"
          style={{ width: `${pctVal}%` }}
        />
      </div>
      <span className="w-[34px] shrink-0 text-right text-[10px] text-zinc-400 tnum">
        {value.toFixed(2)}
      </span>
    </div>
  );
}

function ResiliencySection({ res }: { res: ResiliencyNode }) {
  const color = healthColor(res.health);
  const band = healthBand(res.health);
  return (
    <section className="space-y-2">
      <h3 className="text-[9.5px] font-semibold uppercase tracking-wider text-zinc-500">
        Resiliency
      </h3>

      {/* health score + band */}
      <div className="flex items-center gap-2">
        <span className="text-[20px] font-bold tnum" style={{ color }}>
          {res.health != null ? res.health.toFixed(0) : "—"}
        </span>
        <span className="text-[10px] text-zinc-500">/100</span>
        <span
          className="ml-1 inline-block px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm border"
          style={{ color, borderColor: color }}
        >
          {band}
        </span>
        {res.is_articulation && (
          <span className="ml-auto inline-block px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm border border-rose-500/60 text-rose-400 bg-rose-500/10">
            ⚠ SPOF
          </span>
        )}
      </div>

      {/* component bars */}
      <div className="space-y-1">
        <ComponentBar label="concentr." value={res.components.concentration} />
        <ComponentBar label="spof" value={res.components.spof} />
        <ComponentBar label="redundancy" value={res.components.redundancy} />
        <ComponentBar label="certainty" value={res.components.certainty} />
      </div>

      {/* scalar metrics */}
      <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[10px]">
        <div className="flex justify-between gap-2">
          <span className="text-zinc-500">ENS</span>
          <span className="text-zinc-300 tnum">
            {res.ens != null ? num(res.ens, 1) : "—"}
          </span>
        </div>
        <div className="flex justify-between gap-2">
          <span className="text-zinc-500">In SCC</span>
          <span className="text-zinc-300">{res.in_scc ? "yes" : "no"}</span>
        </div>
        <div className="flex justify-between gap-2">
          <span className="text-zinc-500">PageRank</span>
          <span className="text-zinc-300 tnum">{num(res.pagerank, 4)}</span>
        </div>
        <div className="flex justify-between gap-2">
          <span className="text-zinc-500">Betweenness</span>
          <span className="text-zinc-300 tnum">{num(res.betweenness, 4)}</span>
        </div>
      </div>

      {res.flags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {res.flags.map((f) => (
            <span
              key={f}
              className="inline-block px-1.5 py-px text-[9.5px] rounded-sm bg-amber-500/10 text-amber-400 border border-amber-500/40"
            >
              {f}
            </span>
          ))}
        </div>
      )}

      <p className="text-[9px] text-zinc-600 leading-snug">
        Structural / indicative resiliency — not a dollar-loss estimate. Not
        financial advice.
      </p>
    </section>
  );
}

// ---- panel -----------------------------------------------------------------

export default function NodeDetailPanel({
  web,
  selectedId,
  resiliency,
  linkedChokepoints,
  onSelectChokepoint,
}: {
  web: CapitalWeb;
  selectedId: string | null;
  resiliency?: ResiliencyNode[];
  // Chokepoints touching the selected node (Round 6), pre-filtered by the
  // caller via chokepointsForNode() — optional so every existing caller is
  // unaffected. Empty/absent renders no chip row.
  linkedChokepoints?: Chokepoint[];
  onSelectChokepoint?: (id: string) => void;
}) {
  const nodeMap = new Map(web.nodes.map((n) => [n.id, n]));
  const node = selectedId ? nodeMap.get(selectedId) : undefined;

  if (!node) {
    return (
      <div className="h-full grid place-items-center p-4 text-center">
        <p className="text-[11px] text-term-muted max-w-[240px]">
          Select a node or click one in the graph to see its relationships &amp;
          sources.
        </p>
      </div>
    );
  }

  const touching = web.edges.filter(
    (e) => e.src === selectedId || e.dst === selectedId,
  );
  const sorted = [...touching].sort((a, b) => {
    const r = certaintyRank(a.certainty) - certaintyRank(b.certainty);
    if (r !== 0) return r;
    return a.type.localeCompare(b.type);
  });

  const outbound = sorted.filter((e) => e.src === selectedId);
  const inbound = sorted.filter((e) => e.dst === selectedId);

  const res = resiliency?.find((r) => r.id === selectedId);

  return (
    <div className="h-full flex flex-col">
      {/* header */}
      <div className="px-2.5 py-2 border-b border-term-border shrink-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h2 className="text-[13px] font-semibold text-zinc-100">
            {node.name || node.id}
          </h2>
          {node.layer && <LayerChip layer={node.layer} />}
          <span className="text-[9.5px] uppercase tracking-wider text-zinc-500">
            {node.type}
          </span>
        </div>
        {node.type === "public" && (
          <Link
            href={`/stocks/${node.id}`}
            className="mt-0.5 inline-block text-[10px] text-sky-400 hover:text-sky-300 hover:underline"
          >
            view {node.id} fundamentals ↗
          </Link>
        )}
        {node.note && (
          <p className="mt-0.5 text-[10px] text-term-muted">{node.note}</p>
        )}
        <p className="mt-1 text-[10px] text-zinc-500 tnum">
          {touching.length} relationship{touching.length === 1 ? "" : "s"} ·{" "}
          {outbound.length} out · {inbound.length} in
        </p>
        {linkedChokepoints && linkedChokepoints.length > 0 && (
          <div className="mt-1.5 flex flex-wrap items-center gap-1">
            <span className="text-[9px] uppercase tracking-wider text-zinc-500">
              Linked chokepoints
            </span>
            {linkedChokepoints.map((cp) => {
              const color = categoryColor(cp.category);
              return (
                <button
                  key={cp.id}
                  type="button"
                  onClick={() => onSelectChokepoint?.(cp.id)}
                  title={`${cp.name} — ${categoryLabel(cp.category)} · severity ${cp.severity_score}/100`}
                  className="inline-block px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm border transition-colors hover:brightness-125"
                  style={{ color, borderColor: color, backgroundColor: `${color}1a` }}
                >
                  ⛓ {cp.name}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* scrollable body */}
      <div className="flex-1 overflow-y-auto px-2.5 py-2 space-y-3">
        {res && <ResiliencySection res={res} />}
        {outbound.length > 0 && (
          <section className="space-y-1.5">
            <h3 className="text-[9.5px] font-semibold uppercase tracking-wider text-zinc-500">
              Outbound → ({outbound.length})
            </h3>
            {outbound.map((e, i) => (
              <EdgeCard
                key={`o-${i}`}
                edge={e}
                selfId={selectedId!}
                nodeMap={nodeMap}
              />
            ))}
          </section>
        )}
        {inbound.length > 0 && (
          <section className="space-y-1.5">
            <h3 className="text-[9.5px] font-semibold uppercase tracking-wider text-zinc-500">
              Inbound ← ({inbound.length})
            </h3>
            {inbound.map((e, i) => (
              <EdgeCard
                key={`i-${i}`}
                edge={e}
                selfId={selectedId!}
                nodeMap={nodeMap}
              />
            ))}
          </section>
        )}
        {touching.length === 0 && (
          <p className="text-[11px] text-term-muted">
            No recorded relationships for this node.
          </p>
        )}
      </div>
    </div>
  );
}
