import {z} from 'zod';

// Rich-text: a sub/caption/line field can be a plain string (unstyled) or an
// ordered array of inline segments — each with an optional tone color and an
// optional bold flag — to reproduce halal-reels/src/WulfReel.tsx's hand-authored
// <b style={{color: ...}}> emphasis spans (e.g. "38%" bold-amber, "impermissible"
// bold-red) from data instead of hardcoded JSX per ticker.
export const richTextSchema = z.array(z.object({
  t: z.string(),
  tone: z.enum(['text', 'emerald', 'amber', 'red', 'muted']).optional(),
  b: z.boolean().optional(),
}));
export type RichTextSegments = z.infer<typeof richTextSchema>;
// Convenience alias for the union every sub/caption/line field below accepts.
export type RichTextValue = string | RichTextSegments;
const richOrString = () => z.union([z.string(), richTextSchema]);

export const beatSchema = z.discriminatedUnion('kind', [
  z.object({kind: z.literal('hook'), headline: z.string(),
            // Second hook line (WulfReel's "bitcoin money." under "This stock
            // earns") — its own size step + a single tone for the whole line,
            // distinct from richText's per-segment tone (the reference renders
            // this line fully toned, not word-by-word).
            headline2: z.string().optional(),
            headline2Tone: z.enum(['amber', 'emerald', 'red']).default('amber'),
            sub: richOrString(),
            accentWord: z.string().optional(), durationInFrames: z.number()}),
  z.object({kind: z.literal('donut'), title: z.string(), pct: z.number(),
            centerLabel: z.string(), caption: richOrString(),
            tone: z.enum(['pass', 'fail', 'warn']), durationInFrames: z.number()}),
  z.object({kind: z.literal('bars'), title: z.string(), caption: richOrString().optional(),
            bars: z.array(z.object({label: z.string(), ratio: z.number().nullable(),
              threshold: z.number(), status: z.enum(['pass', 'fail', 'unknown'])})),
            durationInFrames: z.number()}),
  z.object({kind: z.literal('stamp'), verdict: z.enum(['halal', 'not_halal', 'questionable', 'insufficient_data']),
            basis: z.string(), line: richOrString(), durationInFrames: z.number()}),
  z.object({kind: z.literal('basket'), title: z.string(),
            rows: z.array(z.object({
              ticker: z.string(),
              note: richOrString(),
              badge: z.string(),
              badgeTone: z.enum(['emerald', 'amber', 'red']).default('emerald'),
            })).min(1).max(5),
            caption: richOrString().optional(),
            durationInFrames: z.number()}),
  z.object({kind: z.literal('endcard'), headline: z.string(), sub: richOrString(),
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
  // Whisper-timed VO track (Task 3/4 producer; Task 6 copies the WAV under
  // remotion/public/daily/<folder>/ so `staticFile` resolves it). Optional —
  // absent for VO-less slide mode (bubbleClips-driven fixtures).
  voiceSrc: z.string().optional(),
  // Photographic hero backdrop (Task 3 producer; staticFile-relative, e.g.
  // "heroes/Q4-security.jpg"). Optional — absent renders the composition
  // exactly as before (no HeroLayer mounted).
  heroSrc: z.string().optional(),
});
export type SlideStoryProps = z.infer<typeof slideStoryPropsSchema>;

// Additive (not part of the plan's verbatim block): a per-beat type, convenient for the
// composition's discriminated-union rendering switch and for T3/T4 consumers.
export type Beat = z.infer<typeof beatSchema>;
