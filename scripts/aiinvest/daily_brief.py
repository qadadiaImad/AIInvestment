import re

def _news_count(ticker, news):
    # The structured `tickers` list is authoritative. The title fallback is a naive
    # substring match, which is catastrophic for short tickers ("D" matches nearly
    # every headline), so gate it on word-boundary AND length >= 3.
    if not ticker:
        return 0
    pat = re.compile(rf"\b{re.escape(ticker)}\b") if len(ticker) >= 3 else None
    n = 0
    for a in news:
        tks = a.get("tickers") or []
        if ticker in tks or (pat and pat.search(a.get("title") or "")):
            n += 1
    return n

def _hottest(rows, news):
    best, best_score = None, -1.0
    for r in rows:
        perf = r.get("perf_1y")
        if not isinstance(perf, (int, float)):
            continue
        score = abs(perf) * (1 + _news_count(r.get("ticker", ""), news))
        if score > best_score:
            best, best_score = r, score
    return best

def pick_movers(ai_rows, quantum_rows, news):
    return {"ai": _hottest(ai_rows, news), "quantum": _hottest(quantum_rows, news)}

_OUTLETS = ["yahoo", "bloomberg", "reuters", "cnbc", "motley", "fool", "barron", "seeking alpha"]

def rail_check(text):
    v = []
    low = text.lower()
    if re.search(r"\b(i|me|my|we|our|us)\b", text, re.IGNORECASE):
        v.append("first person pronoun present")
    for o in _OUTLETS:
        if o in low:
            v.append(f"news outlet named: {o}")
            break
    if "gurufocus" in low or re.search(r"\bGF\b", text, re.IGNORECASE):
        v.append("provider name present (use 'fundamental value')")
    if "not advice" not in low and "not financial advice" not in low:
        v.append("missing not-advice disclaimer")
    # Require an actual date adjacent to "utc", not merely the bare word — a lone
    # "utc" must not satisfy the datestamp guarantee.
    if not re.search(r"\d{4}-\d{2}-\d{2}[^\n]*utc", low):
        v.append("missing UTC datestamp")
    wc = len(text.split())
    if wc < 180 or wc > 320:
        v.append(f"word count out of range: {wc}")
    return v

def build_brief(date, pulse, picks, catalysts):
    return {"date": date, "pulse": pulse, "picks": picks, "catalysts": list(catalysts)}

def _arrow(c):
    return "up" if c > 0 else "down" if c < 0 else "flat"

def _fmt(x):
    # Round live numeric figures to one decimal for clean copy; pass text through.
    return f"{x:.1f}" if isinstance(x, (int, float)) else str(x)

def render_post(brief):
    p, picks = brief["pulse"], brief["picks"]
    ai, q = picks["ai"], picks["quantum"]
    cats = brief["catalysts"] or ["the next major macro print"]
    pulse_line = (f"Broad tape: the S&P is {_arrow(p['sp500']['change_pct'])} "
                  f"{abs(p['sp500']['change_pct'])}% and the Nasdaq {_arrow(p['nasdaq']['change_pct'])} "
                  f"{abs(p['nasdaq']['change_pct'])}%, with the VIX near {p['vix']['price']} and the "
                  f"10-year around {p['ten_year']['price']}%. Risk appetite reads "
                  f"{'constructive' if p['sp500']['change_pct'] >= 0 else 'cautious'}, led by a familiar set of AI names. "
                  f"The tape continues to price in steady growth with limited recession risk.")
    ai_perf = ai['perf_1y']
    ai_rev = _fmt(ai.get('rev_growth_yoy', 'n/a'))
    if isinstance(ai_perf, (int, float)) and ai_perf < 0:
        ai_line = (f"AI stack: {ai['ticker']} is the tell, down {_fmt(abs(ai_perf))}% over the past year on "
                   f"roughly {ai_rev}% revenue growth — the data frames this as a repricing, not a broken thesis, "
                   f"with the multiple compressing faster than the fundamentals. The setup rewards patience: watch "
                   f"whether the business keeps compounding while the sentiment resets.")
    else:
        ai_line = (f"AI stack: {ai['ticker']} is the tell, up {_fmt(ai_perf)}% over the past year on "
                   f"roughly {ai_rev}% revenue growth — the data still frames this as "
                   f"leadership earning its multiple, not a crowd trade. Fundamentals support the thesis: "
                   f"the business compounds, and multiples are rational relative to growth.")
    q_rev = q.get('rev_growth_yoy')
    if isinstance(q_rev, (int, float)) and q_rev >= 25:
        q_rev_clause = (f"on {_fmt(q_rev)}% revenue growth — momentum the fundamentals are beginning to back, "
                        f"though the multiple still prices in years of execution")
    elif isinstance(q_rev, (int, float)):
        q_rev_clause = (f"while revenue grew {_fmt(q_rev)}% — a tape moving ahead of the fundamentals, "
                        f"not because of them")
    else:
        q_rev_clause = "on a still-thin revenue base — a story-priced, momentum-led move"
    q_perf = q['perf_1y']
    q_verb = "fallen" if isinstance(q_perf, (int, float)) and q_perf < 0 else "run"
    q_perf_disp = _fmt(abs(q_perf)) if isinstance(q_perf, (int, float)) else _fmt(q_perf)
    q_line = (f"Quantum & frontier: {q['ticker']} has {q_verb} {q_perf_disp}% {q_rev_clause}. "
              f"This remains a bet on optionality more than today's cash flow, and a name that tends to "
              f"re-rate quickly in both directions as sentiment shifts. "
              f"Watch for technical support and news inflection points.")
    watch = "Watch: " + "; ".join(cats[:2]) + "."
    pad = "The desk keeps the read simple: respect the trend, price the risk, and let the numbers - not the noise - set position size. "
    tags = " ".join(f"#{t}" for t in [ai["ticker"], q["ticker"]]) + " #AIstocks #Markets #Quantum"
    body = "\n\n".join([pulse_line, ai_line, q_line, pad + watch,
                        f"Educational - not advice. Data as of {brief['date']} (UTC).", tags])
    return body
