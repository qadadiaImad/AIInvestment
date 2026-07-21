from aiinvest.halal_lint import lint_halal_script

CARD = {"standards_rows": [{"name": "AAOIFI", "ratio": "21.0%", "threshold": "30.0%", "margin": "+9.0pt"}],
        "business_line": "Business activity: crypto-mining — 38.2% impermissible",
        "purification_line": "Purification (estimated): ~$0.13/share"}
GOOD = ("TeraWulf... thirty-eight point two percent of revenue is mining. "
        "The screen flags it for review. Educational, not financial or religious advice.")

def test_clean_script_passes():
    assert lint_halal_script(GOOD, CARD) == []

def test_is_halal_claim_rejected():
    errs = lint_halal_script("WULF is halal. Educational, not financial or religious advice.", CARD)
    assert any("is halal" in e for e in errs)

def test_is_haram_claim_rejected():
    errs = lint_halal_script("This stock is haram. Educational, not financial or religious advice.", CARD)
    assert any("is haram" in e for e in errs)

def test_missing_disclaimer_rejected():
    errs = lint_halal_script("Thirty-eight point two percent is mining revenue.", CARD)
    assert any("disclaimer" in e.lower() for e in errs)

def test_no_card_number_rejected():
    errs = lint_halal_script("A company did things. Educational, not financial or religious advice.", CARD)
    assert any("number" in e.lower() for e in errs)
