# Grok prompt — Maya talking head (podcast) for the TradingQuiz reel

Grok generates **only Maya**. The compositing happens in Remotion
(`QuizWithHost` composition) so the chart video is embedded pixel-exact and
can't be regenerated or reinterpreted.

Paste her clip into `remotion/public/host/` and render — see "Once you have the
clip" below.

---

## The prompt

```
Load the Maya car reel skill and make a new one with this script:

Maya in a dark podcast studio — condenser mic on a boom arm in the foreground,
acoustic panels behind her, warm key from the left, teal rim light, shallow
depth of field. Chest-up, vertical 1080×1920, 16 seconds, one continuous take,
no cuts, static camera.

She's walking someone through a chart on a screen off to her left — small
glances that way between lines, one light hand gesture, calm and dry. Not a
hype creator.

Her lines, natural pauses in the gaps:
1.0–4.3s   "Watch that level — it's already held three times."
5.3–9.3s   "Now the red candle swallows the green one whole."
10.0–12.0s "Buyers tried. Sellers took all of it."
12.5–15.5s "Bearish engulfing at resistance. That's a sell."

For audio, adapt to this voice: /home/workdir/artifacts/maya_voice_fingerprint.wav

Her voice only — no music, no sound effects. No text, no captions, no graphics,
no UI. Just her.
```

---

## Notes

**Why it's short.** The skill carries Maya's appearance — that's the point of
invoking it. Re-describing her face/hair/wardrobe in the prompt would just risk
contradicting the skill. Only the *setting* (podcast studio) and the *script*
vary per reel.

**Why Grok isn't compositing.** Generative models routinely regenerate an
attached video instead of embedding it. If the candlesticks come back even
slightly different, the bearish-engulfing pattern is no longer mathematically
valid and the reel teaches something false. Remotion embeds the real file.

**Framing matters for the composite.** Chest-up and centered — she gets cropped
into a tile, so anything near the edges gets lost. Static camera for the same
reason.

## Once you have the clip

```bash
cp <maya-clip>.mp4 remotion/public/host/maya_trading_quiz.mp4
cd remotion && npx remotion render src/index.ts QuizWithHost out.mp4 \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell \
  --codec h264 --crf 17
```

The composition renders a placeholder tile until that file exists, so it's
previewable now. If her clip isn't exactly 16s, set `hostDurationInFrames` in
the fixture and it'll be held/trimmed to fit rather than drifting out of sync.
