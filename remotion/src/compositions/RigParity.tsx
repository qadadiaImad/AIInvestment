// RigParity — proves the rig is a safe drop-in for the flat drawing.
//
// The rig is now the renderer inside FairMarketEp1's Char. That is only
// acceptable if, with every channel at rest, it draws EXACTLY what the flat
// <Img> drew — otherwise wiring it in silently restages 39 approved beats.
//
// Asserting that is worthless; this measures it. Each row stacks the flat
// drawing over the rigged one with mix-blend-mode: difference, so identical
// pixels come out pure black and any discrepancy glows. The third column
// repeats the test with a VISEME head swapped in, which is the case that
// actually has to hold for a rigged character to keep talking.
import React from "react";
import {AbsoluteFill, Img, staticFile} from "remotion";
import rigParts from "../fixtures/cast_ep1/rig_parts.json";
import visemes from "../fixtures/cast_ep1/visemes.json";
import anchors from "../fixtures/cast_ep1/pose_anchors.json";
import {CharRig, type Rig} from "../motion/CharRig";

export const RIGPARITY_FRAMES = 1;

const RIG = rigParts as unknown as Record<string, Rig>;
const VI = visemes as unknown as Record<string, Record<string, string>>;
const AN = anchors as unknown as Record<string, {src: string}>;

const POSES = ["sol_point", "sol_smug", "rex_skeptic", "rex_shock", "sol_laugh"];

const Cell: React.FC<{
  label: string;
  flat: string;
  rig: Rig;
  headPart?: string;
  w: number;
  h: number;
  mode?: "diff" | "rig" | "flat";
}> = ({label, flat, rig, headPart, w, h, mode = "diff"}) => (
  <div style={{width: w, marginRight: 18}}>
    <div style={{position: "relative", width: w, height: h, background: "#000"}}>
      {mode !== "flat" ? <CharRig rig={rig} pose={{breath: 0, headPart}} /> : null}
      {mode !== "rig" ? (
        <Img
          src={staticFile(flat)}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            // the rig's parts carry z-index 1..6; without a z above them the
            // difference layer is painted UNDER the stack and never blends
            zIndex: 99,
            ...(mode === "diff" ? {mixBlendMode: "difference" as const} : {}),
          }}
        />
      ) : null}
    </div>
    <div style={{fontFamily: "Arial", fontSize: 15, color: "#C8D2E4", marginTop: 6}}>
      {label}
    </div>
  </div>
);

export const RigParity: React.FC = () => (
  <AbsoluteFill style={{background: "#11151C", padding: 26}}>
    <div
      style={{
        fontFamily: "Impact, Arial",
        fontSize: 30,
        letterSpacing: 1,
        color: "#EDF2FA",
        marginBottom: 4,
      }}
    >
      PARITY — flat drawing XOR rigged-at-rest. Pure black = identical.
    </div>
    <div style={{fontFamily: "Arial", fontSize: 16, color: "#8794A8", marginBottom: 16}}>
      Any glow is a pixel the rig moved that the flat drawing did not.
    </div>
    {POSES.map((pose) => {
      const rig = RIG[pose];
      const an = AN[pose];
      if (!rig || !an) return null;
      const h = 300;
      const w = h * (rig.w / rig.h);
      const vi = VI[pose] ?? {};
      const vkey = vi.open ? "open" : vi.half ? "half" : vi.closed ? "closed" : null;
      return (
        <div
          key={pose}
          style={{display: "flex", alignItems: "flex-start", marginBottom: 14}}
        >
          <div
            style={{
              width: 190,
              fontFamily: "Arial",
              fontSize: 17,
              color: "#EDF2FA",
              paddingTop: h / 2 - 10,
            }}
          >
            {pose}
          </div>
          <Cell label="flat" flat={an.src} rig={rig} w={w} h={h} mode="flat" />
          <Cell label="rig at rest" flat={an.src} rig={rig} w={w} h={h} mode="rig" />
          <Cell label="XOR" flat={an.src} rig={rig} w={w} h={h} />
          {vkey ? (
            <Cell
              label={`XOR viseme "${vkey}"`}
              flat={vi[vkey]}
              rig={rig}
              headPart={"head__" + vkey}
              w={w}
              h={h}
            />
          ) : (
            <div style={{width: w, marginRight: 18}} />
          )}
        </div>
      );
    })}
  </AbsoluteFill>
);
