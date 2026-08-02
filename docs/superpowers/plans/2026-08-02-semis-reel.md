# Semis "Out of Buyers" Reel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `SemisReel` — a ~38s vertical animated reel (full + mini) that faithfully retells the source reel's 7-beat "semis are running out of buyers" story using Grok video clips + Remotion chart/typography animations, on the existing `halal-reels` spine.

**Architecture:** New `src/semisData.ts` (deterministic, unit-tested math for the crash/gap/leverage/rotation animations + the relayed figures). New presentational units in `src/ui.tsx` (`StickerHook`, `RollingCaption`, `GrokClip`) and `src/charts.tsx` (`CrashChart`, `RotationFlow`). New `src/SemisReel.tsx` composition (full + `mini`), registered in `src/Root.tsx`. Grok video/still assets live in `public/semis/`.

**Tech Stack:** Remotion 4.0.496, React 19, TypeScript 5.9, Vitest (added in Task 1), `grok-cli.exe` (subscription, for asset generation).

## Global Constraints

- 30fps · 1080×1920 · `halal-reels/` project. All new compositions use `FPS=30, W=1080, H=1920`.
- Palette from `src/theme.ts` `C`: dark `#0A0D12`, gold `C.amber`, mint `C.mint`, emerald `C.emerald`. **Red (`C.red`/`C.redHot`) is allowed ONLY for down-price candles / falling-chart data — NEVER as text emphasis or decoration.**
- Fonts from `FONT` (Fraunces display, Inter body, JetBrains Mono numerics).
- Deterministic only: NO `Math.random` / `Date.now` / `new Date()` in any reel/data code (mirror `correlationData.ts`).
- Borrowed figures are relayed **as reported**: every on-screen figure carries a small "as reported" tag; the close carries the full rail. CTA offers an educational DM, never "setups/signals".
- Model policy: every subagent / workflow `agent()` call runs on **`model:'sonnet'`**. Orchestrator (main agent) generates Grok assets and reviews; it does not delegate asset generation.
- Commit trailer on every commit:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- Media (`.mp4`/`.jpg`/`.png`) is gitignored; `.ts`/`.tsx` sources are committed.
- Figures to display (relayed as reported): SanDisk (SNDK) **−14.1%** one day · retail leverage record **$39B** · healthcare **best week since 2022**.

---

## Task 1: Test infra + `semisData.ts` (deterministic math)

**Files:**
- Modify: `halal-reels/package.json` (add vitest devDep + `test` script)
- Create: `halal-reels/src/semisData.ts`
- Test: `halal-reels/src/semisData.test.ts`

**Interfaces:**
- Produces:
  - `SEMIS_DATE: string`
  - Beat lengths (frames): `CRASH_LEN, LEV_LEN, KOREA_LEN, FORCED_LEN, US_LEN, ROT_LEN, CTA_LEN: number`
  - `SEMIS_STARTS: { crash:number; lev:number; korea:number; forced:number; us:number; rot:number; cta:number }`
  - `SEMIS_TOTAL: number`
  - `SEMIS_MINI_STARTS: { crash:number; rot:number; cta:number }`, `SEMIS_MINI_TOTAL: number`
  - `crashCloses(n:number): number[]` — normalized 0..1, declining
  - `crashCandles(n:number): Array<{o:number;h:number;l:number;c:number}>` — normalized 0..1
  - `gapCloses(n:number): number[]` — normalized 0..1, step-gapped decline
  - `SNDK_DROP_PCT: number` (=-14.1), `LEVERAGE_B: number` (=39), `LEVERAGE_PREV_B: number` (=30)
  - `WHOOSH_OFFSETS: number[]` (beat starts, full reel)

- [ ] **Step 1: Add vitest + test script**

Edit `halal-reels/package.json` — add to `devDependencies`: `"vitest": "^3.2.4"`, and to `scripts`: `"test": "vitest run"`. Then:

Run: `cd halal-reels && npm install`
Expected: installs vitest, exits 0.

- [ ] **Step 2: Write the failing test**

