"""Tests for macro_stress — pure stress_graph() logic.

Semantics (A0 fix): ``snapshot`` is the zero-stress reference (live FRED
snapshot). A scenario is an explicit ``shock`` dict (Δbps / Δelec_pct)
applied ON TOP of the snapshot. Zero shock → all stress_score == 1.0.

TDD: these tests drive the implementation.
All fixtures are deterministic synthetic snapshots — no network calls.
Educational/research only — not investment advice.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Synthetic graph_dict helpers
# ---------------------------------------------------------------------------

def _node(nid: str, layer: str = "L1-chips") -> dict:
    return {"id": nid, "name": nid, "type": "public", "ticker": nid, "layer": layer}


def _edge(
    src: str,
    dst: str,
    etype: str = "customer",
    certainty: str = "reported",
    attrs: dict | None = None,
) -> dict:
    return {
        "src": src,
        "dst": dst,
        "type": etype,
        "attrs": attrs or {},
        "certainty": certainty,
        "origin": "curated",
        "source_url": "test",
    }


# ---------------------------------------------------------------------------
# Snapshots — these are the live zero-stress reference points.
# Scenarios are expressed as explicit shocks, NOT as different snapshots.
# ---------------------------------------------------------------------------

#: Live snapshot at "current" rates (the zero-shock baseline).
_LIVE_SNAPSHOT = {"dff": 3.64, "dgs10": 4.30, "elec": 0.138, "retrieved_at": "2026-05-31T00:00:00Z"}

#: A legacy-value snapshot matching the old hardcoded baselines; useful for
#: tests that need a specific known value as the live reference.
_BASELINE_SNAPSHOT = {"dff": 4.50, "dgs10": 4.25, "elec": 0.142, "retrieved_at": "2026-05-31T00:00:00Z"}

# ---------------------------------------------------------------------------
# Shock dicts — explicit scenario deltas applied on top of the snapshot.
# ---------------------------------------------------------------------------

#: No shock: zero delta on all channels.
_NO_SHOCK: dict = {}

#: +200bps on both DFF and DGS10 (severe tightening scenario).
_SHOCK_PLUS200BPS: dict = {"dff_bps": 200.0, "dgs10_bps": 200.0}

#: +30% electricity price shock.
_SHOCK_ELEC_UP30PCT: dict = {"elec_pct": 0.30}

#: -20% electricity price (drop scenario).
_SHOCK_ELEC_DOWN20PCT: dict = {"elec_pct": -0.20}

#: DFF shock that brings effective DFF to exactly 5.50 from _BASELINE_SNAPSHOT (4.50 + 100bps).
_SHOCK_DFF_TO_5_5: dict = {"dff_bps": 100.0}

#: DFF shock that brings effective DFF to 6.00 from _BASELINE_SNAPSHOT (4.50 + 150bps).
_SHOCK_DFF_TO_6_0: dict = {"dff_bps": 150.0}

#: DFF shock that brings effective DFF to 6.00 from _BASELINE_SNAPSHOT AND +100bps DGS10.
_SHOCK_DFF_6_0_DGS10_PLUS100: dict = {"dff_bps": 150.0, "dgs10_bps": 100.0}

#: Extreme tightening for floor tests.
_SHOCK_EXTREME: dict = {"dff_bps": 1000.0, "dgs10_bps": 1000.0}


# ---------------------------------------------------------------------------
# Import module under test
# ---------------------------------------------------------------------------

from aiinvest import macro_stress as ms  # noqa: E402


# ---------------------------------------------------------------------------
# Return shape
# ---------------------------------------------------------------------------

class TestReturnShape:
    """stress_graph() must return the correct envelope."""

    def _graph_one_edge(self):
        return {
            "nodes": [_node("MSFT", "L2-infra"), _node("NVDA", "L1-chips")],
            "edges": [_edge("MSFT", "NVDA", "compute_commitment", "filed")],
        }

    def test_returns_edges_and_params_keys(self):
        result = ms.stress_graph(self._graph_one_edge(), _LIVE_SNAPSHOT)
        assert "edges" in result
        assert "params" in result

    def test_edges_length_matches_input(self):
        g = self._graph_one_edge()
        result = ms.stress_graph(g, _LIVE_SNAPSHOT)
        assert len(result["edges"]) == len(g["edges"])

    def test_edge_has_required_keys(self):
        result = ms.stress_graph(self._graph_one_edge(), _LIVE_SNAPSHOT)
        e = result["edges"][0]
        required = {"src", "dst", "type", "stress_score", "stressed_weight"}
        assert required.issubset(e.keys()), f"Missing: {required - e.keys()}"

    def test_params_contains_snapshot_values(self):
        result = ms.stress_graph(self._graph_one_edge(), _LIVE_SNAPSHOT)
        p = result["params"]
        assert "dff" in p and "dgs10" in p and "elec" in p

    def test_stress_score_in_zero_one(self):
        result = ms.stress_graph(self._graph_one_edge(), _LIVE_SNAPSHOT, _SHOCK_PLUS200BPS)
        for e in result["edges"]:
            assert 0.0 <= e["stress_score"] <= 1.0, (
                f"stress_score out of range: {e['stress_score']}"
            )

    def test_stressed_weight_non_negative(self):
        result = ms.stress_graph(self._graph_one_edge(), _LIVE_SNAPSHOT, _SHOCK_PLUS200BPS)
        for e in result["edges"]:
            assert e["stressed_weight"] >= 0.0

    def test_zero_shock_stress_score_is_one(self):
        """No shock applied → stress_score == 1.0 for every edge (core A0 fix)."""
        result = ms.stress_graph(self._graph_one_edge(), _LIVE_SNAPSHOT)
        for e in result["edges"]:
            assert e["stress_score"] == pytest.approx(1.0, abs=1e-9), (
                f"stress_score {e['stress_score']} != 1.0 with zero shock"
            )

    def test_zero_shock_with_stale_dff_still_one(self):
        """Even if snapshot DFF is 3.64 (below old hardcoded 4.50), zero shock => 1.0."""
        result = ms.stress_graph(self._graph_one_edge(), _LIVE_SNAPSHOT, _NO_SHOCK)
        for e in result["edges"]:
            assert e["stress_score"] == pytest.approx(1.0, abs=1e-9)

    def test_empty_graph_returns_empty_edges(self):
        g = {"nodes": [], "edges": []}
        result = ms.stress_graph(g, _LIVE_SNAPSHOT)
        assert result["edges"] == []

    def test_params_contains_shock_applied(self):
        result = ms.stress_graph(self._graph_one_edge(), _LIVE_SNAPSHOT, _SHOCK_PLUS200BPS)
        assert "shock_applied" in result["params"]

    def test_params_delta_bps_zero_when_no_shock(self):
        result = ms.stress_graph(self._graph_one_edge(), _LIVE_SNAPSHOT)
        p = result["params"]
        assert p["delta_dff_bps"] == pytest.approx(0.0)
        assert p["delta_dgs10_bps"] == pytest.approx(0.0)
        assert p["delta_elec_pct"] == pytest.approx(0.0)

    def test_params_delta_bps_matches_shock(self):
        result = ms.stress_graph(self._graph_one_edge(), _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        p = result["params"]
        assert p["delta_dff_bps"] == pytest.approx(200.0)
        assert p["delta_dgs10_bps"] == pytest.approx(200.0)


# ---------------------------------------------------------------------------
# Channel 1 — Rates: neocloud beta > hyperscaler beta
# ---------------------------------------------------------------------------

class TestChannel1Rates:
    """At +200bps DFF shock, neocloud compute_commitment has LOWER stress_score than hyperscaler."""

    def _two_edge_graph(self):
        return {
            "nodes": [
                _node("CRWV", "L2-infra"),   # neocloud src
                _node("MSFT", "L2-infra"),   # hyperscaler src
                _node("NVDA", "L1-chips"),
            ],
            "edges": [
                _edge("CRWV", "NVDA", "compute_commitment", "filed"),
                _edge("MSFT", "NVDA", "compute_commitment", "filed"),
            ],
        }

    def test_neocloud_lower_stress_than_hyperscaler_at_plus200bps(self):
        """Higher beta on CRWV → bigger stress hit → lower stress_score."""
        result = ms.stress_graph(self._two_edge_graph(), _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        by_src = {e["src"]: e["stress_score"] for e in result["edges"]}
        assert by_src["CRWV"] < by_src["MSFT"], (
            f"CRWV stress_score {by_src['CRWV']:.4f} should be < MSFT {by_src['MSFT']:.4f}"
        )

    def test_neocloud_stress_score_strictly_below_one_at_plus200bps(self):
        result = ms.stress_graph(self._two_edge_graph(), _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        by_src = {e["src"]: e["stress_score"] for e in result["edges"]}
        assert by_src["CRWV"] < 1.0

    def test_hyperscaler_stress_less_impacted_than_neocloud(self):
        """Hyperscaler beta is only 0.03 so +200bps → stress=max(0,1-0.06)=0.94."""
        result = ms.stress_graph(self._two_edge_graph(), _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        by_src = {e["src"]: e["stress_score"] for e in result["edges"]}
        # beta=0.03, delta=200bps → stress = 1 - 0.03*2 = 0.94
        assert by_src["MSFT"] == pytest.approx(0.94, abs=1e-6)

    def test_neocloud_exact_stress_at_plus200bps(self):
        """CRWV beta=0.12, shock=+200bps → stress = max(0, 1-0.12*2) = 0.76."""
        result = ms.stress_graph(self._two_edge_graph(), _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        by_src = {e["src"]: e["stress_score"] for e in result["edges"]}
        assert by_src["CRWV"] == pytest.approx(0.76, abs=1e-6)

    def test_equity_stake_uses_dgs10(self):
        """equity_stake stress uses DGS10 shock, beta=0.08."""
        g = {
            "nodes": [_node("MSFT", "L2-infra"), _node("openai", "private-lab")],
            "edges": [_edge("MSFT", "openai", "equity_stake", "filed")],
        }
        shock = {"dgs10_bps": 100.0}  # +100bps DGS10 only; DFF unchanged
        result = ms.stress_graph(g, _BASELINE_SNAPSHOT, shock)
        e = result["edges"][0]
        # delta_dgs10 = 100bps, beta=0.08 → stress = 1 - 0.08*1 = 0.92
        assert e["stress_score"] == pytest.approx(0.92, abs=1e-6)

    def test_stress_score_floored_at_zero(self):
        """Extreme shock should floor at 0, not go negative."""
        g = {
            "nodes": [_node("CRWV", "L2-infra"), _node("NVDA", "L1-chips")],
            "edges": [_edge("CRWV", "NVDA", "compute_commitment", "filed")],
        }
        # +1000bps would give 1 - 0.12*10 = -0.2 → must clamp to 0
        result = ms.stress_graph(g, _BASELINE_SNAPSHOT, _SHOCK_EXTREME)
        assert result["edges"][0]["stress_score"] >= 0.0

    def test_zero_shock_no_rate_stress(self):
        """Zero DFF/DGS10 shock → rate channel contributes nothing → stress = 1.0."""
        g = {
            "nodes": [_node("CRWV", "L2-infra"), _node("NVDA", "L1-chips")],
            "edges": [_edge("CRWV", "NVDA", "compute_commitment", "filed")],
        }
        result = ms.stress_graph(g, _LIVE_SNAPSHOT)
        assert result["edges"][0]["stress_score"] == pytest.approx(1.0, abs=1e-9)

    def test_negative_shock_gives_score_above_one_for_l0(self):
        """Rate cut shock (negative bps) should not lower stress below 1 for non-elec channels."""
        g = {
            "nodes": [_node("CRWV", "L2-infra"), _node("NVDA", "L1-chips")],
            "edges": [_edge("CRWV", "NVDA", "compute_commitment", "filed")],
        }
        # -100bps DFF → 1 - 0.12*(-1) = 1.12 — raw_stress > 1.0; acceptable
        result = ms.stress_graph(g, _BASELINE_SNAPSHOT, {"dff_bps": -100.0})
        assert result["edges"][0]["stress_score"] > 1.0


# ---------------------------------------------------------------------------
# Channel 1 — Termination amplifier
# ---------------------------------------------------------------------------

class TestTerminationAmplifier:
    """termination_days ≤ 90 multiplies (1-stress) by 1.5; 91-180 by 1.2."""

    def _edge_with_term(self, days: int, src: str = "CRWV") -> dict:
        return _edge(src, "NVDA", "compute_commitment", "filed", attrs={"termination_days": days})

    def _graph_with_term(self, days: int, src: str = "CRWV") -> dict:
        return {
            "nodes": [_node(src, "L2-infra"), _node("NVDA", "L1-chips")],
            "edges": [self._edge_with_term(days, src)],
        }

    def test_short_termination_amplifies_stress(self):
        """<=90 days: (1-stress) * 1.5 → final score = 1 - 1.5*(1-stress_raw)."""
        # CRWV +200bps raw stress = 0.76 → (1-0.76)=0.24 * 1.5 = 0.36 → score=0.64
        result_with = ms.stress_graph(self._graph_with_term(30), _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        result_without = ms.stress_graph(
            {
                "nodes": [_node("CRWV", "L2-infra"), _node("NVDA", "L1-chips")],
                "edges": [_edge("CRWV", "NVDA", "compute_commitment", "filed")],
            },
            _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS,
        )
        assert result_with["edges"][0]["stress_score"] < result_without["edges"][0]["stress_score"]

    def test_short_term_exact_value(self):
        """CRWV +200bps raw=0.76; term_days=30 → (1-0.76)*1.5=0.36 → score=0.64."""
        result = ms.stress_graph(self._graph_with_term(30), _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        assert result["edges"][0]["stress_score"] == pytest.approx(0.64, abs=1e-6)

    def test_medium_termination_amplifier(self):
        """CRWV +200bps raw=0.76; term_days=120 → (1-0.76)*1.2=0.288 → score=0.712."""
        result = ms.stress_graph(self._graph_with_term(120), _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        assert result["edges"][0]["stress_score"] == pytest.approx(0.712, abs=1e-6)

    def test_long_termination_no_amplifier(self):
        """term_days=200 → no amplifier; score equals raw stress."""
        result_long = ms.stress_graph(self._graph_with_term(200), _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        result_base = ms.stress_graph(
            {
                "nodes": [_node("CRWV", "L2-infra"), _node("NVDA", "L1-chips")],
                "edges": [_edge("CRWV", "NVDA", "compute_commitment", "filed")],
            },
            _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS,
        )
        assert result_long["edges"][0]["stress_score"] == pytest.approx(
            result_base["edges"][0]["stress_score"], abs=1e-6
        )

    def test_term_score_floored_at_zero(self):
        """Amplified stress must never go below 0."""
        result = ms.stress_graph(self._graph_with_term(30), _BASELINE_SNAPSHOT, _SHOCK_EXTREME)
        assert result["edges"][0]["stress_score"] >= 0.0

    def test_zero_shock_term_no_effect(self):
        """With zero shock, termination days do not alter the 1.0 base score."""
        result = ms.stress_graph(self._graph_with_term(30), _LIVE_SNAPSHOT)
        assert result["edges"][0]["stress_score"] == pytest.approx(1.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Channel 2 — Electricity
# ---------------------------------------------------------------------------

class TestChannel2Electricity:
    """Electricity rise stresses an L2-infra inbound edge (dst is L2-infra)."""

    def _l2_inbound_graph(self) -> dict:
        return {
            "nodes": [
                _node("TSM", "L1-chips"),       # src
                _node("AMZN", "L2-infra"),      # dst — L2-infra; stressed by elec
            ],
            "edges": [_edge("TSM", "AMZN", "customer", "filed")],
        }

    def _l0_outbound_graph(self) -> dict:
        return {
            "nodes": [
                _node("SO", "L0-energy"),       # src L0-energy
                _node("AMZN", "L2-infra"),      # dst
            ],
            "edges": [_edge("SO", "AMZN", "infra_partner", "filed")],
        }

    def test_elec_rise_lowers_stress_on_l2_inbound(self):
        result = ms.stress_graph(self._l2_inbound_graph(), _BASELINE_SNAPSHOT, _SHOCK_ELEC_UP30PCT)
        e = result["edges"][0]
        assert e["stress_score"] < 1.0

    def test_elec_rise_l2_exact_value(self):
        """Δelec_pct = 0.30 → stress = max(0, 1 - 0.15 * 0.30) = 0.955."""
        result = ms.stress_graph(self._l2_inbound_graph(), _BASELINE_SNAPSHOT, _SHOCK_ELEC_UP30PCT)
        e = result["edges"][0]
        assert e["stress_score"] == pytest.approx(1.0 - 0.15 * 0.30, abs=1e-6)

    def test_elec_rise_l0_outbound_above_one_capped_at_1_5(self):
        """L0-energy src outbound stress can exceed 1 (up to 1.5 cap) on elec rise."""
        result = ms.stress_graph(self._l0_outbound_graph(), _BASELINE_SNAPSHOT, _SHOCK_ELEC_UP30PCT)
        e = result["edges"][0]
        expected = min(1.5, 1.0 + 0.15 * 0.30)
        assert e["stress_score"] == pytest.approx(expected, abs=1e-6)

    def test_no_elec_shock_no_channel2_effect(self):
        """No electricity shock → no channel-2 stress impact (score stays 1.0)."""
        result = ms.stress_graph(self._l2_inbound_graph(), _BASELINE_SNAPSHOT)
        e = result["edges"][0]
        assert e["stress_score"] == pytest.approx(1.0, abs=1e-6)

    def test_elec_drop_can_increase_l2_score_capped_at_one(self):
        """Electricity price drop → Δelec_pct < 0 → 1 - 0.15*(-0.20) = 1.03 → clamped to 1.0."""
        result = ms.stress_graph(self._l2_inbound_graph(), _BASELINE_SNAPSHOT, _SHOCK_ELEC_DOWN20PCT)
        e = result["edges"][0]
        # Δelec_pct = -0.20 → 1 - 0.15*(-0.20) = 1.03 → should clamp to 1.0 for L2 inbound
        assert e["stress_score"] <= 1.0


# ---------------------------------------------------------------------------
# Channel 3 — Rate-regime trigger on rumored edges
# ---------------------------------------------------------------------------

class TestChannel3RumoredDiscount:
    """Effective DFF (snapshot + shock) >= 5.5 applies extra -0.15 on all rumored edges."""

    def _rumored_graph(self) -> dict:
        return {
            "nodes": [_node("MSFT", "L2-infra"), _node("openai", "private-lab")],
            "edges": [_edge("MSFT", "openai", "equity_stake", "rumored")],
        }

    def _filed_graph(self) -> dict:
        return {
            "nodes": [_node("MSFT", "L2-infra"), _node("openai", "private-lab")],
            "edges": [_edge("MSFT", "openai", "equity_stake", "filed")],
        }

    def test_dff_shock_to_6_0_discounts_rumored_edge(self):
        """Snapshot 4.50 + shock +150bps → effective DFF 6.0 >= 5.5 → rumored discounted."""
        result = ms.stress_graph(self._rumored_graph(), _BASELINE_SNAPSHOT, _SHOCK_DFF_TO_6_0)
        e = result["edges"][0]
        # Channel1: dgs10_bps=0 → no rate stress on equity_stake.
        # Channel3: DFF>=5.5, rumored → -0.15. Score = 1.0 - 0.15 = 0.85
        assert e["stress_score"] < 1.0

    def test_dff_shock_to_6_0_exact_rumored_discount(self):
        """Effective DFF=6.0, dgs10 no shock → channel1 stress=1.0; channel3 → 1.0-0.15=0.85."""
        result = ms.stress_graph(self._rumored_graph(), _BASELINE_SNAPSHOT, _SHOCK_DFF_TO_6_0)
        e = result["edges"][0]
        assert e["stress_score"] == pytest.approx(0.85, abs=1e-6)

    def test_no_shock_below_5_5_no_channel3(self):
        """No shock, snapshot DFF=4.50 → below 5.5 → no channel3 → rumored edge stress = 1.0."""
        result = ms.stress_graph(self._rumored_graph(), _BASELINE_SNAPSHOT)
        e = result["edges"][0]
        assert e["stress_score"] == pytest.approx(1.0, abs=1e-6)

    def test_dff_shock_to_exactly_5_5_triggers_channel3(self):
        """Snapshot 4.50 + shock +100bps → effective DFF exactly 5.5 (boundary, >=5.5 triggers)."""
        result = ms.stress_graph(self._rumored_graph(), _BASELINE_SNAPSHOT, _SHOCK_DFF_TO_5_5)
        e = result["edges"][0]
        assert e["stress_score"] == pytest.approx(0.85, abs=1e-6)

    def test_filed_edge_not_affected_by_channel3(self):
        """Channel3 only affects rumored edges; filed stays at 1.0 with no other shock."""
        result = ms.stress_graph(self._filed_graph(), _BASELINE_SNAPSHOT, _SHOCK_DFF_TO_6_0)
        e = result["edges"][0]
        # dgs10_bps=0 → channel1 stress=1.0; no channel3 for filed → 1.0
        assert e["stress_score"] == pytest.approx(1.0, abs=1e-6)

    def test_channel3_combined_with_channel1(self):
        """DFF shock to 6.0, DGS10 +100bps, rumored equity_stake: both channels apply."""
        result = ms.stress_graph(self._rumored_graph(), _BASELINE_SNAPSHOT, _SHOCK_DFF_6_0_DGS10_PLUS100)
        e = result["edges"][0]
        # Channel1 equity_stake: dgs10_bps=100bps, beta=0.08 → raw_stress = 1-0.08 = 0.92
        # Channel3: effective DFF >= 5.5, rumored → subtract 0.15 → 0.92-0.15 = 0.77
        assert e["stress_score"] == pytest.approx(0.77, abs=1e-6)

    def test_channel3_floor_at_zero(self):
        """After channel3, score must not go below 0."""
        g = {
            "nodes": [_node("CRWV", "L2-infra"), _node("openai", "private-lab")],
            "edges": [_edge("CRWV", "openai", "compute_commitment", "rumored")],
        }
        result = ms.stress_graph(g, _BASELINE_SNAPSHOT, {"dff_bps": 150.0, "dgs10_bps": 1000.0})
        assert result["edges"][0]["stress_score"] >= 0.0

    def test_live_snapshot_below_threshold_no_channel3(self):
        """Live snapshot with DFF=3.64, zero shock → effective DFF 3.64 < 5.5 → no channel3."""
        result = ms.stress_graph(self._rumored_graph(), _LIVE_SNAPSHOT)
        e = result["edges"][0]
        assert e["stress_score"] == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Base weight computation
# ---------------------------------------------------------------------------

class TestBaseWeight:
    """stressed_weight = base_weight * stress_score; base from certainty * type_base."""

    def _single_edge_graph(self, etype: str, certainty: str) -> dict:
        return {
            "nodes": [_node("A"), _node("B")],
            "edges": [_edge("A", "B", etype, certainty)],
        }

    _TYPE_BASE = {
        "compute_commitment": 3,
        "equity_stake": 2,
        "voting_power": 2,
        "subsidiary": 2,
        "customer": 1,
        "infra_partner": 1,
    }
    _CERTAINTY_W = {"filed": 1.0, "reported": 0.7, "rumored": 0.3}

    @pytest.mark.parametrize("etype,tb", list(_TYPE_BASE.items()))
    @pytest.mark.parametrize("cert,cw", list(_CERTAINTY_W.items()))
    def test_base_weight_at_zero_shock(self, etype, tb, cert, cw):
        """Zero shock → stress_score=1 → stressed_weight == cw * tb."""
        g = self._single_edge_graph(etype, cert)
        result = ms.stress_graph(g, _LIVE_SNAPSHOT)
        e = result["edges"][0]
        expected = cw * tb
        assert e["stressed_weight"] == pytest.approx(expected, abs=1e-9)

    def test_stressed_weight_proportional_to_stress_score(self):
        """stressed_weight = base_weight * stress_score (not independent)."""
        g = self._single_edge_graph("compute_commitment", "filed")
        result = ms.stress_graph(g, _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        e = result["edges"][0]
        # For non-neocloud, non-hyperscaler src, beta for compute_commitment is "others" (small)
        # Just verify proportionality: stressed_weight == base_weight_at_stress1 * stress_score
        base = 1.0 * 3  # filed=1.0, compute_commitment=3
        assert e["stressed_weight"] == pytest.approx(base * e["stress_score"], abs=1e-9)


# ---------------------------------------------------------------------------
# Edge-type default/fallback betas
# ---------------------------------------------------------------------------

class TestDefaultBetas:
    """Other edge types (customer, infra_partner, voting_power, subsidiary) use small betas."""

    def test_customer_edge_minimal_rate_stress(self):
        """customer beta=0.02 per +100bps DFF → +200bps → stress=1-0.04=0.96."""
        g = {
            "nodes": [_node("AAPL", "L4-app"), _node("NVDA", "L1-chips")],
            "edges": [_edge("AAPL", "NVDA", "customer", "filed")],
        }
        result = ms.stress_graph(g, _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        e = result["edges"][0]
        assert e["stress_score"] == pytest.approx(1.0 - 0.02 * 2, abs=1e-6)

    def test_infra_partner_minimal_stress(self):
        """infra_partner beta=0.01 per +100bps → +200bps → stress=1-0.02=0.98."""
        g = {
            "nodes": [_node("GEV", "L0-energy"), _node("AMZN", "L2-infra")],
            "edges": [_edge("GEV", "AMZN", "infra_partner", "filed")],
        }
        result = ms.stress_graph(g, _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        e = result["edges"][0]
        assert e["stress_score"] == pytest.approx(1.0 - 0.01 * 2, abs=1e-6)

    def test_nbis_is_neocloud(self):
        """NBIS is a neocloud src: beta=0.12."""
        g = {
            "nodes": [_node("NBIS", "L2-infra"), _node("META", "L2-infra")],
            "edges": [_edge("NBIS", "META", "compute_commitment", "filed")],
        }
        result = ms.stress_graph(g, _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        e = result["edges"][0]
        assert e["stress_score"] == pytest.approx(0.76, abs=1e-6)

    def test_iren_is_neocloud(self):
        """IREN is a neocloud src: beta=0.12."""
        g = {
            "nodes": [_node("IREN", "L2-infra"), _node("META", "L2-infra")],
            "edges": [_edge("IREN", "META", "compute_commitment", "filed")],
        }
        result = ms.stress_graph(g, _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        e = result["edges"][0]
        assert e["stress_score"] == pytest.approx(0.76, abs=1e-6)

    def test_amzn_is_hyperscaler(self):
        """AMZN is a hyperscaler src: beta=0.03."""
        g = {
            "nodes": [_node("AMZN", "L2-infra"), _node("NVDA", "L1-chips")],
            "edges": [_edge("AMZN", "NVDA", "compute_commitment", "filed")],
        }
        result = ms.stress_graph(g, _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        e = result["edges"][0]
        assert e["stress_score"] == pytest.approx(0.94, abs=1e-6)

    def test_googl_is_hyperscaler(self):
        """GOOGL is a hyperscaler src: beta=0.03."""
        g = {
            "nodes": [_node("GOOGL", "L2-infra"), _node("NVDA", "L1-chips")],
            "edges": [_edge("GOOGL", "NVDA", "compute_commitment", "filed")],
        }
        result = ms.stress_graph(g, _BASELINE_SNAPSHOT, _SHOCK_PLUS200BPS)
        e = result["edges"][0]
        assert e["stress_score"] == pytest.approx(0.94, abs=1e-6)

    def test_zero_shock_all_betas_give_one(self):
        """Zero shock → all edge types produce stress_score=1.0 regardless of beta."""
        for etype in ["customer", "infra_partner", "equity_stake", "compute_commitment"]:
            g = {
                "nodes": [_node("CRWV", "L2-infra"), _node("NVDA", "L1-chips")],
                "edges": [_edge("CRWV", "NVDA", etype, "filed")],
            }
            result = ms.stress_graph(g, _LIVE_SNAPSHOT)
            e = result["edges"][0]
            assert e["stress_score"] == pytest.approx(1.0, abs=1e-9), (
                f"etype={etype} got stress_score={e['stress_score']} != 1.0 with zero shock"
            )


# ---------------------------------------------------------------------------
# Ordering of edges in result aligned to input
# ---------------------------------------------------------------------------

class TestEdgeOrdering:
    """Result edges must be aligned (same order) as input graph_dict['edges']."""

    def test_multi_edge_order_preserved(self):
        g = {
            "nodes": [_node("A"), _node("B"), _node("C")],
            "edges": [
                _edge("A", "B", "customer", "filed"),
                _edge("B", "C", "equity_stake", "reported"),
                _edge("A", "C", "infra_partner", "rumored"),
            ],
        }
        result = ms.stress_graph(g, _LIVE_SNAPSHOT)
        in_edges = g["edges"]
        out_edges = result["edges"]
        for i, (ie, oe) in enumerate(zip(in_edges, out_edges)):
            assert ie["src"] == oe["src"], f"Position {i} src mismatch"
            assert ie["dst"] == oe["dst"], f"Position {i} dst mismatch"
            assert ie["type"] == oe["type"], f"Position {i} type mismatch"


# ---------------------------------------------------------------------------
# A0 regression: stale hardcoded baseline must not exist
# ---------------------------------------------------------------------------

class TestA0Regression:
    """Regression tests for the A0 stale-baseline bug."""

    def test_no_default_baselines_constant(self):
        """The module must not have a _DEFAULT_BASELINES dict with hardcoded stale rates."""
        assert not hasattr(ms, "_DEFAULT_BASELINES"), (
            "_DEFAULT_BASELINES still present; A0 fix removes hardcoded stale baselines"
        )

    def test_live_snapshot_low_dff_zero_shock_gives_one(self):
        """DFF=3.64 snapshot with no shock must give stress_score=1.0 (not inflated)."""
        g = {
            "nodes": [_node("CRWV", "L2-infra"), _node("NVDA", "L1-chips")],
            "edges": [_edge("CRWV", "NVDA", "compute_commitment", "filed")],
        }
        result = ms.stress_graph(g, _LIVE_SNAPSHOT)
        assert result["edges"][0]["stress_score"] == pytest.approx(1.0, abs=1e-9)

    def test_stress_graph_signature_has_shock_not_baselines(self):
        """stress_graph() must accept 'shock' as the third parameter (not 'baselines')."""
        import inspect
        sig = inspect.signature(ms.stress_graph)
        params = list(sig.parameters.keys())
        assert "shock" in params, f"'shock' not in signature params: {params}"
        assert "baselines" not in params, f"'baselines' still in signature params: {params}"
