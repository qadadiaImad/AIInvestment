// Set.tsx — the room the show is filmed in.
//
// WHY THIS EXISTS. Until now the characters stood on nothing: a dark
// vignette, a floating exhibit card, and each figure placed at whatever
// y looked right for that beat. That is why they read as cut-outs laid
// over a background rather than two people in a space — there was no
// space. A set fixes several things at once:
//
//   * ONE FLOOR. Every standing figure is planted on the same line, so
//     their relative heights become real instead of per-beat guesses.
//   * A DESK to stand behind, which hides the feet. The cast drawings
//     are cropped differently from one another; a common occluder means
//     that never has to be reconciled.
//   * A SCREEN to put the exhibits on. A filing card floating in the air
//     is a caption; the same card playing on the studio's monitor is
//     something the characters are looking at.
//
// Geometry is exported so the composition can plant actors on FLOOR_Y
// and render card/caricature content inside TV_SCREEN rather than
// re-deriving numbers that must agree.
import React from 'react';

export const W = 1080;
export const H = 1920;

/** Wall meets floor here. */
export const HORIZON = 1180;
/** Top edge of the desk slab — everything below is foreground. */
export const DESK_TOP = 1620;
/** Where a standing figure's feet go. Below DESK_TOP on purpose: the
 *  desk hides the legs, so drawings cropped at different heights still
 *  share a believable ground.
 *
 *  The gap between these two is how much of a figure the desk EATS, and
 *  it used to be 340px — which forced every character to be staged huge
 *  just to be visible above it, and a huge figure is a wide figure, and
 *  two wide figures cannot fit side by side in a 1080px frame. That is
 *  the real reason the two-shots were overlapping. The desk now hides
 *  110px, so a two-shot can be staged at a sane size and still read. */
export const FLOOR_Y = 1730;

/** The monitor's picture area — exhibits play in here. */
export const TV_SCREEN = {x: 108, y: 250, w: 864, h: 486};

const BEZEL = 18;

export const Room: React.FC<{dark?: boolean}> = ({dark = false}) => {
  const wall = dark ? '#0E1421' : '#16203A';
  const wallLo = dark ? '#0A0F19' : '#101A2E';
  const floor = dark ? '#0B111C' : '#111A2B';
  const deskTop = dark ? '#241A16' : '#3A2A22';
  const deskFace = dark ? '#171010' : '#271C17';
  return (
    <>
      {/* wall */}
      <div style={{position: 'absolute', left: 0, top: 0, width: W, height: HORIZON,
        background: `linear-gradient(180deg, ${wallLo} 0%, ${wall} 62%, ${wallLo} 100%)`}} />
      {/* a soft pool of light behind the talent, so the wall is not flat paint */}
      <div style={{position: 'absolute', left: W / 2 - 620, top: -260, width: 1240, height: 1240,
        borderRadius: '50%', opacity: dark ? 0.22 : 0.5,
        background: 'radial-gradient(circle, rgba(90,130,200,0.30) 0%, rgba(90,130,200,0) 70%)'}} />
      {/* floor */}
      <div style={{position: 'absolute', left: 0, top: HORIZON, width: W, height: H - HORIZON,
        background: `linear-gradient(180deg, ${floor} 0%, ${dark ? '#05080E' : '#0A1018'} 100%)`}} />
      {/* skirting: the line that actually sells wall-meets-floor */}
      <div style={{position: 'absolute', left: 0, top: HORIZON - 10, width: W, height: 10,
        background: dark ? '#070B12' : '#0B1220'}} />
      {/* desk slab, in perspective — wider at the bottom so it reads as
          coming toward camera rather than as a rectangle */}
      <div style={{position: 'absolute', left: -60, top: DESK_TOP, width: W + 120, height: 44,
        background: deskTop, clipPath: 'polygon(6% 0, 94% 0, 100% 100%, 0 100%)'}} />
      <div style={{position: 'absolute', left: -60, top: DESK_TOP + 40, width: W + 120,
        height: H - DESK_TOP - 40, background: deskFace}} />
      {/* a highlight along the desk edge, the only bright line down here */}
      <div style={{position: 'absolute', left: -60, top: DESK_TOP, width: W + 120, height: 5,
        background: dark ? 'rgba(190,150,110,0.28)' : 'rgba(230,190,140,0.5)',
        clipPath: 'polygon(6% 0, 94% 0, 94% 100%, 6% 100%)'}} />
    </>
  );
};

/** The monitor itself: bezel, stand-off shadow and a glass sheen. The
 *  picture is drawn by the composition into TV_SCREEN so the exhibits
 *  and the caricature share one frame. */
export const TVFrame: React.FC<{glow?: boolean}> = ({glow = false}) => (
  <>
    <div style={{position: 'absolute',
      left: TV_SCREEN.x - BEZEL, top: TV_SCREEN.y - BEZEL,
      width: TV_SCREEN.w + BEZEL * 2, height: TV_SCREEN.h + BEZEL * 2,
      background: '#0A0D14', borderRadius: 14,
      boxShadow: '0 26px 60px rgba(0,0,0,0.55)',
      border: '3px solid #1E2637'}} />
    {glow ? (
      <div style={{position: 'absolute',
        left: TV_SCREEN.x - 130, top: TV_SCREEN.y - 110,
        width: TV_SCREEN.w + 260, height: TV_SCREEN.h + 220,
        pointerEvents: 'none', opacity: 0.5,
        background: 'radial-gradient(ellipse, rgba(150,190,255,0.30) 0%, rgba(150,190,255,0) 68%)'}} />
    ) : null}
  </>
);

/** Glass over the picture — a diagonal sheen and a vignette, so the
 *  content reads as displayed rather than pasted. */
export const TVGlass: React.FC = () => (
  <>
    <div style={{position: 'absolute', ...rect(), pointerEvents: 'none',
      background: 'linear-gradient(118deg, rgba(255,255,255,0.10) 0%,'
        + ' rgba(255,255,255,0.03) 26%, rgba(255,255,255,0) 46%)'}} />
    <div style={{position: 'absolute', ...rect(), pointerEvents: 'none',
      boxShadow: 'inset 0 0 70px rgba(0,0,0,0.55)'}} />
  </>
);

function rect() {
  return {left: TV_SCREEN.x, top: TV_SCREEN.y,
          width: TV_SCREEN.w, height: TV_SCREEN.h};
}