Create `halal-reels/src/semisData.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import {
  crashCloses, crashCandles, gapCloses,
  SEMIS_STARTS, SEMIS_TOTAL, SEMIS_MINI_TOTAL,
  CRASH_LEN, LEV_LEN, KOREA_LEN, FORCED_LEN, US_LEN, ROT_LEN, CTA_LEN,
  SNDK_DROP_PCT, LEVERAGE_B,
} from "./semisData";

const inUnit = (a: number[]) => a.every((v) => v >= 0 && v <= 1);

describe("semisData", () => {
  it("beat starts are cumulative and total matches", () => {
    expect(SEMIS_STARTS.crash).toBe(0);
    expect(SEMIS_STARTS.lev).toBe(CRASH_LEN);
    expect(SEMIS_STARTS.cta).toBe(CRASH_LEN + LEV_LEN + KOREA_LEN + FORCED_LEN + US_LEN + ROT_LEN);
    expect(SEMIS_TOTAL).toBe(CRASH_LEN + LEV_LEN + KOREA_LEN + FORCED_LEN + US_LEN + ROT_LEN + CTA_LEN);
    expect(SEMIS_MINI_TOTAL).toBeGreaterThan(0);
  });
  it("crashCloses declines and stays in unit range", () => {
    const c = crashCloses(60);
    expect(c).toHaveLength(60);
    expect(inUnit(c)).toBe(true);
    expect(c[0]).toBeGreaterThan(c[c.length - 1]);
    expect(c[0] - c[c.length - 1]).toBeGreaterThan(0.4); // a real crash, not a drift
  });
  it("crashCandles are OHLC-consistent in unit range", () => {
    const k = crashCandles(60);
    expect(k).toHaveLength(60);
    for (const c of k) {
      expect(c.h).toBeGreaterThanOrEqual(Math.max(c.o, c.c));
      expect(c.l).toBeLessThanOrEqual(Math.min(c.o, c.c));
      expect(c.l).toBeGreaterThanOrEqual(0);
      expect(c.h).toBeLessThanOrEqual(1);
    }
  });
  it("gapCloses declines and stays in unit range", () => {
    const g = gapCloses(60);
    expect(inUnit(g)).toBe(true);
    expect(g[0]).toBeGreaterThan(g[g.length - 1]);
  });
  it("relayed figures are the source values", () => {
    expect(SNDK_DROP_PCT).toBeCloseTo(-14.1);
    expect(LEVERAGE_B).toBe(39);
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd halal-reels && npm test`
Expected: FAIL — cannot resolve `./semisData`.

- [ ] **Step 4: Write `semisData.ts`**

Create `halal-reels/src/semisData.ts`:

