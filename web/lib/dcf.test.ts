import { describe, it, expect } from "vitest";
import {
  deriveBaseFcfPerShare,
  deriveDefaultGrowth,
  deriveDefaultDiscountRate,
  buildDefaultDcfInputs,
  runDcf,
  runDcfWithUpside,
  sensitivityGrid,
  GROWTH_CAP,
  GROWTH_DEFAULT,
  TERMINAL_GROWTH_DEFAULT,
} from "./dcf";
import type { MacroData } from "./macro";

// Hand-computed fixtures per docs/superpowers/specs (Round 7 DCF design spec)
// §5. Arithmetic cross-checked with a standalone Python/Node script
// implementing the exact §1 formulas — see spec for the worked values.

describe("deriveBaseFcfPerShare", () => {
  it("case 1: pfcf basis (primary)", () => {
    const result = deriveBaseFcfPerShare({
      valuation: { price: 100, pe: null, profitability: null },
      fundamentals: {
        gross_margin: null,
        operating_margin: null,
        net_margin: null,
        fcf_margin: null,
        roe: null,
        roa: null,
        roic: null,
        debt_to_equity: null,
        current_ratio: null,
        ps: null,
        pb: null,
        pfcf: 20,
        rev_growth_yoy: null,
        eps_growth_yoy: null,
        sector: null,
        industry: null,
      },
    });
    expect(result).toEqual({ value: 5, basis: "pfcf", reason: null });
  });

  it("case 2: pfcf rejected (<=0), falls to ps/fcf_margin", () => {
    const result = deriveBaseFcfPerShare({
      valuation: { price: 50, pe: null, profitability: null },
      fundamentals: {
        gross_margin: null,
        operating_margin: null,
        net_margin: null,
        fcf_margin: 0.15,
        roe: null,
        roa: null,
        roic: null,
        debt_to_equity: null,
        current_ratio: null,
        ps: 5,
        pb: null,
        pfcf: -3,
        rev_growth_yoy: null,
        eps_growth_yoy: null,
        sector: null,
        industry: null,
      },
    });
    expect(result.basis).toBe("ps_margin");
    expect(result.reason).toBeNull();
    expect(result.value).toBeCloseTo(1.5, 6);
  });

  it("case 3: everything unusable -> null, never faked (no price)", () => {
    const result = deriveBaseFcfPerShare({
      valuation: { price: null, pe: null, profitability: null },
      fundamentals: {
        gross_margin: null,
        operating_margin: null,
        net_margin: null,
        fcf_margin: 0.15,
        roe: null,
        roa: null,
        roic: null,
        debt_to_equity: null,
        current_ratio: null,
        ps: 5,
        pb: null,
        pfcf: 20,
        rev_growth_yoy: null,
        eps_growth_yoy: null,
        sector: null,
        industry: null,
      },
    });
    expect(result).toEqual({ value: null, basis: "none", reason: "no price" });
  });
});

describe("deriveDefaultGrowth", () => {
  it("case 4: actual, within cap", () => {
    const result = deriveDefaultGrowth({
      fundamentals: {
        gross_margin: null,
        operating_margin: null,
        net_margin: null,
        fcf_margin: null,
        roe: null,
        roa: null,
        roic: null,
        debt_to_equity: null,
        current_ratio: null,
        ps: null,
        pb: null,
        pfcf: null,
        rev_growth_yoy: 0.2,
        eps_growth_yoy: null,
        sector: null,
        industry: null,
      },
    });
    expect(result).toEqual({ rate: 0.2, raw: 0.2, source: "actual" });
  });

  it("case 5: actual, clamped at cap", () => {
    const result = deriveDefaultGrowth({
      fundamentals: {
        gross_margin: null,
        operating_margin: null,
        net_margin: null,
        fcf_margin: null,
        roe: null,
        roa: null,
        roic: null,
        debt_to_equity: null,
        current_ratio: null,
        ps: null,
        pb: null,
        pfcf: null,
        rev_growth_yoy: 0.9,
        eps_growth_yoy: null,
        sector: null,
        industry: null,
      },
    });
    expect(result).toEqual({ rate: GROWTH_CAP, raw: 0.9, source: "actual" });
  });

  it("case 6: null -> default", () => {
    const result = deriveDefaultGrowth({
      fundamentals: {
        gross_margin: null,
        operating_margin: null,
        net_margin: null,
        fcf_margin: null,
        roe: null,
        roa: null,
        roic: null,
        debt_to_equity: null,
        current_ratio: null,
        ps: null,
        pb: null,
        pfcf: null,
        rev_growth_yoy: null,
        eps_growth_yoy: null,
        sector: null,
        industry: null,
      },
    });
    expect(result).toEqual({ rate: GROWTH_DEFAULT, raw: null, source: "default" });
  });
});

