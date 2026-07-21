# Remotion Reel Factory — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A previewable `HalalVerdictReel` Remotion composition (1080×1920@30fps) rendering the real DDOG 5.29% story from fixture props with the existing `higgs/s2mini_clip1_talking_raw.mp4` as the talking bubble — zero Higgsfield spend, no voice dependency.

**Architecture:** Scaffold `remotion/` from the official TikTok template (keeps its caption machinery for Phase 2), add our composition + seven focused components fed by a zod-validated props JSON. Fixture = real values from `web/public/data/halal.json` (DDOG). Duration fixed at 24s (3 scenes × 8s), bubble clip loops.

**Tech Stack:** Remotion 4.x (template scaffold), React + TypeScript, zod, @remotion/google-fonts (Fraunces, Inter, JetBrains Mono). No Python in Phase 1.

## Global Constraints

- **Zero Higgsfield generation** — only `higgs/s2mini_clip1_talking_raw.mp4` and repo data (spec §7 step 1-2).
- Visual system (spec §5): ground `#0A0D12`; emerald `#34D399` pass / red `#F87171` fail / amber `#E0A23B` questionable; text `#E8EDF2`, muted `#8B98A5`; Fraunces = big numbers, Inter = body, JetBrains Mono = tickers/labels. Safe margins ≥120px top / ≥220px bottom.
- Copy rails (spec §5): methodology framing — "fails the AAOIFI interest-income screen", never "haram" as an accusation head; persistent disclaimer footer "Educational research only — not financial advice, not a fatwa."
- Every component consumes plain props only — no file reads, no data fetching inside components (spec §3 isolation rule).
- Whisper NOT in Phase 1 — fixture captions are hand-timed for the bubble clip's known line.
- Verify each task with `cd remotion; npx tsc --noEmit` at minimum; commit per task with trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- Windows shell (PowerShell); paths with backslashes in commands, forward slashes in TS imports.

---

### Task 1: Scaffold `remotion/` from the TikTok template

**Files:**
- Create: `remotion/` (via scaffolder), `remotion/public/bubble_ddog.mp4` (copied asset)

**Interfaces:**
- Produces: a running Remotion project: `cd remotion; npx tsc --noEmit` clean, `npx remotion studio` opens, template's caption components remain in place (Phase 2 will reuse them). Bubble asset available via `staticFile('bubble_ddog.mp4')`.

