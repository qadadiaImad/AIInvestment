import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { C, FONT, NOT_FATWA } from "./theme";
import { Bg, Caption, Foot, Kicker, Slam, clamp, easeOut, inOut, pop } from "./ui";
import { PortraitBubble } from "./IntroScenes";

// Beat constants (frames @30fps) — refined against Whisper timestamps of
// voice_toolbox.wav after generation (word_timestamps.json key "toolbox").
// Whisper-anchored (voice_toolbox.wav): "Number 1" 16.12s · "$80" 27.18 · "37%" 32.12 ·
// "read, not a call" 34.66 · "Number 2" 37.64 · "is 20" 48.16-48.82 · "Number 3" 56.4 ·
// "grew 15%" 59.74 · "Price vs the model" 69.34 · disclaimer 82.0-87.7 · ends 88.2
export const TOOLBOX_BEATS = {
  hook: { from: 6, dur: 478 },
  model: { from: 484, dur: 645 },
  pe: { from: 1129, dur: 563 },
  growth: { from: 1692, dur: 388 },
  close: { from: 2080 },
  total: 2680,
};

const B = TOOLBOX_BEATS;

/** Two price tags: market price vs model read, then a discount bar. */
const PriceTags: React.FC<{ from: number; from2: number; barFrom: number }> = ({ from, from2, barFrom }) => {
  const frame = useCurrentFrame();
  const p1 = interpolate(frame, [from, from + 14], [0, 1], { ...clamp, easing: pop });
  const p2 = interpolate(frame, [from2, from2 + 14], [0, 1], { ...clamp, easing: pop });
  const bar = interpolate(frame, [barFrom, barFrom + 50], [0, 0.37], { ...clamp, easing: inOut });
  const Tag: React.FC<{ label: string; price: string; color: string; p: number; rot: string }> = ({ label, price, color, p, rot }) => (
    <div
      style={{
        border: `4px solid ${color}`,
        background: `${color}14`,
        borderRadius: 20,
        padding: "26px 38px",
        opacity: p,
        scale: String(0.7 + 0.3 * p),
        rotate: rot,
      }}
    >
      <div style={{ fontFamily: FONT.mono, fontWeight: 600, fontSize: 24, letterSpacing: 3, color: C.muted }}>{label}</div>
      <div style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: 88, color, marginTop: 6 }}>{price}</div>
    </div>
  );
  return (
    <div>
      <div style={{ display: "flex", gap: 34, alignItems: "center" }}>
        <Tag label="THE MARKET" price="$50" color={C.ink === "#E8EDF2" ? "#E8EDF2" : C.ink} p={p1} rot="-2deg" />
        <div style={{ fontFamily: FONT.mono, fontSize: 44, color: C.muted, opacity: p2 }}>vs</div>
        <Tag label="MODEL'S READ" price="$80" color={C.emerald} p={p2} rot="2deg" />
      </div>
      <div style={{ marginTop: 44, opacity: interpolate(frame, [barFrom - 6, barFrom], [0, 1], clamp) }}>
        <div style={{ position: "relative", height: 40, background: C.panel, borderRadius: 12, border: `1.5px solid ${C.line}` }}>
          <div
            style={{
              position: "absolute", left: 0, top: 0, bottom: 0,
              width: `${bar * 100 * 2.2}%`,
              background: C.emeraldDeep, borderRadius: 12,
            }}
          />
        </div>
        <div style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: 40, color: C.mint, marginTop: 16 }}>
          {(bar * 100).toFixed(0)}% <span style={{ fontSize: 26, color: C.muted, fontWeight: 600 }}>BELOW THE MODEL</span>
        </div>
      </div>
    </div>
  );
};

/** P/E — a coin per "year of profit" stacking into rows of 10. */
const YearCoins: React.FC<{ from: number; count?: number; step?: number }> = ({ from, count = 20, step = 3 }) => {
  const frame = useCurrentFrame();
  return (
    <div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, maxWidth: 620 }}>
        {new Array(count).fill(0).map((_, i) => {
          const p = interpolate(frame, [from + i * step, from + i * step + 10], [0, 1], { ...clamp, easing: pop });
          return (
            <div
              key={i}
              style={{
                width: 52, height: 52, borderRadius: 26,
                background: `radial-gradient(circle at 35% 30%, ${C.mint}, ${C.emeraldDeep})`,
                border: `3px solid ${C.emerald}`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontFamily: FONT.mono, fontWeight: 800, fontSize: 20, color: C.bg,
                opacity: p,
                scale: String(p),
              }}
            >
              {i + 1}
            </div>
          );
        })}
      </div>
      <div
        style={{
          fontFamily: FONT.mono, fontWeight: 800, fontSize: 46, color: C.ink, marginTop: 30,
          opacity: interpolate(frame, [from + count * step + 8, from + count * step + 20], [0, 1], clamp),
        }}
      >
        P/E 20 <span style={{ fontSize: 27, color: C.muted, fontWeight: 600 }}>= PAYING FOR 20 YEARS OF TODAY&apos;S PROFIT</span>
      </div>
    </div>
  );
};

