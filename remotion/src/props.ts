import {z} from 'zod';

export const testResultSchema = z.object({
  id: z.string(),
  label: z.string(),
  ratio: z.number().nullable(),
  threshold: z.number(),
  status: z.enum(['pass', 'fail', 'unknown']),
});

export const sceneSchema = z.object({
  kind: z.enum(['hook', 'math', 'takeaway']),
  headline: z.string(),
  sub: z.string().optional(),
});

export const captionWordSchema = z.object({
  text: z.string(),
  fromMs: z.number(),
  toMs: z.number(),
});

export const reelPropsSchema = z.object({
  ticker: z.string(),
  overall: z.enum(['halal', 'not_halal', 'questionable', 'insufficient_data']),
  overallBasis: z.string(),
  decisive: z.object({
    valuePct: z.number(),        // 5.29
    thresholdPct: z.number(),    // 5.0
    label: z.string(),           // "interest income / revenue"
  }),
  tests: z.array(testResultSchema),
  activityStatus: z.enum(['pass', 'fail', 'unknown']),
  purificationPerShare: z.number().nullable(),
  inputsAsof: z.string(),
  scenes: z.array(sceneSchema).length(3),
  bubbleSrc: z.string(),         // staticFile-relative, e.g. "bubble_ddog.mp4"
  captions: z.array(captionWordSchema),
  disclaimer: z.string(),
});

export type ReelProps = z.infer<typeof reelPropsSchema>;
