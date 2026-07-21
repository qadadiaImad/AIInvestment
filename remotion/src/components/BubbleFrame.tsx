import React from 'react';
import {Loop, OffthreadVideo, staticFile} from 'remotion';
import {brand} from '../brand';

// NOTE (deviation from plan): installed remotion@4.0.496's OffthreadVideo has no
// `loop` prop (tsc TS2322 — see props.d.ts MandatoryOffthreadVideoProps /
// OptionalOffthreadVideoProps). Looping is done via the <Loop> wrapper instead,
// using the bubble clip's known 8s (240 frames @ 30fps) length — same assumption
// the plan already makes for SCENE_FRAMES and CaptionTrack's `8 * fps`.
const BUBBLE_LOOP_FRAMES = 240;

export const BubbleFrame: React.FC<{src: string}> = ({src}) => (
  <div style={{
    position: 'absolute', right: 36, bottom: brand.safeBottom + 40,
    width: '30%', aspectRatio: '9 / 16', borderRadius: 24, overflow: 'hidden',
    border: `3px solid ${brand.border}`, boxShadow: '0 12px 48px rgba(0,0,0,0.55)',
  }}>
    <Loop durationInFrames={BUBBLE_LOOP_FRAMES}>
      <OffthreadVideo src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    </Loop>
  </div>
);
