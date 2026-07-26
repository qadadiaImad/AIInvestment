# Meme-reel pipeline — cartoon character reacting to a live chart

Build brief for a reel format: a rubber-hose cartoon character animated over an
illustrated room, reacting to a real chart playing inside a monitor on the desk.

> **BUILT — 2026-07-26.** First cut shipped:
> `content/meme_reel/intc_failed_breakout.mp4` (17.05s, 510f, 1080×1920).
> See [`content/meme_reel/README.md`](../content/meme_reel/README.md) for what
> actually got made and how to re-render it.
>
> **One deliberate deviation from §3/§4 below:** the character is a **pure SVG
> pivot rig**, not generated PNG limb layers. Rubber-hose is the one style where
> that trade inverts — thick constant-width outlines and flat fills *are* vector
> primitives, so drawing it directly *removes* the two failure modes §3 warns
> about (limbs detaching, style drift between separately generated layers)
> instead of managing them. Generated art still does the static room plate.
> Everything else below was followed as written.

**There is a ready-to-paste prompt at the bottom.** Pull this repo on your
laptop, open Claude Code in the repo root, and paste the block under
[§7 The prompt](#7-the-prompt). Everything above it is context for a human.

---

## 1. What the format actually is

Deconstructed from the reference reel (`joh.fx1`, 17s, 1170×2532 @60fps). It is
four independent layers, not one technique — which is exactly why trying to
generate the whole thing with an image-to-video model fails.

| Layer | What it is | How it moves |
|---|---|---|
| **Room plate** | Illustrated wall, clock, desk, monitor bezel. Muted beige, soft painterly. | Static. Camera moves over it. |
| **Character** | Rubber-hose meme figure — thick black outline, noodle limbs, bug eyes, white/grey fill. | Leans on the monitor, gestures, reacts. |
| **Screen** | Chart inside the monitor: entry line, stop line, a big running number. | Bars print; number counts. |
| **Camera** | Wide room shot ↔ monitor close-up. | Push-in and pan, with grain and slight blur. |

The story beat *is* the reel: setup → shock → payoff, in about 17 seconds.

## 2. Why not just generate the video

A generative model asked for "cartoon man reacts to trading chart" gives you:

- a character that drifts between shots,
- a chart that is illegible nonsense (models cannot draw a correct candlestick
  sequence, and will happily invent one that contradicts the caption),
- no way to hit a beat, so the punchline lands whenever the model felt like it.

We already learned the last two the hard way in this repo — see
`scripts/ta_quiz/validate.py` and the trigger-displacement repair, and the
`find_real_windows.py` rewrite after the first styles explainer shipped
synthetic charts.

**So: generate the ART once, animate and composite in Remotion.** Deterministic
timing, real data on the screen, and re-rendering with a different ticker is a
data change rather than a new generation.

## 3. Architecture

```
Higgsfield (once, per asset)          Remotion (every render)
─────────────────────────────         ─────────────────────────────
room plate .png            ─────►  background, parallax layer 0
monitor bezel .png (alpha) ─────►  foreground frame over the screen
character limb layers .png ─────►  RubberHoseRig, pivot-animated
                                   ScreenInsert  ← matrix3d onto the bezel quad
                                     └── TradingQuiz / TradingStyles chart
                                   PnLCounter, camera, Grain + Vignette
```

**The character must be generated as separate limb layers on transparent
background** — head, torso, upper arm, forearm, hand, thigh, shin, foot — not as
one flat figure. A single flat PNG can only be moved and scaled; layers can be
rigged. This is the single most important instruction to get right at the
generation step, because it cannot be fixed later.

## 4. What already exists in this repo

Reuse these; do not rebuild them.

| Asset | Where |
|---|---|
| Easing curves, spring configs, `stagger`, `cameraPushIn`, `parallax`, `DEPTH` | `remotion/src/motion/craft.ts` |
| `Grain`, `Vignette`, `KeyGlow` | `remotion/src/motion/Polish.tsx` |
| Pivot-rigged SVG character pattern (6 mascots) | `remotion/src/characters/*Rig.tsx` |
| Live tape chart engine — hard-tick candle printing, real OHLC | `remotion/src/compositions/TradingQuiz.tsx` |
| Real IBKR price bars + provenance stamps | `data/prices/*.json` |
| Regime window scanner | `scripts/trading_styles/find_real_windows.py` |
| Higgsfield generation | the `higgsfield-generate` skill |

Missing, and therefore the actual work:

1. **`RubberHoseRig.tsx`** — a limbed humanoid puppet. The existing rigs are
   blob mascots; they prove the pivot pattern but none of them has arms and legs.
2. **`ScreenInsert.tsx`** — perspective-maps a child composition onto the
   monitor quad via `matrix3d`, plus screen glow and a faint glass reflection.
3. **The room plate and character layers** — generated assets.

## 5. The rail — read this before writing any script

The reference reel's hook is **"I turned −19,168 into +123,716."** We cannot ship
that. It is a returns claim, and framing it as a meme does not make it less of
one — it reads as an implied achievable profit, which is exactly what this repo's
disclaimers exist to prevent.

**The format survives without it.** Point the character at a *pattern* instead of
a *payout*:

- he leans in as a breakout sets up, then facepalms when it closes back inside
  the box,
- he shrugs at a doji, because a doji on its own means nothing,
- he stares at a neckline break he was warned about.

Same comedy, same structure, real chart, no implied P&L. Every frame keeps the
standard footer. If a counter appears on screen it shows **price**, not profit.

## 6. Running it on a laptop

Two differences from the sandbox this brief was written in:

- **Drop `--browser-executable`.** That path (`/opt/pw-browsers/...`) only exists
  in the remote container. Remotion finds local Chrome on its own.
- **Render in one pass.** The three-chunk `--frames=` split in
  `content/trading_styles/README.md` was a 10-minute shell timeout in the
  sandbox, not a Remotion limitation.

---

## 7. The prompt

Paste everything between the rules into Claude Code, from the repo root.

---

> Read `references/meme-reel-pipeline.md` first — it is the brief for this task
> and explains the format, the architecture and the rails. Then build it.
>
> **Goal:** a 15–20 second vertical reel (1080×1920, 30fps) in which a
> rubber-hose cartoon character stands at a desk and reacts to a chart playing on
> the monitor in front of him. The chart must be REAL price data rendered by our
> existing engine, composited into the monitor with a perspective transform — not
> a drawn or generated chart.
>
> **Use a coordinated subagent workflow.** This is explicit authorisation to call
> the Workflow tool. Per `CLAUDE.md` §1 rule 7, every subagent must set
> `model: 'sonnet'`; only you run the top model. Keep the workflow under 15
> agents. Structure it roughly as:
>
> - **Phase 1 — Design (parallel, ~3 agents).** One agent specs the
>   `RubberHoseRig` joint hierarchy and the pose keyframes for each story beat.
>   One agent specs `ScreenInsert` (the `matrix3d` maths to map a 1080×1920 child
>   composition onto an arbitrary quad, plus glow and reflection). One agent
>   writes the Higgsfield prompts for the room plate and the character limb
>   layers, with a single locked style reference so they match.
> - **Phase 2 — Build (you, the orchestrator).** Write the components. Do not
>   delegate the TSX — agents writing React that has to compile and compose
>   consistently is where these runs fall apart. Agents produce specs and copy;
>   you write code.
> - **Phase 3 — Review (parallel, 2 agents, effort high).** One adversarially
>   checks the animation against the craft playbook: is anything linear, does
>   every gesture have anticipation and follow-through, does the character ever
>   move in a way a rubber-hose figure would not. One checks compliance: any
>   implied return, any profit figure, any missing disclaimer.
>
> **Hard requirements:**
>
> 1. **Reuse, do not rebuild.** `motion/craft.ts` for all easing and springs,
>    `motion/Polish.tsx` for grain and vignette, the `TradingQuiz` candle-printing
>    logic for the chart. Read `remotion/src/characters/chipRig.tsx` first to see
>    the established pivot-rig pattern and follow it.
> 2. **Real data only.** Pull the chart window from `data/prices/*.json` via
>    `scripts/trading_styles/find_real_windows.py`, or pull fresh bars from the
>    brokerage MCP (`get_price_history`) and stamp them with source, endpoint
>    parameters and retrieval time the way the existing price files are stamped.
>    Never author OHLC yourself and never let a subagent author it.
> 3. **No P&L, no returns claim.** See §5 of the brief. The character reacts to a
>    pattern, not to a profit. Any on-screen counter shows price. Keep the
>    standard footer on every frame.
> 4. **Character generated as separate limb layers**, transparent background —
>    head, torso, upper arm, forearm, hand, thigh, shin, foot. A single flat
>    figure cannot be rigged and this cannot be fixed after generation.
> 5. **Verify visually before claiming it works.** Extract frames with ffmpeg and
>    actually look at them. This composition has two failure modes that typecheck
>    cleanly: the screen insert landing off the monitor quad, and limbs detaching
>    at the joints. Check both explicitly.
>
> **Work in phases and stop for my confirmation between each.** Show me the
> generated art before you rig it, and the rig before you render the full reel.
>
> Commit to the branch `claude/refresh-data-import-stock-story-svya0l` and push.

---

*Educational content only — not financial advice.*
