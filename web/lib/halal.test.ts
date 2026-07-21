import { describe, expect, it } from "vitest";
import { fmtRatioPct, overallLabel, overallTone, purificationAmount } from "./halal";

describe("halal display helpers", () => {
  it("labels every overall verdict", () => {
    expect(overallLabel("halal")).toBe("Halal");
    expect(overallLabel("not_halal")).toBe("Not halal");
    expect(overallLabel("questionable")).toBe("Questionable");
    expect(overallLabel("insufficient_data")).toBe("Insufficient data");
  });
  it("maps verdicts to tones", () => {
    expect(overallTone("halal")).toBe("pass");
    expect(overallTone("not_halal")).toBe("fail");
    expect(overallTone("questionable")).toBe("warn");
    expect(overallTone("insufficient_data")).toBe("muted");
  });
  it("formats ratios as percentages, em-dash for null", () => {
    expect(fmtRatioPct(0.0026)).toBe("0.26%");
    expect(fmtRatioPct(0.5)).toBe("50.00%");
    expect(fmtRatioPct(null)).toBe("—");
  });
});

describe("purificationAmount", () => {
  it("multiplies perShare by shares", () => {
    expect(purificationAmount(0.031, 100)).toBeCloseTo(3.1, 9);
  });
  it("returns null when perShare is null", () => {
    expect(purificationAmount(null, 100)).toBeNull();
  });
  it("returns null when shares is 0", () => {
    expect(purificationAmount(0.03, 0)).toBeNull();
  });
  it("returns null when shares is negative", () => {
    expect(purificationAmount(0.03, -5)).toBeNull();
  });
});
