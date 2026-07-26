// RigCheck.tsx — a contact sheet of the RubberHoseRig at every story beat.
//
// This is not a deliverable. It exists because the meme reel has two failure
// modes that typecheck and render without error:
//   1. limbs detaching at the joints, and
//   2. a key pose that is simply wrong (arm through the head, leg inverted),
// and hunting for either inside a 510-frame reel is slow and unreliable. Here
// every beat's key frame sits side by side in one still, at a size where a
// detached joint is obvious.
//
// `mode: 'sheet'` renders the six beat poses as a grid. `mode: 'live'` plays
// the rig alone on a flat background at full size, for watching the motion
// without the room and the chart competing for attention.
import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {FONT} from '../slides/theme';
import {RUBBER_HOSE_BEATS, RubberHoseRig} from '../characters/rubberHoseRig';

export const rigCheckSchema = z.object({
  mode: z.enum(['sheet', 'live']),
});
export type RigCheckProps = z.infer<typeof rigCheckSchema>;

/** The frame at which each beat is at its KEY pose — not the frame it starts.
 * A beat's start is usually its anticipation, which is deliberately the least
 * representative frame in it. */
const KEY_FRAMES: {label: string; frame: number}[] = [
  {label: 'idle', frame: RUBBER_HOSE_BEATS.idle + 40},
  {label: 'notices', frame: 104},
  {label: 'leans in', frame: 212},
  {label: 'pattern fails', frame: 250},
  {label: 'facepalm', frame: 362},
  {label: 'shrug', frame: 432},
];

export const RigCheck: React.FC<RigCheckProps> = ({mode}) => {
  const frame = useCurrentFrame();

  if (mode === 'live') {
    return (
      <AbsoluteFill style={{backgroundColor: '#E9DEC7', alignItems: 'center', justifyContent: 'flex-end'}}>
        <RubberHoseRig size={760} facing="left" />
        <div
          style={{
            position: 'absolute',
            top: 40,
            left: 0,
            right: 0,
            textAlign: 'center',
            fontFamily: FONT.mono,
            fontSize: 30,
            color: '#5A5147',
          }}
        >
          frame {frame}
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{backgroundColor: '#E9DEC7'}}>
      <div
        style={{
          position: 'absolute',
          top: 34,
          left: 0,
          right: 0,
          textAlign: 'center',
          fontFamily: FONT.mono,
          fontSize: 28,
          letterSpacing: 2,
          color: '#4A4239',
        }}
      >
        RUBBER-HOSE RIG · BEAT CONTACT SHEET
      </div>
      <div
        style={{
          position: 'absolute',
          top: 90,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gridTemplateRows: 'repeat(2, 1fr)',
        }}
      >
        {KEY_FRAMES.map((k) => (
          <div
            key={k.label}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'flex-end',
              paddingBottom: 12,
              borderLeft: '1px dashed rgba(0,0,0,0.14)',
              borderTop: '1px dashed rgba(0,0,0,0.14)',
            }}
          >
            <RubberHoseRig size={300} facing="left" frameOverride={k.frame} shadow={false} />
            <div style={{fontFamily: FONT.mono, fontSize: 22, color: '#4A4239', marginTop: 6}}>
              {k.label} · f{k.frame}
            </div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
