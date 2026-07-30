// PatternGallery.tsx — the animated version of the classic "trading chart
// patterns" cheat sheet. 1080x1920, 30fps, 1350 frames (45.0s), silent-first:
// the owner scores it with a trending track at post time, so every beat is cut
// on a clean grid and the only SFX are sparse candle blips and stamp ticks
// that sit under any music.
//
// The reference is the static pattern-sheet post: 25 tiny diagrams in a grid.
// This does what that format cannot — each formation gets a readable moment
// where it DRAWS itself (tape-print candles, pen-drawn trendlines, the
// breakout firing, the verdict stamping) — and then earns what that format
// does best: the completed cards assemble into a save-able poster at the end.
// Watch it once, screenshot the last frame.
//
// Theme: the channel's prod quiz look — near-black green terminal, serif
// display title, MAYA LAB window chrome, glowing candles.
//
// Data: the validated synthetic pattern library, prepared by
// scripts/patterns_post/build_fixture.py (which computes all overlay
// geometry). These are idealized illustrations BY DESIGN — like every cheat
// sheet's diagrams — and the footer says so on every frame. No prices are
// authored here.
import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {FONT} from '../slides/theme';
import {EASE, fadeOf} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';
import {CARD_T, PatternCard, PT, type PatternData} from '../components/PatternCard';

export const patternGallerySchema = z.object({
  chapters: z.array(
    z.object({
      title: z.string(),
      sub: z.string(),
      cards: z.array(z.any()),
    })
  ),
  footer: z.string(),
  durationInFrames: z.number(),
});
export type PatternGalleryProps = z.infer<typeof patternGallerySchema>;

// ------------------------------------------------------------------ timeline
// 56 intro + 3 x (26 header + 4 x 92 cards) + 112 poster = 1350 exactly.
const INTRO = 56;
const HEADER = 26;
const CARD = 92;
const CHAPTER = HEADER + 4 * CARD; // 394
const POSTER_IN = INTRO + 3 * CHAPTER; // 1238
export const PATTERN_GALLERY_FRAMES = 1350;

const chapterStart = (c: number) => INTRO + c * CHAPTER;
const cardStart = (c: number, j: number) => chapterStart(c) + HEADER + j * CARD;

const ACCENTS = ['#E0A23B', '#22E07E', '#8FB6E8'];

