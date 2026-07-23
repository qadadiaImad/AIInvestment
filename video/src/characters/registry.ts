// Character layer — reads the EXISTING character canon as the single source of
// truth. Nothing here redefines a name, palette, silhouette, or voice; this file
// only imports and re-exposes what already exists in ../../../remotion/src/characters.
// Per the Phase-1 recon: Maya is out of scope for this project (excluded on request).
import { ChipRig } from "../../../remotion/src/characters/chipRig";
import { WattRig } from "../../../remotion/src/characters/wattRig";
import { QubitRig } from "../../../remotion/src/characters/qubitRig";
import { CapRig } from "../../../remotion/src/characters/capRig";
import { NovaRig } from "../../../remotion/src/characters/novaRig";
import { CloudyRig } from "../../../remotion/src/characters/cloudyRig";
import { CHARACTERS as CHARACTER_META } from "../../../remotion/src/characters/family";

export const RIGS = {
  chip: ChipRig,
  watt: WattRig,
  qubit: QubitRig,
  cap: CapRig,
  nova: NovaRig,
  cloudy: CloudyRig,
} as const;

export type CharKey = keyof typeof RIGS;

// Karim is a persona (course/persona/*), not an SVG rig — no component to reuse
// here yet. He participates in this project via voice (public/audio) and the
// existing static portrait, composited directly in compositions that need him.
export const KARIM_KEY = "karim" as const;

export const CHARACTERS = CHARACTER_META;
