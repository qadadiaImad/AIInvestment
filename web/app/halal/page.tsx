import type { Metadata } from "next";
import { getHalalData, getHalalAlerts } from "@/lib/data";
import HalalTable from "@/components/HalalTable";
import Link from "next/link";
import type { HalalVerdict } from "@/lib/halal";
import { overallTone, fmtRatioPct } from "@/lib/halal";

export const metadata: Metadata = {
  title: "Halal Screening · AI STACK",
  description:
    "AAOIFI, FTSE Yasaar, MSCI Islamic, S&P Shariah, and DJIM ratio screens over the AI + Quantum universe — worked math, every standard, every number date-stamped. Educational research only; not financial or religious advice.",
};

// Threshold table for the methodology explainer
const STANDARD_THRESHOLDS = [
  {
    key: "AAOIFI",
    name: "AAOIFI SS 21",
    denom: "Spot market cap",
    debt: "< 30%",
    cash: "< 30%",
    recv: "—",
    activity: "< 5%",
  },
  {
    key: "FTSE",
    name: "FTSE Yasaar",
    denom: "Total assets",
    debt: "< 33.3%",
    cash: "< 33.3%",
    recv: "(receivables + cash) < 50%",
    activity: "< 5%",
  },
  {
    key: "MSCI",
    name: "MSCI Islamic",
    denom: "Total assets",
    debt: "< 33.3%",
    cash: "< 33.3%",
    recv: "(receivables + cash) < 70%",
    activity: "< 5%",
  },
  {
    key: "SP",
    name: "S&P Shariah",
    denom: "36-month avg market cap",
    debt: "< 33.3%",
    cash: "—",
    recv: "—",
    activity: "< 5% incl. all interest",
  },
  {
    key: "DJIM",
    name: "DJIM",
    denom: "24-month avg market cap",
    debt: "< 33.3%",
    cash: "—",
    recv: "—",
    activity: "< 5% incl. all interest",
  },
];

// Map overallTone values to tailwind text/bg colors for alert badges
const TONE_COLORS: Record<string, { text: string; bg: string }> = {
  pass: { text: "text-emerald-300", bg: "bg-emerald-500/15" },
  fail: { text: "text-red-300", bg: "bg-red-500/15" },
  warn: { text: "text-amber-300", bg: "bg-amber-500/15" },
  muted: { text: "text-zinc-400", bg: "bg-zinc-500/10" },
};

