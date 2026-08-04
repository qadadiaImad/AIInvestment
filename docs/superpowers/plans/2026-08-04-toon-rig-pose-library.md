# Toon Character Rig + Pose Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a parametric SVG character rig plus a generated, validated pose/expression library for our own flat-2D deadpan "analyst" mascot, feeding Remotion animation.

**Architecture:** A pure `Character(params)` SVG component is the single source of truth. Poses/expressions are `Partial<RigParams>` patches merged over a default. Pure `merge`/`tween`/`posed` functions (unit-tested) drive both static composition and frame-to-frame animation. A `PoseSheet` Remotion composition renders contact sheets for visual culling. A Sonnet subagent fans out a larger catalog which is validated against the schema and culled before landing in `catalog.json`.

**Tech Stack:** TypeScript, React, Remotion 4.0.496, Vitest (in-repo test runner), Node. All new files live under `halal-reels/src/toon/`.

## Global Constraints

- Remotion/React/TS only for rig + animation; no new npm dependencies.
- 30fps, 1080×1920 base (matches existing compositions).
- Single character skin: `ANALYST`. Rig must stay skin-parametric (skin passed as a param) but only one skin ships.
- No IK solver — noodle-limb geometry is forward-kinematic angle math only.
- Vector/code only — no AI-generated art in the rig. 100% deterministic rendering.
- Deterministic descriptions — `describe()` maps params → text via templates, no free-text hallucination in the required `desc` field.
- Test files use Vitest, named `*.test.ts`, run with `npm test` (which runs `vitest run`) from `halal-reels/`.
- Every subagent (if dispatched) runs `model: 'sonnet'` per project model policy.

---

## File Structure

- `halal-reels/src/toon/types.ts` — `RigParams`, patch/keyframe types, `DeepPartial`.
- `halal-reels/src/toon/defaults.ts` — `ANALYST` skin + `DEFAULT` neutral rig params.
- `halal-reels/src/toon/merge.ts` — pure `merge()` + `tween()`.
- `halal-reels/src/toon/merge.test.ts` — Vitest for merge/tween.
- `halal-reels/src/toon/animate.ts` — pure `posed()` keyframe helper.
- `halal-reels/src/toon/animate.test.ts` — Vitest for posed.
- `halal-reels/src/toon/describe.ts` — deterministic `describe(params)`.
- `halal-reels/src/toon/describe.test.ts` — Vitest for describe.
- `halal-reels/src/toon/rig.tsx` — `Character(params)` SVG (visual, no unit test).
- `halal-reels/src/toon/poses.ts` — `POSES`, `EXPR` patch libraries with `desc`.
- `halal-reels/src/toon/catalog.json` — generated master catalog.
- `halal-reels/src/toon/PoseSheet.tsx` — Remotion contact-sheet composition.
- `halal-reels/src/toon/gen_catalog.mjs` — validate + merge subagent candidates → `catalog.json`.
- `halal-reels/src/Root.tsx` — register `PoseSheet` composition (modify).

---

### Task 1: Types + defaults + `merge()`

**Files:**
- Create: `halal-reels/src/toon/types.ts`
- Create: `halal-reels/src/toon/defaults.ts`
- Create: `halal-reels/src/toon/merge.ts`
- Test: `halal-reels/src/toon/merge.test.ts`

**Interfaces:**
- Produces: `RigParams`, `Arm`, `Skin`, `Brow`, `Eyes`, `Mouth`, `Prop`, `PosePatch`, `Keyframe`, `DeepPartial<T>` (types.ts); `ANALYST: Skin`, `DEFAULT: RigParams` (defaults.ts); `merge(base: RigParams, ...patches: PosePatch[]): RigParams` (merge.ts).

- [ ] **Step 1: Write `types.ts`**

```ts
export type Brow = "flat" | "raise" | "furrow" | "sad";
export type Eyes = "open" | "blink" | "wide" | "dead" | "sideL" | "sideR";
export type Mouth = "flat" | "open" | "frown" | "smile" | "grimace" | "o";
export type Prop = "none" | "fiddle" | "paper" | "phone" | "pointer";

export interface Arm { shoulder: number; elbow: number; wrist: number } // degrees
export interface Skin { skinFill: string; outline: string; shirtFill: string }

export interface RigParams {
  skin: Skin;
  headTurn: number; // deg, +right
  lean: number;     // deg, +right
  bob: number;      // px vertical
  brows: { l: Brow; r: Brow };
  eyes: Eyes;
  mouth: Mouth;
  sweat: boolean;
  armL: Arm;
  armR: Arm;
  prop: Prop;
}

export type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K];
};
export type PosePatch = DeepPartial<RigParams>;
export interface Keyframe { frame: number; patch: PosePatch }
```

