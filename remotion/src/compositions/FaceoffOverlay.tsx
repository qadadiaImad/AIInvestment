// FaceoffOverlay.tsx — slide 1 of the "Two Balance Sheets" carousel: the
// Higgsfield heart installation with pixel-perfect stat overlays burned into
// the top corners. Static (no animation) — rendered as a still. Numbers from
// site.json as of 2026-07-11; NET (chained heart, left) vs CRDO (rose heart,
// right).
import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {z} from 'zod';
import {FONT} from '../slides/theme';

export const faceoffOverlaySchema = z.object({
  img: z.string(),
});
export type FaceoffOverlayProps = z.infer<typeof faceoffOverlaySchema>;

const INK = '#12161d';
const MUTED = '#5b6470';
const RED = '#C0463F';
const GREEN = '#0E9E6E';

type Row = {label: string; value: string; tone?: 'red' | 'green'};

const StatBlock: React.FC<{
  align: 'left' | 'right';
  ticker: string;
  name: string;
  rows: Row[];
  verdict: string;
  verdictTone: 'red' | 'green';
}> = ({align, ticker, name, rows, verdict, verdictTone}) => (
  <div
    style={{
      position: 'absolute',
      top: 52,
      [align]: 52,
      width: 476,
      display: 'flex',
      flexDirection: 'column',
      alignItems: align === 'left' ? 'flex-start' : 'flex-end',
      textAlign: align,
      // white halo on every glyph: invisible on the lit wall, lifts text off
      // the sculptures where a block would sit over dark metal / white roses
      textShadow: '0 0 6px rgba(255,255,255,0.95), 0 1px 2px rgba(255,255,255,0.95), 0 0 14px rgba(255,255,255,0.7)',
      padding: '16px 20px',
    }}
  >
    <div style={{display: 'flex', alignItems: 'baseline', gap: 12, flexDirection: align === 'right' ? 'row-reverse' : 'row'}}>
      <span style={{fontFamily: FONT.mono, fontWeight: 800, fontSize: 52, letterSpacing: 2, color: INK}}>{ticker}</span>
      <span style={{fontFamily: FONT.body, fontWeight: 500, fontSize: 27, color: MUTED}}>{name}</span>
    </div>
    <div style={{width: '82%', height: 2, background: INK, opacity: 0.32, margin: '12px 0 14px'}} />
    <div style={{display: 'flex', flexDirection: 'column', gap: 7, width: '100%'}}>
      {rows.map((r) => (
        <div
          key={r.label}
          style={{display: 'flex', flexDirection: align === 'right' ? 'row-reverse' : 'row', justifyContent: 'space-between', width: '100%'}}
        >
          <span style={{fontFamily: FONT.body, fontWeight: 500, fontSize: 25, color: MUTED}}>{r.label}</span>
          <span
            style={{
              fontFamily: FONT.mono,
              fontWeight: 800,
              fontSize: 27,
              color: r.tone === 'red' ? RED : r.tone === 'green' ? GREEN : INK,
            }}
          >
            {r.value}
          </span>
        </div>
      ))}
    </div>
    <div
      style={{
        marginTop: 14,
        fontFamily: FONT.mono,
        fontWeight: 800,
        fontSize: 22,
        letterSpacing: 0.3,
        whiteSpace: 'nowrap',
        color: verdictTone === 'red' ? RED : GREEN,
      }}
    >
      {verdict}
    </div>
  </div>
);

export const FaceoffOverlay: React.FC<FaceoffOverlayProps> = ({img}) => (
  <AbsoluteFill style={{background: '#f4f5f7'}}>
    <Img src={staticFile(img)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />

    {/* LEFT — NET (the chained heart) */}
    <StatBlock
      align="left"
      ticker="NET"
      name="Cloudflare"
      rows={[
        {label: 'Net margin', value: '−3.7%', tone: 'red'},
        {label: 'ROIC', value: '−2.7%', tone: 'red'},
        {label: 'Debt / equity', value: '2.31', tone: 'red'},
        {label: 'Revenue', value: '+32% YoY'},
        {label: 'Price', value: '1.6× fair'},
      ]}
      verdict="✕ UNPROFITABLE · LEVERAGED"
      verdictTone="red"
    />

    {/* RIGHT — CRDO (the blooming heart) */}
    <StatBlock
      align="right"
      ticker="CRDO"
      name="Credo"
      rows={[
        {label: 'Net margin', value: '+35.4%', tone: 'green'},
        {label: 'ROIC', value: '+34.0%', tone: 'green'},
        {label: 'Debt / equity', value: '0.01', tone: 'green'},
        {label: 'Revenue', value: '+206% YoY'},
        {label: 'Price', value: '1.2× fair'},
      ]}
      verdict="✓ PROFITABLE · DEBT-FREE"
      verdictTone="green"
    />
  </AbsoluteFill>
);
