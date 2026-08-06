/**
 * reelkit — shared UI for the V&V Quarterly Report episodes (karaoke, bug, disclaimer,
 * chyron, source tag, studio host wrapper, big reaction face). Keeps each episode file
 * thin: an episode = VO/captions + a back-wall viz + scene text + these primitives.
 */
import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { PremiumHost, HostTheme } from "./host";
import { loadFont as loadLuckiest } from "@remotion/google-fonts/LuckiestGuy";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";

const luckiest = loadLuckiest("normal", { weights: ["400"], subsets: ["latin"] });
const inter = loadInter("normal", { weights: ["700", "800", "900"], subsets: ["latin"] });
export const FUN = luckiest.fontFamily;
export const BODY = inter.fontFamily;
export const PAL = { gold: "#E7B23B", mint: "#7FE9C2", red: "#E0524D", green: "#34D399", ink: "#141414", paper: "#FFF6E9" };

export const isBlink = (f: number) => { const c = f % 78; return c < 4 || (c > 40 && c < 44); };
export const flap = (f: number) => Math.floor(f / 4) % 2 === 0;

type Cap = { words: { w: string; t0: number; t1: number }[]; dur: number };
// `max` chunks a long line into subtitle-sized groups (shows only the group around the
// currently-spoken word) so multi-second VO lines don't bury the frame in text. Default
// shows the whole line (short-beat episodes are unaffected).
// `reveal` makes words pop in one-by-one as they're spoken (no pre-shown dim ghosts);
// `max` chunks a long line into subtitle-sized groups so it never buries the frame.
export const Karaoke: React.FC<{ caps: Record<string, Cap>; id: string; cue: number; bottom?: number; hot?: RegExp; max?: number; reveal?: boolean }> = ({ caps, id, cue, bottom = 205, hot = /[0-9]/, max = 100, reveal = false }) => {
  const f = useCurrentFrame();
  const cap = caps[id];
  if (!cap) return null;
  const tt = (f - cue) / 30;
  if (tt < -0.15 || tt > cap.dur + 0.4) return null;
  const all = cap.words;
  let shown = all;
  if (all.length > max) {
    let ai = all.findIndex((w) => tt >= w.t0 && tt < w.t1);
    if (ai < 0) ai = tt >= all[all.length - 1].t1 ? all.length - 1 : 0;
    const base = Math.floor(ai / max) * max;
    shown = all.slice(base, base + max);
  }
  return (
    <div style={{ position: "absolute", left: 50, right: 50, bottom, textAlign: "center", lineHeight: 1.16, zIndex: 4 }}>
      {shown.map((w, i) => {
        if (reveal && tt < w.t0) return null; // not spoken yet → not on screen
        const active = tt >= w.t0 && tt < w.t1;
        const spoken = tt >= w.t1;
        const pop = active && reveal ? interpolate(f - cue - w.t0 * 30, [0, 4], [0.6, 1.1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : active ? 1.1 : 1;
        const color = active ? (hot.test(w.w) ? PAL.gold : PAL.mint) : spoken ? PAL.paper : "rgba(255,246,233,0.5)";
        return <span key={i} style={{ display: "inline-block", margin: "4px 10px", fontFamily: BODY, fontWeight: 900, fontSize: 54, color, WebkitTextStroke: `3px ${PAL.ink}`, paintOrder: "stroke", transform: `scale(${pop})`, textShadow: "0 6px 16px rgba(0,0,0,.5)" }}>{w.w}</span>;
      })}
    </div>
  );
};

export const Bug: React.FC = () => (
  <div style={{ position: "absolute", left: 40, top: 40, fontFamily: BODY, fontWeight: 800, fontSize: 26, color: PAL.paper, letterSpacing: 1, textShadow: "0 2px 8px #000", zIndex: 5 }}>V<span style={{ color: PAL.mint }}>&amp;</span>V · QUARTERLY REPORT</div>
);
export const Disclaimer: React.FC<{ text: string }> = ({ text }) => (
  <div style={{ position: "absolute", left: 0, right: 0, bottom: 108, textAlign: "center", fontFamily: BODY, fontWeight: 700, fontSize: 21, color: "#DfE5Ec", textShadow: "0 1px 8px #000", zIndex: 6 }}>{text}</div>
);
export const Chyron: React.FC<{ f: number; tag: string; text: string; red?: boolean }> = ({ f, tag, text, red = true }) => {
  const x = interpolate(f, [4, 16], [1200, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const blink = Math.floor(f / 12) % 2 === 0;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 96, transform: `translateX(${x}px)`, display: "flex", alignItems: "center", zIndex: 5 }}>
      <div style={{ background: red ? (blink ? "#D63A34" : "#8f1f1b") : "#1f4b8f", color: "#fff", fontFamily: BODY, fontWeight: 900, fontSize: 30, padding: "12px 20px" }}>● {tag}</div>
      <div style={{ background: "rgba(10,13,18,.92)", color: "#fff", fontFamily: BODY, fontWeight: 800, fontSize: 30, padding: "12px 22px" }}>{text}</div>
    </div>
  );
};
export const Source: React.FC<{ t: string }> = ({ t }) => (
  <div style={{ position: "absolute", left: 0, right: 0, bottom: 140, textAlign: "center", fontFamily: BODY, fontWeight: 700, fontSize: 19, color: "#A9B3C0", textShadow: "0 1px 8px #000", zIndex: 6 }}>{t}</div>
);

export const studioHost = (f: number, theme: HostTheme, mouthTalk = true) => (
  <g transform={`translate(0 ${Math.sin(f / 12) * 3})`}>
    <PremiumHost e={{ mouth: mouthTalk && flap(f) ? "open" : "rest", blink: isBlink(f), brow: 1 }} theme={theme} id="rk" />
  </g>
);

// big reaction head (empathetic / deadpan, no comedic shake)
export const BigFace: React.FC<{ theme: HostTheme; f: number; mouth?: "flat" | "soft" | "open"; brow?: number }> = ({ theme, f, mouth = "flat", brow = -1 }) => (
  <svg width="760" height="820" viewBox="0 0 760 820">
    <g transform="translate(-52 -90) scale(1.62)"><PremiumHost e={{ mouth, brow, blink: isBlink(f) }} theme={theme} id="rkbig" /></g>
  </svg>
);