```ts
// Deterministic data + timing for SemisReel. No Math.random / Date.now:
// same numbers every render (mirror correlationData.ts). The price motions are
// ILLUSTRATIVE animations of a reported market story, not real tick data — the
// relayed figures (SNDK_DROP_PCT etc.) are shown "as reported", see the reel rail.

export const SEMIS_DATE = "2026-08-02";

// Beat lengths @30fps.
export const CRASH_LEN = 180; // 6s
export const LEV_LEN = 150;   // 5s
export const KOREA_LEN = 150; // 5s
export const FORCED_LEN = 150;// 5s
export const US_LEN = 150;    // 5s
export const ROT_LEN = 180;   // 6s
export const CTA_LEN = 180;   // 6s

export const SEMIS_STARTS = {
  crash: 0,
  lev: CRASH_LEN,
  korea: CRASH_LEN + LEV_LEN,
  forced: CRASH_LEN + LEV_LEN + KOREA_LEN,
  us: CRASH_LEN + LEV_LEN + KOREA_LEN + FORCED_LEN,
  rot: CRASH_LEN + LEV_LEN + KOREA_LEN + FORCED_LEN + US_LEN,
  cta: CRASH_LEN + LEV_LEN + KOREA_LEN + FORCED_LEN + US_LEN + ROT_LEN,
};
export const SEMIS_TOTAL =
  CRASH_LEN + LEV_LEN + KOREA_LEN + FORCED_LEN + US_LEN + ROT_LEN + CTA_LEN;

// Mini cut: crash (hook+drop) -> rotation (payoff) -> cta.
export const SEMIS_MINI_STARTS = { crash: 0, rot: CRASH_LEN, cta: CRASH_LEN + ROT_LEN };
export const SEMIS_MINI_TOTAL = CRASH_LEN + ROT_LEN + CTA_LEN;

export const WHOOSH_OFFSETS = [
  SEMIS_STARTS.crash, SEMIS_STARTS.lev, SEMIS_STARTS.korea,
  SEMIS_STARTS.forced, SEMIS_STARTS.us, SEMIS_STARTS.rot, SEMIS_STARTS.cta,
];

// Relayed-as-reported figures (NOT our data).
export const SNDK_DROP_PCT = -14.1;
export const LEVERAGE_B = 39;
export const LEVERAGE_PREV_B = 30;

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

/** Declining normalized close series: high -> low with an accelerating drop
 * plus a small deterministic wiggle. 1 = top of frame region. */
export const crashCloses = (n: number): number[] =>
  Array.from({ length: n }, (_, i) => {
    const t = i / (n - 1);
    const trend = 0.92 - 0.78 * Math.pow(t, 1.5);
    const wiggle = 0.035 * Math.sin(i * 0.7) + 0.02 * Math.sin(i * 0.31 + 1.1);
    return clamp01(trend + wiggle);
  });

/** OHLC candles derived from crashCloses: open = prior close, close = this
 * close, high/low bracket the body with a deterministic wick. */
export const crashCandles = (
  n: number,
): Array<{ o: number; h: number; l: number; c: number }> => {
  const cl = crashCloses(n);
  return cl.map((c, i) => {
    const o = i === 0 ? clamp01(c + 0.05) : cl[i - 1];
    const wick = 0.02 + 0.02 * Math.abs(Math.sin(i * 0.9));
    const h = clamp01(Math.max(o, c) + wick);
    const l = clamp01(Math.min(o, c) - wick);
    return { o, h, l, c };
  });
};

/** Korea "gap down" series: flat holds punctuated by sharp downward gaps. */
export const gapCloses = (n: number): number[] => {
  const steps = 5;
  return Array.from({ length: n }, (_, i) => {
    const seg = Math.floor((i / n) * steps);
    const level = 0.9 - seg * 0.16;
    const wiggle = 0.015 * Math.sin(i * 1.3);
    return clamp01(level + wiggle);
  });
};
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd halal-reels && npm test`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add halal-reels/package.json halal-reels/package-lock.json halal-reels/src/semisData.ts halal-reels/src/semisData.test.ts
git commit -m "feat(semis): deterministic data/timing for SemisReel + vitest infra

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Grok assets (ORCHESTRATOR-RUN — not delegated)

**Files:**
- Create: `halal-reels/public/semis/*.mp4` (video), `halal-reels/public/semis/*.jpg` (stills)

> The orchestrator runs these `grok-cli` commands and visually verifies each asset (extract a frame for video, Read the still). Subagents do NOT run this task — they assume the files exist. If an asset is weak, regenerate before wiring. The panic-floor clip from spec de-risk (`public/semis/_test_panic.mp4`) is reused as `panic_floor.mp4`.

- [ ] **Step 1: Generate video clips** (each ~64s; `GROK="$HOME/.local/bin/grok-cli.exe"`)

```bash
cd halal-reels/public/semis
# panic floor already exists as _test_panic.mp4 — reuse:
cp _test_panic.mp4 panic_floor.mp4
# Seoul skyline (Korea beat):
"$GROK" video --json --duration 6 --aspect-ratio 9:16 --resolution 720p --timeout 300 \
  --prompt "Cinematic vertical 9:16. Seoul city skyline at dusk, dense neon high-rises, moody tech-noir teal-and-amber grade, slow aerial drift, film grain. No text, no logos, no watermark." | python -c "import sys,json,urllib.request;u=json.load(sys.stdin)['data']['video'];urllib.request.urlretrieve(u,'seoul.mp4');print('seoul.mp4',u)"
# US exchange exterior (US beat):
"$GROK" video --json --duration 6 --aspect-ratio 9:16 --resolution 720p --timeout 300 \
  --prompt "Cinematic vertical 9:16. Exterior of a grand US stock-exchange building at night, columns lit cold blue with faint amber, tense atmosphere, slow push-in, film grain. No text, no logos, no watermark." | python -c "import sys,json,urllib.request;u=json.load(sys.stdin)['data']['video'];urllib.request.urlretrieve(u,'us_exchange.mp4');print('us_exchange.mp4',u)"
```

