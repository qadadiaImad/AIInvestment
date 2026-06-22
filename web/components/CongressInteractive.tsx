"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type {
  CongressTrade,
  CongressPolitician,
  CongressSector,
  Ideology,
} from "@/lib/data";
import { isValidConflictSignal } from "@/lib/conflict";
import { ideologyLabel, ideologyPosition } from "@/lib/congress_profile";
import { usd, dateOnly, DASH } from "@/lib/format";

// ---- transaction type helpers ---------------------------------------------

// House filings use single-letter codes: P=purchase, S=sale (full),
// "S (partial)" / "Sp"=partial sale, E=exchange. Normalize to buy/sell/other.
function txnClass(t: string | null | undefined): "buy" | "sell" | "other" {
  if (!t) return "other";
  const s = t.trim().toUpperCase();
  if (s.startsWith("P")) return "buy";
  if (s.startsWith("S")) return "sell";
  return "other";
}

function txnLabel(t: string | null | undefined): string {
  const c = txnClass(t);
  if (c === "buy") return "BUY";
  if (c === "sell") return "SELL";
  return t ? t.toUpperCase() : DASH;
}

function txnCls(t: string | null | undefined): string {
  const c = txnClass(t);
  if (c === "buy") return "text-emerald-400";
  if (c === "sell") return "text-rose-400";
  return "text-zinc-400";
}

// Parse "MM/DD/YYYY" or ISO into a sortable timestamp (NaN-safe).
function ts(d: string | null | undefined): number {
  if (!d) return -Infinity;
  const t = Date.parse(d);
  return Number.isNaN(t) ? -Infinity : t;
}

function partyChipCls(p: string | null | undefined): string {
  const s = (p ?? "").trim().toUpperCase();
  if (s.startsWith("D")) return "text-sky-400 border-sky-500/50 bg-sky-500/10";
  if (s.startsWith("R")) return "text-rose-400 border-rose-500/50 bg-rose-500/10";
  if (s.startsWith("I"))
    return "text-amber-400 border-amber-500/50 bg-amber-500/10";
  return "text-zinc-400 border-zinc-600 bg-zinc-700/20";
}

// Normalize a roster party string to a coarse bucket for filtering.
function partyBucket(
  p: string | null | undefined,
): "D" | "R" | "I" | "" {
  const s = (p ?? "").trim().toUpperCase();
  if (s.startsWith("D")) return "D";
  if (s.startsWith("R")) return "R";
  if (s.startsWith("I")) return "I";
  return "";
}

type IdeologyBucket = "" | "Liberal" | "Moderate" | "Conservative";

// Resolve the ideology label for a politician, preferring an explicit label
// from the data but falling back to the dim1 threshold (same thresholds as the
// data layer) so the bucket filter stays consistent.
function resolveIdeologyLabel(
  ideo: Ideology | null | undefined,
): "Liberal" | "Moderate" | "Conservative" | null {
  if (!ideo) return null;
  if (ideo.label) return ideo.label;
  return ideologyLabel(ideo.dim1);
}

// Text color for an ideology label (Lib=sky, Con=rose, Mod=neutral). Purely a
// visual cue for the measured DW-NOMINATE score — not a value judgment.
function ideoTextCls(
  label: "Liberal" | "Moderate" | "Conservative" | null,
): string {
  if (label === "Liberal") return "text-sky-300";
  if (label === "Conservative") return "text-rose-300";
  if (label === "Moderate") return "text-zinc-300";
  return "text-term-muted";
}

type SortKey = "recency" | "amount" | "lag";

const PAGE_SIZE = 200;

interface Props {
  trades: CongressTrade[];
  byPolitician: CongressPolitician[];
  bySector: CongressSector[];
}

