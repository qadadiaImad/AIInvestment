# Meme reel — voiceover

`vo_maya.wav` — the narration for `../intc_failed_breakout_voiced.mp4`.

| | |
|---|---|
| Engine | Higgsfield `seed_audio` (Seed Audio 1.0) |
| Voice | preset **Simone** · `d3b201aa-086c-4d54-8568-a6bb9f4a0b63` |
| Params | `speech_rate: 0` (default) |
| Duration | 11.62 s |
| Placed at | **2.0 s** into the 17.0 s reel, loudness-normalised to −16 LUFS |

## The script — exactly what was sent as `prompt`

```
Intel, daily. One level: one forty-one forty-five. Twice it stalled there,
and never closed above. Higher high. Lower close. No close above the level,
no breakout. The level held.
```

Nothing else. **No voice direction in the prompt** — `seed_audio` speaks it.
Same line with a `"Calm professional analyst... Says:"` prefix measured 13.28 s
against 9.04 s bare; the difference is the model narrating the directions. See
the warning box in `references/higgsfield-audio-workflow.md`.

## Voice choice

There is no "Maya" voice in Higgsfield — Maya is this repo's persona
(`higgs/maya-bio.md`): dry analyst, no hype, no emoji, educational. Simone was
picked to match that register. **It was chosen from the name and the persona
brief, not auditioned** — swapping it is a one-line `voice_id` change, and the
preview URLs come from `list_voices`.

## Compliance

The narration states only what the caption track states, which is only what the
bars support: one level, two prior rejections, a higher high with a lower close,
and the level holding. No returns claim, no P&L, no recommendation.

## Re-mux

```bash
ffmpeg -y -i intc_failed_breakout.mp4 -i audio/vo_maya.wav \
  -filter_complex "[1:a]adelay=2000|2000,loudnorm=I=-16:TP=-1.5:LRA=11,apad[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest \
  intc_failed_breakout_voiced.mp4
```

Verify the voice actually made it in — a missing track still produces a valid
file:

```bash
ffmpeg -v error -i intc_failed_breakout_voiced.mp4 -vn -ac 1 -ar 8000 /tmp/a.wav -y
# then bucket the RMS; silence reads 0
```

---

*Educational content only — not financial advice.*
