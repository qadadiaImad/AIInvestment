from aiinvest.daily_brief import rail_check

CLEAN = ("Risk-on tape today. Chips led on the data. Educational - not advice. "
         "Data as of 2026-07-02 21:00 UTC. " + ("word " * 190))

def test_clean_passes():
    assert rail_check(CLEAN) == []

def test_flags_first_person_outlet_provider_and_missing_disclaimer():
    bad = "I think Yahoo says GuruFocus value is high. " + ("word " * 190)
    v = rail_check(bad)
    assert any("first person" in x for x in v)
    assert any("outlet" in x for x in v)
    assert any("provider" in x for x in v)
    assert any("disclaimer" in x for x in v)
