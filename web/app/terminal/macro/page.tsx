import type { Metadata } from "next";
import Link from "next/link";
import { getMacroData, getMacroGroups } from "@/lib/macro";
import { MACRO_GROUP_ORDER } from "@/lib/format";
import TerminalSubNav from "@/components/terminal/TerminalSubNav";
import MacroRegimeStrip from "@/components/terminal/MacroRegimeStrip";
import MacroGroupSection from "@/components/terminal/MacroGroupSection";

// macro.json may not exist at Vercel build time (it's a gitignored, owner-
// generated file) — force dynamic rendering, same reasoning as
// terminal/risk/page.tsx.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Macro Desk · AI STACK TERMINAL",
  robots: { index: false, follow: false },
};

export default function MacroDeskPage() {
  const data = getMacroData();
  const groups = getMacroGroups();

  return (
    <div className="flex flex-col">
      <TerminalSubNav currentPath="/terminal/macro" />

      <div className="px-3 py-3 flex flex-col gap-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="text-lg font-bold tracking-tight">MACRO DESK</h1>
          <div className="flex items-center gap-3">
            <span className="text-[10.5px] text-term-muted tnum">
              {data ? `Updated ${data.generated_at}` : ""}
            </span>
            {data && (
              <Link
                href="/terminal/card/macro"
                className="text-[10.5px] px-2 py-1 border border-term-border rounded-sm text-term-muted hover:text-emerald-400 hover:border-emerald-500/50"
              >
                Capture card →
              </Link>
            )}
          </div>
        </div>

        {!data ? (
          <div className="border border-term-border rounded-sm bg-[#0e131d] px-4 py-10 flex flex-col items-center justify-center text-center gap-2">
            <p className="text-[13px] text-zinc-300">
              Macro desk data not generated yet.
            </p>
            <p className="text-[11px] text-term-muted">
              Run pull_macro.py on the owner&apos;s machine.
            </p>
          </div>
        ) : (
          <>
            {/* indicative disclaimer banner */}
            <div className="rounded-sm border border-amber-500/50 bg-amber-500/10 px-3 py-2 text-[11.5px] text-amber-200 leading-relaxed">
              <span className="font-semibold uppercase tracking-wider text-amber-300">
                Indicative only.
              </span>{" "}
              Regime labels are rule-based descriptive flags, not
              predictions — not investment advice.
            </div>

            <MacroRegimeStrip chips={data.regime.chips} />

            {data.regime.headline && (
              <p className="text-[11px] text-zinc-300">
                {data.regime.headline}
              </p>
            )}

            {MACRO_GROUP_ORDER.map((group) => (
              <MacroGroupSection
                key={group}
                group={group}
                series={groups[group]}
              />
            ))}

            {data.warnings.length > 0 && (
              <div className="text-[10px] text-amber-400 flex flex-col gap-0.5">
                {data.warnings.map((w, i) => (
                  <span key={i}>⚠ {w}</span>
                ))}
              </div>
            )}

            {/* footer disclaimer — release-lag caveat, not a VaR-style
                model caveat: macro series are lagging/backward-looking by
                construction (FRED release schedules), not a predictive
                risk model. */}
            <section className="border-t border-term-border pt-3">
              <p className="text-term-muted text-[11px] leading-relaxed">
                {data.disclaimer} Macro series are release-lagged
                (rates/VIX daily, CPI/electricity monthly, Fed balance sheet
                weekly) and backward-looking — they describe the current
                policy/liquidity backdrop, not a forecast. Educational /
                research only — not investment advice.
              </p>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
