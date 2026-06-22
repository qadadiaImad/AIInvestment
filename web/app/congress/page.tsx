import type { Metadata } from "next";
import { getCongressData } from "@/lib/data";
import { usd, dateOnly } from "@/lib/format";
import CongressInteractive from "@/components/CongressInteractive";

export const metadata: Metadata = {
  title: "Congress · AI STACK",
  description:
    "U.S. House STOCK Act trade disclosures by sector — sortable, filterable, with per-member drill-down. Educational research only; amounts are reported ranges with up to a 45-day filing lag. Not an accusation.",
};

export default function CongressPage() {
  const data = getCongressData();
  const t = data.totals;

  return (
    <div className="flex flex-col px-3 py-3 gap-4">
      {/* Header + totals */}
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <h1 className="text-[12px] font-semibold uppercase tracking-wider text-zinc-300">
          Congress — {t.n_trades.toLocaleString()} disclosed trades
        </h1>
        <span className="text-[10.5px] text-term-muted tnum">
          {dateOnly(t.date_min)} → {dateOnly(t.date_max)} ·{" "}
          {t.n_politicians} members · {t.n_tickers.toLocaleString()} tickers ·{" "}
          {t.n_sectors} sectors
        </span>
      </div>

      {/* Totals strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <TotalCard label="Trades" value={t.n_trades.toLocaleString()} />
        <TotalCard label="Members" value={t.n_politicians.toLocaleString()} />
        <TotalCard
          label="Est. volume"
          value={`${usd(t.est_volume_low)}–${usd(t.est_volume_high)}`}
        />
        <TotalCard
          label="Date range"
          value={`${dateOnly(t.date_min)} → ${dateOnly(t.date_max)}`}
        />
      </div>

      {/* Disclaimer banner — prominent */}
      <div
        role="alert"
        className="rounded border-2 border-amber-500/80 bg-amber-500/10 px-3 py-2.5 text-amber-200"
      >
        <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-amber-300">
          <span className="text-amber-400">▲</span>
          Educational only · reported ranges · ~45-day lag · not an accusation
        </div>
        <p className="mt-1 text-[11.5px] leading-relaxed text-amber-100/90">
          {data.disclaimer}
        </p>
      </div>

      {/* Committee-overlap signal explainer (collapsible) */}
      {(t.n_conflict_flagged ?? 0) > 0 && (
        <details className="rounded border border-term-border bg-[#0d1220] px-3 py-2 [&_summary::-webkit-details-marker]:hidden">
          <summary className="flex cursor-pointer items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-zinc-300 select-none">
            <span
              aria-hidden
              className="inline-block rounded-sm border border-amber-500/50 bg-amber-500/10 px-1.5 py-px text-[9px] font-semibold tracking-wider text-amber-300"
            >
              COMMITTEE OVERLAP
            </span>
            What does &ldquo;committee overlap&rdquo; mean?
            <span className="ml-auto text-[10px] font-normal text-term-muted">
              {t.n_conflict_flagged?.toLocaleString()} of{" "}
              {t.n_trades.toLocaleString()} trades flagged · tap to expand
            </span>
          </summary>
          <div className="mt-2 space-y-1.5 text-[11px] leading-relaxed text-zinc-400">
            <p>
              A trade is tagged{" "}
              <span className="text-amber-300">committee overlap</span> when two
              public facts line up: (1) the member factually serves on a
              congressional committee, and (2) the traded stock falls in a
              sector that committee has curated, approximate jurisdiction over.
            </p>
            <p>
              This is a{" "}
              <strong className="text-zinc-300">
                correlational overlap only
              </strong>{" "}
              — it is <strong className="text-zinc-300">not</strong> evidence of
              wrongdoing, insider trading, conflict of interest, or any improper
              conduct, and it does not imply the member traded because of, used,
              or benefited from their position. Committee-to-sector mapping is
              approximate and hand-curated.
            </p>
            <p>
              Dollar figures are{" "}
              <strong className="text-zinc-300">reported ranges</strong>{" "}
              (low–high), not exact amounts; self-reported filings are
              unverified and carry up to a{" "}
              <strong className="text-zinc-300">~45-day lag</strong>. Educational
              research only — not financial advice.
            </p>
          </div>
        </details>
      )}

      {/* Ideology + policy-area explainer (collapsible) */}
      {((t.n_with_ideology ?? 0) > 0 ||
        (data.committee_policy_map?.length ?? 0) > 0) && (
        <details className="rounded border border-term-border bg-[#0d1220] px-3 py-2 [&_summary::-webkit-details-marker]:hidden">
          <summary className="flex cursor-pointer items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-zinc-300 select-none">
            <span
              aria-hidden
              className="inline-block rounded-sm border border-sky-500/50 bg-sky-500/10 px-1.5 py-px text-[9px] font-semibold tracking-wider text-sky-300"
            >
              IDEOLOGY &amp; POLICY
            </span>
            What do the ideology axis and policy areas mean?
            <span className="ml-auto text-[10px] font-normal text-term-muted">
              {(t.n_with_ideology ?? 0).toLocaleString()} members scored · tap
              to expand
            </span>
          </summary>
          <div className="mt-2 space-y-1.5 text-[11px] leading-relaxed text-zinc-400">
            <p>
              The{" "}
              <span className="text-sky-300">Lib —●— Con</span> axis plots a
              member&apos;s{" "}
              <strong className="text-zinc-300">
                DW-NOMINATE first-dimension score
              </strong>{" "}
              from{" "}
              <a
                href="https://voteview.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sky-400 hover:text-sky-300 underline"
              >
                Voteview
              </a>
              .{" "}
              {data.ideology_note ??
                "This is a statistical measure of roll-call voting patterns (academic), not a personal judgment."}
            </p>
            <p>
              <strong className="text-zinc-300">
                Policy areas (committee jurisdiction)
              </strong>{" "}
              are derived from the member&apos;s committee assignments via a
              curated, approximate committee-to-domain map
              {data.committee_policy_map_note
                ? ` — ${data.committee_policy_map_note}`
                : "; it is not a legal statement of jurisdiction"}
              .{" "}
              {t.bills_enabled && (
                <>
                  <strong className="text-zinc-300">
                    Sponsored legislation (public record)
                  </strong>{" "}
                  lists bills the member introduced, with titles quoted verbatim
                  from the public record.
                </>
              )}
            </p>
            <p>
              These descriptors are{" "}
              <strong className="text-zinc-300">factual and sourced</strong>;
              they are <strong className="text-zinc-300">not</strong> an
              inference about motive and{" "}
              <strong className="text-zinc-300">not an accusation</strong> of
              wrongdoing against any individual.
            </p>
          </div>
        </details>
      )}

      {/* Interactive: filters + trades table + per-member drill-down + sectors */}
      <CongressInteractive
        trades={data.trades}
        byPolitician={data.by_politician}
        bySector={data.by_sector}
      />

      {/* Provenance */}
      <p className="text-[10px] leading-relaxed text-term-muted border-t border-term-border pt-2">
        Source: self-reported STOCK Act Periodic Transaction Reports filed with
        the U.S. House Clerk{" "}
        <span className="tnum">[{data.source_class ?? "filing"}]</span>.
        Generated {dateOnly(data.generated_at)}. Dollar figures are{" "}
        <strong className="text-zinc-300">reported ranges</strong> (low–high),
        not exact amounts; filings carry up to a{" "}
        <strong className="text-zinc-300">45-day lag</strong>. Sector labels are
        best-effort classifications.{" "}
        {(t.n_with_ideology ?? 0) > 0 && (
          <>
            Ideology scores are DW-NOMINATE first-dimension values from{" "}
            <a
              href="https://voteview.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sky-400 hover:text-sky-300 underline"
            >
              Voteview
            </a>{" "}
            — a statistical measure of voting patterns, not a personal
            judgment.{" "}
          </>
        )}
        {(data.committee_policy_map?.length ?? 0) > 0 && (
          <>
            Policy areas are derived from committee jurisdiction (curated,
            approximate)
            {t.bills_enabled
              ? "; sponsored-legislation titles are quoted verbatim from the public record"
              : ""}
            .{" "}
          </>
        )}
        This is{" "}
        <strong className="text-zinc-300">not financial advice</strong> and{" "}
        <strong className="text-zinc-300">not an accusation</strong> of
        wrongdoing against any individual.
        {t.n_scanned_skipped > 0 && (
          <>
            {" "}
            {t.n_scanned_skipped.toLocaleString()} scanned rows were skipped as
            unparseable.
          </>
        )}
      </p>
    </div>
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
