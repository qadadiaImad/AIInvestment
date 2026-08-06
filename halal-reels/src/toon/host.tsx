/**
 * PremiumHost — a refined, modern flat-illustration news anchor to replace the
 * stick-figure rig. Still pure vector (100% frame-consistent), but with proper
 * proportions, gradient shading for volume, real eyes with highlights, a blazer,
 * and soft shadows. Parametric: mouth (talk), eyes (blink), browRaise, look.
 * Drawn in a 540x680 bust space (face centered ~270,250) so it drops into the
 * newsroom set. Palette-swappable via `theme`.
 */
import React from "react";

export type HostExpr = { mouth?: "rest" | "open" | "soft" | "flat"; blink?: boolean; brow?: number; look?: number };
export type HostTheme = { skin: string; skinShade: string; hair: string; hairHi: string; blazer: string; blazerShade: string; blouse: string; lip: string; ink: string; glasses?: boolean; masc?: boolean };

export const HOST_ANCHOR: HostTheme = {
  skin: "#F4C9A6", skinShade: "#E3AE86", hair: "#3B2A1E", hairHi: "#5A4130",
  blazer: "#8E3B5E", blazerShade: "#6E2A47", blouse: "#F3E7EE", lip: "#C56B7A", ink: "#2A2233",
};
export const HOST_ANALYST: HostTheme = {
  skin: "#F1C6A0", skinShade: "#DDA97F", hair: "#241A12", hairHi: "#3A2B1E",
  blazer: "#2E5E86", blazerShade: "#20486B", blouse: "#EAF0F6", lip: "#B77B6A", ink: "#22222E",
};
// masculine anchor — short crop, squarer jaw shading, muted lips (navy suit, red tie accent)
export const HOST_ANCHOR_M: HostTheme = {
  skin: "#E7B488", skinShade: "#CE9868", hair: "#241A12", hairHi: "#3C2C1E",
  blazer: "#2C4A6E", blazerShade: "#1E3653", blouse: "#EAF0F6", lip: "#A9765F", ink: "#20232E", masc: true,
};
export const HOST_QUANT: HostTheme = {
  skin: "#EEC49B", skinShade: "#D9A87C", hair: "#2A2018", hairHi: "#43342A",
  blazer: "#2F6F63", blazerShade: "#215248", blouse: "#EAF2EF", lip: "#B0765F", ink: "#20242A", glasses: true,
};

