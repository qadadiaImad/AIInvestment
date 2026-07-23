# Audio generation prompt — ChokepointStory-TSMC (Maya)

Ready-to-use prompt/spec for whatever TTS or voice-clone pipeline generates
Maya's voiceover for `video` composition `ChokepointStory-TSMC`
(1080×1920, 30fps, 780 frames / 26.000s total). Text is **verbatim** from the
on-screen captions in `video/src/compositions/ChokepointStory.tsx`
(`CAPTIONS` array) so spoken audio never drifts from what's on screen.
Timestamps are exact — derived from each caption's `from`/`duration` frame
values at 30fps (`ms = frame * 1000 / 30`), not estimated.

**This supersedes `voice/maya_script.txt`** for this composition — that
earlier file was one continuous paragraph written before `ChokepointStory`
existed and doesn't line up beat-for-beat with the final on-screen captions.
Keep `maya_script.txt` only if you want a non-captioned, straight-narration
cut later; use this file for anything synced to the current render.

## Voice

**Maya** — `@StackedWithMaya`, the channel's persona
(`.claude/agents/higgsfield-ugc.md`): 24, sharp markets analyst. Calm,
fast-but-controlled delivery; dry wit over hype; no forced slang, no
emoji-cadence, no "literally/bestie/no cap." Confident and a little dry, not
a hype creator. Voice is not yet cloned anywhere in this repo (see brief.md's
Voiceover section) — this prompt is ready the moment a reference clip or TTS
voice exists.

## Global constraints

- Each line's spoken audio must fit inside its ms budget below (matches the
  caption's on-screen hold time) — if a generated clip runs long, trim the
  line, don't extend the caption.
- Deliver each line as its own audio file/clip so it can be placed at its
  exact `start_ms` via a `<Sequence>` (same pattern as
  `scripts/voice/infra_countdown_voice.py` used for Karim/InfraCountdown).
- No music/SFX bed implied by this prompt — VO only. Sound design (whoosh 2–3
  frames before each beat's entrance, soft tick under the "90%"/allocation
  numbers) is a separate pass, not part of this prompt.
- "Chokepoint #1 of 13" line (beat 7) should land with a slight smile in the
  voice — it's the CTA, not the risk statement.

## Beats — text + exact placement (ms)

| # | Start (ms) | End (ms) | Budget (ms) | Spoken text |
|---|---|---|---|---|
| 1 | 0 | 1500 | 1500 | "Meet the single point of failure sitting under every AI stock you own." |
| 2 | 1600 | 3000 | 1400 | "One company. One island. TSMC." |
| 3 | 3167 | 9000 | 5833 | "More than 90% of the world's leading-edge chips run through it." |
| 4 | 9167 | 15000 | 5833 | "Nvidia, AMD, Broadcom — all renting time on the same line." |
| 5 | 15167 | 21000 | 5833 | "Even TSMC has a single point of failure: ASML is its only source for EUV lithography." |
| 6 | 21167 | 24500 | 3333 | "One earthquake. One blockade. The whole AI stack stalls." |
| 7 | 24600 | 26000 | 1400 | "Chokepoint #1 of 13 — save this, more of the series coming." |

Beats 1, 2, and 7 are tight (1.4–1.5s) — say them at a brisk, confident pace;
if a TTS render doesn't fit, shorten rather than speed up unnaturally (e.g.
beat 2 can drop to "One company. One island." and let "TSMC" appear as text
only).

## Character-action context (for future SFX/emphasis sync, not required now)

`WAYPOINTS` frame → ms, if a later pass wants a whoosh/hit synced to Chip's
movement: wave @1500ms, point @4667ms, jump @10667ms, point @16667ms,
wave-outro @22667ms (all `frame * 1000/30`, walk transitions in between).

## Output

Once generated, wire the same way as InfraCountdown: files named
`voice_beat1.wav` … `voice_beat7.wav` in a `voiceDir`, gated behind a
`withVoice` prop on `ChokepointStory`, each in its own
`<Sequence from={Math.round(start_ms / 1000 * 30)} layout="none"><Audio .../></Sequence>`
(schema/wiring not yet added to the composition — add it when audio exists,
same pattern as `remotion/src/compositions/InfraCountdown.tsx`).
