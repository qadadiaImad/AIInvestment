# Hormuz reel — voiceover script

Male documentary, close-mic, unhurried but not ponderous. Reads like someone who
has watched this happen before, not like someone selling it.

**Rules this script is written under**
- No first person. No "we", no "I", no "my". The tape is the subject.
- No source is named aloud — provenance lives in the footer, not the narration.
- Nothing is advice: the pattern is *described*, the outcome is *reported*, and
  the last line is the base rate rather than the winner.
- No "educational purposes" disclaimer read aloud. The footer carries it.
- Every figure spoken here comes from `remotion/src/fixtures/oil_reel/hormuz.json`,
  which is built by `scripts/oil_reel/build_hormuz.py` from real Brent bars.

**Timing.** Each line is placed on a fixed frame so the voice lands with the
picture beat it belongs to. Durations are measured after generation, not
estimated — see `mux_vo.py`, which fails loudly if a line overruns the next.

| # | Frame | Time | Line | Lands on |
|---|-------|------|------|----------|
| 1 | 14 | 0.5s | Twenty point nine million barrels cross a single strait every day. A fifth of the world's oil. | the chokepoint stat |
| 2 | 246 | 8.2s | Friday the twenty-seventh. Brent settles at seventy-two. | the last calm bar |
| 3 | 362 | 12.1s | Then it happens on a Saturday. Markets are closed. | the sting + the mark |
| 4 | 464 | 15.5s | Monday opens four fifty-two higher. Six percent, before a single trade. | the gap, framed wide |
| 5 | 598 | 19.9s | It runs to eighty-two, then closes four dollars under. | push into the upper wick |
| 6 | 702 | 23.4s | Whoever chased it bought the high of the day. | the trap, held |
| 7 | 802 | 26.7s | An inside bar. One day sitting entirely inside the day before. | the nested boxes |
| 8 | 908 | 30.3s | The trigger is a close above that range. Stop under the coil. Target, twice the risk. | the trade frame |
| 9 | 1040 | 34.7s | It gets there in two sessions. | the target printing |
| 10 | 1154 | 38.5s | Then the premium unwinds. A hundred and twenty-six in April, seventy by July. | the tape races, camera opens |
| 11 | 1252 | 41.7s | That setup fired seventeen times in two years. It reached target four. | the wide + 24% |

**Why line 11 is the last thing said.** The trade worked, and a reel that stops
there is a highlight. The number that decides whether the method is worth
anything is the one that includes the twelve times it didn't.
