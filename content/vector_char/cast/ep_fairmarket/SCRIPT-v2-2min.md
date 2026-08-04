# FairMarketEp1 — 2-minute script (v2)

Target 120s / 3600 frames @30fps. Current cut is 60s.

**What changed and why.** Rex used to blurt "They made it an INDEX?!" out of
nowhere — he was announcing a fact he had no way of knowing, which is the
narration captioning itself. Now **Sol builds to it**: one filing → people
track these portfolios like a leaderboard → here are the ones they watch →
somebody wrapped it in a fund. Rex's line then lands as a reaction to
something he was just shown, which is what makes it funny instead of
expository.

**Accuracy note.** The STOCK Act's periodic-transaction reporting is a
*congressional* mechanism. A president is not a member of Congress, so the
script says **"politicians whose trades people track"**, never "congress
investors", when both caricatures are on screen. No on-screen text names a
person; the cards state only what public filings state; the parody /
public-record / educational / not-an-accusation footer runs on every frame.

---

## ACT 1 — the claim  (existing VO, ~20s)

| # | who | line | picture |
|---|-----|------|---------|
| 1 | SOL | Kid… let me tell you about the so-called "fair" market. | intro, monitor idles on the tracker chart |
| 2 | REX | Boss! It's all fundamentals, right?! | two-shot |
| 3 | SOL | HA! …Fundamentals. | Sol laughs, Rex arms-crossed |
| 4 | SOL | Sometimes… it trades on POLITICS. | Sol alone |
| 5 | REX | WHAT?! | **reaction — staged IN THE SET now, not a full-screen face** |

## ACT 2 — the evidence  (existing VO, ~10s)

| # | who | line | picture |
|---|-----|------|---------|
| 6 | SOL | July 2022. The Speaker's household sold NVIDIA — days before the chip subsidies passed. At a loss, kid. | **TIMELINE graphic** builds: rail, both markers, gap bracket, 25,000 count |

## ACT 3 — the leaderboard  (NEW, ~40s)

| # | who | line | picture |
|---|-----|------|---------|
| 7 | REX | Okay… but that's one trade. One person. | two-shot |
| 8 | SOL | One? People track these disclosures like a leaderboard. | Sol |
| 9 | SOL | Whole portfolios. Filing by filing. Year by year. | **candlestick chart** progressing on the monitor |
| 10 | SOL | The Speaker's household — technology, mostly. Big positions, disclosed late. | caricature 1 on monitor |
| 11 | SOL | And it isn't one party. Other politicians get tracked exactly the same way. | caricature 2 on monitor |
| 12 | REX | People are keeping SCORE? | Rex reaction |
| 13 | SOL | Some years the trackers reported those portfolios beating the market. That's why people watch. | chart with a marker |
| 14 | SOL | And then somebody did the obvious thing. | Sol, beat |
| 15 | SOL | They wrapped the disclosures in a fund. You can buy the strategy. | **fund graphic** |
| 16 | REX | They made it an INDEX?! | ← now EARNED |
| 17 | SOL | All disclosed. In ranges. Up to 45 days late. All legal. | Sol |

## ACT 4 — Rex is wrong  (existing VO, ~20s)

| # | who | line | picture |
|---|-----|------|---------|
| 18 | REX | Then I'll just copy them! Buy what they buy! | Rex excited — **the one glint-eye line** |
| 19 | SOL | Copy them. With a filing from six weeks ago? | two-shot |
| 20 | REX | Six weeks? | Rex alone |
| 21 | SOL | The trade is public. The edge is not. By the time you read it, the move already happened. | **45-day counter** graphic |
| 22 | REX | So the filings are useless. | Rex deflated |
| 23 | SOL | No. They're a map of attention. Who is watching what, and when. | Sol, then vanishes |

## ACT 5 — the payoff  (NEW + existing, ~20s)

| # | who | line | picture |
|---|-----|------|---------|
| 24 | REX | So what do I actually do with it? | Rex alone |
| 25 | SOL | Watch what they sit near. Committees. Hearings. Then do your own homework. | Sol pops back |
| 26 | REX | So — read the filings! | Rex |
| 27 | SOL | Now you're learning, kid. | Sol |
| 28 | SOL | Fair? No. **But now you can read it.** | ← **closes the thesis the cold open opened**, direct to camera |

---

## AS SHIPPED — v20

**Timeline:** 29 beats, 3600 frames, exactly 120.0s. 32 VO tracks totalling
92.1s of speech; the remaining 28s is graphic builds, reaction holds and
the title/outro. Beat boundaries were computed from MEASURED wav durations,
not estimated, so no line is clipped by its own beat.

**11 new lines generated** (Chatterbox zero-shot, cloned from the existing
Sol and Rex tracks so the new dialogue is continuous with the old):

```
a3_rex_onetrade     rex  3.02s  Okay... but that is one trade. One person.
a3_sol_leaderboard  sol  3.26s  One? People track these disclosures like a leaderboard.
a3_sol_portfolios   sol  3.66s  Whole portfolios. Filing by filing. Year by year.
a3_sol_speaker      sol  5.06s  The Speaker's household. Technology, mostly. Big positions, disclosed late.
a3_sol_others       sol  5.98s  And it is not one person, or one party. Other politicians get tracked exactly the same way.
a3_rex_score        rex  2.06s  People are keeping SCORE?
a3_sol_beating      sol  5.42s  Some years, the trackers reported those portfolios beating the market. That is why people watch.
a3_sol_obvious      sol  2.14s  And then somebody did the obvious thing.
a5_rex_dowhat       rex  2.46s  So what do I actually do with it?
a5_sol_homework     sol  4.38s  Watch what they sit near. Committees. Hearings. Then do your own homework.
a5_sol_fair         sol  2.54s  Fair? No. But now you can read it.
```

Plus `v11_sol_bothsides` and `v12_rex_both`, which had been generated for
the 60s cut and never used — they now carry the both-sides beat.

**Cut in review:** `v13_sol_public` ("all of it public, the law says they
have to disclose") duplicates `v8_sol_legal`, and `v14`/`v15` ("weeks
late") duplicate `a2_sol_sixweeks`. Saying the same fact twice is worse
than a shorter episode, so all three stay on the shelf.

## Assets built

- **`congress2_scheme` / `congress2_smug`** — the second politician
  archetype. First generation came back as young generic businessmen (the
  model ignored the age and build cues); regenerated with heavy age
  weighting. Registered as poses, so they are staged, lit and reframed by
  exactly the same machinery as the cast.
- **`TickerTape`** (motion/Infographic.tsx) — the monitor's idle state is
  now a candlestick tracker printing through time, replacing a decorative
  polyline. The newest bar is live: its close wanders inside its own
  high/low and its colour tracks that live print, so a bar can flip
  green-to-red while you watch. Labelled ILLUSTRATIVE on its face, because
  the series is a seeded walk and not a real price history.

## Two rules now MEASURED, not eyeballed

`scripts/vector/stage_audit.py` parses the real BEATS array out of the
composition and checks, for every shot at both ends of its camera creep:

1. no character overlaps another
2. no actor covers the monitor on a shot that is showing an exhibit
3. no two-shot loses a figure off the frame edge, and no solo push-in
   loses the face

Current status: **0 / 0 / 0 across 29 beats.** It replaces
`overlap_audit.py`, which checked rule 1 against a hand-copied beat list
whose `FLOOR_Y` still said 1900 after the set moved to 1730 — a second
source of truth that had already gone stale.
