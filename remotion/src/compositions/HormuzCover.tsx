// HormuzCover.tsx — the cover still for the Hormuz reel.
//
// Division of labor, learned from a Grok image whose price axis read
// 12→16→45→19: the AI generates ATMOSPHERE ONLY (a no-text tanker aerial,
// prompt-banned from drawing charts or numbers), and everything numeric on
// this frame — the candles, the dates, the marks — is the real Brent fixture
// rendered by the same OilChart the reel uses. Mood from the model, numbers
// from the data.
import React from 'react';
import {AbsoluteFill, staticFile} from 'remotion';
import {z} from 'zod';
import {FONT} from '../slides/theme';
import {PT} from '../components/PatternCard';
import {OilChart, type OBar} from '../components/OilChart';
import fx from '../fixtures/oil_reel/hormuz.json';

export const hormuzCoverSchema = z.object({});

const BARS = fx.bars as OBar[];
const J = fx.july as NonNullable<typeof fx.july>;
const GAP = fx.shock.firstSessionIndex;

export const HormuzCover: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: PT.bg}}>
      {/* the AI layer: atmosphere only, generated with text/charts banned */}
      <img
        src={staticFile('covers/hormuz_bg_grok.png')}
        style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}}
      />
      {/* scrims so type and chart sit IN the scene rather than on it */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(2,7,10,0.82) 0%, rgba(2,7,10,0.25) 26%, rgba(2,7,10,0) 45%, rgba(2,7,10,0.55) 68%, rgba(2,7,10,0.96) 88%)',
        }}
      />

      {/* title block */}
      <div style={{position: 'absolute', top: 128, left: 64, right: 64, textAlign: 'center'}}>
        <div
          style={{
            fontFamily: FONT.mono,
            fontSize: 26,
            fontWeight: 700,
            color: PT.ice,
            letterSpacing: 6,
            marginBottom: 18,
          }}
        >
          STRAIT OF HORMUZ
        </div>
        <div
          style={{
            fontFamily: FONT.mono,
            fontSize: 84,
            fontWeight: 900,
            color: '#EAFFF4',
            lineHeight: 1.06,
            letterSpacing: -2,
            textShadow: '0 4px 34px rgba(0,0,0,0.95)',
          }}
        >
          WHAT MOVES
          <br />
          THE PRICE OF OIL
        </div>
        <div
          style={{
            marginTop: 20,
            fontFamily: FONT.mono,
            fontSize: 25,
            fontWeight: 700,
            color: PT.steel,
            letterSpacing: 1.8,
          }}
        >
          ONE STRAIT CARRIES <span style={{color: PT.ice}}>1 IN 5</span> BARRELS THE WORLD BURNS
        </div>
      </div>

      {/* the DATA layer: the real six months, same component as the reel */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 108,
          height: 500,
          opacity: 0.94,
        }}
      >
        <OilChart
          bars={BARS}
          width={1080}
          height={500}
          printedThrough={BARS.length + 1}
          zoom={1}
          marks={[
            {i: GAP, label: '28 FEB', color: PT.down, opacity: 0.95},
            {i: J.shockIdx, label: '13 JUL', color: PT.down, opacity: 0.95},
          ]}
        />
      </div>

      {/* provenance — a cover is a claim too */}
      <div
        style={{
          position: 'absolute',
          bottom: 46,
          left: 56,
          right: 56,
          textAlign: 'center',
          fontFamily: FONT.mono,
          fontSize: 16,
          color: PT.steel,
          letterSpacing: 0.6,
        }}
      >
        REAL DAILY BARS &middot; BRENT FRONT-MONTH &middot; FEB&ndash;JUL 2026 &middot; NOT INVESTMENT ADVICE
      </div>
    </AbsoluteFill>
  );
};
