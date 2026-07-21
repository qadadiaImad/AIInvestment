// Server Component — zero client JS. Native <details> accordions only.
// Renders the per-stock halal verdict card ("Show the math") per Task 9
// of docs/superpowers/plans/2026-07-21-halal-screening-v1.md §7.
//
// Verdict precedence (AAOIFI basis): halal | not_halal | questionable |
// insufficient_data.  Missing/dirty inputs render as "—" or
// "Insufficient data" — never silently pass.
//
// Computed methodology results, NOT fatwas. Educational only —
// not financial or religious advice.

import type {
  HalalVerdict,
  HalalStandardResult,
  HalalTestResult,
} from "@/lib/halal";
import { overallLabel, overallTone, fmtRatioPct } from "@/lib/halal";

// ---- styling helpers ----

const TONE_BADGE: Record<string, string> = {
  pass: "text-emerald-400 border-emerald-500/50 bg-emerald-500/10",
  fail: "text-rose-400 border-rose-500/50 bg-rose-500/10",
  warn: "text-amber-400 border-amber-500/50 bg-amber-500/10",
  muted: "text-zinc-400 border-zinc-500/50 bg-zinc-500/10",
};

const STATUS_CHIP: Record<string, string> = {
  pass: "text-emerald-400 bg-emerald-500/10",
  fail: "text-rose-400 bg-rose-500/10",
  unknown: "text-zinc-400 bg-zinc-500/10",
};

function toneClass(tone: string): string {
  return TONE_BADGE[tone] ?? TONE_BADGE.muted;
}

function statusChip(status: string): string {
  return STATUS_CHIP[status] ?? STATUS_CHIP.unknown;
}

function marginColor(margin: number | null): string {
  if (margin === null) return "text-zinc-400";
  return margin >= 0 ? "text-emerald-400" : "text-rose-400";
}

const DASH = "—";

function fmtNum(v: number | null, decimals = 2): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return DASH;
  return v.toLocaleString("en-US", {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
  });
}

function dateSlice(iso: string | null): string {
  if (!iso) return DASH;
  return iso.slice(0, 10);
}

// ---- sub-components (all server) ----

function TestRow({ t }: { t: HalalTestResult }) {
  return (
    <>
      <tr className="border-t border-term-border/40">
        <td className="py-1 pr-2 text-zinc-300 text-[11px]">{t.label}</td>
        <td className="py-1 pr-2 text-right tnum text-[11px] text-zinc-300">
          {t.numerator_value !== null ? fmtNum(t.numerator_value / 1e9) + "B" : DASH}
        </td>
        <td className="py-1 pr-2 text-right tnum text-[11px] text-zinc-300">
          {t.denominator_value !== null ? fmtNum(t.denominator_value / 1e9) + "B" : DASH}
        </td>
        <td className="py-1 pr-2 text-right tnum text-[11px]">
          {fmtRatioPct(t.ratio)}
        </td>
        <td className="py-1 pr-2 text-right tnum text-[11px] text-term-muted">
          {fmtRatioPct(t.threshold)}
        </td>
        <td
          className={`py-1 pr-2 text-right tnum text-[11px] ${marginColor(t.margin)}`}
        >
          {t.margin !== null ? fmtRatioPct(t.margin) : DASH}
        </td>
        <td className="py-1 text-right">
          <span
            className={`text-[9.5px] px-1 py-0.5 rounded-sm font-semibold uppercase ${statusChip(t.status)}`}
          >
            {t.status}
          </span>
        </td>
      </tr>
      <tr>
        <td
          colSpan={7}
          className="pb-1.5 text-[9px] text-term-muted leading-snug"
        >
          {t.citation}
        </td>
      </tr>
    </>
  );
}

