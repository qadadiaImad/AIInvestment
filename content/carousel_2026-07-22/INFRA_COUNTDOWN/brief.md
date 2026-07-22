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

Same sector. Four AI-infrastructure names. Four wildly different prices vs. what the fundamentals actually support. 📊

The ranking flips live in the reel — worst to best, judged purely on the gap between price and modeled fair value. Not by story, not by hype. 🔻🔺

The reveal, worst → best:
4️⃣ CIEN — Ciena: ~373% above modeled fair value
3️⃣ ANET — Arista: ~33% above fair value
2️⃣ AVGO — Broadcom: ~26% above fair value
1️⃣ SMCI — Super Micro: ~68% BELOW fair value — the one worth watching 👀

Honesty check before anyone screenshots just the ranking: cheapest-vs-model isn't automatically "best stock." Arista and Broadcom post the best margins of the four (38%+) — they're just priced well ahead of the model right now. Ciena pairs the steepest overvaluation with a thin margin. Super Micro is the value name here, but it also carries the thinnest margin and the most leverage of the group. Read past the rank.

Part 1 of this series (CRDO vs NET) is a few posts back — save this one, it's the framework, not just the ranking. 🔖

Educational only, not financial advice — DYOR.

#SMCI #AVGO #ANET #CIEN #AIinfrastructure #AIstocks #semiconductors #datacenters #fundamentalanalysis #investing #stockstowatch #stocktrading #stockmarket #wallstreet

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

## Voiceover (Karim — generated, `infra_countdown_voiced.mp4` is the post-ready file)

Narration is on (`withVoice: true`) and rendered. Generated locally (Chatterbox
needs `huggingface.co`, blocked from the cloud sandbox — see
`GENERATE_VOICE.md` for the full local-run checklist and the exact timing
mechanics). Six clips: an intro hook line, one per ticker, and an outro —
`remotion/public/audio/infra_countdown/voice_{intro,cien,anet,avgo,smci,outro}.wav`.

**Scripts** (`content/carousel_2026-07-22/INFRA_COUNTDOWN/voice/*.txt`) —
each ticker line ties the business to its on-screen valuation verdict rather
than just describing what the company does:
- INTRO: "Same sector wildly different prices"
- CIEN: "Ciena builds optical networks for data centers, priced well above fair value."
- ANET: "Arista builds switches for AI data centers, still trading above fair value."
- AVGO: "Broadcom designs chips for major clouds, priced above fair value."
- SMCI: "Super Micro builds AI servers, and trades well below fair value."
- OUTRO: "Super Micro trades far below fair value — the one worth watching."

No spoken disclaimer (owner direction 2026-07-22) — the on-screen footer
("...educational, not financial advice") renders for the whole video, so the
outro line instead calls back to the winner. See the Compliance section above:
the caption and footer still carry the caveat.

To regenerate after further script edits: `<chatterbox-venv-python>
scripts/voice/infra_countdown_voice.py`, then re-render:
```
cd remotion && npx remotion render InfraCountdown ../content/carousel_2026-07-22/INFRA_COUNTDOWN/infra_countdown_voiced.mp4
```
