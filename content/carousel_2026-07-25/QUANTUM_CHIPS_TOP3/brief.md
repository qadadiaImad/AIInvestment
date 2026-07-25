# Top 3 (chips + quantum) — 15s Maya script — 2026-07-25

Picks selected from `web/public/data/site.json` (chips) and
`web/public/data/quantum.json` (quantum), stamped 2026-07-11, plus
`intel_deep_dive.md` (same folder tree, `CONGRESS_UNDERVALUED/`) for Intel's
sourced catalyst list. One name gets most of the runtime (per your spec —
"mainly talking about the stock one, others mentioned quickly"), two get a
quick namedrop, one gets flagged to avoid.

## The pick: Intel (INTC) — ~6.5s of runtime

Chosen because it's the only name in scope with a *stack* of recent,
sourced corporate activity spanning both chips and quantum in one story
(full sourcing in `../CONGRESS_UNDERVALUED/intel_deep_dive.md`):
- US government converted CHIPS Act funds into a 9.9% equity stake (Aug
  2025), now worth ~$36B.
- Apple confirmed as an Intel 18A foundry customer (CES 2026, Jan 2026).
- Panther Lake AI PCs shipped on 18A, Intel's most advanced node.
- NVIDIA took an equity stake in Intel + signed a custom x86 co-design deal
  (completed Dec 2025).
- Intel runs its own quantum-computing research program (Tunnel Falls
  silicon spin-qubit chip, Sandia/university partnerships) — the bridge
  that lets one stock carry both the "chips" and "quantum" angle of this
  script.

Not repeated here: the 18A-yield caveat (still below profitable levels per
reporting) — cut for time in the 15s script, but it's on-record in
`intel_deep_dive.md` and belongs in any longer-form follow-up.

## Quick hits (~4.5s combined)

- **IonQ (IONQ)** — pure quantum-computing play, revenue grew 334.6% YoY
  (`quantum.json`) — "more than tripled" is the accurate, slightly
  conservative read of that number. Not mentioned on-script: IonQ's gross
  margin is still negative (-28.8%) and it trades at ~85x sales — explosive
  growth off a small base, not yet a profitable business. Worth a full
  slide of its own later; too much nuance for a 2-second namedrop here.
- **NVIDIA (NVDA)** — still the highest-margin, highest-growth name in the
  set: 63.0% net margin, revenue +70.7% YoY, +28.4% over the past year
  (`site.json`). Included specifically because it ties back to the Intel
  beat (NVIDIA is now both an Intel investor and co-design partner).

## What to avoid: Rigetti (RGTI) — ~4s

Data-driven, not vibes: RGTI trades at **~553x sales**, with a
**-2,253.6% net margin** and a **fundamental_discount_pct of -1,460.4%**
(`quantum.json`) — the model's fair-value estimate is a small fraction of
the current price, meaning it's priced far ahead of any fundamental
support, and it's still deeply cash-burning. Checked the two obvious
alternates first: QBTS is comparably bad (-663.9% discount, -2,957.2% net
margin) and QUBT is worse still (-916.2% net margin, 447.6x sales) — RGTI
was picked as the single example because it's the most-searched/most
recognizable of the three meme-adjacent quantum names, not because the
others are meaningfully safer. Framed as "priced past its fundamentals,"
not "this will go to zero" — a valuation observation, not a prediction.

## Script (Maya, ~15s, one continuous read)

> "My pick: Intel — a government stake, a new Apple foundry deal, and its
> own quantum chip program. Quick hits: IonQ's revenue more than tripled,
> Nvidia still owns the crown. Skip Rigetti — priced miles past its
> fundamentals, still burning cash."

41 words ≈ 14.9s at a brisk 165 wpm (this is meant to read fast/punchy —
"quick hits" as a spoken cue, not just a label). Written to be read as one
uninterrupted pass, same technique as the congress carousel — doesn't wait
on any visual to land before moving to the next beat.

Rough beat timing if this gets built into video (not done yet):
| Beat | ~Time | Words |
|---|---|---|
| Intel (main) | 0.0–6.5s | 23 |
| IonQ + Nvidia (quick) | 6.5–11.0s | 13 |
| Avoid: Rigetti | 11.0–15.0s | 9 |

## Compliance

- No spoken disclaimer in the script itself — same call your own laptop
  session already made on the InfraCountdown cut ("drop spoken disclaimer,
  close on the winner," commit `d59cedd`) given how tight 15s already is.
  **On-screen text disclaimer is still required** ("Educational only — not
  financial advice · DYOR") per house rule §7 — needs to be burned into
  whatever video/carousel this gets built into, same as every other post
  in this repo.
- "My pick" / "skip" is opinion framing on a content-creator persona, not
  personalized investment advice — no "buy this," no price target, no
  timing call.
- Every number traces to `site.json`/`quantum.json` (2026-07-11 stamp) or
  the already-sourced `intel_deep_dive.md` — nothing invented. Figures are
  dated; note "as of July 11" on-screen if this becomes a visual post.
- Rigetti/QBTS/QUBT comparison numbers are model outputs (fundamental
  discount, margins) — labeled as such above, not stated as fact in the
  script itself (the script just says "priced past its fundamentals,"
  which is what the model shows).

## Not done yet

This is the script only, per your ask — no video/carousel built. Voice
generation has the same sandbox blocker as every other Maya script in this
repo (see `CONGRESS_UNDERVALUED/brief.md`'s Voiceover section) — ready to
record whenever that's unblocked.
