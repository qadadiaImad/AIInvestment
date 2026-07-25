# Grok prompt — Maya podcast/video-call wrapper around the Remotion reel

**Input:** attach `trading_quiz_engulfing.mp4` (the Remotion cut in this folder,
1080×1920, 16s, silent).
**Output:** the same reel presented as a screen-share inside a video call, with
Maya reacting/explaining from a podcast studio.

The layout brief is written so the source video is **never covered** — the
Remotion cut has content at the top (title, answer badge), through the middle
(chart), and at the bottom (lesson card, disclaimer footer), so a floating
corner bubble would sit on top of something no matter where it goes. Reserving
a dedicated strip is the layout that actually works. A corner-bubble variant is
included at the end if you want to try both.

---

## The prompt

Load the Maya car reel skill and make a new one with this script:

Take the attached vertical video and present it as a screen-share inside a video call, with Maya on camera explaining it. Output 1080×1920 vertical, 16 seconds, matching the attached clip's exact duration and timing.

For audio, adapt to this voice: `/home/workdir/artifacts/maya_voice_fingerprint.wav`

**Her lines** (timed to the reel's beats — natural pauses in the gaps, no filler):

| Time | Line |
|---|---|
| 1.0–4.3s | "Watch that level — it's already held three times." |
| 5.3–9.3s | "Now the red candle swallows the green one whole." |
| 10.0–12.0s | "Buyers tried. Sellers took all of it." |
| 12.5–15.5s | "Bearish engulfing at resistance. That's a sell." |

Delivery: calm, fast-but-controlled, a little dry. She's walking someone through a chart, not selling them anything. No hype inflection, no upspeak, no forced enthusiasm.

No music bed, no sound effects — her voice only.

**Overall layout**

- **Background:** a dark, moody podcast studio, heavily out of focus (shallow depth of field) — acoustic foam panels on the wall, a warm practical light source, faint amber and teal rim lighting. It should read as atmosphere, not detail. Near-black overall (#0A0D12-ish) so it never competes with the screen.
- **Shared screen (main element):** the attached video, unmodified and uncropped, presented as a rounded-corner card occupying the **top ~78% of the frame**, horizontally centered, with a thin 1px light border, a soft outer glow, and a subtle drop shadow — like a screen being shared in a call. Do not crop, letterbox, zoom, speed up, or overlay anything on this card. Its content must remain fully legible end to end.
- **Presenter tile (small element):** in the **bottom ~18% of the frame**, on the left, a rounded-rectangle webcam tile showing a young woman in a podcast setup, chest-up. Thin border matching the screen card. To the right of her tile, on the studio background, a small monospace handle chip reading `@StackedWithMaya` in dim white, and under it a smaller line: `MARKETS ANALYST`.
- Keep a consistent margin around everything; nothing touches the frame edges.

**The presenter — identity lock (must stay exactly consistent across every generation of this character)**

A 24-year-old mixed-race woman with warm light-to-medium olive skin and natural skin texture (not airbrushed or plastic). Shoulder-length dark hair in soft natural waves. Warm brown eyes, soft-oval face with defined but gentle cheekbones, natural full lips. Light natural makeup — dewy finish, subtle brow, no heavy contour or dramatic eye makeup. Small gold hoop earrings. Wearing a cream ribbed knit top under an oversized soft blazer.

Her expression and energy: calm, quietly confident, dry — a sharp financial analyst walking someone through a chart, not a hype influencer. No exaggerated reactions, no wide-eyed shock, no big gestures.

**Podcast setup around her**

A broadcast condenser microphone on a boom arm entering her tile from the lower-left foreground, slightly out of focus. Closed-back headphones either worn or resting around her neck. Warm key light from front-left, soft teal rim light from behind-right separating her from the dark background. Shallow depth of field so the studio behind her melts into bokeh.

**Her performance across the 16 seconds** (lip-sync to the lines above)

- 0–5s: looking toward the shared screen, following the chart as it builds, occasional small nod. Delivers the first line while glancing between screen and camera.
- 5–9.5s: turns to camera for the second line — one small hand gesture entering frame as she says "swallows."
- 9.5–12s: eyebrow raise, slight knowing smile as the countdown runs; delivers the third line flatly, like it's obvious.
- 12–15.5s: a single confident nod on "that's a sell," still to camera.
- 15.5–16s: settles, small shrug-and-smile, gestures once toward the screen as the lesson card appears.

Motion should be subtle and continuous — natural micro-movement, breathing, occasional blink. No cuts, no camera moves, no zoom. One continuous take.

**Call UI**

Keep it minimal and generic: just the rounded tiles, borders, and the handle chip described above. **Do not include any real video-call product's branding, logo, interface, or color scheme** — no Zoom, FaceTime, Teams, Meet, or any recognizable app UI. A small dim "REC" dot in a corner is fine; nothing else.

**Do not add:** captions, subtitles, extra text overlays, emoji, arrows, watermarks, or any additional graphics on top of the shared screen. The attached video already carries all of its own text.

---

## Notes

**Audio.** Maya speaks here, pinned to her voice fingerprint
(`/home/workdir/artifacts/maya_voice_fingerprint.wav`, in Grok's workspace — not
checked into this repo). This supersedes the earlier "no cloned voice" caveat in
`../CONGRESS_UNDERVALUED/brief.md` and `../../carousel_2026-07-23/CHOKEPOINT_TSMC/brief.md`:
that blocker was about this sandbox's local TTS path, which is still blocked —
the Grok route works. Her voice only; no music bed, so trending audio can still
be layered at post time if you want it.

**Skill invocation.** The prompt opens with the required
`Load the Maya car reel skill…` line per
[`higgs/maya-grok-conventions.md`](../../../higgs/maya-grok-conventions.md).
Reproduce it verbatim; it's a literal Grok-side invocation string.

**Identity lock.** The physical description block is lifted verbatim from
`higgs/maya-facial-prompt.md` (which itself comes from the persona bible in
`.claude/agents/higgsfield-ugc.md`). Reuse that exact block in every future Maya
generation — drifting it is how a recurring character stops being recognizable.
The **only** thing changed here is the setting: home-office → podcast studio.

**What to check in the output**

- **Nothing covers the shared screen.** The reel's lesson card (≈13s onward) and
  the persistent disclaimer footer are the most likely casualties — confirm both
  are fully readable.
- **The attached video plays unmodified** — not re-rendered, re-timed, sped up,
  or "interpreted." Generative models frequently regenerate the content instead
  of compositing it. If the chart differs at all from the source, the output is
  unusable: the whole point of the Remotion cut is that the candlestick pattern
  is mathematically correct.
- **Duration matches 16s exactly** and her beats line up with the reel's
  (countdown ≈7.7–10.5s, answer ≈10.5s).
- **Maya matches the locked description** — hair length, gold hoops, cream knit
  + blazer, no heavy makeup. Regenerate rather than accept drift.
- **No real app branding** crept into the call UI.
- **Her voice matches the fingerprint** and the delivery is dry/controlled — if
  it comes back hype-inflected or upspeaking, that's off-persona, regenerate.
- **Lip-sync lands on the beats** — especially "that's a sell" against the
  answer badge at ≈10.5s.
- **Legibility after compression** — the reel's small monospace text (footer,
  pattern label) has to survive being scaled to 78% and re-encoded. If it turns
  to mush, fall back to the corner-bubble variant below, which keeps the source
  full-size.

---

## Alt variant — corner bubble (source stays full-size)

Swap the two layout bullets for this if the scaled-down text doesn't hold up:

> Present the attached video **full-bleed**, filling the entire 1080×1920 frame,
> unmodified. Place the presenter in a small rounded-rectangle tile in the
> **top-right corner**, roughly 24% of the frame width, inset from the edges,
> with a thin border and soft shadow — positioned in the empty dark space to the
> right of the title and above the chart. Everything else in the prompt stays
> the same.

Tradeoff: the source stays pin-sharp, but the tile will graze the BUY/SELL arrow
labels around 6.5–11s. Check that region specifically.
