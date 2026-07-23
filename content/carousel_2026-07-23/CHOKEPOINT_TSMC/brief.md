# Chokepoint #1 — TSMC leading-edge fab concentration — 2026-07-23

First post in a new series built off `chokepoints_source.json` (13 chokepoints)
cross-referenced against the capital relationship graph (`capital_web.json` /
`capital_web_enriched.json`, 117 nodes / 392 edges). This entry: `tsmc-advanced-node`,
severity 92/100 — the highest-severity chokepoint in the dataset.

**Node:** TSM (Taiwan Semiconductor Manufacturing Co.) · layer `L1-chips`, edges
also touch `L2-infra` and `L3-models`. 29 graph edges connect to TSM — the ones
below are grouped by sector, using each sector's own relationship vocabulary
(chips = fabless customer / wafer allocation / process node; infra & equipment =
capex / capacity reservation / supply agreement; design tooling = EDA/IP license).

## IG caption

Every AI accelerator you've heard of — Nvidia, AMD's Instinct line, Google's TPUs, the custom silicon inside AWS and Broadcom's ASICs — is fabricated on one company's process nodes, in one country. TSMC makes essentially all of the world's sub-7nm logic. Chips at 7nm-and-below were 74% of TSMC's own wafer revenue in 2025, and its share of global leading-edge output is north of 90%. There's no qualified second source at that scale.

The wafer allocation itself tells you the pecking order: Nvidia has secured roughly 60% of TSMC's 2026 CoWoS advanced-packaging capacity, Broadcom around 15% for its custom AI ASICs, AMD about 11% for the Instinct MI350/MI400 line. Everyone downstream of the AI trade is renting time on the same production line.

TSMC isn't independent of its own chokepoints, either. ASML is its sole source for EUV lithography — TSMC's 2026 capex plan ($52–56B) implies buying on the order of 30 EUV machines just for capacity additions. Lam Research and KLA both name TSMC as a top-3 customer; Entegris pulled 16% of its FY2025 net sales from TSMC materials alone. Cadence and Synopsys co-develop the design tooling TSMC's advanced nodes actually ship on. And when TSMC diversifies geographically — the Dresden (ESMC) and Kumamoto (JASM) joint ventures — its own equipment customers (NXP, Bosch, Infineon, Microchip) show up again as its JV partners.

One fab cluster. One strait. Every layer of the AI stack sits downstream of it — including the layers that supply it.

Save this if you want the rest of the chokepoint series — 12 more to go.

Educational only, not financial advice — DYOR.

#TSM #TSMC #NVDA #AVGO #AMD #ASML #semiconductors #aichips #chokepoints #supplychain #aiinfrastructure #aistocks #investing #stockmarket #wallstreet

## Relationship table (sector-adequate framing)

