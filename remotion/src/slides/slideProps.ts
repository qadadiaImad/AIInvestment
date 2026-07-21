import {z} from 'zod';

export const beatSchema = z.discriminatedUnion('kind', [
  z.object({kind: z.literal('hook'), headline: z.string(), sub: z.string(),
            accentWord: z.string().optional(), durationInFrames: z.number()}),
  z.object({kind: z.literal('donut'), title: z.string(), pct: z.number(),
            centerLabel: z.string(), caption: z.string(),
            tone: z.enum(['pass', 'fail', 'warn']), durationInFrames: z.number()}),
  z.object({kind: z.literal('bars'), title: z.string(), caption: z.string().optional(),
            bars: z.array(z.object({label: z.string(), ratio: z.number().nullable(),
              threshold: z.number(), status: z.enum(['pass', 'fail', 'unknown'])})),
            durationInFrames: z.number()}),
  z.object({kind: z.literal('stamp'), verdict: z.enum(['halal', 'not_halal', 'questionable', 'insufficient_data']),
            basis: z.string(), line: z.string(), durationInFrames: z.number()}),
  z.object({kind: z.literal('endcard'), headline: z.string(), sub: z.string(),
            durationInFrames: z.number()}),
]);
export const bubbleClipSchema = z.object({src: z.string(), durationInFrames: z.number()});
export const slideStoryPropsSchema = z.object({
  ticker: z.string(), tickerSub: z.string(), badge: z.string(),
  beats: z.array(beatSchema).min(2),
  vo: z.array(z.string()),               // one narration line per beat (Phase 2b consumes)
  bubbleClips: z.array(bubbleClipSchema).default([]),   // empty = friend's VO-less slide mode
  captions: z.array(z.object({text: z.string(), fromMs: z.number(), toMs: z.number()})).default([]),
  disclaimer: z.string(),
});
export type SlideStoryProps = z.infer<typeof slideStoryPropsSchema>;

// Additive (not part of the plan's verbatim block): a per-beat type, convenient for the
// composition's discriminated-union rendering switch and for T3/T4 consumers.
export type Beat = z.infer<typeof beatSchema>;
