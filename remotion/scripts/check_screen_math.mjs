// check_screen_math.mjs — run the ScreenInsert projective maths under plain
// node and assert it against an INDEPENDENTLY computed test vector.
//
// This exists because the perspective map has a failure mode that typechecks
// and renders without error: a mis-packed matrix3d puts the chart somewhere
// other than the monitor. The corner round-trip below reads the packed
// 16-value array by index, so it validates the packing, not just the solve.
//
// Run:  cd remotion && node scripts/check_screen_math.mjs
// (bundles src/components/screenMath.ts with the local esbuild first)
import {mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import * as esbuild from 'esbuild';

// esbuild's JS API rather than its CLI: spawning the .cmd shim fails with
// EINVAL on Windows under node 22 without shell:true, and the API is the same
// binary either way.
const dir = mkdtempSync(join(tmpdir(), 'screenmath-'));
const out = join(dir, 'screenMath.mjs');
await esbuild.build({
  entryPoints: ['src/components/screenMath.ts'],
  bundle: true,
  format: 'esm',
  outfile: out,
  logLevel: 'error',
});
const {solveHomography, applyHomography, isConvexQuad} = await import(pathToFileURL(out).href);

let failures = 0;
const check = (name, ok, detail = '') => {
  console.log(`${ok ? '  ok  ' : ' FAIL '} ${name}${detail ? '  ' + detail : ''}`);
  if (!ok) failures++;
};

// ---------------------------------------------------------------- vector
// Independently computed in the Phase-1 design pass (separate implementation,
// separate node run). Agreement to 1e-9 means two derivations of the packing
// concur — the point of the exercise.
const W = 1200;
const H = 750;
const quad = [
  {x: 300, y: 500},
  {x: 760, y: 460},
  {x: 780, y: 900},
  {x: 280, y: 930},
];
const expected = {
  a: 0.3655333937745543,
  b: -0.0561136294953158,
  c: 300,
  d: -0.044106980961015355,
  e: 0.4755273496524629,
  f: 500,
  g: -0.000023420973103656583,
  h: -0.00010516772438803264,
};

console.log('\nScreenInsert projective maths');
const m = solveHomography(W, H, quad);
check('solve returns a matrix', Boolean(m));

if (m) {
  const got = {a: m[0], d: m[1], g: m[3], b: m[4], e: m[5], h: m[7], c: m[12], f: m[13]};
  let maxCoef = 0;
  for (const k of Object.keys(expected)) maxCoef = Math.max(maxCoef, Math.abs(got[k] - expected[k]));
  check('coefficients match the independent vector', maxCoef < 1e-9, `max err ${maxCoef.toExponential(2)}`);

  check('z column is identity (0,0,1,0), not zeros', m[8] === 0 && m[9] === 0 && m[10] === 1 && m[11] === 0, `got ${m.slice(8, 12).join(',')}`);

  // Round-trip every source corner through the PACKED array — this is what
  // catches a column-major/row-major transposition.
  const src = [[0, 0], [W, 0], [W, H], [0, H]];
  let maxErr = 0;
  src.forEach(([u, v], i) => {
    const p = applyHomography(m, u, v);
    maxErr = Math.max(maxErr, Math.hypot(p.x - quad[i].x, p.y - quad[i].y));
  });
  check('all 4 corners round-trip to the destination quad', maxErr < 1e-6, `max err ${maxErr.toExponential(2)}`);

  // The child's centre must land strictly inside the quad's bbox — a flipped
  // or degenerate mapping fails this even when the corners happen to match.
  const c = applyHomography(m, W / 2, H / 2);
  const xs = quad.map((p) => p.x);
  const ys = quad.map((p) => p.y);
  const inside = c.x > Math.min(...xs) && c.x < Math.max(...xs) && c.y > Math.min(...ys) && c.y < Math.max(...ys);
  check('child centre maps inside the quad', inside, `(${c.x.toFixed(3)}, ${c.y.toFixed(3)})`);
}

// ------------------------------------------------------------- guardrails
check('collinear quad is refused', solveHomography(W, H, [{x: 0, y: 0}, {x: 100, y: 0}, {x: 200, y: 0}, {x: 300, y: 0}]) === null);
// A bowtie: TR and BR swapped. The solver alone would happily return a matrix.
check('bowtie (out-of-order corners) is refused', solveHomography(W, H, [{x: 300, y: 500}, {x: 780, y: 900}, {x: 760, y: 460}, {x: 280, y: 930}]) === null);
check('a plain axis-aligned rect is convex', isConvexQuad([{x: 0, y: 0}, {x: 10, y: 0}, {x: 10, y: 10}, {x: 0, y: 10}]));

// An axis-aligned destination must degenerate to a pure affine map: g and h
// are exactly 0 when there is no foreshortening.
const affine = solveHomography(100, 50, [{x: 10, y: 20}, {x: 210, y: 20}, {x: 210, y: 120}, {x: 10, y: 120}]);
check('axis-aligned rect gives g=h=0 (affine)', Math.abs(affine[3]) < 1e-12 && Math.abs(affine[7]) < 1e-12, `g=${affine[3]}, h=${affine[7]}`);
check('axis-aligned rect scales 2x horizontally', Math.abs(affine[0] - 2) < 1e-12, `a=${affine[0]}`);

rmSync(dir, {recursive: true, force: true});
console.log(failures === 0 ? '\nPASS\n' : `\n${failures} FAILURE(S)\n`);
process.exit(failures === 0 ? 0 : 1);
