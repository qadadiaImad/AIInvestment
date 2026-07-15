import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import {
  getAllSymbols,
  getStock,
  getNewsForSymbol,
  getCongressData,
  type PeerMetric,
} from "@/lib/data";
import LayerChip from "@/components/LayerChip";
import Sparkline from "@/components/Sparkline";
import PriceChart from "@/components/PriceChart";
import TradingViewChart from "@/components/TradingViewChart";
import StockNews from "@/components/StockNews";
import WhyConsider, {
  type CongressSummary,
} from "@/components/WhyConsider";
import ArchetypePanel from "@/components/terminal/ArchetypePanel";
import { getArchetypeForSymbol } from "@/lib/archetypes";
import DcfPanel from "@/components/terminal/DcfPanel";
import { buildDefaultDcfInputs } from "@/lib/dcf";
import { getMacroData } from "@/lib/macro";
import {
  price as fmtPrice,
  ratio,
  pct,
  num,
  usd,
  signedPct,
  dateOnly,
  titleCase,
  DASH,
} from "@/lib/format";

export function generateStaticParams() {
  return getAllSymbols().map((symbol) => ({ symbol }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ symbol: string }>;
}): Promise<Metadata> {
  const { symbol } = await params;
  const stock = getStock(symbol);
  if (!stock) return { title: "Not found · AI STACK" };
  return {
    title: `${stock.symbol} · AI STACK`,
    description: `Educational fundamentals, relationships, and bottleneck analysis for ${stock.symbol}. Not financial advice.`,
  };
}

// Format a catalyst date for display. Some feeds emit a raw unix epoch in
// SECONDS (e.g. "1786536000") rather than an ISO string. When the value is
// all-digits, treat it as epoch-seconds; otherwise fall back to dateOnly,
// preserving existing ISO-string behavior.
function catalystDate(v: string | null | undefined): string {
  if (!v) return DASH;
  if (/^\d+$/.test(v)) {
    const d = new Date(Number(v) * 1000);
    if (!Number.isNaN(d.getTime())) return d.toISOString().slice(0, 10);
  }
  return dateOnly(v);
}

// Derive a deterministic per-symbol congressional-trade summary from the public
// STOCK Act disclosures (getCongressData). Returns null when no member traded
// the ticker. This is PUBLIC RECORD only — WHO traded and the net buy/sell
// counts — never a buy/sell signal and never an accusation. House filings use
// single-letter txn codes (P=purchase, S=sale, E=exchange); we classify by the
// leading letter and tally distinct members, ranking them by trade count.
function getCongressForSymbol(symbol: string): CongressSummary | null {
  const data = getCongressData();
  const trades = (data.trades ?? []).filter((t) => t.ticker === symbol);
  if (trades.length === 0) return null;

  let nBuys = 0;
  let nSells = 0;
  const byMember = new Map<
    string,
    { name: string; party: string | null; count: number }
  >();
  for (const t of trades) {
    const code = (t.txn_type ?? "").trim().toUpperCase();
    if (code.startsWith("P")) nBuys += 1;
    else if (code.startsWith("S")) nSells += 1;
    const key = t.politician;
    const existing = byMember.get(key);
    if (existing) existing.count += 1;
    else byMember.set(key, { name: t.politician, party: t.party, count: 1 });
  }

  const topMembers = [...byMember.values()]
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
    .slice(0, 3)
    .map((m) => ({ name: m.name, party: m.party }));

  return { nMembers: byMember.size, nBuys, nSells, topMembers };
}

// ---- small presentational helpers ----

function Panel({
  title,
  children,
  className = "",
  id,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section
      id={id}
      className={`border border-term-border rounded-sm bg-[#0e131d] ${className}`}
    >
      <div className="px-3 py-1.5 border-b border-term-border text-[10.5px] font-semibold uppercase tracking-wider text-term-muted">
        {title}
      </div>
      <div className="p-3">{children}</div>
    </section>
  );
}

function Stat({
  label,
  value,
  cls = "",
}: {
  label: string;
  value: React.ReactNode;
  cls?: string;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[9.5px] uppercase tracking-wider text-term-muted">
        {label}
      </span>
      <span className={`text-[13px] tnum ${cls}`}>{value}</span>
    </div>
  );
}