- [ ] **Step 2: Generate stills** (each ~5s; for the graphics-over-still beats)

```bash
cd halal-reels/public/semis
GROK="$HOME/.local/bin/grok-cli.exe"
"$GROK" image --json --aspect-ratio 9:16 --output-file leverage_bg.jpg --timeout 120 \
  --prompt "Vertical 9:16 tech-noir wallpaper. Abstract surging red-and-amber leverage/debt bars rising in deep shadow on near-black, mint-green haze, bokeh, top third near-black for text. No text, no numbers, no logos, no watermark."
"$GROK" image --json --aspect-ratio 9:16 --output-file forced_bg.jpg --timeout 120 \
  --prompt "Vertical 9:16 tech-noir wallpaper. Abstract falling dominoes of light in deep shadow, amber and cold blue, near-black, sense of cascade/liquidation, top third near-black for text. No text, no numbers, no logos, no watermark."
"$GROK" image --json --aspect-ratio 9:16 --output-file rotation_bg.jpg --timeout 120 \
  --prompt "Vertical 9:16 tech-noir wallpaper. Streams of light flowing from a dim red-amber cluster toward a glowing mint-green cluster (capital rotating), deep haze on near-black, top third near-black for text. No text, no numbers, no logos, no watermark."
"$GROK" image --json --aspect-ratio 9:16 --output-file terminal_bg.jpg --timeout 120 \
  --prompt "Vertical 9:16 tech-noir wallpaper. Dark financial data terminal, faint green glyph wall receding into black, one amber glow low, bottom two-thirds near-solid black for text. No readable text, no numbers, no logos, no watermark."
```

- [ ] **Step 3: Verify each asset**

For each video: `node_modules/../@remotion/compositor-win32-x64-msvc/ffmpeg.exe -y -ss 2 -i public/semis/<name>.mp4 -frames:v 1 /tmp/<name>.jpg` then Read the frame. For each still: Read it directly. Regenerate any weak asset (vary the prompt). Confirm all 6 files exist:
Run: `ls -la halal-reels/public/semis/{panic_floor,seoul,us_exchange}.mp4 halal-reels/public/semis/{leverage_bg,forced_bg,rotation_bg,terminal_bg}.jpg`
Expected: all present, non-zero.

- [ ] **Step 4: Ensure media is gitignored** (no commit of binaries)

Run: `cd halal-reels && git check-ignore public/semis/panic_floor.mp4 || echo "ADD public/semis/ TO .gitignore"`
If not ignored, add `public/semis/` (or `*.mp4`,`*.jpg`) to `halal-reels/.gitignore` and commit only the `.gitignore` change.

---

## Task 3: `StickerHook`, `RollingCaption`, `GrokClip` (ui.tsx)

**Files:**
- Modify: `halal-reels/src/ui.tsx` (append three components)

**Interfaces:**
- Consumes: `C`, `FONT` from `./theme`; `easeOut`, `pop`, `clamp` (already in ui.tsx); `useCurrentFrame`, `interpolate`, `AbsoluteFill`, `OffthreadVideo`, `Img`, `staticFile` from `remotion`.
- Produces:
  - `StickerHook: React.FC<{ pre:string; keyword:string; post?:string; from?:number }>`
  - `RollingCaption: React.FC<{ text:string; from:number; asReported?:boolean }>`
  - `GrokClip: React.FC<{ src:string; kind:"video"|"image"; scrim?:string; kenBurns?:boolean }>`

- [ ] **Step 1: Append the components to `ui.tsx`**

At the top of `ui.tsx`, ensure the import line includes `OffthreadVideo, Img, staticFile` (add any missing). Then append:

