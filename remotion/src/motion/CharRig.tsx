// CharRig — a cut-out puppet built from one drawing's own vector paths.
//
// WHY THIS AND NOT GENERATION, settled by measurement rather than taste:
//
//  · AnimateDiff on an approved pose gave frame-to-frame delta 2.0 (conservative)
//    to 8.6 (aggressive) against 50.6 for a real pose cut. That is boil, not
//    motion — the exact artefact this project already banned.
//  · Anchored img2img held identity perfectly and turned NOTHING, at denoise
//    0.62 / 0.72 / 0.82 / 0.92. Pure t2i lost the framing entirely.
//    Root cause: the cast LoRA was trained on flat front-facing sheets, so no
//    angle other than front exists in the model to sample.
//
// So the turn is FAKED, which is what every cut-out rig in the business does.
// A flat drawing cannot rotate through depth, but the eye does not read depth
// from rotation — it reads it from four cues, and all four are cheap here:
//
//   1. OCCLUSION  the far arm passes BEHIND the torso.  <- by far the strongest
//   2. FORESHORTENING  the body narrows on x while the head narrows less,
//      because a sphere stays round longer than a slab.
//   3. PARALLAX  the head leads the body into the turn; the feet lag it.
//   4. SILHOUETTE  the near shoulder grows, the far one shrinks.
//
// Every value is a continuous function of frame, so the supply of in-betweens
// is infinite rather than the 16 a generator hands back, it costs nothing to
// render, and identity cannot drift because these are literally the same paths.
import React from "react";
import {Img, staticFile} from "remotion";

export type Rig = {
  w: number;
  h: number;
  pivots: Record<string, number[]>;
  parts: Record<string, string>;
};

/** One articulated pose. Everything is optional and defaults to rest, so a
 *  caller only names the channels it actually drives. */
export type RigPose = {
  /** -1 = turned 45° toward viewer-left, +1 = viewer-right, 0 = front on. */
  turn?: number;
  /** walk cycle phase in radians; `stride` scales how far the legs travel. */
  walkPhase?: number;
  stride?: number;
  /** 0 = arm at rest, 1 = arm fully raised toward the screen. */
  pointAt?: number;
  /** which arm carries the gesture — Sol points with his screen-left hand. */
  gestureArm?: "armL" | "armR";
  /** 0 = level gaze, 1 = chin fully raised. */
  lookUp?: number;
  /** -1..1 lean from the ankles. */
  lean?: number;
  /** breath amplitude; 1 is the resting idle. */
  breath?: number;
  /** breath phase in radians (so several characters do not inhale in unison). */
  breathPhase?: number;
  /** slow standing weight shift, -1..1. */
  sway?: number;
};

const Part: React.FC<{
  rig: Rig;
  name: string;
  rot?: number;
  dx?: number;
  dy?: number;
  sx?: number;
  sy?: number;
  z: number;
}> = ({rig, name, rot = 0, dx = 0, dy = 0, sx = 1, sy = 1, z}) => {
  const src = rig.parts[name];
  if (!src) return null;
  const [px, py] = rig.pivots[name] ?? [0.5, 0.5];
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        zIndex: z,
        transform: `translate(${dx}px, ${dy}px) rotate(${rot}deg) scale(${sx}, ${sy})`,
        transformOrigin: `${px * 100}% ${py * 100}%`,
      }}
    >
      <Img
        src={staticFile(src)}
        style={{position: "absolute", inset: 0, width: "100%", height: "100%"}}
      />
    </div>
  );
};

