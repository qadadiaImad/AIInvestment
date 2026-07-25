# Grok video prompt — Trading Quiz reel

Paste the block below into Grok (attach the benchmark reel too, if you want it
matched more tightly). It describes the **same** setup the Remotion version in
this folder renders, so the two outputs are directly comparable — same pattern,
same beats, same answer.

**No audio** — this is a silent, caption-carried reel by design (matches the
benchmark, and keeps it usable with trending audio dropped on at post time).

---

## The prompt

Generate a 16-second vertical (1080×1920, 9:16) motion-graphics video. No audio, no voiceover, no music — silent, text-and-motion only. Dark financial-terminal aesthetic: near-black background (#0A0D12), neon glow on every chart element, clean sans/serif typography, no stock-footage, no people, no logos.

**Subject:** an animated candlestick chart quiz. A viewer sees a price chart build in real time, is asked to guess the next move, gets a countdown, then sees the answer revealed.

**Beat 1 — Hook (0:00–0:01.5)**
Title card centered near the top: "TRADING QUIZ" in a heavy display serif, "TRADING" in white, "QUIZ" in neon mint green (#34D399). It springs in with a slight scale-up and settles. It stays on screen for the whole video, drifting up slightly as the chart appears.

**Beat 2 — The chart prints (0:01.2–0:05)**
A candlestick chart draws itself left to right, one candle at a time, each candle growing outward from its open price like live tape. Green candles (#34D399) for up, red (#E0524D) for down, each with a soft outer glow. The sequence: a strong uptrend from the lower left, then price stalls and chops sideways across the upper third of the chart.

**Beat 3 — The level (0:04–0:05.5)**
A horizontal dashed amber line (#E0A23B) draws left-to-right across the top of the chop, with a small monospace label above it reading "RESISTANCE · TESTED 3×". The chart has visibly touched and been rejected from this line three separate times.

**Beat 4 — The pattern (0:05.3–0:06.5)**
A rounded amber outline box snaps around the last two candles, pulsing gently. A dashed leader line drops from the box into the empty space below the chart, ending at a monospace amber label: "BEARISH ENGULFING". The two boxed candles: a green candle pushing up into the resistance line, immediately followed by a larger red candle that opens above the green candle's close and closes below its open — visibly swallowing it whole.

**Beat 5 — The fork (0:06.5–0:07.7)**
Two thick glowing arrows spring out from the right edge of the last candle, diverging: one green arrow angling up-right labeled "BUY", one red arrow angling down-right labeled "SELL". Both in bold white display type.

**Beat 6 — Countdown (0:07.7–0:10.5)**
A large monospace digit in a rounded outlined box appears below the title: "3", then "2", then "1", each popping in at a slightly oversized scale and settling. Tension builds; the chart and arrows hold still underneath.

**Beat 7 — The reveal (0:10.5–0:12)**
The countdown is replaced by a large pill-shaped badge reading "SELL" in near-black text on a red (#E0524D) fill with a strong red glow. Under it, one line of white text: "Third rejection. Sellers took the whole candle." The green BUY arrow fades away; the red SELL arrow holds for a beat, then also fades.

**Beat 8 — The proof (0:11.5–0:12.6)**
Three more red candles print in sequence to the right of the boxed pattern, stepping decisively downward — each making a lower high and a lower low than the last. Price breaks well below the chop.

**Beat 9 — The lesson (0:13–0:16)**
A rounded dark card slides up from the bottom third with a thin border. Small amber monospace header: "THE SETUP". Below it, white body text: "A level tested 3× + a red candle that fully engulfs the green one before it = rejection. Confirmation is the next candle printing a lower high AND a lower low."

**Persistent footer** (small, dim, monospace, bottom of frame, entire video): "Illustrative example, not a real chart — educational only, not financial advice · DYOR"

**Motion rules:** no linear easing anywhere — springs on every entrance, fast accelerating exits. Nothing enters simultaneously; stagger everything. Keep all critical text inside the middle 75% vertically (platform UI covers top and bottom). Film grain and a subtle vignette over the whole frame.

---

## Notes for comparing against the Remotion cut

Things the Remotion version does that a generative model will likely miss — worth
checking Grok's output for specifically:

- **The engulfing candle is mathematically correct.** Setup candle opens 97,
  closes 99.8; the next opens 100.5 and closes 96 — the red body fully contains
  the green body. Generative video usually produces candles that *look* like a
  pattern without satisfying it. If the pattern is wrong, the reel is teaching
  something false.
- **Three genuine resistance touches** at the same price (~100), not just a line
  drawn near some highs.
- **The reveal candles actually confirm** — each makes a lower high AND a lower
  low, which is the confirmation rule the closing card states.
- **Text never clips.** The first Remotion render pushed "BUY"/"SELL" past the
  right edge and dropped the pattern label on top of the candles; both needed
  fixing. Check the same two spots.
- **Legibility of the disclaimer** — it has to survive compression and stay
  readable, since it's the compliance rail.

If Grok's cut wins on look but loses on chart accuracy, the practical move is to
take its styling notes back into the Remotion composition rather than shipping
an incorrect chart — the pattern correctness is the whole point of the format.
