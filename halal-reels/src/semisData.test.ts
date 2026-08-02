import { describe, it, expect } from "vitest";
import {
  crashCloses, crashCandles, gapCloses,
  SEMIS_STARTS, SEMIS_TOTAL, SEMIS_MINI_TOTAL,
  CRASH_LEN, LEV_LEN, KOREA_LEN, FORCED_LEN, US_LEN, ROT_LEN, CTA_LEN,
  SNDK_DROP_PCT, LEVERAGE_B,
} from "./semisData";

const inUnit = (a: number[]) => a.every((v) => v >= 0 && v <= 1);

describe("semisData", () => {
  it("beat starts are cumulative and total matches", () => {
    expect(SEMIS_STARTS.crash).toBe(0);
    expect(SEMIS_STARTS.lev).toBe(CRASH_LEN);
    expect(SEMIS_STARTS.cta).toBe(CRASH_LEN + LEV_LEN + KOREA_LEN + FORCED_LEN + US_LEN + ROT_LEN);
    expect(SEMIS_TOTAL).toBe(CRASH_LEN + LEV_LEN + KOREA_LEN + FORCED_LEN + US_LEN + ROT_LEN + CTA_LEN);
    expect(SEMIS_MINI_TOTAL).toBeGreaterThan(0);
  });
  it("crashCloses declines and stays in unit range", () => {
    const c = crashCloses(60);
    expect(c).toHaveLength(60);
    expect(inUnit(c)).toBe(true);
    expect(c[0]).toBeGreaterThan(c[c.length - 1]);
    expect(c[0] - c[c.length - 1]).toBeGreaterThan(0.4); // a real crash, not a drift
  });
  it("crashCandles are OHLC-consistent in unit range", () => {
    const k = crashCandles(60);
    expect(k).toHaveLength(60);
    for (const c of k) {
      expect(c.h).toBeGreaterThanOrEqual(Math.max(c.o, c.c));
      expect(c.l).toBeLessThanOrEqual(Math.min(c.o, c.c));
      expect(c.l).toBeGreaterThanOrEqual(0);
      expect(c.h).toBeLessThanOrEqual(1);
    }
  });
  it("gapCloses declines and stays in unit range", () => {
    const g = gapCloses(60);
    expect(inUnit(g)).toBe(true);
    expect(g[0]).toBeGreaterThan(g[g.length - 1]);
  });
  it("relayed figures are the source values", () => {
    expect(SNDK_DROP_PCT).toBeCloseTo(-14.1);
    expect(LEVERAGE_B).toBe(39);
  });
});
