"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { NewsArticle, GraphEdgeRef, Certainty } from "@/lib/news";
import { certaintyMeta, edgeBadge } from "@/lib/news";
import { dateOnly, DASH } from "@/lib/format";

type CertaintyFilter = "" | Certainty;

const PAGE_SIZE = 50;

// Parse an ISO/date-like string into a sortable timestamp (NaN-safe).
function ts(d: string | null | undefined): number {
  if (!d) return -Infinity;
  const t = Date.parse(d);
  return Number.isNaN(t) ? -Infinity : t;
}

interface Props {
  articles: NewsArticle[];
}

export default function NewsInteractive({ articles }: Props) {
  const [query, setQuery] = useState("");
  const [ticker, setTicker] = useState("");
  const [certainty, setCertainty] = useState<CertaintyFilter>("");
  const [linkedOnly, setLinkedOnly] = useState(false);
  const [page, setPage] = useState(0);

  // Distinct ticker options across all articles, alphabetical.
  const tickerOptions = useMemo(() => {
    const set = new Set<string>();
    for (const a of articles) {
      for (const t of a.tickers ?? []) set.add(t);
    }
    return [...set].sort((a, b) => a.localeCompare(b));
  }, [articles]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let rows = articles.filter((a) => {
      if (ticker && !(a.tickers ?? []).includes(ticker)) return false;
      if (certainty && a.certainty !== certainty) return false;
      if (linkedOnly && !((a.graph_edges?.length ?? 0) > 0)) return false;
      if (q) {
        const hay = `${a.title ?? ""} ${a.source ?? ""} ${
          a.summary ?? ""
        } ${(a.tickers ?? []).join(" ")}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
    rows = [...rows];
    rows.sort((a, b) => ts(b.published) - ts(a.published));
    return rows;
  }, [articles, query, ticker, certainty, linkedOnly]);

  const linkedCount = useMemo(
    () => articles.filter((a) => (a.graph_edges?.length ?? 0) > 0).length,
    [articles],
  );

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages - 1);
  const pageRows = useMemo(
    () => filtered.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE),
    [filtered, safePage],
  );

  function resetPageAnd(fn: () => void) {
    fn();
    setPage(0);
  }

  const inputCls =
    "rounded border border-term-border bg-[#11182a] px-2 py-1 text-[11px] text-zinc-200 focus:outline-none focus:border-emerald-500/70 focus:ring-1 focus:ring-emerald-500/50";

  return (
    <div className="flex flex-col gap-3">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => resetPageAnd(() => setQuery(e.target.value))}
          placeholder="Search headline, source, ticker…"
          aria-label="Search news"
          className={`${inputCls} w-[260px]`}
        />
        <label className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-term-muted">
          Ticker
          <select
            value={ticker}
            onChange={(e) => resetPageAnd(() => setTicker(e.target.value))}
            aria-label="Filter by ticker"
            className={inputCls}
          >
            <option value="">All tickers</option>
            {tickerOptions.map((t) => (
              <option key={t} value={t} className="bg-[#11182a] text-zinc-200">
                {t}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-term-muted">
          Certainty
          <select
            value={certainty}
            onChange={(e) =>
              resetPageAnd(() =>
                setCertainty(e.target.value as CertaintyFilter),
              )
            }
            aria-label="Filter by certainty"
            className={inputCls}
          >
            <option value="">All certainty</option>
            <option value="filed">Filed</option>
            <option value="reported">Reported</option>
            <option value="rumored">Rumored</option>
          </select>
        </label>
        {linkedCount > 0 && (
          <label
            className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-sky-300/90 cursor-pointer select-none"
            title="Show only articles that touch a curated capital-web edge. Badges carry the edge's own certainty — not upgraded from news."
          >
            <input
              type="checkbox"
              checked={linkedOnly}
              onChange={(e) =>
                resetPageAnd(() => setLinkedOnly(e.target.checked))
              }
              aria-label="Show only graph-linked articles"
              className="h-3 w-3 accent-sky-500"
            />
            Graph-linked only
            <span className="text-sky-400/60 tnum">
              ({linkedCount.toLocaleString()})
            </span>
          </label>
        )}
        <span className="ml-auto text-[10.5px] text-term-muted tnum">
          {filtered.length.toLocaleString()} articles
        </span>
      </div>

      {/* Feed */}
      <ul className="flex flex-col gap-2">
        {pageRows.map((a, i) => (
          <ArticleCard key={`${a.url ?? ""}-${i}`} article={a} />
        ))}
        {pageRows.length === 0 && (
          <li className="rounded border border-term-border bg-[#0d1220] px-3 py-4 text-center text-[11px] text-term-muted">
            No articles match these filters.
          </li>
        )}
      </ul>

      {/* Pagination */}
      {filtered.length > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-3 text-[11px]">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={safePage === 0}
            className="rounded border border-term-border bg-[#11182a] px-2 py-1 text-zinc-300 hover:border-emerald-500/70 hover:text-emerald-400 disabled:opacity-40 disabled:hover:border-term-border disabled:hover:text-zinc-300"
          >
            ← Prev
          </button>
          <span className="tnum text-term-muted">
            Page {safePage + 1} / {totalPages} ·{" "}
            {(safePage * PAGE_SIZE + 1).toLocaleString()}–
            {Math.min(
              (safePage + 1) * PAGE_SIZE,
              filtered.length,
            ).toLocaleString()}{" "}
            of {filtered.length.toLocaleString()}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={safePage >= totalPages - 1}
            className="rounded border border-term-border bg-[#11182a] px-2 py-1 text-zinc-300 hover:border-emerald-500/70 hover:text-emerald-400 disabled:opacity-40 disabled:hover:border-term-border disabled:hover:text-zinc-300"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

function ArticleCard({ article: a }: { article: NewsArticle }) {
  const cm = certaintyMeta(a.certainty);
  const edges = a.graph_edges ?? [];
  const candidates = a.candidate_edges ?? [];
  const hasCandidate = candidates.length > 0;

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
        <span className="tnum text-zinc-600">
          [{a.source_class || "news"}]
        </span>
      </div>

      {a.summary && (
        <p className="mt-1 text-[11px] leading-relaxed text-zinc-400 line-clamp-3">
          {a.summary}
        </p>
      )}

      {/* Ticker chips */}
      {(a.tickers?.length ?? 0) > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {a.tickers.map((t) => (
            <Link
              key={t}
              href={`/stocks/${t}`}
              className="inline-flex items-center rounded-sm border border-term-border bg-[#11182a] px-1.5 py-0.5 text-[10px] font-semibold text-sky-400 hover:border-sky-500/60 hover:text-sky-300"
            >
              {t}
            </Link>
          ))}
        </div>
      )}

      {/* Graph-edge badges — carry the CURATED edge's own certainty + source. */}
      {edges.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {edges.map((ref, i) => (
            <EdgeBadge key={`${ref.src}-${ref.dst}-${ref.type}-${i}`} ref_={ref} />
          ))}
        </div>
      )}

      {/* Candidate-edge flag — possible NEW deal, unverified, not in graph. */}
      {hasCandidate && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {candidates.map((c, i) => (
            <span
              key={`${c.src}-${c.dst}-${i}`}
              title={`Possible new deal between ${c.src} and ${c.dst} (${c.type_guess}) detected in news — UNVERIFIED, not in the graph. Review for /map.`}
              className="inline-flex items-center gap-1 rounded-sm border border-amber-500/40 bg-amber-500/10 px-1.5 py-px text-[9px] font-semibold uppercase tracking-wider text-amber-300/90 cursor-help"
            >
              ◇ possible new deal · unverified
            </span>
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
