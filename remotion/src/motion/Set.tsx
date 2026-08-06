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

// ── PANEL STUDIO ─────────────────────────────────────────────────────────
// The football-halftime layout the owner asked for: the panel sits at one
// desk, the exhibits play on a GIANT wall behind them (mid-match analysis
// scale, not a monitor above their heads), and all the variety comes from
// the scene CAMERA — wide table shot, punch-in on the speaker — while the
// characters themselves stay calm. Same studio, same palette; different
// grammar.

/** The video wall's picture area — stadium scale. */
export const WALL = {x: 52, y: 150, w: 976, h: 740};

/** Where a panelist's feet go in desk mode. The foreground desk (drawn
 *  OVER the actors) hides everything below the waist, which is what makes
 *  a standing drawing read as seated. */
export const PANEL_FLOOR = 1826;

/** Fixed seats — the panel does not wander. Rex stage-left, Sol stage-right. */
// RESCALED for the table. At h~1000 the heads filled the frame and the
// desk read as a strip under two portraits; a panel shot wants the person
// SMALLER than the room. These sit head-and-shoulders above the curve with
// studio visible around them.
export const SEATS: Record<'sol' | 'rex', {x: number; h: number}> = {
  rex: {x: 322, h: 792},
  sol: {x: 760, h: 772},
};

/** Each panelist's palette, for the hand that rests on the table — pulled
 *  from their own drawings so the drawn hand and the generated character
 *  share skin, sleeve and line colour exactly. */
export const HAND_PALETTE: Record<'sol' | 'rex',
  {skin: string; cuff: string; ink: string}> = {
  sol: {skin: '#F9D9C1', cuff: '#693B40', ink: '#3E1A20'},
  rex: {skin: '#F6D8BC', cuff: '#8A8F98', ink: '#1A1615'},
};

export const WallFrame: React.FC<{glow?: boolean}> = ({glow = false}) => (
  <>
    <div style={{position: 'absolute',
      left: WALL.x - 14, top: WALL.y - 14,
      width: WALL.w + 28, height: WALL.h + 28,
      background: '#0A0D14', borderRadius: 10,
      boxShadow: '0 30px 80px rgba(0,0,0,0.6)',
      border: '3px solid #1E2637'}} />
    {glow ? (
      <div style={{position: 'absolute',
        left: WALL.x - 120, top: WALL.y - 90,
        width: WALL.w + 240, height: WALL.h + 180,
        pointerEvents: 'none', opacity: 0.45,
        background: 'radial-gradient(ellipse, rgba(150,190,255,0.28) 0%, rgba(150,190,255,0) 68%)'}} />
    ) : null}
  </>
);

/** The desk the panel sits behind — drawn OVER the characters, which is
 *  the entire trick: a standing drawing with its lower half occluded by a
 *  branded desk IS a seated panelist. */
export const DeskFront: React.FC<{dark?: boolean}> = ({dark = false}) => (
  <>
    {/* top slab, in perspective */}
    <div style={{position: 'absolute', left: -80, top: 1555, width: W + 160, height: 52,
      background: dark ? '#241A16' : '#3A2A22',
      clipPath: 'polygon(5% 0, 95% 0, 100% 100%, 0 100%)'}} />
    {/* edge highlight */}
    <div style={{position: 'absolute', left: -80, top: 1555, width: W + 160, height: 6,
      background: dark ? 'rgba(190,150,110,0.30)' : 'rgba(230,190,140,0.55)',
      clipPath: 'polygon(5% 0, 95% 0, 95% 100%, 5% 100%)'}} />
    {/* face */}
    <div style={{position: 'absolute', left: -80, top: 1603, width: W + 160, height: H - 1603,
      background: dark
        ? 'linear-gradient(180deg, #171010 0%, #0D0908 100%)'
        : 'linear-gradient(180deg, #271C17 0%, #150F0C 100%)'}} />
    {/* the show badge — corner of the desk face, clear of the subtitles */}
    <div style={{position: 'absolute', left: 70, top: 1615,
      fontFamily: 'Impact, Arial', fontSize: 26, letterSpacing: 3,
      color: 'rgba(255,216,96,0.8)'}}>
      MARKET LESSONS <span style={{color: 'rgba(159,178,216,0.65)',
        fontFamily: 'Arial', fontSize: 17, letterSpacing: 2}}>· THE DESK</span>
    </div>
  </>
);

/** THE ROUND TABLE. Drawn, not generated — two rounds of diffusion
 *  produced crescent moons and school desks, and a broadcast desk is
 *  geometry anyway: an elliptical arc that bulges TOWARD camera (nearest
 *  at centre, rising at the wings) is what reads as "the panel sits
 *  around a round table". Warm wood, gold rim, seat divider hints. */
export const RoundDesk: React.FC<{dark?: boolean}> = ({dark = false}) => {
  const wood = dark ? '#241A16' : '#3A2A22';
  const woodLo = dark ? '#0D0908' : '#150F0C';
  const top = dark ? '#4A362B' : '#5C4434';
  const rim = dark ? 'rgba(190,150,110,0.5)' : 'rgba(230,190,140,0.85)';
  // the near-edge arc: high at the wings, lowest (nearest) at centre
  const arc = 'M -80 1546 Q 540 1752 1160 1546';
  const arcTop = 'M -80 1506 Q 540 1712 1160 1506';
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}
      style={{position: 'absolute', inset: 0}}>
      {/* desk top surface: a band between two arcs */}
      <path d={`${arcTop} L 1160 1445 Q 540 1650 -80 1445 Z`}
        fill={top} />
      {/* subtle sheen on the top */}
      <path d={`M -80 1513 Q 540 1718 1160 1513 L 1160 1525 Q 540 1730 -80 1525 Z`}
        fill="#fff" opacity={0.07} />
      {/* gold rim on the near edge */}
      <path d={arc} fill="none" stroke={rim} strokeWidth={7} />
      {/* front face down to the bottom of frame */}
      <path d={`${arc} L 1160 ${H} L -80 ${H} Z`} fill={wood} />
      <path d={`M -80 1782 Q 540 1940 1160 1782 L 1160 ${H} L -80 ${H} Z`}
        fill={woodLo} opacity={0.75} />
      {/* seat divider hints wrapping the curve */}
      <path d="M 214 1619 q 8 60 2 300" stroke={woodLo} strokeWidth={5}
        fill="none" opacity={0.55} />
      <path d="M 866 1619 q -8 60 -2 300" stroke={woodLo} strokeWidth={5}
        fill="none" opacity={0.55} />
      {/* no badge on the face: the subtitles own that zone, and the first
          still had the show name striking through Sol's own line */}
    </svg>
  );
};

