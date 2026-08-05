// RigTest — the five moves the owner asked for, driven off ONE drawing.
//
//   "needs in the final animation the character moving, walking, raise his
//    hand to the screen, look up, turn 45% and give viewers the shoulder
//    when talking to rex - 3d depicted in 2d"
//
// All five come out of the same six vector parts. Nothing here is generated:
// AnimateDiff produced boil, and anchored img2img would not turn the
// character at any denoise because the cast LoRA has only ever seen front
// views. See the header of motion/CharRig.tsx for the measurements.
import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {CharRig, type Rig, type RigPose} from "../motion/CharRig";
import rigParts from "../fixtures/cast_ep1/rig_parts.json";

export const RIGTEST_FRAMES = 420; // 14s at 30fps

const RIG = rigParts as unknown as Record<string, Rig>;
const POSE = "sol_point";

/** Each move gets a hold long enough to read, and the beats butt up against
 *  each other so the transitions are part of the test rather than hidden. */
const BEATS: {at: number; label: string}[] = [
  {at: 0, label: "IDLE — breath, weight shift"},
  {at: 70, label: "WALK — legs counter-phase, body bobs at 2×"},
  {at: 190, label: "RAISE HAND TO THE SCREEN"},
  {at: 260, label: "LOOK UP — head rides off the neck"},
  {at: 320, label: "TURN 45° — gives the viewer his shoulder"},
];

const ease = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, b], [from, to], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

const Stage: React.FC = () => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const rig = RIG[POSE];
  const t = frame / 30;

  // ── walk ──────────────────────────────────────────────────────────────
  // stride ramps in and out so the legs do not snap from still to full gait
  const stride = ease(frame, 70, 90) * (1 - ease(frame, 168, 188));
  const walkPhase = t * 6.6;
  // he actually crosses ground; a walk cycle in place is a treadmill
  const travel = interpolate(frame, [80, 180], [0, width * 0.2], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.quad),
  });

  const pointAt = ease(frame, 196, 222) * (1 - ease(frame, 252, 266));
  const lookUp = ease(frame, 266, 288) * (1 - ease(frame, 310, 322));
  const turn = ease(frame, 326, 356);

  const pose: RigPose = {
    turn,
    walkPhase,
    stride,
    pointAt,
    lookUp,
    lean: stride * 0.25,
    breath: 1,
    breathPhase: t * 2.0,
    sway: Math.sin(t * 0.72) * (1 - stride),
  };

  const boxH = height * 0.68;
  const boxW = boxH * (rig.w / rig.h);
  const label =
    [...BEATS].reverse().find((b) => frame >= b.at)?.label ?? BEATS[0].label;

  return (
    <AbsoluteFill style={{background: "#E8EDF4", overflow: "hidden"}}>
      {/* floor line, so the walk has ground to travel across and the bob
          has something to be measured against */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: height * 0.12,
          height: 2,
          background: "rgba(30,50,80,0.30)",
        }}
      />
      {/* the screen he gestures at and turns toward */}
      <div
        style={{
          position: "absolute",
          right: width * 0.05,
          top: height * 0.14,
          width: width * 0.3,
          height: height * 0.42,
          border: "3px solid #12864F",
          borderRadius: 10,
          background: "rgba(20,120,70,0.10)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "Impact, Arial",
          fontSize: 40,
          letterSpacing: 2,
          color: "#12864F",
        }}
      >
        THE SCREEN
      </div>

      <div
        style={{
          position: "absolute",
          left: width * 0.1 + travel,
          bottom: height * 0.12,
          width: boxW,
          height: boxH,
        }}
      >
        <CharRig rig={rig} pose={pose} />
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 26,
          textAlign: "center",
          fontFamily: "Impact, Arial",
          fontSize: 34,
          letterSpacing: 2,
          color: "#16203A",
        }}
      >
        {label}
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 18,
          textAlign: "center",
          fontFamily: "Arial",
          fontSize: 19,
          color: "#65748C",
        }}
      >
        one drawing · six vector parts · every in-between computed
      </div>
    </AbsoluteFill>
  );
};

export const RigTest: React.FC = () => {
  if (!RIG[POSE]) return <AbsoluteFill style={{background: "#E8EDF4"}} />;
  return <Stage />;
};