export default function HalalPage() {
  const data = getHalalData();
  const alertsData = getHalalAlerts();

  // Methodology explainer is always rendered — even when halal.json absent
  const Explainer = (
    <section className="flex flex-col gap-4">
      {/* Standards threshold table */}
      <div>
        <h2 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-300 mb-1.5">
          Five standards at a glance
        </h2>
        <div className="overflow-x-auto border border-term-border rounded-sm">
          <table className="term text-[10.5px]">
            <thead className="bg-[#0e131d]">
              <tr>
                <th>Standard</th>
                <th>Denominator</th>
                <th>Debt</th>
                <th>Cash</th>
                <th>Receivables</th>
                <th>Activity</th>
              </tr>
            </thead>
            <tbody>
              {STANDARD_THRESHOLDS.map((s) => (
                <tr key={s.key}>
                  <td className="font-semibold text-zinc-200">{s.name}</td>
                  <td className="text-term-muted">{s.denom}</td>
                  <td className="tnum text-amber-300">{s.debt}</td>
                  <td className="tnum text-amber-300">{s.cash}</td>
                  <td className="tnum text-amber-300">{s.recv}</td>
                  <td className="tnum text-amber-300">{s.activity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[10px] text-term-muted mt-1">
          The same company can pass one standard and fail another — denominators
          and thresholds genuinely differ. AAOIFI verdict is the primary basis
          here; FTSE, MSCI, S&amp;P Shariah, and DJIM are shown for comparison.
        </p>
        <p className="text-[10px] text-term-muted mt-1">
          Note: S&amp;P Shariah and DJIM dropped their cash and receivables
          screens in 2023, leaving only the leverage ratio and activity test.
          This is a meaningful methodological divergence from AAOIFI/FTSE/MSCI.
        </p>
      </div>

      {/* Conventions — shown only when data is loaded */}
      {data && (
        <div>
          <h2 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-300 mb-1.5">
            Disclosed v1 conventions
          </h2>
          <ol className="flex flex-col gap-1.5">
            {data.conventions.map((c, i) => (
              <li
                key={i}
                className="text-[10.5px] leading-relaxed text-term-muted border-l-2 border-term-border pl-2"
              >
                <span className="text-zinc-400 font-semibold">{i + 1}.</span>{" "}
                {c}
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  );

  // Empty state when halal.json not yet generated
  if (!data) {
    return (
      <div className="flex flex-col px-3 py-3 gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-[12px] font-semibold uppercase tracking-wider text-zinc-300">
            Halal screening — the worked math, every standard, every number
            stamped.
          </h1>
          <p className="text-[11px] text-term-muted leading-relaxed">
            AAOIFI SS 21, FTSE Yasaar, MSCI Islamic, S&amp;P Shariah, and DJIM
            ratio screens applied to the full AI + Quantum investment universe —
            with the worked math shown for every test.
          </p>
        </div>

        {Explainer}

        <div
          role="status"
          className="rounded border border-term-border bg-[#0d1220] px-3 py-4 text-[11.5px] leading-relaxed text-term-muted"
        >
          Screening data not yet generated. Run{" "}
          <code className="text-zinc-300">python pull_halal.py</code> then{" "}
          <code className="text-zinc-300">python export_halal.py</code> to
          produce the screening bundle. Computed from published methodologies —
          we are not a Sharia board. Educational only; not financial or religious
          advice.
        </div>
      </div>
    );
  }

  // Build sorted verdict list: halal first, then symbol
  const verdicts: HalalVerdict[] = Object.values(data.verdicts).sort((a, b) => {
    const ORDER = ["halal", "questionable", "insufficient_data", "not_halal"];
    const oa = ORDER.indexOf(a.overall);
    const ob = ORDER.indexOf(b.overall);
    if (oa !== ob) return oa - ob;
    return a.symbol.localeCompare(b.symbol);
  });

  const counts: Record<string, number> = {};
  for (const v of verdicts) {
    counts[v.overall] = (counts[v.overall] ?? 0) + 1;
  }

  return (
    <div className="flex flex-col px-3 py-3 gap-4">
      {/* Hero */}
      <div className="flex flex-col gap-1">
        <div className="flex items-baseline justify-between flex-wrap gap-2">
          <h1 className="text-[12px] font-semibold uppercase tracking-wider text-zinc-300">
            Halal screening — the worked math, every standard, every number
            stamped.
          </h1>
          <span className="text-[10px] tnum text-term-muted">
            Generated {data.generated_at}
          </span>
        </div>
        <p className="text-[11px] text-term-muted leading-relaxed">
          {data.methodology_note}
        </p>
      </div>

      {/* Summary counts */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {(
          [
            ["halal", "Halal", "#10b981"],
            ["questionable", "Questionable", "#f59e0b"],
            ["insufficient_data", "Insufficient data", "#6b7280"],
            ["not_halal", "Not halal", "#ef4444"],
          ] as const
        ).map(([key, label, color]) => (
          <div
            key={key}
            className="rounded border border-term-border bg-[#0d1220] px-3 py-2"
          >
            <div className="text-[9.5px] uppercase tracking-wider text-term-muted">
              {label}
            </div>
            <div
              className="mt-0.5 text-[15px] font-semibold tnum"
              style={{ color }}
            >
              {counts[key] ?? 0}
            </div>
          </div>
        ))}
      </div>

      {/* Disclaimer — prominent */}
      <div
        role="alert"
        className="rounded border-2 border-amber-500/80 bg-amber-500/10 px-3 py-2.5 text-amber-200"
      >
        <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-amber-300">
          <span className="text-amber-400">▲</span>
          Computed methodology results — not a fatwa — not financial advice
        </div>
        <p className="mt-1 text-[11.5px] leading-relaxed text-amber-100/90">
          {data.disclaimer}
        </p>
      </div>

      {/* Methodology explainer */}
      {Explainer}

      {/* What changed — compliance-change alerts feed */}
      <section className="flex flex-col gap-2">
        <h2 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-300">
          What changed
        </h2>
        {!alertsData || alertsData.alerts.length === 0 ? (
          <p className="text-[10.5px] text-term-muted">
            No compliance changes recorded yet.
          </p>
        ) : (
          <div className="flex flex-col gap-1.5">
            {alertsData.alerts.map((alert, i) => {
              const fromTone = TONE_COLORS[overallTone(alert.from as Parameters<typeof overallTone>[0])] ?? TONE_COLORS.muted;
              const toTone = TONE_COLORS[overallTone(alert.to as Parameters<typeof overallTone>[0])] ?? TONE_COLORS.muted;
              return (
                <div
                  key={i}
                  className="rounded border border-term-border bg-[#0d1220] px-3 py-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[10.5px]"
                >
                  {/* Symbol link */}
                  <Link
                    href={`/stocks/${alert.symbol}`}
                    className="font-semibold text-zinc-200 hover:text-white underline-offset-2 hover:underline"
                  >
                    {alert.symbol}
                  </Link>
                  {/* Date */}
                  <span className="tnum text-term-muted">{alert.date}</span>
                  {/* from → to badges */}
                  <span className="flex items-center gap-1">
                    <span
                      className={`rounded px-1.5 py-0.5 text-[9.5px] font-semibold uppercase tracking-wider ${fromTone.bg} ${fromTone.text}`}
                    >
                      {alert.from.replace(/_/g, " ")}
                    </span>
                    <span className="text-term-muted">→</span>
                    <span
                      className={`rounded px-1.5 py-0.5 text-[9.5px] font-semibold uppercase tracking-wider ${toTone.bg} ${toTone.text}`}
                    >
                      {alert.to.replace(/_/g, " ")}
                    </span>
                  </span>
                  {/* Worked before/after */}
                  {alert.old_value !== null || alert.new_value !== null ? (
                    <span className="tnum text-term-muted">
                      {fmtRatioPct(alert.old_value)}
                      <span className="mx-1">→</span>
                      {fmtRatioPct(alert.new_value)}
                      {alert.threshold !== null && (
                        <span className="ml-1 text-zinc-500">
                          (limit {fmtRatioPct(alert.threshold)})
                        </span>
                      )}
                    </span>
                  ) : null}
                  {/* Driver test label */}
                  {alert.driver_test && alert.driver_test !== "overall" && (
                    <span className="text-zinc-500 text-[9.5px]">
                      {alert.driver_test}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Interactive table */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <h2 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-300">
            Screening results — {verdicts.length} names
          </h2>
          <span className="text-[10.5px] text-term-muted">
            Click any column header to sort · click a symbol for the full sheet
          </span>
        </div>
        <HalalTable verdicts={verdicts} />
      </div>

      {/* Provenance footer */}
      <p className="text-[10px] leading-relaxed text-term-muted border-t border-term-border pt-2">
        Ratios computed from TradingView balance-sheet scanner (REST). Business
        activity from curated seed (2026-07-21). Standards: AAOIFI SS 21, FTSE
        Yasaar v4.6 (Feb 2026), MSCI Islamic (Dec 2025), S&amp;P Shariah (May
        2025 ed.), DJIM (May 2025 ed.). S&amp;P and DJIM leverage screens use a
        trailing-average market cap with a constant-shares approximation (see
        conventions). Verdicts are computed methodology results, not fatwas.
        Educational only — not financial or religious advice.
      </p>
    </div>
  );
}
