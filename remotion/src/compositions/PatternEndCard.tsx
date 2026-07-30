// PatternEndCard.tsx — the CTA frame that closes the pattern sheet.
//
// The owner merges this into Instagram themselves, so it is a STILL, not a
// beat: one 1080x1920 frame that has to sit against the sheet without a seam.
// Every token here is imported from the same places the sheet uses (PT for
// colour, FONT for type, the same 108px ruled grid, the same Grain/Vignette
// at the same strengths) rather than re-typed — a hand-copied hex is how a
// merged end card ends up a shade off and reads as someone else's slide.
//
// The composition is a `Still` in Root: no timeline, one frame, rendered with
// `remotion still`. It carries the same footer discipline as every other
// surface in the channel.
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {z} from 'zod';
import {FONT} from '../slides/theme';
import {Grain, Vignette} from '../motion/Polish';
import {PT} from '../components/PatternCard';

export const patternEndCardSchema = z.object({
  /** The ask, in two lines — kept in props so a variant is a prop change. */
  headline: z.string(),
  headlineAccent: z.string(),
  sub: z.string(),
  /** The comment prompt, styled as a terminal input the viewer "types" in. */
  prompt: z.string(),
  placeholder: z.string(),
  footer: z.string(),
});
export type PatternEndCardProps = z.infer<typeof patternEndCardSchema>;

/** Tickers shown as example chips — the ask is concrete when it is
 * illustrated, and these are the assets the scanner can genuinely run on. */
const CHIPS = ['AAPL', 'BTC', 'NVDA', 'TSLA', 'GOLD', 'EURUSD'];

