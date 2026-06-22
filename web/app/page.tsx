import Link from "next/link";
import { getSiteData } from "@/lib/data";
import CapitalGraph from "@/components/CapitalGraph";
import ScreenerTable from "@/components/ScreenerTable";
import { LAYER_ORDER, LAYER_LABELS, LAYER_COLORS } from "@/lib/format";

export default function Home() {
  const data = getSiteData();

  const layerCounts = LAYER_ORDER.map((l) => ({
    key: l,
    label: LAYER_LABELS[l],
    color: LAYER_COLORS[l],
    count: (data.layers[l as keyof typeof data.layers] ?? []).length,
  }));

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

      {/* Graph hero */}
      <section className="relative border-b border-term-border">
        <div className="flex items-center justify-between px-3 py-1.5">
          <h1 className="text-[12px] font-semibold uppercase tracking-wider text-zinc-300">
            Capital Web — who funds, builds, and buys across the AI value chain
          </h1>
          <Link
            href="/map"
            className="text-[11px] text-blue-400 hover:text-blue-300"
          >
            Full map →
          </Link>
        </div>
        <div className="h-[58vh] min-h-[380px] w-full bg-[#0b0f17]">
          <CapitalGraph web={data.capital_web} />
        </div>
      </section>

      {/* Screener */}
      <section className="px-3 py-3 flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h2 className="text-[12px] font-semibold uppercase tracking-wider text-zinc-300">
            Screener — {data.screener.length} names (click headers to sort)
          </h2>
          <Link
            href="/screener"
            className="text-[11px] text-blue-400 hover:text-blue-300"
          >
            Open screener →
          </Link>
        </div>
        <ScreenerTable rows={data.screener} caption="AI-stack screener" />
      </section>
    </div>
  );
}
