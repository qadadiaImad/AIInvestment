import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {brand} from '../brand';

export const DecisiveNumber: React.FC<{valuePct: number; thresholdPct: number; label: string}> =
({valuePct, thresholdPct, label}) => {
  const frame = useCurrentFrame();
  const v = interpolate(frame, [0, 60], [0, valuePct], {extrapolateRight: 'clamp'});
  const over = v > thresholdPct;
  return (
    <div style={{textAlign: 'left'}}>
      <div style={{fontFamily: brand.fontBig, fontSize: 220, fontWeight: 600, lineHeight: 1,
        color: over ? brand.fail : brand.text, transition: 'color 0.2s'}}>
        {v.toFixed(2)}%
      </div>
      <div style={{fontFamily: brand.fontMono, fontSize: 30, color: brand.muted, marginTop: 12}}>
        {label} · limit {thresholdPct.toFixed(1)}%
      </div>
    </div>
  );
};
