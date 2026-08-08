// ARCADE VERSUS — the alternative art direction, built so it can be
// compared against the panel-desk episodes rather than argued about.
//
// The owner looked at the politician caricature probes, said they read like
// arcade games rather than JoJo, and asked whether that could be used
// deliberately to land jokes and opinions. This is that, built out.
//
// WHY THE GENRE FITS THIS SERIES, in one line each:
//
//   * NUMBERS. House rule: code owns every number, and a generated image
//     may never carry a figure. An arcade HUD — health bars, round timer,
//     combo counter, result plate — is a code layer BY NATURE. Everything
//     numeric below is drawn here, in this file. The generated art supplies
//     only a stage and three fighters, every surface of them blank.
//   * IP LEAK. "1990s arcade fighting game" is a genre, not one
//     rights-holder's character. The JoJo tag kept dragging Jotaro into
//     frame — four of five failures in the last exhibit gate. This does
//     not have that failure mode.
//   * MOTION. The house animation grammar in motion/toon.ts already IS
//     sprite grammar: anticipation, volume-preserving squash/stretch,
//     2-frame smears, three-beat holds. Reused here unchanged.
//
// THE CONTENT IS THE EPISODE'S OWN FACT, not a new claim: a tracked
// lawmaker household's disclosed 2024 return against a fund that copies
// those disclosures 45 days late, against the S&P 500. The round timer
// counts down 45 — the lag IS the clock. Educational, parody, public
// record, no advice, and the loser is a strategy rather than a person.
import React from "react";
import {AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate,
  Easing} from "remotion";
import {squash, actionCurve, smear, impact} from "../motion/toon";
import {Grain, Vignette} from "../motion/Polish";

export const ARCADE_FRAMES = 540;          // 18s at 30fps
const W = 1080;

const NAVY = "#0A1020";
const AMBER = "#FFC24A";
const TEAL = "#3FD2C7";
const BURG = "#C0426A";
const INK = "#050810";

// ---------------------------------------------------------------- beats
const VS_IN = 0, ROUND_CALL = 96, FIGHT = 132, KO = 402, RESULT = 444;

// The three figures the round resolves into. Sourced, and labelled as
// reported rather than as fact of our own.
const ROWS = [
  {label: "DISCLOSED PORTFOLIO", pct: 70.9, tone: AMBER},
  {label: "COPYING IT, 45 DAYS LATE", pct: 26.8, tone: BURG},
  {label: "S&P 500", pct: 24.9, tone: TEAL},
];

const px = (n: number) => `${n}px`;

/** Chunky arcade lettering. No web font needed; Impact is already the
 *  house display face and it is what an arcade marquee looks like. */
const Arcade: React.FC<{size: number; color?: string; children: React.ReactNode;
  glow?: boolean; style?: React.CSSProperties}> =
  ({size, color = "#FFFFFF", children, glow, style}) => (
    <div style={{fontFamily: "Impact, Haettenschweiler, Arial Black, sans-serif",
      fontSize: px(size), color, letterSpacing: size * 0.02,
      lineHeight: 1.02, WebkitTextStroke: `${Math.max(2, size * 0.045)}px ${INK}`,
      paintOrder: "stroke fill",
      textShadow: glow ? `0 0 ${px(size * 0.5)} ${color}88` : "none",
      ...style}}>{children}</div>
  );

/** HEALTH BAR. Drains in hard steps, never smoothly — a continuous drain
 *  reads as a progress bar, a stepped one reads as hits landing. */
const HealthBar: React.FC<{frac: number; flip?: boolean; label: string;
  tone: string}> = ({frac, flip, label, tone}) => (
  <div style={{flex: 1, display: "flex",
    flexDirection: "column", alignItems: flip ? "flex-end" : "flex-start"}}>
    <div style={{width: "100%", height: 34, background: "#141C2E",
      border: `4px solid ${INK}`, boxShadow: `0 0 0 2px #2A3550`,
      display: "flex", justifyContent: flip ? "flex-end" : "flex-start"}}>
      <div style={{width: `${Math.max(0, Math.min(1, frac)) * 100}%`,
        height: "100%", background: `linear-gradient(180deg, ${tone}, ${tone}AA)`,
        boxShadow: `0 0 18px ${tone}99`}} />
    </div>
    <Arcade size={26} color="#C9D6F2" style={{marginTop: 8}}>{label}</Arcade>
  </div>
);

/** One fighter, cropped out of its own generated frame. Every fighter
 *  plate is a figure centred on a flat dark-navy stage, so two of them
 *  butted together share one continuous background and the seam does not
 *  show — which is why they are composited this way rather than cut out. */