```tsx
// ---- SemisReel presentational units ----------------------------------------

/** Pinned white "sticker" hook caption (studied from the source reel): bold
 * near-black text with one gold keyword; pops in, then holds on screen. */
export const StickerHook: React.FC<{ pre: string; keyword: string; post?: string; from?: number }> = ({
  pre, keyword, post = "", from = 0,
}) => {
  const frame = useCurrentFrame();
  const s = interpolate(frame, [from, from + 12], [0.7, 1], { ...clamp, easing: pop });
  const o = interpolate(frame, [from, from + 10], [0, 1], clamp);
  return (
    <div style={{
      position: "absolute", top: 150, left: 0, right: 0, display: "flex", justifyContent: "center",
      opacity: o, transform: `scale(${s})`, zIndex: 6,
    }}>
      <div style={{
        maxWidth: 820, background: "#F4F6F8", borderRadius: 26, padding: "22px 34px",
        boxShadow: "0 18px 50px rgba(0,0,0,.55)", fontFamily: FONT.body, fontWeight: 800,
        fontSize: 62, lineHeight: 1.08, color: "#111418", textAlign: "center",
      }}>
        {pre} <span style={{ color: C.amber }}>{keyword}</span>{post}
      </div>
    </div>
  );
};

/** Burned rolling subtitle that advances per beat; optional "as reported" tag. */
export const RollingCaption: React.FC<{ text: string; from: number; asReported?: boolean }> = ({
  text, from, asReported = false,
}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [from, from + 12], [0, 1], clamp);
  const y = interpolate(frame, [from, from + 12], [22, 0], { ...clamp, easing: easeOut });
  return (
    <div style={{
      position: "absolute", bottom: 360, left: 60, right: 60, textAlign: "center",
      opacity: o, transform: `translateY(${y}px)`, zIndex: 6,
    }}>
      <div style={{
        fontFamily: FONT.display, fontWeight: 700, fontSize: 52, lineHeight: 1.2,
        color: C.ink, textShadow: "0 3px 22px rgba(0,0,0,.85)",
      }}>{text}</div>
      {asReported && (
        <div style={{
          marginTop: 14, fontFamily: FONT.mono, fontWeight: 700, fontSize: 20, letterSpacing: 1.5,
          color: C.muted, textShadow: "0 2px 10px rgba(0,0,0,.9)",
        }}>AS REPORTED · NOT INDEPENDENTLY VERIFIED</div>
      )}
    </div>
  );
};

/** Full-bleed Grok background (video or still) with a dark scrim + optional
 * slow Ken-Burns for stills. Charts/text sit above it. */
export const GrokClip: React.FC<{ src: string; kind: "video" | "image"; scrim?: string; kenBurns?: boolean }> = ({
  src, kind, scrim = "linear-gradient(180deg, rgba(10,13,18,.45) 0%, rgba(10,13,18,.35) 40%, rgba(10,13,18,.85) 100%)", kenBurns = true,
}) => {
  const frame = useCurrentFrame();
  const k = kenBurns && kind === "image" ? interpolate(frame, [0, 300], [1.06, 1.16], clamp) : 1;
  return (
    <AbsoluteFill>
      {kind === "video" ? (
        <OffthreadVideo src={staticFile(src)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : (
        <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${k})` }} />
      )}
      <AbsoluteFill style={{ background: scrim }} />
    </AbsoluteFill>
  );
};
```

- [ ] **Step 2: Typecheck**

Run: `cd halal-reels && npx tsc --noEmit`
Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add halal-reels/src/ui.tsx
git commit -m "feat(semis): StickerHook, RollingCaption, GrokClip primitives

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: `CrashChart` + `RotationFlow` (charts.tsx)

**Files:**
- Modify: `halal-reels/src/charts.tsx` (append two components; reuse module-private `buildPoints`/`buildSmoothPath`)

**Interfaces:**
- Consumes: `crashCandles`, `crashCloses` from `./semisData`; `C`, `FONT`; `useCurrentFrame`, `interpolate`.
- Produces:
  - `CrashChart: React.FC<{ candles:{o:number;h:number;l:number;c:number}[]; reveal:number; dropPct:number; width:number; height:number }>`
  - `RotationFlow: React.FC<{ t:number; width:number; height:number }>` (`t` 0..1 = rotation progress)

- [ ] **Step 1: Append to `charts.tsx`**

```tsx
// ---- SemisReel charts ------------------------------------------------------

/** Candlestick free-fall. Down candles use C.red (data, not decoration).
 * `reveal` 0..1 draws candles left->right; `dropPct` shows the headline % . */
