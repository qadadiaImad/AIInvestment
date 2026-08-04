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
