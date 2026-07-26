# Higgsfield audio → Remotion video, on a laptop

How to generate the voiceover for a finished Remotion render and mux it back in.

**This is a laptop task, not a sandbox one.** `higgsfield auth login` is
interactive — it opens a browser and waits — so it cannot complete in a remote
container. The CLI is not installed in the sandbox either.

**There is a ready-to-paste prompt at [§5](#5-the-prompt).**

---

## 1. Setup

```bash
# install (idempotent)
curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh

# authenticate — interactive, opens a browser
higgsfield auth login

# confirm
higgsfield account status
```

If a later call fails with `Session expired` or `Not authenticated`, run
`higgsfield auth login` again. Everything else in this document assumes the
account check passes.

## 2. Generate per segment, never in one take

The instinct is to paste the whole 361-word script and get one file back. Don't.

**Generate one take per beat, then place each at its exact offset.** Reasons:

- A single long take drifts against the video. Nothing forces the narrator to
  reach "Breakout trading…" at 1:10, so by the back half the words and the
  on-screen style no longer match — and on a piece whose entire structure is
  "this segment is about this style", that is not a cosmetic problem.
- One bad segment means regenerating one segment, not the whole track.
- Silence between beats is free and sounds deliberate. Compression to fit is
  what sounds rushed.

The generation call:

```bash
higgsfield generate create seed_audio \
  --prompt "Calm professional male narrator, measured pace, warm and even. \
Says: \"<the segment's exact words>\"" \
  --wait
```

**Seed Audio 1.0** (`seed_audio`) is the default for voice. It is a
text-to-audio model rather than a strict TTS engine — it will not honour a
target duration exactly, so **measure what comes back** and adjust before
placing it. Do not assume a 30-word segment lands at 12 seconds.

> ### ⚠️ DO NOT put voice direction in the prompt — it gets SPOKEN
>
> The `"Calm professional narrator... Says: \"...\""` pattern shown above is
> **wrong**, and every voiceover produced with it carries several seconds of the
> model reading the stage directions aloud.
>
> Measured 2026-07-26, same line, same voice, same model:
>
> | prompt | duration |
> |---|---|
> | `Calm professional female analyst, measured and even... Says: "<19 words>"` | **13.28 s** |
> | `<the same 19 words, nothing else>` | **9.04 s** |
>
> The 4.2 s difference is the direction being narrated.
>
> **Put ONLY the words to be spoken in `prompt`.** Shape the delivery with the
> parameters the model actually exposes — `voice_id` (see `list_voices`),
> `speech_rate`, `pitch_rate`, `loudness_rate` — not with prose.

Download each result to `content/trading_styles/audio/seg_NN.wav`.

## 3. The beat map — Find Your Trading Style

Video is 140.0s / 4200 frames @30fps. Full text per segment is in
[`../content/trading_styles/voiceover_script.md`](../content/trading_styles/voiceover_script.md).

| # | Offset | Segment | Words |
|---|---|---|---|
| 00 | 0:00 / 0s | Intro | 25 |
| 01 | 0:10 / 10s | Scalping | 31 |
| 02 | 0:22 / 22s | Day trading | 32 |
| 03 | 0:34 / 34s | Swing | 31 |
| 04 | 0:46 / 46s | Position | 30 |
| 05 | 0:58 / 58s | Trend | 31 |
| 06 | 1:10 / 70s | Breakout | 31 |
| 07 | 1:22 / 82s | Range | 32 |
| 08 | 1:34 / 94s | News | 32 |
| 09 | 1:46 / 106s | Algorithmic | 31 |
| 10 | 1:58 / 118s | Portfolio | 30 |
| 11 | 2:10 / 130s | Close + disclaimer | 25 |

Each style segment owns a **12-second** slot. A take longer than 12s must be
regenerated shorter — it will collide with the next scene, and the scene change
is a hard visual cut the ear notices.

## 4. Assemble and mux

Build one continuous track by placing each take at its offset over silence, then
mux it onto the video. Nothing is re-encoded on the video side.

```bash
cd content/trading_styles

# 1. a silent bed exactly as long as the video
ffmpeg -f lavfi -i anullsrc=r=48000:cl=stereo -t 140.0 -c:a pcm_s16le bed.wav -y

# 2. delay each take to its offset and mix everything down
#    adelay takes MILLISECONDS, per channel
ffmpeg -i bed.wav \
  -i audio/seg_00.wav -i audio/seg_01.wav -i audio/seg_02.wav \
  -i audio/seg_03.wav -i audio/seg_04.wav -i audio/seg_05.wav \
  -i audio/seg_06.wav -i audio/seg_07.wav -i audio/seg_08.wav \
  -i audio/seg_09.wav -i audio/seg_10.wav -i audio/seg_11.wav \
  -filter_complex "\
[1]adelay=0|0[a0];       [2]adelay=10000|10000[a1];   [3]adelay=22000|22000[a2]; \
[4]adelay=34000|34000[a3];[5]adelay=46000|46000[a4];  [6]adelay=58000|58000[a5]; \
[7]adelay=70000|70000[a6];[8]adelay=82000|82000[a7];  [9]adelay=94000|94000[a8]; \
[10]adelay=106000|106000[a9];[11]adelay=118000|118000[a10];[12]adelay=130000|130000[a11]; \
[0][a0][a1][a2][a3][a4][a5][a6][a7][a8][a9][a10][a11]amix=inputs=13:normalize=0[out]" \
  -map "[out]" -c:a pcm_s16le voiceover.wav -y

# 3. mux onto the video — video stream copied, not re-encoded
ffmpeg -i find_your_trading_style.mp4 -i voiceover.wav \
  -c:v copy -c:a aac -b:a 192k -shortest \
  find_your_trading_style_vo.mp4 -y
```

`normalize=0` on `amix` matters: without it ffmpeg divides every input by the
input count and the result is inaudibly quiet.

### Verify before shipping

```bash
# duration must still be ~140.0s and there must be an audio stream
ffprobe -v error -show_entries format=duration \
        -show_entries stream=codec_type,codec_name -of json find_your_trading_style_vo.mp4

# listen at each scene boundary — the words must match the style on screen
for t in 9 21 33 45 57 69 81 93 105 117 129; do
  ffmpeg -v error -ss $t -i find_your_trading_style_vo.mp4 -t 3 -vn /tmp/chk_$t.wav -y
done
```

The failure this catches is drift: audio that starts correct and is a full
segment out of step by the end. Check the **last** boundary, not the first.

## 5. The prompt

Paste into Claude Code from the repo root, on the laptop.

---

> Read `references/higgsfield-audio-workflow.md`, then produce the voiceover for
> `content/trading_styles/find_your_trading_style.mp4` and mux it in.
>
> **Setup first.** Install the Higgsfield CLI if it is not on `$PATH`, then run
> `higgsfield account status`. If that fails, stop and ask me to run
> `higgsfield auth login` — it is interactive and you cannot complete it. Do not
> proceed until the account check passes.
>
> **Generate one take per beat, not one long take.** The script and per-segment
> word counts are in `content/trading_styles/voiceover_script.md`; the offsets are
> in §3 of the workflow doc. Use `seed_audio` with a voice direction of calm,
> professional, measured, warm — and hold that same direction across all twelve so
> the tone does not shift between styles. The piece's entire premise is that no
> style is better than another, and a narrator who brightens for scalping
> undermines it.
>
> **Measure every take before placing it.** `seed_audio` does not honour a target
> duration. Any style segment longer than 12 seconds must be regenerated shorter —
> it will run into the next scene, and the scene cut is a hard visual change the
> ear notices. Being a second under is fine and sounds deliberate.
>
> **Assemble and mux** with the ffmpeg recipe in §4. Keep `normalize=0` on the
> `amix` or the whole track comes out inaudibly quiet. Copy the video stream, do
> not re-encode it.
>
> **Then verify, and do not skip this.** Extract three seconds of audio at each
> scene boundary and confirm the words match the style on screen — check the LAST
> boundary specifically, because the failure mode here is cumulative drift that
> looks fine at the start and is a whole segment out by the end. Report the actual
> measured duration of every take in a table rather than telling me it worked.
>
> Write the result to `content/trading_styles/find_your_trading_style_vo.mp4`,
> keep the takes in `content/trading_styles/audio/`, commit to
> `claude/refresh-data-import-stock-story-svya0l` and push.
>
> The closing line "This is educational content, not financial advice" must be in
> the audio, not just on screen.

---

## 6. Reusing this for other renders

The only thing specific to this video is the offset table. For any other
Remotion piece: take the beat map from its composition constants, convert frames
to seconds at 30fps, and the rest of §4 is unchanged.

Music: `seed_audio` also handles beds and ambience. If you add one, duck it under
the voice (`sidechaincompress`) rather than mixing it flat — a bed at constant
level fights narration in a way that reads as amateur.

---

*Educational content only — not financial advice.*