const MACRO_FIXTURE: MacroData = {
  generated_at: "2026-07-14T00:00:00Z",
  schema_version: "macro-desk-v1",
  source: "FRED",
  source_class: "api",
  disclaimer: "Educational only.",
  series: [
    {
      series_id: "DGS10",
      symbol: "10Y",
      display_name: "10-Year Treasury",
      group: "RATES",
      frequency: "daily",
      unit: "%",
      unit_kind: "pct",
      decimals: 3,
      transform: "level",
      last: 4.474,
      previous: null,
      change_abs: null,
      change_pct: null,
      value_1y_ago: null,
      change_1y_pct: null,
      as_of: "2026-07-14",
      history_window_days: 365,
      sparkline: [],
      retrieved_at: "2026-07-14T00:00:00Z",
      source: "FRED",
      source_class: "api",
      source_url: "https://fred.stlouisfed.org",
      warnings: [],
    },
  ],
  regime: { headline: "", chips: [] },
  warnings: [],
};

describe("deriveDefaultDiscountRate", () => {
  it("case 7: macro present, DGS10 resolvable", () => {
    const result = deriveDefaultDiscountRate(MACRO_FIXTURE);
    expect(result.source).toBe("macro_dgs10");
    expect(result.dgs10).toBe(4.474);
    expect(result.rate).toBeCloseTo(0.08974, 6);
  });

  it("case 8: macro null -> flat fallback", () => {
    const result = deriveDefaultDiscountRate(null);
    expect(result).toEqual({ rate: 0.095, source: "flat_fallback", dgs10: null });
  });
});

describe("runDcf", () => {
  it("case 9: Fixture A, full engine", () => {
    const r = runDcf({
      baseFcfPerShare: 5,
      growthY1: 0.2,
      terminalGrowth: 0.025,
      discountRate: 0.1,
    });
    expect(r.valid).toBe(true);
    expect(r.error).toBeNull();
    const growths = r.rows.map((row) => row.growth);
    const expectedGrowths = [0.2, 0.15625, 0.1125, 0.06875, 0.025];
    growths.forEach((g, i) => expect(g).toBeCloseTo(expectedGrowths[i], 9));
    expect(r.rows.map((row) => row.fcf)).toEqual([
      expect.closeTo(6.0, 4),
      expect.closeTo(6.9375, 4),
      expect.closeTo(7.717969, 4),
      expect.closeTo(8.248579, 4),
      expect.closeTo(8.454794, 4),
    ] as unknown as number[]);
    expect(r.sumPvStage1).toBeCloseTo(27.870293, 3);
    expect(r.terminalValue).toBeCloseTo(115.548846, 3);
    expect(r.pvTerminalValue).toBeCloseTo(71.746742, 3);
    expect(r.fairValuePerShare).toBeCloseTo(99.617035, 3);
  });

  it("case 10: Fixture B, ps/fcf_margin-derived base", () => {
    const r = runDcf({
      baseFcfPerShare: 1.5,
      growthY1: 0.1,
      terminalGrowth: 0.025,
      discountRate: 0.0897,
    });
    expect(r.valid).toBe(true);
    expect(r.sumPvStage1).toBeCloseTo(7.204561, 2);
    expect(r.terminalValue).toBeCloseTo(32.127649, 2);
    expect(r.pvTerminalValue).toBeCloseTo(20.909526, 2);
    expect(r.fairValuePerShare).toBeCloseTo(28.114087, 2);
  });

  it("case 11: invalidity guard, r <= gT", () => {
    const r = runDcf({
      baseFcfPerShare: 5,
      growthY1: 0.2,
      terminalGrowth: 0.025,
      discountRate: 0.02,
    });
    expect(r.valid).toBe(false);
    expect(r.error).toBe("discount rate must exceed terminal growth");
    expect(r.fairValuePerShare).toBeNull();
    expect(Number.isFinite(r.sumPvStage1)).toBe(true);
    // Never surface NaN/Infinity, even in the internal fields.
    expect(Number.isFinite(r.terminalValue)).toBe(true);
    expect(Number.isFinite(r.pvTerminalValue)).toBe(true);
  });

  it("case 12: zero-growth-fade flat case collapses to plain Gordon growth", () => {
    const r = runDcf({
      baseFcfPerShare: 10,
      growthY1: 0.025,
      terminalGrowth: 0.025,
      discountRate: 0.075,
    });
    expect(r.valid).toBe(true);
    expect(r.rows.every((row) => row.growth === 0.025)).toBe(true);
    // Independent cross-check: FCF0*(1+g)/(r-g) — the plain growing-perpetuity
    // closed form — should match since stage-1/stage-2 fade collapses to a
    // constant growth rate when g1 === gT.
    const closedForm = (10 * (1 + 0.025)) / (0.075 - 0.025);
    expect(r.fairValuePerShare).toBeCloseTo(closedForm, 3);
    expect(r.fairValuePerShare).toBeCloseTo(205.0, 1);
  });
});

