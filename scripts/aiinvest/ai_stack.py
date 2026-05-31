"""The AI value-chain universe, from references/investing-brief.md (Part B).

Tickers are TradingView ``EXCHANGE:SYMBOL`` form for the *america* scanner. Each public
US-listed name lives in ONE primary layer (its dominant exposure). Foreign listings
(Siemens Energy, Schneider, SK Hynix, Samsung) and private / pre-IPO names (OpenAI,
Anthropic, xAI, Mistral, Cohere, Crusoe, Lambda, Cerebras) are intentionally excluded —
they can't be pulled from the america scanner. See PRE_IPO below for the watch-list.
"""
from __future__ import annotations

LAYERS = {
    # L0 — Energy & power (the gatekeeper): IPPs, utilities, equipment/grid, nuclear/uranium, gas
    "L0-energy": [
        "NYSE:VST", "NASDAQ:CEG", "NASDAQ:TLN", "NYSE:NRG", "NYSE:PEG", "NYSE:SO", "NYSE:D",
        "NYSE:NEE", "NYSE:DUK", "NASDAQ:AEP", "NASDAQ:XEL", "NASDAQ:EXC",
        "NYSE:GEV", "NYSE:VRT", "NYSE:ETN", "NYSE:PWR", "NYSE:PH", "NYSE:EMR", "NYSE:HUBB", "NYSE:NVT",
        "NYSE:SMR", "NYSE:OKLO", "NASDAQ:NNE", "NYSE:LEU", "NYSE:CCJ", "NYSE:BWXT",
        "NYSE:WMB", "NYSE:KMI", "NYSE:ET", "NYSE:OKE", "NYSE:TRGP", "NYSE:LNG",
    ],
    # L1 — Chips & semis: compute, foundry/equipment, EDA, memory, optical/interconnect
    "L1-chips": [
        "NASDAQ:NVDA", "NASDAQ:AMD", "NASDAQ:AVGO", "NASDAQ:MRVL", "NASDAQ:QCOM", "NASDAQ:INTC",
        "NASDAQ:ARM", "NASDAQ:TXN", "NASDAQ:MCHP", "NASDAQ:ADI", "NASDAQ:ON", "NASDAQ:NXPI",
        "NASDAQ:MPWR", "NASDAQ:CRDO",
        "NYSE:TSM", "NASDAQ:ASML", "NASDAQ:AMAT", "NASDAQ:LRCX", "NASDAQ:KLAC", "NASDAQ:TER", "NASDAQ:ENTG",
        "NASDAQ:SNPS", "NASDAQ:CDNS",
        "NASDAQ:MU", "NASDAQ:WDC", "NASDAQ:STX", "NYSE:COHR",
    ],
    # L2 — Infra / neocloud / hyperscalers / DC REITs / servers / networking
    "L2-infra": [
        "NASDAQ:CRWV", "NASDAQ:NBIS", "NASDAQ:IREN",
        "NASDAQ:MSFT", "NASDAQ:AMZN", "NASDAQ:GOOGL", "NYSE:ORCL", "NASDAQ:META",
        "NASDAQ:EQIX", "NYSE:DLR",
        "NYSE:DELL", "NASDAQ:SMCI", "NYSE:HPE", "NYSE:ANET", "NASDAQ:CSCO",
        "NASDAQ:NTAP", "NYSE:CIEN",
    ],
    # L3 — Models (foundation): public exposure is via L2 hyperscaler proxies (GOOGL/META/
    # MSFT/AMZN); the pure-play labs are private/pre-IPO (see PRE_IPO). No unique tickers.
    "L3-models": [],
    # L4 — Application, software & tooling
    "L4-application": [
        "NASDAQ:PLTR", "NYSE:NOW", "NYSE:CRM", "NASDAQ:CRWD", "NYSE:FIG", "NASDAQ:DDOG",
        "NYSE:SNOW", "NASDAQ:DUOL", "NYSE:IBM", "NASDAQ:ADBE", "NASDAQ:INTU", "NASDAQ:PANW",
        "NASDAQ:ZS", "NYSE:NET", "NASDAQ:MDB", "NASDAQ:WDAY", "NYSE:AI", "NYSE:PATH",
        "NYSE:S", "NASDAQ:APP", "NASDAQ:TEAM",
    ],
}

# Not tradeable on the america scanner — track via news/filings (SEC EDGAR) instead.
PRE_IPO = {
    "L2-infra": ["Crusoe", "Lambda"],
    "L3-models": ["OpenAI", "Anthropic", "xAI", "Mistral", "Cohere", "Cerebras (CBRS)"],
}


def all_tickers():
    """Flat, de-duplicated list of every tradeable ticker across the stack."""
    seen, out = set(), []
    for tickers in LAYERS.values():
        for t in tickers:
            if t not in seen:
                seen.add(t)
                out.append(t)
    return out


def layer_of(ticker):
    """Return the stack-layer key for a ticker, or None if not in the universe."""
    for layer, tickers in LAYERS.items():
        if ticker in tickers:
            return layer
    return None
