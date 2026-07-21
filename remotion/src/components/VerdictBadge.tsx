import React from 'react';
import {brand} from '../brand';

const LABELS = {halal: 'HALAL', not_halal: 'NOT HALAL', questionable: 'QUESTIONABLE', insufficient_data: 'INSUFFICIENT DATA'} as const;
const TONES = {halal: brand.pass, not_halal: brand.fail, questionable: brand.warn, insufficient_data: brand.muted} as const;

export const VerdictBadge: React.FC<{overall: keyof typeof LABELS; basis: string}> = ({overall, basis}) => (
  <div style={{display: 'inline-flex', flexDirection: 'column', alignItems: 'flex-start', gap: 8}}>
    <div style={{
      fontFamily: brand.fontMono, fontSize: 44, fontWeight: 700, letterSpacing: 2,
      color: brand.bg, background: TONES[overall], padding: '10px 28px', borderRadius: 12,
    }}>{LABELS[overall]}</div>
    <div style={{fontFamily: brand.fontMono, fontSize: 24, color: brand.muted}}>basis: {basis}</div>
  </div>
);
