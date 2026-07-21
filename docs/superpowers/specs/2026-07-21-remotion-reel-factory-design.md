# Remotion Reel Factory — Design Spec

**Date:** 2026-07-21 · **Status:** Approved (owner, this session; bubble contract amended same day)
**Owner decisions:** bubble mode = **talking on camera** (podcast feel) · first template = **halal verdict story** · approach = **scaffold from the official Remotion TikTok template**

## 0-bis. Bubble contract (owner amendment, 2026-07-21 evening)

1. **The bubble spans the full reel with NO loops.** Talking clips run back-to-back
   (`<Series>` of clips, one per script beat), each generated so **his lips read the
   exact line that narrates that scene's slide**. Reel duration derives from the
   concatenated clips; the revoiced speech is the master audio; whisper captions run
   over the full track. Looping B-roll is dead — it reads as fake.
2. **Setting = his podcast room, not the kitchen.** A serious content creator's setup:
   **always next to his microphone**, projecting confidence and professionalism.
   **Pose may vary between clips/reels** — sometimes seated at the desk mic, sometimes
   standing at a boom mic — but the room, mic presence, wardrobe register (smart
   casual/blazer) and grade stay consistent. (The kitchen theme survives as an
   occasional creative variant, e.g. the S2 metaphor piece — not the default set.)
3. **One-time set anchors:** 2–3 podcast-room stills (seated-at-mic, standing-at-mic)
   generated once with the persona identity reference and reused as start frames for
   every talking clip — same room forever. Gated on the persona decision (Karim vs
   Gentle Planner); if Karim, his pinned IDs in `course/persona/higgsfield-ids.json`
   apply.
