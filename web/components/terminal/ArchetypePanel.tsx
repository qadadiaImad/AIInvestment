import Link from "next/link";
import type {
  ArchetypeKey,
  ArchetypeScorecard,
  ArchetypeStockRecord,
} from "@/lib/archetypes";
import {
  ARCHETYPE_COLORS,
  ARCHETYPE_LABELS,
  ARCHETYPE_SUBTITLES,
  ARCHETYPE_ORDER,
  archetypeCriterionValue,
  archetypeScoreColor,
  archetypeScoreTextClass,
  archetypeVerdictLabel,
  criterionMarkColor,
  criterionMarkGlyph,
  DASH,
} from "@/lib/format";

// Renders the three Graham/Buffett/Lynch scorecards for one stock. Pure
// Server Component — no client JS: the per-archetype criteria breakdown
// uses a native <details>/<summary> disclosure rather than client-side
// toggle state, matching this codebase's bias toward server-rendered
// terminal panels wherever no genuine interactivity is needed.
//
// Caller (app/stocks/[symbol]/page.tsx) only renders this when
// getArchetypeForSymbol() returns non-null — this component assumes a
// record exists and does not itself handle the absent case.

function ScoreDial({
  score,
  verdict,
}: {
  score: number | null;
  verdict: ArchetypeScorecard["verdict"];
}) {
  const color = archetypeScoreColor(score);
  return (
    <div className="flex flex-col items-center gap-1 shrink-0">
      <div
        className="w-14 h-14 rounded-full border-2 flex items-center justify-center text-[15px] font-bold tnum"
        style={{ borderColor: color, color }}
      >
        {score != null ? Math.round(score) : DASH}
      </div>
      <span
        className={`text-[9px] font-semibold uppercase tracking-wider ${archetypeScoreTextClass(score)}`}
      >
        {archetypeVerdictLabel(verdict)}
      </span>
    </div>
  );
}

function ScorecardCard({
  archetype,
  card,
}: {
  archetype: ArchetypeKey;
  card: ArchetypeScorecard;
}) {
  const accent = ARCHETYPE_COLORS[archetype];
  return (
    <div className="flex flex-col gap-3 rounded-sm border border-term-border bg-[#0e131d] p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-0.5">
          <span
            className="text-[13px] font-bold uppercase tracking-wide"
            style={{ color: accent }}
          >
            {ARCHETYPE_LABELS[archetype]}
          </span>
          <span className="text-[10px] text-term-muted">
            {ARCHETYPE_SUBTITLES[archetype]}
          </span>
          <span className="text-[9.5px] text-term-muted tnum mt-1">
            {card.n_pass}/{card.n_evaluable} pass · {card.n_evaluable}/
            {card.n_total} evaluable
          </span>
        </div>
        <ScoreDial score={card.score} verdict={card.verdict} />
      </div>

      {(card.likes.length > 0 || card.concerns.length > 0) && (
        <div className="flex flex-col gap-1.5">
          {card.likes.map((l, i) => (
            <div key={`like-${i}`} className="flex gap-1.5 text-[11px] leading-snug">
              <span className="text-emerald-400 shrink-0">✓</span>
              <span className="text-zinc-300">{l}</span>
            </div>
          ))}
          {card.concerns.map((c, i) => (
            <div key={`concern-${i}`} className="flex gap-1.5 text-[11px] leading-snug">
              <span className="text-rose-400 shrink-0">✗</span>
              <span className="text-zinc-300">{c}</span>
            </div>
          ))}
        </div>
      )}

      <details className="text-[11px]">
        <summary className="cursor-pointer select-none text-[10px] uppercase tracking-wider text-term-muted hover:text-zinc-200">
          Full checklist ({card.n_total})
        </summary>
        <div className="mt-2 flex flex-col gap-1.5">
          {card.criteria.map((c) => (
            <div
              key={c.key}
              className="flex items-baseline justify-between gap-2 border-t border-term-border/60 pt-1.5 first:border-t-0 first:pt-0"
            >
              <div className="flex items-baseline gap-1.5 min-w-0">
                <span
                  className="shrink-0 font-semibold"
                  style={{ color: criterionMarkColor(c.pass) }}
                >
                  {criterionMarkGlyph(c.pass)}
                </span>
                <span className="text-zinc-300 truncate">{c.label}</span>
              </div>
              <span className="shrink-0 tnum text-term-muted">
                {c.evaluable ? archetypeCriterionValue(c.actual, c.unit) : DASH}
              </span>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}

export default function ArchetypePanel({
  record,
}: {
  record: ArchetypeStockRecord;
}) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex justify-end">
        {/* Capture card lives under /terminal, gated by web/proxy.ts when
            TERMINAL_KEY is set (visitors without the key cookie get a 404;
            with the env var unset — e.g. local dev — the route is open). */}
        <Link
          href={`/terminal/card/archetype/${record.symbol}`}
          className="text-[10.5px] px-2 py-1 border border-term-border rounded-sm text-term-muted hover:text-emerald-400 hover:border-emerald-500/50"
        >
          Capture card →
        </Link>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {ARCHETYPE_ORDER.map((key) => (
          <ScorecardCard key={key} archetype={key} card={record.archetypes[key]} />
        ))}
      </div>
      {record.warnings.length > 0 && (
        <div className="text-[10px] text-amber-400 flex flex-col gap-0.5">
          {record.warnings.map((w, i) => (
            <span key={i}>⚠ {w}</span>
          ))}
        </div>
      )}
      <p className="text-[9.5px] leading-snug text-term-muted">
        Rule-based checklist against public fundamentals — deterministic, not
        a prediction, not an opinion about what Graham/Buffett/Lynch would
        actually say about this name today. Not investment advice.
      </p>
    </div>
  );
}
