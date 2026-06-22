"""RED tests for GuruFocus extraction + gate detection (Mode-B Playwright fetch is live)."""
from aiinvest import gurufocus as gf


# Representative innerText from the live /valuation page (GF Value $334.32, value-trap verdict).
PAGE = ("NVIDIA Corp (NVDA) $ 211.14  GF Value $334.32  Possible Value Trap, Think Twice  "
        "PE Ratio 32.33  Market Cap $5.11T")


def test_extract_gf_value_as_stamped_envelope():
    m = gf.extract_metrics(PAGE, "https://www.gurufocus.com/stock/NVDA/valuation", "2026-05-30T12:00:00Z")
    env = m["gf_value"]
    assert env["value"] == 334.32
    assert env["unit"] == "usd"
    assert env["source"] == "gurufocus"
    assert env["source_class"] == "innertext-regex"
    assert env["dirty"] is False


def test_extract_verdict_text():
    m = gf.extract_metrics(PAGE, "url", "t")
    assert m["valuation_verdict"]["value"] == "Possible Value Trap"


def test_absent_metric_is_none_and_not_dirty():
    # GF Score isn't on this page text -> genuinely absent, not an extraction failure.
    m = gf.extract_metrics(PAGE, "url", "t")
    assert m["gf_score"]["value"] is None
    assert m["gf_score"]["dirty"] is False


# --- detect_gate(): decide whether to rotate the instance ---

def test_detect_gate_on_paywall_text():
    res = gf.detect_gate("Subscribe to Premium to unlock GF Value", status_codes=[200])
    assert res["gated"] is True
    assert "subscribe to premium" in res["reasons"][0].lower()


def test_detect_gate_on_http_429():
    res = gf.detect_gate("normal page", status_codes=[200, 429])
    assert res["gated"] is True


def test_no_gate_on_clean_page():
    res = gf.detect_gate(PAGE, status_codes=[200])
    assert res["gated"] is False


# --- to_record(): adapt extraction into a merge-ready record ---

def test_to_record_wraps_metrics_for_merge():
    rec = gf.to_record(PAGE, "NVDA", "https://www.gurufocus.com/stock/NVDA/valuation", "2026-05-30T12:00:00Z")
    assert rec["symbol"] == "NVDA"
    assert rec["metrics"]["gf_value"]["value"] == 334.32
