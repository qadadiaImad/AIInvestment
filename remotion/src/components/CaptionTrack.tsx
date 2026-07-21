// CaptionTrack.tsx — karaoke-style: current word highlighted
import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {brand} from '../brand';
import type {z} from 'zod';
import type {captionWordSchema} from '../props';

type Word = z.infer<typeof captionWordSchema>;

export const CaptionTrack: React.FC<{words: Word[]}> = ({words}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ms = ((frame % (8 * fps)) / fps) * 1000; // loops with the 8s bubble clip
  const active = words.findIndex((w) => ms >= w.fromMs && ms < w.toMs);
  const windowWords = words.slice(Math.max(0, active - 2), Math.max(0, active - 2) + 5);
  if (active === -1) return null;
  return (
    <div style={{position: 'absolute', left: 40, right: '34%', bottom: brand.safeBottom + 60,
      display: 'flex', flexWrap: 'wrap', gap: 10}}>
      {windowWords.map((w) => (
        <span key={`${w.fromMs}-${w.text}`} style={{
          fontFamily: brand.fontBody, fontWeight: 800, fontSize: 42,
          color: ms >= w.fromMs && ms < w.toMs ? brand.warn : brand.text,
          textShadow: '0 2px 12px rgba(0,0,0,0.8)',
        }}>{w.text}</span>
      ))}
    </div>
  );
};
