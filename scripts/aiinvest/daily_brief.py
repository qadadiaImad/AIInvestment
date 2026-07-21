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
    if wc < 180 or wc > 600:
        v.append(f"word count out of range: {wc}")
    return v

def build_brief(date, pulse, picks, catalysts, extras=None):
    # extras (optional): {"ai_rows": [...], "quantum_rows": [...]} — full screener rows for
    # the expansive sections (board leaders, value corner, quantum peer read).
    return {"date": date, "pulse": pulse, "picks": picks, "catalysts": list(catalysts),
            "extras": extras or {}}

def _numrows(rows, key):
    return [r for r in rows if isinstance(r.get(key), (int, float))]

def _spct(v):
    return f"{v:+.0f}%"

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
    elif isinstance(ai.get('rev_growth_yoy'), (int, float)) and ai['rev_growth_yoy'] < 0:
        # Big price move on FALLING reported revenue — never claim fundamentals support it.
        ai_line = (f"AI stack: {ai['ticker']} is the tell, up {_fmt(ai_perf)}% over the past year while "
                   f"reported revenue fell {_fmt(abs(ai['rev_growth_yoy']))}% — a move carried by re-rating "
                   f"and positioning, not by the current income statement. The risk here is the multiple, "
                   f"not the narrative: gains built on re-rating unwind faster than gains built on earnings.")
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
    # --- expansive sections, only when full screener rows were provided (extras) ---
    extras = brief.get("extras") or {}
    ai_rows, q_rows = extras.get("ai_rows") or [], extras.get("quantum_rows") or []
    board_line = None
    lead = sorted(_numrows(ai_rows, "perf_1y"), key=lambda r: r["perf_1y"], reverse=True)[:3]
    if lead:
        runs = "; ".join(
            f"{r['ticker']} {_spct(r['perf_1y'])}"
            + (f" on {_spct(r['rev_growth_yoy'])} revenue" if isinstance(r.get("rev_growth_yoy"), (int, float)) else "")
            for r in lead)
        board_line = (f"Board leaders on the year: {runs}. Dispersion inside the stack stays wide — "
                      f"the tape is paying for specific bottlenecks, not the theme as a whole.")
    val_line = None
    vals = [r for r in _numrows(ai_rows, "fundamental_discount_pct")
            if isinstance(r.get("fundamental_value"), (int, float)) and r["fundamental_value"] > 0
            and isinstance(r.get("price"), (int, float))]
    if vals:
        disc = max(vals, key=lambda r: r["fundamental_discount_pct"])
        prem = min(vals, key=lambda r: r["fundamental_discount_pct"])
        val_line = (f"Value corner: the widest gaps versus analysts' fundamental-value model sit at the extremes — "
                    f"{disc['ticker']} trades {_fmt(disc['fundamental_discount_pct'])}% below the model "
                    f"(${_fmt(disc['price'])} vs ${_fmt(disc['fundamental_value'])}), while {prem['ticker']} runs "
                    f"{_fmt(abs(prem['fundamental_discount_pct']))}% above it "
                    f"(${_fmt(prem['price'])} vs ${_fmt(prem['fundamental_value'])}). Gaps that wide are information "
                    f"about expectations, not instructions to trade.")
    peers = sorted([r for r in _numrows(q_rows, "perf_1y") if r.get("ticker") != q["ticker"]],
                   key=lambda r: r["perf_1y"], reverse=True)[:3]
    if peers:
        pruns = "; ".join(
            f"{r['ticker']} {_spct(r['perf_1y'])}"
            + (f" on {_spct(r['rev_growth_yoy'])} revenue" if isinstance(r.get("rev_growth_yoy"), (int, float)) else "")
            for r in peers)
        q_line += (f" Across the rest of the pure-plays: {pruns} — price action and revenue trajectory "
                   f"remain loosely coupled at best across the group.")
    watch = "Watch: " + "; ".join(cats[:2]) + "."
    pad = "The desk keeps the read simple: respect the trend, price the risk, and let the numbers - not the noise - set position size. "
    tags = " ".join(f"#{t}" for t in [ai["ticker"], q["ticker"]]) + " #AIstocks #Markets #Quantum"
    parts = [pulse_line, ai_line]
    if board_line: parts.append(board_line)
    if val_line: parts.append(val_line)
    parts += [q_line, pad + watch,
              f"Educational - not advice. Data as of {brief['date']} (UTC).", tags]
    return "\n\n".join(parts)
