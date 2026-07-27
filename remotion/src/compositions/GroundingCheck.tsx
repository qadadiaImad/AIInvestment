// GroundingCheck.tsx — the gate before any animation on the 40s IBIT reel.
//
// The owner's requirement: the character must look like he is standing IN the
// room, not pasted on top of a picture of one. That is decided entirely at the
// placement stage — feet on the real floor, height consistent with a real desk,
// eye-line consistent with the room's camera — and it is only visible by
// looking. So this composition exists purely to be looked at.
//
// Every number here comes from scripts/meme_reel/measure_floor_plane.py, which
// measures the plate rather than guessing: the wall/floor junction, the desk's
// top surface, and the desk's foot contact. Character height then follows from
// one real-world ratio (75cm desk, 175cm adult) rather than from taste.
//
// `guides` draws the measured lines over the top so a wrong placement is
// obvious rather than merely unsatisfying.
import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {z} from 'zod';
import {PoseCut} from '../characters/poseCut';
import {FONT} from '../slides/theme';

export const groundingCheckSchema = z.object({
  /** Multiplier on the MEASURED height. 1.0 = exactly what the desk implies. */
  scale: z.number(),
  /** Horizontal centre of the figure, in composition px. */
  x: z.number(),
  /** Draw the measured floor/desk/screen lines over the plate. */
  guides: z.boolean(),
  label: z.string(),
  poseFrame: z.number(),
  /** Which drawing to stand him in. The widest silhouettes (shock, point) are
   * the ones that decide whether a scale clips, so they get checked too. */
  pose: z.enum(['idle', 'notices', 'point', 'shock', 'facepalm', 'shrug', 'reach']).optional(),
});
export type GroundingCheckProps = z.infer<typeof groundingCheckSchema>;

// ------------------------------------------------- measured, not chosen
// scripts/meme_reel/measure_floor_plane.py against remotion/public/meme_reel/room_plate.png
export const ROOM = {
  wallFloorY: 1508.6,
  deskTopY: 1040.7,
  deskFootY: 1556.4,
  deskHeightPx: 515.7,
  /** (deskHeightPx / 75cm) * 175cm */
  characterHeightPx: 1203.3,
  /** The generated character is a set of held DRAWINGS (poses/*.png), placed
   * by their ground-contact anchor via PoseCut — not the SVG rig. PoseCut's
   * `height` is already the character's ink height in frame px and its
   * anchors.json equalises the drawings to each other, so the floating-figure
   * problem the SVG rig had does not arise here. */
  screenQuad: {x0: 85, y0: 722, x1: 502, y1: 974},
};

export const GroundingCheck: React.FC<GroundingCheckProps> = (p) => {
  const targetH = ROOM.characterHeightPx * p.scale;
  // Feet land on the desk's foot line — the one depth in the plate whose floor
  // position is actually known.
  const feetY = ROOM.deskFootY;

  return (
    <AbsoluteFill style={{background: '#000'}}>
      <Img
        src={staticFile('meme_reel/room_plate.png')}
        style={{position: 'absolute', inset: 0, width: 1080, height: 1920, objectFit: 'cover'}}
      />

      {/* the generated character, facing LEFT because the monitor is on his left */}
      <PoseCut
        height={targetH}
        footX={p.x}
        footY={feetY}
        facing="left"
        frameOverride={p.poseFrame}
        poseOverride={p.pose ?? 'idle'}
        shadow={false}
      />

      {/* Contact shadow, drawn separately so it sits on the plate's own floor
       * rather than inside the rig's bounding box. Without it he floats, which
       * is the single most common tell of a pasted-on character. */}
      <div
        style={{
          position: 'absolute',
          left: p.x,
          top: feetY - 16,
          transform: 'translateX(-50%)',
          width: targetH * 0.34,
          height: 34,
          borderRadius: '50%',
          background: 'radial-gradient(ellipse, rgba(30,18,8,.5), transparent 70%)',
          filter: 'blur(6px)',
        }}
      />

      {p.guides ? (
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          {[
            {y: ROOM.deskTopY, c: '#4FB6E8', t: `desk top ${ROOM.deskTopY}`},
            {y: ROOM.wallFloorY, c: '#E0A23B', t: `wall/floor ${ROOM.wallFloorY}`},
            {y: ROOM.deskFootY, c: '#00E676', t: `floor @ desk depth ${ROOM.deskFootY} — feet here`},
            {y: feetY - targetH, c: '#FF3B30', t: `head ${(feetY - targetH).toFixed(0)}`},
          ].map((g) => (
            <g key={g.t}>
              <line x1={0} x2={1080} y1={g.y} y2={g.y} stroke={g.c} strokeWidth={2} strokeDasharray="10 8" opacity={0.9} />
              <text x={14} y={g.y - 8} fill={g.c} fontFamily={FONT.mono} fontSize={20} fontWeight={700}>
                {g.t}
              </text>
            </g>
          ))}
          <rect
            x={ROOM.screenQuad.x0}
            y={ROOM.screenQuad.y0}
            width={ROOM.screenQuad.x1 - ROOM.screenQuad.x0}
            height={ROOM.screenQuad.y1 - ROOM.screenQuad.y0}
            fill="none"
            stroke="#8FB6E8"
            strokeWidth={2}
            strokeDasharray="8 6"
          />
        </svg>
      ) : null}

      <div
        style={{
          position: 'absolute',
          top: 28,
          left: 0,
          right: 0,
          textAlign: 'center',
          fontFamily: FONT.mono,
          fontSize: 30,
          fontWeight: 700,
          color: '#fff',
          textShadow: '0 2px 10px #000',
        }}
      >
        {p.label} · height {targetH.toFixed(0)}px ({((targetH / 1920) * 100).toFixed(0)}% of frame)
      </div>
    </AbsoluteFill>
  );
};
