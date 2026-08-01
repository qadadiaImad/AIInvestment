// CameraRig.tsx — a camera that moves over a chart that has already drawn itself.
//
// The chart renders ONCE at full extent. The rig decides what you are looking
// at: a keyframed shot list of {at, zoom, x, y}, where x/y are the point of the
// child that should sit in the middle of the viewport, in 0..1 of the child's
// own box. Between two shots the camera eases; outside the list it holds.
//
// Captions do NOT live in here. They sit in a layer above, so a push-in never
// scales the type — the reference reel keeps its text pin-sharp while the
// chart moves underneath, and scaled text is the fastest way to look cheap.
import React from 'react';
import {EASE} from './craft';

export type Shot = {
  /** Frame this shot is fully reached on. */
  at: number;
  /** 1 = the whole child fits the viewport. 2 = twice as close. */
  zoom: number;
  /** Point of the child to centre, in 0..1 of its own width/height. */
  x: number;
  y: number;
  /** Easing into this shot. Defaults to EASE.cruise, which craft.ts documents
   * as the curve for long drifts and camera moves — quick out, damped in,
   * never linear. A linear push reads as a slideshow zoom, not a camera. */
  ease?: (t: number) => number;
};

export type CameraState = {zoom: number; x: number; y: number};

/** Where the camera is on `frame`. Pure — unit-testable without rendering. */
export const cameraAt = (frame: number, shots: Shot[]): CameraState => {
  if (shots.length === 0) return {zoom: 1, x: 0.5, y: 0.5};
  const sorted = [...shots].sort((a, b) => a.at - b.at);
  if (frame <= sorted[0].at) {
    const s = sorted[0];
    return {zoom: s.zoom, x: s.x, y: s.y};
  }
  const last = sorted[sorted.length - 1];
  if (frame >= last.at) return {zoom: last.zoom, x: last.x, y: last.y};

  let i = 0;
  for (let k = 0; k < sorted.length - 1; k++) if (frame >= sorted[k].at) i = k;
  const a = sorted[i];
  const b = sorted[i + 1];
  const span = Math.max(1, b.at - a.at);
  const t = (frame - a.at) / span;
  const e = (b.ease ?? EASE.cruise)(Math.min(1, Math.max(0, t)));
  const mix = (u: number, v: number) => u + (v - u) * e;
  return {zoom: mix(a.zoom, b.zoom), x: mix(a.x, b.x), y: mix(a.y, b.y)};
};

/**
 * The transform that puts (x, y) of a `w`x`h` child in the middle of a
 * `vw`x`vh` viewport at `zoom`. Returned as a string so the caller can drop it
 * straight into a style, and computed here so the maths is in one place.
 */
export const cameraTransform = (
  cam: CameraState,
  w: number,
  h: number,
  vw: number,
  vh: number
): string => {
  const dx = vw / 2 - cam.x * w * cam.zoom;
  const dy = vh / 2 - cam.y * h * cam.zoom;
  return `translate(${dx}px, ${dy}px) scale(${cam.zoom})`;
};

export const CameraRig: React.FC<{
  frame: number;
  shots: Shot[];
  /** The child's intrinsic size — what the chart was laid out at. */
  childWidth: number;
  childHeight: number;
  viewportWidth: number;
  viewportHeight: number;
  children: React.ReactNode;
}> = ({frame, shots, childWidth, childHeight, viewportWidth, viewportHeight, children}) => {
  const cam = cameraAt(frame, shots);
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: viewportWidth,
        height: viewportHeight,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: childWidth,
          height: childHeight,
          transform: cameraTransform(cam, childWidth, childHeight, viewportWidth, viewportHeight),
          transformOrigin: '0 0',
        }}
      >
        {children}
      </div>
    </div>
  );
};
