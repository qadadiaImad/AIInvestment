"""Macro stress overlay for the AI capital web.

Two public functions:

``fetch_macro_snapshot()``  — thin network wrapper; pulls DFF, DGS10 and
    APU000072610 from FRED (keyless CSV) and returns the latest non-null
    value for each, plus a UTC ``retrieved_at`` timestamp.  Not unit-tested
    (network I/O).

``stress_graph(graph_dict, snapshot, baselines)``  — pure computation.
    Takes the canonical graph_dict, a macro snapshot dict, and optional
    baseline overrides.  Returns a parallel-edges list with
    ``stress_score ∈ [0,1]`` (L0-energy outbound up to 1.5) and
    ``stressed_weight``, plus a ``params`` provenance dict.

Three channels, per §4 of the feasibility spec:

  Channel 1 — Rates (DFF / DGS10)
      stress_score = max(0, 1 − beta × Δrate_bps / 100)
      Termination amplifier: ≤90 days → (1−raw)*1.5; 91–180 → (1−raw)*1.2.

  Channel 2 — Electricity (APU000072610)
      L2-infra dst: stress = max(0, 1 − 0.15 × Δelec_pct); capped at 1.
      L0-energy src outbound: stress = min(1.5, 1 + 0.15 × Δelec_pct).

  Channel 3 — Rate-regime trigger
      DFF ≥ 5.5 → subtract 0.15 from all rumored edges (floored at 0).

Base weight (proxy for unsized edges):
    w_base = certainty_w × type_base_weight
    stressed_weight = w_base × stress_score

Educational/research only — not investment advice.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Neocloud tickers (floating-rate private credit; heavy off-B/S leases).
_NEOCLOUD_TICKERS: frozenset[str] = frozenset({"CRWV", "NBIS", "IREN"})

#: Hyperscaler tickers (IG balance sheet; huge FCF — less rate-sensitive).
_HYPERSCALER_TICKERS: frozenset[str] = frozenset({"MSFT", "AMZN", "GOOGL", "META"})

#: Betas per edge type / src class (per +100 bps).
#: compute_commitment is further split by src class in _rate_beta().
_RATE_BETA: dict[str, float] = {
    "equity_stake": 0.08,
    "customer": 0.02,
    "infra_partner": 0.01,
    "voting_power": 0.01,
    "subsidiary": 0.01,
}

#: Electricity stress coefficient (gamma).
_ELEC_GAMMA: float = 0.15

#: DFF threshold for the regime-trigger channel.
_DFF_REGIME_THRESHOLD: float = 5.5

#: Extra discount on rumored edges when DFF ≥ threshold.
_RUMORED_DISCOUNT: float = 0.15

#: Certainty weights.
_CERTAINTY_W: dict[str, float] = {"filed": 1.0, "reported": 0.7, "rumored": 0.3}

#: Base weights per edge type.
_TYPE_BASE: dict[str, float] = {
    "compute_commitment": 3.0,
    "equity_stake": 2.0,
    "voting_power": 2.0,
    "subsidiary": 2.0,
    "customer": 1.0,
    "infra_partner": 1.0,
}

#: Default baselines (spec §4).
_DEFAULT_BASELINES: dict[str, float] = {
    "dff": 4.50,
    "dgs10": 4.25,
    "elec": 0.142,
}


# ---------------------------------------------------------------------------
# Network function (not unit-tested)
# ---------------------------------------------------------------------------

def fetch_macro_snapshot(session=None) -> dict[str, Any]:
    """Fetch latest DFF, DGS10, and APU000072610 from FRED (keyless CSV).

    Returns::

        {
            "dff": float,        # Fed Funds Effective Rate (%)
            "dgs10": float,      # 10-Year Treasury Constant Maturity (%)
            "elec": float,       # Avg US residential electricity price ($/kWh)
            "retrieved_at": str, # UTC ISO-8601
        }

    Not unit-tested (network I/O).
    """
    from . import fred  # local import — keep network out of pure logic

    def _latest(series_id: str) -> float:
        rows = fred.fetch_csv(series_id, session=session)
        # rows are chronological; find last non-null
        for row in reversed(rows):
            if row["value"] is not None:
                return float(row["value"])
        raise ValueError(f"No non-null values in FRED series {series_id!r}")

    dff = _latest("DFF")
    dgs10 = _latest("DGS10")
    elec = _latest("APU000072610")
    retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"dff": dff, "dgs10": dgs10, "elec": elec, "retrieved_at": retrieved_at}


# ---------------------------------------------------------------------------
# Pure stress computation
# ---------------------------------------------------------------------------

def stress_graph(
    graph_dict: dict,
    snapshot: dict[str, Any],
    baselines: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Compute per-edge macro stress scores from a macro snapshot.

    Parameters
    ----------
    graph_dict:
        Canonical ``{"nodes": [...], "edges": [...]}`` — not mutated.
    snapshot:
        Dict with keys ``"dff"``, ``"dgs10"``, ``"elec"`` (and optionally
        ``"retrieved_at"``).  Values from ``fetch_macro_snapshot()``.
    baselines:
        Override the default baselines (DFF 4.50, DGS10 4.25, ELEC 0.142).

    Returns
    -------
    dict::

        {
            "edges": [
                {
                    "src": str,
                    "dst": str,
                    "type": str,
                    "stress_score": float,   # 0–1 (L0-energy outbound up to 1.5)
                    "stressed_weight": float,
                }
                ...   # same order / length as graph_dict["edges"]
            ],
            "params": {
                "dff": float,
                "dgs10": float,
                "elec": float,
                "delta_dff_bps": float,
                "delta_dgs10_bps": float,
                "delta_elec_pct": float,
                "baselines_used": dict,
                "retrieved_at": str | None,
            },
        }

    Pure — no network calls.
    """
    bl = {**_DEFAULT_BASELINES, **(baselines or {})}

    dff: float = float(snapshot["dff"])
    dgs10: float = float(snapshot["dgs10"])
    elec: float = float(snapshot["elec"])

    delta_dff_bps: float = (dff - bl["dff"]) * 100.0    # % → bps
    delta_dgs10_bps: float = (dgs10 - bl["dgs10"]) * 100.0
    delta_elec_pct: float = (elec - bl["elec"]) / bl["elec"] if bl["elec"] else 0.0

    regime_trigger: bool = dff >= _DFF_REGIME_THRESHOLD

    # Build node-id → layer lookup
    node_layer: dict[str, str] = {
        n["id"]: n.get("layer", "") for n in graph_dict.get("nodes", [])
    }

    out_edges: list[dict[str, Any]] = []
    for edge in graph_dict.get("edges", []):
        src: str = edge.get("src", "")
        dst: str = edge.get("dst", "")
        etype: str = edge.get("type", "")
        certainty: str = edge.get("certainty", "reported")
        attrs: dict = edge.get("attrs") or {}

        src_layer: str = node_layer.get(src, "")
        dst_layer: str = node_layer.get(dst, "")

        # ---------------------------------------------------------------
        # Channel 1 — Rates
        # ---------------------------------------------------------------
        stress = _channel1_rate_stress(
            etype, src, delta_dff_bps, delta_dgs10_bps, attrs
        )

        # ---------------------------------------------------------------
        # Channel 2 — Electricity
        # ---------------------------------------------------------------
        stress = _channel2_elec_stress(stress, etype, src_layer, dst_layer, delta_elec_pct)

        # ---------------------------------------------------------------
        # Channel 3 — Rate-regime discount on rumored edges
        # ---------------------------------------------------------------
        if regime_trigger and certainty == "rumored":
            stress = max(0.0, stress - _RUMORED_DISCOUNT)

        # Final floor
        stress = max(0.0, stress)

        # ---------------------------------------------------------------
        # Base weight
        # ---------------------------------------------------------------
        certainty_w = _CERTAINTY_W.get(certainty, 0.5)
        type_base = _TYPE_BASE.get(etype, 1.0)
        base_weight = certainty_w * type_base
        stressed_weight = base_weight * stress

        out_edges.append(
            {
                "src": src,
                "dst": dst,
                "type": etype,
                "stress_score": stress,
                "stressed_weight": stressed_weight,
            }
        )

    params: dict[str, Any] = {
        "dff": dff,
        "dgs10": dgs10,
        "elec": elec,
        "delta_dff_bps": delta_dff_bps,
        "delta_dgs10_bps": delta_dgs10_bps,
        "delta_elec_pct": delta_elec_pct,
        "baselines_used": bl,
        "retrieved_at": snapshot.get("retrieved_at"),
    }

    return {"edges": out_edges, "params": params}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _rate_beta(etype: str, src: str, delta_bps: float) -> float:
    """Return beta for Channel-1 rate stress (per +100 bps)."""
    if etype == "compute_commitment":
        if src in _NEOCLOUD_TICKERS:
            return 0.12
        if src in _HYPERSCALER_TICKERS:
            return 0.03
        # Other sources: use intermediate value (between neocloud and hyperscaler)
        return 0.02
    return _RATE_BETA.get(etype, 0.01)


