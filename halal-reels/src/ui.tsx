import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  OffthreadVideo,
  interpolate,
  random,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { C, FONT, NOT_FATWA } from "./theme";

export const easeOut = Easing.bezier(0.16, 1, 0.3, 1);
export const pop = Easing.bezier(0.34, 1.56, 0.64, 1);
export const inOut = Easing.bezier(0.45, 0, 0.55, 1);
/** True easeInOutCubic (cubic power curve, eased both ends) -- used for the
 * correlation demo's r-sweep + balance-marker morph so both glide smoothly
 * between holds instead of a linear/near-linear ramp. */
export const easeInOutCubic = Easing.inOut(Easing.cubic);

export const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

/** Ambient dark background: radial glow + slow-drifting emerald motes.
 * `driftSpeed` (default 1 = original behavior, unchanged for every existing
 * caller) scales both the vertical drift speed and adds a horizontal sway --
 * pass a higher value (e.g. CorrelationReel's synced-demo beat) to make the
 * motes read as more noticeably alive without touching any other reel. */
export const Bg: React.FC<{ tint?: string; driftSpeed?: number }> = ({ tint = C.emerald, driftSpeed = 1 }) => {
  const frame = useCurrentFrame();
  const motes = new Array(14).fill(0).map((_, i) => {
    const sway = (driftSpeed - 1) * 14 * Math.sin(frame * 0.008 * driftSpeed + i);
    const x = random(`mx${i}`) * 1080 + sway;
    const y = ((random(`my${i}`) * 2200 + frame * (0.3 + random(`ms${i}`)) * driftSpeed) % 2100) - 100;
    const s = 3 + random(`msz${i}`) * 7;
    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: x,
          top: 1920 - y,
          width: s,
          height: s,
          borderRadius: s,
          background: tint,
          opacity: 0.05 + random(`mo${i}`) * 0.1,
        }}
      />
    );
  });
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 90% 55% at 50% 8%, ${tint}14, transparent 60%), radial-gradient(ellipse 80% 50% at 50% 100%, #00000088, transparent)`,
        }}
      />
      {motes}
    </AbsoluteFill>
  );
};

/** Small mono kicker label, types in. */
export const Kicker: React.FC<{ text: string; color?: string }> = ({ text, color = C.emerald }) => {
  const frame = useCurrentFrame();
  const n = Math.round(interpolate(frame, [0, 18], [0, text.length], clamp));
  return (
    <div
      style={{
        fontFamily: FONT.mono,
        fontWeight: 700,
        fontSize: 30,
        letterSpacing: 6,
        color,
        minHeight: 40,
      }}
    >
      {text.slice(0, n)}
      <span style={{ opacity: frame % 16 < 8 && n < text.length ? 1 : 0 }}>▌</span>
    </div>
  );
};

/** Big display headline that slams in with overshoot. */
export const Slam: React.FC<{
  children: React.ReactNode;
  size?: number;
  color?: string;
  delay?: number;
}> = ({ children, size = 108, color = C.ink, delay = 0 }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [delay, delay + 16], [0, 1], { ...clamp, easing: pop });
  return (
    <div
      style={{
        fontFamily: FONT.display,
        fontWeight: 700,
        fontSize: size,
        lineHeight: 1.02,
        letterSpacing: -3,
        color,
        opacity: Math.min(1, p * 1.4),
        scale: String(0.7 + 0.3 * p),
        transformOrigin: "left bottom",
        textShadow: "0 8px 44px rgba(0,0,0,.55)",
      }}
    >
      {children}
    </div>
  );
};

/** Bottom caption line (plain-words explainer), fades/slides up. */
export const Caption: React.FC<{ children: React.ReactNode; delay?: number }> = ({
  children,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [delay, delay + 14], [0, 1], { ...clamp, easing: easeOut });
  return (
    <div
      style={{
        fontFamily: FONT.body,
        fontWeight: 500,
        fontSize: 44,
        lineHeight: 1.35,
        color: C.inkSoft,
        opacity: p,
        translate: `0px ${(1 - p) * 30}px`,
        textShadow: "0 2px 18px rgba(0,0,0,.8)",
      }}
    >
      {children}
    </div>
  );
};

export const Foot: React.FC<{ text?: string }> = ({ text = NOT_FATWA }) => (
  <div
    style={{
      fontFamily: FONT.mono,
      fontSize: 22,
      letterSpacing: 0.5,
      color: C.muted,
    }}
  >
    {text}
  </div>
);

