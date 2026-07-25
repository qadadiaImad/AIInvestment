# Congress + fundamentals-screened stocks — 2026-07-25 carousel/reel

Selected via `hot-topics` + a direct sweep of `web/public/data/congress.json`
(material AI-stack trades, `amount_range_low >= $15,001`, sorted by
`filing_date`) and `web/public/data/site.json` (`valuation.fundamental_discount_pct`,
excluding every ticker already used in `CHOKEPOINT_TSMC`/`INFRA_COUNTDOWN`).
Bundle stamp: data as of **2026-07-11** (most recent refresh available in this
session — live refresh is network-blocked here, see task #1/#2 status).

**Format:** 5-slide carousel / quick-cut Reel — congress filing, Intel bull
case, a "how to screen for cheap stocks" transition, then two fundsheets
(Duolingo, Super Micro). Intuit was swapped out for Super Micro per your
request; its slide/fixture/script still exist in this folder but are no
longer part of the active lineup (see "Superseded" below). Maya narrates
continuously across all slides — the VO does **not** wait for each slide's
image to finish loading/transitioning before speaking the next line; it's
one uninterrupted read while slides cut underneath it, then a short outro
tag. Each slide gets its own ~6s VO beat + its own on-screen headline.

## Why these

1. **Congress — Pelosi filing, INTC.** The largest, most material trade in
   the current AI-stack-filtered dataset. It's **200 Intel call options**
   ($50 strike, exp. 3/19/2027 — right to 20,000 shares), filed as a
   **$1M–$5M** position, **executed by Paul Pelosi** (Nancy Pelosi's
   husband), transaction date 5/29/2026, filed 6/23/2026 — one day after a
   wave of positive Intel news. See `intel_deep_dive.md` for the dollar-figure
   reconciliation against secondary reporting.
2. **Intel bull case.** Filed right as Intel stacked up real catalysts: a
   9.9% US government equity stake (now worth ~$36B), an Apple 18A foundry
   deal, Panther Lake/18A AI PCs shipping, an NVIDIA equity stake +
   co-design partnership, and a genuine quantum-computing research program
   (Tunnel Falls chip, Sandia/university partnerships, Japan AIST
   collaboration). Full sourcing and the 18A-yield caveat (not sugar-coated)
   in `intel_deep_dive.md`.
3. **"The Method" transition.** Your requested bridge line — "searching for
   cheap stocks, use fundamentals" — reframes the pivot from the congress/
   Intel news into the two screened names, so it doesn't read as a
   non-sequitur cut.
4. **Duolingo (DUOL).** 68.3% discount to modeled fair value ($124.76 vs.
   $393.67), but not a "cheap because it's broken" story: 38.4% net margin,
   34.7% ROIC, 0.07 debt/equity, still growing revenue 35.5% YoY. Down
   68.1% over the past year — the gap between the stock chart and the
   fundamentals is the hook.
5. **Super Micro (SMCI)** — replaces Intuit. 67.9% discount ($28.31 vs.
   $88.20), revenue growing 56.6% YoY, P/E 14.9x. Genuinely mixed picture,
   shown honestly on-slide: gross margin is thin (8.4% — typical for a
   server-assembly business, not a red flag on its own) and debt/equity is
   elevated (1.21) — same caveat this channel already used for SMCI in the
   `INFRA_COUNTDOWN` post ("carries the most leverage of the four"). Down
   44.3% over the past year.

DUOL and Intuit (the original #2) were picked over higher-raw-discount names
(TEAM 68.4%, e.g.) specifically because they still post healthy margins —
that filter doesn't apply as cleanly to SMCI, which is why its stat grid
keeps the thin-margin/high-leverage numbers in amber/red rather than
smoothing them into a clean "undervalued" story. Consistent with the
channel's standing caveat that "most undervalued" isn't automatically "best
stock."

## Slide scripts (Maya, ~6s each, back-to-back — no wait-for-image gaps)

| # | Slide | On-screen headline | Spoken (target ~6s / ~13-17 words) |
|---|---|---|---|
| 1 | Congress | "PELOSI FILING: $1M–$5M INTEL CALLS" | "Congress just filed it — Paul Pelosi bought one to five million dollars in Intel call options." |
| 2 | Why Intel | "GOV STAKE. APPLE DEAL. AI + QUANTUM." | "Intel just landed a government stake, an Apple foundry deal, and record AI-chip demand." |
| 3 | The Method | "SEARCHING FOR CHEAP STOCKS? USE FUNDAMENTALS." | "If you're hunting for cheap stocks, use fundamentals — not just a falling price." |
| 4 | DUOL | "DUOLINGO: DOWN 68%. MARGINS: UP." | "Duolingo is down sixty-eight percent this year, but net margins sit at thirty-eight percent." |
| 5 | SMCI | "SUPER MICRO: -44% BUT GROWING 57%." | "Super Micro is down forty-four percent, priced sixty-eight percent below its modeled fair value." |
| — | Outro | "SWIPE LEFT FOR THE FULL BREAKDOWN" | "Full breakdown — swipe left. And don't forget to follow and like." |

Full text also written to `voice/*.txt` (one file per beat, matching the
InfraCountdown script convention) for whichever TTS/voice-clone pipeline
picks this up: `slide1_congress_intc.txt`, `slide1b_intel_bullcase.txt`,
`slide3_method.txt`, `slide4_duol.txt`, `slide5_smci.txt`, `outro.txt`.
(`slide1b_intel_bullcase.txt`'s name predates the slide numbering settling
on "2" — kept as-is rather than re-touching an already-correct file.)

## Rendered carousel (5 slides, 1080×1350, PNG)

Built on the `KurzSlide` engine (same one used for the AMD/INTC/QBTS
carousels): `kind: "news"` for slides 1–2, `kind: "text"` for slide 3,
`kind: "fundsheet"` for slides 4–5. Logos: `logos/INTC.svg` (existing),
`logos/DUOL.svg` + `logos/SMCI.svg` (new, generated from `simple-icons`
v16.27.0 — same source/process as the existing logo set); slide 3 has no
logo (transition card).

| File | Fixture |
|---|---|
| `slide_1_congress_news.png` | `remotion/src/fixtures/carousel_2026-07-25/slide_1_congress_news.json` |
| `slide_2_intel_bullcase_news.png` | `remotion/src/fixtures/carousel_2026-07-25/slide_2_intel_bullcase_news.json` |
| `slide_3_method_text.png` | `remotion/src/fixtures/carousel_2026-07-25/slide_3_method_text.json` |
| `slide_4_duol_fundsheet.png` | `remotion/src/fixtures/carousel_2026-07-25/slide_4_duol_fundsheet.json` |
| `slide_5_smci_fundsheet.png` | `remotion/src/fixtures/carousel_2026-07-25/slide_5_smci_fundsheet.json` |

Render command (settled frame — a raw `still` at frame 0 catches the
entrance springs mid-animation):
```
npx remotion still src/index.ts KurzSlide out.png --props=<fixture>.json \
  --frame=150 --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell
```

### Superseded (kept, not in the active lineup)

`slide_4_intu_fundsheet.png` / `remotion/src/fixtures/carousel_2026-07-25/slide_4_intu_fundsheet.json`
(Intuit fundsheet) and `voice/slide3_intu.txt` — the original last slide,
before you asked to replace it with Super Micro. Left in place rather than
deleted in case you want an alternate cut later; just not part of the
5-slide order above.

## Master IG/TikTok caption

Congress just filed it: Paul Pelosi (Nancy Pelosi's husband) disclosed Intel call options — 200 contracts, $50 strike, exp 3/19/2027, filed as a $1M–$5M position. Public record, dated, not a signal, just attention.

It landed right as Intel stacked up real catalysts: a 9.9% US government equity stake (now worth ~$36B after the stock's run), a confirmed Apple foundry deal on the new 18A chip process, Panther Lake AI PCs shipping, an NVIDIA equity stake and co-design partnership, and a real quantum-computing research program running with national labs. Not sugar-coating it — 18A yields are still below profitable levels per reporting, this is a turnaround in progress, not a victory lap.

Searching for cheap stocks? Use fundamentals, not just a falling price. Two names that passed the screen: Duolingo, down 68% this year but still posting 38% net margins and 35% revenue growth. Super Micro, down 44%, revenue growing 57% YoY — though margins are thin and leverage is elevated, worth knowing going in.

Congress trades are public record — transparency, not a buy signal, not an accusation. Fundamentals shown are as of July 11; news items are dated and labeled reported/filed, not treated as settled fact.

Swipe left for the full numbers. Save this, and don't hesitate to follow for the next one.

Educational only, not financial advice — DYOR.

#Pelosi #INTC #DUOL #SMCI #congresstrading #undervaluedstocks #fundamentalanalysis #quantumcomputing #stockmarket #investing #aistocks #stocktrading #wallstreet

## Compliance

- Congress framing: filed/public-record language only ("just filed it"),
  no accusation, no "copy this trade" language, dated to the actual
  filing/transaction dates.
- Every number (discount %, margin, ROIC, D/E, revenue growth, 1y perf)
  traces to `web/public/data/site.json`, stamped as of 2026-07-11 — noted in
  the caption ("as of July 11") per house rule on decayed figures.
- "Most undervalued" is not framed as "best stock" — margins/ROIC/leverage
  are cited alongside the discount %, same caveat pattern as INFRA_COUNTDOWN.
  SMCI's thin margin/elevated leverage are shown in amber/red on-slide, not
  smoothed over just because it replaced a cleaner-looking name.
- Disclaimer present in caption; recommend a spoken/on-screen "not financial
  advice" tag on the outro slide too when this gets built into video.

## Voiceover — not yet generated

Maya has a voice fingerprint at
`/home/workdir/artifacts/maya_voice_fingerprint.wav` (Grok's workspace, not this
repo), so these scripts **can** be voiced via Grok — see
[`higgs/maya-grok-conventions.md`](../../../higgs/maya-grok-conventions.md) for
the required prompt format (skill invocation + voice line). What's still blocked
is generating audio *locally from this sandbox*: `huggingface.co` and Speechify
are both denied by the egress policy.

Each script is deliberately self-contained (no "as you can see" visual-dependent
phrasing) so they work read back-to-back without waiting on slide transitions,
per your instruction.

## Next step (not done yet)

This delivers scripts + posts only, to be "merged with videos" later per your
instruction — no Remotion video composition built for this one (the 5 PNGs
above are stills for a carousel post, not a Reel). When ready to build a
video cut, the InfraCountdown/ChokepointStory pattern (per-beat `<Sequence>`
+ `<Audio>`, once VO clips exist) is the template to reuse.
