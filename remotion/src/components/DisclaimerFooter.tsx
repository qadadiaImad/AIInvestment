import React from 'react';
import {brand} from '../brand';

export const DisclaimerFooter: React.FC<{text: string}> = ({text}) => (
  <div style={{
    position: 'absolute', bottom: 40, left: 0, right: 0, textAlign: 'center',
    fontFamily: brand.fontBody, fontSize: 22, color: brand.muted, opacity: 0.85,
  }}>{text}</div>
);