export const CrashChart: React.FC<{
  candles: { o: number; h: number; l: number; c: number }[];
  reveal: number; dropPct: number; width: number; height: number;
}> = ({ candles, reveal, dropPct, width, height }) => {
  const n = candles.length;
  const shown = Math.max(0, Math.min(n, Math.floor(reveal * n)));
  const cw = (width / n) * 0.62;
  const yOf = (v: number) => height - v * height;
  return (
    <svg width={width} height={height} style={{ overflow: "visible" }}>
      {candles.slice(0, shown).map((k, i) => {
        const x = (i + 0.5) * (width / n);
        const down = k.c <= k.o;
        const col = down ? C.redHot : C.emerald;
        const bodyTop = yOf(Math.max(k.o, k.c));
        const bodyBot = yOf(Math.min(k.o, k.c));
        return (
          <g key={i}>
            <line x1={x} x2={x} y1={yOf(k.h)} y2={yOf(k.l)} stroke={col} strokeWidth={2} />
            <rect x={x - cw / 2} y={bodyTop} width={cw} height={Math.max(2, bodyBot - bodyTop)} fill={col} rx={2} />
          </g>
        );
      })}
      <text x={width} y={28} textAnchor="end" fontFamily={FONT.mono} fontWeight={800}
        fontSize={64} fill={C.redHot}>{dropPct.toFixed(1)}%</text>
    </svg>
  );
};

/** Capital rotating from an amber "chips" node (left) to a mint "healthcare"
 * node (right). `t` 0..1 drives particle travel + node glow swap. */
export const RotationFlow: React.FC<{ t: number; width: number; height: number }> = ({ t, width, height }) => {
  const cy = height / 2;
  const lx = width * 0.2, rx = width * 0.8;
  const dots = Array.from({ length: 14 }, (_, i) => {
    const phase = (i / 14 + t) % 1;
    const x = lx + (rx - lx) * phase;
    const y = cy + Math.sin(phase * Math.PI * 2 + i) * 40;
    return { x, y, o: Math.sin(phase * Math.PI) };
  });
  return (
    <svg width={width} height={height} style={{ overflow: "visible" }}>
      <circle cx={lx} cy={cy} r={54} fill="none" stroke={C.amber} strokeWidth={3} opacity={1 - t * 0.6} />
      <circle cx={rx} cy={cy} r={54} fill="none" stroke={C.mint} strokeWidth={3} opacity={0.4 + t * 0.6} />
      {dots.map((d, i) => (
        <circle key={i} cx={d.x} cy={d.y} r={7} fill={d.x < (lx + rx) / 2 ? C.amber : C.mint} opacity={d.o} />
      ))}
      <text x={lx} y={cy + 100} textAnchor="middle" fontFamily={FONT.mono} fontWeight={700} fontSize={26} fill={C.amber}>CHIPS</text>
      <text x={rx} y={cy + 100} textAnchor="middle" fontFamily={FONT.mono} fontWeight={700} fontSize={26} fill={C.mint}>HEALTHCARE</text>
    </svg>
  );
};
```

- [ ] **Step 2: Typecheck**

Run: `cd halal-reels && npx tsc --noEmit`
Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add halal-reels/src/charts.tsx
git commit -m "feat(semis): CrashChart + RotationFlow chart primitives

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: `SemisReel.tsx` composition + Root registration

**Files:**
- Create: `halal-reels/src/SemisReel.tsx`
- Modify: `halal-reels/src/Root.tsx` (register full + mini)

**Interfaces:**
- Consumes: everything above + `Bg`, `Foot`, `LimitMeter`, `StickerHook`, `RollingCaption`, `GrokClip` from `./ui`; `CrashChart`, `RotationFlow` from `./charts`; `Audio`, `Sequence`, `AbsoluteFill`, `staticFile`, `interpolate`, `useCurrentFrame` from `remotion`; all `semisData` exports.
- Produces: `SemisReel: React.FC<{ mini?: boolean }>`, `SEMIS_BEATS = { total: SEMIS_TOTAL }`, `SEMIS_MINI_TOTAL`.

- [ ] **Step 1: Create `SemisReel.tsx`**

Build one `<Sequence>` per beat using `SEMIS_STARTS` (full) or `SEMIS_MINI_STARTS` (mini). Each scene: a `GrokClip` background (video for crash/korea/us, still for lev/forced/rot/cta), the persistent `StickerHook` (crash beat + held), a `RollingCaption` for that beat's line (crash/lev/korea/rot carry `asReported`), and the beat's chart (`CrashChart` on crash+us, `LimitMeter` on lev, gap line via `CrashChart` reuse or a simple SVG on korea, `RotationFlow` on rot). CTA beat: `StickerHook` resolves + a mint comment pill "COMMENT \"SEMIS\"" + `Foot` rail. Add the audio bed (`Audio` `staticFile("quiz/music.mp3")` low volume) and a `reveal.mp3` whoosh `Sequence` at each `WHOOSH_OFFSETS`. Full rail text: `"Relaying reported market data · educational only — not financial advice · not a trade signal."` Reuse `CorrelationReel.tsx` as the structural reference for audio ducking + mini-offset technique. Register `SEMIS_BEATS.total = mini ? SEMIS_MINI_TOTAL : SEMIS_TOTAL`.

- [ ] **Step 2: Register in `Root.tsx`**

Add imports and two `<Composition>` entries:

```tsx
import { SemisReel, SEMIS_BEATS, SEMIS_MINI_TOTAL } from "./SemisReel";
// ...
<Composition id="SemisReel" component={SemisReel} durationInFrames={SEMIS_BEATS.total} fps={FPS} width={W} height={H} defaultProps={{ mini: false }} />
<Composition id="SemisReelMini" component={SemisReel} durationInFrames={SEMIS_MINI_TOTAL} fps={FPS} width={W} height={H} defaultProps={{ mini: true }} />
```

- [ ] **Step 3: Typecheck + commit**

Run: `cd halal-reels && npx tsc --noEmit` → 0 errors.
```bash
git add halal-reels/src/SemisReel.tsx halal-reels/src/Root.tsx
git commit -m "feat(semis): SemisReel composition (full + mini) + Root registration

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Render, verify, caption

