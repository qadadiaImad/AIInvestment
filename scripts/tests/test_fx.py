import pytest

from aiinvest import fx

RATES = {"CNY": 6.7, "HKD": 7.8, "JPY": 157.0, "GBP": 0.75, "EUR": 0.87}


def test_usd_passthrough():
    assert fx.to_usd(100.0, "USD", RATES) == 100.0
    assert fx.to_usd(None, "USD", RATES) is None


def test_cny_conversion():
    assert fx.to_usd(67.0, "CNY", RATES) == pytest.approx(10.0)


def test_pence_are_normalised_to_pounds_before_conversion():
    # 75 pence = 0.75 GBP = 1 USD
    assert fx.to_usd(75.0, "GBX", RATES) == pytest.approx(1.0)
    assert fx.normalise_currency(250.0, "GBX") == (2.5, "GBP")


def test_unknown_currency_yields_none():
    assert fx.to_usd(5.0, "XYZ", RATES) is None
    assert fx.to_usd(5.0, "CNY", {}) is None
