"""FX rates for converting foreign-listed market caps and prices to USD.

REST-first: ECB reference rates via the keyless Frankfurter API (verified live
2026-09-22: USD -> CNY 6.7001, HKD 7.8434, JPY 157.18, ...). Pure conversion helpers are
unit-tested with injected rates; `fetch_rates()` is the thin network layer.

GBX (pence) is a TradingView quirk for LSE quotes: prices come in pence while the
fundamental currency is GBP. `normalise_currency()` handles it.
"""
from __future__ import annotations

import datetime

import requests

FRANKFURTER = "https://api.frankfurter.app/latest"
CURRENCIES = ("CNY", "HKD", "JPY", "AUD", "CAD", "GBP", "KRW", "EUR")


def normalise_currency(amount, currency):
    """Map pence (GBX) to pounds; everything else passes through unchanged."""
    if amount is None:
        return None, currency
    if currency == "GBX":
        return amount / 100.0, "GBP"
    return amount, currency


def to_usd(amount, currency, rates):
    """Convert `amount` in `currency` to USD using {ccy: units-per-USD}. None if unknown."""
    if amount is None:
        return None
    amount, currency = normalise_currency(amount, currency)
    if currency in (None, "USD"):
        return amount
    rate = (rates or {}).get(currency)
    if not rate:
        return None
    return amount / rate


def fetch_rates(base="USD", symbols=CURRENCIES, timeout=20):
    """{ccy: units per base} plus provenance stamps; raises on network failure."""
    r = requests.get(FRANKFURTER, params={"from": base, "to": ",".join(symbols)}, timeout=timeout)
    r.raise_for_status()
    body = r.json()
    return {
        "base": base,
        "rates": body["rates"],
        "as_of": body.get("date"),
        "source": "frankfurter.app (ECB reference rates)",
        "source_url": r.url,
        "source_class": "api",
        "retrieved_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
