import { describe, it, expect } from "vitest";
import {
  ARCHETYPE_ORDER,
  ARCHETYPE_LABELS,
  ARCHETYPE_SUBTITLES,
  ARCHETYPE_COLORS,
  ARCHETYPE_DISCLAIMER,
  archetypeScoreColor,
  archetypeScoreTextClass,
  archetypeVerdictLabel,
  criterionMarkColor,
  criterionMarkGlyph,
  archetypeCriterionValue,
  healthColor,
  healthTextClass,
} from "./format";

// ---------------------------------------------------------------------------
// Verdict-band alignment: archetypeScoreColor/TextClass must be BYTE-
// IDENTICAL thin wrappers over healthColor/healthTextClass (score>70/50-70/
// <50) — this is the corrected merge decision documented in the design doc
// (§7): the backend already emits these exact bands, so no fourth threshold
// constant may be introduced here. These tests pin that contract.
// ---------------------------------------------------------------------------

describe("archetypeScoreColor / archetypeScoreTextClass", () => {
  it("matches healthColor at every boundary", () => {
    for (const v of [null, 0, 49, 50, 50.01, 70, 70.01, 71, 100]) {
      expect(archetypeScoreColor(v)).toBe(healthColor(v));
      expect(archetypeScoreTextClass(v)).toBe(healthTextClass(v));
    }
  });

  it("strong_fit boundary: score just above 70 is emerald", () => {
    expect(archetypeScoreTextClass(70.01)).toBe("text-emerald-400");
  });

  it("partial_fit boundary: score exactly 50 and exactly 70 are amber", () => {
    expect(archetypeScoreTextClass(50)).toBe("text-amber-400");
    expect(archetypeScoreTextClass(70)).toBe("text-amber-400");
  });

  it("poor_fit boundary: score just below 50 is rose", () => {
    expect(archetypeScoreTextClass(49.99)).toBe("text-rose-400");
  });

  it("null (not_evaluable) is grey", () => {
    expect(archetypeScoreTextClass(null)).toBe("text-zinc-500");
  });
});

describe("archetypeVerdictLabel", () => {
  it("maps every verdict to its exact human label", () => {
    expect(archetypeVerdictLabel("strong_fit")).toBe("Strong fit");
    expect(archetypeVerdictLabel("partial_fit")).toBe("Partial fit");
    expect(archetypeVerdictLabel("poor_fit")).toBe("Poor fit");
    expect(archetypeVerdictLabel("not_evaluable")).toBe("Not evaluable");
  });
});

describe("criterionMarkColor / criterionMarkGlyph", () => {
  it("pass=true -> emerald + check", () => {
    expect(criterionMarkColor(true)).toBe("#34d399");
    expect(criterionMarkGlyph(true)).toBe("✓");
  });
  it("pass=false -> rose + cross", () => {
    expect(criterionMarkColor(false)).toBe("#fb7185");
    expect(criterionMarkGlyph(false)).toBe("✗");
  });
  it("pass=null (not evaluable) -> grey + dash", () => {
    expect(criterionMarkColor(null)).toBe("#6b7280");
    expect(criterionMarkGlyph(null)).toBe("–");
  });
});

describe("archetypeCriterionValue", () => {
  it("unit x -> ratio (1dp, x suffix)", () => {
    expect(archetypeCriterionValue(46.2, "x")).toBe("46.2x");
  });
  it("unit pct -> percentage (1dp)", () => {
    expect(archetypeCriterionValue(55.8, "pct")).toBe("55.8%");
  });
  it("unit num, small magnitude (PEG) -> plain 2dp", () => {
    expect(archetypeCriterionValue(1.9, "num")).toBe("1.90");
  });
  it("unit num, large magnitude (market_cap) -> usd() B/T formatting", () => {
    expect(archetypeCriterionValue(200_000_000_000, "num")).toBe("$200.0B");
  });
  it("null actual -> em dash regardless of unit", () => {
    expect(archetypeCriterionValue(null, "x")).toBe("—");
    expect(archetypeCriterionValue(null, "pct")).toBe("—");
    expect(archetypeCriterionValue(null, "num")).toBe("—");
  });
});

describe("archetype static metadata", () => {
  it("ARCHETYPE_ORDER is graham, buffett, lynch", () => {
    expect(ARCHETYPE_ORDER).toEqual(["graham", "buffett", "lynch"]);
  });
  it("every archetype has a label, subtitle, and color", () => {
    for (const key of ARCHETYPE_ORDER) {
      expect(ARCHETYPE_LABELS[key]).toBeTruthy();
      expect(ARCHETYPE_SUBTITLES[key]).toBeTruthy();
      expect(ARCHETYPE_COLORS[key]).toMatch(/^#[0-9a-f]{6}$/);
    }
  });
  it("ARCHETYPE_DISCLAIMER is non-empty and mentions rule-based", () => {
    expect(ARCHETYPE_DISCLAIMER).toContain("Rule-based");
    expect(ARCHETYPE_DISCLAIMER).toContain("not investment advice");
  });
});
