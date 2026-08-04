import { describe, it, expect } from "vitest";
import { merge, tween } from "./merge";
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

describe("tween", () => {
  const a = DEFAULT;
  const b = merge(DEFAULT, { headTurn: 10, mouth: "open", armR: { shoulder: 250 } });
  it("lerps numeric fields", () => {
    expect(tween(a, b, 0.5).headTurn).toBeCloseTo(5);
    expect(tween(a, b, 0.5).armR.shoulder).toBeCloseTo((DEFAULT.armR.shoulder + 250) / 2);
  });
  it("switches enum fields at the midpoint", () => {
    expect(tween(a, b, 0.49).mouth).toBe("flat");
    expect(tween(a, b, 0.5).mouth).toBe("open");
  });
  it("t=0 is a, t=1 is b", () => {
    expect(tween(a, b, 0).headTurn).toBe(0);
    expect(tween(a, b, 1).headTurn).toBe(10);
  });
});