| Sector | Company | Relationship to TSM | Detail | Certainty |
|---|---|---|---|---|
| Chips (fabless customer) | NVDA | customer | ~60% of TSMC's 2026 CoWoS advanced-packaging allocation | reported |
| Chips (fabless customer) | AVGO | customer | ~15% of CoWoS capacity for custom AI ASICs (Google/Meta) | reported |
| Chips (fabless customer) | AMD | customer | ~11% allocation, powers Instinct MI350/MI400 | reported |
| Chips (fabless customer) | QCOM | infra_partner (primary foundry) | TSMC's largest fabless customer; Snapdragon/Dragonwing SoCs | filed |
| Chips (fabless customer) | MRVL | customer | $2.76B unconditional wafer purchase commitments (FY27+) | filed |
| Chips (fabless customer) | AMZN | customer | Trainium/Inferentia on TSMC 3nm + CoWoS, via Alchip design services | reported |
| Chips (fabless customer) | INTC | customer | ~30% of wafers outsourced to TSMC at 3nm (Arrow Lake/Lunar Lake) | filed |
| Chips (fabless customer) | ADI, CRDO, MU, ARM | customer / infra_partner | wafer supply / licensed-core manufacturing | filed/reported |
| Equipment & materials (infra) | ASML | customer (TSM buys) | sole EUV supplier; ~30 EUV machines implied by 2026 capex ($52–56B) | reported |
| Equipment & materials (infra) | LRCX | customer (TSM buys) | TSM named a top customer FY2023–25 | filed |
| Equipment & materials (infra) | KLAC | customer (TSM buys) | TSM = ~19% of KLAC's FY2025 revenue, largest named customer every year since FY2023 | filed |
| Equipment & materials (infra) | ENTG | customer (TSM buys) | TSM = 16% of ENTG's FY2025 net sales ($526.8M) | filed |
| Equipment & materials (infra) | AMAT | infra_partner | joint innovation partnership at Applied's EPIC Center | reported |
| Design tooling | CDNS, SNPS | infra_partner | certified EDA flows / silicon-proven IP for TSMC's N3/N2/A16/A14 nodes | reported |
| Infra (JV / geographic capacity) | NXPI | infra_partner + equity_stake | 38.8% NC interest in TSM's SSMC JV (Singapore); $183M invested of $587M ESMC (Dresden) commitment, alongside Bosch/Infineon (10% each), TSM 70% | filed |
| Infra (JV / geographic capacity) | MCHP | infra_partner | 40nm capacity via JASM (TSMC's Kumamoto, Japan subsidiary) | reported |

No energy-layer edge exists for TSM in the current graph — omitted rather than inferred; fabs are energy-intensive but that specific relationship isn't in the sourced dataset yet.

## Provenance

- Chokepoint definition, severity score/rationale, tagline: `chokepoints_source.json`
  → `chokepoints[0]` (`id: tsmc-advanced-node`), retrieved 2026-07-15.
- All relationship edges + quotes: `capital_web.json` / `capital_web_enriched.json`,
  edges where `src == "TSM" or dst == "TSM"` (29 of 392 total edges). Certainty
  labels (`filed` = SEC filing, `reported` = news/press) preserved as-is from the
  graph — nothing upgraded or downgraded.
- CoWoS allocation percentages (NVDA/AVGO/AMD) are analyst estimates
  (`certainty: reported`), not TSMC-disclosed figures — flagged as such in the
  caption ("secured roughly", "around").

## Compliance

- Every company named traces to a specific graph edge with a source class;
  no relationship stated without one.
- Percentages and dollar figures are labeled by certainty (filed vs. reported) in
  the table; the caption itself doesn't overstate analyst estimates as fact.
- "Educational only, not financial advice — DYOR" in the caption.

## Voiceover (Maya, opt-in — NOT yet generated in this render)

Script written for **Maya** — `@StackedWithMaya`, the channel's on-camera
persona (`.claude/agents/higgsfield-ugc.md`): 24, sharp markets analyst, calm/
fast-but-controlled delivery, dry wit over hype, no forced slang, one
surprising number per beat.

Voice generation is **not available in this sandbox** — same blocker as the
Karim InfraCountdown voiceover: Chatterbox-style zero-shot cloning needs
`huggingface.co` for model weights, and this session's network policy blocks
that host (confirmed via the proxy's relay-failure log). Unlike Karim, there
is also no existing Maya reference voice sample in this repo yet (only a
Higgsfield avatar reference, `higgs/_maya_avatar.json` — no audio). Leaving
this for later per your instruction: the script below is ready to record
(any TTS/voice-clone pipeline, run wherever you have model access), and once
there's a reference clip for Maya's voice the same `scripts/voice/` pattern
used for Karim can be adapted for her.

Script: [`voice/maya_script.txt`](voice/maya_script.txt) — ~115 words, timed
for a 35–45s Reel.

## Video (silent-first, captions carry the story)

`video/` (Remotion, `ChokepointStory-TSMC` composition, 26s/1080×1920): Chip —
the chips-sector mascot — plays in front of a live animated ring of real
company logos (Nvidia, AMD, Broadcom, Qualcomm, Arm, Intel, NXP, ASML)
orbiting a TSM center mark, while on-screen captions tell the chokepoint's
story beat by beat. No voiceover needed for this cut — every load-bearing
line is on-screen text (muted-autoplay-safe per `references/instagram-best-practices.md`
§3); Maya's `voice/maya_script.txt` can still be recorded later and laid over
the same render once audio generation is available. See `video/README.md`
for the composition/render details.
