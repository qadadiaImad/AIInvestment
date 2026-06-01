// WhyConsider — a DETERMINISTIC, sourced "Why consider this ticker" card.
//
// No LLM, no opinion: every line is derived from the data passed in by the
// server page (valuation block, recent news, congressional trades). The card
// presents THREE labeled FACTOR blocks — VALUATION, NEWS, CONGRESS — and is
// explicitly framed as FACTORS, NOT ADVICE.
//
// LEGAL RAILS (hard requirements):
//   • The congress factor is STRICTLY CORRELATIONAL. It states only WHO traded
//     and the public net buy/sell counts. It NEVER implies a politician's trade
//     is a buy/sell signal, insider information, or an accusation of wrongdoing.
//   • The whole card carries a footer disclaimer: factors for research/education
//     only — not a recommendation or investment advice.
//
// This is a server component (no client interactivity). It imports VALUES only
// from client-safe libs (@/lib/format) and TYPES only from @/lib/data.

import type { Stock, NewsArticle } from "@/lib/data";
import { price as fmtPrice, pct, signedPct, DASH } from "@/lib/format";

// ---- Per-symbol congress summary (derived server-side, passed as a prop) ----
// Plain, serializable shape so this component stays presentational. `topMembers`
// lists the members who traded this ticker (name + party label), public record.
export interface CongressMember {
  name: string;
  party: string | null;
}

export interface CongressSummary {
  nMembers: number;
  nBuys: number;
  nSells: number;
  topMembers: CongressMember[];
}

interface Props {
  stock: Stock;
  news: NewsArticle[];
  congress: CongressSummary | null;
  // Link target for the on-page Related-news panel (an in-page anchor).
  newsAnchor?: string;
}

// Coarse party label from a roster party string. Used only for the factual
// "who traded" line — purely descriptive, never evaluative.
function partyLabel(p: string | null | undefined): string | null {
  const s = (p ?? "").trim().toUpperCase();
  if (!s) return null;
  if (s.startsWith("D")) return "D";
  if (s.startsWith("R")) return "R";
  if (s.startsWith("I")) return "I";
  return p ?? null;
}

// Map a news certainty bucket to a count key. Anything unrecognized is counted
// under "other" so the mix line never silently drops items.
function certaintyBucket(c: string): "filed" | "reported" | "rumored" | "other" {
  if (c === "filed" || c === "reported" || c === "rumored") return c;
  return "other";
}

