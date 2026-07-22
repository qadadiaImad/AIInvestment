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
  footnote: z.string(),
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

export const kurzSlidePropsSchema = z.discriminatedUnion('kind', [
  kurzIntroVideoSchema,
  kurzCompanySchema,
  kurzTextSchema,
]);

export type KurzSlideProps = z.infer<typeof kurzSlidePropsSchema>;
export type KurzIntroVideoProps = z.infer<typeof kurzIntroVideoSchema>;
export type KurzCompanyProps = z.infer<typeof kurzCompanySchema>;
export type KurzTextProps = z.infer<typeof kurzTextSchema>;
