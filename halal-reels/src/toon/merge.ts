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