**Files:**
- Create: `higgs/semis_reel.mp4`, `higgs/semis_reel_mini.mp4`, `higgs/semis_caption.txt`

- [ ] **Step 1: Render still frames for each beat**

Run (one per beat start+40): `cd halal-reels && npx remotion still SemisReel higgs/_semis_f<F>.png --frame=<F>` for F in {40, 220, 360, 500, 650, 820, 1010}.

- [ ] **Step 2: Verify stills visually** (orchestrator Reads each)

Confirm per beat: StickerHook pinned + legible; RollingCaption + "as reported" tag present on crash/lev/korea/rot; CrashChart reads red free-fall with −14.1%; LeverageGauge hits $39B; RotationFlow reads amber→mint; CTA pill + full rail; palette correct (no red as text). Fix any issue in the relevant task's file and re-render.

- [ ] **Step 3: Render both MP4s**

Run: `cd halal-reels && npx remotion render SemisReel ../higgs/semis_reel.mp4 && npx remotion render SemisReelMini ../higgs/semis_reel_mini.mp4`
Expected: two MP4s written.

- [ ] **Step 4: Write caption** `higgs/semis_caption.txt`

Retells the 7 beats in our voice; ends with rails ("relaying reported market data · educational only — not financial advice · not a trade signal") + `Comment "SEMIS" and I'll DM you the breakdown`. No "setups/signals".

- [ ] **Step 5: Final commit** (sources only; MP4s gitignored)

```bash
git add halal-reels/src
git commit -m "feat(semis): SemisReel renders verified; caption written

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

- **Spec coverage:** 7 segments → Task 5 Sequences; hybrid Grok assets → Task 2; sticker+rolling caption format → Task 3; crash/leverage/rotation animations → Tasks 1+4; attribution/rails → RollingCaption `asReported` + Task 5 Foot; mini cut → `SEMIS_MINI_*`; build via workflow/subagent + Sonnet → handoff below.
- **Placeholders:** none — data + primitives carry full code; Task 5 gives explicit per-beat wiring against named interfaces.
- **Type consistency:** `crashCandles` shape `{o,h,l,c}` consistent across Tasks 1→4→5; `SEMIS_STARTS`/`SEMIS_MINI_STARTS` keys consistent; `SEMIS_BEATS.total` + `SEMIS_MINI_TOTAL` match Root registration.
- **Deviations:** red allowed only for down-candles (Global Constraints); CTA is educational-DM not setups (rail).
