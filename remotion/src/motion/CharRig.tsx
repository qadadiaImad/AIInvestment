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
  /** measured off the pose's alpha: where the two feet first separate */
  crotch?: number;
  /** where the body is cut into torso and feet — sits ABOVE the crotch so
   *  the torso draw covers the straight edge */
  legCut?: number;
  /** x of the gap between the two feet */
  footMid?: number;
  /** the neck line — where the body silhouette is cut so its head region
   *  can travel with the head part instead of staying behind it */
  neck?: number;
  /** true only when a real gap between the feet was measured. Where it is
   *  false the feet are one connected blob and must move together — halving
   *  it and moving the halves apart tears the drawing. */
  feetSplit?: boolean;
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
  /** 0 = level gaze, 1 = chin fully raised, negative = chin down (a nod). */
  lookUp?: number;
  /** extra lateral head tilt in degrees — the channel that carries most of
   *  what reads as "listening" or "making a point". */
  tilt?: number;
  /** -1..1 lean from the ankles. */
  lean?: number;
  /** breath amplitude; 1 is the resting idle. */
  breath?: number;
  /** breath phase in radians (so several characters do not inhale in unison). */
  breathPhase?: number;
  /** slow standing weight shift, -1..1. */
  sway?: number;
  /** which head artwork to draw — "head", or "head__open"/"head__oh"/... for
   *  a viseme variant. The variants differ ONLY inside the mouth mask, so a
   *  variant head registers exactly with the base body. */
  headPart?: string;
};

