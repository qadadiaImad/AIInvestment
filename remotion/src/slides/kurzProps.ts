import {z} from 'zod';
import {richTextSchema} from './slideProps';

// kurzProps.ts — schema for KurzSlide.tsx, the Kurzgesagt-inspired animated
// carousel slide engine. A single discriminated union covers the three
// slide shapes the carousel factory needs: a video-intro title card, a
// per-company performance card, and a plain text/CTA card. One JSON file =
// one slide's full props (see fixtures/carousel_top3/slide{1..6}.json).

const richOrString = () => z.union([z.string(), richTextSchema]);

// Corporate-logo chip, shown on every slide of a company's carousel when set.
// logoSrc is staticFile-relative (e.g. "logos/AMD.svg"); logoLabel is the
// small mono caption beside the mark (usually the ticker).
const logoFields = {
  logoSrc: z.string().optional(),
  logoLabel: z.string().optional(),
};

export const kurzIntroVideoSchema = z.object({
  kind: z.literal('introVideo'),
  ...logoFields,
  footer: z.string().optional(), // per-slide disclaimer override (default: theme NOT_FATWA)
  videoSrc: z.string(), // staticFile-relative, e.g. "intro_kitchen_counter.mp4"
  kick: z.string(),
  title: z.string(),
  sub: z.string(),
  durationInFrames: z.number(),
});

export const kurzCompanySchema = z.object({
  kind: z.literal('company'),
  ...logoFields,
  footer: z.string().optional(),
  ticker: z.string(),
  name: z.string(),
  tagline: z.string(),
  perfPct: z.number(),
  perfLabel: z.string(),
  motif: z.enum(['beams', 'prism', 'stack']),
  pills: z.array(z.object({label: z.string(), value: z.string()})).length(3),
  footnote: z.string().optional(),
  durationInFrames: z.number(),
});

export const kurzTextSchema = z.object({
  kind: z.literal('text'),
  ...logoFields,
  footer: z.string().optional(),
  kick: z.string(),
  title: z.string(),
  body: richOrString(),
  durationInFrames: z.number(),
});

// "What the company sells" — 2-4 segment cards, each a name + one-liner.
export const kurzBusinessSchema = z.object({
  kind: z.literal('business'),
  ...logoFields,
  footer: z.string().optional(),
  kick: z.string(),
  title: z.string(),
  sub: z.string().optional(), // one-line framing under the title
  segments: z.array(z.object({name: z.string(), desc: z.string()})).min(2).max(4),
  footnote: z.string().optional(),
  durationInFrames: z.number(),
});

// Dated headline timeline that explains the current trend. Certainty tags
// follow the repo's fact-vs-rumor rail: FACT (emerald) / REPORTED (amber) /
// EXPECTED (red-ish, unconfirmed).
export const kurzNewsSchema = z.object({
  kind: z.literal('news'),
  ...logoFields,
  footer: z.string().optional(),
  kick: z.string(),
  title: z.string(),
  items: z
    .array(
      z.object({
        date: z.string(), // short display date, e.g. "7/21"
        tag: z.enum(['FACT', 'REPORTED', 'EXPECTED']),
        text: richOrString(),
      }),
    )
    .min(2)
    .max(4),
  footnote: z.string().optional(),
  durationInFrames: z.number(),
});

// Fundamental sheet: model fundamental value vs market price as animated
// compare bars + a grid of the ratios behind it.
export const kurzFundsheetSchema = z.object({
  kind: z.literal('fundsheet'),
  ...logoFields,
  footer: z.string().optional(),
  kick: z.string(),
  title: z.string(),
  fv: z.number(), // modeled fundamental value, $
  price: z.number(), // market price the model was computed against, $
  fvLabel: z.string().optional(), // default "MODEL VALUE"
  priceLabel: z.string().optional(), // default "PRICE"
  verdict: z.string(), // e.g. "OVERVALUED · model cached 7/11"
  stats: z
    .array(z.object({label: z.string(), value: z.string(), tone: z.enum(['emerald', 'amber', 'red', 'muted']).optional()}))
    .min(4)
    .max(6),
  footnote: z.string().optional(),
  durationInFrames: z.number(),
});

export const kurzSlidePropsSchema = z.discriminatedUnion('kind', [
  kurzIntroVideoSchema,
  kurzCompanySchema,
  kurzTextSchema,
  kurzBusinessSchema,
  kurzNewsSchema,
  kurzFundsheetSchema,
]);

export type KurzSlideProps = z.infer<typeof kurzSlidePropsSchema>;
export type KurzIntroVideoProps = z.infer<typeof kurzIntroVideoSchema>;
export type KurzCompanyProps = z.infer<typeof kurzCompanySchema>;
export type KurzTextProps = z.infer<typeof kurzTextSchema>;
export type KurzBusinessProps = z.infer<typeof kurzBusinessSchema>;
export type KurzNewsProps = z.infer<typeof kurzNewsSchema>;
export type KurzFundsheetProps = z.infer<typeof kurzFundsheetSchema>;
