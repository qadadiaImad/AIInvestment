"""FRED (St. Louis Fed) helper — macro, rates, electricity prices (Part D energy).

Two paths:
- `fredgraph_csv_url` / `fetch_csv`  → KEYLESS, quick series download (CSV).
- `observations_url` / `fetch_observations` → official JSON API (needs free api_key in .env).

FRED encodes missing observations as ``"."`` — exactly the dirty value GuruTrade stored as
junk. We route every value through `schema.parse_number`, so missing -> None.

Useful series for this project:
  DGS10  10-Year Treasury · DFF Fed Funds · INDPRO Industrial Production
  APU000072610  Avg price, electricity per kWh (US city) · CUUR0000SEHF01 CPI electricity
"""
from __future__ import annotations

from . import schema

FREDGRAPH_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
OBSERVATIONS = ("https://api.stlouisfed.org/fred/series/observations"
                "?series_id={series_id}&api_key={api_key}&file_type=json")


def fredgraph_csv_url(series_id):
    return FREDGRAPH_CSV.format(series_id=series_id)


def observations_url(series_id, api_key, extra=""):
    return OBSERVATIONS.format(series_id=series_id, api_key=api_key) + extra


def parse_fred_csv(text):
    """Parse fredgraph CSV (header + DATE,VALUE rows). Missing ('.') -> None."""
    rows = []
    lines = [ln for ln in text.splitlines() if ln.strip()]
    for ln in lines[1:]:  # skip header
        parts = ln.split(",")
        if len(parts) < 2:
            continue
        rows.append({"date": parts[0].strip(), "value": schema.parse_number(parts[1])})
    return rows


def parse_observations(payload):
    """Parse official JSON API observations. Missing ('.') -> None."""
    return [
        {"date": o.get("date"), "value": schema.parse_number(o.get("value"))}
        for o in payload.get("observations", [])
    ]


def _get_text(url, timeout=20, session=None):
    import requests
    http = session or requests
    resp = http.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def fetch_csv(series_id, session=None):
    """Keyless: download a series via fredgraph.csv and parse it."""
    return parse_fred_csv(_get_text(fredgraph_csv_url(series_id), session=session))


def fetch_observations(series_id, api_key, session=None):
    """Official JSON API (needs a free FRED api_key)."""
    import json
    import requests
    http = session or requests
    resp = http.get(observations_url(series_id, api_key), timeout=20)
    resp.raise_for_status()
    return parse_observations(json.loads(resp.text))
