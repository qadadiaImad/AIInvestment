from aiinvest.halal_lint import lint_halal_script, lint_visceral, lint_editorial

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


def test_visceral_rejects_capital_false_anchor():
    bad = ["58% of institutional capital is allocated."]
    assert lint_visceral(bad)


def test_visceral_rejects_unlimited_false_anchor():
    bad = ["Revenue could grow 200% with unlimited upside."]
    assert lint_visceral(bad)


def test_visceral_accepts_real_cap_word():
    assert lint_visceral(["Debt sits at 14%, under the 30% cap."]) == []


def test_visceral_accepts_per_cent_with_limit():
    ok = ["56 per cent of revenue is flagged, against a 30 per cent limit."]
    assert lint_visceral(ok) == []


def test_visceral_rejects_per_cent_without_anchor():
    bad = ["56 per cent of revenue comes from mining."]
    assert lint_visceral(bad)


# --- lint_editorial: bans buy/sell-adjacent judgment words -------------------

def test_editorial_flags_dangerous_leverage():
    errs = lint_editorial(["This is dangerous leverage."])
    assert errs and "dangerous" in errs[0].lower()


def test_editorial_flags_debt_trap():
    errs = lint_editorial(["It's a debt trap waiting to happen."])
    assert errs and "trap" in errs[0].lower()


def test_editorial_flags_each_banned_word():
    words = ("dangerous", "danger", "trap", "too much", "overvalued", "avoid",
              "risky", "terrible", "crash", "plummet", "soar", "guaranteed")
    for w in words:
        errs = lint_editorial([f"Some line with {w} in it."])
        assert errs, f"{w!r} should be flagged"


def test_editorial_is_word_bounded_not_substring():
    # "guarantee" (no trailing d) must NOT trip on the "guaranteed" entry;
    # "avoidance" must not trip on "avoid".
    assert lint_editorial(["No guarantee is implied here."]) == []
    assert lint_editorial(["Standard avoidance language applies."]) == []


def test_editorial_case_insensitive():
    errs = lint_editorial(["DANGEROUS territory."])
    assert errs


def test_editorial_passes_factual_extreme_wkey_line():
    line = ("It owes 5.6 times what the whole company is worth — the "
            "screen's limit is 30%, and it isn't close.")
    assert lint_editorial([line]) == []


def test_editorial_one_violation_per_line_even_with_two_banned_words():
    errs = lint_editorial(["This dangerous, risky bet."])
    assert len(errs) == 1


# --- review fix: bounded inflection stems (soared/crashed/plummeted/dangerously) --

def test_editorial_flags_soared_and_soaring():
    assert lint_editorial(["Shares soared today."])
    assert lint_editorial(["Shares are soaring this week."])


def test_editorial_flags_crashed_and_crashing():
    assert lint_editorial(["The stock crashed hard."])
    assert lint_editorial(["The stock is crashing right now."])


def test_editorial_flags_plummeted_and_plummeting():
    assert lint_editorial(["Revenue plummeted last quarter."])
    assert lint_editorial(["Revenue is plummeting."])


def test_editorial_flags_dangerously():
    errs = lint_editorial(["This trades dangerously close to the limit."])
    assert errs and "danger" in errs[0].lower()


def test_editorial_does_not_over_ban_risk_or_avoidance():
    # 'risky' stays banned (exact); 'risk' itself is a legitimate finance word
    # and must NOT be caught by stemming.
    assert lint_editorial(["This carries risk."]) == []
    assert lint_editorial(["Risk management is disciplined here."]) == []
    assert lint_editorial(["Standard avoidance language applies."]) == []
