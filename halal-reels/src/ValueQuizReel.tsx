import React from "react";
import { AbsoluteFill, Audio, Img, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import { C, FONT } from "./theme";
import { QUIZ_DATE, QUIZ_RAILS, QUIZ_ROUNDS, type QuizRound } from "./valueQuizData";
import { Bg, Caption, Foot, Kicker, Slam, clamp, easeOut, pop } from "./ui";

// ---------------------------------------------------------------------------
// Timing — "5-Second Value Test" v2 (hero backgrounds, 5s countdown).
// Per round: question card -> 5-4-3-2-1 countdown ring -> reveal.
// ~2.5s question + 5.0s countdown + 2.5s reveal = 10.0s/round; 6 rounds + ~3.5s
// end card ≈ 63.5s total.
// ---------------------------------------------------------------------------
const QUESTION_LEN = 75; // 2.5s
const COUNTDOWN_LEN = 150; // 5.0s (5 ticks x 30f)
const REVEAL_LEN = 75; // 2.5s
const ROUND_LEN = QUESTION_LEN + COUNTDOWN_LEN + REVEAL_LEN; // 300f / 10.0s
const END_LEN = 105; // 3.5s

export const QUIZ_BEATS = {
  question: QUESTION_LEN,
  countdown: COUNTDOWN_LEN,
  reveal: REVEAL_LEN,
  round: ROUND_LEN,
  total: ROUND_LEN * QUIZ_ROUNDS.length + END_LEN,
};

// ---------------------------------------------------------------------------
// Audio timing — derived from the same beat constants above so ticks/reveal
// hits always line up with what's on screen, per round:
//   round start -> [question 75f] -> countdown start -> [countdown 150f, 5
//   ticks @ 30f apart] -> reveal start -> [reveal 75f] -> next round.
// music.mp3: low-volume bed under the whole reel, ducked briefly on reveal.
// tick.mp3:  one hit per second of each round's 5s countdown, louder as it
//            nears zero.
// reveal.mp3: one hit exactly at each round's reveal start (the pill flash).
// ---------------------------------------------------------------------------
const TICK_STEP = COUNTDOWN_LEN / 5; // 30f = 1s per tick
const COUNTDOWN_STARTS = QUIZ_ROUNDS.map((_, i) => i * ROUND_LEN + QUESTION_LEN);
const REVEAL_FRAMES = QUIZ_ROUNDS.map((_, i) => i * ROUND_LEN + QUESTION_LEN + COUNTDOWN_LEN);
const TICK_FRAMES = COUNTDOWN_STARTS.flatMap((start) =>
  Array.from({ length: 5 }, (_, t) => start + t * TICK_STEP),
);

const MUSIC_VOL = 0.3;
const MUSIC_DUCK_VOL = 0.12;
const MUSIC_DUCK_LEN = 20; // frames

/** Music bed volume envelope — baseline, with a short dip on each reveal. */
const musicVolume = (frame: number) => {
  for (const r of REVEAL_FRAMES) {
    const rel = frame - r;
    if (rel >= 0 && rel < MUSIC_DUCK_LEN) {
      return interpolate(
        rel,
        [0, 4, MUSIC_DUCK_LEN - 4, MUSIC_DUCK_LEN],
        [MUSIC_VOL, MUSIC_DUCK_VOL, MUSIC_DUCK_VOL, MUSIC_VOL],
        clamp,
      );
    }
  }
  return MUSIC_VOL;
};

/** Countdown-tick volume — ramps up as the ring nears zero (tick 5 -> 1). */
const tickVolume = (tickIndex: number) => 0.35 + tickIndex * 0.1;

const PAD = 84;
const UNDER_COLOR = C.emerald;
const OVER_COLOR = C.amber;

const verdictColor = (v: QuizRound["verdict"]) => (v === "UNDER" ? UNDER_COLOR : OVER_COLOR);
const verdictLabel = (v: QuizRound["verdict"]) => (v === "UNDER" ? "UNDERVALUED" : "OVERVALUED");

// ---------------------------------------------------------------------------
// Hero background — full-bleed company image with a dark scrim so the
// headline/pills/equation stay legible over it. Slow Ken-Burns drift for life.
// Rendered once per round; sits behind the question, countdown, and reveal.
// ---------------------------------------------------------------------------
const HeroBg: React.FC<{ src: string; totalFrames: number; tint: string }> = ({ src, totalFrames, tint }) => {
  const frame = useCurrentFrame();
  // Parallax Ken-Burns: zoom + a diagonal drift (not just a static zoom).
  const scale = interpolate(frame, [0, totalFrames], [1.09, 1.22], clamp);
  const panX = interpolate(frame, [0, totalFrames], [-2.2, 2.2], clamp);
  const panY = interpolate(frame, [0, totalFrames], [2.4, -3.2], clamp);
  // A slow diagonal light sweep travelling across the frame.
  const sweep = interpolate(frame, [0, totalFrames], [-30, 140], clamp);
  // Breathing vignette + ambient verdict-tint glow.
  const vig = 0.42 + 0.1 * Math.sin(frame * 0.055);
  const glow = 0.16 + 0.09 * Math.sin(frame * 0.045 + 1);
  // Deterministic drifting glow particles (no Math.random/Date — frame+index).
  const N = 26;
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: C.bg }}>
      <Img
        src={staticFile(`quiz/${src}`)}
        style={{
          width: "116%",
          height: "116%",
          objectFit: "cover",
          transform: `translate(${panX}%, ${panY}%) scale(${scale})`,
          transformOrigin: "50% 42%",
        }}
      />
      {/* base legibility scrim */}
      <AbsoluteFill
        style={{ background: `linear-gradient(180deg, ${C.bg}F0 0%, ${C.bg}52 24%, ${C.bg}5E 58%, ${C.bg}F5 100%)` }}
      />
      {/* moving light sweep (verdict-tinted) */}
      <AbsoluteFill
        style={{
          background: `linear-gradient(115deg, transparent ${sweep - 26}%, ${tint}22 ${sweep}%, transparent ${sweep + 26}%)`,
          mixBlendMode: "screen",
        }}
      />
      {/* drifting glow particles */}
      {Array.from({ length: N }).map((_, i) => {
        const seed = i * 47.3;
        const x = (Math.sin(seed) * 0.5 + 0.5) * 100;
        const speed = 0.12 + 0.11 * ((i % 5) / 5);
        const base = (Math.cos(seed * 1.7) * 0.5 + 0.5) * 120;
        let y = (base - frame * speed) % 120;
        if (y < 0) y += 120;
        const size = 3 + (i % 4) * 2.5;
        const op = 0.18 + 0.32 * (Math.sin(frame * 0.05 + seed) * 0.5 + 0.5);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y - 10}%`,
              width: size,
              height: size,
              borderRadius: "50%",
              background: tint,
              opacity: op,
              boxShadow: `0 0 ${size * 3.5}px ${tint}`,
            }}
          />
        );
      })}
      {/* ambient verdict glow + breathing vignette */}
      <AbsoluteFill
        style={{ background: `radial-gradient(ellipse 78% 60% at 50% 44%, ${tint}${Math.round(glow * 255).toString(16).padStart(2, "0")} 0%, transparent 55%)`, mixBlendMode: "screen" }}
      />
      <AbsoluteFill
        style={{ background: `radial-gradient(ellipse 88% 74% at 50% 50%, transparent ${Math.round(38 * vig)}%, ${C.bg}66 100%)` }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Binary option pill.
// ---------------------------------------------------------------------------
const Pill: React.FC<{
  label: string;
  sub: string;
  color: string;
  delay?: number;
  win?: boolean;
  dim?: boolean;
}> = ({ label, sub, color, delay = 0, win, dim }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [delay, delay + 14], [0, 1], { ...clamp, easing: pop });
  return (
    <div
      style={{
        flex: 1,
        textAlign: "center",
        padding: win ? "44px 20px" : "34px 18px",
        borderRadius: 30,
        border: `4px solid ${color}`,
        background: win ? `${color}4d` : `${color}26`,
        opacity: dim ? 0.3 : p,
        scale: String(0.72 + 0.28 * p),
        boxShadow: win ? `0 0 60px ${color}77` : "none",
        backdropFilter: "blur(2px)",
      }}
    >
      <div
        style={{
          fontFamily: FONT.mono,
          fontWeight: 800,
          fontSize: win ? 56 : 42,
          color,
          letterSpacing: 1,
          textShadow: "0 4px 18px rgba(0,0,0,.8)",
        }}
      >
        {win ? "✓ " : ""}
        {label}
      </div>
      <div
        style={{
          fontFamily: FONT.mono,
          fontWeight: 600,
          fontSize: win ? 26 : 21,
          color,
          opacity: 0.85,
          marginTop: 8,
          letterSpacing: 2,
          textShadow: "0 2px 12px rgba(0,0,0,.8)",
        }}
      >
        {sub}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Small ticker/aka tag — secondary identity marker (headline is the full name).
// ---------------------------------------------------------------------------
const TickerTag: React.FC<{ ticker: string; aka?: string }> = ({ ticker, aka }) => (
  <div
    style={{
      fontFamily: FONT.mono,
      fontWeight: 700,
      fontSize: 26,
      letterSpacing: 2,
      color: C.inkSoft,
      background: "rgba(10,13,18,.6)",
      border: `1.5px solid ${C.line}`,
      padding: "10px 20px",
      borderRadius: 12,
      whiteSpace: "nowrap",
      textShadow: "0 2px 10px rgba(0,0,0,.8)",
    }}
  >
    {ticker}
    {aka ? ` · ${aka}` : ""}
  </div>
);

// ---------------------------------------------------------------------------
// Countdown ring — depletes over the beat, ticking 5-4-3-2-1.
// ---------------------------------------------------------------------------
const CountdownRing: React.FC<{ totalFrames: number; startAt?: number }> = ({ totalFrames, startAt = 5 }) => {
  const frame = useCurrentFrame();
  const R = 168;
  const CIRC = 2 * Math.PI * R;
  const elapsed = interpolate(frame, [0, totalFrames], [0, 1], clamp);
  const remaining = 1 - elapsed;
  const seg = totalFrames / startAt;
  const num = Math.max(1, startAt - Math.floor(frame / seg));
  const tickFrame = frame % seg;
  const pulse = interpolate(tickFrame, [0, 9], [1.22, 1], { ...clamp, easing: pop });
  const urgent = num <= 2;
  return (
    <div style={{ position: "relative", width: 400, height: 400 }}>
      <svg width={400} height={400} viewBox="0 0 400 400">
        <circle cx="200" cy="200" r={R} stroke={C.panel} strokeWidth={28} fill="none" />
        <circle
          cx="200"
          cy="200"
          r={R}
          stroke={urgent ? C.amber : C.ink}
          strokeWidth={28}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={CIRC}
          strokeDashoffset={CIRC * (1 - remaining)}
          style={{ transformOrigin: "200px 200px", rotate: "-90deg" }}
        />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            fontFamily: FONT.mono,
            fontWeight: 800,
            fontSize: 176,
            color: urgent ? C.amber : C.ink,
            scale: String(pulse),
            textShadow: "0 10px 44px rgba(0,0,0,.6)",
          }}
        >
          {num}
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// One full round: hero background + question -> countdown -> reveal.
// ---------------------------------------------------------------------------
const RoundScene: React.FC<{ round: QuizRound; roundIndex: number }> = ({ round, roundIndex }) => {
  const color = verdictColor(round.verdict);
  const label = verdictLabel(round.verdict);
  const score = `${roundIndex + 1}/${roundIndex + 1}`;

  return (
    <>
      <HeroBg src={round.hero} totalFrames={ROUND_LEN} tint={color} />

      {/* --- Question card --- */}
      <Sequence from={0} durationInFrames={QUESTION_LEN} name={`R${roundIndex + 1}-Question`}>
        <AbsoluteFill style={{ padding: PAD, justifyContent: "center", gap: 28 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 20 }}>
            <Kicker text={`ROUND ${roundIndex + 1} OF ${QUIZ_ROUNDS.length} · VALUE QUIZ`} color={C.mint} />
            <TickerTag ticker={round.ticker} aka={round.aka} />
          </div>

          <Slam size={100} delay={8}>
            {round.name}
          </Slam>

          <div
            style={{
              fontFamily: FONT.mono,
              fontWeight: 800,
              fontSize: 128,
              lineHeight: 1,
              color: C.ink,
              letterSpacing: -3,
              textShadow: "0 8px 40px rgba(0,0,0,.75)",
            }}
          >
            ${round.price.toFixed(2)}
          </div>

          <div style={{ marginTop: 10 }}>
            <Slam size={76} delay={26}>
              OVERVALUED
            </Slam>
            <Slam size={76} color={C.mint} delay={36}>
              or UNDERVALUED?
            </Slam>
          </div>

          <div style={{ display: "flex", gap: 24, marginTop: 18 }}>
            <Pill label="UNDERVALUED" sub="(cheap)" color={UNDER_COLOR} delay={54} />
            <Pill label="OVERVALUED" sub="(expensive)" color={OVER_COLOR} delay={62} />
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* --- Countdown --- */}
      <Sequence from={QUESTION_LEN} durationInFrames={COUNTDOWN_LEN} name={`R${roundIndex + 1}-Countdown`}>
        <AbsoluteFill style={{ padding: PAD, alignItems: "center", justifyContent: "center", gap: 50 }}>
          <div
            style={{
              fontFamily: FONT.mono,
              fontWeight: 800,
              fontSize: 46,
              letterSpacing: 5,
              color: C.ink,
              textAlign: "center",
              textShadow: "0 4px 20px rgba(0,0,0,.8)",
            }}
          >
            CALL IT BEFORE THE TIMER
          </div>
          <CountdownRing totalFrames={COUNTDOWN_LEN} startAt={5} />
          <div style={{ display: "flex", gap: 24, width: "100%" }}>
            <Pill label="UNDERVALUED" sub="(cheap)" color={UNDER_COLOR} />
            <Pill label="OVERVALUED" sub="(expensive)" color={OVER_COLOR} />
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* --- Reveal --- */}
      <Sequence from={QUESTION_LEN + COUNTDOWN_LEN} durationInFrames={REVEAL_LEN} name={`R${roundIndex + 1}-Reveal`}>
        <RevealCard round={round} color={color} label={label} score={score} />
      </Sequence>
    </>
  );
};

const RevealCard: React.FC<{ round: QuizRound; color: string; label: string; score: string }> = ({
  round,
  color,
  label,
  score,
}) => {
  const frame = useCurrentFrame();
  const flash = interpolate(frame, [0, 3, 14], [0.9, 0.9, 0], clamp);
  const scoreP = interpolate(frame, [30, 44], [0, 1], { ...clamp, easing: pop });
  const eqP = interpolate(frame, [20, 34], [0, 1], { ...clamp, easing: easeOut });
  const whyDelay = 40;

  return (
    <AbsoluteFill style={{ padding: PAD, justifyContent: "center", gap: 30 }}>
      <AbsoluteFill style={{ background: color, opacity: flash, mixBlendMode: "screen" }} />

      <Kicker text="REVEAL" color={color} />

      <div style={{ display: "flex", gap: 20 }}>
        <Pill label="UNDERVALUED" sub="(cheap)" color={UNDER_COLOR} win={round.verdict === "UNDER"} dim={round.verdict !== "UNDER"} delay={0} />
        <Pill label="OVERVALUED" sub="(expensive)" color={OVER_COLOR} win={round.verdict === "OVER"} dim={round.verdict !== "OVER"} delay={0} />
      </div>

      <div
        style={{
          fontFamily: FONT.mono,
          fontWeight: 700,
          fontSize: 42,
          color: C.ink,
          opacity: eqP,
          translate: `0px ${(1 - eqP) * 20}px`,
          marginTop: 8,
          textShadow: "0 4px 20px rgba(0,0,0,.8)",
        }}
      >
        ${round.price.toFixed(2)} vs a model&apos;s <span style={{ color }}>${round.modelValue.toFixed(2)}</span> ={" "}
        <span style={{ color, fontWeight: 800 }}>
          {round.multipleLabel} {label}
        </span>
      </div>

      <div style={{ maxWidth: 900 }}>
        <Caption delay={whyDelay}>{round.why}</Caption>
      </div>

      <div
        style={{
          fontFamily: FONT.mono,
          fontWeight: 800,
          fontSize: 40,
          letterSpacing: 2,
          color: C.bg,
          background: color,
          padding: "16px 30px",
          borderRadius: 16,
          display: "inline-block",
          width: "fit-content",
          opacity: scoreP,
          scale: String(0.8 + 0.2 * scoreP),
        }}
      >
        SCORE: {score}
      </div>

      <div style={{ position: "absolute", bottom: 40, left: PAD, right: PAD, opacity: eqP }}>
        <Foot text={QUIZ_RAILS} />
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// End card.
// ---------------------------------------------------------------------------
const QuizEndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 18], [0, 1], { ...clamp, easing: easeOut });
  const tagP = interpolate(frame, [10, 26], [0, 1], { ...clamp, easing: pop });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 40, padding: 90 }}>
      <div
        style={{
          fontFamily: FONT.mono,
          fontWeight: 700,
          fontSize: 34,
          letterSpacing: 3,
          color: C.bg,
          background: C.mint,
          padding: "18px 32px",
          borderRadius: 16,
          opacity: tagP,
          scale: String(0.8 + 0.2 * tagP),
        }}
      >
        VALUE IQ #1
      </div>
      <div
        style={{
          fontFamily: FONT.display,
          fontWeight: 700,
          fontSize: 70,
          lineHeight: 1.15,
          color: C.ink,
          textAlign: "center",
          opacity: p,
          maxWidth: 880,
        }}
      >
        How many did you get?
        <br />
        Comment your score {"👇"}
      </div>
      <div
        style={{
          fontFamily: FONT.body,
          fontWeight: 600,
          fontSize: 34,
          color: C.mint,
          opacity: p,
        }}
      >
        Follow for the next Value IQ
      </div>
      <div style={{ fontFamily: FONT.mono, fontSize: 24, color: C.muted, opacity: p }}>
        data as of {QUIZ_DATE}
      </div>
      <div style={{ position: "absolute", bottom: 70, left: 90, right: 90, textAlign: "center" }}>
        <Foot text={QUIZ_RAILS} />
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Root composition.
// ---------------------------------------------------------------------------
export const ValueQuizReel: React.FC = () => {
  return (
    <AbsoluteFill style={{ fontFamily: FONT.body }}>
      {/* --- Music bed: full reel length, low volume, ducks briefly on each reveal --- */}
      <Audio src={staticFile("quiz/music.mp3")} volume={musicVolume} />

      {/* --- Countdown ticks: one per second of each round's 5s countdown --- */}
      {TICK_FRAMES.map((f, i) => (
        <Sequence key={`tick-${f}`} from={f} durationInFrames={TICK_STEP} name={`Tick-${i % 5}`}>
          <Audio src={staticFile("quiz/tick.mp3")} volume={tickVolume(i % 5)} />
        </Sequence>
      ))}

      {/* --- Reveal impact: exactly at each round's reveal start --- */}
      {REVEAL_FRAMES.map((f, i) => (
        <Sequence key={`reveal-sfx-${f}`} from={f} durationInFrames={REVEAL_LEN} name={`RevealSfx-R${i + 1}`}>
          <Audio src={staticFile("quiz/reveal.mp3")} volume={0.8} />
        </Sequence>
      ))}

      {QUIZ_ROUNDS.map((round, i) => (
        <Sequence key={round.ticker} from={i * ROUND_LEN} durationInFrames={ROUND_LEN} name={`Round-${round.ticker}`}>
          <RoundScene round={round} roundIndex={i} />
        </Sequence>
      ))}
      <Sequence from={ROUND_LEN * QUIZ_ROUNDS.length} durationInFrames={END_LEN} name="EndCard">
        <Bg tint={C.mint} />
        <QuizEndCard />
      </Sequence>
    </AbsoluteFill>
  );
};
