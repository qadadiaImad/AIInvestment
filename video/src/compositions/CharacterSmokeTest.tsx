// Phase 5 smoke test: one 8s vertical (1080x1920) reel per character, using ONLY
// the Phase-3-approved additive enhancements — never a redesign of the existing
// rig/definition. Layer stack (bottom -> top): BgMesh -> character (Entrance +
// existing rig, unmodified) -> name/tagline card -> Grade -> Grain -> Vignette ->
// SafeZoneGuide (debug only).
import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { z } from "zod";
import { RIGS, CHARACTERS, type CharKey } from "../characters/registry";
import { Entrance } from "../components/Entrance";
import { BgMesh } from "../components/BgMesh";
import { Grade } from "../components/Grade";
import { SafeZoneGuide } from "../components/SafeZoneGuide";
import { Grain, Vignette } from "../../../remotion/src/motion/Polish";
import { theme } from "../theme";

export const characterSmokeTestSchema = z.object({
  character: z.enum(["chip", "watt", "qubit", "cap", "nova", "cloudy"]),
  debugSafeZone: z.boolean().optional(),
});

export const CharacterSmokeTest: React.FC<z.infer<typeof characterSmokeTestSchema>> = ({
  character,
  debugSafeZone,
}) => {
  const frame = useCurrentFrame();
  const Rig = RIGS[character as CharKey];
  const meta = CHARACTERS.find((c) => c.key === character)!;

  // Idle breathing once settled (SKILL.md rule 7 / motion-patterns.md §12).
  const breathe = 1 + Math.sin(frame / 22) * 0.015;

  return (
    <AbsoluteFill>
      <BgMesh hero={meta.color} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <Entrance delay={6}>
          <div style={{ transform: `scale(${breathe})` }}>
            <Rig size={460} mode="wave" />
          </div>
        </Entrance>
      </AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-start", paddingTop: 210 }}>
        <Entrance delay={16}>
          <div style={{ textAlign: "center" }}>
            <div
              style={{
                fontFamily: theme.fonts.display,
                fontWeight: 700,
                fontSize: 96,
                color: theme.colors.text,
                letterSpacing: "-0.03em",
              }}
            >
              {meta.name}
            </div>
            <div
              style={{
                fontFamily: theme.fonts.body,
                fontWeight: 500,
                fontSize: 34,
                color: meta.color,
                marginTop: 8,
              }}
            >
              {meta.role}
            </div>
          </div>
        </Entrance>
      </AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end", paddingBottom: 260 }}>
        <Entrance delay={26}>
          <div
            style={{
              fontFamily: theme.fonts.body,
              fontWeight: 400,
              fontSize: 38,
              color: theme.colors.textDim,
              maxWidth: 820,
              textAlign: "center",
              padding: "0 60px",
            }}
          >
            {meta.tagline}
          </div>
        </Entrance>
      </AbsoluteFill>
      <Grade hero={meta.color} />
      <Grain />
      <Vignette />
      <SafeZoneGuide enabled={debugSafeZone} />
    </AbsoluteFill>
  );
};
