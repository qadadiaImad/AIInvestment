import type { TaInstrument } from "@/lib/ta";
import { DASH, num } from "@/lib/format";

// Local Stat helper — duplicated from the stocks/[symbol]/page.tsx pattern
// (not a shared component; that page keeps its own copy too).
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

function dp(assetClass: string) {
  return assetClass === "fx" ? 4 : 2;
}

export default function LevelsPanel({
  instrument,
}: {
  instrument: TaInstrument;
}) {
  const p = instrument.levels.daily_pivots;
  const atr = instrument.atr14;
  const sessions = instrument.sessions;
  const d = dp(instrument.asset_class);

  const rows: { label: string; value: number | null }[] = [
    { label: "R3", value: p.r3 },
    { label: "R2", value: p.r2 },
    { label: "R1", value: p.r1 },
    { label: "PP", value: p.pp },
    { label: "S1", value: p.s1 },
    { label: "S2", value: p.s2 },
    { label: "S3", value: p.s3 },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="text-[10px] uppercase tracking-wider text-term-muted mb-1">
          Daily pivots
          {p.basis_date ? ` — basis ${p.basis_date}` : ""}
        </div>
        <div className="overflow-x-auto">
          <table className="term">
            <thead>
              <tr>
                <th>Level</th>
                <th className="numcell">Price</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.label}>
                  <td
                    className={
                      r.label === "PP"
                        ? "text-zinc-200 font-semibold"
                        : r.label.startsWith("R")
                          ? "text-emerald-400"
                          : "text-rose-400"
                    }
                  >
                    {r.label}
                  </td>
                  <td className="numcell tnum">{num(r.value, d)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <div className="text-[10px] uppercase tracking-wider text-term-muted mb-1.5">
          ATR(14) bands
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Stat label="ATR14" value={num(atr.value, d)} />
          <Stat label="+1x" value={num(atr.upper_1x, d)} cls="text-emerald-400" />
          <Stat label="-1x" value={num(atr.lower_1x, d)} cls="text-rose-400" />
          <Stat label="+2x / -2x" value={`${num(atr.upper_2x, d)} / ${num(atr.lower_2x, d)}`} />
        </div>
      </div>

      <div>
        <div className="text-[10px] uppercase tracking-wider text-term-muted mb-1.5">
          Session high / low ({sessions.date})
        </div>
        <div className="grid grid-cols-3 gap-3">
          {(
            [
              ["Tokyo", sessions.tokyo],
              ["London", sessions.london],
              ["New York", sessions.new_york],
            ] as const
          ).map(([label, s]) => (
            <div key={label} className="flex flex-col gap-1">
              <span className="text-[9.5px] uppercase tracking-wider text-term-muted">
                {label}
                {!s.complete && (
                  <span className="text-amber-400 ml-1">●</span>
                )}
              </span>
              <span className="text-[12px] tnum">
                {s.high != null ? num(s.high, d) : DASH} /{" "}
                {s.low != null ? num(s.low, d) : DASH}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