- [ ] **Step 1:** From repo root: `npm create video@latest -- --tiktok remotion` (if the scaffolder prompts, choose the TikTok/captions template, TypeScript, skip git init). If Whisper install prompts/attempts a large download, SKIP/abort that step — not needed in Phase 1 (document what was skipped in the commit message).
- [ ] **Step 2:** `Copy-Item higgs\s2mini_clip1_talking_raw.mp4 remotion\public\bubble_ddog.mp4`
- [ ] **Step 3:** Install fonts + zod inside the project: `cd remotion; npm i zod @remotion/google-fonts` (template may already carry some — `npm ls zod` to check first, skip if present).
- [ ] **Step 4:** Verify: `npx tsc --noEmit` clean; `npx remotion render` lists the template compositions (or `npx remotion compositions src/index.ts`).
- [ ] **Step 5:** Commit: `git add remotion; git commit -m "feat(reels): scaffold remotion project from tiktok template + bubble fixture asset"` (add `-f` only if some template subpath is gitignored — check `git check-ignore -v` first; node_modules must NOT be committed — ensure `remotion/node_modules/` is ignored, add a `remotion/.gitignore` with `node_modules/`+`out/` if the template didn't).

---

### Task 2: Brand tokens, props schema, DDOG fixture

**Files:**
- Create: `remotion/src/brand.ts`, `remotion/src/props.ts`, `remotion/src/fixtures/ddog.json`
- Create: `remotion/src/validateFixture.ts`

**Interfaces:**
- Produces (all later tasks consume): `brand` object (colors/fonts/margins); `ReelProps` zod schema + TS type; the fixture. Validation entry: `npx tsx src/validateFixture.ts` exits 0 on valid, 1 with message on invalid.

- [ ] **Step 1:** `remotion/src/brand.ts`:

```ts
export const brand = {
  bg: '#0A0D12',
  pass: '#34D399',
  fail: '#F87171',
  warn: '#E0A23B',
  text: '#E8EDF2',
  muted: '#8B98A5',
  card: '#11161F',
  border: '#1E2733',
  fontBig: 'Fraunces',
  fontBody: 'Inter',
  fontMono: 'JetBrains Mono',
  safeTop: 120,
  safeBottom: 220,
} as const;
```

- [ ] **Step 2:** `remotion/src/props.ts`:

```ts
import {z} from 'zod';

export const testResultSchema = z.object({
  id: z.string(),
  label: z.string(),
  ratio: z.number().nullable(),
  threshold: z.number(),
  status: z.enum(['pass', 'fail', 'unknown']),
});

export const sceneSchema = z.object({
  kind: z.enum(['hook', 'math', 'takeaway']),
  headline: z.string(),
  sub: z.string().optional(),
});

export const captionWordSchema = z.object({
  text: z.string(),
  fromMs: z.number(),
  toMs: z.number(),
});

export const reelPropsSchema = z.object({
  ticker: z.string(),
  overall: z.enum(['halal', 'not_halal', 'questionable', 'insufficient_data']),
  overallBasis: z.string(),
  decisive: z.object({
    valuePct: z.number(),        // 5.29
    thresholdPct: z.number(),    // 5.0
    label: z.string(),           // "interest income / revenue"
  }),
  tests: z.array(testResultSchema),
  activityStatus: z.enum(['pass', 'fail', 'unknown']),
  purificationPerShare: z.number().nullable(),
  inputsAsof: z.string(),
  scenes: z.array(sceneSchema).length(3),
  bubbleSrc: z.string(),         // staticFile-relative, e.g. "bubble_ddog.mp4"
  captions: z.array(captionWordSchema),
  disclaimer: z.string(),
});

export type ReelProps = z.infer<typeof reelPropsSchema>;
```

- [ ] **Step 3:** `remotion/src/fixtures/ddog.json` — real values from `web/public/data/halal.json` (verdicts.DDOG, retrieved 2026-07-21; the 5.29% figure is interest_income $194.4M / TTM revenue $3.67B from the v1.1 ship-gate ledger):

```json
{
  "ticker": "DDOG",
  "overall": "not_halal",
  "overallBasis": "AAOIFI SS 21",
  "decisive": {"valuePct": 5.29, "thresholdPct": 5.0, "label": "interest income / revenue"},
  "tests": [
    {"id": "aaoifi_debt", "label": "Debt / market cap", "ratio": 0.0137, "threshold": 0.3, "status": "pass"},
    {"id": "aaoifi_cash", "label": "Cash & interest-bearing / market cap", "ratio": 0.0508, "threshold": 0.3, "status": "pass"}
  ],
  "activityStatus": "fail",
  "purificationPerShare": 0.5462,
  "inputsAsof": "2026-07-21",
  "scenes": [
    {"kind": "hook", "headline": "Every ratio passes.", "sub": "DDOG still fails the screen."},
    {"kind": "math", "headline": "The worked math", "sub": "AAOIFI SS 21 — data as of 2026-07-21"},
    {"kind": "takeaway", "headline": "0.29 points over the line", "sub": "Discipline is the whole recipe."}
  ],
  "bubbleSrc": "bubble_ddog.mp4",
  "captions": [
    {"text": "When", "fromMs": 800, "toMs": 1000}, {"text": "the", "fromMs": 1000, "toMs": 1120},
    {"text": "pan", "fromMs": 1120, "toMs": 1350}, {"text": "flares,", "fromMs": 1350, "toMs": 1800},
    {"text": "amateurs", "fromMs": 1900, "toMs": 2400}, {"text": "jump", "fromMs": 2400, "toMs": 2700},
    {"text": "back.", "fromMs": 2700, "toMs": 3100}, {"text": "Cooks", "fromMs": 3600, "toMs": 4000},
    {"text": "lower", "fromMs": 4000, "toMs": 4350}, {"text": "the", "fromMs": 4350, "toMs": 4500},
    {"text": "flame.", "fromMs": 4500, "toMs": 5100}
  ],
  "disclaimer": "Educational research only — not financial advice, not a fatwa."
}
```

- [ ] **Step 4:** `remotion/src/validateFixture.ts`:

```ts
import {reelPropsSchema} from './props';
import fixture from './fixtures/ddog.json';

const r = reelPropsSchema.safeParse(fixture);
if (!r.success) {
  console.error(r.error.format());
  process.exit(1);
}
console.log('fixture OK');
```

- [ ] **Step 5:** Run `npx tsx src/validateFixture.ts` → `fixture OK`; `npx tsc --noEmit` clean. Commit `feat(reels): brand tokens, zod props schema, DDOG fixture (real halal.json values)`.

---

### Task 3: Static components — DisclaimerFooter, VerdictBadge, BubbleFrame

**Files:**
- Create: `remotion/src/components/DisclaimerFooter.tsx`, `remotion/src/components/VerdictBadge.tsx`, `remotion/src/components/BubbleFrame.tsx`

**Interfaces:**
- Consumes: `brand` (T2).
- Produces: `<DisclaimerFooter text={string} />`; `<VerdictBadge overall={ReelProps['overall']} basis={string} />`; `<BubbleFrame src={string} />` (positions itself absolute bottom-right, 30% width, above the safe-bottom margin; loops the clip; audio plays).

- [ ] **Step 1:**

```tsx
// DisclaimerFooter.tsx
import React from 'react';
import {brand} from '../brand';

export const DisclaimerFooter: React.FC<{text: string}> = ({text}) => (
  <div style={{
    position: 'absolute', bottom: 40, left: 0, right: 0, textAlign: 'center',
    fontFamily: brand.fontBody, fontSize: 22, color: brand.muted, opacity: 0.85,
  }}>{text}</div>
);
```

```tsx
// VerdictBadge.tsx
import React from 'react';
import {brand} from '../brand';

const LABELS = {halal: 'HALAL', not_halal: 'NOT HALAL', questionable: 'QUESTIONABLE', insufficient_data: 'INSUFFICIENT DATA'} as const;
const TONES = {halal: brand.pass, not_halal: brand.fail, questionable: brand.warn, insufficient_data: brand.muted} as const;

export const VerdictBadge: React.FC<{overall: keyof typeof LABELS; basis: string}> = ({overall, basis}) => (
  <div style={{display: 'inline-flex', flexDirection: 'column', alignItems: 'flex-start', gap: 8}}>
    <div style={{
      fontFamily: brand.fontMono, fontSize: 44, fontWeight: 700, letterSpacing: 2,
      color: brand.bg, background: TONES[overall], padding: '10px 28px', borderRadius: 12,
    }}>{LABELS[overall]}</div>
    <div style={{fontFamily: brand.fontMono, fontSize: 24, color: brand.muted}}>basis: {basis}</div>
  </div>
);
```

```tsx
// BubbleFrame.tsx
import React from 'react';
import {OffthreadVideo, staticFile} from 'remotion';
import {brand} from '../brand';

export const BubbleFrame: React.FC<{src: string}> = ({src}) => (
  <div style={{
    position: 'absolute', right: 36, bottom: brand.safeBottom + 40,
    width: '30%', aspectRatio: '9 / 16', borderRadius: 24, overflow: 'hidden',
    border: `3px solid ${brand.border}`, boxShadow: '0 12px 48px rgba(0,0,0,0.55)',
  }}>
    <OffthreadVideo loop src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
  </div>
);
```

- [ ] **Step 2:** `npx tsc --noEmit` clean. Commit `feat(reels): static components — disclaimer, verdict badge, bubble frame`.

---

### Task 4: Animated components — DecisiveNumber, RatioBars, PurificationLine

**Files:**
- Create: `remotion/src/components/DecisiveNumber.tsx`, `remotion/src/components/RatioBars.tsx`, `remotion/src/components/PurificationLine.tsx`

**Interfaces:**
- Consumes: `brand`, `testResultSchema` type (T2), Remotion `useCurrentFrame`/`interpolate`/`spring`.
- Produces: `<DecisiveNumber valuePct thresholdPct label />` (counts up, turns red past threshold); `<RatioBars tests={TestResult[]} activityStatus decisive={{valuePct, thresholdPct, label}} />` (bars grow to ratio/threshold scale, threshold line, activity row breaches); `<PurificationLine perShare={number|null} />`.

- [ ] **Step 1:**

```tsx
// DecisiveNumber.tsx
import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {brand} from '../brand';

export const DecisiveNumber: React.FC<{valuePct: number; thresholdPct: number; label: string}> =
({valuePct, thresholdPct, label}) => {
  const frame = useCurrentFrame();
  const v = interpolate(frame, [0, 60], [0, valuePct], {extrapolateRight: 'clamp'});
  const over = v > thresholdPct;
  return (
    <div style={{textAlign: 'left'}}>
      <div style={{fontFamily: brand.fontBig, fontSize: 220, fontWeight: 600, lineHeight: 1,
        color: over ? brand.fail : brand.text, transition: 'color 0.2s'}}>
        {v.toFixed(2)}%
      </div>
      <div style={{fontFamily: brand.fontMono, fontSize: 30, color: brand.muted, marginTop: 12}}>
        {label} · limit {thresholdPct.toFixed(1)}%
      </div>
    </div>
  );
};
```

```tsx
// RatioBars.tsx
import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {brand} from '../brand';
import type {z} from 'zod';
import type {testResultSchema} from '../props';

type TestResult = z.infer<typeof testResultSchema>;
const TONE = {pass: brand.pass, fail: brand.fail, unknown: brand.muted} as const;

const Bar: React.FC<{label: string; frac: number; status: keyof typeof TONE; delay: number; detail: string}> =
({label, frac, status, delay, detail}) => {
  const frame = useCurrentFrame();
  const w = interpolate(frame, [delay, delay + 45], [0, Math.min(frac, 1.6) * 62.5], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  }); // threshold sits at 62.5% of track width => frac 1.0
  return (
    <div style={{marginBottom: 34}}>
      <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: brand.fontMono,
        fontSize: 26, color: brand.text, marginBottom: 8}}>
        <span>{label}</span><span style={{color: TONE[status]}}>{detail}</span>
      </div>
      <div style={{position: 'relative', height: 26, background: brand.card, borderRadius: 13,
        border: `1px solid ${brand.border}`}}>
        <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: `${w}%`,
          background: TONE[status], borderRadius: 13}} />
        <div style={{position: 'absolute', left: '62.5%', top: -8, bottom: -8, width: 3,
          background: brand.text, opacity: 0.7}} />
      </div>
    </div>
  );
};

export const RatioBars: React.FC<{tests: TestResult[]; activityStatus: 'pass' | 'fail' | 'unknown';
  decisive: {valuePct: number; thresholdPct: number; label: string}}> =
({tests, activityStatus, decisive}) => (
  <div>
    {tests.map((t, i) => (
      <Bar key={t.id} label={t.label} frac={(t.ratio ?? 0) / t.threshold} status={t.status}
        delay={i * 20} detail={t.ratio === null ? '—' : `${(t.ratio * 100).toFixed(1)}% / ${(t.threshold * 100).toFixed(0)}%`} />
    ))}
    <Bar label={decisive.label} frac={decisive.valuePct / decisive.thresholdPct} status={activityStatus}
      delay={tests.length * 20 + 10} detail={`${decisive.valuePct.toFixed(2)}% / ${decisive.thresholdPct.toFixed(1)}%`} />
  </div>
);
```

```tsx
// PurificationLine.tsx
import React from 'react';
import {brand} from '../brand';

export const PurificationLine: React.FC<{perShare: number | null}> = ({perShare}) => (
  <div style={{fontFamily: brand.fontBody, fontSize: 30, color: brand.muted}}>
    {perShare === null ? 'Purification: insufficient data' :
      <>Purification: <span style={{color: brand.text, fontFamily: brand.fontMono}}>${perShare.toFixed(4)}/share</span> of held-period income</>}
  </div>
);
```

- [ ] **Step 2:** `npx tsc --noEmit` clean. Commit `feat(reels): animated canvas components — decisive number, ratio bars, purification`.

---

### Task 5: CaptionTrack + HalalVerdictReel composition + Root registration

**Files:**
- Create: `remotion/src/components/CaptionTrack.tsx`, `remotion/src/compositions/HalalVerdictReel.tsx`
- Modify: the template's root (`remotion/src/Root.tsx`) — ADD our `<Composition>`, do not remove the template's.

**Interfaces:**
- Consumes: everything above; fixture as `defaultProps`.
- Produces: composition id `HalalVerdictReel`, 1080×1920, fps 30, `durationInFrames: 720` (24s; 3 scenes × 8s matching the looping 8s bubble clip).

- [ ] **Step 1:**

```tsx
// CaptionTrack.tsx — karaoke-style: current word highlighted
import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {brand} from '../brand';
import type {z} from 'zod';
import type {captionWordSchema} from '../props';

type Word = z.infer<typeof captionWordSchema>;

export const CaptionTrack: React.FC<{words: Word[]}> = ({words}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ms = ((frame % (8 * fps)) / fps) * 1000; // loops with the 8s bubble clip
  const active = words.findIndex((w) => ms >= w.fromMs && ms < w.toMs);
  const windowWords = words.slice(Math.max(0, active - 2), Math.max(0, active - 2) + 5);
  if (active === -1) return null;
  return (
    <div style={{position: 'absolute', left: 40, right: '34%', bottom: brand.safeBottom + 60,
      display: 'flex', flexWrap: 'wrap', gap: 10}}>
      {windowWords.map((w) => (
        <span key={`${w.fromMs}-${w.text}`} style={{
          fontFamily: brand.fontBody, fontWeight: 800, fontSize: 42,
          color: ms >= w.fromMs && ms < w.toMs ? brand.warn : brand.text,
          textShadow: '0 2px 12px rgba(0,0,0,0.8)',
        }}>{w.text}</span>
      ))}
    </div>
  );
};
```

```tsx
// HalalVerdictReel.tsx
import React from 'react';
import {AbsoluteFill, Series} from 'remotion';
import {brand} from '../brand';
import type {ReelProps} from '../props';
import {BubbleFrame} from '../components/BubbleFrame';
import {VerdictBadge} from '../components/VerdictBadge';
import {RatioBars} from '../components/RatioBars';
import {DecisiveNumber} from '../components/DecisiveNumber';
import {PurificationLine} from '../components/PurificationLine';
import {CaptionTrack} from '../components/CaptionTrack';
import {DisclaimerFooter} from '../components/DisclaimerFooter';

const SCENE_FRAMES = 240; // 8s @ 30fps, matches the bubble clip loop

const SceneShell: React.FC<{headline: string; sub?: string; children?: React.ReactNode}> =
({headline, sub, children}) => (
  <div style={{position: 'absolute', top: brand.safeTop + 40, left: 48, right: 48}}>
    <h1 style={{fontFamily: brand.fontBig, fontSize: 76, color: brand.text, margin: 0, lineHeight: 1.1}}>{headline}</h1>
    {sub ? <p style={{fontFamily: brand.fontBody, fontSize: 32, color: brand.muted, marginTop: 14}}>{sub}</p> : null}
    <div style={{marginTop: 48, marginRight: '4%'}}>{children}</div>
  </div>
);

export const HalalVerdictReel: React.FC<ReelProps> = (p) => (
  <AbsoluteFill style={{background: brand.bg}}>
    <Series>
      <Series.Sequence durationInFrames={SCENE_FRAMES}>
        <SceneShell headline={p.scenes[0].headline} sub={p.scenes[0].sub}>
          <div style={{marginTop: 30, fontFamily: brand.fontMono, fontSize: 120, color: brand.text}}>{p.ticker}</div>
        </SceneShell>
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENE_FRAMES}>
        <SceneShell headline={p.scenes[1].headline} sub={p.scenes[1].sub}>
          <RatioBars tests={p.tests} activityStatus={p.activityStatus} decisive={p.decisive} />
        </SceneShell>
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENE_FRAMES}>
        <SceneShell headline={p.scenes[2].headline} sub={p.scenes[2].sub}>
          <DecisiveNumber valuePct={p.decisive.valuePct} thresholdPct={p.decisive.thresholdPct} label={p.decisive.label} />
          <div style={{marginTop: 40}}><VerdictBadge overall={p.overall} basis={p.overallBasis} /></div>
          <div style={{marginTop: 28}}><PurificationLine perShare={p.purificationPerShare} /></div>
        </SceneShell>
      </Series.Sequence>
    </Series>
    <BubbleFrame src={p.bubbleSrc} />
    <CaptionTrack words={p.captions} />
    <DisclaimerFooter text={p.disclaimer} />
  </AbsoluteFill>
);
```

Root registration (added beside the template's existing compositions):

```tsx
import fixture from './fixtures/ddog.json';
import {HalalVerdictReel} from './compositions/HalalVerdictReel';
import {reelPropsSchema} from './props';
// inside the root component's returned fragment:
<Composition
  id="HalalVerdictReel"
  component={HalalVerdictReel}
  durationInFrames={720}
  fps={30}
  width={1080}
  height={1920}
  schema={reelPropsSchema}
  defaultProps={reelPropsSchema.parse(fixture)}
/>
```

Font loading: if the template does not already load them, add at the top of `Root.tsx`: `import {loadFont as loadFraunces} from '@remotion/google-fonts/Fraunces'; import {loadFont as loadInter} from '@remotion/google-fonts/Inter'; import {loadFont as loadJBM} from '@remotion/google-fonts/JetBrainsMono'; loadFraunces(); loadInter(); loadJBM();` (install the three `@remotion/google-fonts/*` entries come with the single package).

- [ ] **Step 2:** `npx tsc --noEmit` clean; `npx remotion compositions src/index.ts` lists `HalalVerdictReel`.
- [ ] **Step 3:** Commit `feat(reels): HalalVerdictReel composition + captions + root registration`.

---

### Task 6: Preview render for owner review

- [ ] **Step 1:** Smoke: `cd remotion; npx remotion render HalalVerdictReel ..\higgs\preview_ddog_phase1.mp4 --frames=0-30` → file exists.
- [ ] **Step 2:** Full render: `npx remotion render HalalVerdictReel ..\higgs\preview_ddog_phase1.mp4` (720 frames; audio from the looping bubble clip is included automatically). Expected: MP4 ~24s, 1080×1920.
- [ ] **Step 3:** Report to owner: local path `higgs\preview_ddog_phase1.mp4`, what to look at (layout proportions, bubble size/position, bar animation timing, caption sync vs bubble speech, disclaimer legibility), plus `npx remotion studio` as the live-tweak option.
- [ ] **Step 4:** Commit any final adjustments; do NOT commit the rendered MP4 (`higgs/` renders are artifacts; confirm `.gitignore` doesn't need an entry — `higgs/*.mp4` files have been committed before as samples, so leave the preview untracked deliberately by not staging it).

---

## Self-Review

1. **Spec coverage (Phase-1 slice):** §3 project structure → T1/T2/T5; §5 visual system + rails → T2 brand + fixture copy + footer; §6 zod gate + render smoke → T2/T6; §7 steps 1-2 → T6 deliverable. Whisper/build_halal_reel.py/voice explicitly out (Phase 2) — consistent with the argument scope.
2. **Placeholders:** none — every component ships complete code; the only conditional instruction (font loading / zod presence) includes the exact command and code.
3. **Type consistency:** `ReelProps`/`testResultSchema`/`captionWordSchema` (T2) match component prop types (T3-T5) field-for-field; `bubbleSrc` flows fixture→BubbleFrame via staticFile; scene count `.length(3)` matches the composition's three `Series.Sequence` blocks; 8s loop assumption consistent between CaptionTrack (`frame % (8*fps)`) and SCENE_FRAMES=240.
