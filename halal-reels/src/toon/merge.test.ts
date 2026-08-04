import { describe, it, expect } from "vitest";
import { merge } from "./merge";
import { DEFAULT } from "./defaults";

describe("merge", () => {
  it("returns a copy of base when no patches", () => {
    const r = merge(DEFAULT);
    expect(r).toEqual(DEFAULT);
    expect(r).not.toBe(DEFAULT); // new object, not a reference
  });
  it("overrides scalar fields, later patches win", () => {
    const r = merge(DEFAULT, { mouth: "open" }, { mouth: "smile" });
    expect(r.mouth).toBe("smile");
  });
  it("deep-merges nested arm/brows without dropping siblings", () => {
    const r = merge(DEFAULT, { armR: { shoulder: 260 } });
    expect(r.armR.shoulder).toBe(260);
    expect(r.armR.elbow).toBe(DEFAULT.armR.elbow); // sibling preserved
  });
  it("does not mutate base", () => {
    merge(DEFAULT, { headTurn: 9 });
    expect(DEFAULT.headTurn).toBe(0);
  });
});