def _channel1_rate_stress(
    etype: str,
    src: str,
    delta_dff_bps: float,
    delta_dgs10_bps: float,
    attrs: dict,
) -> float:
    """Compute Channel-1 (rates) stress_score, including termination amplifier.

    Uses DFF delta for compute_commitment; DGS10 delta for equity_stake;
    DFF delta as default for all others.
    """
    # Choose which rate delta drives this edge type
    if etype == "equity_stake":
        delta_bps = delta_dgs10_bps
    else:
        delta_bps = delta_dff_bps

    beta = _rate_beta(etype, src, delta_bps)
    raw_stress = max(0.0, 1.0 - beta * delta_bps / 100.0)

    # Termination amplifier: shortens the effective lock-in → more stressed
    term_days: int | None = attrs.get("termination_days")
    if term_days is not None:
        if term_days <= 90:
            amplifier = 1.5
        elif term_days <= 180:
            amplifier = 1.2
        else:
            amplifier = 1.0
        if amplifier > 1.0:
            # Amplify the stressed portion: stressed_portion = 1 - raw_stress
            stressed_portion = (1.0 - raw_stress) * amplifier
            raw_stress = max(0.0, 1.0 - stressed_portion)

    return raw_stress


def _channel2_elec_stress(
    current_stress: float,
    etype: str,
    src_layer: str,
    dst_layer: str,
    delta_elec_pct: float,
) -> float:
    """Apply Channel-2 (electricity price) stress adjustment.

    L2-infra destination (inbound): lower stress on elec rise.
    L0-energy source outbound: higher stress (margin-positive) on elec rise, capped 1.5.
    Only applies when there is an actual electricity delta.
    """
    if delta_elec_pct == 0.0:
        return current_stress

    if src_layer == "L0-energy":
        # Energy producers benefit from higher elec prices → margin-positive.
        # Takes precedence over dst-layer check so that L0→L2 edges are
        # treated as L0-outbound (supplier benefiting), not L2-inbound stress.
        elec_boost = min(1.5, 1.0 + _ELEC_GAMMA * delta_elec_pct)
        # Use the max (most resilient / boosted)
        return max(current_stress, elec_boost)

    if dst_layer == "L2-infra":
        # Electricity price rise stresses the datacenter/infra operators
        elec_stress = max(0.0, 1.0 - _ELEC_GAMMA * delta_elec_pct)
        # Combine: take the min (most stressed)
        combined = min(current_stress, elec_stress)
        # Cap at 1.0 on the downside branch (can't exceed baseline)
        return min(1.0, combined)

    return current_stress
