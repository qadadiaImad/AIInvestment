import Link from "next/link";
import { getSiteData } from "@/lib/data";
import HomeGraph from "@/components/HomeGraph";
import ScreenerTable from "@/components/ScreenerTable";
import { LAYER_ORDER, LAYER_LABELS, LAYER_COLORS } from "@/lib/format";

// Home is a launcher, not a data dump (mobile audit, 2026-09-25). It used to
// inline the full 511-row screener under the graph, which made the phone page
// ~15,000px tall. It now shows a bounded, explicitly-sorted preview and sends
// readers to the routes that own the full datasets.
const PREVIEW_ROWS = 10;

const TASKS = [
  { href: "/screener", title: "Screen a sector", sub: "511 names · sort & filter" },
  { href: "/map", title: "Explore the map", sub: "who funds, builds, buys" },
  { href: "/news", title: "Read the news", sub: "vetted, ticker-tagged" },
  { href: "/terminal", title: "Open the TA desk", sub: "levels, macro, risk" },
];

export default function Home() {
  const data = getSiteData();

  const layerCounts = LAYER_ORDER.map((l) => ({
    key: l,
    label: LAYER_LABELS[l],
    color: LAYER_COLORS[l],
    count: (data.layers[l as keyof typeof data.layers] ?? []).length,
  }));

  // Top movers by 1-year performance; nulls sort last. The caption says what
  // the slice is so a reader never mistakes ten rows for the universe.
  const preview = [...data.screener]
    .filter((r) => typeof r.perf_1y === "number" && Number.isFinite(r.perf_1y))
    .sort((a, b) => (b.perf_1y as number) - (a.perf_1y as number))
    .slice(0, PREVIEW_ROWS);

  return (
    <div className="flex flex-col">
      {/* Stack strip */}
      <div className="flex flex-wrap items-center gap-2 px-3 py-2 border-b border-term-border text-[11px]">
        <span className="text-term-muted uppercase tracking-wider">
          AI Stack:
        </span>
        {layerCounts.map((l) => (
          <span key={l.key} className="flex items-center gap-1">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: l.color }}
            />
            <span style={{ color: l.color }}>{l.label}</span>
            <span className="text-term-muted tnum">{l.count}</span>
          </span>
        ))}
        <span className="text-term-muted tnum ml-auto">
          {data.screener.length} names · {data.capital_web.nodes.length} nodes ·{" "}
          {data.capital_web.edges.length} edges
        </span>
      </div>

      {/* Task tiles: the phone's first screen answers "where do I go" */}
      <nav
        aria-label="Start here"
        className="grid grid-cols-2 sm:grid-cols-4 gap-2 px-3 py-3 border-b border-term-border"
      >
        {TASKS.map((t) => (
          <Link
            key={t.href}
            href={t.href}
            className="flex flex-col justify-center min-h-[56px] px-3 py-2 rounded-sm border border-term-border bg-term-panel hover:border-emerald-500/60 transition-colors"
          >
            <span className="text-[12px] font-semibold text-zinc-200">
              {t.title} →
            </span>
            <span className="text-[10.5px] text-term-muted">{t.sub}</span>
          </Link>
        ))}
      </nav>

      {/* Graph hero: full graph on wide screens, tap-to-open on phones */}
      <section className="relative border-b border-term-border">
        <div className="flex items-start justify-between gap-3 px-3 py-1.5">
          <h1 className="text-[12px] font-semibold uppercase tracking-wider text-zinc-300 min-w-0">
            Capital Web — who funds, builds, and buys across the AI value chain
          </h1>
          <Link
            href="/map"
            className="text-[11px] text-blue-400 hover:text-blue-300 shrink-0 whitespace-nowrap"
          >
            Full map →
          </Link>
        </div>
        <HomeGraph web={data.capital_web} />
      </section>

      {/* Screener preview */}
      <section className="px-3 py-3 flex flex-col gap-2">
        <div className="flex items-start justify-between gap-3">
          <h2 className="text-[12px] font-semibold uppercase tracking-wider text-zinc-300 min-w-0">
            Top {preview.length} by 1-year performance
          </h2>
          <Link
            href="/screener"
            className="text-[11px] text-blue-400 hover:text-blue-300 shrink-0 whitespace-nowrap"
          >
            All {data.screener.length} names →
          </Link>
        </div>
        <ScreenerTable
          rows={preview}
          caption={`Top ${preview.length} AI-stack names by 1-year performance`}
        />
        <Link
          href="/screener"
          className="sm:hidden min-h-[44px] flex items-center justify-center rounded-sm border border-term-border text-[11px] text-term-muted uppercase tracking-wider"
        >
          Open the full screener →
        </Link>
      </section>
    </div>
  );
}