const Part: React.FC<{
  rig: Rig;
  /** which artwork file to draw */
  src: string;
  /** which pivot to rotate about */
  pivot: string;
  rot?: number;
  dx?: number;
  dy?: number;
  sx?: number;
  sy?: number;
  z: number;
  /** CSS inset() clip, applied in the part's own rest space BEFORE the
   *  transform — so the clipped piece rotates as one object. */
  clip?: string;
}> = ({rig, src, pivot, rot = 0, dx = 0, dy = 0, sx = 1, sy = 1, z, clip}) => {
  const file = rig.parts[src];
  if (!file) return null;
  const [px, py] = rig.pivots[pivot] ?? [0.5, 0.5];
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
      <div style={{position: "absolute", inset: 0, clipPath: clip}}>
        <Img
          src={staticFile(file)}
          style={{position: "absolute", inset: 0, width: "100%", height: "100%"}}
        />
      </div>
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
    tilt = 0,
    lean = 0,
    breath = 1,
    breathPhase = 0,
    sway = 0,
    headPart = "head",
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
  // This cast walks with a WADDLE, and that is a fact about the drawings
  // rather than a stylistic choice. Sol's cardigan hangs to his shoe tops:
  // his silhouette is one unbroken mass down to y=0.938, so there are no legs
  // to swing. What he has is two feet below that line and a heavy body above
  // it, which is exactly the Peanuts/chibi cycle — the body rocks, the feet
  // alternate, and the weight lands on the planted side.
  //
  // Feet alternate in counter-phase; the body bobs at DOUBLE that frequency
  // because the hips rise once per step, not once per cycle. Arms counter-
  // swing against the feet, which is what stops a walk reading as a shuffle.
  const s = stride;
  const stepL = Math.sin(walkPhase);
  const stepR = Math.sin(walkPhase + Math.PI);
  const footLRot = stepL * 9 * s;
  const footRRot = stepR * 9 * s;
  // a foot lifts as it swings forward and plants as it comes back
  const footLDy = -Math.max(0, stepL) * rig.h * 0.016 * s;
  const footRDy = -Math.max(0, stepR) * rig.h * 0.016 * s;
  const bob = -Math.abs(Math.cos(walkPhase)) * rig.h * 0.012 * s;
  // the rock: the body leans over whichever foot is planted
  const rock = -stepL * 2.6 * s;
  const walkLean = 2.4 * s;
  const armSwing = stepR * 11 * s;

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
  const lookSy = 1 + 0.02 * Math.abs(u);

  // Per-arm resolution. The gesture lives on a NAMED arm, not on whichever
  // arm happens to be nearest — Sol's pointing hand is his screen-left one,
  // and it has to keep pointing while he turns, not hop across his body.
  const arm = (name: "armL" | "armR") => {
    const isL = name === "armL";
    const far = isL ? lIsFar : !lIsFar;
    const isGesture = name === gestureArm;
    return {
      src: name,
      pivot: name,
      // far arm goes behind the torso; a raised gesture goes above the head
      z: far && at > 0.12 ? 1 : isGesture && p > 0.5 ? 6 : far ? 3 : 4,
      // Arms take the TORSO's scale, not their own. They used to shrink
      // (far) and swell (near) independently, which is the textbook
      // silhouette cue — but this cast's line art is one shared path living
      // in `body`, so an arm scaled differently from the torso pulls its
      // fill off its own outline and leaves an arm-shaped void. Occlusion
      // is the stronger cue anyway and costs nothing.
      sx: torsoSx,
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

  // THE CUT. The body ships as one piece of artwork and is drawn three times,
  // each clipped to a different region and transformed on its own. The cut
  // sits ABOVE the crotch and the torso draw covers it, so the straight edge
  // is never on screen and each foot swings about a pivot nobody can see.
  const cut = rig.legCut ?? 0.9;
  const fm = rig.footMid ?? 0.5;
  const pc = (v: number) => `${(v * 100).toFixed(3)}%`;
  const clipFootL = `inset(${pc(cut)} ${pc(1 - fm)} 0% 0%)`;
  const clipFootR = `inset(${pc(cut)} 0% 0% ${pc(fm)})`;
  // overlap past the cut so the seam is buried under the torso

  const clipFeet = `inset(${pc(cut)} 0% 0% 0%)`;
  const split = rig.feetSplit !== false;
  // THE LINE ART FOLLOWS THE HEAD. vtracer traced this cast's whole outline
  // as ONE closed contour — 759x1141 of a 771x1159 canvas, a single subpath,
  // so it cannot be divided by geometry. Leaving it all in the torso meant
  // the head could turn but its OUTLINE stayed put, which is why every
  // amplitude had to be kept apologetically small. Cutting the silhouette
  // at the neck and carrying the upper band on the head's own transform
  // fixes that: the outline turns with the face. The head part draws over
  // the cut, so the straight edge is never visible.
  const neck = rig.neck ?? 0.48;
  const clipHeadBand = `inset(0% 0% ${pc(1 - neck)} 0%)`;
  const clipTorsoBand = `inset(${pc(neck)} 0% ${pc(1 - Math.min(1, cut + 0.075))} 0%)`;

  return (
    <>
      <Part rig={rig} {...armL} />
      <Part rig={rig} {...armR} />
      {split ? (
        <>
          <Part
            rig={rig}
            src="body"
            pivot="legL"
            clip={clipFootL}
            z={1}
            rot={footLRot + leanRot * 0.2}
            dx={legDx + swayDx * 0.4}
            dy={footLDy}
            sx={torsoSx}
          />
          <Part
            rig={rig}
            src="body"
            pivot="legR"
            clip={clipFootR}
            z={1}
            rot={footRRot + leanRot * 0.2}
            dx={legDx + swayDx * 0.4}
            dy={footRDy}
            sx={torsoSx}
          />
        </>
      ) : (
        <Part
          rig={rig}
          src="body"
          pivot="torso"
          clip={clipFeet}
          z={1}
          dx={legDx + swayDx * 0.4}
          sx={torsoSx}
        />
      )}
      <Part
        rig={rig}
        src="body"
        pivot="torso"
        clip={clipTorsoBand}
        z={2}
        rot={leanRot + walkLean + rock + sway * 0.6}
        dx={torsoDx + swayDx}
        dy={-br * 2 + bob}
        sx={torsoSx * (1 - br * 0.004)}
        sy={1 + br * 0.006}
      />
      <Part
        rig={rig}
        src="body"
        pivot="head"
        clip={clipHeadBand}
        z={0}
        rot={headRot + lookRot + tilt + leanRot * 0.5 + rock * 0.8 + brLag * 0.5 + sway * 1.9}
        dx={headDx + swayDx * 1.6}
        dy={-brLag * 4.2 + lookDy + bob * 1.15}
        sx={headSx * (1 + brLag * 0.003)}
        sy={lookSy * (1 + brLag * 0.004)}
      />
      <Part
        rig={rig}
        src={rig.parts[headPart] ? headPart : "head"}
        pivot="head"
        z={5}
        rot={headRot + lookRot + tilt + leanRot * 0.5 + rock * 0.8 + brLag * 0.5 + sway * 1.9}
        dx={headDx + swayDx * 1.6}
        dy={-brLag * 4.2 + lookDy + bob * 1.15}
        sx={headSx * (1 + brLag * 0.003)}
        sy={lookSy * (1 + brLag * 0.004)}
      />
    </>
  );
};