/** Ticker header chip. */
export const Head: React.FC<{ tk: string; sub: string; badge: { text: string; color: string } }> = ({
  tk,
  sub,
  badge,
}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 14], [0, 1], { ...clamp, easing: easeOut });
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 26, opacity: p }}>
      <div>
        <div style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: 66, color: "#fff", lineHeight: 0.95 }}>
          {tk}
        </div>
        <div style={{ fontFamily: FONT.mono, fontWeight: 600, fontSize: 22, letterSpacing: 3, color: C.emerald, marginTop: 6 }}>
          {sub}
        </div>
      </div>
      <div
        style={{
          marginLeft: "auto",
          fontFamily: FONT.mono,
          fontWeight: 700,
          fontSize: 26,
          letterSpacing: 2,
          color: C.bg,
          background: badge.color,
          padding: "14px 22px",
          borderRadius: 14,
          translate: `0px ${(1 - p) * -30}px`,
        }}
      >
        {badge.text}
      </div>
    </div>
  );
};

/** Money counter + limit bar. Value counts up; breaching the cap shakes the frame and reddens the bar. */
export const LimitMeter: React.FC<{
  value: number; // final value
  cap: number;
  scaleMax: number;
  from: number; // frame the count starts
  countFrames?: number;
  fmt?: (v: number) => string;
  capLabel?: string;
  overLabel?: string;
}> = ({ value, cap, scaleMax, from, countFrames = 70, fmt = (v) => `$${v.toFixed(0)}`, capLabel, overLabel }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [from, from + countFrames], [0, 1], { ...clamp, easing: inOut });
  const v = p * value;
  const over = v > cap;
  const justOverP = interpolate(v, [cap, cap * 1.25], [0, 1], clamp);
  const shake = over ? Math.sin(frame * 2.6) * 6 * (1 - Math.min(1, (v - cap) / (value - cap + 0.001))) : 0;
  const capX = (cap / scaleMax) * 100;
  return (
    <div style={{ translate: `${shake}px 0px` }}>
      <div
        style={{
          fontFamily: FONT.mono,
          fontWeight: 800,
          fontSize: 190,
          lineHeight: 0.9,
          color: over ? C.redHot : C.ink,
          letterSpacing: -6,
        }}
      >
        {fmt(v)}
        {overLabel ? (
          <span
            style={{
              marginLeft: 28,
              fontFamily: FONT.mono,
              fontWeight: 700,
              fontSize: 34,
              letterSpacing: 2,
              color: C.bg,
              background: C.redHot,
              padding: "10px 18px",
              borderRadius: 12,
              verticalAlign: "middle",
              opacity: justOverP,
              display: over ? "inline-block" : "none",
              rotate: "-3deg",
            }}
          >
            {overLabel}
          </span>
        ) : null}
      </div>
      <div style={{ position: "relative", height: 46, marginTop: 44, background: C.panel, borderRadius: 12, border: `1.5px solid ${C.line}` }}>
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            bottom: 0,
            width: `${Math.min(100, (v / scaleMax) * 100)}%`,
            background: over ? C.redHot : C.emeraldDeep,
            borderRadius: 12,
          }}
        />
        <div
          style={{
            position: "absolute",
            left: `${capX}%`,
            top: -18,
            bottom: -18,
            borderLeft: `4px dashed ${over ? C.redHot : C.ink}`,
            opacity: 0.9,
          }}
        />
        <div
          style={{
            position: "absolute",
            left: `${capX}%`,
            top: -66,
            translate: "-50% 0px",
            fontFamily: FONT.mono,
            fontWeight: 700,
            fontSize: 26,
            color: over ? C.redHot : C.ink,
            whiteSpace: "nowrap",
          }}
        >
          {capLabel}
        </div>
      </div>
    </div>
  );
};

/** Verdict stamp — slams in rotated with a landing shake. */
export const Stamp: React.FC<{
  ok: boolean;
  label: string;
  detail?: string;
  delay: number;
}> = ({ ok, label, detail, delay }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [delay, delay + 10], [0, 1], { ...clamp, easing: pop });
  const land = interpolate(frame, [delay + 10, delay + 18], [1, 0], clamp);
  const color = ok ? C.emeraldDeep : C.redHot;
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 24,
        opacity: Math.min(1, p * 2),
        scale: String(1.6 - 0.6 * p),
        rotate: `${(1 - p) * -14 + Math.sin(frame * 3) * land * 2}deg`,
      }}
    >
      <div
        style={{
          width: 74,
          height: 74,
          borderRadius: 18,
          border: `5px solid ${color}`,
          color,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 44,
          fontWeight: 800,
          fontFamily: FONT.mono,
          background: `${color}22`,
        }}
      >
        {ok ? "✓" : "✕"}
      </div>
      <div>
        <div style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: 46, color: C.ink }}>{label}</div>
        {detail ? (
          <div style={{ fontFamily: FONT.mono, fontWeight: 600, fontSize: 26, color: C.muted, marginTop: 4 }}>{detail}</div>
        ) : null}
      </div>
    </div>
  );
};

