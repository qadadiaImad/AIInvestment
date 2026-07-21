import React from "react";
import { AbsoluteFill, Easing, Sequence, interpolate, useCurrentFrame } from "remotion";
import { DATE, WULF } from "./data";
import { C, FONT } from "./theme";
import { Bg, Caption, CoinDrop, EndCard, Foot, Head, Kicker, LimitMeter, Slam, Stamp, clamp } from "./ui";

const Donut: React.FC<{ pct: number; from: number }> = ({ pct, from }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [from, from + 55], [0, 1], { ...clamp, easing: Easing.bezier(0.45, 0, 0.55, 1) });
  const R = 150;
  const CIRC = 2 * Math.PI * R;
  const shown = p * (pct / 100);
  return (
    <div style={{ position: "relative", width: 380, height: 380 }}>
      <svg width="380" height="380" viewBox="0 0 380 380">
        <circle cx="190" cy="190" r={R} stroke={C.panel} strokeWidth="46" fill="none" />
        <circle
          cx="190"
          cy="190"
          r={R}
          stroke={C.amber}
          strokeWidth="46"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={CIRC}
          strokeDashoffset={CIRC * (1 - shown)}
          style={{ transformOrigin: "190px 190px", rotate: "-90deg" }}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: FONT.mono,
        }}
      >
        <div style={{ fontWeight: 800, fontSize: 84, color: C.amber }}>{(shown * 100).toFixed(1)}%</div>
        <div style={{ fontWeight: 600, fontSize: 24, color: C.muted, letterSpacing: 2 }}>BITCOIN MINING</div>
      </div>
    </div>
  );
};

const PAD = 84;

export const WulfReel: React.FC = () => {
  return (
    <AbsoluteFill style={{ fontFamily: FONT.body }}>
      <Bg tint={C.amber} />
      <AbsoluteFill style={{ padding: PAD }}>
        <Head tk="WULF" sub="AI DATACENTERS · NASDAQ" badge={WULF.badge} />
      </AbsoluteFill>

      {/* S1 — cold open */}
      <Sequence from={8} durationInFrames={92} name="Hook">
        <AbsoluteFill style={{ padding: PAD, justifyContent: "center" }}>
          <Slam size={118}>This stock earns</Slam>
          <Slam size={132} color={C.amber} delay={14}>
            bitcoin money.
          </Slam>
          <div style={{ marginTop: 60, maxWidth: 900 }}>
            <Caption delay={40}>
              Muslim investors run a <b style={{ color: C.emerald }}>halal screen</b> — a math test for
              stocks. Watch it work.
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S2 — debt counter */}
      <Sequence from={100} durationInFrames={150} name="DebtTest">
        <AbsoluteFill style={{ padding: PAD, justifyContent: "center", gap: 40 }}>
          <Kicker text="TEST 1 — THE DEBT" color={C.amber} />
          <LimitMeter
            value={57}
            cap={30}
            scaleMax={70}
            from={14}
            countFrames={75}
            capLabel="LIMIT $30"
            overLabel="OVER THE LIMIT"
          />
          <div style={{ marginTop: 30, maxWidth: 900 }}>
            <Caption delay={95}>
              Of every <b style={{ color: C.ink }}>$100</b> of company value, <b style={{ color: C.redHot }}>$57 is borrowed</b>.
              Islamic screens cap it at <b style={{ color: C.ink }}>$30</b>.
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S3 — three stamps */}
      <Sequence from={250} durationInFrames={100} name="Stamps">
        <AbsoluteFill style={{ padding: PAD, justifyContent: "center", gap: 46 }}>
          <Kicker text="THE RULEBOOKS AGREE" color={C.redHot} />
          {WULF.stamps.map((s, i) => (
            <Stamp key={s.name} ok={s.ok} label={s.name} detail={`${s.ratioPct}% vs cap ${s.capPct}%`} delay={8 + i * 22} />
          ))}
          <div style={{ maxWidth: 900 }}>
            <Caption delay={72}>Too much debt — in all three rulebooks.</Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S4 — bitcoin slice */}
      <Sequence from={350} durationInFrames={120} name="BitcoinSlice">
        <AbsoluteFill style={{ padding: PAD, justifyContent: "center", gap: 44, alignItems: "center" }}>
          <Kicker text="TEST 2 — THE BUSINESS" color={C.amber} />
          <Donut pct={WULF.miningPct} from={10} />
          <div style={{ maxWidth: 900 }}>
            <Caption delay={60}>
              <b style={{ color: C.amber }}>38%</b> of its income is still bitcoin mining — that slice is
              flagged <b style={{ color: C.redHot }}>impermissible</b>.
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S5 — purification */}
      <Sequence from={470} durationInFrames={92} name="Purification">
        <AbsoluteFill style={{ padding: PAD, justifyContent: "center", gap: 40, alignItems: "center" }}>
          <Kicker text="THE FIX HAS A NAME" />
          <CoinDrop from={16} label="13¢" />
          <div style={{ maxWidth: 920 }}>
            <Caption delay={40}>
              <b style={{ color: C.emerald }}>Purification</b>: the impure slice doesn&apos;t belong in your
              pocket — you give it to charity. Here: about <b style={{ color: C.mint }}>13¢ a share</b>.
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S6 — end card */}
      <Sequence from={562} name="EndCard">
        <Bg tint={C.amber} />
        <EndCard badge={WULF.badge} line="Real business. Flagged twice. Verdict: review." date={DATE} />
      </Sequence>

      <AbsoluteFill style={{ padding: PAD, justifyContent: "flex-end", pointerEvents: "none" }}>
        <Sequence from={0} durationInFrames={562} layout="none" name="Footer">
          <Foot />
        </Sequence>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
