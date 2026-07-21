import type { Metadata } from "next";
import { getTaDeskData, getTaGroups } from "@/lib/ta";
import { TA_GROUP_ORDER } from "@/lib/format";
import SessionClockStrip from "@/components/terminal/SessionClockStrip";
import GroupSection from "@/components/terminal/GroupSection";
import TerminalSubNav from "@/components/terminal/TerminalSubNav";

export const metadata: Metadata = {
  title: "TA Desk · AI STACK TERMINAL",
  robots: { index: false, follow: false },
};

export default function TerminalPage() {
  const data = getTaDeskData();
  const groups = getTaGroups();

  return (
    <div className="flex flex-col">
      <TerminalSubNav currentPath="/terminal" />
      <SessionClockStrip />

      <div className="px-3 py-3 flex flex-col gap-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="text-lg font-bold tracking-tight">TA DESK</h1>
          <span className="text-[10.5px] text-term-muted tnum">
            {data ? `Updated ${data.generated_at}` : ""}
          </span>
        </div>

        {!data ? (
          <div className="border border-term-border rounded-sm bg-[#0e131d] px-4 py-10 flex flex-col items-center justify-center text-center gap-2">
            <p className="text-[13px] text-zinc-300">
              TA desk data not generated yet.
            </p>
            <p className="text-[11px] text-term-muted">
              Run pull_ta.py on the owner&apos;s machine.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-6">
            {TA_GROUP_ORDER.map((g) => (
              <GroupSection key={g} group={g} instruments={groups[g]} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