export const CharRig: React.FC<{rig: Rig; pose: RigPose}> = ({rig, pose}) => {
  const {
    turn = 0,
    walkPhase = 0,
    stride = 0,
    pointAt = 0,
    gestureArm = "armL",
    lookUp = 0,
    lean = 0,
    breath = 1,
    breathPhase = 0,
    sway = 0,
  } = pose;

  const W = rig.w;
  const t = Math.max(-1, Math.min(1, turn));
  const at = Math.abs(t);

  // ── the turn ────────────────────────────────────────────────────────────
  // Foreshortening is NOT uniform: a head is closer to a sphere than a torso
  // is, so it keeps its width far longer. Squashing both by the same factor
  // is the giveaway that reads as "the picture got thinner".
  const torsoSx = 1 - 0.26 * at;
  const headSx = 1 - 0.11 * at;
  // The head leads the body into a turn and the feet lag it — that offset
  // spread across the height is the parallax cue.
  const headDx = t * W * 0.055;
  const torsoDx = t * W * 0.022;
  const legDx = t * W * 0.008;
  const headRot = t * 3.2;

  // Turning right rotates the character's screen-LEFT side away from us, so
  // armL becomes the far arm; turning left does the reverse. The far arm
  // tucks toward the spine and goes BEHIND the torso — that occlusion is the
  // cue that actually sells the depth. The near arm swings into open space.
  const lIsFar = t > 0;

  // ── breath, sway, lean ──────────────────────────────────────────────────
  const br = Math.sin(breathPhase) * breath;
  // the head answers the breath a beat late; that lag is what makes two
  // pieces read as one body instead of two objects on the same timeline
  const brLag = Math.sin(breathPhase - 0.55) * breath;
  const leanRot = lean * 5.5;
  const swayDx = sway * W * 0.006;

  // ── walk ────────────────────────────────────────────────────────────────
  // Legs are counter-phase; the body bobs at DOUBLE leg frequency because the
  // pelvis rises once per step, not once per cycle. Arms counter-swing
  // against the legs, which is what stops a walk reading as a shuffle.
  const s = stride;
  const legLRot = Math.sin(walkPhase) * 15 * s;
  const legRRot = Math.sin(walkPhase + Math.PI) * 15 * s;
  const bob = -Math.abs(Math.cos(walkPhase)) * rig.h * 0.012 * s;
  const walkLean = 2.4 * s;
  const armSwing = Math.sin(walkPhase + Math.PI) * 11 * s;

  // ── point at the screen ─────────────────────────────────────────────────
  // Overshoot on the way up, then settle. A gesture that arrives linearly on
  // its final value reads as a slider being dragged.
  // SIGN MATTERS AND WAS WRONG TWICE. The pivot is the shoulder, and Sol's
  // pointing finger sits to the LEFT of it, so a counter-clockwise turn
  // swings the hand DOWN across his chest - which is what the first two
  // renders showed. Raising it is clockwise, i.e. positive, for the
  // screen-left arm. His hand is already up, so the throw is modest.
  const p = pointAt;
  const pointRot = 24 * p + Math.sin(p * Math.PI) * 5;
  const pointDy = -rig.h * 0.030 * p;
  const pointDx = -rig.w * 0.010 * p;   // outward, so the hand clears his cheek

  // ── look up ─────────────────────────────────────────────────────────────
  // A chin raise is not just rotation: the head also rides UP off the neck
  // and stretches slightly, or it reads as the head detaching.
  const u = lookUp;
  const lookRot = -7.5 * u;
  const lookDy = -rig.h * 0.016 * u;
  const lookSy = 1 + 0.02 * u;

  // Per-arm resolution. The gesture lives on a NAMED arm, not on whichever
  // arm happens to be nearest — Sol's pointing hand is his screen-left one,
  // and it has to keep pointing while he turns, not hop across his body.
  const arm = (name: "armL" | "armR") => {
    const isL = name === "armL";
    const far = isL ? lIsFar : !lIsFar;
    const isGesture = name === gestureArm;
    return {
      name,
      // far arm goes behind the torso; a raised gesture goes above the head
      z: far && at > 0.12 ? 0 : isGesture && p > 0.5 ? 6 : far ? 3 : 4,
      sx: far ? 1 - 0.34 * at : 1 + 0.06 * at,
      dx:
        (far ? t * W * 0.055 : t * W * 0.012 + (isL ? -1 : 1) * W * 0.018 * at) +
        swayDx +
        (isGesture ? pointDx * (isL ? 1 : -1) : 0),
      dy: -brLag * (far ? 1.6 : 2.2) + bob + (isGesture ? pointDy : 0),
      rot:
        leanRot * 0.7 +
        (isL ? armSwing : -armSwing) +
        (isGesture ? pointRot * (isL ? 1 : -1) : 0),
    };
  };
  const armL = arm("armL");
  const armR = arm("armR");

  return (
    <>
      <Part rig={rig} {...armL} />
      <Part rig={rig} {...armR} />
      <Part
        rig={rig}
        name="legL"
        z={1}
        rot={legLRot + leanRot * 0.2}
        dx={legDx + swayDx * 0.4}
        sx={torsoSx}
      />
      <Part
        rig={rig}
        name="legR"
        z={1}
        rot={legRRot + leanRot * 0.2}
        dx={legDx + swayDx * 0.4}
        sx={torsoSx}
      />
      <Part
        rig={rig}
        name="torso"
        z={2}
        rot={leanRot + walkLean + sway * 0.6}
        dx={torsoDx + swayDx}
        dy={-br * 2 + bob}
        sx={torsoSx * (1 - br * 0.004)}
        sy={1 + br * 0.006}
      />
      <Part
        rig={rig}
        name="head"
        z={5}
        rot={headRot + lookRot + leanRot * 0.5 + brLag * 0.5 + sway * 1.9}
        dx={headDx + swayDx * 1.6}
        dy={-brLag * 4.2 + lookDy + bob * 1.15}
        sx={headSx * (1 + brLag * 0.003)}
        sy={lookSy * (1 + brLag * 0.004)}
      />
    </>
  );
};
