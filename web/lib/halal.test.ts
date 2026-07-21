import { describe, expect, it } from "vitest";
import { fmtRatioPct, overallLabel, overallTone } from "./halal";

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
