// family.tsx — the AI STACK character family. Original mascots in a
// Kurzgesagt-INSPIRED flat-vector language (rounded geometry, big eyes,
// gentle constant motion) — designed from scratch, no traced trade dress.
// Every character is pure SVG + theme palette, animated off useCurrentFrame,
// so identity is code: same proportions in every render, forever.
//
// Shared DNA: 240×240 viewBox, ground line ~y=214, soft shadow, sine bob,
// periodic blink, one domain color per character.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C} from '../slides/theme';

export type CharKey = 'chip' | 'watt' | 'qubit' | 'cap' | 'nova' | 'cloudy';

export const CHARACTERS: {key: CharKey; name: string; role: string; tagline: string; color: string}[] = [
  {key: 'chip', name: 'Chip', role: 'Chips · L1', tagline: 'lives in the silicon layer — where the margins are made.', color: C.emerald},
  {key: 'watt', name: 'Watt', role: 'Energy · L0', tagline: "powers every model you've ever prompted.", color: C.amber},
  {key: 'qubit', name: 'Qubit', role: 'Quantum', tagline: 'in two minds about everything, always.', color: C.mint},
  {key: 'cap', name: 'Cap', role: 'Politics', tagline: "reads every filing — it's all public record.", color: C.redHot},
  {key: 'nova', name: 'Nova', role: 'AI Apps', tagline: 'turns models into products people pay for.', color: C.emeraldDeep},
  {key: 'cloudy', name: 'Cloudy', role: 'Neocloud · Infra', tagline: 'rents out the racks the boom runs on.', color: '#8fa2b8'},
];

/** Periodic blink: returns eye scaleY (1 open → 0.08 closed) on a ~4s cycle,
 * phase-shifted per character so the family never blinks in unison. */
const useBlink = (phase = 0) => {
  const frame = useCurrentFrame();
  const t = (frame + phase) % 120;
  if (t < 4) return 0.12;
  if (t < 8) return 1 - Math.abs(6 - t) * 0.22;
  return 1;
};

/** Gentle idle bob, phase-shifted per character. */
const useBob = (phase = 0, amp = 4) => {
  const frame = useCurrentFrame();
  return Math.sin((frame + phase * 13) / 22) * amp;
};

const Eye: React.FC<{cx: number; cy: number; blink: number; look?: number; pupil?: string}> = ({cx, cy, blink, look = 0, pupil = '#10141c'}) => (
  <g transform={`translate(${cx} ${cy}) scale(1 ${blink})`}>
    <ellipse cx="0" cy="0" rx="14.5" ry="17" fill="#FDFEFF" />
    <circle cx={look} cy="2.5" r="6.4" fill={pupil} />
    <circle cx={look + 2.2} cy="0.2" r="2" fill="#FDFEFF" opacity="0.9" />
  </g>
);

const Smile: React.FC<{x: number; y: number; w?: number; open?: boolean}> = ({x, y, w = 34, open = false}) =>
  open ? (
    <ellipse cx={x} cy={y} rx={9} ry={11} fill="#10141c" />
  ) : (
    <path d={`M${x - w / 2},${y} Q${x},${y + 13} ${x + w / 2},${y}`} fill="none" stroke="#10141c" strokeWidth="5" strokeLinecap="round" />
  );

const Shadow: React.FC<{bob: number}> = ({bob}) => (
  <ellipse cx="120" cy="220" rx={62 - bob * 2} ry={10 - bob * 0.6} fill="#000" opacity="0.28" />
);

