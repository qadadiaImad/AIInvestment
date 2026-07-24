// A mascot "plays" in front of real company logos orbiting a TSM center mark
// (../components/OrbitBackground.tsx, sourced from ../data/orbitLogos.ts)
// while staged captions tell the chokepoint's story. Contrast is the point: a
// cheerful character delivering a genuinely serious supply-chain risk, the
// way Kurzgesagt-style explainers do it.
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { z } from "zod";
import { RIGS, CHARACTERS, type CharKey } from "../characters/registry";
import { Entrance } from "../components/Entrance";
import { Grade } from "../components/Grade";
import { OrbitBackground } from "../components/OrbitBackground";
import { SafeZoneGuide } from "../components/SafeZoneGuide";
import { Grain, Vignette } from "../../../remotion/src/motion/Polish";
import { theme } from "../theme";

type Beat = { frame: number; x: number; mode: "idle" | "walk" | "wave" | "point" | "jump" | "turn" };
type Caption = { from: number; duration: number; lines: string[] };

const WAYPOINTS: Beat[] = [
  { frame: 0, x: 0.18, mode: "walk" },
  { frame: 45, x: 0.18, mode: "wave" },
  { frame: 90, x: 0.5, mode: "walk" },
  { frame: 140, x: 0.5, mode: "point" },
  { frame: 270, x: 0.74, mode: "walk" },
  { frame: 320, x: 0.74, mode: "jump" },
  { frame: 450, x: 0.28, mode: "walk" },
  { frame: 500, x: 0.28, mode: "point" },
  { frame: 630, x: 0.5, mode: "walk" },
  { frame: 680, x: 0.5, mode: "wave" },
];

const CAPTIONS: Caption[] = [
  { from: 0, duration: 45, lines: ["Meet the single point of failure", "sitting under every AI stock you own."] },
  { from: 48, duration: 42, lines: ["One company.", "One island.", "TSMC."] },
  { from: 95, duration: 175, lines: ["More than 90% of the world's", "leading-edge chips run through it."] },
  { from: 275, duration: 175, lines: ["Nvidia, AMD, Broadcom —", "all renting time on the same line."] },
  { from: 455, duration: 175, lines: ["Even TSMC has a single point of failure:", "ASML is its only source for EUV lithography."] },
  { from: 635, duration: 100, lines: ["One earthquake. One blockade.", "The whole AI stack stalls."] },
  { from: 738, duration: 42, lines: ["Chokepoint #1 of 13 — save this,", "more of the series coming."] },
];

function modeAt(frame: number): Beat["mode"] {
  let m: Beat["mode"] = "idle";
  for (const b of WAYPOINTS) {
    if (frame >= b.frame) m = b.mode;
  }
  return m;
}

const StoryCaption: React.FC<{ c: Caption; frame: number; heroColor: string }> = ({ c, frame, heroColor }) => {
  const local = frame - c.from;
  if (local < 0 || local > c.duration) return null;
  const exitStart = c.duration - 14;
  const opacity =
    local < exitStart
      ? 1
      : interpolate(local, [exitStart, c.duration], [1, 0], {
          easing: theme.ease.in,
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-start", paddingTop: 190, opacity }}>
      <Entrance delay={0}>
        <div style={{ textAlign: "center", padding: "0 90px" }}>
          {c.lines.map((line, i) => (
            <div
              key={i}
              style={{
                fontFamily: theme.fonts.display,
                fontWeight: 700,
                fontSize: 62,
                lineHeight: 1.18,
                color: i === c.lines.length - 1 ? heroColor : theme.colors.text,
                textShadow: "0 2px 20px rgba(0,0,0,0.6)",
              }}
            >
              {line}
            </div>
          ))}
        </div>
      </Entrance>
    </AbsoluteFill>
  );
};

export const chokepointStorySchema = z.object({
  character: z.enum(["chip", "watt", "qubit", "cap", "nova", "cloudy"]).default("chip"),
  debugSafeZone: z.boolean().optional(),
});

export const ChokepointStory: React.FC<z.infer<typeof chokepointStorySchema>> = ({
  character,
  debugSafeZone,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const Rig = RIGS[character as CharKey];
  const meta = CHARACTERS.find((c) => c.key === character)!;

  const xFrac = interpolate(
    frame,
    WAYPOINTS.map((b) => b.frame),
    WAYPOINTS.map((b) => b.x),
    { easing: theme.ease.inOut, extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const mode = modeAt(frame);
  const bob = mode === "walk" ? Math.sin(frame / 5) * 6 : Math.sin(frame / 22) * 4;

  return (
    <AbsoluteFill style={{ background: theme.colors.bg }}>
      <OrbitBackground heroColor={meta.color} />
      <Grade hero={meta.color} opacity={0.14} />

      {/* character, walking a ground line ~78% down the frame */}
      <div
        style={{
          position: "absolute",
          left: xFrac * width,
          top: height * 0.78 + bob,
          transform: "translate(-50%, -100%)",
        }}
      >
        <Rig size={340} mode={mode} />
      </div>

      {CAPTIONS.map((c, i) => (
        <StoryCaption key={i} c={c} frame={frame} heroColor={meta.color} />
      ))}

      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-start", paddingTop: 70 }}>
        <div
          style={{
            fontFamily: theme.fonts.mono,
            fontWeight: 700,
            fontSize: 26,
            letterSpacing: "0.08em",
            color: theme.colors.textDim,
          }}
        >
          CHOKEPOINT #1 — {meta.name.toUpperCase()} EXPLAINS
        </div>
      </AbsoluteFill>

      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end", paddingBottom: 90 }}>
        <div
          style={{
            fontFamily: theme.fonts.body,
            fontWeight: 500,
            fontSize: 24,
            color: theme.colors.textDim,
          }}
        >
          Educational only — not financial advice · DYOR
        </div>
      </AbsoluteFill>

      <Grain />
      <Vignette />
      <SafeZoneGuide enabled={debugSafeZone} />
    </AbsoluteFill>
  );
};