const Fighter: React.FC<{file: string; flip?: boolean; hit: number;
  lean: number}> = ({file, flip, hit, lean}) => {
  const sq = squash(hit > 0 ? -0.16 * hit : 0);
  const sm = smear(hit > 0 ? (1 - hit) * 2 : 99, 1.1 * hit);
  return (
    <div style={{flex: 1, overflow: "hidden", position: "relative"}}>
      <div style={{position: "absolute", inset: 0,
        transform: `translateX(${lean}px) scale(${sq.sx * sm.sx}, ${sq.sy * sm.sy})`,
        transformOrigin: "50% 100%",
        filter: sm.blur ? `blur(${sm.blur}px)` : "none"}}>
        {/* height:100% is what makes the plate COVER its panel. Sizing by
            width left bare strips above and below the art, and because
            each plate carries its own spotlight the bare edges read as a
            seam down the middle of the stage rather than as one room. */}
        <Img src={staticFile(`characters/cast_ep1/arcade/${file}.png`)}
          style={{position: "absolute", left: "50%", top: "50%",
            height: "100%", width: "auto", maxWidth: "none", transform:
              `translate(-50%,-50%) scaleX(${flip ? -1 : 1})`,
            imageRendering: "auto"}} />
      </div>
      {/* the hit flash, two frames, over the figure only */}
      {hit > 0.55 ? (
        <div style={{position: "absolute", inset: 0,
          background: "#FFFFFF", opacity: (hit - 0.55) * 0.9,
          mixBlendMode: "overlay"}} />
      ) : null}
    </div>
  );
};