// ---------------------------------------------------------------- Chip (L1)
export const ChipChar: React.FC<{size?: number}> = ({size = 240}) => {
  const blink = useBlink(0);
  const bob = useBob(0);
  const frame = useCurrentFrame();
  const antennaGlow = 0.55 + Math.sin(frame / 14) * 0.35;
  return (
    <svg width={size} height={size} viewBox="0 0 240 240">
      <Shadow bob={bob} />
      <g transform={`translate(0 ${bob})`}>
        {/* side + bottom pins */}
        <g fill="#caa64a">
          {[92, 116, 140].map((x) => (
            <rect key={`b${x}`} x={x} y="196" width="12" height="18" rx="4" />
          ))}
          {[96, 126, 156].map((y) => (
            <React.Fragment key={`s${y}`}>
              <rect x="44" y={y} width="18" height="12" rx="4" />
              <rect x="178" y={y} width="18" height="12" rx="4" />
            </React.Fragment>
          ))}
        </g>
        {/* antenna */}
        <line x1="120" y1="72" x2="120" y2="44" stroke={C.emeraldDeep} strokeWidth="7" strokeLinecap="round" />
        <circle cx="120" cy="38" r="9" fill={C.mint} opacity={antennaGlow} />
        <circle cx="120" cy="38" r="4.5" fill="#FDFEFF" opacity={antennaGlow} />
        {/* body */}
        <defs>
          <linearGradient id="chipBody" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={C.emerald} />
            <stop offset="1" stopColor={C.emeraldDeep} />
          </linearGradient>
        </defs>
        <rect x="58" y="70" width="124" height="132" rx="26" fill="url(#chipBody)" />
        {/* circuit traces */}
        <g stroke="#FDFEFF" strokeWidth="3.5" opacity="0.28" fill="none" strokeLinecap="round">
          <path d="M74,178 L96,178 L96,166" />
          <path d="M166,178 L146,178 L146,168" />
          <circle cx="96" cy="162" r="3.4" fill="#FDFEFF" stroke="none" />
          <circle cx="146" cy="164" r="3.4" fill="#FDFEFF" stroke="none" />
        </g>
        <Eye cx={97} cy={118} blink={blink} look={1.5} />
        <Eye cx={143} cy={118} blink={blink} look={1.5} />
        <Smile x={120} y={155} />
      </g>
    </svg>
  );
};

// --------------------------------------------------------------- Watt (L0)
export const WattChar: React.FC<{size?: number}> = ({size = 240}) => {
  const blink = useBlink(31);
  const bob = useBob(2, 5);
  const frame = useCurrentFrame();
  const sparkPulse = 0.4 + Math.abs(Math.sin(frame / 11)) * 0.6;
  return (
    <svg width={size} height={size} viewBox="0 0 240 240">
      <Shadow bob={bob} />
      <g transform={`translate(0 ${bob})`}>
        <defs>
          <linearGradient id="wattBody" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#F2C05C" />
            <stop offset="1" stopColor={C.amber} />
          </linearGradient>
        </defs>
        {/* chunky rounded bolt body — head wide enough to carry the face */}
        <path
          d="M104,34 Q100,26 110,26 L166,26 Q176,26 172,36 L146,98 L164,98 Q174,98 167,108 L96,208 Q88,218 84,206 Q82,201 84,196 L108,132 L90,132 Q80,132 84,122 Z"
          fill="url(#wattBody)"
          stroke="#c9821f"
          strokeWidth="4"
          strokeLinejoin="round"
        />
        {/* sparks */}
        <g stroke={C.amber} strokeWidth="5" strokeLinecap="round" opacity={sparkPulse}>
          <path d="M186,64 L198,64 M192,58 L192,70" />
          <path d="M54,84 L64,84 M59,79 L59,89" />
          <path d="M172,144 L182,144" />
        </g>
        <Eye cx={116} cy={62} blink={blink} look={-2} />
        <Eye cx={148} cy={64} blink={blink} look={-2} />
        <Smile x={130} y={92} w={26} />
      </g>
    </svg>
  );
};