/** Confetti burst (deterministic). */
export const Confetti: React.FC<{ from: number; count?: number }> = ({ from, count = 34 }) => {
  const frame = useCurrentFrame();
  const t = frame - from;
  if (t < 0) return null;
  const colors = [C.emerald, C.mint, C.amber, "#fff"];
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {new Array(count).fill(0).map((_, i) => {
        const a = random(`ca${i}`) * Math.PI - Math.PI; // upward-ish
        const speed = 14 + random(`cs${i}`) * 20;
        const x = 540 + Math.cos(a) * speed * Math.min(t, 26) * (0.7 + random(`cx${i}`));
        const y = 980 + Math.sin(a) * speed * Math.min(t, 26) + 0.5 * 1.6 * t * t;
        const o = interpolate(t, [0, 10, 55], [0, 1, 0], clamp);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: 12 + random(`cw${i}`) * 10,
              height: 8 + random(`ch${i}`) * 8,
              background: colors[i % colors.length],
              opacity: o,
              rotate: `${t * (8 + random(`cr${i}`) * 14)}deg`,
              borderRadius: 3,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** A coin that drops and bounces into a charity box (purification beat). */
export const CoinDrop: React.FC<{ from: number; label: string }> = ({ from, label }) => {
  const frame = useCurrentFrame();
  const t = Math.max(0, frame - from);
  const y = interpolate(t, [0, 22], [-360, 0], { ...clamp, easing: Easing.bounce });
  const coinIn = interpolate(frame, [from - 6, from], [0, 1], clamp);
  const boxP = interpolate(frame, [from - 10, from], [0, 1], { ...clamp, easing: easeOut });
  const settledP = interpolate(t, [22, 34], [0, 1], clamp);
  return (
    <div style={{ position: "relative", width: 560, height: 420 }}>
      <div
        style={{
          position: "absolute",
          left: 190,
          top: 40 + y,
          width: 180,
          height: 180,
          borderRadius: 90,
          background: `radial-gradient(circle at 35% 30%, ${C.mint}, ${C.emeraldDeep})`,
          border: `6px solid ${C.emerald}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: FONT.mono,
          fontWeight: 800,
          fontSize: 64,
          color: C.bg,
          boxShadow: "0 18px 50px rgba(0,0,0,.5)",
          opacity: coinIn,
        }}
      >
        {label}
      </div>
      <div
        style={{
          position: "absolute",
          left: 40,
          bottom: 0,
          width: 480,
          height: 210,
          borderRadius: 24,
          border: `5px solid ${C.amber}`,
          background: `${C.amber}18`,
          opacity: boxP,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: 0,
            left: "50%",
            translate: "-50% 0px",
            width: 260,
            height: 14,
            borderRadius: 8,
            background: C.amber,
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: 22,
            width: "100%",
            textAlign: "center",
            fontFamily: FONT.mono,
            fontWeight: 700,
            fontSize: 34,
            letterSpacing: 3,
            color: C.amber,
            opacity: 0.4 + settledP * 0.6,
          }}
        >
          CHARITY
        </div>
      </div>
    </div>
  );
};

/** Spinning wind turbine (GEV fun bit). */
export const Turbine: React.FC<{ size?: number }> = ({ size = 300 }) => {
  const frame = useCurrentFrame();
  return (
    <svg width={size} height={size * 1.3} viewBox="0 0 200 260">
      <line x1="100" y1="110" x2="100" y2="250" stroke={C.muted} strokeWidth="10" strokeLinecap="round" />
      <g style={{ transformOrigin: "100px 100px", rotate: `${frame * 3.2}deg` }}>
        {[0, 120, 240].map((a) => (
          <g key={a} style={{ transformOrigin: "100px 100px", rotate: `${a}deg` }}>
            <ellipse cx="100" cy="46" rx="11" ry="52" fill={C.emerald} opacity="0.92" />
          </g>
        ))}
        <circle cx="100" cy="100" r="14" fill={C.ink} />
      </g>
    </svg>
  );
};

/** End card. */
export const EndCard: React.FC<{
  badge: { text: string; color: string };
  line: string;
  date: string;
}> = ({ badge, line, date }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 16], [0, 1], { ...clamp, easing: easeOut });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 44, padding: 90 }}>
      <div
        style={{
          fontFamily: FONT.mono,
          fontWeight: 700,
          fontSize: 40,
          letterSpacing: 3,
          color: C.bg,
          background: badge.color,
          padding: "22px 38px",
          borderRadius: 18,
          scale: String(0.8 + 0.2 * p),
          opacity: p,
        }}
      >
        {badge.text}
      </div>
      <div
        style={{
          fontFamily: FONT.display,
          fontWeight: 600,
          fontSize: 66,
          lineHeight: 1.1,
          color: C.ink,
          textAlign: "center",
          opacity: p,
          maxWidth: 860,
        }}
      >
        {line}
      </div>
      <div style={{ fontFamily: FONT.mono, fontSize: 26, color: C.muted, opacity: p }}>
        THE HALAL SCREEN · data as of {date}
      </div>
      <div style={{ position: "absolute", bottom: 70, left: 90, right: 90, textAlign: "center" }}>
        <Foot />
      </div>
    </AbsoluteFill>
  );
};

// ---- SemisReel presentational units ----------------------------------------

/** Pinned white "sticker" hook caption (studied from the source reel): bold
 * near-black text with one gold keyword; pops in, then holds on screen. */
export const StickerHook: React.FC<{ pre: string; keyword: string; post?: string; from?: number }> = ({
  pre, keyword, post = "", from = 0,
}) => {
  const frame = useCurrentFrame();
  const s = interpolate(frame, [from, from + 12], [0.7, 1], { ...clamp, easing: pop });
  const o = interpolate(frame, [from, from + 10], [0, 1], clamp);
  return (
    <div style={{
      position: "absolute", top: 150, left: 0, right: 0, display: "flex", justifyContent: "center",
      opacity: o, transform: `scale(${s})`, zIndex: 6,
    }}>
      <div style={{
        maxWidth: 820, background: "#F4F6F8", borderRadius: 26, padding: "22px 34px",
        boxShadow: "0 18px 50px rgba(0,0,0,.55)", fontFamily: FONT.body, fontWeight: 800,
        fontSize: 62, lineHeight: 1.08, color: "#111418", textAlign: "center",
      }}>
        {pre} <span style={{ color: C.amber }}>{keyword}</span>{post}
      </div>
    </div>
  );
};

/** Burned rolling subtitle that advances per beat; optional "as reported" tag. */
export const RollingCaption: React.FC<{ text: string; from: number; asReported?: boolean }> = ({
  text, from, asReported = false,
}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [from, from + 12], [0, 1], clamp);
  const y = interpolate(frame, [from, from + 12], [22, 0], { ...clamp, easing: easeOut });
  return (
    <div style={{
      position: "absolute", bottom: 360, left: 60, right: 60, textAlign: "center",
      opacity: o, transform: `translateY(${y}px)`, zIndex: 6,
    }}>
      <div style={{
        fontFamily: FONT.display, fontWeight: 700, fontSize: 52, lineHeight: 1.2,
        color: C.ink, textShadow: "0 3px 22px rgba(0,0,0,.85)",
      }}>{text}</div>
      {asReported && (
        <div style={{
          marginTop: 14, fontFamily: FONT.mono, fontWeight: 700, fontSize: 20, letterSpacing: 1.5,
          color: C.muted, textShadow: "0 2px 10px rgba(0,0,0,.9)",
        }}>AS REPORTED · NOT INDEPENDENTLY VERIFIED</div>
      )}
    </div>
  );
};

/** Full-bleed Grok background (video or still) with a dark scrim + optional
 * slow Ken-Burns for stills. Charts/text sit above it. */
export const GrokClip: React.FC<{ src: string; kind: "video" | "image"; scrim?: string; kenBurns?: boolean }> = ({
  src, kind, scrim = "linear-gradient(180deg, rgba(10,13,18,.45) 0%, rgba(10,13,18,.35) 40%, rgba(10,13,18,.85) 100%)", kenBurns = true,
}) => {
  const frame = useCurrentFrame();
  const k = kenBurns && kind === "image" ? interpolate(frame, [0, 300], [1.06, 1.16], clamp) : 1;
  return (
    <AbsoluteFill>
      {kind === "video" ? (
        <OffthreadVideo src={staticFile(src)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : (
        <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${k})` }} />
      )}
      <AbsoluteFill style={{ background: scrim }} />
    </AbsoluteFill>
  );
};
