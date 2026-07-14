"use client";

import { useEffect, useState } from "react";

const CARD_WIDTH = 1080;

// Wraps CaptureCard ONLY for on-screen human review at
// /terminal/card/[symbol] (without ?capture=1). Computes a CSS transform
// scale purely for the owner's phone preview. This scale wrapper is
// IRRELEVANT to the actual capture: Claude's Playwright screenshot step
// targets #capture-canvas directly (an element screenshot at native DOM
// pixel size), which is unaffected by any ancestor's CSS transform.
export default function CardScaleShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const [scale, setScale] = useState(1);

  useEffect(() => {
    function update() {
      setScale(Math.min(1, window.innerWidth / CARD_WIDTH));
    }
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  return (
    <div
      style={{
        width: "100%",
        display: "flex",
        justifyContent: "center",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: CARD_WIDTH * scale,
          height: 1350 * scale,
        }}
      >
        <div
          style={{
            transform: `scale(${scale})`,
            transformOrigin: "top left",
          }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}
