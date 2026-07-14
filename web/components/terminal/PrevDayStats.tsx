import type { TaInstrument } from "@/lib/ta";
import { num, signedPct } from "@/lib/format";

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

// 5 Stat blocks: O/H/L/C/Change% from levels.previous_day_ohlc.
export default function PrevDayStats({
  instrument,
}: {
  instrument: TaInstrument;
}) {
  const o = instrument.levels.previous_day_ohlc;
  const d = instrument.asset_class === "fx" ? 4 : 2;
  const chg = signedPct(o.change_pct);
  return (
    <div className="grid grid-cols-3 sm:grid-cols-5 gap-3">
      <Stat label={o.date ? `Open (${o.date})` : "Open"} value={num(o.open, d)} />
      <Stat label="High" value={num(o.high, d)} />
      <Stat label="Low" value={num(o.low, d)} />
      <Stat label="Close" value={num(o.close, d)} />
      <Stat label="Change" value={chg.text} cls={chg.cls} />
    </div>
  );
}