export default function CongressInteractive({
  trades,
  byPolitician,
  bySector,
}: Props) {
  const [query, setQuery] = useState("");
  const [sector, setSector] = useState("");
  const [txn, setTxn] = useState<"" | "buy" | "sell">("");
  const [party, setParty] = useState<"" | "D" | "R" | "I">("");
  const [ideology, setIdeology] = useState<IdeologyBucket>("");
  const [politician, setPolitician] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("recency");
  const [overlapOnly, setOverlapOnly] = useState(false);
  const [page, setPage] = useState(0);

  // Per-politician profile lookup (party + ideology) for filtering trades.
  const profileByName = useMemo(() => {
    const m = new Map<string, CongressPolitician>();
    for (const p of byPolitician) m.set(p.politician, p);
    return m;
  }, [byPolitician]);

  // Whether any politician carries an ideology score — gate the filter on it.
  const hasIdeology = useMemo(
    () => byPolitician.some((p) => resolveIdeologyLabel(p.ideology) != null),
    [byPolitician],
  );

  // Sector dropdown options, alphabetical.
  const sectorOptions = useMemo(
    () => [...bySector].map((s) => s.sector).sort((a, b) => a.localeCompare(b)),
    [bySector],
  );

  const politicianCard = useMemo(
    () => byPolitician.find((p) => p.politician === politician) ?? null,
    [byPolitician, politician],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let rows = trades.filter((t) => {
      if (sector && t.sector !== sector) return false;
      if (txn && txnClass(t.txn_type) !== txn) return false;
      if (politician && t.politician !== politician) return false;
      if (party) {
        const prof = profileByName.get(t.politician);
        if (partyBucket(prof?.party ?? t.party) !== party) return false;
      }
      if (ideology) {
        const prof = profileByName.get(t.politician);
        if (resolveIdeologyLabel(prof?.ideology) !== ideology) return false;
      }
      if (overlapOnly && !isValidConflictSignal(t.conflict_signal)) return false;
      if (q) {
        const hay =
          `${t.politician ?? ""} ${t.ticker ?? ""}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
    rows = [...rows];
    if (sortKey === "recency") {
      rows.sort((a, b) => ts(b.txn_date) - ts(a.txn_date));
    } else if (sortKey === "amount") {
      rows.sort(
        (a, b) => (b.amount_range_high ?? 0) - (a.amount_range_high ?? 0),
      );
    } else {
      rows.sort(
        (a, b) =>
          (b.reporting_lag_days ?? -Infinity) -
          (a.reporting_lag_days ?? -Infinity),
      );
    }
    return rows;
  }, [
    trades,
    query,
    sector,
    txn,
    party,
    ideology,
    politician,
    sortKey,
    overlapOnly,
    profileByName,
  ]);

  const overlapCount = useMemo(
    () => trades.filter((t) => isValidConflictSignal(t.conflict_signal)).length,
    [trades],
  );

  // Reset to first page whenever the result set changes.
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages - 1);
  const pageRows = useMemo(
    () => filtered.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE),
    [filtered, safePage],
  );

  function resetPageAnd(fn: () => void) {
    fn();
    setPage(0);
  }

  const inputCls =
    "rounded border border-term-border bg-[#11182a] px-2 py-1 text-[11px] text-zinc-200 focus:outline-none focus:border-emerald-500/70 focus:ring-1 focus:ring-emerald-500/50";

  return (
    <div className="flex flex-col gap-3">
      {/* Selected-politician summary card (client-side drill-down) */}
      {politicianCard && (
        <section className="rounded border border-emerald-500/40 bg-[#0d1220] px-3 py-3">
          <div className="flex items-start justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-[13px] font-semibold text-zinc-100">
                {politicianCard.politician}
              </h2>
              {politicianCard.party && (
                <span
                  className={`inline-block px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm border ${partyChipCls(
                    politicianCard.party,
                  )}`}
                >
                  {politicianCard.party}
                </span>
              )}
              <span className="text-[10px] uppercase tracking-wider text-zinc-500">
                {politicianCard.state ?? DASH}
              </span>
              <IdeologyChip ideology={politicianCard.ideology} />
            </div>
            <button
              type="button"
              onClick={() => resetPageAnd(() => setPolitician(null))}
              className="text-[10.5px] text-term-muted hover:text-emerald-400"
            >
              clear ✕
            </button>
          </div>

          <div className="mt-2 grid grid-cols-2 sm:grid-cols-4 gap-x-3 gap-y-1.5 text-[11px]">
            <Stat label="Trades" value={politicianCard.n_trades.toLocaleString()} />
            <Stat
              label="Buy / Sell"
              value={`${politicianCard.n_buys} / ${politicianCard.n_sells}`}
            />
            <Stat
              label="Est. volume"
              value={`${usd(politicianCard.est_volume_low)}–${usd(
                politicianCard.est_volume_high,
              )}`}
            />
            <Stat
              label="Last trade"
              value={dateOnly(politicianCard.last_trade_date)}
            />
          </div>

          {politicianCard.top_sectors.length > 0 && (
            <div className="mt-2">
              <div className="text-[9.5px] uppercase tracking-wider text-term-muted mb-1">
                Top sectors
              </div>
              <div className="flex flex-wrap gap-1">
                {politicianCard.top_sectors.map((s) => (
                  <span
                    key={s.sector}
                    className="inline-flex items-center gap-1 rounded-sm border border-term-border bg-[#11182a] px-1.5 py-0.5 text-[10px] text-zinc-300"
                  >
                    {s.sector}
                    <span className="text-zinc-500 tnum">{s.n}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {((politicianCard.committees?.length ?? 0) > 0 ||
            (politicianCard.jurisdiction_sectors?.length ?? 0) > 0) && (
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {(politicianCard.committees?.length ?? 0) > 0 && (
                <div>
                  <div className="text-[9.5px] uppercase tracking-wider text-term-muted mb-1">
                    Committees
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {politicianCard.committees!.map((c) => (
                      <span
                        key={c}
                        className="inline-flex items-center rounded-sm border border-term-border bg-[#11182a] px-1.5 py-0.5 text-[10px] text-zinc-300"
                      >
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {(politicianCard.jurisdiction_sectors?.length ?? 0) > 0 && (
                <div>
                  <div className="text-[9.5px] uppercase tracking-wider text-term-muted mb-1">
                    Jurisdiction sectors
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {politicianCard.jurisdiction_sectors!.map((s) => (
                      <span
                        key={s}
                        className="inline-flex items-center rounded-sm border border-amber-500/30 bg-amber-500/5 px-1.5 py-0.5 text-[10px] text-amber-200/80"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {(politicianCard.policy_areas?.length ?? 0) > 0 && (
            <div className="mt-2">
              <div className="text-[9.5px] uppercase tracking-wider text-term-muted mb-1">
                Policy areas (committee jurisdiction)
              </div>
              <div className="flex flex-wrap gap-1">
                {politicianCard.policy_areas!.map((a) => (
                  <span
                    key={a}
                    className="inline-flex items-center rounded-sm border border-sky-500/30 bg-sky-500/5 px-1.5 py-0.5 text-[10px] text-sky-200/85"
                  >
                    {a}
                  </span>
                ))}
              </div>
            </div>
          )}

          {politicianCard.sponsored &&
            politicianCard.sponsored.n > 0 && (
              <div className="mt-2">
                <div className="flex items-center gap-1.5 text-[9.5px] uppercase tracking-wider text-term-muted mb-1">
                  Sponsored legislation (public record)
                  <span className="tnum text-zinc-500">
                    {politicianCard.sponsored.n.toLocaleString()}
                  </span>
                </div>
                {(politicianCard.sponsored.top_policy_areas?.length ?? 0) >
                  0 && (
                  <div className="mb-1.5 flex flex-wrap gap-1">
                    {politicianCard.sponsored.top_policy_areas.map((tp) => (
                      <span
                        key={tp.area}
                        className="inline-flex items-center gap-1 rounded-sm border border-term-border bg-[#11182a] px-1.5 py-0.5 text-[10px] text-zinc-300"
                      >
                        {tp.area}
                        <span className="text-zinc-500 tnum">{tp.n}</span>
                      </span>
                    ))}
                  </div>
                )}
                {(politicianCard.sponsored.recent?.length ?? 0) > 0 && (
                  <ul className="space-y-1">
                    {politicianCard.sponsored.recent.map((b) => (
                      <li
                        key={`${b.type}-${b.number}`}
                        className="rounded-sm border border-term-border bg-[#0b101c] px-2 py-1 text-[10px] leading-relaxed"
                      >
                        <div className="flex items-baseline gap-1.5">
                          <span className="font-semibold tnum text-zinc-300">
                            {b.type} {b.number}
                          </span>
                          {b.introduced_date && (
                            <span className="tnum text-term-muted">
                              {dateOnly(b.introduced_date)}
                            </span>
                          )}
                          {b.policy_area && (
                            <span className="ml-auto inline-flex items-center rounded-sm border border-sky-500/30 bg-sky-500/5 px-1 py-px text-[9px] text-sky-200/80">
                              {b.policy_area}
                            </span>
                          )}
                        </div>
                        <div className="mt-0.5 text-zinc-300">{b.title}</div>
                        {b.latest_action && (
                          <div className="mt-0.5 text-term-muted">
                            {b.latest_action}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

          <p className="mt-2 text-[9.5px] text-term-muted">
            Showing this member&apos;s filings below — clear to see all members.
            Committee–sector overlaps shown on this page are{" "}
            <span className="text-amber-300/80">correlational only</span>, not an
            accusation. Ideology is a statistical measure of voting patterns
            (Voteview), not a personal judgment.
          </p>
        </section>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => resetPageAnd(() => setQuery(e.target.value))}
          placeholder="Search politician or ticker…"
          aria-label="Search politician or ticker"
          className={`${inputCls} w-[220px]`}
        />
        <label className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-term-muted">
          Sector
          <select
            value={sector}
            onChange={(e) => resetPageAnd(() => setSector(e.target.value))}
            aria-label="Filter by sector"
            className={inputCls}
          >
            <option value="">All sectors</option>
            {sectorOptions.map((s) => (
              <option key={s} value={s} className="bg-[#11182a] text-zinc-200">
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-term-muted">
          Type
          <select
            value={txn}
            onChange={(e) =>
              resetPageAnd(() => setTxn(e.target.value as "" | "buy" | "sell"))
            }
            aria-label="Filter by transaction type"
            className={inputCls}
          >
            <option value="">Buy &amp; sell</option>
            <option value="buy">Buys</option>
            <option value="sell">Sells</option>
          </select>
        </label>
        <label className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-term-muted">
          Party
          <select
            value={party}
            onChange={(e) =>
              resetPageAnd(() =>
                setParty(e.target.value as "" | "D" | "R" | "I"),
              )
            }
            aria-label="Filter by party"
            className={inputCls}
          >
            <option value="">All parties</option>
            <option value="D">Democrat</option>
            <option value="R">Republican</option>
            <option value="I">Independent</option>
          </select>
        </label>
        {hasIdeology && (
          <label
            className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-term-muted"
            title="Ideology buckets are derived from DW-NOMINATE first-dimension scores (Voteview) — a statistical measure of voting patterns, not a personal judgment."
          >
            Ideology
            <select
              value={ideology}
              onChange={(e) =>
                resetPageAnd(() =>
                  setIdeology(e.target.value as IdeologyBucket),
                )
              }
              aria-label="Filter by ideology bucket"
              className={inputCls}
            >
              <option value="">All ideology</option>
              <option value="Liberal">Liberal</option>
              <option value="Moderate">Moderate</option>
              <option value="Conservative">Conservative</option>
            </select>
          </label>
        )}
        <label className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-term-muted">
          Sort
          <select
            value={sortKey}
            onChange={(e) =>
              resetPageAnd(() => setSortKey(e.target.value as SortKey))
            }
            aria-label="Sort trades"
            className={inputCls}
          >
            <option value="recency">Recency</option>
            <option value="amount">$ range</option>
            <option value="lag">Filing lag</option>
          </select>
        </label>
        {overlapCount > 0 && (
          <label
            className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-amber-300/90 cursor-pointer select-none"
            title="Show only trades with a correlational committee-jurisdiction overlap. Not an accusation."
          >
            <input
              type="checkbox"
              checked={overlapOnly}
              onChange={(e) =>
                resetPageAnd(() => setOverlapOnly(e.target.checked))
              }
              aria-label="Show only committee-overlap trades"
              className="h-3 w-3 accent-amber-500"
            />
            Committee overlap only
            <span className="text-amber-400/60 tnum">
              ({overlapCount.toLocaleString()})
            </span>
          </label>
        )}
        <span className="ml-auto text-[10.5px] text-term-muted tnum">
          {filtered.length.toLocaleString()} trades
        </span>
      </div>

      {/* Trades table */}
      <div className="overflow-x-auto border border-term-border rounded-sm">
        <table className="term">
          <caption className="sr-only">Congressional trades</caption>
          <thead className="bg-[#0e131d] sticky top-0 z-10">
            <tr>
              <th>Politician</th>
              <th>Party</th>
              <th>Ideology</th>
              <th>State</th>
              <th>Ticker</th>
              <th>Sector</th>
              <th>Type</th>
              <th>Txn date</th>
              <th>Filed</th>
              <th className="numcell">Lag (d)</th>
              <th className="numcell">$ range</th>
            </tr>
          </thead>
          <tbody>
            {pageRows.map((t, i) => {
              const prof = profileByName.get(t.politician);
              const partyVal = prof?.party ?? t.party;
              const ideo = prof?.ideology;
              const ideoLabel = resolveIdeologyLabel(ideo);
              return (
              <tr key={`${t.source ?? ""}-${i}`}>
                <td>
                  <button
                    type="button"
                    onClick={() =>
                      resetPageAnd(() => setPolitician(t.politician))
                    }
                    className="text-left font-semibold text-emerald-400 hover:text-emerald-300"
                  >
                    {t.politician}
                  </button>
                </td>
                <td>
                  {partyVal ? (
                    <span
                      title={partyVal}
                      className={`inline-block px-1 py-px text-[9px] font-semibold uppercase tracking-wider rounded-sm border ${partyChipCls(
                        partyVal,
                      )}`}
                    >
                      {partyBucket(partyVal) || partyVal}
                    </span>
                  ) : (
                    <span className="text-term-muted">{DASH}</span>
                  )}
                </td>
                <td>
                  {ideo && ideoLabel ? (
                    <span
                      className={`tnum ${ideoTextCls(ideoLabel)}`}
                      title={`DW-NOMINATE dim-1 = ${
                        ideo.dim1 != null ? ideo.dim1.toFixed(3) : "n/a"
                      } (Voteview) — a statistical measure of voting patterns, not a personal judgment.`}
                    >
                      {ideoLabel.slice(0, 3)}
                      {ideo.dim1 != null && (
                        <span className="ml-1 text-term-muted">
                          {ideo.dim1 > 0 ? "+" : ""}
                          {ideo.dim1.toFixed(2)}
                        </span>
                      )}
                    </span>
                  ) : (
                    <span className="text-term-muted">{DASH}</span>
                  )}
                </td>
                <td className="tnum text-zinc-400">{t.state ?? DASH}</td>
                <td>
                  <span className="inline-flex items-center gap-1.5">
                    {t.ticker ? (
                      <Link
                        href={`/stocks/${t.ticker}`}
                        className="font-semibold text-sky-400 hover:text-sky-300"
                      >
                        {t.ticker}
                      </Link>
                    ) : (
                      <span className="text-term-muted">{DASH}</span>
                    )}
                    <OverlapChip signal={t.conflict_signal} />
                  </span>
                </td>
                <td className="text-zinc-300">{t.sector ?? DASH}</td>
                <td className={`font-semibold ${txnCls(t.txn_type)}`}>
                  {txnLabel(t.txn_type)}
                </td>
                <td className="tnum text-zinc-300">{dateOnly(t.txn_date)}</td>
                <td className="tnum text-term-muted">
                  {dateOnly(t.filing_date)}
                </td>
                <td className="numcell tnum text-zinc-400">
                  {t.reporting_lag_days ?? DASH}
                </td>
                <td className="numcell tnum text-zinc-200">
                  {t.amount_range_low != null && t.amount_range_high != null
                    ? `${usd(t.amount_range_low)}–${usd(t.amount_range_high)}`
                    : DASH}
                </td>
              </tr>
              );
            })}
            {pageRows.length === 0 && (
              <tr>
                <td colSpan={11} className="text-center text-term-muted py-4">
                  No trades match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {filtered.length > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-3 text-[11px]">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={safePage === 0}
            className="rounded border border-term-border bg-[#11182a] px-2 py-1 text-zinc-300 hover:border-emerald-500/70 hover:text-emerald-400 disabled:opacity-40 disabled:hover:border-term-border disabled:hover:text-zinc-300"
          >
            ← Prev
          </button>
          <span className="tnum text-term-muted">
            Page {safePage + 1} / {totalPages} ·{" "}
            {(safePage * PAGE_SIZE + 1).toLocaleString()}–
            {Math.min(
              (safePage + 1) * PAGE_SIZE,
              filtered.length,
            ).toLocaleString()}{" "}
            of {filtered.length.toLocaleString()}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={safePage >= totalPages - 1}
            className="rounded border border-term-border bg-[#11182a] px-2 py-1 text-zinc-300 hover:border-emerald-500/70 hover:text-emerald-400 disabled:opacity-40 disabled:hover:border-term-border disabled:hover:text-zinc-300"
          >
            Next →
          </button>
        </div>
      )}

      {/* Sector breakdown */}
      <section className="mt-2">
        <h2 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-300 mb-2">
          Sector breakdown
        </h2>
        <SectorBreakdown
          sectors={bySector}
          activeSector={sector}
          onPick={(s) =>
            resetPageAnd(() => setSector((cur) => (cur === s ? "" : s)))
          }
        />
      </section>
    </div>
  );
}

// Subtle, informational (not alarming) indicator for a trade whose member's
// committee jurisdiction overlaps the traded sector. The native title tooltip
// surfaces the exact, validated correlational rationale text.
function OverlapChip({ signal }: { signal?: CongressTrade["conflict_signal"] }) {
  if (!isValidConflictSignal(signal)) return null;
  const committees = signal.committees.join(", ");
  return (
    <span
      title={signal.rationale}
      aria-label={`Committee overlap: ${committees}. ${signal.rationale}`}
      className="inline-flex items-center rounded-sm border border-amber-500/40 bg-amber-500/10 px-1 py-px text-[8.5px] font-semibold uppercase tracking-wider text-amber-300/90 cursor-help whitespace-nowrap"
    >
      ⊚ overlap
    </span>
  );
}

// Labeled Lib —●— Con ideology axis chip. Renders the DW-NOMINATE 1st-dimension
// position as a marker on a left(Liberal)→right(Conservative) scale, plus the
// numeric score. The tooltip cites Voteview and explicitly frames this as a
// statistical measure of voting patterns, not a personal judgment.
function IdeologyChip({
  ideology,
}: {
  ideology?: Ideology | null;
}) {
  if (!ideology) return null;
  const dim1 = ideology.dim1;
  if (dim1 == null || Number.isNaN(dim1)) return null;
  const label = ideology.label ?? ideologyLabel(dim1);
  const pos = ideology.position ?? ideologyPosition(dim1);
  const pct = pos == null ? 50 : pos * 100;
  const tooltip =
    `Ideology: DW-NOMINATE 1st dimension = ${dim1.toFixed(3)}` +
    (label ? ` (${label})` : "") +
    `. Source: Voteview. This is a statistical measure of roll-call voting ` +
    `patterns, not a personal judgment.`;

  return (
    <span
      title={tooltip}
      aria-label={tooltip}
      className="inline-flex items-center gap-1.5 rounded-sm border border-term-border bg-[#11182a] px-1.5 py-0.5 text-[9.5px] text-zinc-300 cursor-help"
    >
      <span className="text-sky-400/80">Lib</span>
      <span className="relative inline-block h-1 w-12 rounded-full bg-gradient-to-r from-sky-500/40 via-zinc-600/40 to-rose-500/40 align-middle">
        <span
          className="absolute top-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full border border-zinc-200 bg-zinc-100"
          style={{ left: `${pct}%` }}
        />
      </span>
      <span className="text-rose-400/80">Con</span>
      <span className="tnum text-zinc-400">{dim1.toFixed(2)}</span>
      {label && (
        <span className="uppercase tracking-wider text-term-muted">
          {label}
        </span>
      )}
    </span>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-[9.5px] uppercase tracking-wider text-term-muted">
        {label}
      </span>
      <span className="text-zinc-200 tnum">{value}</span>
    </div>
  );
}

function SectorBreakdown({
  sectors,
  activeSector,
  onPick,
}: {
  sectors: CongressSector[];
  activeSector: string;
  onPick: (s: string) => void;
}) {
  const sorted = useMemo(
    () => [...sectors].sort((a, b) => b.n_trades - a.n_trades),
    [sectors],
  );
  const maxTrades = sorted.length ? sorted[0].n_trades : 1;

  return (
    <div className="overflow-x-auto border border-term-border rounded-sm">
      <table className="term">
        <caption className="sr-only">Trades by sector</caption>
        <thead className="bg-[#0e131d]">
          <tr>
            <th>Sector</th>
            <th className="numcell">Trades</th>
            <th className="numcell">Buys</th>
            <th className="numcell">Sells</th>
            <th className="numcell">Est. volume</th>
            <th className="numcell">Members</th>
            <th className="w-[34%]">Share</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((s) => {
            const w = Math.max(2, (s.n_trades / maxTrades) * 100);
            const active = activeSector === s.sector;
            return (
              <tr
                key={s.sector}
                role="button"
                tabIndex={0}
                aria-label={`Filter trades to ${s.sector}`}
                onClick={() => onPick(s.sector)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onPick(s.sector);
                  }
                }}
                className={`cursor-pointer ${active ? "bg-emerald-500/10" : ""}`}
              >
                <td
                  className={
                    active ? "text-emerald-300 font-semibold" : "text-zinc-200"
                  }
                >
                  {s.sector}
                </td>
                <td className="numcell tnum text-zinc-200">
                  {s.n_trades.toLocaleString()}
                </td>
                <td className="numcell tnum text-emerald-400">
                  {s.n_buys.toLocaleString()}
                </td>
                <td className="numcell tnum text-rose-400">
                  {s.n_sells.toLocaleString()}
                </td>
                <td className="numcell tnum text-zinc-300">
                  {usd(s.est_volume_low)}–{usd(s.est_volume_high)}
                </td>
                <td className="numcell tnum text-zinc-400">
                  {s.n_politicians.toLocaleString()}
                </td>
                <td>
                  <div className="h-2 w-full rounded-sm bg-zinc-800 overflow-hidden">
                    <div
                      className="h-full rounded-sm bg-emerald-500/70"
                      style={{ width: `${w}%` }}
                    />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