export const PremiumHost: React.FC<{ e?: HostExpr; theme?: HostTheme; id?: string }> = ({ e = {}, theme = HOST_ANCHOR, id = "h" }) => {
  const t = theme;
  const blink = e.blink;
  const lx = (e.look ?? 0); // eye look offset px
  const brow = e.brow ?? 0; // px raise
  const mouth = e.mouth ?? "rest";
  const masc = !!t.masc;
  const lipW = masc ? 7 : 9;
  const g = (s: string) => `${id}-${s}`;
  return (
    <g>
      <defs>
        <radialGradient id={g("skin")} cx="42%" cy="38%" r="70%">
          <stop offset="0%" stopColor={t.skin} />
          <stop offset="100%" stopColor={t.skinShade} />
        </radialGradient>
        <linearGradient id={g("hair")} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={t.hairHi} />
          <stop offset="100%" stopColor={t.hair} />
        </linearGradient>
        <linearGradient id={g("blazer")} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={t.blazer} />
          <stop offset="100%" stopColor={t.blazerShade} />
        </linearGradient>
        <filter id={g("soft")} x="-40%" y="-40%" width="180%" height="180%">
          <feDropShadow dx="0" dy="10" stdDeviation="14" floodColor="#000" floodOpacity="0.28" />
        </filter>
      </defs>

      {/* ---- body (behind head): sculpted shoulders, structured blazer ---- */}
      <g filter={`url(#${g("soft")})`}>
        {/* neck + under-chin shadow */}
        <path d="M242 348 L242 372 C242 412 298 412 298 372 L298 348 Z" fill={t.skinShade} />
        <ellipse cx="270" cy="356" rx="32" ry="13" fill="#000" opacity="0.12" />
        {/* torso / blazer */}
        <path d="M88 584 C88 444 168 394 270 394 C372 394 452 444 452 584 L452 680 L88 680 Z" fill={`url(#${g("blazer")})`} />
        {/* shoulder sheen */}
        <path d="M126 468 C168 430 216 414 270 414 C324 414 372 430 414 468" fill="none" stroke="#fff" strokeOpacity="0.10" strokeWidth="16" strokeLinecap="round" />
        {/* shirt V */}
        <path d="M234 400 L270 512 L306 400 L306 458 L270 502 L234 458 Z" fill={t.blouse} />
        {/* shirt collar */}
        <path d="M248 400 L270 452 L234 470 L222 428 Z" fill="#fff" opacity="0.9" />
        <path d="M292 400 L270 452 L306 470 L318 428 Z" fill="#fff" opacity="0.9" />
        {/* tie (masc) */}
        {masc && (
          <g>
            <path d="M258 404 L282 404 L276 424 L264 424 Z" fill="#B4322E" />
            <path d="M264 424 L276 424 L286 502 L270 520 L254 502 Z" fill="#9E2A26" />
          </g>
        )}
        {/* blazer lapels */}
        <path d="M234 398 L270 512 L238 532 L200 452 Z" fill={t.blazerShade} />
        <path d="M306 398 L270 512 L302 532 L340 452 Z" fill={t.blazerShade} />
        {/* placket buttons */}
        <circle cx="270" cy="540" r="5" fill={t.blazerShade} />
        <circle cx="270" cy="582" r="5" fill={t.blazerShade} />
        {/* lapel pin (brand accent) */}
        <circle cx="230" cy="486" r="7" fill="#E7B23B" stroke={t.ink} strokeWidth="2" />
      </g>

      {/* ---- hair back ---- */}
      {masc ? (
        // short back-and-sides: a cap that ends near ear level, with brief sideburns
        <path d="M158 262 C158 140 210 100 270 100 C330 100 382 140 382 262 L376 292 L360 262 C360 224 352 208 340 200 L200 200 C188 208 180 224 180 262 L164 292 Z" fill={`url(#${g("hair")})`} />
      ) : (
        <path d="M150 250 C150 132 200 96 270 96 C340 96 390 132 390 250 C390 330 372 372 356 404 L332 372 C348 320 344 250 344 250 L196 250 C196 250 192 320 208 372 L184 404 C168 372 150 330 150 250 Z" fill={`url(#${g("hair")})`} />
      )}

      {/* ---- head ---- */}
      <ellipse cx="270" cy="248" rx="104" ry="118" fill={`url(#${g("skin")})`} />
      {/* soft cheek + jaw shading */}
      <ellipse cx="270" cy="300" rx="92" ry="70" fill={t.skinShade} opacity="0.18" />
      {/* ears */}
      <ellipse cx="168" cy="256" rx="15" ry="22" fill={t.skinShade} />
      <ellipse cx="372" cy="256" rx="15" ry="22" fill={t.skinShade} />

      {/* ---- hair front ---- */}
      {masc ? (
        // short side part: crisp low hairline, small swept fringe
        <path d="M170 224 C172 138 216 104 270 104 C324 104 372 136 372 224 C356 198 332 184 304 182 C296 178 288 178 288 178 C270 168 236 176 214 198 C198 196 182 206 170 224 Z" fill={`url(#${g("hair")})`} />
      ) : (
        <path d="M166 236 C166 130 214 100 270 100 C326 100 374 130 374 236 C356 198 330 180 298 176 C304 194 304 200 304 200 C272 182 236 190 216 210 C198 208 180 218 166 236 Z" fill={`url(#${g("hair")})`} />
      )}

      {/* ---- brows (gentle raised arcs, well-separated) ---- */}
      <path d={`M206 ${203 - brow} q27 -11 53 -1`} fill="none" stroke={t.hair} strokeWidth="8" strokeLinecap="round" />
      <path d={`M281 ${203 - brow} q27 -11 53 1`} fill="none" stroke={t.hair} strokeWidth="8" strokeLinecap="round" />

      {/* ---- eyes ---- */}
      {blink ? (
        <>
          <path d="M214 240 q24 14 48 0" fill="none" stroke={t.ink} strokeWidth="6" strokeLinecap="round" />
          <path d="M278 240 q24 14 48 0" fill="none" stroke={t.ink} strokeWidth="6" strokeLinecap="round" />
        </>
      ) : (
        <>
          {/* left */}
          <ellipse cx="238" cy="240" rx="26" ry="20" fill="#fff" />
          <circle cx={238 + lx} cy="242" r="13" fill="#5A3A22" />
          <circle cx={238 + lx} cy="242" r="6.5" fill={t.ink} />
          <circle cx={242 + lx} cy="237" r="3.5" fill="#fff" />
          <path d="M212 226 q26 -10 52 2" fill="none" stroke={t.ink} strokeWidth="4.5" strokeLinecap="round" opacity="0.85" />
          {/* right */}
          <ellipse cx="302" cy="240" rx="26" ry="20" fill="#fff" />
          <circle cx={302 + lx} cy="242" r="13" fill="#5A3A22" />
          <circle cx={302 + lx} cy="242" r="6.5" fill={t.ink} />
          <circle cx={306 + lx} cy="237" r="3.5" fill="#fff" />
          <path d="M276 228 q26 -10 52 -2" fill="none" stroke={t.ink} strokeWidth="4.5" strokeLinecap="round" opacity="0.85" />
        </>
      )}

      {/* ---- glasses (optional) ---- */}
      {t.glasses && (
        <g stroke={t.ink} strokeWidth="6" fill="none" strokeLinecap="round">
          <circle cx="238" cy="242" r="33" fill="rgba(150,200,220,0.10)" />
          <circle cx="302" cy="242" r="33" fill="rgba(150,200,220,0.10)" />
          <path d="M271 238 q-1 -4 -2 0" />
          <path d="M205 240 q-16 -4 -30 4" />
          <path d="M335 240 q16 -4 30 4" />
        </g>
      )}

      {/* ---- nose ---- */}
      <path d="M268 250 q-8 26 -14 34 q10 8 22 2" fill="none" stroke={t.skinShade} strokeWidth="5" strokeLinecap="round" opacity="0.9" />

      {/* ---- cheeks / jaw ---- */}
      <ellipse cx="212" cy="292" rx="20" ry="12" fill={t.lip} opacity={masc ? 0.05 : 0.16} />
      <ellipse cx="328" cy="292" rx="20" ry="12" fill={t.lip} opacity={masc ? 0.05 : 0.16} />
      {masc && (
        <>
          {/* stubble / squarer jaw shading */}
          <ellipse cx="270" cy="322" rx="80" ry="46" fill="#39414f" opacity="0.10" />
          <path d="M186 262 C196 330 230 360 270 360 C310 360 344 330 354 262" fill="none" stroke={t.skinShade} strokeWidth="6" strokeLinecap="round" opacity="0.35" />
        </>
      )}

      {/* ---- mouth ---- */}
      {mouth === "open" ? (
        <>
          <path d="M244 316 q26 30 52 0 q-26 12 -52 0 Z" fill="#7A2E38" />
          <path d="M250 318 q20 6 40 0" fill="#fff" opacity="0.9" />
          <path d="M244 316 q26 -8 52 0" fill="none" stroke={t.lip} strokeWidth="6" strokeLinecap="round" />
        </>
      ) : mouth === "soft" ? (
        <path d="M246 314 q24 20 48 0" fill="none" stroke={t.lip} strokeWidth={lipW} strokeLinecap="round" />
      ) : mouth === "flat" ? (
        <path d="M248 316 l44 0" fill="none" stroke={t.lip} strokeWidth={lipW} strokeLinecap="round" />
      ) : (
        <path d="M248 314 q22 14 44 0" fill="none" stroke={t.lip} strokeWidth={lipW} strokeLinecap="round" />
      )}
    </g>
  );
};

// ---- preview composition (evaluate the new host) ----
import { AbsoluteFill } from "remotion";
export const HostPreview: React.FC = () => {
  const busts: [string, HostExpr, HostTheme][] = [
    ["neutral", { mouth: "soft" }, HOST_ANCHOR],
    ["talking", { mouth: "open", brow: 3 }, HOST_ANCHOR],
    ["anchor-M (talk)", { mouth: "open", brow: 2 }, HOST_ANCHOR_M],
    ["anchor-M", { mouth: "soft" }, HOST_ANCHOR_M],
  ];
  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg,#2b3040,#171a24)" }}>
      <svg width="1080" height="1350" viewBox="0 0 1080 1350">
        {busts.map(([label, e, th], i) => {
          const x = (i % 2) * 540 + 5;
          const y = Math.floor(i / 2) * 660 + 20;
          return (
            <g key={label} transform={`translate(${x} ${y}) scale(0.92)`}>
              <PremiumHost e={e} theme={th} id={"p" + i} />
              <text x="270" y="672" textAnchor="middle" fontFamily="monospace" fontSize="26" fill="#cfd6e2">{label}</text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
