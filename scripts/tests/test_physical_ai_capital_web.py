from aiinvest import physical_ai_capital_web as pcw


def test_graph_validates():
    g = pcw.build_graph()
    assert pcw.validate(g) == []
    assert g["edges"], "seed edges must exist"


def test_every_edge_cites_a_url_and_a_date():
    for e in pcw.EDGES:
        assert e["source_url"].startswith("https://"), e
        assert e["as_of"] and e["retrieved_at"], e
        assert e["certainty"] in {"filed", "reported", "rumored"}


def test_mp_has_dod_investor():
    g = pcw.build_graph()
    assert "DOD" in pcw.investors_of(g, "MP")