/** y of the desk's near edge at any x — the same quadratic RoundDesk draws
 *  with, exported so hands and props can sit ON the table rather than at a
 *  guessed height that only matches at one point of the curve. */
export const deskYAt = (x: number) => {
  const t = Math.max(0, Math.min(1, (x + 80) / 1240));
  return (1 - t) * (1 - t) * 1546 + 2 * t * (1 - t) * 1752 + t * t * 1546;
};

export type HandSpec = {
  x: number; skin: string; cuff: string; ink: string;
  /** 0..1 — a small lift-and-land, used sparingly on the speaker */
  tap?: number;
  flip?: boolean;
};

/** A hand resting on the table. Drawn rather than cut from the cast art:
 *  the pose drawings' arms are raised or crossed, and rotating one down to
 *  the desk pulled its fill off the shared line art (the same failure that
 *  produced the floating-fragment ghost). A drawn hand in the character's
 *  own palette, with the cast's line weight, sits on the desk correctly at
 *  every camera angle and costs nothing. */
export const DeskHand: React.FC<HandSpec> = ({
  x, skin, cuff, ink, tap = 0, flip = false,
}) => {
  const y = deskYAt(x) - 6 - tap * 12;
  const s = flip ? -1 : 1;
  return (
    <g transform={`translate(${x} ${y}) scale(${s} 1) rotate(${tap * -3})`}>
      {/* sleeve cuff, behind the hand and running back under the desk edge */}
      <path d="M -66 -6 q -6 -40 26 -46 l 44 0 q 30 6 24 46 z"
        fill={cuff} stroke={ink} strokeWidth={7} strokeLinejoin="round" />
      {/* back of the hand */}
      <path d="M -34 2 q -26 -34 8 -46 q 34 -12 56 6 q 22 18 14 40 q -6 14 -30 12 z"
        fill={skin} stroke={ink} strokeWidth={7} strokeLinejoin="round" />
      {/* finger separations along the near edge */}
      <path d="M -14 -4 q 2 -14 4 -22 M 6 -2 q 3 -15 4 -24 M 26 -2 q 2 -13 1 -22"
        fill="none" stroke={ink} strokeWidth={5} strokeLinecap="round"
        opacity={0.75} />
      {/* thumb */}
      <path d="M -34 -10 q -16 -6 -14 -22 q 2 -14 18 -10"
        fill={skin} stroke={ink} strokeWidth={7} strokeLinecap="round"
        strokeLinejoin="round" />
    </g>
  );
};

export const DeskHands: React.FC<{hands: HandSpec[]}> = ({hands}) => (
  <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}
    style={{position: 'absolute', inset: 0, pointerEvents: 'none'}}>
    {hands.map((h, i) => <DeskHand key={i} {...h} />)}
  </svg>
);

/** The crawl along the desk face — the band a market channel runs, in the
 *  space the table was otherwise wasting. Two copies tile so the loop is
 *  seamless, and the illustrative-data rail rides INSIDE the crawl so the
 *  fictional tape can never be mistaken for a quote feed. */
export const NewsBand: React.FC<{frame: number; dark?: boolean}> = ({
  frame, dark = false,
}) => {
  const ITEMS = [
    'MARKET LESSONS · THE DESK',
    'ILLUSTRATIVE TAPE · NOT REAL PRICES',
    'LTX  111.13  ▲ 0.42%',
    'VOLQ  24.80  ▼ 1.10%',
    'CRUDE  63.40  ▲ 0.88%',
    'EDUCATIONAL · NOT ADVICE',
    'BONDS  4.12%  ▼ 3bp',
    'MEGA-CAP  ▲ 0.31%',
  ];
  const line = ITEMS.join('     ·     ') + '     ·     ';
  const SPEED = 78; // px per second
  const CYCLE = 2600; // approx px of one copy at this font size
  const dx = -((frame / 30) * SPEED) % CYCLE;
  const bg = dark ? '#0A0E17' : '#0D1322';
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: 1792, height: 62,
      background: bg, borderTop: '2px solid rgba(230,190,140,0.45)',
      borderBottom: '2px solid rgba(0,0,0,0.5)', overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: 0, top: 0, height: 62,
        whiteSpace: 'nowrap', transform: `translateX(${dx}px)`,
        fontFamily: 'Arial', fontWeight: 700, fontSize: 27, lineHeight: '62px',
        letterSpacing: 1.5, color: '#9FE8C0'}}>
        {line}{line}
      </div>
      {/* soft edges so items enter and leave rather than pop */}
      <div style={{position: 'absolute', inset: 0, pointerEvents: 'none',
        background: `linear-gradient(90deg, ${bg} 0%, rgba(0,0,0,0) 7%,`
          + ` rgba(0,0,0,0) 93%, ${bg} 100%)`}} />
    </div>
  );
};