4. **Cost per ~24s reel** updates to: 3 × 8s talking clips (SD 2.0 Mini ~20 cr) +
   3 × voice_change (2 cr) ≈ **66 cr** + free render. The zero-credit VO-only mode
   (friend's slide style, no bubble) remains available per reel.

---

## 1. What this is

A programmatic 9:16 video factory: **70% animated data canvas** (React components fed by
the site's JSON bundles) + **30% persona bubble** (the creator talking while cooking,
revoiced to his cloned voice) + **word-synced captions**. Rendered locally with the
Remotion CLI into `higgs/`. Replaces one-shot hero-clip generation — where acting +
lip-sync + delivery in a single AI shot kept producing cringe — with a layout where the
persona is a small webcam bubble and the *data animation* carries the content.

**License note (verified 2026-07-21):** Remotion is free for orgs ≤3 people, commercial
use, self-hosted rendering. At 4+ people the "Automators" tier applies ($0.01/render,
$100/mo minimum) — flagged as a growth threshold, not a current cost.

**Not in v1:** congress/daily-brief templates (later compositions reusing every layer),
music bed, auto-posting, non-English captions.

---

## 2. Pipeline (per video)

```
halal_alerts.json / aiinvest.halal_stories  →  pick story
        │
scripts/build_halal_reel.py                 →  script JSON:
        │                                      { beats: [{vo_line, canvas_scene, data}],
        │                                        shot_list: [bubble clip prompts] }
        ▼
[SERIAL MCP PHASE — orchestrator-driven, per the established 2-phase factory pattern]
  Seedance 2.0 Mini talking clips (8s, 720p, 9:16, ~2-3 per video, ~20 cr each)
  → voice_change to the cloned persona voice (2 cr each)
  → download to higgs/reel_assets/<ticker>_<date>/
        │
        ▼
audio extraction (ffmpeg) — the revoiced clips ARE the master audio track
        │
Whisper.cpp (from the TikTok template) → word-timestamped captions JSON
        │
props JSON assembled (story data + clip paths + captions + audio path)
        ▼
npx remotion render HalalVerdictReel --props=<props.json>
        ▼
higgs/reel_remotion_<ticker>_<date>.mp4   (1080×1920, 30fps, 30-45s)
```

Marginal cost ≈ **50–70 Higgsfield credits per video** (talking clips + voice_change);
canvas, captions, and render are free local compute.

**Voice dependency:** the cloned persona voice (`voice_id`, voice_type `element`) — the
clone sample is already uploaded (media `2a61ffac-5973-4000-9fcb-b826b59b7a1b`); creation
is blocked until the owner deletes the stuck custom voice occupying the plan's slot
(no delete API exists in the MCP — browser-only action). Until then, dev proceeds on
fixture assets; the raw SD-mini voice is acceptable for previews only, never for
published output.

---

## 3. Remotion project — `remotion/` (repo root)

Scaffolded with `npx create-video@latest --tiktok` (brings Whisper.cpp install +
word-by-word caption components), then our composition added beside the template's.

```
remotion/
  src/Root.tsx                     registers HalalVerdictReel (1080×1920@30fps;
                                   duration from master audio via calculateMetadata)
  src/compositions/HalalVerdictReel.tsx   scene sequencer: beats → <Series> of scenes
  src/components/
    BubbleFrame.tsx                30% rounded PIP, bottom-right, subtle border,
                                   <OffthreadVideo> of the revoiced clip(s)
    VerdictBadge.tsx               overall verdict chip (tone colors)
    RatioBars.tsx                  animated fill vs threshold marker ("Show the math",
                                   animated: bar grows, threshold line pulses on breach)
    DecisiveNumber.tsx             big Fraunces number counting up (e.g. 5.29%)
    PurificationLine.tsx           per-share purification line
    CaptionTrack.tsx               template caption system restyled to brand
    DisclaimerFooter.tsx           persistent small "Educational research only — not
                                   financial advice, not a fatwa."
  src/props.ts                     zod schema for the props JSON (single source of truth;
                                   the Python generator's output is validated against it)
  src/fixtures/ddog.json           fixture props (the DDOG 5.29% story) for dev preview
```

Design-for-isolation: every component consumes plain props; no component reads files or
knows about Higgsfield; the composition is previewable in Remotion Studio from fixtures
alone (`npx remotion studio`).

---

## 4. Factory glue — `scripts/build_halal_reel.py`

- `pick_story()` → reuses `aiinvest.halal_stories.pick_stories` (alerts first).
- `emit_script(story)` → beats (hook / math / verdict-takeaway), each with a VO line
  obeying the copy rails, the canvas scene id, and the data slice; plus the shot list
  (bubble prompts with the sober acting guidelines: minimal motion, no camera-mugging,
  glances only).
- `--assets-dir` mode: consumes the downloaded+revoiced clips, extracts master audio
  (ffmpeg), runs Whisper alignment, assembles + zod-validates props, invokes
  `npx remotion render`, writes the MP4 to `higgs/`.
- The MCP generation step stays MANUAL/orchestrator-driven between `emit_script` and
  `--assets-dir` (same split as the reel engine: MCP gen serial, assembly scripted).

## 5. Visual system

Dashboard language exactly: `#0A0D12` ground; emerald `#34D399` pass / red fail / amber
questionable; Fraunces (big numbers), Inter (body), JetBrains Mono (tickers/labels).
Safe margins ≥120px top / ≥220px bottom for platform UI. Copy rails enforced in
`emit_script`: methodology framing ("fails the AAOIFI debt screen", never "haram" as an
accusation head), no first-person-plural hype, disclaimer footer always on.

## 6. Error posture & testing

- Story with missing decisive data → generator **aborts with a named reason**; never
  renders a half-empty canvas.
- Whisper failure → sentence-level fallback timing (VO line count ÷ audio duration).
- zod schema rejects malformed props at render entry.
- Tests: pytest for `emit_script` (beat structure, copy rails, abort paths) and a render
  smoke (`npx remotion render --frames=0-10` on fixture props → output exists);
  `npx tsc --noEmit` in `remotion/`. Visual taste = owner review of the first render.

## 7. Rollout

1. Scaffold + fixture-driven `HalalVerdictReel` previewable in Studio (no credits spent).
2. Owner eyeballs a fixture render (DDOG story) → visual iteration.
3. Voice unblocked → clone → first real video end-to-end → owner validation.
4. Then: batch mode, congress + daily-brief compositions, music bed — each its own
   small increment.
