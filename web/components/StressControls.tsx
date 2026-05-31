"use client";

// Two macro-stress sliders shared by /resiliency and /map.
// Rate shock: Δ basis points, 0…+300. Electricity: Δ%, 0…+50.
// 0/0 = current snapshot (no recompute).

export interface StressState {
  dRateBps: number;
  dElecPct: number;
}

export const STRESS_ZERO: StressState = { dRateBps: 0, dElecPct: 0 };

export default function StressControls({
  value,
  onChange,
  compact = false,
}: {
  value: StressState;
  onChange: (v: StressState) => void;
  compact?: boolean;
}) {
  const { dRateBps, dElecPct } = value;
  const active = dRateBps !== 0 || dElecPct !== 0;

  const labelCls = compact
    ? "text-[9.5px] uppercase tracking-wider text-term-muted whitespace-nowrap"
    : "text-[10.5px] uppercase tracking-wider text-term-muted";
  const valCls = compact
    ? "tnum text-[10px] text-zinc-200 w-[58px] text-right"
    : "tnum text-[12px] font-semibold text-zinc-100 w-[72px] text-right";

  return (
    <div
      className={
        compact
          ? "flex flex-wrap items-center gap-x-3 gap-y-1.5"
          : "flex flex-col gap-3"
      }
    >
      <div
        className={
          compact
            ? "flex items-center gap-2"
            : "flex items-center gap-3 flex-wrap"
        }
      >
        <label htmlFor="rate-shock" className={labelCls}>
          Rate shock
        </label>
        <input
          id="rate-shock"
          type="range"
          min={0}
          max={300}
          step={5}
          value={dRateBps}
          onChange={(e) =>
            onChange({ ...value, dRateBps: Number(e.target.value) })
          }
          className={compact ? "accent-emerald-500 w-28" : "accent-emerald-500 flex-1 min-w-[160px]"}
        />
        <span className={valCls}>+{dRateBps} bps</span>
      </div>

      <div
        className={
          compact
            ? "flex items-center gap-2"
            : "flex items-center gap-3 flex-wrap"
        }
      >
        <label htmlFor="elec-shock" className={labelCls}>
          Electricity
        </label>
        <input
          id="elec-shock"
          type="range"
          min={0}
          max={50}
          step={1}
          value={dElecPct}
          onChange={(e) =>
            onChange({ ...value, dElecPct: Number(e.target.value) })
          }
          className={compact ? "accent-amber-500 w-28" : "accent-amber-500 flex-1 min-w-[160px]"}
        />
        <span className={valCls}>+{dElecPct}%</span>
      </div>

      <button
        type="button"
        onClick={() => onChange(STRESS_ZERO)}
        disabled={!active}
        className={`${
          compact ? "text-[9.5px] px-1.5 py-0.5" : "text-[10.5px] px-2 py-1 self-start"
        } rounded-sm border border-term-border uppercase tracking-wider transition-colors ${
          active
            ? "text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
            : "text-zinc-600 cursor-default"
        }`}
      >
        Reset
      </button>
    </div>
  );
}
