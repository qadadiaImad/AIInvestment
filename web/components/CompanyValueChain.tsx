"use client";

import Link from "next/link";
import type { CapitalWeb, ResiliencyNode } from "@/lib/data";
import {
  buildEgoModel,
  formatTerms,
  relationKindMeta,
  type Counterparty,
  type Relation,
  type RelationKind,
} from "@/lib/egograph";
import { layerLabel, healthColor, healthBand } from "@/lib/format";

// Edge-type labels match NodeDetailPanel's vocabulary so the two views read the
// same. The relation's OWN certainty / source travel with it untouched — a
// rumored edge stays rumored here.
const TYPE_LABELS: Record<string, string> = {
  equity_stake: "equity stake",
  compute_commitment: "compute commitment",
  customer: "customer",
  infra_partner: "infra partner",
  voting_power: "voting power",
  subsidiary: "subsidiary",
};

function typeLabel(t: string): string {
  return TYPE_LABELS[t] ?? t.replace(/[_-]+/g, " ");
}

function isUrl(s?: string): boolean {
  return !!s && /^https?:\/\//i.test(s);
}

// Honesty rule: each relation shows the edge's own certainty, never upgraded.
function CertaintyChip({ certainty }: { certainty?: string }) {
  const c = certainty ?? "unknown";
  const map: Record<string, string> = {
    filed: "text-emerald-400 border-emerald-500/50 bg-emerald-500/10",
    reported: "text-amber-400 border-amber-500/50 bg-amber-500/10",
    rumored: "text-zinc-400 border-zinc-500/50 bg-zinc-500/10 border-dashed",
  };
  const cls = map[c] ?? "text-zinc-400 border-zinc-600 bg-zinc-700/20";
  return (
    <span
      className={`inline-block px-1 py-px text-[8.5px] font-semibold uppercase tracking-wider rounded-sm border ${cls}`}
    >
      {c}
    </span>
  );
}