function StandardDetails({ std }: { std: HalalStandardResult }) {
  const tone =
    std.status === "pass"
      ? "pass"
      : std.status === "fail"
        ? "fail"
        : "muted";
  return (
    <details className="border border-term-border/60 rounded-sm">
      <summary className="cursor-pointer select-none px-3 py-2 flex items-center gap-2 text-[11px] font-semibold text-zinc-300 hover:bg-white/5">
        <span>{std.name}</span>
        <span
          className={`text-[9.5px] px-1.5 py-px rounded-sm uppercase font-semibold ${statusChip(tone)}`}
        >
          {std.status}
        </span>
      </summary>
      <div className="px-3 pb-3">
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="text-term-muted text-[9.5px] uppercase tracking-wider">
                <th className="text-left pb-1 pr-2">Test</th>
                <th className="text-right pb-1 pr-2">Numerator</th>
                <th className="text-right pb-1 pr-2">Denominator</th>
                <th className="text-right pb-1 pr-2">Ratio</th>
                <th className="text-right pb-1 pr-2">Threshold</th>
                <th className="text-right pb-1 pr-2">Margin</th>
                <th className="text-right pb-1">Status</th>
              </tr>
            </thead>
            <tbody>
              {std.tests.map((t) => (
                <TestRow key={t.id} t={t} />
              ))}
              {/* Activity row */}
              <tr className="border-t border-term-border/40">
                <td className="py-1 pr-2 text-zinc-300 text-[11px]">
                  Business activity (impermissible income &lt;{std.activity_threshold_pct}%)
                </td>
                <td colSpan={5} className="py-1 text-term-muted text-[11px] pr-2">
                  {/* activity uses curated data, not a ratio */}
                  see business block below
                </td>
                <td className="py-1 text-right">
                  <span
                    className={`text-[9.5px] px-1 py-0.5 rounded-sm font-semibold uppercase ${statusChip(std.activity_status === "unknown" ? "unknown" : std.activity_status)}`}
                  >
                    {std.activity_status}
                  </span>
                </td>
              </tr>
              <tr>
                <td
                  colSpan={7}
                  className="pb-1.5 text-[9px] text-term-muted"
                >
                  {std.activity_citation}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </details>
  );
}

// ---- public component ----

export interface HalalCardProps {
  verdict: HalalVerdict;
  disclaimer: string;
  conventions: string[];
}

