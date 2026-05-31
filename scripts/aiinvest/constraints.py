"""Part D constraint knowledge — the one physical + regulatory bottleneck that matters.

Curated from brief Part D (late May 2026). `for_node(layer, symbol)` returns the relevant
bottleneck record; a specific-name override beats the layer default. Lead times are the
alpha — a great demand story stalls on a turbine backlog or a 20-year nuclear timeline.
"""
from __future__ import annotations

_GENERIC = {
    "physical_bottleneck": "unspecified — verify per name",
    "regulatory_bottleneck": "unspecified — verify per name",
    "lead_time_note": "verify live",
}

BY_LAYER = {
    "L0-energy": {
        "physical_bottleneck": "gas-turbine order backlog (GEV/Siemens); grid interconnection "
                               "queues & high-voltage transmission permitting; water/cooling siting",
        "regulatory_bottleneck": "local data-center moratoria; utility tariff design; permitting reform",
        "lead_time_note": "turbines multi-year; transmission permitting can exceed a decade",
    },
    "L1-chips": {
        "physical_bottleneck": "advanced packaging (CoWoS) and HBM — the real near-term bottleneck, "
                               "not raw wafers; leading-edge node concentration at TSMC",
        "regulatory_bottleneck": "US/EU high-end GPU export controls to China (rules shift by administration)",
        "lead_time_note": "packaging/HBM capacity adds quarters-to-years",
    },
    "L2-infra": {
        "physical_bottleneck": "power & cooling siting; behind-the-meter / on-site gas; GPU supply",
        "regulatory_bottleneck": "local DC moratoria, utility tariffs; antitrust on hyperscaler-lab stakes",
        "lead_time_note": "neocloud GPU rental commoditizing; power is the scarce, sticky asset",
    },
    "L3-models": {
        "physical_bottleneck": "compute access & power (leased, multi-sourced)",
        "regulatory_bottleneck": "antitrust on hyperscaler equity stakes (caps appearing); EU AI Act phase-ins",
        "lead_time_note": "pre-IPO labs are venture bets; revenue share shifts fast",
    },
    "L4-application": {
        "physical_bottleneck": "inference/compute cost pass-through; dependence on upstream model pricing",
        "regulatory_bottleneck": "data-privacy/security; sector-specific & EU AI Act use-case rules",
        "lead_time_note": "valuation sensitive to AI-monetization proof; watch P/E vs growth",
    },
    "private-lab": {
        "physical_bottleneck": "compute access & power (leased, multi-sourced); single-counterparty leases",
        "regulatory_bottleneck": "antitrust on hyperscaler stakes; export controls; EU AI Act",
        "lead_time_note": "pre-revenue / pre-IPO — venture bet, not a value buy",
    },
}

BY_NAME = {
    "ASML": {
        "physical_bottleneck": "EUV lithography — ASML is the sole supplier (single point of failure)",
        "regulatory_bottleneck": "export controls on EUV/DUV tools to China",
        "lead_time_note": "EUV tool lead times are long; demand tied to fab buildout",
    },
    "TSM": {
        "physical_bottleneck": "leading-edge node + CoWoS packaging concentration",
        "regulatory_bottleneck": "Taiwan geopolitical single-point risk; export controls",
        "lead_time_note": "new fabs take years; packaging is the binding constraint",
    },
    "MU": {
        "physical_bottleneck": "HBM capacity — a primary near-term AI bottleneck",
        "regulatory_bottleneck": "export controls on advanced memory",
        "lead_time_note": "HBM ramp adds quarters; tightly allocated",
    },
}

# SMR / advanced-nuclear names: pre-commercial, licensing risk.
for _smr in ("SMR", "OKLO", "NNE"):
    BY_NAME[_smr] = {
        "physical_bottleneck": "no commercial-scale plant yet; fuel supply (HALEU)",
        "regulatory_bottleneck": "NRC design/licensing risk",
        "lead_time_note": "pre-commercial; a 2035+ story, not 2030 — pre-revenue, venture bet",
    }

# Gas-turbine equipment: the bottleneck IS the order backlog.
BY_NAME["GEV"] = {
    "physical_bottleneck": "gas-turbine build capacity — multi-year order backlog is itself the bottleneck",
    "regulatory_bottleneck": "emissions/siting permitting",
    "lead_time_note": "turbine backlog stretches multiple years",
}


def for_node(layer, symbol):
    """Return the constraint record for a name; specific-name override beats layer default."""
    if symbol in BY_NAME:
        return dict(BY_NAME[symbol])
    return dict(BY_LAYER.get(layer, _GENERIC))
