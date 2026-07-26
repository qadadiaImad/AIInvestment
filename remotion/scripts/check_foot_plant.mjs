// check_foot_plant.mjs — measure how far the character's feet slide and float.
//
// A standing figure's feet stay ON THE FLOOR and the body moves over them. If
// the feet translate with the body, the figure reads as sliding on ice or
// hovering — which is the single most "physically illogical" thing a rig can
// do, and it is invisible in a still.
//
// The first rig applied `translate(weightShift, bob)` to a group that CONTAINED
// the legs, so every breath lifted the feet off the floor and every weight
// shift slid them sideways. This quantifies that.
//
// Run:  cd remotion && node scripts/check_foot_plant.mjs
import {mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import * as esbuild from 'esbuild';

const dir = mkdtempSync(join(tmpdir(), 'foot-'));
const out = join(dir, 'bundle.mjs');

await esbuild.build({
  stdin: {
    contents: `
      export {computeRubberHosePose} from './src/characters/rubberHoseRig';
      export * as SK from './src/characters/toonSkeleton';
      export {armIK, armFK} from './src/characters/armIK';
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

const {computeRubberHosePose, SK, armIK, armFK} = await import(pathToFileURL(out).href);

// The feet are now INPUTS (SK.STANCE), so their drift is zero by construction.
// The meaningful question is different: as the pelvis moves, can each leg still
// REACH its planted foot? If the hip travels further than the leg is long, the
// IK clamps and the foot silently detaches from the floor after all.
const GAIN = 2.2;
const PX = 1240 / 2900;

let worst = {gap: -Infinity, frame: 0, which: ''};
let maxErr = 0;
let unreachable = 0;

for (let f = 0; f <= 510; f++) {
  const p = computeRubberHosePose(f);
  const pelvisX = SK.CX + p.weightShift * GAIN;
  const pelvisY = SK.HIP_Y + p.bob * GAIN;

  for (const which of ['near', 'far']) {
    const hip = {x: pelvisX + SK.HIP_DX * (which === 'near' ? 1 : -1), y: pelvisY};
    const ankle = SK.STANCE[which];
    const d = Math.hypot(ankle.x - hip.x, ankle.y - hip.y);
    const gap = d - SK.LEG_REACH;
    if (gap > worst.gap) worst = {gap, frame: f, which};
    if (!({}).hasOwnProperty.call(ankle, 'x')) continue;

    const ik = armIK(hip, ankle, SK.THIGH_BONE, SK.SHIN_BONE, 1);
    if (!ik.reached) unreachable++;
    const fk = armFK(hip, ik.shoulderDeg, ik.elbowDeg, SK.THIGH_BONE, SK.SHIN_BONE);
    maxErr = Math.max(maxErr, Math.hypot(fk.wrist.x - ankle.x, fk.wrist.y - ankle.y));
  }
}

console.log('');
console.log('Foot plant — the feet are IK targets, so drift is zero by construction.');
console.log('');
console.log(`  leg length              : ${SK.LEG_REACH.toFixed(0)} art units`);
console.log(`  hip rests at            : ${(SK.LEG_REST / SK.LEG_REACH * 100).toFixed(1)}% of full extension`);
console.log(`                            (never 100% — a straight two-link chain is the IK singularity)`);
console.log(`  worst hip-to-foot reach : ${(SK.LEG_REACH + worst.gap).toFixed(0)} units at f${worst.frame} (${worst.which} leg)`);
console.log(`  headroom                : ${(-worst.gap).toFixed(0)} units`);
console.log(`  frames the leg could NOT reach its planted foot: ${unreachable}`);
console.log(`  worst ankle placement error: ${(maxErr * PX).toFixed(3)} px`);
console.log('');

if (unreachable === 0 && maxErr * PX < 0.01) {
  console.log('  PASS — every foot stays exactly on its floor position, all 510 frames.');
} else {
  console.log('  FAIL — the pelvis travels further than the legs can follow.');
}
console.log('');

rmSync(dir, {recursive: true, force: true});
