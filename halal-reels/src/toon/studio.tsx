/**
 * NewsStudio — a broadcast news-studio set (replaces the flat grey Newsroom):
 * dark studio, a back video-wall with a dotted world map + ambient chart screens
 * + station logo, a modern branded anchor desk with folded hands, a floating main
 * stat screen, and a scrolling LIVE ticker. Pure SVG. Pass the host node, the main
 * screen content, ticker text, an accent color, the skin tone (for hands), and f.
 */
import React from "react";

const BODY = "system-ui, sans-serif";

const MiniBars: React.FC<{ c: string }> = ({ c }) => (
  <g>{[0, 1, 2, 3, 4].map((i) => <rect key={i} x={10 + i * 20} y={60 - (i % 3) * 14 - 12} width="13" height={(i % 3) * 14 + 24} rx="2" fill={c} opacity={0.85} />)}</g>
);
const MiniLine: React.FC<{ c: string }> = ({ c }) => (
  <polyline points="8,66 30,40 52,52 74,24 96,34" fill="none" stroke={c} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
);

export const NewsStudio: React.FC<{
  host: React.ReactNode; screen: React.ReactNode; ticker: string; accent: string; skin: string; f: number;
}> = ({ host, screen, ticker, accent, skin, f }) => {
  const scroll = -((f * 3) % 1680);
  return (
    <svg width="1080" height="1920" viewBox="0 0 1080 1920">
      <defs>
        <radialGradient id="st-bg" cx="50%" cy="20%" r="90%">
          <stop offset="0%" stopColor="#1b2536" />
          <stop offset="60%" stopColor="#111a29" />
          <stop offset="100%" stopColor="#0a1017" />
        </radialGradient>
        <linearGradient id="st-desk" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#243246" />
          <stop offset="100%" stopColor="#141d2b" />
        </linearGradient>
        <linearGradient id="st-floor" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#0c131d" />
          <stop offset="100%" stopColor="#060a10" />
        </linearGradient>
        <filter id="st-glow" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="0" stdDeviation="14" floodColor={accent} floodOpacity="0.5" /></filter>
      </defs>

      {/* studio background */}
      <rect x="0" y="0" width="1080" height="1920" fill="url(#st-bg)" />
      <rect x="0" y="1180" width="1080" height="740" fill="url(#st-floor)" />

      {/* ---- back video wall ---- */}
      <rect x="44" y="96" width="992" height="1000" rx="22" fill="#0b1220" stroke="#1f2c42" strokeWidth="3" />
      {/* dotted world-map field */}
      <g fill="#2b4066" opacity="0.55">
        {Array.from({ length: 9 }).map((_, r) =>
          Array.from({ length: 22 }).map((_, c) => {
            const on = (r * 7 + c * 3) % 5 < 2 && !(r > 2 && r < 6 && c > 7 && c < 14);
            return on ? <circle key={`${r}-${c}`} cx={90 + c * 42} cy={150 + r * 66} r="4.5" /> : null;
          })
        )}
      </g>
      {/* ambient chart screens (top corners) */}
      <g transform="translate(96 150)"><rect x="-10" y="-8" width="128" height="92" rx="8" fill="#0e1a2c" stroke="#243a5a" strokeWidth="2" /><MiniBars c="#4ea1ff" /></g>
      <g transform="translate(872 150)"><rect x="-10" y="-8" width="128" height="92" rx="8" fill="#0e1a2c" stroke="#243a5a" strokeWidth="2" /><MiniLine c={accent} /></g>
      {/* station logo bug on the wall */}
      <g transform="translate(452 148)">
        <rect x="0" y="0" width="176" height="60" rx="10" fill="#0e1a2c" stroke="#263a5a" strokeWidth="2" />
        <text x="88" y="40" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="30" fill="#fff">V<tspan fill={accent}>&amp;</tspan>V</text>
      </g>

      {/* ---- host (behind desk) ---- */}
      <g transform="translate(88 560) scale(1.16)">{host}</g>

      {/* ---- floating main stat screen (right) ---- */}
      <g transform="translate(598 706)" filter="url(#st-glow)">
        <rect x="0" y="0" width="436" height="330" rx="16" fill="#0a1220" stroke={accent} strokeWidth="3" />
        <rect x="0" y="0" width="436" height="46" rx="16" fill={accent} />
        <rect x="0" y="30" width="436" height="16" fill={accent} />
        <text x="22" y="32" fontFamily={BODY} fontWeight="800" fontSize="24" fill="#0a1220">● LIVE DATA</text>
        <g transform="translate(3 52)">{screen}</g>
      </g>

      {/* ---- anchor desk ---- */}
      <path d="M0 1180 C0 1180 0 1180 0 1180 L1080 1180 L1080 1300 C1080 1360 900 1392 540 1392 C180 1392 0 1360 0 1300 Z" fill="url(#st-desk)" />
      <rect x="0" y="1180" width="1080" height="8" fill={accent} opacity="0.85" />
      {/* desk front lit panel + logo */}
      <rect x="360" y="1226" width="360" height="120" rx="12" fill="#0e1826" stroke="#25344c" strokeWidth="2" />
      <text x="540" y="1300" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="46" fill="#fff" letterSpacing="2">V<tspan fill={accent}>&amp;</tspan>V</text>
      <rect x="410" y="1316" width="260" height="4" rx="2" fill={accent} />
      {/* folded hands on the desk */}
      <g transform="translate(300 1150)">
        <path d="M-4 40 C-40 30 -70 44 -78 70 L4 70 Z" fill={skin} opacity="0.98" />
        <path d="M188 40 C224 30 254 44 262 70 L180 70 Z" fill={skin} opacity="0.98" />
        <ellipse cx="92" cy="60" rx="70" ry="20" fill={skin} />
        <ellipse cx="92" cy="52" rx="66" ry="15" fill="#000" opacity="0.06" />
      </g>

      {/* ---- ticker ---- */}
      <rect x="0" y="1834" width="1080" height="86" fill="#0a0f18" />
      <g transform={`translate(${210 + scroll} 0)`}>
        <text x="0" y="1888" fontFamily={BODY} fontWeight="700" fontSize="32" fill="#cfd8e6">{ticker}</text>
        <text x="1680" y="1888" fontFamily={BODY} fontWeight="700" fontSize="32" fill="#cfd8e6">{ticker}</text>
      </g>
      {/* LIVE badge drawn on top so the scroll disappears behind it */}
      <rect x="0" y="1834" width="196" height="86" fill="#D63A34" />
      <text x="98" y="1888" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="34" fill="#fff">● LIVE</text>
      <rect x="196" y="1834" width="6" height="86" fill={accent} />
    </svg>
  );
};
