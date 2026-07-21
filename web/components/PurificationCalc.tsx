// Client Component — interactive purification calculator.
// Renders under the purification block in HalalCard.
//
// No persistence, no server calls. Pure client-side math.
// Computed methodology results — not a fatwa, not financial advice. Educational only.

"use client";

import { useState } from "react";
import { purificationAmount } from "@/lib/halal";

export interface PurificationCalcProps {
  perShare: number | null;
  status: string;
  missing: string | null;
}

export default function PurificationCalc({
  perShare,
  status,
  missing,
}: PurificationCalcProps) {
  const [shares, setShares] = useState<string>("");

  if (status !== "computed" || perShare === null) {
    return (
      <p className="text-[10.5px] text-zinc-400 mt-1.5">
        Total purification unavailable
        {missing ? ` — ${missing}` : ""}
      </p>
    );
  }

  const sharesNum = parseFloat(shares);
  const total =
    shares !== "" && Number.isFinite(sharesNum)
      ? purificationAmount(perShare, sharesNum)
      : null;

  return (
    <div className="mt-2 flex flex-col gap-1.5">
      <label className="text-[10px] text-term-muted font-semibold uppercase tracking-wider">
        Calculate total purification
      </label>
      <div className="flex items-center gap-2">
        <input
          type="number"
          min="0"
          step="1"
          value={shares}
          onChange={(e) => setShares(e.target.value)}
          placeholder="Shares held"
          className="w-32 px-2 py-1 text-[11px] text-zinc-200 bg-[#0e131d] border border-term-border rounded-sm focus:outline-none focus:border-zinc-500 tnum placeholder:text-term-muted"
        />
        {total !== null ? (
          <span className="text-[12px] text-zinc-200 tnum font-semibold">
            $
            {total.toLocaleString("en-US", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </span>
        ) : (
          shares !== "" && (
            <span className="text-[11px] text-term-muted">—</span>
          )
        )}
      </div>
      <p className="text-[9.5px] text-term-muted leading-snug">
        {perShare.toFixed(4)} per share × shares held. Computed methodology result — not a fatwa.
      </p>
    </div>
  );
}
