"""RED tests for the Part D constraint knowledge module."""
from aiinvest import constraints as ct


def test_for_node_returns_layer_default():
    rec = ct.for_node("L0-energy", "NRG")
    assert "turbine" in rec["physical_bottleneck"].lower() or "grid" in rec["physical_bottleneck"].lower()
    assert rec["regulatory_bottleneck"]
    assert rec["lead_time_note"]


def test_record_always_has_three_keys():
    rec = ct.for_node("L4-application", "PLTR")
    assert set(rec.keys()) >= {"physical_bottleneck", "regulatory_bottleneck", "lead_time_note"}


def test_name_override_beats_layer_default():
    # ASML is L1 but its specific bottleneck is EUV sole-supply, not generic packaging.
    rec = ct.for_node("L1-chips", "ASML")
    assert "euv" in rec["physical_bottleneck"].lower()


def test_smr_names_flagged_pre_commercial():
    rec = ct.for_node("L0-energy", "OKLO")
    assert "pre-commercial" in rec["lead_time_note"].lower() or "licensing" in rec["regulatory_bottleneck"].lower()


def test_unknown_layer_returns_record_with_keys():
    rec = ct.for_node("L9-bogus", "ZZZZ")
    assert set(rec.keys()) >= {"physical_bottleneck", "regulatory_bottleneck", "lead_time_note"}
