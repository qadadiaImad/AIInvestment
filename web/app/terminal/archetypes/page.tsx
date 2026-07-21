import type { Metadata } from "next";
import { getArchetypeData, getArchetypeRows } from "@/lib/archetypes";
import TerminalSubNav from "@/components/terminal/TerminalSubNav";
import ArchetypeLeaderboardStrip from "@/components/terminal/ArchetypeLeaderboardStrip";
import ArchetypeScreenerTable from "@/components/terminal/ArchetypeScreenerTable";

// archetypes.json may not exist at Vercel build time (it's a gitignored,
// owner-generated file, computed from site.json by build_archetypes.py) —
// force dynamic rendering, same reasoning as terminal/risk and
// terminal/macro.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Archetypes · AI STACK TERMINAL",
  robots: { index: false, follow: false },
};

export default function ArchetypesScreenerPage() {
  const data = getArchetypeData();
  const rows = getArchetypeRows();

  return (
    <div className="flex flex-col">
      <TerminalSubNav currentPath="/terminal/archetypes" />

      <div className="px-3 py-3 flex flex-col gap-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="text-lg font-bold tracking-tight">
            INVESTOR ARCHETYPES
          </h1>
          <div className="flex items-center gap-3">
            <span className="text-[10.5px] text-term-muted tnum">
              {data ? `Updated ${data.generated_at}` : ""}
            </span>
          </div>
        </div>

        {!data ? (
          <div className="border border-term-border rounded-sm bg-[#0e131d] px-4 py-10 flex flex-col items-center justify-center text-center gap-2">
            <p className="text-[13px] text-zinc-300">
              Archetype scorecards not generated yet.
            </p>
            <p className="text-[11px] text-term-muted">
              Run build_archetypes.py on the owner&apos;s machine.
            </p>
          </div>
        ) : (
          <>
            {/* indicative disclaimer banner */}
            <div className="rounded-sm border border-amber-500/50 bg-amber-500/10 px-3 py-2 text-[11.5px] text-amber-200 leading-relaxed">
              <span className="font-semibold uppercase tracking-wider text-amber-300">
                Rule-based, not predictive.
              </span>{" "}
              Deterministic checklist against public fundamentals — not a
              prediction, not an opinion about what Graham/Buffett/Lynch
              would actually say about a name today, not investment advice.
            </div>

            <ArchetypeLeaderboardStrip top={data.top} />

            <section className="flex flex-col gap-2">
              <h2 className="text-[10.5px] font-semibold uppercase tracking-wider text-term-muted">
                Full universe ({rows.length})
              </h2>
              <ArchetypeScreenerTable rows={rows} />
            </section>

            {data.warnings.length > 0 && (
              <div className="text-[10px] text-amber-400 flex flex-col gap-0.5">
                {data.warnings.map((w, i) => (
                  <span key={i}>⚠ {w}</span>
                ))}
              </div>
            )}

            {/* footer disclaimer */}
            <section className="border-t border-term-border pt-3">
              <p className="text-term-muted text-[11px] leading-relaxed">
                {data.disclaimer} Methodology: {data.methodology_version}.
                Educational / research only — not investment advice.
              </p>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
