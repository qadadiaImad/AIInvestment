# AI-infra countdown reel — 2026-07-22 (Part 2 of the face-off series)

`infra_countdown.mp4` — 9:16, ~35s. Built with `remotion/src/compositions/InfraCountdown.tsx`,
data fixture `remotion/src/fixtures/infra_countdown_2026-07-22.json`.

Four AI-infrastructure names, same sector, revealed worst-to-best by discount
to modeled fair value. Each ticker expands into a 5-stat table (Price, Fair
Value, Discount %, Net Margin, Debt/Equity), Chip points at it, then it
collapses into the ranked rail at the bottom — every new reveal is the new
best-so-far, so it always lands at the front and pushes the rest back.

Reveal order (worst → best): **CIEN → ANET → AVGO → SMCI**

| Rank | Ticker | Vs. fair value | Net margin | Debt/equity |
|---|---|---|---|---|
| #1 (best) | SMCI — Super Micro Computer | +67.9% undervalued | +3.7% | 1.21 |
| #2 | AVGO — Broadcom | −25.5% overvalued | +38.8% | 0.74 |
| #3 | ANET — Arista Networks | −33.2% overvalued | +38.3% | 0.00 |
| #4 (worst) | CIEN — Ciena | −372.7% overvalued | +7.9% | 0.55 |

## IG caption

Four similar AI-infrastructure stocks — same sector, comparable business model. Four completely different prices vs. what the fundamentals actually support.

We ranked them worst to best — not by hype, by the gap between price and modeled fair value. Watch the numbers build, then watch the ranking flip in real time as a better name knocks the previous "best" down a spot.

Quick honesty check: cheapest-vs-fair-value isn't automatically "best stock." Ciena and Arista both post excellent margins — they're just priced well ahead of the model right now. Broadcom is the highest-margin name in the group, still overvalued by our numbers. Super Micro is the value name here, but it also carries the most leverage of the four. Read the whole table, not just the rank.

Part 1 of this series (CRDO vs NET) is a few posts back if you missed it. Save this one — it's the framework, not just the ranking.

Educational only, not financial advice — DYOR.

#SMCI #AVGO #ANET #CIEN #aiinfrastructure #aistocks #semiconductors #datacenters #fundamentalanalysis #investing #trading #stocktrading #stockmarket #wallstreet

## Provenance

All figures: `web/public/data/site.json`, generated 2026-07-11. Ranking
metric = `valuation.fundamental_discount_pct` (positive = undervalued,
negative = overvalued vs. `valuation.fundamental_value`). Net margin and
debt/equity from `fundamentals`. No figures invented; NBIS/CRWV excluded
from this lineup per the earlier data caveat (their fundamental_value ==
price exactly in this bundle — no distinct model estimate, not a genuine
"fairly valued" signal).

## Compliance

- Dated footer on every frame: "Figures as of July 11, 2026 — educational,
  not financial advice."
- Framed as a valuation snapshot (price vs. modeled fair value), not a buy/
  sell signal — the caption explicitly warns against reading "most
  undervalued" as "best stock" and calls out each name's real fundamentals.
- No company named without its number traced to the bundle.

## Voiceover (Karim, opt-in — NOT yet generated in this render)

Narration is wired into the composition but **off by default**
(`withVoice: false` in the fixture) because generating it requires the
Chatterbox voice-clone model, and this cloud session's network policy blocks
both `huggingface.co` (Chatterbox's model weights host) and the edge-tts
endpoint — confirmed via the proxy's own relay-failure log (403 on both).
Neither TTS path is reachable from here. The voice asset itself
(`course/persona/voice/karim_sample.wav`) IS in the repo; the generation step
just has to run somewhere with model access — i.e., your machine, per
`course/persona/VOICE.md`'s existing local-Chatterbox pipeline.

**One-time setup** (if not already done — see `VOICE.md`): a Python venv with
`torch` + `chatterbox-tts` installed.

**Generate the 5 clips** (4 ticker blurbs + 1 outro line, ~4.8s each, same
voice/seed/delivery settings as the rest of the channel):
```
<chatterbox-venv-python> scripts/voice/infra_countdown_voice.py
```
Writes `remotion/public/audio/infra_countdown/voice_{cien,anet,avgo,smci,outro}.wav`
+ `durations.json`, and warns if any ticker clip runs past its 5.1667s
display budget (155 frames) so you can trim the script before re-rendering.

**Scripts** (`content/carousel_2026-07-22/INFRA_COUNTDOWN/voice/*.txt`,
"briefly what they're good at," not the numbers already on screen):
- CIEN: "Ciena builds the optical networks moving data across the world's data centers."
- ANET: "Arista builds the high speed switches inside the world's biggest data centers."
- AVGO: "Broadcom designs custom chips and networking silicon for the largest cloud providers."
- SMCI: "Super Micro builds the servers that pack AI chips into deployable racks."
- OUTRO: "Educational commentary only — not financial advice."

Each ticker clip starts exactly when that ticker's card appears and is fully
contained inside its number-display window (before the collapse-into-rail
animation begins) — it does not run during the collapse or into the next
ticker's segment.

**Enable + re-render**: set `"withVoice": true` in
`remotion/src/fixtures/infra_countdown_2026-07-22.json`, then:
```
cd remotion && npx remotion render InfraCountdown out.mp4
```