- [ ] **Step 2: Write `defaults.ts`**

```ts
import { RigParams, Skin } from "./types";

export const ANALYST: Skin = { skinFill: "#F3C9A2", outline: "#1A1A1A", shirtFill: "#37B6A6" };

// Neutral, front-facing, arms resting on the desk edge.
export const DEFAULT: RigParams = {
  skin: ANALYST,
  headTurn: 0,
  lean: 0,
  bob: 0,
  brows: { l: "flat", r: "flat" },
  eyes: "open",
  mouth: "flat",
  sweat: false,
  armL: { shoulder: 150, elbow: 40, wrist: 0 },
  armR: { shoulder: 210, elbow: -40, wrist: 0 },
  prop: "none",
};
```

- [ ] **Step 3: Write the failing test `merge.test.ts`**

```ts
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
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd halal-reels && npx vitest run src/toon/merge.test.ts`
Expected: FAIL ("Failed to resolve import './merge'" or merge undefined).

- [ ] **Step 5: Write minimal `merge.ts`**

```ts
import { RigParams, PosePatch } from "./types";

function isObj(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function deep<T>(base: T, patch: unknown): T {
  if (!isObj(patch)) return (patch as T) ?? base;
  const out: Record<string, unknown> = Array.isArray(base) ? [...(base as unknown[])] : { ...(base as object) };
  for (const k of Object.keys(patch)) {
    const bv = (base as Record<string, unknown>)?.[k];
    const pv = (patch as Record<string, unknown>)[k];
    out[k] = isObj(bv) && isObj(pv) ? deep(bv, pv) : pv;
  }
  return out as T;
}

export function merge(base: RigParams, ...patches: PosePatch[]): RigParams {
  return patches.reduce<RigParams>((acc, p) => deep(acc, p), deep(base, {}));
}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd halal-reels && npx vitest run src/toon/merge.test.ts`
Expected: PASS (4 tests).

- [ ] **Step 7: Commit**

```bash
git add halal-reels/src/toon/types.ts halal-reels/src/toon/defaults.ts halal-reels/src/toon/merge.ts halal-reels/src/toon/merge.test.ts
git commit -m "feat(toon): RigParams types, ANALYST defaults, pure merge()"
```

---

### Task 2: `tween()` between two RigParams

**Files:**
- Modify: `halal-reels/src/toon/merge.ts`
- Test: `halal-reels/src/toon/merge.test.ts` (append)

**Interfaces:**
- Consumes: `RigParams` (types.ts), `DEFAULT` (defaults.ts).
- Produces: `tween(a: RigParams, b: RigParams, t: number): RigParams` — numeric fields (`headTurn`, `lean`, `bob`, each arm `shoulder`/`elbow`/`wrist`) linearly interpolate; enum/boolean/skin fields switch to `b` at `t >= 0.5`.

- [ ] **Step 1: Append failing tests to `merge.test.ts`**

```ts
import { tween } from "./merge";

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd halal-reels && npx vitest run src/toon/merge.test.ts`
Expected: FAIL ("tween is not a function").

- [ ] **Step 3: Add `tween()` to `merge.ts`**

```ts
const lerp = (x: number, y: number, t: number) => x + (y - x) * t;

export function tween(a: RigParams, b: RigParams, t: number): RigParams {
  const pick = <T>(x: T, y: T) => (t >= 0.5 ? y : x);
  const arm = (x: RigParams["armL"], y: RigParams["armL"]) => ({
    shoulder: lerp(x.shoulder, y.shoulder, t),
    elbow: lerp(x.elbow, y.elbow, t),
    wrist: lerp(x.wrist, y.wrist, t),
  });
  return {
    skin: pick(a.skin, b.skin),
    headTurn: lerp(a.headTurn, b.headTurn, t),
    lean: lerp(a.lean, b.lean, t),
    bob: lerp(a.bob, b.bob, t),
    brows: { l: pick(a.brows.l, b.brows.l), r: pick(a.brows.r, b.brows.r) },
    eyes: pick(a.eyes, b.eyes),
    mouth: pick(a.mouth, b.mouth),
    sweat: pick(a.sweat, b.sweat),
    armL: arm(a.armL, b.armL),
    armR: arm(a.armR, b.armR),
    prop: pick(a.prop, b.prop),
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd halal-reels && npx vitest run src/toon/merge.test.ts`
Expected: PASS (all merge + tween tests).