export default function WhyConsider({
  stock,
  news,
  congress,
  newsAnchor = "#related-news",
}: Props) {
  const v = stock.valuation;
  const f = stock.fundamentals;

  // ---- VALUATION factor --------------------------------------------------
  const hasFundamentalValue =
    typeof v.fundamental_value === "number" &&
    Number.isFinite(v.fundamental_value);
  const disc = v.fundamental_discount_pct;
  const hasDisc = typeof disc === "number" && Number.isFinite(disc);
  // Label from the sign/magnitude of the discount (price vs fundamental value).
  // Positive discount => price below fundamental value => Undervalued.
  let valTag: string | null = v.fundamental_valuation ?? null;
  if (!valTag && hasDisc) {
    const d = disc as number;
    if (d >= 10) valTag = "Undervalued";
    else if (d <= -10) valTag = "Overvalued";
    else valTag = "Fairly valued";
  }
  const valTagCls =
    valTag === "Undervalued"
      ? "text-emerald-400"
      : valTag === "Overvalued"
        ? "text-rose-400"
        : valTag === "Fairly valued" || valTag === "Fairly Valued"
          ? "text-amber-400"
          : "text-zinc-300";
  const discFmt = hasDisc ? signedPct(disc) : null;

  // ---- NEWS factor -------------------------------------------------------
  const nNews = news.length;
  const mix = { filed: 0, reported: 0, rumored: 0, other: 0 };
  let nWithEdge = 0;
  for (const a of news) {
    mix[certaintyBucket(String(a.certainty))] += 1;
    if ((a.graph_edges?.length ?? 0) > 0) nWithEdge += 1;
  }
  const mixParts: string[] = [];
  if (mix.filed) mixParts.push(`${mix.filed} filed`);
  if (mix.reported) mixParts.push(`${mix.reported} reported`);
  if (mix.rumored) mixParts.push(`${mix.rumored} rumored`);
  if (mix.other) mixParts.push(`${mix.other} unlabeled`);

  // ---- CONGRESS factor ---------------------------------------------------
  const hasCongress = !!congress && congress.nMembers > 0;
  const memberStr = hasCongress
    ? congress!.topMembers
        .map((m) => {
          const pl = partyLabel(m.party);
          return pl ? `${m.name} (${pl})` : m.name;
        })
        .join(", ")
    : "";

  return (
    <div className="flex flex-col gap-3">
      <p className="text-[10.5px] leading-snug text-term-muted">
        Three public, deterministically-derived factors for {stock.symbol}. These
        are <span className="text-zinc-300">factors, not advice</span> — not a
        recommendation to buy or sell.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* VALUATION */}
        <FactorBlock label="Valuation">
          {hasFundamentalValue ? (
            <>
              <FactRow
                label="Estimate"
                value={
                  <span className={`font-semibold ${valTagCls}`}>
                    {valTag ?? DASH}
                  </span>
                }
              />
              <FactRow
                label="Fundamental value"
                value={fmtPrice(v.fundamental_value)}
              />
              <FactRow label="Price" value={fmtPrice(v.price)} />
              <FactRow
                label="vs Price"
                value={
                  discFmt ? (
                    <span className={discFmt.cls}>{discFmt.text}</span>
                  ) : (
                    DASH
                  )
                }
              />
            </>
          ) : (
            <p className="text-[11px] text-term-muted">
              No intrinsic-value estimate available — price shown for reference.
            </p>
          )}
          <div className="mt-2 border-t border-term-border pt-2">
            <FactRow label="Net margin" value={pct(f.net_margin)} />
            <FactRow label="Rev growth (YoY)" value={signedPct(f.rev_growth_yoy).text} />
            <FactRow label="ROIC" value={pct(f.roic)} />
          </div>
          <p className="mt-2 text-[9px] leading-snug text-term-muted">
            Fundamental value is a third-party intrinsic-value estimate; the
            under/fair/over label is computed from the live price.
          </p>
        </FactorBlock>

        {/* NEWS */}
        <FactorBlock label="News">
          {nNews > 0 ? (
            <>
              <FactRow
                label="Recent items"
                value={
                  <span className="font-semibold text-zinc-200">{nNews}</span>
                }
              />
              <FactRow
                label="Certainty mix"
                value={
                  <span className="text-zinc-300">
                    {mixParts.length ? mixParts.join(" · ") : DASH}
                  </span>
                }
              />
              {nWithEdge > 0 && (
                <p className="mt-1.5 text-[10.5px] leading-snug text-sky-300/90">
                  {nWithEdge} item{nWithEdge > 1 ? "s" : ""} reference a curated
                  capital-web deal edge.
                </p>
              )}
              <a
                href={newsAnchor}
                className="mt-2 inline-block text-[10.5px] font-semibold text-emerald-400 hover:text-emerald-300"
              >
                See related news ↓
              </a>
            </>
          ) : (
            <p className="text-[11px] text-term-muted">No recent news.</p>
          )}
        </FactorBlock>

        {/* CONGRESS */}
        <FactorBlock label="Congress">
          {hasCongress ? (
            <>
              <p className="text-[11.5px] leading-snug text-zinc-300">
                Traded by{" "}
                <span className="font-semibold text-zinc-100">
                  {congress!.nMembers}
                </span>{" "}
                member{congress!.nMembers > 1 ? "s" : ""} of Congress (
                <span className="text-emerald-400">{congress!.nBuys} buys</span>{" "}
                /{" "}
                <span className="text-rose-400">{congress!.nSells} sells</span>)
                as public record.
              </p>
              {memberStr && (
                <p className="mt-1.5 text-[10.5px] leading-snug text-term-muted">
                  Top: <span className="text-zinc-300">{memberStr}</span>
                </p>
              )}
              <p className="mt-2 text-[9px] leading-snug text-amber-300/80">
                Congressional trades are public disclosures shown for
                transparency — NOT a buy/sell signal and not an accusation.
              </p>
            </>
          ) : (
            <p className="text-[11px] text-term-muted">
              No congressional trades on record.
            </p>
          )}
        </FactorBlock>
      </div>

      <p className="text-[10px] leading-snug text-term-muted border-t border-term-border pt-2">
        Factors shown for research/education only — not a recommendation or
        investment advice.
      </p>
    </div>
  );
}

function FactorBlock({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-sm border border-term-border bg-[#0b0f17] p-2.5">
      <div className="mb-1.5 text-[9.5px] font-semibold uppercase tracking-wider text-term-muted">
        {label}
      </div>
      {children}
    </div>
  );
}

function FactRow({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-baseline justify-between gap-2 py-0.5">
      <span className="text-[10px] text-term-muted">{label}</span>
      <span className="text-[12px] tnum text-right">{value}</span>
    </div>
  );
}
