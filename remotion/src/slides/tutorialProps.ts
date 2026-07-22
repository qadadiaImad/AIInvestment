import {z} from 'zod';

// TutorialReel — walkthrough reel that narrates a screen recording of the
// live product (see compositions/TutorialReel.tsx). Follows the same
// schema-driven idiom as slideProps.ts (SlideStoryReel): a single typed
// props object drives a parameterized composition instead of one
// hand-authored .tsx per video.

const zoomPointSchema = z.object({
  scale: z.number(), // ~1.0-1.8
  x: z.number(),     // focal point, 0-1 (fraction of capture width)
  y: z.number(),     // focal point, 0-1 (fraction of capture height)
});

export const calloutSchema = z.object({
  text: z.string(),
  atFrame: z.number(),  // frame within the scene the callout fades in at
  x: z.number(),        // anchor position relative to the browser-chrome frame, 0-1
  y: z.number(),        // anchor position relative to the browser-chrome frame, 0-1
});
export type Callout = z.infer<typeof calloutSchema>;

export const tutorialSceneSchema = z.object({
  id: z.string(),
  src: z.string(),                 // staticFile-relative screen capture (webm/mp4), e.g. "caps/table.webm"
  durationInFrames: z.number(),
  vo: z.string(),                  // one calm narration sentence for this scene
  callouts: z.array(calloutSchema).default([]),
  zoom: z.object({from: zoomPointSchema, to: zoomPointSchema}).optional(), // slow ken-burns over the capture
});
export type TutorialScene = z.infer<typeof tutorialSceneSchema>;

export const tutorialPropsSchema = z.object({
  title: z.string(),
  badge: z.string(),
  scenes: z.array(tutorialSceneSchema).min(3),
  karimSrc: z.string(),             // static photo, staticFile-relative
  audioSrc: z.string().optional(),  // single master VO track, muxed post-render or rendered via <Audio>
  disclaimer: z.string(),
});
export type TutorialProps = z.infer<typeof tutorialPropsSchema>;