export default async function StockPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = await params;
  const s = getStock(symbol);
  if (!s) notFound();

  const f = s.fundamentals;
  const v = s.valuation;
  const hasFundamentalValue =
    typeof v.fundamental_value === "number" &&
    Number.isFinite(v.fundamental_value);
  const perf = s.performance;
  const p1y = signedPct(perf.perf_1y);
  const pytd = signedPct(perf.perf_ytd);
  const revG = signedPct(f.rev_growth_yoy);
  const epsG = signedPct(f.eps_growth_yoy);
  const n = s.narrative ?? {};
  const hasNarrative =
    n.valuation_take ||
    n.bottleneck_rationale ||
    (n.scenarios && n.scenarios.length) ||
    (n.risks && n.risks.length) ||
    n.synthesis;

  const counterparties = s.relationships?.counterparties ?? [];
  const labExposure = s.relationships?.lab_exposure ?? [];
  const catalysts = (s.catalysts ?? []).filter((c) => c.date || c.display);
  const news = getNewsForSymbol(s.symbol);
  const congress = getCongressForSymbol(s.symbol);
  const archetype = getArchetypeForSymbol(s.symbol);
  const dcfDefaults = buildDefaultDcfInputs(s, getMacroData());

  // peer comparison rows
  const industryPeers = s.peer_comparison?.industry ?? {};
  const layerPeers = s.peer_comparison?.layer ?? {};
  const peerKeys = Array.from(
    new Set([...Object.keys(industryPeers), ...Object.keys(layerPeers)])
  ).sort();

  const histories: { label: string; key: keyof typeof s.history; eps?: boolean }[] =
    [
      { label: "Revenue", key: "annualTotalRevenue" },
      { label: "Gross profit", key: "annualGrossProfit" },
      { label: "Net income", key: "annualNetIncome" },
      { label: "Free cash flow", key: "annualFreeCashFlow" },
      { label: "Diluted EPS", key: "annualDilutedEPS", eps: true },
    ];

  return (
    <div className="px-3 py-3 flex flex-col gap-3">
      {/* breadcrumb */}
      <div className="text-[10.5px] text-term-muted">
        <Link href="/screener" className="hover:text-emerald-400">
          screener
        </Link>{" "}
        / <span className="text-zinc-300">{s.symbol}</span>
      </div>

      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-3 border border-term-border rounded-sm bg-[#0e131d] px-3 py-2.5">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight">{s.symbol}</h1>
          <LayerChip layer={s.layer} />
          <div className="text-[11px] text-term-muted leading-tight">
            <div>{f.sector ?? DASH}</div>
            <div>{f.industry ?? DASH}</div>
          </div>
        </div>
        <div className="flex items-end gap-5">
          <div className="text-right">
            <div className="text-[9.5px] uppercase tracking-wider text-term-muted">
              Price
            </div>
            <div className="text-xl font-bold tnum">{fmtPrice(v.price)}</div>
          </div>
          <div className="text-right">
            <div className="text-[9.5px] uppercase tracking-wider text-term-muted">
              1Y
            </div>
            <div className={`text-base font-semibold tnum ${p1y.cls}`}>
              {p1y.text}
            </div>
          </div>
        </div>
      </div>

      {s.risk_flags && s.risk_flags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {s.risk_flags.map((r) => (
            <span
              key={r}
              className="text-[10px] px-1.5 py-0.5 rounded-sm border border-rose-500/50 text-rose-300 bg-rose-500/10"
            >
              ⚠ {titleCase(r)}
            </span>
          ))}
        </div>
      )}

      {/* Why consider this ticker — deterministic factor card (factors, not advice) */}
      <Panel title="Why consider this ticker">
        <WhyConsider stock={s} news={news} congress={congress} />
      </Panel>

      {/* top grid: valuation + performance */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Panel title="Valuation">
          <div className="grid grid-cols-3 gap-3">
            <Stat label="Price" value={fmtPrice(v.price)} />
            <Stat label="P/E" value={ratio(v.pe, 1)} />
            <Stat
              label="Profitability"
              value={
                <span
                  className={
                    v.profitability === "profitable"
                      ? "text-emerald-400 text-[12px]"
                      : "text-amber-400 text-[12px]"
                  }
                >
                  {v.profitability ? titleCase(v.profitability) : DASH}
                </span>
              }
            />
            <Stat label="P/S" value={ratio(f.ps, 1)} />
            <Stat label="P/B" value={ratio(f.pb, 1)} />
            <Stat label="P/FCF" value={ratio(f.pfcf, 1)} />
            <Stat
              label="Fundamental value"
              value={fmtPrice(v.fundamental_value)}
            />
            <Stat
              label="Estimate"
              value={<FundamentalTag tag={v.fundamental_valuation} />}
            />
            <Stat
              label="vs Price"
              value={
                hasFundamentalValue
                  ? signedPct(v.fundamental_discount_pct).text
                  : DASH
              }
              cls={
                hasFundamentalValue ? signedPct(v.fundamental_discount_pct).cls : ""
              }
            />
          </div>
          <p className="mt-3 text-[9.5px] leading-snug text-term-muted">
            Fundamental value is a third-party intrinsic-value estimate; the
            under/fair/over tag is computed from our live price. Educational only
            — verify before acting.
          </p>
        </Panel>

        <Panel title="Performance — price return">
          {(() => {
            const r = s.returns ?? {};
            const r1 = signedPct(r["1y"]);
            const r3 = signedPct(r["3y"]);
            const r5 = signedPct(r["5y"]);
            return (
              <>
                <div className="grid grid-cols-3 gap-3">
                  <Stat label="1Y return" value={r1.text} cls={r1.cls} />
                  <Stat label="3Y return" value={r3.text} cls={r3.cls} />
                  <Stat label="5Y return" value={r5.text} cls={r5.cls} />
                </div>
                <div className="grid grid-cols-3 gap-3 mt-3">
                  <Stat label="YTD" value={pytd.text} cls={pytd.cls} />
                  <Stat label="Beta" value={num(perf.beta, 2)} />
                </div>
              </>
            );
          })()}
        </Panel>
      </div>

      {/* Price vs Fundamental Value chart */}
      <Panel title="Price vs Fundamental Value">
        <PriceChart
          symbol={s.symbol}
          fundamentalSeries={s.fundamental_value_series}
        />
      </Panel>

      {/* Interactive TradingView chart */}
      <Panel title="Interactive chart (TradingView)">
        <TradingViewChart tvSymbol={s.tv_symbol} />
      </Panel>

      {/* Fundamentals grid */}
      <Panel title="Fundamentals">
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-x-4 gap-y-3">
          <Stat label="Gross margin" value={pct(f.gross_margin)} />
          <Stat label="Operating margin" value={pct(f.operating_margin)} />
          <Stat label="Net margin" value={pct(f.net_margin)} />
          <Stat label="FCF margin" value={pct(f.fcf_margin)} />
          <Stat label="ROE" value={pct(f.roe)} />
          <Stat label="ROA" value={pct(f.roa)} />
          <Stat label="ROIC" value={pct(f.roic)} />
          <Stat label="Debt / equity" value={num(f.debt_to_equity, 2)} />
          <Stat label="Current ratio" value={num(f.current_ratio, 2)} />
          <Stat label="Rev YoY" value={revG.text} cls={revG.cls} />
          <Stat label="EPS YoY" value={epsG.text} cls={epsG.cls} />
        </div>
      </Panel>

      {/* Investor archetype scorecards — graceful absence: renders nothing
          when archetypes.json hasn't been generated yet or this symbol
          isn't in it (same degradation pattern as every other optional
          section on this page). */}
      {archetype && (
        <Panel title="Investor archetype scorecards">
          <ArchetypePanel record={archetype} />
        </Panel>
      )}

      {/* 2-stage FCF DCF — graceful absence: base FCF/share can't be
          derived from any real fundamentals field for every name (never
          fabricated), so the whole panel (including its header) is skipped
          rather than showing an empty shell. Same degradation pattern as
          every other optional section on this page. */}
      {dcfDefaults.baseFcf.value != null && (
        <Panel title="DCF — fair value estimate (toy model)">
          <DcfPanel symbol={s.symbol} defaults={dcfDefaults} />
        </Panel>
      )}

      {/* History sparklines */}
      <Panel title="History — annual (oldest → newest)">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-3">
          {histories.map((h) => (
            <div key={h.key} className="flex items-center justify-between gap-3">
              <span className="text-[11px] text-term-muted whitespace-nowrap">
                {h.label}
              </span>
              <Sparkline series={s.history?.[h.key]} isEps={h.eps} />
            </div>
          ))}
        </div>
      </Panel>

      {/* Peer comparison */}
      {peerKeys.length > 0 && (
        <Panel title="Peer comparison — value vs cohort median (percentile)">
          <div className="overflow-x-auto">
            <table className="term">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th className="numcell">Value</th>
                  <th className="numcell">Industry median</th>
                  <th className="numcell">Ind. %ile</th>
                  <th className="numcell">Layer median</th>
                  <th className="numcell">Layer %ile</th>
                </tr>
              </thead>
              <tbody>
                {peerKeys.map((k) => {
                  const ind: PeerMetric | undefined = industryPeers[k];
                  const lay: PeerMetric | undefined = layerPeers[k];
                  const val = ind?.value ?? lay?.value ?? null;
                  return (
                    <tr key={k}>
                      <td className="text-zinc-300">{titleCase(k)}</td>
                      <td className="numcell tnum">{num(val, 2)}</td>
                      <td className="numcell tnum text-term-muted">
                        {num(ind?.median ?? null, 2)}
                      </td>
                      <td className="numcell tnum">
                        <Pctile value={ind?.percentile} />
                      </td>
                      <td className="numcell tnum text-term-muted">
                        {num(lay?.median ?? null, 2)}
                      </td>
                      <td className="numcell tnum">
                        <Pctile value={lay?.percentile} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {/* The one bottleneck */}
      <Panel title="The one bottleneck">
        <dl className="flex flex-col gap-2 text-[12px]">
          <BottleneckRow
            label="Physical"
            value={s.constraint?.physical_bottleneck}
          />
          <BottleneckRow
            label="Regulatory"
            value={s.constraint?.regulatory_bottleneck}
          />
          <BottleneckRow
            label="Lead time"
            value={s.constraint?.lead_time_note}
          />
        </dl>
      </Panel>

      {/* Catalysts */}
      {catalysts.length > 0 && (
        <Panel title="Catalysts">
          <div className="overflow-x-auto">
            <table className="term">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Event</th>
                  <th>Certainty</th>
                </tr>
              </thead>
              <tbody>
                {catalysts.map((c) => (
                  <tr key={c.id}>
                    <td className="tnum">{catalystDate(c.display ?? c.date)}</td>
                    <td className="text-zinc-300">
                      {c.type ? titleCase(c.type) : DASH}
                    </td>
                    <td className="text-zinc-300 whitespace-normal">
                      {c.title ?? DASH}
                    </td>
                    <td className="text-term-muted">
                      {c.certainty ? titleCase(c.certainty) : DASH}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {/* Related news */}
      <Panel title="Related news" className="scroll-mt-16" id="related-news">
        <StockNews articles={news} />
      </Panel>

      {/* Relationships */}
      {(counterparties.length > 0 || labExposure.length > 0) && (
        <Panel title="Relationships">
          {counterparties.length > 0 && (
            <div className="overflow-x-auto">
              <table className="term">
                <thead>
                  <tr>
                    <th>Counterparty</th>
                    <th>Type</th>
                    <th className="numcell">USD</th>
                  </tr>
                </thead>
                <tbody>
                  {counterparties.map((c, i) => {
                    const link = getStock(c.node);
                    return (
                      <tr key={`${c.node}-${i}`}>
                        <td>
                          {link ? (
                            <Link
                              href={`/stocks/${c.node}`}
                              className="text-emerald-400 hover:text-emerald-300 font-semibold"
                            >
                              {c.node}
                            </Link>
                          ) : (
                            <span className="text-zinc-300">
                              {titleCase(c.node)}
                            </span>
                          )}
                        </td>
                        <td className="text-term-muted">{titleCase(c.type)}</td>
                        <td className="numcell tnum">{usd(c.usd)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          {labExposure.length > 0 && (
            <div className="mt-3">
              <div className="text-[10px] uppercase tracking-wider text-term-muted mb-1">
                Lab exposure
              </div>
              <div className="flex flex-wrap gap-1.5">
                {labExposure.map((le, i) => (
                  <span
                    key={`${le.lab}-${i}`}
                    className="text-[11px] px-1.5 py-0.5 rounded-sm border border-term-border bg-[#0b0f17]"
                  >
                    <span className="text-zinc-200">{titleCase(le.lab)}</span>
                    {le.pct != null && (
                      <span className="text-term-muted"> · {pct(le.pct, 0)}</span>
                    )}
                    {le.usd != null && (
                      <span className="text-term-muted"> · {usd(le.usd)}</span>
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}
        </Panel>
      )}

      {/* Narrative */}
      {hasNarrative && (
        <Panel title="Narrative">
          <div className="flex flex-col gap-4 text-[12.5px] leading-relaxed text-zinc-300">
            {n.valuation_take && (
              <NarrSection title="Valuation take" body={n.valuation_take} />
            )}
            {n.bottleneck_rationale && (
              <NarrSection
                title="Bottleneck rationale"
                body={n.bottleneck_rationale}
              />
            )}
            {n.scenarios && n.scenarios.length > 0 && (
              <div>
                <h3 className="text-[10.5px] font-semibold uppercase tracking-wider text-term-muted mb-1.5">
                  Scenarios
                </h3>
                <ul className="flex flex-col gap-2">
                  {n.scenarios.map((sc, i) => (
                    <li
                      key={i}
                      className="border-l-2 border-term-border pl-3"
                    >
                      {sc}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {n.risks && n.risks.length > 0 && (
              <div>
                <h3 className="text-[10.5px] font-semibold uppercase tracking-wider text-term-muted mb-1.5">
                  Risks
                </h3>
                <ul className="list-disc pl-5 flex flex-col gap-1">
                  {n.risks.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
            {n.synthesis && (
              <NarrSection title="Synthesis" body={n.synthesis} />
            )}
          </div>
        </Panel>
      )}

      <p className="text-[10px] text-term-muted">
        Figures as of {dateOnly(s.as_of)}. Educational research only — not
        financial advice. Values may be null and render as —.
      </p>
    </div>
  );
}

function FundamentalTag({ tag }: { tag?: string | null }) {
  if (!tag) return <span className="text-term-muted text-[12px]">{DASH}</span>;
  const color =
    tag === "Undervalued"
      ? "#10b981"
      : tag === "Overvalued"
        ? "#ef4444"
        : tag === "Fairly Valued"
          ? "#f59e0b"
          : undefined;
  return (
    <span
      className="text-[12px] font-semibold"
      style={color ? { color } : undefined}
    >
      {tag}
    </span>
  );
}

function Pctile({ value }: { value?: number | null }) {
  if (typeof value !== "number" || !Number.isFinite(value))
    return <span className="text-term-muted">{DASH}</span>;
  const cls =
    value >= 75
      ? "text-emerald-400"
      : value <= 25
        ? "text-rose-400"
        : "text-zinc-300";
  return <span className={cls}>{value.toFixed(0)}</span>;
}

function BottleneckRow({
  label,
  value,
}: {
  label: string;
  value?: string | null;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:gap-3">
      <dt className="text-[10px] uppercase tracking-wider text-term-muted sm:w-24 shrink-0 pt-0.5">
        {label}
      </dt>
      <dd className="text-zinc-300">{value || DASH}</dd>
    </div>
  );
}

function NarrSection({ title, body }: { title: string; body: string }) {
  return (
    <div>
      <h3 className="text-[10.5px] font-semibold uppercase tracking-wider text-term-muted mb-1">
        {title}
      </h3>
      <p>{body}</p>
    </div>
  );
}