export default function HalalCard({
  verdict,
  disclaimer,
  conventions,
}: HalalCardProps) {
  const tone = overallTone(verdict.overall);
  const label = overallLabel(verdict.overall);
  const biz = verdict.business;
  const pur = verdict.purification;

  return (
    <section className="border border-term-border rounded-sm bg-[#0e131d]">
      {/* Section header */}
      <div className="px-3 py-1.5 border-b border-term-border text-[10.5px] font-semibold uppercase tracking-wider text-term-muted">
        Halal screening — the worked math
      </div>

      <div className="p-3 flex flex-col gap-3">
        {/* Header row: verdict badge + basis + data age */}
        <div className="flex flex-wrap items-center gap-3">
          <span
            className={`text-[12px] font-bold px-2 py-0.5 rounded-sm border ${toneClass(tone)}`}
          >
            {label}
          </span>
          <span className="text-[10px] text-term-muted">
            Basis: {verdict.overall_basis}
          </span>
          {verdict.inputs_asof && (
            <span className="text-[10px] text-term-muted">
              Data as of {dateSlice(verdict.inputs_asof)}
            </span>
          )}
        </div>

        {/* Per-standard accordions */}
        <div className="flex flex-col gap-1.5">
          {Object.values(verdict.standards).map((std) => (
            <StandardDetails key={std.key} std={std} />
          ))}
        </div>

        {/* Business block */}
        <div className="border border-term-border/60 rounded-sm px-3 py-2">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-term-muted mb-1.5">
            Business activity
          </div>
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded-sm font-semibold uppercase ${statusChip(biz.status === "clean" ? "pass" : biz.status === "prohibited" ? "fail" : biz.status === "questionable" ? "unknown" : "unknown")}`}
            >
              {biz.status}
            </span>
            {biz.categories && biz.categories.length > 0 && (
              <span className="text-[10px] text-zinc-400">
                {biz.categories.join(", ")}
              </span>
            )}
            {biz.confidence && (
              <span className="text-[10px] text-term-muted">
                confidence: {biz.confidence}
              </span>
            )}
            {biz.last_reviewed && (
              <span className="text-[10px] text-term-muted">
                reviewed: {biz.last_reviewed}
              </span>
            )}
          </div>
          {/* Methodology notes (AAOIFI fork, sector-exclusion fork, etc.) */}
          {biz.methodology_notes &&
            Object.entries(biz.methodology_notes).length > 0 && (
              <div className="text-[10.5px] text-zinc-300 mb-1.5 flex flex-col gap-0.5">
                {Object.entries(biz.methodology_notes).map(([key, note]) => (
                  <div key={key}>
                    <span className="font-semibold capitalize">
                      {key.replace(/_/g, " ")}:
                    </span>{" "}
                    <span
                      className={
                        note.stance === "pass"
                          ? "text-emerald-400"
                          : note.stance === "fail"
                            ? "text-rose-400"
                            : "text-amber-400"
                      }
                    >
                      {note.stance}
                    </span>{" "}
                    — {note.reason}
                  </div>
                ))}
              </div>
            )}
          {biz.note && (
            <p className="text-[10.5px] text-zinc-400 mb-1.5">{biz.note}</p>
          )}
          {biz.impermissible_revenue_pct?.value != null && (
            <p className="text-[10.5px] text-zinc-300 mb-1.5">
              Impermissible revenue:{" "}
              <span className="tnum text-amber-400">
                {fmtRatioPct(biz.impermissible_revenue_pct.value / 100)}
              </span>
              {biz.impermissible_revenue_pct.basis && (
                <span className="text-term-muted">
                  {" "}({biz.impermissible_revenue_pct.basis})
                </span>
              )}
            </p>
          )}
          {biz.evidence && (
            <blockquote className="border-l-2 border-amber-500/60 pl-2 text-[10px] text-zinc-400 italic">
              &ldquo;{biz.evidence.quote}&rdquo;{" "}
              <a
                href={biz.evidence.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-emerald-400 hover:text-emerald-300 not-italic"
              >
                [source]
              </a>{" "}
              <span className="text-term-muted not-italic">
                ({dateSlice(biz.evidence.retrieved_at)})
              </span>
            </blockquote>
          )}
        </div>

        {/* Purification block */}
        <div className="border border-term-border/60 rounded-sm px-3 py-2">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-term-muted mb-1.5">
            Purification (AAOIFI 3/4/6)
          </div>
          {pur.status === "computed" && pur.per_share !== null ? (
            <>
              <div className="text-[12px] text-zinc-200 tnum mb-0.5">
                {fmtNum(pur.per_share, 4)} per share
              </div>
              {pur.basis && (
                <p className="text-[9.5px] text-term-muted">{pur.basis}</p>
              )}
            </>
          ) : (
            <p className="text-[10.5px] text-zinc-400">
              Insufficient data
              {pur.missing ? ` — ${pur.missing}` : ""}
            </p>
          )}
        </div>

        {/* Footer: disclaimer + conventions accordion */}
        <details className="border border-term-border/40 rounded-sm text-[10px]">
          <summary className="cursor-pointer select-none px-2 py-1.5 text-term-muted hover:bg-white/5">
            Disclaimer &amp; our disclosed conventions
          </summary>
          <div className="px-3 pb-3 flex flex-col gap-2">
            <p className="text-[9.5px] text-term-muted leading-snug mt-2">
              {disclaimer}
            </p>
            <div className="text-[9.5px] font-semibold uppercase tracking-wider text-term-muted">
              Disclosed conventions
            </div>
            <ol className="list-decimal pl-4 flex flex-col gap-1 text-[9.5px] text-zinc-400">
              {conventions.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ol>
          </div>
        </details>
      </div>
    </section>
  );
}
