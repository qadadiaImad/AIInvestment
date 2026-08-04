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
