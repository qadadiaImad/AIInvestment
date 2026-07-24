// Word-synced captions over character footage/voice-over.
// Source: haidrrrry/claude-remotion-skill references/motion-patterns.md §17
// (@remotion/captions createTikTokStyleCaptions) + design-rules.md typography
// ("2–4 words per page, active word in theme color, positioned at ~65% height,
// inside the 9:16 safe zone").
//
// This is a genuinely new wiring: CaptionTrack.tsx already exists in
// ../../../remotion/src/components but only serves HalalVerdictReel via a
// bespoke captionWordSchema + brand.ts import. Rather than duplicate that (or
// couple this project to brand.ts, which Phase 3 flagged as the legacy/
// inconsistent token file), this uses the official @remotion/captions API
// directly against this project's own theme.
import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { createTikTokStyleCaptions, type Caption } from "@remotion/captions";
import { theme } from "../theme";

export const Captions: React.FC<{ captions: Caption[]; heroColor: string }> = ({
  captions,
  heroColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentMs = (frame / fps) * 1000;

  const { pages } = createTikTokStyleCaptions({
    captions,
    combineTokensWithinMilliseconds: 1200, // ~2-4 words/page at natural speech pace
  });

  const page = pages.find(
    (p) => currentMs >= p.startMs && currentMs < p.startMs + p.durationMs
  );
  if (!page) return null;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: "65%",
          left: "8%",
          right: "8%",
          textAlign: "center",
          fontFamily: theme.fonts.display,
          fontWeight: 700,
          fontSize: 58,
          lineHeight: 1.15,
          textShadow: "0 2px 18px rgba(0,0,0,0.55)",
        }}
      >
        {page.tokens.map((token, i) => {
          const active = currentMs >= token.fromMs && currentMs < token.toMs;
          return (
            <span
              key={i}
              style={{
                color: active ? heroColor : theme.colors.text,
                marginRight: 14, // px gap, not em — em resolves against the parent
                // font-size and produces near-zero spacing next to display type
                // (motion-patterns.md §3 gotcha).
              }}
            >
              {token.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