/** Revenue growth bars: three years, last one +15% highlighted. */
const GrowthBars: React.FC<{ from: number }> = ({ from }) => {
  const frame = useCurrentFrame();
  const heights = [150, 190, 240];
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 40, height: 300 }}>
      {heights.map((h, i) => {
        const p = interpolate(frame, [from + i * 16, from + i * 16 + 22], [0, 1], { ...clamp, easing: easeOut });
        const last = i === heights.length - 1;
        return (
          <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
            {last ? (
              <div style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: 40, color: C.mint, opacity: p }}>+15%</div>
            ) : null}
            <div
              style={{
                width: 120,
                height: h * p,
                background: last ? `linear-gradient(180deg, ${C.mint}, ${C.emeraldDeep})` : C.panel,
                border: `2px solid ${last ? C.emerald : C.line}`,
                borderRadius: 14,
              }}
            />
            <div style={{ fontFamily: FONT.mono, fontSize: 22, color: C.muted }}>{["2024", "2025", "2026"][i]}</div>
          </div>
        );
      })}
    </div>
  );
};

export const ToolboxVideo: React.FC<{ wide?: boolean }> = ({ wide = false }) => {
  const PAD = wide ? 100 : 84;
  const contentStyle: React.CSSProperties = wide
    ? { padding: PAD, paddingLeft: 470, justifyContent: "center" }
    : { padding: PAD, paddingBottom: 560, justifyContent: "center" };

  return (
    <AbsoluteFill style={{ fontFamily: FONT.body }}>
      <Bg />
      <Audio src={staticFile("voice_toolbox.wav")} />

      {/* S1 — hook */}
      <Sequence from={B.hook.from} durationInFrames={B.hook.dur} name="Hook">
        <AbsoluteFill style={contentStyle}>
          <Kicker text="KARIM EXPLAINS · HOW I READ A STOCK" />
          <div style={{ marginTop: 30 }}>
            <Slam size={wide ? 92 : 104} delay={95}>Every chart here</Slam>
            <Slam size={wide ? 92 : 104} color={C.emerald} delay={155}>
              comes down to
              <br />
              three numbers.
            </Slam>
          </div>
          <div style={{ marginTop: 50, maxWidth: 900 }}>
            <Caption delay={290}>
              Learn them once — read every post on this page. Meet{" "}
              <b style={{ color: C.emerald }}>Noor Inc.</b>, share price <b style={{ color: C.ink }}>$50</b>.
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S2 — price vs model */}
      <Sequence from={B.model.from} durationInFrames={B.model.dur} name="ModelRead">
        <AbsoluteFill style={contentStyle}>
          <Kicker text="NUMBER 1 — PRICE vs THE MODEL" />
          <div style={{ marginTop: 44 }}>
            <PriceTags from={20} from2={332} barFrom={470} />
          </div>
          <div style={{ marginTop: 40, maxWidth: 900 }}>
            <Caption delay={550}>
              Price is what you pay — the model&apos;s read is what it might be worth.{" "}
              <b style={{ color: C.amber }}>A read, not a call.</b>
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S3 — P/E */}
      <Sequence from={B.pe.from} durationInFrames={B.pe.dur} name="PE">
        <AbsoluteFill style={contentStyle}>
          <Kicker text="NUMBER 2 — THE P/E RATIO" />
          <div style={{ marginTop: 40 }}>
            <YearCoins from={128} step={10} />
          </div>
          <div style={{ marginTop: 40, maxWidth: 900 }}>
            <Caption delay={375}>
              $50 ÷ $2.50 of yearly profit = <b style={{ color: C.mint }}>20 years</b>. Lower means
              cheaper — <b style={{ color: C.amber }}>if the business holds</b>.
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S4 — growth */}
      <Sequence from={B.growth.from} durationInFrames={B.growth.dur} name="Growth">
        <AbsoluteFill style={contentStyle}>
          <Kicker text="NUMBER 3 — REVENUE GROWTH" />
          <div style={{ marginTop: 44 }}>
            <GrowthBars from={70} />
          </div>
          <div style={{ marginTop: 40, maxWidth: 900 }}>
            <Caption delay={170}>
              Marked down <b style={{ color: C.emerald }}>and still growing</b> — a very different story
              from shrinking.
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S5 — close */}
      <Sequence from={B.close.from} name="Close">
        <AbsoluteFill style={{ ...contentStyle, gap: 36 }}>
          <div style={{ display: "flex", gap: 18, flexWrap: "wrap" }}>
            {["PRICE vs MODEL", "YEARS OF PROFIT", "GROWTH"].map((t, i) => (
              <Sequence key={t} from={[0, 60, 104][i]} layout="none" name={"Chip" + i}>
                <div
                  style={{
                    fontFamily: FONT.mono, fontWeight: 700, fontSize: 30, letterSpacing: 2,
                    color: C.bg, background: i === 0 ? C.emerald : i === 1 ? C.mint : C.amber,
                    padding: "16px 26px", borderRadius: 14,
                  }}
                >
                  {t}
                </div>
              </Sequence>
            ))}
          </div>
          <div style={{ fontFamily: FONT.display, fontWeight: 600, fontSize: wide ? 56 : 62, color: C.ink, lineHeight: 1.14, maxWidth: 950 }}>
            The toolbox behind every AI &amp; quantum post here —
            <br />
            <span style={{ color: C.emerald }}>and every stock still walks through the halal screen first.</span>
          </div>
          <div style={{ fontFamily: FONT.mono, fontSize: 24, color: C.muted }}>
            A model&apos;s read is not a recommendation · {NOT_FATWA}
          </div>
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
