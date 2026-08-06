/**
 * Scroll-stopping COVER / thumbnail for the debt reel. Curiosity-gap trigger: the giant
 * live debt number + "TO WHO?" + a tease that the answer subverts expectations. Reuses the
 * male anchor + Debt Clock so the cover matches the episode. Render as a still:
 *   npx remotion still QuarterlyReportDebtCover out/debt_cover.png --frame=40
 */
import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { PremiumHost, HOST_ANCHOR_M } from "./toon/host";
import { DebtClock } from "./toon/props";
import { FUN, BODY, PAL, MoneyMotif, isBlink } from "./toon/reelkit";

export const QR_DEBT_COVER_BEATS = { total: 60 };

export const QuarterlyReportDebtCover: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: "radial-gradient(120% 88% at 50% 20%, #16233a 0%, #0a0f18 55%, #04060b 100%)" }}>
      <MoneyMotif f={f} tint={PAL.gold} base={0.07} />

      {/* brand bug */}
      <div style={{ position: "absolute", left: 44, top: 46, fontFamily: BODY, fontWeight: 800, fontSize: 30, color: PAL.paper, letterSpacing: 1, textShadow: "0 2px 8px #000" }}>
        V<span style={{ color: PAL.mint }}>&amp;</span>V · QUARTERLY REPORT
      </div>

      {/* alarm/segment badge */}
      <div style={{ position: "absolute", top: 150, left: 0, right: 0, textAlign: "center" }}>
        <span style={{ background: "#D63A34", color: "#fff", fontFamily: BODY, fontWeight: 900, fontSize: 32, padding: "12px 26px", borderRadius: 10, letterSpacing: 2, boxShadow: "0 6px 20px rgba(214,58,52,.4)" }}>● FOLLOW THE MONEY</span>
      </div>

      {/* headline */}
      <div style={{ position: "absolute", top: 244, left: 40, right: 40, textAlign: "center", fontFamily: BODY, fontWeight: 900, fontSize: 66, color: PAL.paper, lineHeight: 1.02, textShadow: "0 4px 16px #000" }}>
        THE WHOLE WORLD<br />IS IN DEBT
      </div>

      {/* the live number (the shock) */}
      <svg width="1080" height="150" viewBox="0 0 1080 150" style={{ position: "absolute", top: 452 }}>
        <g transform="translate(150 6)"><DebtClock f={f + 700} digitSize={40} label="RISING EVERY SECOND" /></g>
      </svg>

      {/* the trigger — curiosity gap */}
      <div style={{ position: "absolute", top: 636, left: 20, right: 20, textAlign: "center" }}>
        <div style={{ fontFamily: BODY, fontWeight: 900, fontSize: 46, color: PAL.mint, textShadow: "0 2px 10px #000" }}>…but you owe it</div>
        <div style={{ fontFamily: FUN, fontSize: 210, color: PAL.red, WebkitTextStroke: "8px #000", paintOrder: "stroke", lineHeight: 0.86, marginTop: 4 }}>TO WHO?</div>
      </div>

      {/* the anchor — raised + enlarged to close the gap under the hook */}
      <svg width="1080" height="1160" viewBox="0 0 1080 1160" style={{ position: "absolute", bottom: 0 }}>
        <g transform="translate(162 -70) scale(1.4)">
          <PremiumHost e={{ mouth: "soft", brow: 2, blink: isBlink(f) }} theme={HOST_ANCHOR_M} id="cov" />
        </g>
      </svg>

      {/* tease */}
      <div style={{ position: "absolute", bottom: 64, left: 0, right: 0, textAlign: "center", fontFamily: BODY, fontWeight: 900, fontSize: 38, color: PAL.paper, textShadow: "0 3px 12px #000" }}>
        the answer isn't who you think 👀
      </div>
    </AbsoluteFill>
  );
};
