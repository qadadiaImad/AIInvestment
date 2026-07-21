import React from "react";
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame, Audio, staticFile } from "remotion";
import { DATE, GEV } from "./data";
import { C, FONT } from "./theme";
import { Bg, Caption, Confetti, EndCard, Foot, Head, Kicker, LimitMeter, Slam, Stamp, Turbine, clamp, easeOut, pop } from "./ui";

const ThatsIt: React.FC<{ from: number }> = ({ from }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [from, from + 12], [0, 1], { ...clamp, easing: pop });
  return (
    <div
      style={{
        fontFamily: FONT.display,
        fontStyle: "italic",
        fontWeight: 600,
        fontSize: 66,
        color: C.mint,
        opacity: p,
        rotate: `${(1 - p) * -6 - 2}deg`,
        translate: `0px ${(1 - p) * 40}px`,
      }}
    >
      …that&apos;s it. that&apos;s the debt.
    </div>
  );
};

const Sparkle: React.FC<{ from: number }> = ({ from }) => {
  const frame = useCurrentFrame();
  const pulse = 1 + Math.sin(Math.max(0, frame - from) / 5) * 0.04;
  const p = interpolate(frame, [from, from + 14], [0, 1], { ...clamp, easing: easeOut });
  return (
    <div
      style={{
        fontFamily: FONT.mono,
        fontWeight: 800,
        fontSize: 210,
        letterSpacing: -8,
        color: C.mint,
        opacity: p,
        scale: String(p * pulse),
        textShadow: `0 0 80px ${C.emerald}66`,
      }}
    >
      $0.00
    </div>
  );
};

const PAD = 84;
// Beat-synced (voice_gev.wav): "On the halal screen" 8.12 ; "Borrowed money about $3.50"
// 12.8-14.5 ; "limit of 30" 16.3-17.7 ; "business clean / nothing to purify / zero
// dollars" 19.0-22.9 ; "All three rulebooks say pass" 23.9-25.3. Narration purifies
// BEFORE the rulebook sweep, so Purify precedes Stamps (r1 had them swapped).

export const GevReel: React.FC = () => {
  return (
    <AbsoluteFill style={{ fontFamily: FONT.body }}>
      <Bg />
      <Audio src={staticFile("voice_gev.wav")} />
      <AbsoluteFill style={{ padding: PAD }}>
        <Head tk="GEV" sub="POWER EQUIPMENT · NYSE" badge={GEV.badge} />
      </AbsoluteFill>

      {/* S1 — hook + turbine */}
      <Sequence from={8} durationInFrames={235} name="Hook">
        <AbsoluteFill style={{ padding: PAD, justifyContent: "center" }}>
          <div style={{ position: "absolute", right: 40, top: 380, opacity: 0.9 }}>
            <Turbine size={330} />
          </div>
          <div style={{ maxWidth: 760 }}>
            <Slam size={110}>The AI boom runs on power.</Slam>
            <Slam size={110} color={C.emerald} delay={18}>
              This company builds it.
            </Slam>
          </div>
          <div style={{ marginTop: 60, maxWidth: 880 }}>
            <Caption delay={48}>
              GE Vernova makes the turbines behind AI datacenters. Now —{" "}
              <b style={{ color: C.emerald }}>the halal screen</b>.
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S2 — tiny debt (the joke) */}
      <Sequence from={243} durationInFrames={328} name="DebtTest">
        <AbsoluteFill style={{ padding: PAD, justifyContent: "center", gap: 40 }}>
          <Kicker text="THE DEBT TEST" />
          <LimitMeter
            value={GEV.debtDollars}
            cap={GEV.capDollars}
            scaleMax={70}
            from={140}
            countFrames={45}
            fmt={(v) => `$${v.toFixed(2)}`}
            capLabel="LIMIT $30"
          />
          <ThatsIt from={200} />
          <div style={{ marginTop: 12, maxWidth: 900 }}>
            <Caption delay={250}>
              Borrowed money: <b style={{ color: C.mint }}>$3.50</b> of every $100 of company value. The
              cap is <b style={{ color: C.ink }}>$30</b>.
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S4 — nothing to purify */}
      <Sequence from={571} durationInFrames={137} name="Purify">
        <AbsoluteFill style={{ padding: PAD, justifyContent: "center", gap: 34, alignItems: "center" }}>
          <Kicker text="NOTHING TO PURIFY" />
          <Sparkle from={60} />
          <div style={{ maxWidth: 900 }}>
            <Caption delay={80}>
              Clean business, no impure income — <b style={{ color: C.mint }}>nothing owed to charity</b>.
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S3 — clean sweep stamps + confetti */}
      <Sequence from={708} durationInFrames={90} name="Stamps">
        <AbsoluteFill style={{ padding: PAD, justifyContent: "center", gap: 46 }}>
          <Kicker text="ALL THREE RULEBOOKS" />
          {GEV.stamps.map((s, i) => (
            <Stamp key={s.name} ok={s.ok} label={s.name} detail={`${s.ratioPct}% vs cap ${s.capPct}%`} delay={6 + i * 16} />
          ))}
          <div style={{ maxWidth: 900 }}>
            <Caption delay={55}>
              A <b style={{ color: C.emerald }}>clean sweep</b> — every ratio test, passed.
            </Caption>
          </div>
        </AbsoluteFill>
        <Confetti from={50} />
      </Sequence>


      {/* S5 — end card */}
      <Sequence from={798} name="EndCard">
        <Bg />
        <EndCard badge={GEV.badge} line="The cleanest name on this week's screen." date={DATE} />
      </Sequence>

      <AbsoluteFill style={{ padding: PAD, justifyContent: "flex-end", pointerEvents: "none" }}>
        <Sequence from={0} durationInFrames={798} layout="none" name="Footer">
          <Foot />
        </Sequence>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
