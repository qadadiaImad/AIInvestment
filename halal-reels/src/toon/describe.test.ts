import { describe as d, it, expect } from "vitest";
import { describe as desc } from "./describe";
import { DEFAULT } from "./defaults";
import { merge } from "./merge";

d("describe", () => {
  it("names the deadpan neutral pose", () => {
    const s = desc(DEFAULT);
    expect(s).toContain("analyst");
    expect(s).toContain("brows flat");
    expect(s).toContain("mouth flat");
  });
  it("reflects expression + head turn changes", () => {
    const s = desc(merge(DEFAULT, { mouth: "smile", headTurn: 12, eyes: "wide" }));
    expect(s).toContain("mouth smile");
    expect(s).toContain("eyes wide");
    expect(s).toContain("head turned right");
  });
  it("is deterministic", () => {
    expect(desc(DEFAULT)).toBe(desc(merge(DEFAULT)));
  });
});
