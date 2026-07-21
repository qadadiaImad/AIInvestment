import Link from "next/link";
import type { TaInstrument } from "@/lib/ta";
import { DASH, num, signedPct } from "@/lib/format";
import TrendBadge from "@/components/terminal/TrendBadge";
import Sparkline from "@/components/Sparkline";

// Server component — whole card is a <Link>, >=44px tap target. Missing/
// null fields render DASH, never blank.
export default function InstrumentTile({
  instrument,
}: {
  instrument: TaInstrument;
}) {
  const chg = signedPct(instrument.price?.day_change_pct);
  const nl = instrument.nearest_level;
  const nlSigned =
    nl && typeof nl.distance_pct === "number"
      ? signedPct(nl.distance_pct)
      : null;

  // Sparkline expects {date, value}[] — remap the ta_desk {t,c}[] shape at
  // the call site, never modify Sparkline.tsx itself.
  const sparkSeries = (instrument.sparkline ?? []).map((p) => ({
    date: p.t,
    value: p.c,
  }));

  return (
    <Link
      href={`/terminal/${instrument.symbol}`}
      className="min-h-[44px] flex flex-col gap-1.5 border border-term-border rounded-sm bg-[#0e131d] px-2.5 py-2 hover:border-emerald-500/50 transition-colors"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-bold text-[13px] tracking-tight truncate">
          {instrument.symbol}
        </span>
        <TrendBadge state={instrument.trend?.state} />
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-[18px] font-bold tnum">
          {num(instrument.price?.last, instrument.asset_class === "fx" ? 4 : 2)}
        </span>
        <span className={`text-[11px] tnum ${chg.cls}`}>{chg.text}</span>
      </div>

      <Sparkline series={sparkSeries} width={110} height={24} />

      <div className="text-[10px] tnum truncate">
        {nl ? (
          <span className={nlSigned?.cls ?? "text-term-muted"}>
            {nl.label} {num(nl.value, instrument.asset_class === "fx" ? 4 : 2)}
            {nlSigned ? ` (${nlSigned.text})` : ""}
          </span>
        ) : (
          <span className="text-term-muted">{DASH}</span>
        )}
      </div>
    </Link>
  );
}
