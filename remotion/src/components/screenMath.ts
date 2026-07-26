// screenMath.ts — the projective maths behind ScreenInsert, deliberately kept
// free of React and Remotion imports so it can be bundled and run under plain
// node in a test. The perspective map has a failure mode that typechecks
// perfectly (a mis-packed matrix puts the insert somewhere else entirely), so
// it needs to be checkable outside a render.
//
// The derivation, stated once so the code below is verifiable rather than magic:
//
//   Source corners are the child's own rect: (0,0) (w,0) (w,h) (0,h).
//   Destination corners are 4 points in the parent's pixel space, in the SAME
//   order (TL, TR, BR, BL).
//
//   We want a 3x3 projective H = [a b c; d e f; g h 1] with
//       x = (a*u + b*v + c) / (g*u + h*v + 1)
//       y = (d*u + e*v + f) / (g*u + h*v + 1)
//
//   Clearing denominators gives two linear equations per correspondence:
//       a*u + b*v + c               - g*u*x - h*v*x = x
//                     d*u + e*v + f - g*u*y - h*v*y = y
//   Four correspondences -> an 8x8 system in (a,b,c,d,e,f,g,h), solved here by
//   Gaussian elimination with partial pivoting. No npm dependency: adding one
//   for an 8x8 solve would be absurd, and the solver is 25 lines.
//
//   CSS matrix3d takes 16 values in COLUMN-MAJOR order. Embedding the 2D
//   projective map in 3D, a point (u, v, z, 1) on the child plane must give
//       X = a*u + b*v + 0*z + c
//       Y = d*u + e*v + 0*z + f
//       Z = 0*u + 0*v + 1*z + 0      <- z passed through as identity
//       W = g*u + h*v + 0*z + 1
//   Reading the four CSS columns off those rows:
//       column 1 (u coefficients) = (a, d, 0, g)
//       column 2 (v coefficients) = (b, e, 0, h)
//       column 3 (z coefficients) = (0, 0, 1, 0)
//       column 4 (constants)      = (c, f, 0, 1)
//   =>  matrix3d(a, d, 0, g,  b, e, 0, h,  0, 0, 1, 0,  c, f, 0, 1)
//
//   Two things in there are load-bearing and silent when wrong:
//     * the column-major order — hand-transcribing the row-major hand-math
//       order compiles and renders, just off the quad;
//     * the z column being (0,0,1,0) and not (0,0,0,0) — it multiplies z=0
//       either way for a flat plane, but zeroing it makes the 4x4 singular,
//       and Chromium (which Remotion drives) can treat a singular layer as
//       invisible rather than flat.

/** A point in the parent's pixel space. */
export type Pt = {x: number; y: number};
/** Destination quad, in order: top-left, top-right, bottom-right, bottom-left. */
export type Quad = [Pt, Pt, Pt, Pt];

/**
 * Solve A·z = b by Gaussian elimination with partial pivoting.
 * Returns null if the system is singular.
 */
const solveLinear = (A: number[][], b: number[]): number[] | null => {
  const n = b.length;
  // Augmented copy, so callers keep their inputs.
  const M = A.map((row, i) => [...row, b[i]]);

  for (let col = 0; col < n; col++) {
    let piv = col;
    for (let r = col + 1; r < n; r++) {
      if (Math.abs(M[r][col]) > Math.abs(M[piv][col])) piv = r;
    }
    if (Math.abs(M[piv][col]) < 1e-12) return null; // singular
    if (piv !== col) {
      const t = M[piv];
      M[piv] = M[col];
      M[col] = t;
    }
    for (let r = col + 1; r < n; r++) {
      const f = M[r][col] / M[col][col];
      if (f === 0) continue;
      for (let c = col; c <= n; c++) M[r][c] -= f * M[col][c];
    }
  }

  const z = new Array<number>(n).fill(0);
  for (let r = n - 1; r >= 0; r--) {
    let s = M[r][n];
    for (let c = r + 1; c < n; c++) s -= M[r][c] * z[c];
    z[r] = s / M[r][r];
  }
  return z;
};

/**
 * True if the quad is convex and consistently wound. A bowtie (corners given
 * out of order) still yields *a* matrix from the solver — it just isn't the
 * mapping anyone wanted — so callers check this first and refuse to render
 * rather than shipping a silently sheared insert.
 */
export const isConvexQuad = (q: Quad): boolean => {
  let sign = 0;
  for (let i = 0; i < 4; i++) {
    const a = q[i];
    const b = q[(i + 1) % 4];
    const c = q[(i + 2) % 4];
    const cross = (b.x - a.x) * (c.y - b.y) - (b.y - a.y) * (c.x - b.x);
    if (Math.abs(cross) < 1e-9) continue; // collinear edge pair — ignore
    const s = Math.sign(cross);
    if (sign === 0) sign = s;
    else if (s !== sign) return false;
  }
  return sign !== 0;
};

/**
 * Homography taking the rect (0,0)-(w,h) onto `quad`, returned as the 16
 * column-major values CSS `matrix3d()` expects. Returns null for a degenerate
 * or non-convex quad, which the caller should treat as "do not render".
 */
export const solveHomography = (w: number, h: number, quad: Quad): number[] | null => {
  if (!isConvexQuad(quad)) return null;
  const src: Pt[] = [
    {x: 0, y: 0},
    {x: w, y: 0},
    {x: w, y: h},
    {x: 0, y: h},
  ];
  const A: number[][] = [];
  const b: number[] = [];
  for (let i = 0; i < 4; i++) {
    const {x: u, y: v} = src[i];
    const {x, y} = quad[i];
    //      a  b  c  d  e  f     g       h
    A.push([u, v, 1, 0, 0, 0, -u * x, -v * x]);
    b.push(x);
    A.push([0, 0, 0, u, v, 1, -u * y, -v * y]);
    b.push(y);
  }
  const z = solveLinear(A, b);
  if (!z) return null;
  const [a, bb, c, d, e, f, g, hh] = z;
  // column-major, per the derivation in the header
  return [a, d, 0, g, bb, e, 0, hh, 0, 0, 1, 0, c, f, 0, 1];
};

/**
 * Apply a PACKED 16-value matrix to a point in child space. Reads the array by
 * index, so a test that round-trips corners through this function validates the
 * packing itself and not just the coefficients.
 */
export const applyHomography = (m: number[], u: number, v: number): Pt => {
  const x = m[0] * u + m[4] * v + m[12];
  const y = m[1] * u + m[5] * v + m[13];
  const w = m[3] * u + m[7] * v + m[15];
  return {x: x / w, y: y / w};
};

/** The CSS value. Never round the g/h terms — they are routinely 1e-4..1e-6
 * and truncating them visibly flattens the foreshortening. */
export const toMatrix3d = (m: number[]): string => `matrix3d(${m.join(', ')})`;
