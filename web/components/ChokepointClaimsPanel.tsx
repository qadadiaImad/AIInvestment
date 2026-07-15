"use client";

import type { Chokepoint } from "@/lib/chokepoints";
import { categoryColor, categoryLabel, severityBand, severityColor, claimClassMeta, sortedClaims } from "@/lib/chokepoints";

// Claims/sources/mitigation_watch detail for the currently-focused chokepoint
// on /map. Renders nothing when no chokepoint is focused — NodeDetailPanel
// (or the empty-state prompt) takes the aside space instead.
export default function ChokepointClaimsPanel({ cp }: { cp: Chokepoint | null }) {
  if (!cp) return null;

  const color = categoryColor(cp.category);
  const claims = sortedClaims(cp);

  return (
    <div className="border-b border-term-border px-2.5 py-2 space-y-2.5 max-h-[50vh] overflow-y-auto">
      <div>
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className="inline-block px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm border"
            style={{ color, borderColor: color, backgroundColor: `${color}1a` }}
          >
            {categoryLabel(cp.category)}
          </span>
          <span
            className="inline-block px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm border"
            style={{
              color: severityColor(cp.severity_score),
              borderColor: severityColor(cp.severity_score),
            }}
          >
            {severityBand(cp.severity_score)} · {cp.severity_score}/100
          </span>
          {cp.graph_crossref?.is_articulation && (
            <span className="inline-block px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm border border-rose-500/60 text-rose-400 bg-rose-500/10">
              ⚠ also a graph SPOF
            </span>
          )}
        </div>
        <h3 className="mt-1 text-[13px] font-semibold text-zinc-100">{cp.name}</h3>
        <p className="mt-0.5 text-[10.5px] text-zinc-400 leading-relaxed">{cp.description}</p>
      </div>

      <section className="space-y-1.5">
        <h4 className="text-[9.5px] font-semibold uppercase tracking-wider text-zinc-500">
          Claims &amp; sources ({claims.length})
        </h4>
        {claims.map((c, i) => {
          const meta = claimClassMeta(c.class);
          return (
            <div
              key={i}
              className="rounded-sm border border-term-border bg-[#0b0f17] px-2 py-1.5 text-[10.5px]"
            >
              <div className="flex items-center gap-1.5 flex-wrap">
                <span
                  className={`inline-block px-1.5 py-px text-[9px] font-semibold uppercase tracking-wider rounded-sm border ${meta.chipCls}`}
                >
                  {meta.label}
                </span>
                {c.needs_verification && (
                  <span className="text-[9px] uppercase tracking-wider text-zinc-500">
                    needs verification
                  </span>
                )}
              </div>
              <p className="mt-1 text-zinc-300 leading-relaxed">{c.text}</p>
              <div className="mt-1 flex items-center gap-2 text-[9.5px] text-zinc-500">
                <a
                  href={c.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sky-400 hover:text-sky-300 hover:underline"
                >
                  {c.source_name} ↗
                </a>
                <span>· {c.retrieved_at}</span>
              </div>
            </div>
          );
        })}
      </section>

      {cp.mitigation_watch.length > 0 && (
        <section className="space-y-1">
          <h4 className="text-[9.5px] font-semibold uppercase tracking-wider text-zinc-500">
            Mitigation watch
          </h4>
          <ul className="space-y-0.5">
            {cp.mitigation_watch.map((m, i) => (
              <li key={i} className="text-[10.5px] text-zinc-400 flex gap-1.5">
                <span className="text-zinc-600">·</span>
                <span>{m}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="text-[9px] text-zinc-600 leading-snug">
        {cp.needs_verification
          ? "One or more claims above rely on a secondary/aggregator source — directionally credible, not confirmed."
          : "All claims sourced and stamped."}{" "}
        Educational research only — not financial advice.
      </p>
    </div>
  );
}