- [ ] **Step 5: Commit**

```bash
git add halal-reels/src/toon/merge.ts halal-reels/src/toon/merge.test.ts
git commit -m "feat(toon): tween() interpolates rig params for animation"
```

---

### Task 3: `posed()` keyframe helper

**Files:**
- Create: `halal-reels/src/toon/animate.ts`
- Test: `halal-reels/src/toon/animate.test.ts`

**Interfaces:**
- Consumes: `merge`, `tween` (merge.ts), `RigParams`, `Keyframe` (types.ts), `DEFAULT` (defaults.ts).
- Produces: `posed(frame: number, base: RigParams, keyframes: Keyframe[]): RigParams` — resolves each keyframe patch over `base` once, holds before the first / after the last keyframe, and linearly tweens between the two surrounding keyframes by frame.

- [ ] **Step 1: Write failing `animate.test.ts`**

```ts
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd halal-reels && npx vitest run src/toon/animate.test.ts`
Expected: FAIL ("Failed to resolve import './animate'").

- [ ] **Step 3: Write `animate.ts`**

```ts
import { RigParams, Keyframe } from "./types";
import { merge, tween } from "./merge";

export function posed(frame: number, base: RigParams, keyframes: Keyframe[]): RigParams {
  if (keyframes.length === 0) return merge(base);
  const kf = [...keyframes].sort((a, b) => a.frame - b.frame);
  const resolved = kf.map((k) => ({ frame: k.frame, params: merge(base, k.patch) }));
  if (frame <= resolved[0].frame) return resolved[0].params;
  if (frame >= resolved[resolved.length - 1].frame) return resolved[resolved.length - 1].params;
  let i = 0;
  while (i < resolved.length - 1 && resolved[i + 1].frame <= frame) i++;
  const a = resolved[i];
  const b = resolved[i + 1];
  const t = (frame - a.frame) / (b.frame - a.frame);
  return tween(a.params, b.params, t);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd halal-reels && npx vitest run src/toon/animate.test.ts`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add halal-reels/src/toon/animate.ts halal-reels/src/toon/animate.test.ts
git commit -m "feat(toon): posed() keyframe tweening helper"
```

---

### Task 4: Deterministic `describe()`

**Files:**
- Create: `halal-reels/src/toon/describe.ts`
- Test: `halal-reels/src/toon/describe.test.ts`

**Interfaces:**
- Consumes: `RigParams` (types.ts), `DEFAULT` (defaults.ts), `merge` (merge.ts).
- Produces: `describe(p: RigParams): string` — deterministic sentence built from params.

- [ ] **Step 1: Write failing `describe.test.ts`**

```ts
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd halal-reels && npx vitest run src/toon/describe.test.ts`
Expected: FAIL ("Failed to resolve import './describe'").

- [ ] **Step 3: Write `describe.ts`**

```ts
import { RigParams } from "./types";

