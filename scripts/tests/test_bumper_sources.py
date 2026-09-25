from bumper import sources as s


def _fact(start, end, val, fp=None):
    d = {"start": start, "end": end, "val": val}
    if fp:
        d["fp"] = fp
    return d


def test_quarterly_series_keeps_quarters_and_derives_q4():
    facts = {"facts": {"us-gaap": {
        "Revenues": {"units": {"USD": [
            _fact("2023-01-01", "2023-03-31", 10),
            _fact("2023-04-01", "2023-06-30", 12),
            _fact("2023-01-01", "2023-06-30", 22),   # 6M YTD, must be dropped
            _fact("2023-07-01", "2023-09-30", 15),
            _fact("2023-01-01", "2023-12-31", 60, fp="FY"),  # FY -> Q4 = 60-37 = 23
        ]}},
        "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [
            {"end": "2023-06-30", "val": 100}, {"end": "2023-12-31", "val": 90}]}},
    }}}
    q = s.quarterly_series(facts)
    assert q["revenue"] == [("2023-03-31", 10), ("2023-06-30", 12), ("2023-09-30", 15), ("2023-12-31", 23)]
    assert q["cash"] == [("2023-06-30", 100), ("2023-12-31", 90)]
    assert q["rnd"] == []


def test_concept_fallback_order():
    facts = {"facts": {"us-gaap": {
        "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [
            _fact("2024-01-01", "2024-03-31", 5)]}}}}}
    assert s.quarterly_series(facts)["revenue"] == [("2024-03-31", 5)]
