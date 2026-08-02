# Habits Reel — design (2026-08-02)

Owner feedback on the Maya grind reel (45s, 15 neon clips, Maya in ~10 shots, no
audio): *cringe — too much of the girl, too sci-fi, too slow.* Replacement: a
fast, dopamine-paced chain of **real-photography** shots about trading habits
and the upside they buy, built on the standard hook mechanics of motivational
edits.

## Approved decisions (owner, 2026-08-02)

1. **Audio:** none baked in — silent render, beat-*ready* fixed grid; owner adds
   a trending sound in the platform app. (Rejected: baked-in beat-synced music,
   music+VO.)
2. **Persona:** anonymous fragments only — hands, coffee grip, distant
   silhouette. No recurring character, no faces. Maya retired from this piece.
3. **Design approved as presented** ("Approved — build it").

## The mechanic

- **Hook on frame one:** strongest visual + bold claim, no warm-up shot.
- **Fixed cut grid:** 1 unit = **1.7s = 51 frames @ 30fps** (3 beats at
  ~106 BPM, the middle of the 90–110 BPM trending-sound band). Stills take
  1 unit; videos take 1–2 units (the slower "breathing" moments).
- **One idea per shot:** overlay ≤4 words, changes every cut. Words are habits
  and states of mind — never income claims (compliance rail 10.6).
- **Pattern interrupt:** one wordless slow video mid-reel resets attention.
- **Loop closure:** final shot visually matches the hook shot so replays feel
  seamless.

## Shot list — 18 units = 30.6s = 918 frames

(Rev 2026-08-02: owner added shot 0 — one Maya cameo as the cold open, the
doubt the reel answers; persona rule relaxed to exactly this one shot. Shots
4/5/9 regenerated with trading objects + modern pens, same owner session.)

| # | Units | Type | Text | Shot |
|---|---|---|---|---|
| 0 | 2 | video | THEY SAY YOU DON'T HAVE THE TALENT FOR TRADING | Maya from behind, sunset trading desk, blurred chart monitors |
| 1 | 2 | video | TALENT LOSES TO ROUTINE | pre-dawn dark desk, slow push-in |
| 2 | 1 | still | WAKE EARLY | dark bedroom dawn window, coffee steam |
| 3 | 1 | still | TRAIN | running shoes on wet pavement, dawn |
| 4 | 1 | still | STUDY | open journal + pen, morning window light |
| 5 | 1 | still | PLAN | handwritten checklist card on desk |
| 6 | 1 | still | EXECUTE | hands-on-keyboard fragment, soft screen glow |
| 7 | 1 | still | RISK SMALL | single chess pawn on desk in window light |
| 8 | 2 | video | *(none — interrupt)* | rain on window, out-of-focus city |
| 9 | 1 | still | JOURNAL EVERYTHING | evening desk lamp, handwritten pages |
| 10 | 1 | still | PATIENCE | analog wristwatch on wooden desk |
| 11 | 1 | still | IT COMPOUNDS | sunrise over city skyline from high window |
| 12 | 1 | video | FREEDOM | golden-hour highway motion, car POV |
| 13 | 1 | still | WORTH IT | distant silhouette at dusk window, city below |
| 14 | 1 | video | SAME HABITS. TOMORROW. | the same pre-dawn desk, slow settle |

Stills 10, videos 4 (shots 1, 8, 12, 14). Videos generated at 6s (2-unit shots)
/ 3s (1-unit shots, 6s fallback) so every slot has cover.

## Aesthetic (every AI prompt)

Photorealistic candid photography, 35mm film look, natural/window light, muted
warm tones, soft grain, shallow DOF, vertical 9:16. **Banned:** neon
magenta/teal, sci-fi, readable text/numbers/logos/watermarks, visible faces.
Clock/watch faces blurred or numeral-free — AI-painted numbers are fiction
(house rule 10.1).

## Build

- `scripts/habits/gen_assets.py` — serial grok-cli (images: `grok-cli image
  --json --aspect-ratio 9:16`; videos: same pattern as
  `scripts/grind/gen_clips.py`), writes `remotion/public/habits/shotNN.{png,mp4}`
  + `manifest.json` with `retrieved_at`; resumable.
- `remotion/src/compositions/HabitsReel.tsx` — fixed grid, Ken Burns push on
  stills (alternating direction), 4-frame black dip on every cut (house
  pattern), `Grain`/`Vignette`, house font overlays. Registered in `Root.tsx`.
- Render CRF-19 master + CRF-27 preview → verify frames + confirm silent track
  (rule 10.7) → upload via Higgsfield → CloudFront link for the phone.
