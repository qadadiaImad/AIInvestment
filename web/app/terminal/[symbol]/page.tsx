import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { getTaInstrument } from "@/lib/ta";
import { DASH, num, signedPct, rsiColor } from "@/lib/format";
import TrendBadge from "@/components/terminal/TrendBadge";
import LevelsPanel from "@/components/terminal/LevelsPanel";
import PrevDayStats from "@/components/terminal/PrevDayStats";
import TradingViewChart from "@/components/TradingViewChart";

// ta_desk.json may not exist at Vercel build time (it's a gitignored,
// owner-generated file) — force dynamic rendering so this route never gets
// swept into a static-param crash at build time. No generateStaticParams.
export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ symbol: string }>;
}): Promise<Metadata> {
  const { symbol } = await params;
  const inst = getTaInstrument(symbol);
  if (!inst) return { title: "Not found · TA Desk" };
  return {
    title: `${inst.symbol} · TA Desk · AI STACK TERMINAL`,
    description: `Educational technical levels for ${inst.display_name}. Not financial advice.`,
    robots: { index: false, follow: false },
  };
}

function Panel({
  title,
  children,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`border border-term-border rounded-sm bg-[#0e131d] ${className}`}
    >
      <div className="px-3 py-1.5 border-b border-term-border text-[10.5px] font-semibold uppercase tracking-wider text-term-muted">
        {title}
      </div>
      <div className="p-3">{children}</div>
    </section>
  );
}

export default async function TerminalSymbolPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = await params;
  const inst = getTaInstrument(symbol);
  if (!inst) notFound();

  const chg = signedPct(inst.price.day_change_pct);
  const d = inst.asset_class === "fx" ? 4 : 2;
  const rsi = inst.rsi14;
  const rsiPct =
    typeof rsi.value === "number" && Number.isFinite(rsi.value)
      ? Math.min(100, Math.max(0, rsi.value))
      : null;

  return (
    <div className="px-3 py-3 flex flex-col gap-3">
      <div className="text-[10.5px] text-term-muted">
        <Link href="/terminal" className="hover:text-emerald-400">
          ta desk
        </Link>{" "}
        / <span className="text-zinc-300">{inst.symbol}</span>
      </div>

      {/* Header card */}
      <div className="flex flex-wrap items-end justify-between gap-3 border border-term-border rounded-sm bg-[#0e131d] px-3 py-2.5">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight">{inst.symbol}</h1>
          <TrendBadge state={inst.trend.state} />
          <div className="text-[11px] text-term-muted leading-tight">
            <div>{inst.display_name}</div>
            <div>{inst.group}</div>
          </div>
        </div>
        <div className="flex items-end gap-5">
          <div className="text-right">
            <div className="text-[9.5px] uppercase tracking-wider text-term-muted">
              Last
            </div>
            <div className="text-xl font-bold tnum">
              {num(inst.price.last, d)}
            </div>
          </div>
          <div className="text-right">
            <div className="text-[9.5px] uppercase tracking-wider text-term-muted">
              Day %
            </div>
            <div className={`text-base font-semibold tnum ${chg.cls}`}>
              {chg.text}
            </div>
          </div>
          <Link
            href={`/terminal/card/${inst.symbol}`}
            className="text-[10.5px] px-2 py-1 border border-term-border rounded-sm text-term-muted hover:text-emerald-400 hover:border-emerald-500/50"
          >
            Capture card →
          </Link>
        </div>
      </div>

      {/* Interactive chart */}
      <Panel title="Interactive chart (TradingView)">
        <TradingViewChart tvSymbol={inst.tv_symbol} />
      </Panel>

      {/* Levels */}
      <Panel title="Levels">
        <LevelsPanel instrument={inst} />
      </Panel>

      {/* RSI gauge */}
      <Panel title="RSI(14)">
        <div className="flex flex-col gap-2">
          <div className="relative h-2 rounded-sm overflow-hidden bg-[#1f2937]">
            {/* shaded oversold/overbought bands */}
            <div
              className="absolute inset-y-0 left-0 bg-rose-500/15"
              style={{ width: "30%" }}
            />
            <div
              className="absolute inset-y-0 right-0 bg-emerald-500/15"
              style={{ width: "30%" }}
            />
            {rsiPct != null && (
              <div
                className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-2 h-2 rounded-full border border-[#0e131d]"
                style={{ left: `${rsiPct}%`, backgroundColor: rsiColor(rsi.state) }}
              />
            )}
          </div>
          <div className="flex items-center justify-between text-[10px] text-term-muted tnum">
            <span>0</span>
            <span
              className="text-[13px] font-semibold"
              style={{ color: rsiColor(rsi.state) }}
            >
              {rsi.value != null ? rsi.value.toFixed(1) : DASH}
              {rsi.state ? ` · ${rsi.state}` : ""}
            </span>
            <span>100</span>
          </div>
        </div>
      </Panel>

      {/* Previous day OHLC */}
      <Panel title="Previous day">
        <PrevDayStats instrument={inst} />
      </Panel>

      {inst.warnings.length > 0 && (
        <div className="text-[10px] text-amber-400 flex flex-col gap-0.5">
          {inst.warnings.map((w, i) => (
            <span key={i}>⚠ {w}</span>
          ))}
        </div>
      )}

      <p className="text-[10px] text-term-muted">
        Retrieved {inst.retrieved_at}. Educational research only — not
        financial advice. Levels are computed, not predictive.
      </p>
    </div>
  );
}
