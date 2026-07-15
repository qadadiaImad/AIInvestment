import Link from "next/link";
import type { Chokepoint } from "@/lib/chokepoints";
import {
  categoryColor,
  categoryLabel,
  severityBand,
  severityColor,
  claimClassMeta,
  sortedClaims,
} from "@/lib/chokepoints";
import LayerChip from "@/components/LayerChip";

const TOP_CLAIMS = 3;

// Shareable unit of the /chokepoints board: #cp-<id> deep-link anchor,
// category-color left border, severity badge, top-3 claims with class
// badges + linked sources, mitigation_watch bullets, and a "also a graph
// SPOF" cross-reference badge when graph_crossref.is_articulation is true.
// Never links to the gated capture-card route — matches the house pattern
// that /resiliency doesn't link /terminal/card/risk either (CLAUDE.md §1.7:
// public pages stay NFA-safe and shareable on their own).
export default function ChokepointCard({
  cp,
  knownSymbols,
}: {
  cp: Chokepoint;
  knownSymbols: Set<string>;
}) {
  const color = categoryColor(cp.category);
  const claims = sortedClaims(cp).slice(0, TOP_CLAIMS);
  const remaining = cp.claims.length - claims.length;

  return (
    <div
      id={`cp-${cp.id}`}
      className="scroll-mt-16 rounded-sm border border-term-border bg-term-panel overflow-hidden"
      style={{ borderLeft: `4px solid ${color}` }}
    >
      <div className="px-3 py-3 space-y-2.5">
        {/* header */}
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 flex-wrap">
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
            {cp.needs_verification && (
              <span className="inline-block px-1.5 py-px text-[9.5px] uppercase tracking-wider rounded-sm border border-amber-500/50 text-amber-300 bg-amber-500/10">
                needs verification
              </span>
            )}
          </div>
          <a
            href={`#cp-${cp.id}`}
            className="text-[10px] text-zinc-600 hover:text-zinc-400"
            aria-label="Permalink to this chokepoint"
          >
            #
          </a>
        </div>

        <h3 className="text-[14px] font-semibold text-zinc-100 leading-snug">{cp.name}</h3>
        <p className="text-[11px] text-zinc-400 leading-relaxed">{cp.summary}</p>

        {/* layers */}
        {cp.layers.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {cp.layers.map((l) => (
              <LayerChip key={l} layer={l} />
            ))}
          </div>
        )}

        {/* tickers */}
        {cp.tickers.length > 0 && (
          <div className="flex flex-wrap gap-1.5 text-[10.5px]">
            {cp.tickers.map((t) =>
              knownSymbols.has(t) ? (
                <Link
                  key={t}
                  href={`/stocks/${t}`}
                  className="text-sky-400 hover:text-sky-300 hover:underline tnum"
                >
                  {t}
                </Link>
              ) : (
                <span key={t} className="text-zinc-500 tnum">
                  {t}
                </span>
              ),
            )}
          </div>
        )}

        {/* claims */}
        <div className="space-y-1.5 pt-1">
          {claims.map((c, i) => {
            const meta = claimClassMeta(c.class);
            return (
              <div key={i} className="text-[10.5px] leading-relaxed">
                <span
                  className={`inline-block mr-1.5 px-1.5 py-px text-[9px] font-semibold uppercase tracking-wider rounded-sm border align-middle ${meta.chipCls}`}
                >
                  {meta.label}
                </span>
                <span className="text-zinc-300">{c.text}</span>{" "}
                <a
                  href={c.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sky-400 hover:text-sky-300 hover:underline"
                >
                  [{c.source_name}] ↗
                </a>
              </div>
            );
          })}
          {remaining > 0 && (
            <details className="text-[10px] text-zinc-500">
              <summary className="cursor-pointer hover:text-zinc-300">
                +{remaining} more claim{remaining === 1 ? "" : "s"}
              </summary>
              <div className="mt-1.5 space-y-1.5">
                {sortedClaims(cp)
                  .slice(TOP_CLAIMS)
                  .map((c, i) => {
                    const meta = claimClassMeta(c.class);
                    return (
                      <div key={i} className="text-[10.5px] leading-relaxed">
                        <span
                          className={`inline-block mr-1.5 px-1.5 py-px text-[9px] font-semibold uppercase tracking-wider rounded-sm border align-middle ${meta.chipCls}`}
                        >
                          {meta.label}
                        </span>
                        <span className="text-zinc-300">{c.text}</span>{" "}
                        <a
                          href={c.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sky-400 hover:text-sky-300 hover:underline"
                        >
                          [{c.source_name}] ↗
                        </a>
                      </div>
                    );
                  })}
              </div>
            </details>
          )}
        </div>

        {/* mitigation watch */}
        {cp.mitigation_watch.length > 0 && (
          <div>
            <h4 className="text-[9px] font-semibold uppercase tracking-wider text-zinc-500 mb-1">
              Watching
            </h4>
            <ul className="space-y-0.5">
              {cp.mitigation_watch.map((m, i) => (
                <li key={i} className="text-[10.5px] text-zinc-400 flex gap-1.5">
                  <span className="text-zinc-600">·</span>
                  <span>{m}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* footer */}
      <div className="px-3 py-1.5 border-t border-term-border bg-[#0b0f17] flex items-center justify-between gap-2 flex-wrap">
        <span className="text-[9.5px] text-zinc-500">Reviewed {cp.last_reviewed}</span>
        {cp.graph_crossref?.is_articulation && (
          <Link
            href="/map"
            className="inline-block px-1.5 py-px text-[9px] font-semibold uppercase tracking-wider rounded-sm border border-rose-500/60 text-rose-400 bg-rose-500/10 hover:bg-rose-500/20"
          >
            ⚠ also a graph SPOF
          </Link>
        )}
      </div>
    </div>
  );
}