export const PatternEndCard: React.FC<PatternEndCardProps> = (p) => {
  return (
    <AbsoluteFill style={{backgroundColor: PT.bg}}>
      {/* the sheet's own ruled grid, identical spacing and alpha */}
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        {Array.from({length: 11}, (_, i) => (
          <line key={`v${i}`} x1={i * 108} x2={i * 108} y1={0} y2={1920} stroke="rgba(0,224,130,0.03)" strokeWidth={1} />
        ))}
        {Array.from({length: 19}, (_, i) => (
          <line key={`h${i}`} x1={0} x2={1080} y1={i * 108} y2={i * 108} stroke="rgba(0,224,130,0.03)" strokeWidth={1} />
        ))}
      </svg>

      {/* a soft emerald bloom behind the headline so the middle of the frame
          has depth — the sheet gets its depth from ten lit panels, and without
          something here the card reads flat beside it */}
      <div
        style={{
          position: 'absolute',
          left: 140,
          top: 620,
          width: 800,
          height: 620,
          borderRadius: '50%',
          background: 'radial-gradient(closest-side, rgba(0,230,118,0.13), rgba(0,230,118,0))',
          filter: 'blur(20px)',
        }}
      />

      {/* --------------------------------------------------------- masthead */}
      <div style={{position: 'absolute', top: 120, left: 0, right: 0, textAlign: 'center'}}>
        <div style={{fontFamily: FONT.mono, fontSize: 19, letterSpacing: 6, color: PT.steel, fontWeight: 700}}>
          MAYA LAB
        </div>
      </div>

      {/* ------------------------------------------------- the running tape.
          A row of candles above and below the message, drawn from the same
          palette as the cells: it says "this is the same channel" faster than
          any logo, and fills the vertical space the sheet fills with charts. */}
      {[430, 1372].map((ty, row) => (
        <svg key={ty} width={1080} height={120} style={{position: 'absolute', left: 0, top: ty}}>
          {Array.from({length: 26}, (_, i) => {
            // deterministic pseudo-tape: no randomness, no claim — decoration
            // that never pretends to be a price series
            const seed = (i * 37 + row * 91) % 17;
            const up = seed % 3 !== 0;
            const h = 22 + (seed % 6) * 9;
            const y = 60 - h / 2 + ((seed % 5) - 2) * 6;
            const col = up ? PT.up : PT.down;
            const x = 20 + i * 40.5;
            return (
              <g key={i} opacity={0.16 + (seed % 4) * 0.06}>
                <line x1={x} x2={x} y1={y - 10} y2={y + h + 10} stroke={col} strokeWidth={1.6} />
                <rect x={x - 6} y={y} width={12} height={h} rx={2} fill={col} />
              </g>
            );
          })}
        </svg>
      ))}

      {/* --------------------------------------------------------- headline */}
      <div style={{position: 'absolute', top: 640, left: 60, right: 60, textAlign: 'center'}}>
        <div
          style={{
            fontFamily: FONT.display,
            fontWeight: 700,
            fontSize: 96,
            lineHeight: 1.02,
            letterSpacing: -2,
            color: PT.ink,
          }}
        >
          {p.headline}
          <br />
          <span style={{color: '#9FC2E8'}}>{p.headlineAccent}</span>
        </div>
        <div
          style={{
            fontFamily: FONT.mono,
            fontSize: 30,
            color: PT.steel,
            marginTop: 34,
            letterSpacing: 1.4,
            lineHeight: 1.5,
          }}
        >
          {p.sub}
        </div>
      </div>

      {/* ----------------------------------------------- the comment field.
          Styled as the channel's own terminal input rather than an Instagram
          UI mock: a real platform's chrome on a post ages badly and reads as
          a screenshot of someone else's app. */}
      <div style={{position: 'absolute', top: 1010, left: 90, right: 90}}>
        <div style={{fontFamily: FONT.mono, fontSize: 22, color: PT.ice, letterSpacing: 3, marginBottom: 16}}>
          {p.prompt}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            height: 96,
            padding: '0 28px',
            borderRadius: 16,
            background: 'linear-gradient(#04100C, #020806)',
            border: `1.6px solid ${PT.edge}`,
            boxShadow: '0 0 60px rgba(0,230,118,0.06)',
          }}
        >
          <span style={{fontFamily: FONT.mono, fontSize: 34, color: PT.ice, marginRight: 14}}>&gt;</span>
          <span style={{fontFamily: FONT.mono, fontSize: 34, color: '#7FA290', letterSpacing: 1.2}}>
            {p.placeholder}
          </span>
          {/* the cursor — a still frame's one implied motion */}
          <span
            style={{
              display: 'inline-block',
              width: 16,
              height: 40,
              marginLeft: 8,
              background: PT.ice,
              boxShadow: `0 0 14px ${PT.ice}`,
            }}
          />
        </div>

        {/* example tickers */}
        <div style={{display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: 14, marginTop: 30}}>
          {CHIPS.map((t) => (
            <span
              key={t}
              style={{
                fontFamily: FONT.mono,
                fontSize: 26,
                fontWeight: 700,
                letterSpacing: 1.6,
                color: '#BFE9D2',
                padding: '11px 22px',
                borderRadius: 999,
                border: '1.5px solid rgba(0,224,130,0.22)',
                background: 'rgba(4,16,12,0.7)',
              }}
            >
              {t}
            </span>
          ))}
        </div>
      </div>

      {/* ------------------------------------------------------------ follow */}
      <div style={{position: 'absolute', top: 1560, left: 0, right: 0, textAlign: 'center'}}>
        <span
          style={{
            display: 'inline-block',
            padding: '20px 46px',
            borderRadius: 999,
            background: PT.up,
            fontFamily: FONT.mono,
            fontSize: 34,
            fontWeight: 700,
            letterSpacing: 2.4,
            color: '#04120B',
          }}
        >
          + FOLLOW FOR THE NEXT ONE
        </span>
      </div>

      <Vignette strength={0.24} />
      <Grain opacity={0.038} />

      <div
        style={{
          position: 'absolute',
          left: 40,
          right: 40,
          bottom: 20,
          textAlign: 'center',
          fontFamily: FONT.mono,
          fontSize: 16.5,
          color: '#7FA290',
          letterSpacing: 0.4,
          lineHeight: 1.45,
        }}
      >
        {p.footer}
      </div>
    </AbsoluteFill>
  );
};