// -------------------------------------------------------------- Qubit (Q)
export const QubitChar: React.FC<{size?: number}> = ({size = 240}) => {
  const blink = useBlink(57);
  const bob = useBob(4, 6);
  const frame = useCurrentFrame();
  const split = Math.sin(frame / 30) * 10; // superposition echoes drift apart
  const orbitA = frame * 0.05;
  const ex = Math.cos(orbitA) * 86;
  const ey = Math.sin(orbitA) * 30;
  return (
    <svg width={size} height={size} viewBox="0 0 240 240">
      <Shadow bob={bob} />
      <g transform={`translate(0 ${bob})`}>
        {/* superposition echoes */}
        <circle cx={120 - 10 - split} cy="138" r="60" fill={C.mint} opacity="0.20" />
        <circle cx={120 + 10 + split} cy="138" r="60" fill={C.emerald} opacity="0.16" />
        <defs>
          <radialGradient id="qubitBody" cx="0.38" cy="0.32" r="0.9">
            <stop offset="0" stopColor="#b8f4dd" />
            <stop offset="1" stopColor={C.mint} />
          </radialGradient>
        </defs>
        <circle cx="120" cy="138" r="60" fill="url(#qubitBody)" />
        {/* orbit ring + electron */}
        <g transform="translate(120 138) rotate(-18)">
          <ellipse cx="0" cy="0" rx="88" ry="32" fill="none" stroke="#FDFEFF" strokeWidth="3" opacity="0.35" />
          <circle cx={ex} cy={ey} r="7" fill={C.amber} />
          <circle cx={ex} cy={ey} r="11" fill={C.amber} opacity="0.3" />
        </g>
        <Eye cx={100} cy={130} blink={blink} pupil="#0d3327" />
        <Eye cx={140} cy={130} blink={blink} pupil="#0d3327" />
        <Smile x={120} y={162} open />
      </g>
    </svg>
  );
};

// ---------------------------------------------------------------- Cap (Gov)
export const CapChar: React.FC<{size?: number}> = ({size = 240}) => {
  const blink = useBlink(83);
  const bob = useBob(6, 3);
  const frame = useCurrentFrame();
  const flagWave = Math.sin(frame / 16) * 4;
  return (
    <svg width={size} height={size} viewBox="0 0 240 240">
      <Shadow bob={bob} />
      <g transform={`translate(0 ${bob})`}>
        <defs>
          <linearGradient id="capBody" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#FDFEFF" />
            <stop offset="1" stopColor="#cfd9e4" />
          </linearGradient>
        </defs>
        {/* flag */}
        <line x1="120" y1="56" x2="120" y2="24" stroke="#9aa7b5" strokeWidth="5" strokeLinecap="round" />
        <path d={`M123,26 Q${138 + flagWave},30 152,27 L152,45 Q${138 + flagWave},48 123,44 Z`} fill={C.redHot} />
        <rect x="123" y="26" width="29" height="7" fill="#1c2c55" />
        {/* cupola + dome */}
        <rect x="106" y="54" width="28" height="14" rx="6" fill="#cfd9e4" />
        <path d="M54,196 A66,74 0 0 1 186,196 Z" fill="url(#capBody)" />
        {/* column hints */}
        <g stroke="#aebccb" strokeWidth="6" strokeLinecap="round" opacity="0.85">
          <line x1="84" y1="172" x2="84" y2="194" />
          <line x1="108" y1="166" x2="108" y2="194" />
          <line x1="132" y1="166" x2="132" y2="194" />
          <line x1="156" y1="172" x2="156" y2="194" />
        </g>
        {/* base */}
        <rect x="48" y="196" width="144" height="16" rx="7" fill="#b9c6d4" />
        <Eye cx={100} cy={136} blink={blink} pupil="#22304a" />
        <Eye cx={140} cy={136} blink={blink} pupil="#22304a" />
        <Smile x={120} y={160} w={28} />
        {/* little bowtie */}
        <path d="M112,180 L120,185 L112,190 Z" fill={C.redHot} />
        <path d="M128,180 L120,185 L128,190 Z" fill={C.redHot} />
        <circle cx="120" cy="185" r="2.6" fill="#8c2f2c" />
      </g>
    </svg>
  );
};

