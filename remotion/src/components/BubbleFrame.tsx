import React from 'react';
import {Loop, OffthreadVideo, Series, staticFile} from 'remotion';
import {brand} from '../brand';

// NOTE (deviation from plan, carried over from the original Loop-based
// implementation): installed remotion@4.0.496's OffthreadVideo has no `loop`
// prop (tsc TS2322 — see props.d.ts MandatoryOffthreadVideoProps /
// OptionalOffthreadVideoProps). The legacy single-`src` mode below still
// wraps in <Loop> for that reason. The new `clips` mode added in Task 4
// (§0-bis of the reel-factory spec) never loops — it plays a <Series> of
// distinct clips back-to-back, one per beat, per the "looping B-roll is dead"
// amendment.
const BUBBLE_LOOP_FRAMES = 240;

export type BubbleClip = {src: string; durationInFrames: number};

// Task 4 implementer's choice (documented per the plan): BubbleFrame keeps
// its original single-`src` signature (still used by HalalVerdictReel /
// ddog.json, unchanged) AND gains a `clips` signature (used by
// SlideStoryReel when `bubbleClips` is non-empty). One prop or the other,
// never both — the discriminated prop type below enforces that at compile
// time instead of silently ignoring one.
type BubbleFrameProps = {src: string; clips?: never} | {clips: BubbleClip[]; src?: never};

const frameStyle: React.CSSProperties = {
  position: 'absolute',
  right: 36,
  bottom: brand.safeBottom + 40,
  width: '30%',
  aspectRatio: '9 / 16',
  borderRadius: 24,
  overflow: 'hidden',
  border: `3px solid ${brand.border}`,
  boxShadow: '0 12px 48px rgba(0,0,0,0.55)',
};

const videoStyle: React.CSSProperties = {width: '100%', height: '100%', objectFit: 'cover'};

export const BubbleFrame: React.FC<BubbleFrameProps> = (props) => {
  if (props.clips) {
    return (
      <div style={frameStyle}>
        <Series>
          {props.clips.map((clip, i) => (
            <Series.Sequence key={`${clip.src}-${i}`} durationInFrames={clip.durationInFrames}>
              <OffthreadVideo src={staticFile(clip.src)} style={videoStyle} />
            </Series.Sequence>
          ))}
        </Series>
      </div>
    );
  }

  return (
    <div style={frameStyle}>
      <Loop durationInFrames={BUBBLE_LOOP_FRAMES}>
        <OffthreadVideo src={staticFile(props.src)} style={videoStyle} />
      </Loop>
    </div>
  );
};
