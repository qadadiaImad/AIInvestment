// Deterministic data + timing for SemisReel. No Math.random / Date.now:
// same numbers every render (mirror correlationData.ts). The price motions are
// ILLUSTRATIVE animations of a reported market story, not real tick data — the
// relayed figures (SNDK_DROP_PCT etc.) are shown "as reported", see the reel rail.

export const SEMIS_DATE = "2026-08-02";

// Beat lengths @30fps.
export const CRASH_LEN = 180; // 6s
export const LEV_LEN = 150;   // 5s
export const KOREA_LEN = 150; // 5s
export const FORCED_LEN = 150;// 5s
export const US_LEN = 150;    // 5s
export const ROT_LEN = 180;   // 6s
export const CTA_LEN = 180;   // 6s

export const SEMIS_STARTS = {
  crash: 0,
  lev: CRASH_LEN,
  korea: CRASH_LEN + LEV_LEN,
  forced: CRASH_LEN + LEV_LEN + KOREA_LEN,
  us: CRASH_LEN + LEV_LEN + KOREA_LEN + FORCED_LEN,
  rot: CRASH_LEN + LEV_LEN + KOREA_LEN + FORCED_LEN + US_LEN,
  cta: CRASH_LEN + LEV_LEN + KOREA_LEN + FORCED_LEN + US_LEN + ROT_LEN,
};
export const SEMIS_TOTAL =
  CRASH_LEN + LEV_LEN + KOREA_LEN + FORCED_LEN + US_LEN + ROT_LEN + CTA_LEN;

// Mini cut: crash (hook+drop) -> rotation (payoff) -> cta.
export const SEMIS_MINI_STARTS = { crash: 0, rot: CRASH_LEN, cta: CRASH_LEN + ROT_LEN };
export const SEMIS_MINI_TOTAL = CRASH_LEN + ROT_LEN + CTA_LEN;

export const WHOOSH_OFFSETS = [
  SEMIS_STARTS.crash, SEMIS_STARTS.lev, SEMIS_STARTS.korea,
  SEMIS_STARTS.forced, SEMIS_STARTS.us, SEMIS_STARTS.rot, SEMIS_STARTS.cta,
];

// Relayed-as-reported figures (NOT our data).
export const SNDK_DROP_PCT = -14.1;
export const LEVERAGE_B = 39;
export const LEVERAGE_PREV_B = 30;

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

/** Declining normalized close series: high -> low with an accelerating drop
 * plus a small deterministic wiggle. 1 = top of frame region. */
export const crashCloses = (n: number): number[] =>
  Array.from({ length: n }, (_, i) => {
    const t = i / (n - 1);
    const trend = 0.92 - 0.78 * Math.pow(t, 1.5);
    const wiggle = 0.035 * Math.sin(i * 0.7) + 0.02 * Math.sin(i * 0.31 + 1.1);
    return clamp01(trend + wiggle);
  });

/** OHLC candles derived from crashCloses: open = prior close, close = this
 * close, high/low bracket the body with a deterministic wick. */
export const crashCandles = (
  n: number,
): Array<{ o: number; h: number; l: number; c: number }> => {
  const cl = crashCloses(n);
  return cl.map((c, i) => {
    const o = i === 0 ? clamp01(c + 0.05) : cl[i - 1];
    const wick = 0.02 + 0.02 * Math.abs(Math.sin(i * 0.9));
    const h = clamp01(Math.max(o, c) + wick);
    const l = clamp01(Math.min(o, c) - wick);
    return { o, h, l, c };
  });
};

/** Korea "gap down" series: flat holds punctuated by sharp downward gaps. */
export const gapCloses = (n: number): number[] => {
  const steps = 5;
  return Array.from({ length: n }, (_, i) => {
    const seg = Math.floor((i / n) * steps);
    const level = 0.9 - seg * 0.16;
    const wiggle = 0.015 * Math.sin(i * 1.3);
    return clamp01(level + wiggle);
  });
};
