/**
 * props — reusable newsroom set fixtures. The DEBT CLOCK is a live LED-segment counter
 * (NYC national-debt-clock style) that ticks upward in real time. Drop it into a studio
 * `screen`/`wall` slot or render it big for a CTA. Digits are laid out in fixed-width
 * cells so the number never wobbles as low digits blur past.
 */
import React from "react";
import { BODY } from "./reelkit";

export const DebtClock: React.FC<{
  f: number;
  base?: number;       // starting value (USD)
  rate?: number;       // USD added per real second (global debt ≈ +$29T/yr ≈ $919k/s)
  label?: string;
  digitSize?: number;  // px height of a digit
  color?: string;
}> = ({ f, base = 348_300_000_000_000, rate = 919000, label = "WORLD DEBT · LIVE ESTIMATE", digitSize = 44, color = "#ff4038" }) => {
  const val = base + Math.round(rate * (f / 30));
  const s = "$" + val.toLocaleString("en-US");
  const dw = digitSize * 0.64;
  const nw = digitSize * 0.30; // narrow chars ($ , .)
  let x = 0;
  const cells = s.split("").map((ch) => {
    const narrow = ch === "," || ch === ".";
    const w = narrow ? nw : dw;
    const cx = x + w / 2;
    x += w;
    return { ch, cx };
  });
  const totalW = x;
  const padX = digitSize * 0.7;
  const PW = totalW + padX * 2;
  const PH = digitSize * 1.95;
  const rowY = PH * 0.72;
  const startX = (PW - totalW) / 2;
  const blink = Math.floor(f / 15) % 2 === 0;
  return (
    <g>
      <rect x="0" y="0" width={PW} height={PH} rx="12" fill="#0b0607" stroke="#3a1412" strokeWidth="2" />
      <rect x="6" y="6" width={PW - 12} height={PH - 12} rx="8" fill="#140a09" stroke="#521a17" strokeWidth="1.5" />
      {/* label + live dot */}
      <circle cx={padX + 4} cy={digitSize * 0.62} r={digitSize * 0.11} fill={blink ? "#ff4038" : "#5a1a17"} />
      <text x={padX + digitSize * 0.34} y={digitSize * 0.72} fontFamily={BODY} fontWeight="800" fontSize={digitSize * 0.34} letterSpacing="1.5" fill="#c98b86">{label}</text>
      {/* glow copy */}
      <g style={{ filter: `blur(${digitSize * 0.09}px)` }} opacity="0.85">
        {cells.map((c, i) => (
          <text key={i} x={startX + c.cx} y={rowY} textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize={digitSize} fill={color}>{c.ch}</text>
        ))}
      </g>
      {/* crisp digits */}
      {cells.map((c, i) => (
        <text key={i} x={startX + c.cx} y={rowY} textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize={digitSize} fill={c.ch === "," ? "#8a2a25" : color}>{c.ch}</text>
      ))}
    </g>
  );
};

// exposed so an episode can size a layout around the clock without re-deriving it
export const debtClockWidth = (val: number, digitSize = 44) => {
  const s = "$" + val.toLocaleString("en-US");
  const dw = digitSize * 0.64, nw = digitSize * 0.30;
  const w = s.split("").reduce((a, ch) => a + (ch === "," || ch === "." ? nw : dw), 0);
  return w + digitSize * 1.4;
};
