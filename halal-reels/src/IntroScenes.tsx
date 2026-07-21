import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { C, FONT, NOT_FATWA } from "./theme";
import { Bg, Caption, CoinDrop, Foot, Kicker, Slam, Stamp, clamp, easeOut, pop } from "./ui";

// Beat constants (frames @30fps) — refined against Whisper word timestamps of
// voice_intro.wav after generation (see word_timestamps.json key "intro").
export const INTRO_BEATS = {
  // Whisper-anchored (word_timestamps.json "intro"): "Halal finance" 11.44s ·
  // "So how do you check" 25.38 · "1." 30.28 · "2." 38.48 · "3." 47.7 ·
  // "Pass all three" 54.46 · "One more idea" 59.02 · "And remember" 80.74 · ends 91.8
  hook: { from: 6, dur: 337 },
  filter: { from: 343, dur: 418 },
  screen: { from: 761, dur: 1010 },
  purify: { from: 1771, dur: 651 },
  close: { from: 2422 },
  total: 2790,
};

const B = INTRO_BEATS;

/** Karim podcast bubble — breathing portrait + pulsing emerald ring. */
export const PortraitBubble: React.FC<{ wide: boolean }> = ({ wide }) => {
  const frame = useCurrentFrame();
  const size = wide ? 300 : 340;
  const enter = interpolate(frame, [10, 30], [0, 1], { ...clamp, easing: pop });
  const breathe = 1 + 0.012 * Math.sin(frame / 16);
  const pulse = (frame % 46) / 46;
  const pos: React.CSSProperties = wide
    ? { left: 90, bottom: 70 }
    : { right: 64, bottom: 170 };
  return (
    <div style={{ position: "absolute", ...pos, width: size, height: size, scale: String(enter * breathe) }}>
      <div
        style={{
          position: "absolute",
          inset: -18 - pulse * 26,
          borderRadius: "50%",
          border: `3px solid ${C.emerald}`,
          opacity: (1 - pulse) * 0.5,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: "50%",
          overflow: "hidden",
          border: `5px solid ${C.emerald}`,
          boxShadow: "0 18px 60px rgba(0,0,0,.55)",
        }}
      >
        <Img
          src={staticFile("karim.png")}
          style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "50% 12%" }}
        />
      </div>
      <div
        style={{
          position: "absolute",
          bottom: -54,
          width: "100%",
          textAlign: "center",
          fontFamily: FONT.mono,
          fontWeight: 700,
          fontSize: 24,
          letterSpacing: 3,
          color: C.emerald,
        }}
      >
        KARIM
      </div>
    </div>
  );
};

const XChip: React.FC<{ label: string; delay: number }> = ({ label, delay }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [delay, delay + 12], [0, 1], { ...clamp, easing: pop });
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 18,
        border: `3px solid ${C.redHot}`,
        background: `${C.redHot}18`,
        borderRadius: 16,
        padding: "18px 26px",
        opacity: p,
        scale: String(0.7 + 0.3 * p),
        rotate: `${(1 - p) * -6}deg`,
      }}
    >
      <span style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: 40, color: C.redHot }}>✕</span>
      <span style={{ fontFamily: FONT.mono, fontWeight: 700, fontSize: 34, letterSpacing: 2, color: C.ink }}>{label}</span>
    </div>
  );
};

/** Mini visualizations for the three screen questions. */
const MiniDonut: React.FC<{ active: boolean }> = ({ active }) => {
  const frame = useCurrentFrame();
  const p = active ? interpolate(frame % 1000, [0, 1000], [1, 1]) : 1;
  const R = 44;
  const CIRC = 2 * Math.PI * R;
  return (
    <svg width="120" height="120" viewBox="0 0 120 120">
      <circle cx="60" cy="60" r={R} stroke={C.panel} strokeWidth="18" fill="none" />
      <circle
        cx="60" cy="60" r={R} stroke={C.amber} strokeWidth="18" fill="none" strokeLinecap="round"
        strokeDasharray={CIRC} strokeDashoffset={CIRC * (1 - 0.05 * p)}
        style={{ transformOrigin: "60px 60px", rotate: "-90deg" }}
      />
      <text x="60" y="70" textAnchor="middle" fill={C.amber} fontFamily={FONT.mono} fontWeight="800" fontSize="28">5%</text>
    </svg>
  );
};

