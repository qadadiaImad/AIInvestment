// Per-stock related-news list. Server component (no interactivity) — mirrors
// the ArticleCard styling/patterns from components/NewsInteractive.tsx. Values
// come from the client-safe lib/news; types are type-only from lib/data.
//
// LEGAL/HONESTY: every article shows its OWN certainty label (filed / reported
// / rumored) — never upgraded. Graph-edge badges carry the CURATED edge's own
// certainty + source; certainty is NEVER derived from the news article.

import Link from "next/link";
import { certaintyMeta, edgeBadge } from "@/lib/news";
import type { NewsArticle, GraphEdgeRef } from "@/lib/data";
import { dateOnly, DASH } from "@/lib/format";

export default function StockNews({ articles }: { articles: NewsArticle[] }) {
  if (articles.length === 0) {
    return (
      <div className="rounded border border-term-border bg-[#0d1220] px-3 py-4 text-center text-[11px] text-term-muted">
        No recent news.
      </div>
    );
  }
  return (
    <ul className="flex flex-col gap-2">
      {articles.map((a, i) => (
        <ArticleCard key={`${a.url ?? ""}-${i}`} article={a} />
      ))}
    </ul>
  );
}

function ArticleCard({ article: a }: { article: NewsArticle }) {
  const cm = certaintyMeta(a.certainty);
  const edges = a.graph_edges ?? [];

  return (
    <li className="rounded border border-term-border bg-[#0d1220] px-3 py-2.5">
      <div className="flex items-start gap-2 flex-wrap">
        <a
          href={a.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 min-w-[60%] text-[12.5px] font-semibold leading-snug text-zinc-100 hover:text-emerald-300"
        >
          {a.title}
        </a>
        <span
          title={cm.note}
          aria-label={`Certainty: ${cm.label}. ${cm.note}`}
          className={`inline-flex items-center rounded-sm border px-1.5 py-px text-[9px] font-semibold uppercase tracking-wider cursor-help ${cm.chipCls}`}
        >
          {cm.label}
        </span>
      </div>

      {/* Source + date */}
      <div className="mt-1 flex items-center gap-2 text-[10px] text-term-muted">
        <a
          href={a.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-zinc-400 hover:text-emerald-400"
        >
          {a.source || "source"}
        </a>
        <span className="tnum">{dateOnly(a.published)}</span>
        <span className="tnum text-zinc-600">[{a.source_class || "news"}]</span>
      </div>

      {a.summary && (
        <p className="mt-1 text-[11px] leading-relaxed text-zinc-400 line-clamp-3">
          {a.summary}
        </p>
      )}

      {/* Graph-edge badges — carry the CURATED edge's own certainty + source. */}
      {edges.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {edges.map((ref, i) => (
            <EdgeBadge key={`${ref.src}-${ref.dst}-${ref.type}-${i}`} ref_={ref} />
          ))}
        </div>
      )}
    </li>
  );
}

// Graph-edge badge: "A→B · type · deal terms · certainty", linking to /map.
// The certainty shown is the CURATED edge's OWN certainty — never upgraded
// from the news item that surfaced it.
function EdgeBadge({ ref_ }: { ref_: GraphEdgeRef }) {
  const title =
    `${ref_.src} → ${ref_.dst} · ${edgeBadge(ref_)}` +
    (ref_.as_of ? ` · as of ${dateOnly(ref_.as_of)}` : "") +
    `. Curated capital-web edge — certainty is the edge's own, not derived from this news.`;
  return (
    <Link
      href="/map"
      title={title}
      aria-label={title}
      className="inline-flex items-center gap-1 rounded-sm border border-emerald-500/40 bg-emerald-500/10 px-1.5 py-px text-[9.5px] text-emerald-200/90 hover:border-emerald-400/70 hover:text-emerald-200"
    >
      <span className="font-semibold">
        {ref_.src} → {ref_.dst}
      </span>
      <span className="text-emerald-300/70">·</span>
      <span>{edgeBadge(ref_) || ref_.type || DASH}</span>
    </Link>
  );
}