describe("runDcfWithUpside", () => {
  it("case 13: price comparison", () => {
    const r = runDcfWithUpside(
      {
        baseFcfPerShare: 5,
        growthY1: 0.2,
        terminalGrowth: 0.025,
        discountRate: 0.1,
      },
      110,
    );
    expect(r.currentPrice).toBe(110);
    expect(r.upsidePct).toBeCloseTo(-9.44, 1);
  });

  it("case 14: null price -> null upside, no throw", () => {
    const r = runDcfWithUpside(
      {
        baseFcfPerShare: 5,
        growthY1: 0.2,
        terminalGrowth: 0.025,
        discountRate: 0.1,
      },
      null,
    );
    expect(r.currentPrice).toBeNull();
    expect(r.upsidePct).toBeNull();
  });
});

describe("sensitivityGrid", () => {
  const base = {
    baseFcfPerShare: 5,
    growthY1: 0.2,
    terminalGrowth: 0.025,
    discountRate: 0.1,
  };

  it("case 15: 3x3 grid off Fixture A base case", () => {
    const grid = sensitivityGrid(base);
    expect(grid.length).toBe(3);
    expect(grid[0].length).toBe(3);
    // center cell matches case 9
    expect(grid[1][1].fairValuePerShare).toBeCloseTo(99.617, 2);

    const expected = [
      [110.6245, 115.2945, 120.1027],
      [95.6122, 99.617, 103.7395],
      [84.1385, 87.6357, 91.2349],
    ];
    for (let i = 0; i < 3; i++) {
      for (let j = 0; j < 3; j++) {
        expect(grid[i][j].fairValuePerShare).toBeCloseTo(expected[i][j], 2);
      }
    }

    // Structural monotonicity: lower discount => higher fair value (rows);
    // higher growth => higher fair value (columns).
    for (let j = 0; j < 3; j++) {
      expect(grid[0][j].fairValuePerShare!).toBeGreaterThan(
        grid[1][j].fairValuePerShare!,
      );
      expect(grid[1][j].fairValuePerShare!).toBeGreaterThan(
        grid[2][j].fairValuePerShare!,
      );
    }
    for (let i = 0; i < 3; i++) {
      expect(grid[i][0].fairValuePerShare!).toBeLessThan(
        grid[i][1].fairValuePerShare!,
      );
      expect(grid[i][1].fairValuePerShare!).toBeLessThan(
        grid[i][2].fairValuePerShare!,
      );
    }
  });
});

describe("buildDefaultDcfInputs", () => {
  it("case 16: integration of all four derive* functions", () => {
    const stock = {
      valuation: { price: 100, pe: null, profitability: null },
      fundamentals: {
        gross_margin: null,
        operating_margin: null,
        net_margin: null,
        fcf_margin: null,
        roe: null,
        roa: null,
        roic: null,
        debt_to_equity: null,
        current_ratio: null,
        ps: null,
        pb: null,
        pfcf: 20,
        rev_growth_yoy: 0.2,
        eps_growth_yoy: null,
        sector: null,
        industry: null,
      },
    };
    const result = buildDefaultDcfInputs(stock, MACRO_FIXTURE);
    expect(result.baseFcf).toEqual({ value: 5, basis: "pfcf", reason: null });
    expect(result.growth).toEqual({ rate: 0.2, raw: 0.2, source: "actual" });
    expect(result.terminalGrowth).toBe(TERMINAL_GROWTH_DEFAULT);
    expect(result.discount.source).toBe("macro_dgs10");
    expect(result.discount.dgs10).toBe(4.474);
    expect(result.discount.rate).toBeCloseTo(0.08974, 6);
    expect(result.years).toBe(5);
    expect(result.currentPrice).toBe(100);
  });
});