export const PatternGallery: React.FC<PatternGalleryProps> = (p) => {
  const frame = useCurrentFrame();

  const all: {card: PatternData; c: number; j: number}[] = p.chapters.flatMap((ch, c) =>
    ch.cards.map((card: PatternData, j: number) => ({card, c, j}))
  );

  // Which chapter the playhead is in (for the header strip).
  const chapIdx = Math.max(0, Math.min(2, Math.floor((frame - INTRO) / CHAPTER)));
  const chapter = p.chapters[chapIdx];
  const inPoster = frame >= POSTER_IN;

  const headerP = interpolate(frame, [chapterStart(chapIdx), chapterStart(chapIdx) + 16], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const introP =
    interpolate(frame, [2, 18], [0, 1], {easing: EASE.enter, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) *
    interpolate(frame, [INTRO - 10, INTRO], [1, 0], {easing: EASE.exit, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  const posterP = interpolate(frame, [POSTER_IN, POSTER_IN + 18], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: PT.bg}}>
      {/* faint ruled grid, house terminal */}
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        {Array.from({length: 11}, (_, i) => (
          <line key={`v${i}`} x1={i * 108} x2={i * 108} y1={0} y2={1920} stroke="rgba(0,224,130,0.03)" strokeWidth={1} />
        ))}
        {Array.from({length: 19}, (_, i) => (
          <line key={`h${i}`} x1={0} x2={1080} y1={i * 108} y2={i * 108} stroke="rgba(0,224,130,0.03)" strokeWidth={1} />
        ))}
      </svg>

      {/* --------------------------------------------------------- masthead */}
      <div style={{position: 'absolute', top: 46, left: 0, right: 0, textAlign: 'center'}}>
        <div style={{fontFamily: FONT.mono, fontSize: 21, letterSpacing: 6, color: PT.steel, fontWeight: 700}}>
          MAYA LAB
        </div>
        <div
          style={{
            fontFamily: FONT.display,
            fontWeight: 700,
            fontSize: 74,
            color: PT.ink,
            letterSpacing: -1,
            lineHeight: 1.04,
          }}
        >
          CHART <span style={{color: '#9FC2E8'}}>PATTERNS</span>
        </div>
      </div>

      {/* chapter strip — hidden during intro and poster */}
      {!inPoster && frame >= INTRO ? (
        <div
          style={{
            position: 'absolute',
            top: 214,
            left: 0,
            right: 0,
            textAlign: 'center',
            opacity: headerP,
            transform: `translateY(${(1 - headerP) * -10}px)`,
          }}
        >
          <span
            style={{
              display: 'inline-block',
              padding: '10px 26px',
              borderRadius: 999,
              border: `2px solid ${ACCENTS[chapIdx]}55`,
              background: 'rgba(4,16,12,.8)',
              fontFamily: FONT.mono,
              fontSize: 27,
              fontWeight: 700,
              letterSpacing: 3,
              color: ACCENTS[chapIdx],
            }}
          >
            {chapter.title} — {chapter.sub.toUpperCase()}
          </span>
        </div>
      ) : null}

      {/* ------------------------------------------------------------ intro */}
      {frame < INTRO ? (
        <div style={{position: 'absolute', top: 720, left: 0, right: 0, textAlign: 'center', opacity: introP}}>
          <div style={{fontFamily: FONT.display, fontSize: 58, fontWeight: 700, color: PT.ink, lineHeight: 1.15}}>
            12 real formations.
            <br />
            <span style={{color: '#9FC2E8'}}>Found in the S&amp;P.</span>
          </div>
          <div style={{fontFamily: FONT.mono, fontSize: 24, color: PT.steel, marginTop: 26, letterSpacing: 1.5}}>
            real SPY bars · real dates · save the poster
          </div>
        </div>
      ) : null}

      {/* ------------------------------------------------------- hero cards */}
      {!inPoster
        ? all.map(({card, c, j}) => (
            <Sequence key={card.id} from={cardStart(c, j)} durationInFrames={CARD} layout="none">
              <HeroSlot card={card} />
            </Sequence>
          ))
        : null}

      {/* -------------------------------------------------- collection rail.
          Every completed pattern drops into its slot — progress you can see,
          and the poster the end assembles is literally this rail grown up. */}
      {!inPoster ? (
        <div style={{position: 'absolute', top: 1502, left: 0, right: 0}}>
          <div style={{display: 'flex', justifyContent: 'center', gap: 8}}>
            {all.map(({card, c, j}, idx) => {
              const doneAt = cardStart(c, j) + CARD_T.stampIn + 10;
              const pp = interpolate(frame, [doneAt, doneAt + 10], [0, 1], {
                easing: EASE.settleBack,
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
              return (
                <div
                  key={idx}
                  style={{
                    width: 78,
                    height: 58,
                    borderRadius: 8,
                    border: `1.5px solid ${frame >= doneAt ? `${ACCENTS[c]}88` : 'rgba(0,224,130,0.14)'}`,
                    background: 'rgba(2,8,6,.8)',
                    overflow: 'hidden',
                    transform: `scale(${frame >= doneAt ? pp : 1})`,
                    opacity: frame >= doneAt ? pp : 0.5,
                  }}
                >
                  {frame >= doneAt ? (
                    <PatternCard data={{...card, name: ''}} width={78} height={58} variant="mini" accent={ACCENTS[c]} />
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {/* ----------------------------------------------------------- poster */}
      {inPoster ? (
        <div style={{position: 'absolute', top: 240, left: 0, right: 0, opacity: posterP}}>
          <div style={{display: 'flex', justifyContent: 'center', gap: 14}}>
            {p.chapters.map((ch, c) => (
              <div key={ch.title} style={{width: 336}}>
                <div
                  style={{
                    textAlign: 'center',
                    fontFamily: FONT.mono,
                    fontSize: 20,
                    fontWeight: 700,
                    letterSpacing: 2.4,
                    color: ACCENTS[c],
                    marginBottom: 10,
                  }}
                >
                  {ch.title}
                </div>
                {ch.cards.map((card: PatternData, j: number) => {
                  const at = POSTER_IN + 6 + (c * 4 + j) * 4;
                  const pp = interpolate(frame, [at, at + 10], [0, 1], {
                    easing: EASE.settleBack,
                    extrapolateLeft: 'clamp',
                    extrapolateRight: 'clamp',
                  });
                  return (
                    <div key={card.id} style={{marginBottom: 12, transform: `scale(${0.92 + 0.08 * pp})`, opacity: pp}}>
                      <PatternCard data={card} width={336} height={252} variant="mini" accent={ACCENTS[c]} />
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
          <div
            style={{
              textAlign: 'center',
              marginTop: 18,
              fontFamily: FONT.mono,
              fontSize: 26,
              letterSpacing: 2,
              color: PT.ink,
              opacity: interpolate(frame, [POSTER_IN + 60, POSTER_IN + 74], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              }),
            }}
          >
            SAVE THIS ONE ↓
          </div>
        </div>
      ) : null}

      <Vignette strength={0.26} />
      <Grain opacity={0.04} />

      {/* footer — synthetic declaration + rails, every frame, matching prod */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 24,
          textAlign: 'center',
          fontFamily: FONT.mono,
          fontSize: 17,
          color: '#7FA290',
          letterSpacing: 0.5,
          lineHeight: 1.45,
        }}
      >
        {p.footer}
      </div>

      {/* ------------------------------------------------------------ sound.
          Sparse on purpose — a trending track lands on top later. Blips on
          each card's breakout candles only, a tick under each stamp. */}
      {all.map(({card, c, j}) => {
        const s = cardStart(c, j);
        const nReveal = Math.min(3, card.candles.length - card.revealFrom);
        return (
          <React.Fragment key={`au${card.id}`}>
            {Array.from({length: nReveal}, (_, r) => (
              <Sequence key={r} from={s + CARD_T.revealStart + r * CARD_T.revealPer} durationInFrames={12}>
                <Audio
                  src={staticFile(
                    card.candles[card.revealFrom + r].c >= card.candles[card.revealFrom + r].o
                      ? 'audio/candle_up.wav'
                      : 'audio/candle_down.wav'
                  )}
                  volume={0.34}
                />
              </Sequence>
            ))}
            <Sequence from={s + CARD_T.stampIn} durationInFrames={10}>
              <Audio src={staticFile('audio/tock.wav')} volume={0.4} />
            </Sequence>
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};

/** One hero card slot: pops in, plays its 96-frame draw, eases out. Local
 * frame = card time, so PatternCard's internal schedule just works. */
const HeroSlot: React.FC<{card: PatternData}> = ({card}) => {
  const f = useCurrentFrame();
  const inP = interpolate(f, [0, 9], [0, 1], {easing: EASE.enter, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const outP = interpolate(f, [CARD - 7, CARD - 1], [1, 0], {
    easing: EASE.exit,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const lineP = interpolate(f, [CARD_T.stampIn - 4, CARD_T.stampIn + 10], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div style={{opacity: fadeOf(inP) * outP}}>
      <div
        style={{
          position: 'absolute',
          top: 300,
          left: 40,
          width: 1000,
          transform: `scale(${0.965 + 0.035 * inP})`,
          transformOrigin: '50% 40%',
        }}
      >
        <PatternCard data={card} width={1000} height={880} variant="hero" />
      </div>
      <div
        style={{
          position: 'absolute',
          top: 1226,
          left: 90,
          right: 90,
          textAlign: 'center',
          opacity: lineP,
          transform: `translateY(${(1 - lineP) * 14}px)`,
        }}
      >
        <div style={{fontFamily: FONT.display, fontSize: 44, fontWeight: 700, color: PT.ink, lineHeight: 1.22}}>
          {card.answerLine}
        </div>
        <div style={{fontFamily: FONT.mono, fontSize: 21, color: PT.steel, marginTop: 14, letterSpacing: 1}}>
          {card.levelLabel}
        </div>
      </div>
    </div>
  );
};
