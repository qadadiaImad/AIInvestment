// Fixture for the ValueQuizReel — "5-Second Value Test" (v3, 6-round hero edition).
// Data-driven refresh: price = latest close from web/public/data/prices/<SYM>.json
// (as of 2026-07-31), modelValue = fundamental_value from data/fundamental/<SYM>.json
// (retrieved 2026-08-02). Multiples = max(price,model)/min(price,model), rounded to 1dp.
// Snapshot copied here (not a live retrieval at render time); regenerate when the
// database refreshes. Heroes are Grok-generated tech-noir art (no logos) in
// public/quiz/<hero>.jpg, shown full-bleed behind each round with a dark scrim.

export type Verdict = "UNDER" | "OVER";

export type QuizRound = {
  ticker: string;
  name: string; // full company name — shown as the headline (never the ticker)
  aka?: string; // secondary product/brand name shown next to the ticker tag
  price: number;
  modelValue: number;
  verdict: Verdict;
  multipleLabel: string; // e.g. "1.9x"
  why: string;
  hero: string; // public/quiz/<hero>.jpg
};

export const QUIZ_DATE = "2026-08-02";

export const QUIZ_ROUNDS: QuizRound[] = [
  {
    ticker: "NVDA",
    name: "Nvidia",
    price: 200.75,
    modelValue: 372.14,
    verdict: "UNDER",
    multipleLabel: "1.9x",
    why: "Everyone screams 'AI bubble' — a model says the business is worth nearly 2x the price.",
    hero: "nvidia.jpg",
  },
  {
    ticker: "META",
    name: "Meta Platforms",
    price: 556.71,
    modelValue: 830.19,
    verdict: "UNDER",
    multipleLabel: "1.5x",
    why: "The ad giant everyone calls maxed-out — a model pegs it ~1.5x above the price.",
    hero: "meta.jpg",
  },
  {
    ticker: "GOOGL",
    name: "Alphabet",
    aka: "Google",
    price: 356.13,
    modelValue: 246.93,
    verdict: "OVER",
    multipleLabel: "1.4x",
    why: "The search king everyone loves — priced ~1.4x above a model's read.",
    hero: "googl.jpg",
  },
  {
    ticker: "AMD",
    name: "Advanced Micro Devices",
    price: 476.15,
    modelValue: 245.59,
    verdict: "OVER",
    multipleLabel: "1.9x",
    why: "The hottest AI-chip name, priced near 2x what a model says it's worth.",
    hero: "amd.jpg",
  },
  {
    ticker: "ADBE",
    name: "Adobe",
    price: 250.41,
    modelValue: 585.12,
    verdict: "UNDER",
    multipleLabel: "2.3x",
    why: "'AI will kill Adobe' — a model says the business is worth ~2.3x the price.",
    hero: "adobe.jpg",
  },
  {
    ticker: "INTC",
    name: "Intel",
    price: 90.20,
    modelValue: 31.21,
    verdict: "OVER",
    multipleLabel: "2.9x",
    why: "The fallen giant everyone's buying back — still priced near 3x a model's value.",
    hero: "intel.jpg",
  },
];

export const QUIZ_RAILS = "A model's read, not a call · Educational — not financial advice.";
