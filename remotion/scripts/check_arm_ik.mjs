// check_arm_ik.mjs — assert that the arm IK actually puts the wrist on the
// target, by round-tripping every solution back through forward kinematics.
//
// "The glove lands on his eyes" is a numeric claim. This is where it gets
// checked, rather than by squinting at a contact sheet.
//
// Run:  cd remotion && node scripts/check_arm_ik.mjs
import {mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import * as esbuild from 'esbuild';

const dir = mkdtempSync(join(tmpdir(), 'armik-'));
const out = join(dir, 'armIK.mjs');
await esbuild.build({
  entryPoints: ['src/characters/armIK.ts'],
  bundle: true,
  format: 'esm',
  outfile: out,
  logLevel: 'error',
});
const {armIK, armFK, limbDir, wrapDeg, blendDeg} = await import(pathToFileURL(out).href);

let failures = 0;
const check = (name, ok, detail = '') => {
  console.log(`${ok ? '  ok  ' : ' FAIL '} ${name}${detail ? '  ' + detail : ''}`);
  if (!ok) failures++;
};

console.log('\nRubber-hose arm IK');

// ---------------------------------------------- convention sanity
// A limb at 0 points DOWN; at 90 it points screen-LEFT. If this is wrong,
// every solved pose is mirrored and the character reaches the wrong way.
const d0 = limbDir(0);
const d90 = limbDir(90);
check('angle 0 points down (+y)', Math.abs(d0.x) < 1e-9 && Math.abs(d0.y - 1) < 1e-9, `(${d0.x.toFixed(3)}, ${d0.y.toFixed(3)})`);
check('angle 90 points screen-left (-x)', Math.abs(d90.x + 1) < 1e-9 && Math.abs(d90.y) < 1e-9, `(${d90.x.toFixed(3)}, ${d90.y.toFixed(3)})`);

// ---------------------------------------------- round-trip
const UPPER = 60;
const FORE = 54;
const shoulder = {x: 244, y: 124};

// Targets spanning the arm's real working set, including the two that matter:
// the face (facepalm) and forward-and-down (the desk plant). Every one of
// these is inside the arm's 114px reach — that is a constraint on where the
// rig may ask the hand to go, not a detail: a target further away than
// upperLen+foreLen is unreachable no matter how good the solver is, and the
// honest response is a stretched arm, not a landed one.
const targets = [
  {name: 'face / eye area (facepalm)', p: {x: 236, y: 70}},
  {name: 'forward-down (desk plant)', p: {x: 300, y: 210}},
  {name: 'straight down (rest)', p: {x: 244, y: 230}},
  {name: 'up and back (arms flung)', p: {x: 300, y: 40}},
  {name: 'across the body', p: {x: 180, y: 160}},
  {name: 'behind and low', p: {x: 200, y: 220}},
];

const REACH = UPPER + FORE;
for (const t of targets) {
  const d = Math.hypot(t.p.x - shoulder.x, t.p.y - shoulder.y);
  check(`${t.name} is inside the arm's reach`, d < REACH - 1e-3, `d=${d.toFixed(1)} reach=${REACH}`);
}

for (const t of targets) {
  for (const bend of [1, -1]) {
    const s = armIK(shoulder, t.p, UPPER, FORE, bend);
    const fk = armFK(shoulder, s.shoulderDeg, s.elbowDeg, UPPER, FORE);
    const err = Math.hypot(fk.wrist.x - t.p.x, fk.wrist.y - t.p.y);
    check(
      `${t.name} [bend ${bend > 0 ? '+' : '-'}] wrist lands on target`,
      s.reached && err < 1e-6,
      `err=${err.toExponential(2)} sh=${s.shoulderDeg.toFixed(1)} el=${s.elbowDeg.toFixed(1)}`
    );
  }
}

// The two bend solutions must be genuinely different poses (different elbow
// positions), otherwise the sign parameter is doing nothing.
const sA = armIK(shoulder, targets[0].p, UPPER, FORE, 1);
const sB = armIK(shoulder, targets[0].p, UPPER, FORE, -1);
const eA = armFK(shoulder, sA.shoulderDeg, sA.elbowDeg, UPPER, FORE).elbow;
const eB = armFK(shoulder, sB.shoulderDeg, sB.elbowDeg, UPPER, FORE).elbow;
check('the two bend solutions place the elbow differently', Math.hypot(eA.x - eB.x, eA.y - eB.y) > 10,
  `elbowA=(${eA.x.toFixed(0)},${eA.y.toFixed(0)}) elbowB=(${eB.x.toFixed(0)},${eB.y.toFixed(0)})`);

// ---------------------------------------------- out of reach
const far = {x: shoulder.x + 400, y: shoulder.y};
const s = armIK(shoulder, far, UPPER, FORE, 1);
const fk = armFK(shoulder, s.shoulderDeg, s.elbowDeg, UPPER, FORE);
const reach = Math.hypot(fk.wrist.x - shoulder.x, fk.wrist.y - shoulder.y);
check('out-of-reach target clamps instead of NaN', Number.isFinite(s.shoulderDeg) && Number.isFinite(s.elbowDeg));
check('out-of-reach reports reached=false', s.reached === false);
check('out-of-reach extends the arm nearly straight', Math.abs(reach - (UPPER + FORE)) < 0.5, `reach=${reach.toFixed(3)} max=${UPPER + FORE}`);
check('out-of-reach still aims at the target', Math.abs(fk.wrist.y - shoulder.y) < 1, `wrist y offset ${(fk.wrist.y - shoulder.y).toFixed(3)}`);

// A target sitting exactly at full extension is the other singular case: it
// must resolve to a straight arm, not to NaN or a spin.
const edge = {x: shoulder.x, y: shoulder.y + UPPER + FORE};
const sEdge = armIK(shoulder, edge, UPPER, FORE, 1);
const fkEdge = armFK(shoulder, sEdge.shoulderDeg, sEdge.elbowDeg, UPPER, FORE);
check('target at exactly full extension resolves',
  Number.isFinite(sEdge.shoulderDeg) && Math.hypot(fkEdge.wrist.x - edge.x, fkEdge.wrist.y - edge.y) < 0.01,
  `err=${Math.hypot(fkEdge.wrist.x - edge.x, fkEdge.wrist.y - edge.y).toExponential(2)}`);

// ---------------------------------------------- angle helpers
check('wrapDeg(370) === 10', Math.abs(wrapDeg(370) - 10) < 1e-9);
check('wrapDeg(-190) === 170', Math.abs(wrapDeg(-190) - 170) < 1e-9);
check('blendDeg takes the short way round', Math.abs(wrapDeg(blendDeg(170, -170, 0.5)) - 180) < 1e-9, `got ${blendDeg(170, -170, 0.5)}`);

rmSync(dir, {recursive: true, force: true});
console.log(failures === 0 ? '\nPASS\n' : `\n${failures} FAILURE(S)\n`);
process.exit(failures === 0 ? 0 : 1);
