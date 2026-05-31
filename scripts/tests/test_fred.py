"""RED tests for the FRED helper (macro/rates/electricity-price series)."""
from aiinvest import fred


# --- URL builders ---

def test_fredgraph_csv_url_is_keyless():
    # The fredgraph.csv endpoint needs NO api key — good for quick pulls.
    assert fred.fredgraph_csv_url("DGS10") == \
        "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"


def test_observations_url_includes_key_and_json():
    url = fred.observations_url("APU000072610", api_key="KEY123")
    assert "series_id=APU000072610" in url
    assert "api_key=KEY123" in url
    assert "file_type=json" in url


# --- parse_fred_csv(): FRED marks missing values with "." -> must become None ---

CSV = "observation_date,DGS10\n2024-01-01,.\n2024-01-02,3.95\n2024-01-03,4.01\n"


def test_parse_fred_csv_returns_date_value_rows():
    rows = fred.parse_fred_csv(CSV)
    assert len(rows) == 3
    assert rows[1] == {"date": "2024-01-02", "value": 3.95}


def test_parse_fred_csv_maps_dot_to_none_not_dirty_string():
    rows = fred.parse_fred_csv(CSV)
    assert rows[0]["value"] is None


# --- parse_observations(): official JSON API shape ---

OBS = {"observations": [
    {"date": "2024-01-01", "value": "."},
    {"date": "2024-01-02", "value": "3.95"},
]}


def test_parse_observations_parses_values_and_handles_missing():
    rows = fred.parse_observations(OBS)
    assert rows[0]["value"] is None
    assert rows[1]["value"] == 3.95
