# Congress Panels — Episode 1: "THE REBALANCE"

**Pilot episode.** Source filing: Rep. Dan Newhouse (R-WA04), PTR filed **2026-07-17**,
DocID **20034998**, all transactions dated **2026-07-10**.
Data: `data/congress/fresh_ptrs_20260803.json` (parsed 2026-08-03 from
`disclosures-clerk.house.gov/public_disc/ptr-pdfs/2026/20034998.pdf`, source_class=filing).
Member profile: `data/congress/member_profiles.json` (party Republican; committees:
Agriculture, Appropriations, **Select Committee on the Strategic Competition Between the
United States and the Chinese Communist Party**; DW-NOMINATE dim1 +0.317, Conservative).

**The facts (from the filing):** 31 transactions, one day. 12 buys / 19 sells (partial
sells throughout). Every single row in the smallest disclosure bucket, $1,001–$15,000.
- OUT (partial): NVDA, AMD, AMAT, GOOGL, FTNT, PANW, LLY, MPC, DE, CSX, MGA + full sells
  ADBE, INTU, FMC, HSY, TMO, UPS, UNH, HONAV
- IN: MU, ANET, APH, ACN, HON, MS, FIS, DUK, FE, COST, UBER, AMCR

**The story:** a member of the committee built for the chip war rotated within the AI
stack — out of the GPU/tooling names most exposed to export-control headlines, into
memory (MU), networking (ANET), connectors (APH), and the power layer (DUK, FE).
**The honest verdict:** 31 names, both directions, smallest buckets, one day — the
fingerprint of a portfolio rebalance, not a conviction bet. Say so.

---

## Panels (pilot: 4 of a planned 8)

Art: Z-Image-Turbo draft engine, B&W dramatic manga, 832×1216, fixed seeds.
ALL text is post-process (PIL): art prompts carry NO lettering. Numbers come from the
parsed JSON only. Every panel footer: parody/filing/educational/not-an-accusation line.

### P1 — HOOK ("The Filing")
- **Art:** low-angle dramatic manga panel; a stern silver-haired congressman in a dark
  suit stands before the US Capitol at dusk, storm of paper sheets swirling around him
  like blades, one document glowing in his raised hand; heavy ink, cross-hatching,
  screentone, radiating speed lines, menacing atmosphere. Seed 41001.
- **Caption (top):** JULY 17, 2026. A FILING LANDS AT THE HOUSE CLERK.
- **Title (bottom):** THE REBALANCE — CONGRESS PANELS · EP. 1

### P2 — TENSION ("The Committee")
- **Art:** dramatic manga panel; the same silver-haired congressman seated high at a
  committee hearing bench, pointing forward with extreme foreshortening, his gavel-hand
  huge in frame; behind him a colossal shadow of a coiled dragon wrapped around a giant
  microchip looms on the wall; B&W screentone, hard rim light. Seed 41002.
- **Caption:** REP. DAN NEWHOUSE (R-WA) SITS ON THE SELECT COMMITTEE ON STRATEGIC
  COMPETITION WITH THE CCP — THE COMMITTEE BUILT FOR THE CHIP WAR.
- **Tag (small):** OVERSEES THE CHIP FIGHT. TRADED THE CHIP STOCKS.

### P3 — REVEAL ("The Rotation")
- **Art:** explosive manga action panel; the congressman mid-stride with coat flaring,
  holding aloft a small glowing computer memory chip like a talisman, while giant GPU
  graphics cards topple and shatter behind him, debris and lightning, dense speed lines,
  impact frame, extreme perspective. Seed 41003.
- **Caption:** THE FILING SHOWS 31 TRADES — ONE DAY, JULY 10.
- **Data block (from JSON):** OUT (PARTIAL): NVDA · AMD · AMAT · GOOGL /
  IN: MU · ANET · APH · DUK · FE — EVERY ROW $1,001–$15,000 (FILED RANGES)
- **Beat note:** MU = the US memory maker Beijing barred from critical infrastructure
  in 2023 [verify before lettering — if unverified, drop to "the US memory maker"].

### P4 — VERDICT ("The Honest Read")
- **Art:** quiet aftermath manga panel; the congressman small behind a vast desk in a
  dark office, neat stacks of paper, moonlight through venetian blinds striping the
  floor, calm still atmosphere, fine screentone, no motion lines. Seed 41004.
- **Caption:** THE HONEST READ: 31 NAMES, BOTH DIRECTIONS, SMALLEST BUCKETS —
  A PORTFOLIO REBALANCING, NOT A CONVICTION BET.
- **Verdict line:** VERDICT: WATCH THE COMMITTEE CALENDAR, NOT THIS FILING.

### Planned for full episode (not in pilot): P2b committee-jurisdiction montage,
P3b the power-layer buys (DUK/FE) as "the quiet panel", P3c the party-subtext beat
(a China-hawk posture, a decoupling-aligned portfolio — framed as pattern, not intent),
P4b outro card with provenance.

---

## Compliance checklist (per panel, before ship)
- [ ] No first person anywhere; attribution to "the filing / the public record"
- [ ] Amounts verbatim range buckets; dates from filing; "filed" framing
- [ ] No accusation of wrongdoing, no "insider" language, no profit claims
- [ ] Footer present: PARODY · STYLIZED CARICATURE · BASED ON PUBLIC HOUSE FILINGS
      (DOCID 20034998) · EDUCATIONAL, NOT ADVICE · NOT AN ACCUSATION
- [ ] No JJBA/Araki proper nouns in prompts; caricature is stylized, not photoreal
- [ ] Numbers on screen == numbers in `fresh_ptrs_20260803.json` (code-injected)
