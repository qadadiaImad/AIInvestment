import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {brand} from '../brand';
import type {z} from 'zod';
import type {testResultSchema} from '../props';

type TestResult = z.infer<typeof testResultSchema>;
const TONE = {pass: brand.pass, fail: brand.fail, unknown: brand.muted} as const;

const Bar: React.FC<{label: string; frac: number; status: keyof typeof TONE; delay: number; detail: string}> =
({label, frac, status, delay, detail}) => {
  const frame = useCurrentFrame();
  const w = interpolate(frame, [delay, delay + 45], [0, Math.min(frac, 1.6) * 62.5], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  }); // threshold sits at 62.5% of track width => frac 1.0
  return (
    <div style={{marginBottom: 34}}>
      <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: brand.fontMono,
        fontSize: 26, color: brand.text, marginBottom: 8}}>
        <span>{label}</span><span style={{color: TONE[status]}}>{detail}</span>
      </div>
      <div style={{position: 'relative', height: 26, background: brand.card, borderRadius: 13,
        border: `1px solid ${brand.border}`}}>
        <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: `${w}%`,
          background: TONE[status], borderRadius: 13}} />
        <div style={{position: 'absolute', left: '62.5%', top: -8, bottom: -8, width: 3,
          background: brand.text, opacity: 0.7}} />
      </div>
    </div>
  );
};

export const RatioBars: React.FC<{tests: TestResult[]; activityStatus: 'pass' | 'fail' | 'unknown';
  decisive: {valuePct: number; thresholdPct: number; label: string}}> =
({tests, activityStatus, decisive}) => (
  <div>
    {tests.map((t, i) => (
      <Bar key={t.id} label={t.label} frac={(t.ratio ?? 0) / t.threshold} status={t.status}
        delay={i * 20} detail={t.ratio === null ? '—' : `${(t.ratio * 100).toFixed(1)}% / ${(t.threshold * 100).toFixed(0)}%`} />
    ))}
    <Bar label={decisive.label} frac={decisive.valuePct / decisive.thresholdPct} status={activityStatus}
      delay={tests.length * 20 + 10} detail={`${decisive.valuePct.toFixed(2)}% / ${decisive.thresholdPct.toFixed(1)}%`} />
  </div>
);
