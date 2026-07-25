# Congress + 2 undervalued — 2026-07-25 carousel/reel

Selected via `hot-topics` + a direct sweep of `web/public/data/congress.json`
(material AI-stack trades, `amount_range_low >= $15,001`, sorted by
`filing_date`) and `web/public/data/site.json` (`valuation.fundamental_discount_pct`,
excluding every ticker already used in `CHOKEPOINT_TSMC`/`INFRA_COUNTDOWN`).
Bundle stamp: data as of **2026-07-11** (most recent refresh available in this
session — live refresh is network-blocked here, see task #1/#2 status).

**Format:** 3-slide carousel / quick-cut Reel. Maya narrates continuously
across all 3 slides — the VO does **not** wait for each slide's image to
finish loading/transitioning before speaking the next line; it's one
uninterrupted read while slides cut underneath it, then a short outro tag.
Each slide gets its own ~6s VO beat + its own on-screen headline ("post").

## Why these three

1. **Congress — Nancy Pelosi, INTC.** By far the largest, most material trade
   in the current AI-stack-filtered dataset: a **$1,000,001–$5,000,000
   purchase** of Intel, transaction date 5/29/2026, filed 6/23/2026. Everything
   else material in-window is $15k–$100k routine filings — this is the one
   that's actually a headline.
2. **Duolingo (DUOL) — undervalued #1.** 68.3% discount to modeled fair value
   ($124.76 vs. $393.67), but not a "cheap because it's broken" story: 38.4%
   net margin, 34.7% ROIC, 0.07 debt/equity, still growing revenue 35.5% YoY.
   Down 68.1% over the past year — the gap between the stock chart and the
   fundamentals is the hook.
3. **Intuit (INTU) — undervalued #2.** 66.3% discount ($274.96 vs. $814.91),
   21.9% net margin, 17.2% ROIC, pays a dividend, still growing revenue 15.1%
   YoY. Down 64.2% over the past year.

Both DUOL/INTU were picked over higher-raw-discount names (TEAM 68.4%, e.g.)
specifically because they still post **positive, healthy margins** —
consistent with the channel's standing caveat that "most undervalued" isn't
automatically "best stock" without a fundamentals check.

## Slide scripts (Maya, ~6s each, back-to-back — no wait-for-image gaps)

| Slide | On-screen headline ("post") | Spoken (target ~6s / ~14-17 words) |
|---|---|---|
| 1 — Congress | "PELOSI FILES: $1M–$5M INTEL BUY" | "Congress just filed it — Nancy Pelosi bought one to five million dollars of Intel." |
| 2 — DUOL | "DUOLINGO: DOWN 68%. MARGINS: UP." | "Duolingo is down sixty-eight percent this year, but net margins sit at thirty-eight percent." |
| 3 — INTU | "INTUIT: PRICED LIKE IT'S FAILING. IT'S NOT." | "Intuit's down sixty-four percent too — priced sixty-six percent below its modeled fair value." |
| Outro | "SWIPE LEFT FOR THE FULL BREAKDOWN" | "Full breakdown — swipe left. And don't forget to follow and like." |

Full text also written to `voice/*.txt` (one file per beat, matching the
InfraCountdown script convention) for whichever TTS/voice-clone pipeline
picks this up.

## Master IG/TikTok caption

Congress just filed a seven-figure Intel buy — public record, dated, not a signal, just attention.

While that's making headlines, two names are quietly trading nowhere near what their fundamentals say they're worth. Duolingo: down 68% this year, still posting 38% net margins and 35% revenue growth. Intuit: down 64%, still profitable, still paying a dividend, priced 66% below modeled fair value.

Congress trades are public record — transparency, not a buy signal, not an accusation. Fundamentals shown are as of July 11.

Swipe left for the full numbers. Save this, and don't hesitate to follow for the next one.

Educational only, not financial advice — DYOR.

#Pelosi #INTC #DUOL #INTU #congresstrading #undervaluedstocks #fundamentalanalysis #stockmarket #investing #aistocks #stocktrading #wallstreet

## Compliance

- Congress framing: filed/public-record language only ("just filed it"),
  no accusation, no "copy this trade" language, dated to the actual
  filing/transaction dates.
- Every number (discount %, margin, ROIC, D/E, revenue growth, 1y perf)
  traces to `web/public/data/site.json`, stamped as of 2026-07-11 — noted in
  the caption ("as of July 11") per house rule on decayed figures.
- "Most undervalued" is not framed as "best stock" — margins/ROIC/leverage
  are cited alongside the discount %, same caveat pattern as INFRA_COUNTDOWN.
- Disclaimer present in caption; recommend a spoken/on-screen "not financial
  advice" tag on the outro slide too when this gets built into video.

## Voiceover — not yet generated (same sandbox blocker as prior posts)

Maya's voice isn't cloned anywhere in this repo yet (see `CHOKEPOINT_TSMC/brief.md`'s
Voiceover section — no reference sample, and this session can't reach
`huggingface.co`/Speechify/etc. regardless). Scripts below are ready to record
whenever that's unblocked; each is deliberately self-contained (no "as you
can see" visual-dependent phrasing) so they work read back-to-back without
waiting on slide transitions, per your instruction.

## Next step (not done yet)

This delivers scripts + posts only, to be "merged with videos" later per your
instruction — no Remotion composition built for this one. When ready to
build it, the InfraCountdown/ChokepointStory pattern (per-beat `<Sequence>`
+ `<Audio>`, once VO clips exist) is the template to reuse.