const MiniBar: React.FC = () => (
  <div style={{ width: 150 }}>
    <div style={{ position: "relative", height: 22, background: C.panel, borderRadius: 7 }}>
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: "43%", background: C.emeraldDeep, borderRadius: 7 }} />
      <div style={{ position: "absolute", left: "43%", top: -8, bottom: -8, borderLeft: `3px dashed ${C.ink}` }} />
    </div>
    <div style={{ fontFamily: FONT.mono, fontWeight: 700, fontSize: 24, color: C.ink, marginTop: 12 }}>
      $30 <span style={{ color: C.muted, fontSize: 20 }}>/ $100 cap</span>
    </div>
  </div>
);

const MiniVault: React.FC = () => (
  <div
    style={{
      fontFamily: FONT.mono, fontWeight: 800, fontSize: 30, color: C.ink,
      border: `3px solid ${C.emerald}`, borderRadius: 14, padding: "14px 20px", background: `${C.emerald}14`,
    }}
  >
    CASH <span style={{ color: C.muted }}>→</span> capped
  </div>
);

const QTile: React.FC<{
  n: number; q: string; a: string; viz: React.ReactNode; from: number; activeUntil: number; wide: boolean;
}> = ({ n, q, a, viz, from, activeUntil, wide }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [from, from + 16], [0, 1], { ...clamp, easing: easeOut });
  const active = frame >= from && frame < activeUntil;
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 30,
        border: `2.5px solid ${active ? C.emerald : C.line}`,
        background: active ? "rgba(52,211,153,.07)" : C.panel,
        borderRadius: 22,
        padding: wide ? "26px 34px" : "30px 36px",
        opacity: p,
        translate: `${(1 - p) * 120}px 0px`,
      }}
    >
      <div
        style={{
          fontFamily: FONT.display, fontWeight: 700, fontSize: 64, color: active ? C.emerald : C.muted,
          minWidth: 56,
        }}
      >
        {n}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: wide ? 34 : 38, color: C.ink, letterSpacing: 1 }}>{q}</div>
        <div style={{ fontFamily: FONT.body, fontSize: wide ? 26 : 29, color: C.inkSoft, marginTop: 8, lineHeight: 1.35 }}>{a}</div>
      </div>
      {viz}
    </div>
  );
};

