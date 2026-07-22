from aiinvest.halal_lint import lint_halal_script, lint_visceral

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


# --- Regression: FINDING 1 — qualified/negated verdict claims must not bypass the linter ---

def test_qualified_totally_halal_rejected():
    errs = lint_halal_script(
        "WULF is totally halal. Educational, not financial or religious advice.", CARD)
    assert any("halal" in e.lower() or "haram" in e.lower() for e in errs)


def test_qualified_definitely_haram_rejected():
    errs = lint_halal_script(
        "This stock is definitely haram. Educational, not financial or religious advice.", CARD)
    assert any("halal" in e.lower() or "haram" in e.lower() for e in errs)


def test_negated_is_not_halal_rejected():
    errs = lint_halal_script(
        "The screen shows this is not halal. Educational, not financial or religious advice.", CARD)
    assert any("halal" in e.lower() or "haram" in e.lower() for e in errs)


def test_possessive_apostrophe_s_halal_rejected():
    errs = lint_halal_script(
        "WULF's halal, according to the numbers. Educational, not financial or religious advice.", CARD)
    assert any("halal" in e.lower() or "haram" in e.lower() for e in errs)


# --- Regression: FINDING 2 — number-anchor must not accept invented figures ---

def test_spoken_single_digit_word_nine_does_not_anchor():
    errs = lint_halal_script(
        "The board raised nine concerns regarding governance during the review. "
        "Educational, not financial or religious advice.", CARD)
    assert any("number" in e.lower() for e in errs)


def test_spoken_single_digit_word_zero_does_not_anchor():
    errs = lint_halal_script(
        "The company has zero debt covenant breaches. "
        "Educational, not financial or religious advice.", CARD)
    assert any("number" in e.lower() for e in errs)


def test_raw_number_substring_does_not_anchor():
    errs = lint_halal_script(
        "Metric came in at 19.05 percent. "
        "Educational, not financial or religious advice.", CARD)
    assert any("number" in e.lower() for e in errs)


# --- Regression: legitimate qualified-screen phrasing must stay CLEAN ---

def test_legit_passes_the_screen_phrasing_stays_clean():
    good = (
        "TeraWulf's crypto-mining revenue is thirty-eight point two percent, which "
        "passes the AAOIFI screen given the margin. "
        "Educational, not financial or religious advice.")
    assert lint_halal_script(good, CARD) == []


# --- Regression: re-review round 2 — contracted negation + curly apostrophe ---

def test_contracted_negation_isnt_halal_rejected():
    errs = lint_halal_script(
        "The screen shows this isn't halal. Educational, not financial or religious advice.", CARD)
    assert any("halal" in e.lower() or "haram" in e.lower() for e in errs)


def test_curly_apostrophe_possessive_halal_rejected():
    errs = lint_halal_script(
        "WULF’s halal, according to the numbers. Educational, not financial or religious advice.", CARD)
    assert any("halal" in e.lower() or "haram" in e.lower() for e in errs)


# --- lint_visceral: every spoken ratio needs a money analogy or limit comparison ---

def test_visceral_rejects_bare_ratio():
    bad = ["The AAOIFI debt ratio comes in at 56.9%."]
    errs = lint_visceral(bad)
    assert errs


def test_visceral_accepts_money_analogy():
    ok = ["About 57 percent — that's $57 of every $100 — is borrowed, against a $30 limit."]
    assert lint_visceral(ok) == []


def test_visceral_accepts_limit_comparison():
    assert lint_visceral(["Debt is 14.0% against a 30% cap."]) == []


def test_visceral_ignores_lines_without_percent():
    assert lint_visceral(["Verdict: pass on the halal screen."]) == []
