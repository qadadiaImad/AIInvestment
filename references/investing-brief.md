# AI-Sector Quant Investing — Mission Brief (Parts A–D)

> The authoritative-but-perishable context this data engine serves. Pasted by the project
> owner. **Last refreshed: late May 2026. All figures decay — re-verify before acting.**
> *Educational only. Not investment advice.*
>
> This file is the **consumer** of the data engine. When deciding *what* to retrieve and
> *why a number matters*, read here. When deciding *how* to retrieve it, read the other
> `references/` docs and `../CLAUDE.md`.

---

## PART A — System prompt / role

**Role.** Quantitative research assistant covering the AI value chain. Map exposure across
the stack, screen valuation, trace capital flows, surface catalysts and risks. No buy/sell
recommendations — give the facts and framework the investor needs to decide.

**Non-negotiable operating rules**

1. **Never trust memory for a number.** Every price, valuation, multiple, deal size, GF
   Value, or "current holder of X" must come from a fresh search and carry a date stamp.
   Treat your own prior messages as stale.
2. **Always locate a name in the stack** (Energy → Chips → Infra/Neocloud → Models →
   Application) before discussing it. State which layer(s) and why.
3. **Always run the constraint check.** What's the *physical* bottleneck (power, turbines,
   transmission, fab capacity, HBM, packaging) and the *regulatory* bottleneck (permitting,
   export controls, local moratoria)? Lead times are the alpha.
4. **Always trace the relationships and capex.** Name counterparties, dollar size, duration,
   termination clauses — they reveal who actually has pricing power.
5. **Separate fact from rumor.** Label IPO timing, valuations, unannounced deals as
   *reported / rumored / filed* and cite source class (S-1, Bloomberg, press release, blog).
6. **Distinguish profitable from pre-revenue.** DCF/GF Value/P/E are meaningful for
   cash-generating businesses, misleading for story stocks. Size pre-revenue names as
   venture bets, not value buys, and say so.
7. **Treat the environment as volatile and reflexive.** Every constraint spawns a *solution*
   or a *regulation*. Frame outcomes as scenarios with catalysts, not point predictions.
8. **Always end with risks and disclaimers.** Concentration, liquidity, lockups, IPO
   "pop-then-drop," margin, FX, single-counterparty risk. Not a financial advisor.

**Per-query workflow:** `search live → place in stack → valuation read (with model caveats)
→ constraint check (physical + regulatory) → relationship/capex map → catalysts & calendar
→ scenarios → risks/disclaimer.`

**Output style.** Dashboard-like, scannable. Per name: ticker, layer, live price + date,
valuation verdict, the one bottleneck that matters, key counterparties. Flag "verify live"
where data is older than a few days.

---

## PART B — The AI stack & the big players

**Layer 0 — Energy & power (the gatekeeper)**
- IPPs/generators: Vistra (VST), Constellation (CEG), Talen (TLN), NRG (NRG), Public
  Service Enterprise (PEG), Southern (SO), Dominion (D).
- Equipment & grid: GE Vernova (GEV), Siemens Energy, Vertiv (VRT), Eaton (ETN),
  Quanta (PWR), Schneider Electric.
- SMR/advanced nuclear (speculative): NuScale (SMR), Oklo (OKLO), Nano Nuclear (NNE),
  Centrus (LEU, fuel).
- Pipeline/gas feedstock: Williams (WMB), Kinder Morgan (KMI), Energy Transfer (ET).

**Layer 1 — Chips & semis**
- Compute: Nvidia (NVDA), AMD (AMD), Broadcom (AVGO), Marvell (MRVL), Cerebras *(IPO 2026, CBRS)*.
- Foundry & equipment: TSMC (TSM), ASML (ASML), Applied Materials (AMAT), Lam (LRCX), KLA (KLAC).
- Memory/HBM: SK Hynix, Samsung, Micron (MU).

**Layer 2 — Infrastructure / neocloud / data centers**
- Neoclouds: CoreWeave (CRWV), Nebius (NBIS), IREN (IREN), Crusoe *(private)*, Lambda
  *(private)*; SpaceX/xAI dual-monetization capacity *(IPO 2026)*.
- Hyperscalers: Microsoft (MSFT), Amazon (AMZN), Alphabet (GOOGL), Oracle (ORCL), Meta (META).
- DC REITs/physical: Equinix (EQIX), Digital Realty (DLR); Blackstone BXDC AI-DC vehicle.
- Decentralized compute (speculative): Akash, Render, io.net.

**Layer 3 — Models (foundation)**
- Public proxies: Alphabet (GOOGL, Gemini/DeepMind), Meta (META, Llama), Microsoft (MSFT,
  OpenAI stake), Amazon (AMZN, Anthropic stake + Bedrock).
- Pure-play labs: OpenAI *(IPO Q4 2026)*, Anthropic *(IPO ~Oct 2026)*, xAI (inside SpaceX,
  *IPO 2026*), Mistral *(private)*, Cohere *(private)*.
- Note (Q1 2026, Counterpoint): Anthropic led global LLM revenue share ~31.4%, ahead of
  OpenAI ~29% — verify, share shifts fast.

**Layer 4 — Application & tooling**
- Palantir (PLTR), ServiceNow (NOW), Salesforce (CRM), CrowdStrike (CRWD), Figma (FIG),
  Datadog (DDOG), Snowflake (SNOW), Duolingo (DUOL), and the vertical app long tail.

---

## PART C — Capital & relationship map (a web, not a chain)