export const IntroVideo: React.FC<{ wide?: boolean }> = ({ wide = false }) => {
  const PAD = wide ? 100 : 84;
  const contentStyle: React.CSSProperties = wide
    ? { padding: PAD, paddingLeft: 470, justifyContent: "center" }
    : { padding: PAD, paddingBottom: 560, justifyContent: "center" };

  return (
    <AbsoluteFill style={{ fontFamily: FONT.body }}>
      <Bg />
      <Audio src={staticFile("voice_intro.wav")} />

      {/* S1 — hook */}
      <Sequence from={B.hook.from} durationInFrames={B.hook.dur} name="Hook">
        <AbsoluteFill style={contentStyle}>
          <Kicker text="KARIM EXPLAINS · HALAL INVESTING" />
          <div style={{ marginTop: 30 }}>
            <Slam size={wide ? 96 : 108} delay={100}>Grow your money.</Slam>
            <Slam size={wide ? 96 : 108} color={C.emerald} delay={125}>
              Without trading away
              <br />
              what you believe.
            </Slam>
          </div>
          <div style={{ marginTop: 50, maxWidth: 900 }}>
            <Caption delay={280}>In plain words — no jargon, no lecture.</Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S2 — the filter */}
      <Sequence from={B.filter.from} durationInFrames={B.filter.dur} name="Filter">
        <AbsoluteFill style={contentStyle}>
          <Kicker text="WHAT IT IS" />
          <div style={{ marginTop: 26 }}>
            <Slam size={wide ? 88 : 100}>
              Halal finance
              <br />
              <em style={{ fontStyle: "italic", color: C.emerald }}>is a filter.</em>
            </Slam>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 22, marginTop: 56, maxWidth: 720 }}>
            <XChip label="INTEREST-BASED EARNINGS" delay={143} />
            <XChip label="GAMBLING & HARAM INDUSTRIES" delay={175} />
            <XChip label="CASINO-STYLE DEBT BETS" delay={290} />
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S3 — the screen: three questions */}
      <Sequence from={B.screen.from} durationInFrames={B.screen.dur} name="Screen">
        <AbsoluteFill style={contentStyle}>
          <Kicker text="THE SCREEN — THREE QUESTIONS" />
          <div style={{ display: "flex", flexDirection: "column", gap: 26, marginTop: 44, maxWidth: wide ? 1150 : 912 }}>
            <QTile n={1} q="WHAT DOES IT SELL?" a="Impure income stays under about 5% — or it's flagged." viz={<MiniDonut active />} from={147} activeUntil={393} wide={wide} />
            <QTile n={2} q="HOW MUCH DOES IT BORROW?" a="Borrowed money under about $30 of every $100 of value." viz={<MiniBar />} from={393} activeUntil={670} wide={wide} />
            <QTile n={3} q="WHERE DOES CASH SIT?" a="Interest-bearing balances get capped the same way." viz={<MiniVault />} from={670} activeUntil={872} wide={wide} />
          </div>
          <div style={{ marginTop: 44 }}>
            <Sequence from={872} layout="none" name="ClearsBeat">
              <div style={{ display: "flex", gap: 26, alignItems: "center" }}>
                {[0, 1, 2].map((i) => (
                  <Stamp key={i} ok label={["SELLS", "BORROWS", "CASH"][i]} delay={i * 10} />
                ))}
              </div>
            </Sequence>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S4 — purification */}
      <Sequence from={B.purify.from} durationInFrames={B.purify.dur} name="Purify">
        <AbsoluteFill style={{ ...contentStyle, alignItems: wide ? "flex-start" : "center" }}>
          <Kicker text="ONE MORE IDEA — PURIFICATION" />
          <div style={{ marginTop: 40 }}>
            <CoinDrop from={330} label="¢" />
          </div>
          <div style={{ maxWidth: 900, marginTop: 40 }}>
            <Caption delay={90}>
              The small impure slice doesn&apos;t belong in your pocket — you compute it{" "}
              <b style={{ color: C.mint }}>per share</b> and give it to charity.
            </Caption>
          </div>
          <Sequence from={525} layout="none" name="Recap">
            <div
              style={{
                fontFamily: FONT.display, fontWeight: 700, fontSize: wide ? 64 : 76, color: C.ink, marginTop: 46,
              }}
            >
              Screen. Own. <em style={{ fontStyle: "italic", color: C.emerald }}>Purify.</em>
            </div>
          </Sequence>
        </AbsoluteFill>
      </Sequence>

      {/* S5 — close */}
      <Sequence from={B.close.from} name="Close">
        <AbsoluteFill style={{ ...contentStyle, alignItems: wide ? "flex-start" : "center", gap: 40 }}>
          <div
            style={{
              fontFamily: FONT.mono, fontWeight: 700, fontSize: 34, letterSpacing: 3, color: C.bg,
              background: C.emerald, padding: "20px 34px", borderRadius: 16,
            }}
          >
            THE HALAL SCREEN
          </div>
          <div style={{ fontFamily: FONT.display, fontWeight: 600, fontSize: wide ? 60 : 68, color: C.ink, textAlign: wide ? "left" : "center", lineHeight: 1.12, maxWidth: 950 }}>
            Computed results — not fatwas.
            <br />
            <span style={{ color: C.emerald }}>For your situation, ask a scholar.</span>
          </div>
          <div style={{ fontFamily: FONT.mono, fontSize: 24, color: C.muted }}>{NOT_FATWA}</div>
        </AbsoluteFill>
      </Sequence>

      <PortraitBubble wide={wide} />

      <AbsoluteFill style={{ padding: PAD, paddingLeft: wide ? 470 : PAD, justifyContent: "flex-end", pointerEvents: "none" }}>
        <Sequence from={0} durationInFrames={B.close.from} layout="none" name="Footer">
          <Foot />
        </Sequence>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