// --------------------------------------------------------------- Nova (Apps)
export const NovaChar: React.FC<{size?: number}> = ({size = 240}) => {
  const blink = useBlink(19);
  const bob = useBob(8, 4);
  const frame = useCurrentFrame();
  const twinkle = 0.5 + Math.sin(frame / 9) * 0.5;
  const star = (cx: number, cy: number, r: number, o: number) => (
    <path
      d={`M${cx},${cy - r} Q${cx + r * 0.22},${cy - r * 0.22} ${cx + r},${cy} Q${cx + r * 0.22},${cy + r * 0.22} ${cx},${cy + r} Q${cx - r * 0.22},${cy + r * 0.22} ${cx - r},${cy} Q${cx - r * 0.22},${cy - r * 0.22} ${cx},${cy - r} Z`}
      fill={C.amber}
      opacity={o}
    />
  );
  return (
    <svg width={size} height={size} viewBox="0 0 240 240">
      <Shadow bob={bob} />
      <g transform={`translate(0 ${bob})`}>
        <defs>
          <linearGradient id="novaBody" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#233047" />
            <stop offset="1" stopColor="#131b2a" />
          </linearGradient>
        </defs>
        {/* app-icon body with chat tail */}
        <rect x="60" y="64" width="120" height="120" rx="32" fill="url(#novaBody)" stroke={C.emerald} strokeWidth="4" />
        <path d="M84,180 L74,206 L106,184 Z" fill="#131b2a" stroke={C.emerald} strokeWidth="4" strokeLinejoin="round" />
        {/* sparkles */}
        {star(178, 62, 16, twinkle)}
        {star(52, 104, 9, 1 - twinkle * 0.6)}
        {star(190, 140, 7, 0.4 + twinkle * 0.5)}
        <Eye cx={98} cy={116} blink={blink} look={2} pupil="#0b1020" />
        <Eye cx={142} cy={116} blink={blink} look={2} pupil="#0b1020" />
        <Smile x={120} y={150} w={30} />
      </g>
    </svg>
  );
};

// ------------------------------------------------------------- Cloudy (Infra)
export const CloudyChar: React.FC<{size?: number}> = ({size = 240}) => {
  const blink = useBlink(101);
  const bob = useBob(10, 6);
  const frame = useCurrentFrame();
  const lights = [C.emerald, C.amber, C.redHot].map((c, i) => ({c, on: Math.sin(frame / 10 + i * 2.1) > -0.2}));
  return (
    <svg width={size} height={size} viewBox="0 0 240 240">
      <Shadow bob={bob} />
      <g transform={`translate(0 ${bob})`}>
        <defs>
          <linearGradient id="cloudBody" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#b6c5d6" />
            <stop offset="1" stopColor="#8fa2b8" />
          </linearGradient>
        </defs>
        {/* puffy cloud body */}
        <g fill="url(#cloudBody)">
          <circle cx="86" cy="130" r="44" />
          <circle cx="132" cy="106" r="52" />
          <circle cx="168" cy="142" r="38" />
          <rect x="52" y="130" width="150" height="52" rx="26" />
        </g>
        {/* server light strip */}
        <rect x="92" y="160" width="76" height="16" rx="8" fill="#5c6b7e" />
        {lights.map((l, i) => (
          <circle key={i} cx={106 + i * 24} cy="168" r="5" fill={l.c} opacity={l.on ? 1 : 0.25} />
        ))}
        <Eye cx={108} cy={124} blink={blink} pupil="#2a3646" />
        <Eye cx={148} cy={124} blink={blink} pupil="#2a3646" />
        <Smile x={128} y={146} w={26} />
      </g>
    </svg>
  );
};

export const CHAR_COMPONENTS: Record<CharKey, React.FC<{size?: number}>> = {
  chip: ChipChar,
  watt: WattChar,
  qubit: QubitChar,
  cap: CapChar,
  nova: NovaChar,
  cloudy: CloudyChar,
};
