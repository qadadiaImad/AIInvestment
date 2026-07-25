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

Take the attached vertical video and present it as a screen-share inside a video call, with a second person visible on camera reacting to it. Output 1080×1920 vertical, 16 seconds, matching the attached clip's exact duration and timing. **Silent — no audio, no music, no voiceover.**

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

**Her performance across the 16 seconds (silent — read as speaking, no audio)**

- 0–5s: looking toward the shared screen, following the chart as it builds, occasional small nod.
- 5–7s: turns to camera and speaks a short beat — natural mouth movement, one small hand gesture entering frame.
- 7–10.5s: eyebrow raise, slight knowing smile, glances back at the screen as the countdown runs — playing the "do you see it?" beat without overacting.
- 10.5–13s: a single confident nod as the answer lands, still speaking to camera.
- 13–16s: settles, small shrug-and-smile, gestures once toward the screen as the lesson card appears.

Motion should be subtle and continuous — natural micro-movement, breathing, occasional blink. No cuts, no camera moves, no zoom. One continuous take.

**Call UI**

Keep it minimal and generic: just the rounded tiles, borders, and the handle chip described above. **Do not include any real video-call product's branding, logo, interface, or color scheme** — no Zoom, FaceTime, Teams, Meet, or any recognizable app UI. A small dim "REC" dot in a corner is fine; nothing else.

**Do not add:** captions, subtitles, extra text overlays, emoji, arrows, watermarks, or any additional graphics on top of the shared screen. The attached video already carries all of its own text.

---

## Notes

**Audio.** Specified silent on purpose. Maya has no cloned voice in this repo yet
(see `../CONGRESS_UNDERVALUED/brief.md` → Voiceover), so anything Grok generates
as speech would be a voice that isn't hers and would break persona continuity
the moment a real one exists. She reads as speaking; the audio gets laid over
later. Trending audio can also be dropped on at post time, which is how the
benchmark reels are actually consumed.

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
