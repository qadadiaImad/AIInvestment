import { describe, it, expect } from "vitest";
import { posed } from "./animate";
import { DEFAULT } from "./defaults";
import { Keyframe } from "./types";

const kfs: Keyframe[] = [
  { frame: 0, patch: { headTurn: 0 } },
  { frame: 10, patch: { headTurn: 10 } },
];

describe("posed", () => {
  it("holds the first keyframe before it", () => {
    expect(posed(-5, DEFAULT, kfs).headTurn).toBe(0);
  });
  it("holds the last keyframe after it", () => {
    expect(posed(99, DEFAULT, kfs).headTurn).toBe(10);
  });
  it("tweens linearly between surrounding keyframes", () => {
    expect(posed(5, DEFAULT, kfs).headTurn).toBeCloseTo(5);
  });
  it("returns base when no keyframes", () => {
    expect(posed(3, DEFAULT, []).headTurn).toBe(DEFAULT.headTurn);
  });
});