export function describe(p: RigParams): string {
  const head =
    p.headTurn > 4 ? "head turned right" : p.headTurn < -4 ? "head turned left" : "head straight";
  const lean = p.lean > 4 ? "leaning right" : p.lean < -4 ? "leaning left" : "upright";
  const armWord = (name: string, a: RigParams["armL"]) =>
    `${name} arm ${a.elbow < -15 ? "raised" : a.elbow > 25 ? "lowered" : "mid"}`;
  const parts = [
    "deadpan analyst",
    lean,
    head,
    `brows ${p.brows.l}${p.brows.l === p.brows.r ? "" : "/" + p.brows.r}`,
    `eyes ${p.eyes}`,
    `mouth ${p.mouth}`,
    armWord("left", p.armL),
    armWord("right", p.armR),
    p.prop !== "none" ? `holding ${p.prop}` : "",
    p.sweat ? "sweating" : "",
  ];
  return parts.filter(Boolean).join(", ") + ".";
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd halal-reels && npx vitest run src/toon/describe.test.ts`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add halal-reels/src/toon/describe.ts halal-reels/src/toon/describe.test.ts
git commit -m "feat(toon): deterministic describe() for pose metadata"
```

---

### Task 5: `Character()` SVG rig (visual)

**Files:**
- Create: `halal-reels/src/toon/rig.tsx`

**Interfaces:**
- Consumes: `RigParams`, `Arm` (types.ts).
- Produces: `Character: React.FC<{ p: RigParams }>` rendering an SVG `<g>` in a 540-wide local coordinate space (head centered near x=270, y=200; shoulders near y=360), matching `QuarterlyReport`'s `Guy` scale.

Arms are forward-kinematic: from a fixed shoulder point, the elbow is `L1` away at `shoulder`° (measured from downward vertical, clockwise+), the hand is `L2` further at `shoulder+elbow`°. No unit test — validated by the contact sheet in Task 6.

- [ ] **Step 1: Write `rig.tsx`**

```tsx
import React from "react";
import { RigParams, Arm } from "./types";

const L1 = 70; // upper arm
const L2 = 62; // forearm
const RAD = Math.PI / 180;

function armGeom(ox: number, oy: number, a: Arm) {
  const ex = ox + L1 * Math.sin(a.shoulder * RAD);
  const ey = oy + L1 * Math.cos(a.shoulder * RAD);
  const hx = ex + L2 * Math.sin((a.shoulder + a.elbow) * RAD);
  const hy = ey + L2 * Math.cos((a.shoulder + a.elbow) * RAD);
  return { ex, ey, hx, hy };
}

const Brow: React.FC<{ x: number; kind: string; o: string }> = ({ x, kind, o }) => {
  const y = 150;
  const d =
    kind === "raise" ? `M${x - 20} ${y - 8} q20 -10 40 0`
      : kind === "furrow" ? `M${x - 20} ${y + 4} l40 -8`
      : kind === "sad" ? `M${x - 20} ${y - 6} l40 8`
      : `M${x - 20} ${y} l40 0`;
  return <path d={d} stroke={o} strokeWidth={8} fill="none" strokeLinecap="round" />;
};

const Eyes: React.FC<{ kind: string; o: string }> = ({ kind, o }) => {
  if (kind === "blink" || kind === "dead")
    return (
      <>
        <line x1={222} y1={196} x2={252} y2={196} stroke={o} strokeWidth={8} strokeLinecap="round" />
        <line x1={288} y1={196} x2={318} y2={196} stroke={o} strokeWidth={8} strokeLinecap="round" />
      </>
    );
  const r = kind === "wide" ? 19 : 14;
  const dx = kind === "sideL" ? -6 : kind === "sideR" ? 6 : 0;
  return (
    <>
      <circle cx={237 + dx} cy={196} r={r} fill={o} />
      <circle cx={303 + dx} cy={196} r={r} fill={o} />
    </>
  );
};

const Mouth: React.FC<{ kind: string; o: string }> = ({ kind, o }) => {
  switch (kind) {
    case "open": return <ellipse cx={270} cy={252} rx={20} ry={15} fill={o} />;
    case "o": return <circle cx={270} cy={252} r={13} fill={o} />;
    case "smile": return <path d="M244 248 q26 26 52 0" stroke={o} strokeWidth={7} fill="none" strokeLinecap="round" />;
    case "frown": return <path d="M244 258 q26 -26 52 0" stroke={o} strokeWidth={7} fill="none" strokeLinecap="round" />;
    case "grimace": return <rect x={244} y={246} width={52} height={14} rx={4} fill="none" stroke={o} strokeWidth={6} />;
    default: return <line x1={242} y1={252} x2={298} y2={252} stroke={o} strokeWidth={7} strokeLinecap="round" />;
  }
};

const Prop: React.FC<{ kind: string; x: number; y: number; o: string }> = ({ kind, x, y, o }) => {
  if (kind === "paper") return <rect x={x - 22} y={y - 28} width={44} height={56} rx={3} fill="#FFF6E9" stroke={o} strokeWidth={5} />;
  if (kind === "phone") return <rect x={x - 12} y={y - 24} width={24} height={48} rx={5} fill="#2B2F36" stroke={o} strokeWidth={5} />;
  if (kind === "pointer") return <line x1={x} y1={y} x2={x + 60} y2={y - 40} stroke={o} strokeWidth={7} strokeLinecap="round" />;
  if (kind === "fiddle") return <ellipse cx={x} cy={y} rx={16} ry={26} fill="#B5651D" stroke={o} strokeWidth={5} />;
  return null;
};

export const Character: React.FC<{ p: RigParams }> = ({ p }) => {
  const o = p.skin.outline;
  const L = armGeom(215, 360, p.armL);
  const R = armGeom(325, 360, p.armR);
  const propArm = p.armR; // prop rides the right hand
  void propArm;
  return (
    <g transform={`translate(0 ${p.bob}) rotate(${p.lean} 270 400)`}>
      <line x1={270} y1={300} x2={270} y2={360} stroke={o} strokeWidth={9} />
      <path d="M150 520 C150 400 205 350 270 350 C335 350 390 400 390 520 Z" fill={p.skin.shirtFill} stroke={o} strokeWidth={9} />
      {/* arms */}
      <path d={`M215 360 L${L.ex} ${L.ey} L${L.hx} ${L.hy}`} fill="none" stroke={o} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round" />
      <path d={`M325 360 L${R.ex} ${R.ey} L${R.hx} ${R.hy}`} fill="none" stroke={o} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={L.hx} cy={L.hy} r={13} fill={p.skin.skinFill} stroke={o} strokeWidth={8} />
      <circle cx={R.hx} cy={R.hy} r={13} fill={p.skin.skinFill} stroke={o} strokeWidth={8} />
      <Prop kind={p.prop} x={R.hx} y={R.hy} o={o} />
      {/* head */}
      <g transform={`translate(${p.headTurn} 0)`}>
        <circle cx={270} cy={200} r={115} fill={p.skin.skinFill} stroke={o} strokeWidth={10} />
        <Brow x={232} kind={p.brows.l} o={o} />
        <Brow x={308} kind={p.brows.r} o={o} />
        <Eyes kind={p.eyes} o={o} />
        <Mouth kind={p.mouth} o={o} />
        {p.sweat && <path d="M355 175 q10 20 0 34 q-10 -14 0 -34" fill="#8FD3FF" stroke={o} strokeWidth={3} />}
      </g>
    </g>
  );
};
```

- [ ] **Step 2: Typecheck the rig**

Run: `cd halal-reels && npx tsc --noEmit`
Expected: no errors from `src/toon/`.

- [ ] **Step 3: Commit**

```bash
git add halal-reels/src/toon/rig.tsx
git commit -m "feat(toon): parametric Character() SVG rig (analyst skin)"
```

---

### Task 6: Hero poses + expressions + `PoseSheet` contact sheet

**Files:**
- Create: `halal-reels/src/toon/poses.ts`
- Create: `halal-reels/src/toon/PoseSheet.tsx`
- Modify: `halal-reels/src/Root.tsx`

**Interfaces:**
- Consumes: `PosePatch` (types.ts), `Character` (rig.tsx), `DEFAULT` (defaults.ts), `merge` (merge.ts), `describe` (describe.ts).
- Produces: `POSES: Record<string, { patch: PosePatch; desc: string }>`, `EXPR: Record<string, { patch: PosePatch; desc: string }>` (poses.ts); `PoseSheet: React.FC` composition registered as id `"ToonPoseSheet"`.

- [ ] **Step 1: Write `poses.ts` (10 hero poses + 6 expressions)**

```ts
import { PosePatch } from "./types";

type Entry = { patch: PosePatch; desc: string };
const P = (patch: PosePatch, desc: string): Entry => ({ patch, desc });

export const POSES: Record<string, Entry> = {
  rest: P({ armL: { shoulder: 150, elbow: 40 }, armR: { shoulder: 210, elbow: -40 } }, "hands resting on desk"),
  point_left: P({ armR: { shoulder: 300, elbow: 10, wrist: 0 } }, "right arm pointing left"),
  point_up: P({ armR: { shoulder: 350, elbow: -10 } }, "right arm pointing up"),
  shrug: P({ armL: { shoulder: 120, elbow: -70 }, armR: { shoulder: 240, elbow: 70 } }, "both arms shrugging"),
  facepalm: P({ armR: { shoulder: 15, elbow: 150 }, headTurn: -3 }, "right hand to face"),
  present: P({ armR: { shoulder: 250, elbow: 30 }, armL: { shoulder: 110, elbow: -30 } }, "presenting to the side"),
  type: P({ armL: { shoulder: 165, elbow: 35 }, armR: { shoulder: 195, elbow: -35 } }, "typing on keyboard"),
  panic: P({ armL: { shoulder: 100, elbow: -90 }, armR: { shoulder: 260, elbow: 90 }, lean: -4 }, "arms flailing in panic"),
  lean_back: P({ lean: 8, armR: { shoulder: 210, elbow: -60 } }, "leaning back relaxed"),
  hold_paper: P({ prop: "paper", armR: { shoulder: 235, elbow: 20 } }, "holding a paper"),
};

export const EXPR: Record<string, Entry> = {
  deadpan: P({ brows: { l: "flat", r: "flat" }, eyes: "open", mouth: "flat" }, "deadpan"),
  smug: P({ brows: { l: "raise", r: "flat" }, eyes: "open", mouth: "smile" }, "smug"),
  dead_eyed: P({ eyes: "dead", mouth: "flat" }, "dead-eyed"),
  shocked: P({ brows: { l: "raise", r: "raise" }, eyes: "wide", mouth: "o" }, "shocked"),
  annoyed: P({ brows: { l: "furrow", r: "furrow" }, eyes: "open", mouth: "frown" }, "annoyed"),
  crying: P({ brows: { l: "sad", r: "sad" }, eyes: "dead", mouth: "frown", sweat: true }, "crying"),
};
```

- [ ] **Step 2: Write `PoseSheet.tsx` (grid of every pose×deadpan + neutral×every expr)**

```tsx
import React from "react";
import { AbsoluteFill } from "remotion";
import { Character } from "./rig";
import { DEFAULT } from "./defaults";
import { merge } from "./merge";
import { POSES, EXPR } from "./poses";

const CELL = 300;
const COLS = 6;

export const PoseSheet: React.FC = () => {
  const items = [
    ...Object.entries(POSES).map(([k, v]) => ({ label: k, params: merge(DEFAULT, v.patch, EXPR.deadpan.patch) })),
    ...Object.entries(EXPR).map(([k, v]) => ({ label: k, params: merge(DEFAULT, v.patch) })),
  ];
  const rows = Math.ceil(items.length / COLS);
  return (
    <AbsoluteFill style={{ background: "#8A97A6" }}>
      <svg width={COLS * CELL} height={rows * CELL} viewBox={`0 0 ${COLS * CELL} ${rows * CELL}`}>
        {items.map((it, i) => {
          const x = (i % COLS) * CELL;
          const y = Math.floor(i / COLS) * CELL;
          return (
            <g key={it.label} transform={`translate(${x} ${y})`}>
              <rect x={2} y={2} width={CELL - 4} height={CELL - 4} fill="#B7A6AE" stroke="#1A1A1A" strokeWidth={2} />
              <g transform={`translate(30 -80) scale(0.45)`}>
                <Character p={it.params} />
              </g>
              <text x={CELL / 2} y={CELL - 14} textAnchor="middle" fontFamily="monospace" fontSize={20} fill="#141414">
                {it.label}
              </text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
```

- [ ] **Step 3: Register `PoseSheet` in `Root.tsx`**

Add import near the other imports:
```tsx
import { PoseSheet } from "./toon/PoseSheet";
```
Add composition inside the `<>` fragment (16 items, 6 cols → 3 rows → 900px tall; use a square-ish canvas):
```tsx
<Composition id="ToonPoseSheet" component={PoseSheet} durationInFrames={1} fps={FPS} width={1800} height={900} />
```

- [ ] **Step 4: Render the contact sheet**

Run: `cd halal-reels && npx remotion still ToonPoseSheet out/toon_posesheet.png --frame=0`
Expected: `out/toon_posesheet.png` written.

- [ ] **Step 5: Verify at full resolution and cull**

Open `out/toon_posesheet.png`. For each cell confirm: limbs connect at shoulders/hands, no arm crosses through the head unintentionally, expression reads clearly. For any broken pose, adjust its angles in `poses.ts` and re-render. Do NOT judge on a thumbnail — inspect the full-size PNG.

- [ ] **Step 6: Commit**

```bash
git add halal-reels/src/toon/poses.ts halal-reels/src/toon/PoseSheet.tsx halal-reels/src/Root.tsx
git commit -m "feat(toon): 10 hero poses + 6 expressions + PoseSheet contact sheet"
```

---

### Task 7: Generate + validate the catalog

**Files:**
- Create: `halal-reels/src/toon/catalog.json`
- Create: `halal-reels/src/toon/gen_catalog.mjs`
- Modify: `halal-reels/src/toon/PoseSheet.tsx` (add a catalog-driven mode)

**Interfaces:**
- Consumes: `POSES`, `EXPR` (poses.ts), `RigParams` schema (types.ts), `describe` (describe.ts).
- Produces: `catalog.json` = `{ id: string; params: PosePatch; desc: string; tags: string[] }[]`.

- [ ] **Step 1: Dispatch a Sonnet subagent to propose candidate poses**

Dispatch one subagent (Agent tool, `subagent_type: general-purpose`, `model: 'sonnet'`) with this prompt:

> You are authoring pose patches for a flat-2D SVG character rig. The rig params are: `headTurn`(deg ±, +right), `lean`(deg ±), `brows.l/.r` ∈ {flat,raise,furrow,sad}, `eyes` ∈ {open,blink,wide,dead,sideL,sideR}, `mouth` ∈ {flat,open,frown,smile,grimace,o}, `sweat`(bool), `armL/armR` = {shoulder,elbow,wrist} in degrees where shoulder is measured from downward-vertical clockwise (150–210 ≈ resting down, ~250–300 points sideways, ~350 points up, negative elbow raises the forearm), `prop` ∈ {none,fiddle,paper,phone,pointer}. Existing hero poses (do NOT duplicate): rest, point_left, point_up, shrug, facepalm, present, type, panic, lean_back, hold_paper. Produce 40 NEW distinct body-pose patches as a JSON array of `{ "id": "...", "patch": { ... }, "tags": [ ... ] }`. Keep arms anatomically plausible (elbow within ±150). Output ONLY the JSON array.

Save the returned JSON to `halal-reels/src/toon/_candidates.json`.

- [ ] **Step 2: Write `gen_catalog.mjs` (validate + attach desc + merge)**

```js
import fs from "node:fs";
import path from "node:path";
const dir = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const ENUMS = {
  brow: ["flat", "raise", "furrow", "sad"],
  eyes: ["open", "blink", "wide", "dead", "sideL", "sideR"],
  mouth: ["flat", "open", "frown", "smile", "grimace", "o"],
  prop: ["none", "fiddle", "paper", "phone", "pointer"],
};
const okArm = (a) => !a || (["shoulder", "elbow", "wrist"].every((k) => a[k] === undefined || (typeof a[k] === "number" && Math.abs(a[k]) <= 360)) && (a.elbow === undefined || Math.abs(a.elbow) <= 150));
function valid(p) {
  if (p.eyes && !ENUMS.eyes.includes(p.eyes)) return false;
  if (p.mouth && !ENUMS.mouth.includes(p.mouth)) return false;
  if (p.prop && !ENUMS.prop.includes(p.prop)) return false;
  if (p.brows && [p.brows.l, p.brows.r].some((b) => b && !ENUMS.brow.includes(b))) return false;
  return okArm(p.armL) && okArm(p.armR);
}
const cands = JSON.parse(fs.readFileSync(path.join(dir, "_candidates.json"), "utf8"));
const seen = new Set();
const out = [];
for (const c of cands) {
  if (!c.id || seen.has(c.id) || !valid(c.patch || {})) continue;
  seen.add(c.id);
  out.push({ id: c.id, params: c.patch, desc: "", tags: c.tags || [] });
}
fs.writeFileSync(path.join(dir, "catalog.json"), JSON.stringify(out, null, 2));
console.log(`catalog.json: ${out.length} valid entries (of ${cands.length} candidates)`);
```

- [ ] **Step 3: Run the validator**

Run: `cd halal-reels && node src/toon/gen_catalog.mjs`
Expected: prints `catalog.json: N valid entries` with N close to 40; `catalog.json` written.

- [ ] **Step 4: Add a catalog mode to `PoseSheet.tsx`**

Add below the existing items build, gated by a prop so the hero sheet still works:
```tsx
import catalog from "./catalog.json";
// inside PoseSheet, replace `const items = [...]` with:
export const PoseSheet: React.FC<{ fromCatalog?: boolean }> = ({ fromCatalog }) => {
  const items = fromCatalog
    ? (catalog as { id: string; params: any }[]).map((c) => ({ label: c.id, params: merge(DEFAULT, c.params, EXPR.deadpan.patch) }))
    : [
        ...Object.entries(POSES).map(([k, v]) => ({ label: k, params: merge(DEFAULT, v.patch, EXPR.deadpan.patch) })),
        ...Object.entries(EXPR).map(([k, v]) => ({ label: k, params: merge(DEFAULT, v.patch) })),
      ];
  // ...unchanged grid rendering, but compute rows from items.length...
```
Add a second registration in `Root.tsx`:
```tsx
<Composition id="ToonCatalogSheet" component={PoseSheet} durationInFrames={1} fps={FPS} width={1800} height={2400} defaultProps={{ fromCatalog: true }} />
```

- [ ] **Step 5: Render + cull the catalog sheet**

Run: `cd halal-reels && npx remotion still ToonCatalogSheet out/toon_catalog.png --frame=0`
Open `out/toon_catalog.png` at full size. Delete any entry from `catalog.json` whose limbs break or read wrong. Re-render until every remaining cell is clean.

- [ ] **Step 6: Backfill deterministic descriptions**

Run this Node one-liner to fill each `desc` via the rig's `describe()` semantics (mirror of describe.ts, so no import cycle):
```bash
cd halal-reels && node -e "
const fs=require('fs');const {DEFAULT}=require('./src/toon/defaults.ts');" 2>/dev/null || true
```
If direct import of TS fails, instead add a tiny script `gen_desc.mjs` that reimplements the `describe()` template over `merge(DEFAULT, params)` and writes `desc` for each entry. (describe.ts is the source of truth for wording — copy its template exactly.)

- [ ] **Step 7: Commit**

```bash
git add halal-reels/src/toon/catalog.json halal-reels/src/toon/gen_catalog.mjs halal-reels/src/toon/PoseSheet.tsx halal-reels/src/Root.tsx
git commit -m "feat(toon): generated + validated pose catalog (subagent-authored, culled)"
```

---

### Task 8: Refactor `QuarterlyReport` to consume the rig

**Files:**
- Modify: `halal-reels/src/QuarterlyReport.tsx`

**Interfaces:**
- Consumes: `Character` (rig.tsx), `DEFAULT` (defaults.ts), `POSES`, `EXPR` (poses.ts), `posed` (animate.ts).

- [ ] **Step 1: Replace the inline `Guy` with the rig in the office scene**

In `OfficeScene`, replace the `<Guy .../>` usage with:
```tsx
import { Character } from "./toon/rig";
import { DEFAULT } from "./toon/defaults";
import { POSES, EXPR } from "./toon/poses";
import { merge } from "./toon/merge";
// mouth-flap: swap the merged mouth between flat/open while talking
const talking = inWindows(f, [[8, 91], [100, 246]]) && flap(f);
const params = merge(DEFAULT, POSES.rest.patch, EXPR.deadpan.patch, { mouth: talking ? "open" : "flat", bob });
// ...
<g transform="translate(120 640)"><Character p={params} /></g>
```
Delete the old `Guy` component.

- [ ] **Step 2: Re-render and confirm parity**

Run: `cd halal-reels && npx remotion still QuarterlyReport out/qr_scene_rig.png --frame=200`
Open the PNG: the analyst should match the previous look (deadpan, teal shirt, at the desk). Adjust `POSES.rest` angles if the arms sit differently.

- [ ] **Step 3: Full render + commit**

```bash
cd halal-reels && npx remotion render QuarterlyReport out/quarterly_report.mp4
git add halal-reels/src/QuarterlyReport.tsx
git commit -m "refactor(toon): QuarterlyReport consumes the shared rig"
```

---

## Self-Review

**Spec coverage:**
- Rig (`Character`) → Task 5. ✓
- Types → Task 1. ✓
- Library `POSES`/`EXPR` → Task 6. ✓
- Catalog → Task 7. ✓
- Generator (Sonnet subagent) → Task 7 Step 1. ✓
- Contact sheet → Task 6 (PoseSheet) + Task 7 (catalog mode). ✓
- Animation helper `posed()` → Task 3. ✓
- Merge/tween logic → Tasks 1–2. ✓
- Deterministic descriptions → Task 4 + Task 7 Step 6. ✓
- TDD (Vitest) → Tasks 1–4. ✓
- Visual cull gate → Task 6 Step 5, Task 7 Step 5. ✓
- Single ANALYST skin, skin-parametric → Task 1 defaults + rig. ✓
- QuarterlyReport refactor → Task 8. ✓

**Type consistency:** `RigParams`, `Arm`, `PosePatch`, `Keyframe` defined in Task 1 and used consistently in Tasks 2–8. `merge`/`tween`/`posed`/`describe`/`Character` signatures match across producer and consumer tasks.

**Placeholder note:** Task 7 Step 6 offers a fallback if TS import fails — the concrete action (a `gen_desc.mjs` mirroring `describe.ts`) is specified; keep `describe.ts` as the wording source of truth.
