// Screen data for the three reels — sourced from src/halal.json, a copy of
// web/public/data/halal.json (generated 2026-07-21T13:07:37Z). Re-copy on refresh:
//   cp ../web/public/data/halal.json src/halal.json
import halal from "./halal.json";

type Test = {
  label: string;
  ratio: number | null;
  threshold: number | null;
  margin: number | null;
  status: string;
};
type Standard = { status: string; tests: Test[] };
type Verdict = {
  overall: string;
  standards: Record<string, Standard>;
  purification: { per_share: number | null; status: string };
  inputs_asof: string;
};

const verdicts = (halal as { verdicts: Record<string, Verdict> }).verdicts;

export const DATE = ((halal as { generated_at?: string }).generated_at ?? "").slice(0, 10);

const binding = (v: Verdict, std: string): Test | null => {
  const tests = v.standards[std]?.tests?.filter((t) => typeof t.margin === "number") ?? [];
  if (!tests.length) return null;
  return tests.reduce((a, b) => ((a.margin as number) < (b.margin as number) ? a : b));
};

export const stampRow = (tk: string) => {
  const v = verdicts[tk];
  return (["AAOIFI", "FTSE", "MSCI"] as const).map((s) => ({
    name: s,
    ok: v.standards[s]?.status === "pass",
    ratioPct: Math.round(((binding(v, s)?.ratio ?? 0) as number) * 1000) / 10,
    capPct: Math.round(((binding(v, s)?.threshold ?? 0) as number) * 1000) / 10,
  }));
};

export const WULF = {
  tk: "WULF",
  debtPct: 56.9, // AAOIFI interest-bearing debt / market cap (halal.json)
  capPct: 30,
  miningPct: 38.2, // impermissible revenue share, Q1 2026
  purifyCents: 13, // ~$0.1296/share estimated purification
  stamps: stampRow("WULF"),
  badge: { text: "AAOIFI SCREEN: REVIEW", color: "#E0A23B" },
};

export const ETN = {
  tk: "ETN",
  aaoifiPct: 14.0, // debt / market cap
  aaoifiCap: 30,
  assetsPct: 39.6, // debt / total assets (FTSE & MSCI)
  assetsCap: 33.3,
  stamps: stampRow("ETN"),
  badge: { text: "AAOIFI SCREEN: PASS", color: "#34D399" },
};

export const GEV = {
  tk: "GEV",
  debtDollars: 3.5, // tightest AAOIFI test, per $100 of market cap
  capDollars: 30,
  stamps: stampRow("GEV"),
  badge: { text: "AAOIFI SCREEN: PASS", color: "#34D399" },
};