// One relation chip-row: type · compact terms · certainty · source.
function RelationRow({ rel }: { rel: Relation }) {
  const terms = formatTerms(rel.raw.attrs);
  const url = isUrl(rel.source_url);
  return (
    <div className="flex flex-wrap items-center gap-1 text-[10px] leading-relaxed">
      <span className="uppercase tracking-wider text-zinc-400">
        {typeLabel(rel.type)}
      </span>
      {terms && (
        <span className="inline-block px-1.5 py-px rounded-sm bg-zinc-800/70 text-zinc-200 tnum">
          {terms}
        </span>
      )}
      <CertaintyChip certainty={rel.certainty} />
      {url ? (
        <a
          href={rel.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sky-400 hover:text-sky-300 hover:underline"
        >
          source ↗
        </a>
      ) : rel.source_url ? (
        <span className="text-zinc-600">curated</span>
      ) : null}
    </div>
  );
}

// One counterparty card: name links to /stocks/{id} AND clicking re-centers the
// ego view via onFocus. Below it, every relation between focal and this party.
function CounterpartyCard({
  cp,
  onFocus,
}: {
  cp: Counterparty;
  onFocus: (id: string) => void;
}) {
  return (
    <div className="border border-term-border rounded-sm bg-[#0b0f17] px-2 py-1.5">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 min-w-0">
          <button
            type="button"
            onClick={() => onFocus(cp.id)}
            title={`Re-center on ${cp.name}`}
            className="text-left font-semibold text-zinc-100 hover:text-emerald-300 truncate"
          >
            {cp.name}
          </button>
          {cp.layer && (
            <span className="shrink-0 text-[8.5px] uppercase tracking-wider text-zinc-500">
              {layerLabel(cp.layer)}
            </span>
          )}
        </div>
        <Link
          href={`/stocks/${cp.id}`}
          className="shrink-0 text-[9px] text-sky-400 hover:text-sky-300 hover:underline"
        >
          stock ↗
        </Link>
      </div>
      <div className="mt-1 space-y-1">
        {cp.relations.map((rel, i) => (
          <RelationRow key={i} rel={rel} />
        ))}
      </div>
    </div>
  );
}

// A side column (Inputs or Outputs), with counterparties grouped by kind.
function SideColumn({
  title,
  subtitle,
  counterparties,
  kindOrder,
  emptyNote,
  onFocus,
}: {
  title: string;
  subtitle: string;
  counterparties: Counterparty[];
  kindOrder: RelationKind[];
  emptyNote: string;
  onFocus: (id: string) => void;
}) {
  // Group counterparties by kind, preserving the salience sort within each.
  const byKind = new Map<RelationKind, Counterparty[]>();
  for (const cp of counterparties) {
    const arr = byKind.get(cp.kind) ?? [];
    arr.push(cp);
    byKind.set(cp.kind, arr);
  }
  const groups = kindOrder
    .map((k) => ({ kind: k, items: byKind.get(k) ?? [] }))
    .filter((g) => g.items.length > 0);

  return (
    <div className="flex-1 min-w-0 flex flex-col gap-2">
      <div className="border-b border-term-border pb-1">
        <h3 className="flex items-baseline gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-zinc-200">
          {title}
          <span className="tnum text-zinc-500">{counterparties.length}</span>
        </h3>
        <p className="text-[9.5px] text-term-muted">{subtitle}</p>
      </div>
      {groups.length === 0 ? (
        <p className="text-[10px] text-term-muted italic">{emptyNote}</p>
      ) : (
        groups.map((g) => {
          const meta = relationKindMeta(g.kind);
          return (
            <section key={g.kind} className="space-y-1.5">
              <div className="flex items-center gap-1.5">
                <span
                  className={`inline-block px-1 py-px text-[9px] font-semibold uppercase tracking-wider rounded-sm border ${meta.colorCls}`}
                >
                  {meta.label}
                </span>
                <span className="tnum text-[9px] text-zinc-600">
                  {g.items.length}
                </span>
              </div>
              {g.items.map((cp) => (
                <CounterpartyCard key={cp.id} cp={cp} onFocus={onFocus} />
              ))}
            </section>
          );
        })
      )}
    </div>
  );
}

export default function CompanyValueChain({
  web,
  focalId,
  onFocus,
  resiliency,
}: {
  web: CapitalWeb;
  focalId: string | null;
  onFocus: (id: string) => void;
  resiliency?: ResiliencyNode[];
}) {
  if (!focalId) {
    return (
      <div className="h-full grid place-items-center p-4 text-center">
        <p className="text-[11px] text-term-muted max-w-[260px]">
          Pick a company above (or click a node in the global graph) to see its
          value chain — who it depends on and who depends on it.
        </p>
      </div>
    );
  }

  // Guard against an unknown focal id before building the model (TS-safe and
  // independent of how buildEgoModel handles a missing node).
  const focalExists = web.nodes.some((n) => n.id === focalId);
  if (!focalExists) {
    return (
      <div className="h-full grid place-items-center p-4 text-center">
        <p className="text-[11px] text-term-muted max-w-[260px]">
          No company found for “{focalId}”.
        </p>
      </div>
    );
  }

  const model = buildEgoModel(web, focalId);
  const focal = model.focal;
  const res = resiliency?.find((r) => r.id === focalId);
  const focalIsPublic = focal.type === "public";

  return (
    <div className="h-full overflow-y-auto p-3">
      <div className="flex flex-col lg:flex-row gap-3 lg:gap-2 items-stretch">
        {/* LEFT — inputs */}
        <SideColumn
          title="Inputs"
          subtitle="depends on · can influence its stock"
          counterparties={model.inputs}
          kindOrder={["supply", "compute", "capital", "related"]}
          emptyNote="No recorded inputs (suppliers, compute, or backers)."
          onFocus={onFocus}
        />

        {/* connector */}
        <div
          aria-hidden
          className="hidden lg:flex items-center text-zinc-600 text-lg"
        >
          →
        </div>

        {/* CENTER — focal card */}
        <div className="lg:w-[220px] shrink-0 flex items-stretch">
          <div className="w-full self-center rounded-sm border border-emerald-500/40 bg-[#0d1220] px-3 py-3">
            <div className="text-center">
              <div className="text-[13px] font-semibold text-zinc-100">
                {focal.name || focal.id}
              </div>
              {focal.layer && (
                <div className="mt-0.5 text-[9.5px] uppercase tracking-wider text-zinc-500">
                  {layerLabel(focal.layer)}
                </div>
              )}
              {focalIsPublic && (
                <Link
                  href={`/stocks/${focal.id}`}
                  className="mt-1 inline-block text-[10px] text-sky-400 hover:text-sky-300 hover:underline"
                >
                  view {focal.id} fundamentals ↗
                </Link>
              )}
            </div>

            {res && (
              <div className="mt-2 border-t border-term-border pt-2 text-center">
                <div className="text-[9px] uppercase tracking-wider text-term-muted">
                  Resiliency
                </div>
                <div className="flex items-baseline justify-center gap-1">
                  <span
                    className="text-[18px] font-bold tnum"
                    style={{ color: healthColor(res.health) }}
                  >
                    {res.health != null ? res.health.toFixed(0) : "—"}
                  </span>
                  <span className="text-[9px] text-zinc-500">/100</span>
                </div>
                <div className="flex items-center justify-center gap-1.5">
                  <span
                    className="text-[9px] uppercase tracking-wider"
                    style={{ color: healthColor(res.health) }}
                  >
                    {healthBand(res.health)}
                  </span>
                  {res.is_articulation && (
                    <span className="text-[8.5px] font-semibold uppercase tracking-wider text-rose-400">
                      ⚠ SPOF
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* connector */}
        <div
          aria-hidden
          className="hidden lg:flex items-center text-zinc-600 text-lg"
        >
          →
        </div>

        {/* RIGHT — outputs */}
        <SideColumn
          title="Outputs"
          subtitle="depends on it · which it influences"
          counterparties={model.outputs}
          kindOrder={["supply", "compute", "capital", "related"]}
          emptyNote="No recorded outputs (customers or holdings)."
          onFocus={onFocus}
        />
      </div>

      <p className="mt-3 text-[9px] text-term-muted leading-snug">
        Direction is by relation type, not arrow. Each relation carries its own
        certainty (filed / reported / rumored) and source — never upgraded.
        Educational / research only — not investment advice.
      </p>
    </div>
  );
}
