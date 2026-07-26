// check_joint_limits.mjs — sweep every frame of the reel and report joints the
// authored pose drives outside an anatomically possible range.
//
// This exists because "the movement is not physically logical" is a real defect
// that renders perfectly and typechecks perfectly. The rig originally had NO
// joint limits, and `elbowR` was authored across -88°..+95° — a range that
// crosses zero, which inverts the elbow and bends the forearm backwards.
//
// The clamp in joints.ts stops that reaching the screen. This script reports
// what the clamp is having to CATCH, so the underlying keyframes can be fixed
// rather than silently corrected every frame.
//
// Run:  cd remotion && node scripts/check_joint_limits.mjs
import {mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import * as esbuild from 'esbuild';

const dir = mkdtempSync(join(tmpdir(), 'joints-'));
const out = join(dir, 'bundle.mjs');

// The pose engine imports `interpolate` from remotion; stub it so the sweep can
// run under plain node. It is a pure function and trivially reimplemented — the
// point is to exercise the authored KEYFRAMES, not remotion's easing internals.
await esbuild.build({
  stdin: {
    contents: `
      export {computeRubberHosePose} from './src/characters/rubberHoseRig';
      export {JOINT_LIMITS, violates, wrapDeg} from './src/characters/joints';
    `,
    resolveDir: process.cwd(),
    loader: 'ts',
  },
  bundle: true,
  format: 'esm',
  outfile: out,
  logLevel: 'error',
  plugins: [{
    name: 'stub-remotion',
    setup(build) {
      build.onResolve({filter: /^remotion$/}, () => ({path: 'remotion', namespace: 'stub'}));
      build.onLoad({filter: /.*/, namespace: 'stub'}, () => ({
        contents: `
          export const interpolate = (x, [a, b], [c, d], o = {}) => {
            let t = (x - a) / (b - a);
            if (o.extrapolateLeft === 'clamp' && t < 0) t = 0;
            if (o.extrapolateRight === 'clamp' && t > 1) t = 1;
            if (o.easing) t = o.easing(t);
            return c + (d - c) * t;
          };
          export const Easing = {bezier: () => (t) => t};
          export const useCurrentFrame = () => 0;
          export const spring = () => 1;
          export const random = () => 0.5;
          export const staticFile = (s) => s;
        `,
        loader: 'js',
      }));
    },
  }],
});

const {computeRubberHosePose, JOINT_LIMITS, wrapDeg} = await import(pathToFileURL(out).href);

// Rest angles, mirroring the rigs — limits apply to the FINAL angle.
const REST = {
  shoulderL: 4, shoulderR: -4, elbowL: 14, elbowR: -14,
  handL: -6, handR: 6, hipL: 0, hipR: 0, kneeL: -6, kneeR: -6,
};
const DIRECT = ['leanChest', 'leanHead'];

const worst = {};
for (let f = 0; f <= 510; f++) {
  const p = computeRubberHosePose(f);
  for (const j of Object.keys(JOINT_LIMITS)) {
    const final = wrapDeg(DIRECT.includes(j) ? p[j] : (REST[j] ?? 0) + p[j]);
    if (!Number.isFinite(final)) continue;
    const [lo, hi] = JOINT_LIMITS[j];
    const over = final < lo ? lo - final : final > hi ? final - hi : 0;
    if (over > (worst[j]?.over ?? 0)) worst[j] = {over, final, frame: f, lo, hi};
  }
}

console.log('\nJoint limits — worst excursion per joint over frames 0..510\n');
const rows = Object.entries(worst).sort((a, b) => b[1].over - a[1].over);
if (rows.length === 0) {
  console.log('  every joint stays inside its anatomical range\n');
} else {
  for (const [j, w] of rows) {
    console.log(
      `  ${j.padEnd(11)} range [${String(w.lo).padStart(5)},${String(w.hi).padStart(5)}]` +
      `  peaked ${w.final.toFixed(1).padStart(7)}° at f${String(w.frame).padStart(3)}` +
      `  -> clamped by ${w.over.toFixed(1)}°`
    );
  }
}

// The elbow is the one that MUST NOT cross zero — a hinge that passes through
// zero inverts, and that is the defect this whole file exists for.
let inverted = 0;
for (let f = 0; f <= 510; f++) {
  const p = computeRubberHosePose(f);
  if (wrapDeg(REST.elbowR + p.elbowR) > 0) inverted++;
  if (wrapDeg(REST.elbowL + p.elbowL) < 0) inverted++;
}
console.log(`\n  elbow frames authored on the WRONG SIDE of zero (would invert): ${inverted}`);
console.log('  (these are caught by the clamp; fix the keyframes to remove them)\n');

rmSync(dir, {recursive: true, force: true});