export const ArcadeVersus: React.FC = () => {
  const f = useCurrentFrame();

  // ---- round state, all derived, all integers on screen -------------
  const roundT = Math.max(0, Math.min(1, (f - FIGHT) / (KO - FIGHT)));
  // the timer IS the 45-day lag, counted down
  const clock = Math.max(0, Math.ceil(45 * (1 - roundT)));
  // hits land on a fixed cadence so sound could be cut to them later
  const HITS = [162, 198, 234, 270, 300, 330, 360, 384];
  const lastHit = HITS.filter((h) => f >= h).length;
  const sinceHit = HITS.reduce((a, h) => (f >= h && f - h < a ? f - h : a), 99);
  const hit = f >= FIGHT && f < KO ? impact(sinceHit, 12) : 0;

  // P1 barely drops, P2 drains with every hit - the lag does the damage
  const p1 = 1 - 0.03 * lastHit;
  const p2 = 1 - 0.12 * lastHit;

  // ---- VS screen ----------------------------------------------------
  const vsA = actionCurve(f - VS_IN, 5, 8, 10);
  const inL = interpolate(vsA, [0, 1], [-620, 0]);
  const inR = interpolate(vsA, [0, 1], [620, 0]);
  const vsPlate = actionCurve(f - (VS_IN + 22), 4, 6, 8);

  const showVS = f < ROUND_CALL;
  const showResult = f >= RESULT;

  // camera shake on every hit and on the KO
  const koShake = f >= KO && f < RESULT ? impact(f - KO, 20) : 0;
  const shake = (hit * 10 + koShake * 26);
  const seedX = Math.sin(f * 2.7) * shake;
  const seedY = Math.cos(f * 3.1) * shake * 0.6;

  return (
    <AbsoluteFill style={{background: NAVY, overflow: "hidden"}}>
      <AbsoluteFill style={{transform: `translate(${seedX}px, ${seedY}px)`}}>
        {/* THE STAGE IS THE FIGHTER PLATES THEMSELVES. A separate stage
            image behind them fought the spotlight each plate already
            carries; two covering plates butted together read as one room. */}
        <div style={{position: "absolute", left: 0, top: 300, width: W,
          height: 1240, display: "flex"}}>
          <Fighter file="fighter_pelosi"
            lean={showVS ? inL : Math.min(40, lastHit * 5)} hit={0} />
          <Fighter file="fighter_retail" flip
            lean={showVS ? inR : -Math.min(40, lastHit * 5)} hit={hit} />
        </div>
        {/* seam softener + stage light, over the join */}
        <div style={{position: "absolute", left: 0, top: 300, width: W,
          height: 1240, pointerEvents: "none", background:
            "linear-gradient(90deg, rgba(10,16,32,0.55) 0%, rgba(10,16,32,0) 22%,"
            + " rgba(10,16,32,0) 78%, rgba(10,16,32,0.55) 100%),"
            + "radial-gradient(ellipse 62% 48% at 50% 66%, rgba(255,194,74,0.18) 0%,"
            + " rgba(10,16,32,0) 72%)"}} />
        {/* the band is bounded top and bottom so the HUD sits on ink */}
        <div style={{position: "absolute", left: 0, top: 300, width: W,
          height: 150, pointerEvents: "none", background:
            "linear-gradient(180deg, #0A1020 0%, rgba(10,16,32,0) 100%)"}} />
        <div style={{position: "absolute", left: 0, top: 1390, width: W,
          height: 150, pointerEvents: "none", background:
            "linear-gradient(0deg, #0A1020 0%, rgba(10,16,32,0) 100%)"}} />

        {/* ---------------- HUD. Every numeral below is code. ---------- */}
        <div style={{position: "absolute", left: 44, right: 44, top: 70,
          display: "flex", alignItems: "flex-start", gap: 26}}>
          <HealthBar frac={p1} tone={AMBER} label="DISCLOSED PORTFOLIO" />
          <div style={{textAlign: "center", minWidth: 150}}>
            <Arcade size={92} color={clock <= 9 ? BURG : "#FFFFFF"} glow
              style={{textAlign: "center"}}>{clock}</Arcade>
            <Arcade size={22} color="#8FA3CC" style={{textAlign: "center"}}>
              DAYS OF LAG
            </Arcade>
          </div>
          <HealthBar frac={p2} flip tone={BURG} label="COPYING IT, LATE" />
        </div>

        {/* COMBO COUNTER — arcade furniture, and it is honest: it counts
            the hits the lag has landed, nothing more. */}
        {f >= FIGHT && f < KO && lastHit > 1 ? (
          <div style={{position: "absolute", right: 54,
            top: 1580 + (1 - hit) * 8}}>
            <Arcade size={100} color={AMBER} glow style={{textAlign: "right"}}>
              {lastHit}
            </Arcade>
            <Arcade size={30} color="#C9D6F2" style={{textAlign: "right"}}>
              HITS TAKEN
            </Arcade>
          </div>
        ) : null}

        {/* VS PLATE */}
        {showVS ? (
          <div style={{position: "absolute", left: 0, right: 0, top: 830,
            display: "flex", justifyContent: "center"}}>
            <div style={{transform: `scale(${0.6 + vsPlate * 0.7}) rotate(${-6 + vsPlate * 6}deg)`,
              opacity: Math.min(1, vsPlate * 1.4)}}>
              <Arcade size={260} color={AMBER} glow>VS</Arcade>
            </div>
          </div>
        ) : null}

        {/* ROUND CALL */}
        {f >= ROUND_CALL && f < FIGHT + 26 ? (() => {
          const a = actionCurve(f - ROUND_CALL, 4, 6, 8);
          const fight = f >= FIGHT;
          return (
            <div style={{position: "absolute", left: 0, right: 0, top: 880,
              display: "flex", justifyContent: "center",
              transform: `scale(${0.7 + a * 0.5})`}}>
              <Arcade size={fight ? 190 : 120} color={fight ? BURG : "#FFFFFF"} glow>
                {fight ? "FIGHT!" : "ROUND 1"}
              </Arcade>
            </div>
          );
        })() : null}

        {/* K.O. */}
        {f >= KO && f < RESULT ? (() => {
          const a = actionCurve(f - KO, 3, 5, 9);
          return (
            <div style={{position: "absolute", left: 0, right: 0, top: 820,
              display: "flex", justifyContent: "center",
              transform: `scale(${0.5 + a * 0.9}) rotate(${(1 - a) * -12}deg)`}}>
              <Arcade size={240} color={BURG} glow>K.O.</Arcade>
            </div>
          );
        })() : null}

        {/* RESULT — the actual numbers, drawn, sourced and attributed. */}
        {showResult ? (
          <AbsoluteFill style={{background: "rgba(5,8,16,0.9)",
            padding: "260px 70px", justifyContent: "flex-start"}}>
            <Arcade size={72} color={AMBER} glow>2024, AS REPORTED</Arcade>
            <div style={{marginTop: 56}}>
              {ROWS.map((r, i) => {
                const a = interpolate(f - RESULT - i * 10, [0, 22], [0, 1],
                  {extrapolateLeft: "clamp", extrapolateRight: "clamp",
                   easing: Easing.out(Easing.cubic)});
                return (
                  <div key={r.label} style={{marginBottom: 40}}>
                    <div style={{display: "flex", justifyContent: "space-between",
                      alignItems: "flex-end"}}>
                      <Arcade size={34} color="#C9D6F2">{r.label}</Arcade>
                      <Arcade size={56} color={r.tone}>
                        {(r.pct * a).toFixed(1)}%
                      </Arcade>
                    </div>
                    <div style={{height: 26, marginTop: 10, background: "#141C2E",
                      border: `3px solid ${INK}`}}>
                      <div style={{height: "100%",
                        width: `${(r.pct / 80) * 100 * a}%`,
                        background: r.tone, boxShadow: `0 0 16px ${r.tone}88`}} />
                    </div>
                  </div>
                );
              })}
            </div>
            <Arcade size={30} color="#8FA3CC" style={{marginTop: 20,
              lineHeight: 1.35}}>
              THE EDGE SURVIVES THE DELAY.<br />MOST OF IT DOES NOT.
            </Arcade>
          </AbsoluteFill>
        ) : null}

        {/* the rail, on every frame, exactly as the episodes carry it */}
        <div style={{position: "absolute", left: 0, right: 0, bottom: 26,
          textAlign: "center", fontFamily: "Arial", fontSize: 21,
          letterSpacing: 1.6, color: "#7C8CAE"}}>
          parody · public record · educational, not advice · not an accusation
        </div>
        <div style={{position: "absolute", left: 0, right: 0, bottom: 58,
          textAlign: "center", fontFamily: "Arial", fontSize: 19,
          letterSpacing: 1.1, color: "#5D6C8C"}}>
          portfolio: Unusual Whales 2024 report · fund: NANC 2024 total return
        </div>
      </AbsoluteFill>
      <Vignette strength={0.5} />
      <Grain opacity={0.04} />
    </AbsoluteFill>
  );
};
