import { RigParams, PosePatch } from "./types";

function isObj(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function deep<T>(base: T, patch: unknown): T {
  if (!isObj(patch)) return (patch as T) ?? base;
  const out: Record<string, unknown> = (Array.isArray(base) ? [...(base as unknown[])] : { ...(base as object) }) as Record<string, unknown>;
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