Companies are simultaneously each other's investors, vendors, customers, rivals. Watch the
*direction* and *duration* of the money.

**Anthropic's compute stack (multi-sourced):**
- Google: ~1M TPUs / ~1 GW; reported ~$200B Google Cloud commitment; Alphabet ~14% equity
  stake (capped ~15%).
- AWS/Amazon: up to ~5 GW; reported $100B+ over a decade; ~$13B equity.
- SpaceX/Colossus 1: full 300 MW, ~220k GPUs, ~$1.25B/month to May 2029, **90-day exit**.
- Plus Nvidia and Microsoft capacity. Run-rate reported ~$44B annualized (May 2026);
  break-even target ~2028.

**OpenAI:** "Stargate" build-out (~33 GW vision); Microsoft (equity + Azure), Oracle and
others as infra partners; ~$25B annualized revenue; ~$852B last private valuation; spending
plans ~$115B over four years; profitability target ~2030.

**SpaceX / xAI:** xAI folded into SpaceX as wholly-owned subsidiary (~$250B implied);
combined valuation discussed >$1T; 2025 revenue ~$15–19B (Starlink the profit engine), with
a sizeable net loss; Musk ~85% voting power. Pursuing orbital data centers (filing to launch
up to ~1M satellites, possibly from 2028).

**Reading the map:** the real question is *who has pricing power*. Short leases and
competitors reselling capacity push GPU compute toward **commodity**; scarce/sticky assets
are **power**, **leading-edge fab/packaging**, and **proprietary models with distribution**.

---

## PART D — Constraints, regulation & volatile edges

### Energy constraints
- **Nuclear (large):** ~10–20 yr permit-to-power, cost overruns, fuel supply. A 2035+ story,
  not 2030. SMRs (NuScale/Oklo) not yet at commercial scale — pre-revenue, licensing risk.
- **Gas turbines:** near-term workhorse, but GE Vernova/Siemens face multi-year backlogs —
  turbine build capacity is itself a bottleneck.
- **Grid:** interconnection queues stretch years; HV transmission permitting can exceed a
  decade. Water/cooling siting adds friction → Texas (ERCOT), PJM, behind-the-meter on-site gas.
- **Cost pass-through risk:** rising residential bills near DC clusters = political flashpoint.

### Chip & manufacturing constraints
- Leading-edge concentration: TSMC dominates advanced nodes; Taiwan geopolitical single-point risk.
- Advanced packaging (CoWoS) and HBM are the real near-term bottlenecks, not raw wafers.
- EUV: ASML sole supplier — another single point.
- Export controls: US restrictions on high-end GPUs to China reshape demand, create gray
  markets; rules change with administrations.

### Regulatory watch-list
- US/EU chip export controls; EU AI Act phase-ins (regulates AI uses/systems).
- Energy & siting: local DC moratoria, utility tariff design, permitting reform.
- Securities/IPO dynamics: three mega-IPOs (SpaceX, OpenAI, Anthropic) may drain H2-2026
  liquidity; lockups and "pop-then-drop" (Figma, Cerebras) are structural retail risks.
- Antitrust: scrutiny of hyperscaler stakes in labs (equity caps already appearing).

### The "mini data center at home" question
- Edge/local inference is real and growing (NPUs, small local models). Frontier training and
  large-scale inference favor tightly-coupled hyperscale (InfiniBand, power density, cooling)
  — distributed home GPUs can't match economics or latency/SLA. Home = **inference/edge** story.
- "Rent out your GPUs" exists (Akash, Render, io.net). Limits: residential power/cooling,
  reliability/SLA, security, bandwidth, unit economics. Speculative; watch, don't anchor.
- Regulation: home compute largely unregulated today; future friction more likely from
  energy/grid rules, GPU export controls, data-privacy, tax, and (if a rental marketplace)
  utility/zoning/securities law. Durable winners remain **power + leading-edge chips +
  hyperscale**, with decentralized compute a small optional satellite.

### Where to hunt for winners
- Scarcest links win pricing power: power generation/equipment, leading-edge fab & packaging,
  HBM, models with real distribution.
- Commoditizing links compress margins: undifferentiated GPU rental / neocloud.
- Catalyst calendar: 2026 IPO trio; quarterly hyperscaler capex guides; turbine/SMR orders;
  export-control updates; interconnection & permitting reform.

---

## Appendix — Free / low-cost data sources (the targets this engine retrieves from)

- **SEC EDGAR** — filings, S-1s, 10-Ks (free, authoritative; IPO source of truth).
- **FRED (St. Louis Fed)** — macro, rates, electricity prices (free API).
- **yfinance** (Yahoo wrapper) — prices/fundamentals (free; unofficial).
- **Alpha Vantage / Finnhub / Financial Modeling Prep / Tiingo** — free-tier quotes,
  fundamentals, news.
- **Polygon.io** — free delayed quotes; paid real-time.
- **Nasdaq Data Link (Quandl)** — datasets, some free.
- **GuruFocus / Koyfin / Simply Wall St** — paid; where GF Value / quality scores live
  (the **gated** targets — see `../providers/README.md`).
- **Wiring to an LLM:** expose these via tools/MCP so the model retrieves *fresh* numbers
  rather than recalling stale ones — the single most important habit in this sector.

---

*Reminder: not a financial advisor. Prices, valuations, deal terms, and IPO timing here
reflect reports from ~late May 2026 and will change. Verify against primary sources
(filings, company releases) before any decision.*
