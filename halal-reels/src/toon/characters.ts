/**
 * The cast — distinct rig "skins" (palette + hair + glasses), inspired by the
 * minimalist flat persona sets (man/woman/older/nerd/etc.). One rig, many
 * characters: swap the skin and every pose/expression comes along for free.
 */
import { Skin } from "./types";

export const CHARACTERS: Record<string, Skin> = {
  // the original deadpan analyst — bald, teal
  analyst: { skinFill: "#F3C9A2", outline: "#1A1A1A", shirtFill: "#37B6A6" },
  // seasoned exec — grey side-part, navy
  exec: { skinFill: "#E9BE95", outline: "#1A1A1A", shirtFill: "#37507A", hair: "sidepart", hairColor: "#8A8F98" },
  // quant nerd — mop + round glasses, brick red
  quant: { skinFill: "#F1C7A0", outline: "#1A1A1A", shirtFill: "#C0492E", hair: "mop", hairColor: "#3A2A1A", glasses: "round" },
  // news anchor — top bun, plum
  anchor: { skinFill: "#EFC49E", outline: "#1A1A1A", shirtFill: "#8E3B6B", hair: "bun", hairColor: "#4A2E1C" },
  // fresh intern — buzz cut, amber
  intern: { skinFill: "#F4CBA4", outline: "#1A1A1A", shirtFill: "#E0A23B", hair: "buzz", hairColor: "#2A1E12" },
  // floor trader — short hair + rect specs, green
  trader: { skinFill: "#E7B98D", outline: "#1A1A1A", shirtFill: "#2F8F5B", hair: "short", hairColor: "#1E1712", glasses: "rect" },
};
