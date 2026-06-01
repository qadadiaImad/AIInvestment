import type { Metadata } from "next";
import { getNewsData } from "@/lib/data";
import type { CandidateEdge } from "@/lib/data";
import { dateOnly } from "@/lib/format";
import NewsInteractive from "@/components/NewsInteractive";

export const metadata: Metadata = {
  title: "News · AI STACK",
  description:
    "AI value-chain company news, ticker-tagged and linked to the capital-web graph. Educational research only; headlines are labeled filed / reported / rumored. Candidate deals from news are unverified and never auto-added to the graph.",
};

export default function NewsPage() {
  const data = getNewsData();

  // The news.json may not have been generated yet (the pull step is guarded).
  if (!data) {
    return (
      <div className="flex flex-col px-3 py-3 gap-4">
        <h1 className="text-[12px] font-semibold uppercase tracking-wider text-zinc-300">
          News
        </h1>
        <div
          role="status"
          className="rounded border border-term-border bg-[#0d1220] px-3 py-4 text-[11.5px] leading-relaxed text-term-muted"
        >
          No news feed has been generated yet. Once the daily news pull runs, AI
          value-chain headlines — ticker-tagged and linked to the capital-web
          graph — will appear here. Educational research only — not financial
          advice.
        </div>
      </div>
    );
  }

  const candidates = data.candidate_edges ?? [];

  return (
    <div className="flex flex-col px-3 py-3 gap-4">
      {/* Header + coverage strip */}
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <h1 className="text-[12px] font-semibold uppercase tracking-wider text-zinc-300">
          News — {data.n_articles.toLocaleString()} articles
        </h1>
        <span className="text-[10.5px] text-term-muted tnum">
          {data.n_tickers_covered.toLocaleString()} /{" "}
          {data.n_tickers_requested.toLocaleString()} tickers covered ·{" "}
          {data.key_mode} · {data.window_days}d window
          {(data.http_failed?.length ?? 0) > 0 && (
            <> · {data.http_failed.length.toLocaleString()} failed</>
          )}
        </span>
      </div>

      {/* Coverage cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <TotalCard label="Articles" value={data.n_articles.toLocaleString()} />
        <TotalCard
          label="Coverage"
          value={`${data.n_tickers_covered.toLocaleString()} / ${data.n_tickers_requested.toLocaleString()}`}
        />
        <TotalCard label="Source mode" value={data.key_mode} />
        <TotalCard label="Window" value={`${data.window_days} days`} />
      </div>

      {/* Disclaimer banner — prominent */}
      <div
        role="alert"
        className="rounded border-2 border-amber-500/80 bg-amber-500/10 px-3 py-2.5 text-amber-200"
      >
        <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-amber-300">
          <span className="text-amber-400">▲</span>
          Educational only · filed / reported / rumored · candidate edges
          unverified
        </div>
        <p className="mt-1 text-[11.5px] leading-relaxed text-amber-100/90">
          {data.disclaimer}
        </p>
      </div>

      {/* Candidate edges — possible NEW deals, NOT in the graph. */}
      {candidates.length > 0 && (
        <section className="rounded border border-amber-500/40 bg-[#0d1220] px-3 py-3">
          <div className="flex items-baseline justify-between flex-wrap gap-2">
            <h2 className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-amber-300">
              <span
                aria-hidden
                className="inline-block rounded-sm border border-amber-500/50 bg-amber-500/10 px-1.5 py-px text-[9px] font-semibold tracking-wider text-amber-300"
              >
                CANDIDATE
              </span>
              Candidate edges from news (unverified — review for /map)
            </h2>
            <span className="text-[10px] text-term-muted tnum">
              {candidates.length.toLocaleString()} candidate
              {candidates.length === 1 ? "" : "s"}
            </span>
          </div>
          <p className="mt-1 text-[10.5px] leading-relaxed text-amber-100/80">
            These are{" "}
            <strong className="text-amber-200">
              possible new relationships
            </strong>{" "}
            detected in news between two tagged entities. They are{" "}
            <strong className="text-amber-200">unverified</strong> and{" "}
            <strong className="text-amber-200">not in the graph</strong> — listed
            here only as a review queue for{" "}
            <span className="text-amber-200">/map</span>. Never treated as fact.
          </p>
          <ul className="mt-2 flex flex-col gap-1.5">
            {candidates.map((c, i) => (
              <CandidateRow key={`${c.src}-${c.dst}-${i}`} candidate={c} />
            ))}
          </ul>
        </section>
      )}

      {/* Interactive feed */}
      <NewsInteractive articles={data.articles ?? []} />

      {/* Provenance */}
      <p className="text-[10px] leading-relaxed text-term-muted border-t border-term-border pt-2">
        Source: company-news via{" "}
        <span className="tnum">[{data.source_class}]</span> ({data.key_mode}).
        Generated {dateOnly(data.generated_at)}. Headlines are labeled{" "}
        <strong className="text-zinc-300">filed / reported / rumored</strong>;
        rumors are never laundered into facts. Graph-edge badges carry the{" "}
        <strong className="text-zinc-300">curated edge&apos;s own</strong>{" "}
        certainty and source — certainty is{" "}
        <strong className="text-zinc-300">not upgraded</strong> from news.
        Candidate edges are{" "}
        <strong className="text-zinc-300">always unverified</strong> and are{" "}
        <strong className="text-zinc-300">never auto-added</strong> to the graph.
        Coverage is reported honestly ({data.n_tickers_covered.toLocaleString()}{" "}
        of {data.n_tickers_requested.toLocaleString()} tickers
        {(data.http_failed?.length ?? 0) > 0 && (
          <>, {data.http_failed.length.toLocaleString()} fetch failures</>
        )}
        ). This is{" "}
        <strong className="text-zinc-300">not financial advice</strong>.
      </p>
    </div>
  );
}

function CandidateRow({ candidate: c }: { candidate: CandidateEdge }) {
  return (
    <li className="rounded-sm border border-amber-500/30 bg-amber-500/5 px-2 py-1.5 text-[10.5px] leading-relaxed">
      <div className="flex items-center gap-1.5 flex-wrap">
        <span className="font-semibold text-amber-200">
          {c.src} → {c.dst}
        </span>
        <span className="text-amber-300/60">·</span>
        <span className="text-amber-100/90">{c.type_guess}</span>
        <span className="inline-flex items-center rounded-sm border border-amber-500/40 bg-amber-500/10 px-1 py-px text-[8.5px] font-semibold uppercase tracking-wider text-amber-300/90">
          {c.certainty}
        </span>
        <span className="inline-flex items-center rounded-sm border border-amber-500/40 bg-amber-500/10 px-1 py-px text-[8.5px] font-semibold uppercase tracking-wider text-amber-300/90">
          unverified
        </span>
        {c.detected_at && (
          <span className="ml-auto tnum text-term-muted">
            {dateOnly(c.detected_at)}
          </span>
        )}
      </div>
      <div className="mt-0.5 text-amber-100/70">
        Evidence:{" "}
        {c.url ? (
          <a
            href={c.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-amber-200/90 underline hover:text-amber-100"
          >
            {c.evidence_title}
          </a>
        ) : (
          <span>{c.evidence_title}</span>
        )}
      </div>
    </li>
  );
}

function TotalCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-term-border bg-[#0d1220] px-3 py-2">
      <div className="text-[9.5px] uppercase tracking-wider text-term-muted">
        {label}
      </div>
      <div className="mt-0.5 text-[13px] font-semibold text-zinc-100 tnum">
        {value}
      </div>
    </div>
  );
}
