import React from 'react';
import {brand} from '../brand';

export const PurificationLine: React.FC<{perShare: number | null}> = ({perShare}) => (
  <div style={{fontFamily: brand.fontBody, fontSize: 30, color: brand.muted}}>
    {perShare === null ? 'Purification: insufficient data' :
      <>Purification: <span style={{color: brand.text, fontFamily: brand.fontMono}}>${perShare.toFixed(4)}/share</span> of held-period income</>}
  </div>
);
