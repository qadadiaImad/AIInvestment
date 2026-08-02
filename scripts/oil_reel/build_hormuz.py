"""Build the Hormuz reel fixture from real Brent bars.

Python owns every number the reel shows (CLAUDE.md 10.1). The composition
receives a finished fixture and renders it; it never computes a price, a stop,
or a hit rate of its own, so the chart and the caption cannot disagree.

    python scripts/oil_reel/build_hormuz.py

Reads   data/oil/brent_1d.json          (provenance-stamped Yahoo pull)
Writes  remotion/src/fixtures/oil_reel/hormuz.json
"""
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from oil_reel.hormuz import (  # noqa: E402
    base_rate,
    crisis_split,
    find_inside_bar_breakout,
    iter_inside_bar_breakouts,
    resolve_trade,
)

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "data", "oil", "brent_1d.json")
OUT = os.path.join(REPO, "remotion", "src", "fixtures", "oil_reel", "hormuz.json")

# The window the camera flies over. Starts quiet enough that the shock reads as
# a break from something, ends late enough that the round trip is undeniable.
WIN_FROM = "2026-02-02"
WIN_TO = "2026-07-31"

# The shock. Dated from reporting, never from memory: US and Israeli military
# operations against Iran began Saturday 2026-02-28, with the market shut, so
# Monday 2026-03-02 was the first session that could price it.
SHOCK_DATE = "2026-02-28"
FIRST_SESSION = "2026-03-02"

SOURCES = {
    "bars": "Yahoo Finance chart API — BZ=F (Brent front-month), daily",
    "chokepoint": (
        "U.S. EIA, World Oil Transit Chokepoints (updated 2026-03-03): "
        "20.9 million b/d transited Hormuz in H1 2025, ~20% of global "
        "petroleum liquids consumption"
    ),
    "shock": (
        "Reported: US and Israeli military operations against Iran began "
        "2026-02-28; Brent's first session after was Monday 2026-03-02"
    ),
}


def main():
    raw = json.load(open(SRC))
    all_bars = raw["bars"]
    win = [b for b in all_bars if WIN_FROM <= b["d"] <= WIN_TO]
    if not win:
        raise SystemExit(f"no bars in {WIN_FROM}..{WIN_TO}")

    idx = {b["d"]: i for i, b in enumerate(win)}
    if FIRST_SESSION not in idx:
        raise SystemExit(f"{FIRST_SESSION} is not a trading day in the window")
    gap_i = idx[FIRST_SESSION]

    # Find the pattern the way a trader would: only AFTER the shock, and take
    # the first one that qualifies. No shopping the window for a better one.
    seq = find_inside_bar_breakout(win[gap_i:])
    if seq is None:
        raise SystemExit("UNMATCHED — no inside-bar breakout after the shock")
    seq = {k: v + gap_i for k, v in seq.items()}

    trade = resolve_trade(win, seq["mother"], seq["inside"], seq["trigger"], rr=2.0, horizon=12)
    if trade is None:
        raise SystemExit("UNMATCHED — the pattern fired but the trade is untradeable")

    # The honest denominator: the same definition over the whole 2y series,
    # not just the window the story happens to be about.
    rate = base_rate(all_bars, rr=2.0, horizon=12)

    # The claim that the crisis is the edge, computed rather than asserted:
    # fires within 10 sessions of a >=6% day vs everything else.
    split = crisis_split(all_bars, rr=2.0, horizon=12, shock=0.06, within=10)

    # The CONFIRMING fire: the pattern after a DIFFERENT crisis episode, found
    # by the scanner, never picked by eye. "Different episode" = its shock day
    # sits >=30 sessions past the original gap, so the March aftershocks don't
    # count as confirmation of March. Resolved either way — if the second
    # crisis fire had lost, the reel would show the loss.
    win_shock_idx = [
        i for i in range(1, len(win))
        if abs(win[i]["c"] / win[i - 1]["c"] - 1) >= 0.06
    ]
    july = None
    for s2 in iter_inside_bar_breakouts(win):
        near = [k for k in win_shock_idx if 0 < s2["trigger"] - k <= 10 and k >= gap_i + 30]
        if not near:
            continue
        t2 = resolve_trade(win, s2["mother"], s2["inside"], s2["trigger"], rr=2.0, horizon=12)
        if t2 is None or t2["outcome"] == "open":
            continue
        shock_i = max(near)
        july = {
            **{k: s2[k] for k in ("mother", "inside", "trigger")},
            "triggerDate": win[s2["trigger"]]["d"],
            "shockIdx": shock_i,
            "shockDate": win[shock_i]["d"],
            "shockPct": round((win[shock_i]["c"] / win[shock_i - 1]["c"] - 1) * 100, 1),
            "sessionsAfter": s2["trigger"] - shock_i,
            **{k: t2[k] for k in ("entry", "stop", "target", "outcome", "tpAt")},
            "tpBar": s2["trigger"] + t2["tpAt"] if t2["tpAt"] else None,
            "tpDate": win[s2["trigger"] + t2["tpAt"]]["d"] if t2["tpAt"] else None,
        }
        break

    # What the shock actually did to the tape, measured not asserted.
    prev = win[gap_i - 1]
    gap_bar = win[gap_i]
    peak = max(win, key=lambda b: b["h"])
    trough_after = min((b for b in win if b["d"] > peak["d"]), key=lambda b: b["l"])

    tp_bar = seq["trigger"] + trade["tpAt"] if trade["tpAt"] else None

    fixture = {
        "title": "WHAT MOVES THE PRICE OF OIL",
        "symbol": raw["symbol"],
        "instrument": "Brent crude, front-month futures",
        "bars": win,
        "shock": {
            "date": SHOCK_DATE,
            "weekday": datetime.date.fromisoformat(SHOCK_DATE).strftime("%A"),
            "firstSession": FIRST_SESSION,
            "firstSessionIndex": gap_i,
            "prevClose": prev["c"],
            "gapOpen": gap_bar["o"],
            "gapPts": round(gap_bar["o"] - prev["c"], 2),
            "gapPct": round((gap_bar["o"] / prev["c"] - 1) * 100, 1),
            # the trap: how far above the close the first session ran
            "spikeHigh": gap_bar["h"],
            "spikeGiveback": round(gap_bar["h"] - gap_bar["c"], 2),
        },
        "pattern": {
            "name": "INSIDE BAR BREAKOUT",
            "mother": seq["mother"],
            "inside": seq["inside"],
            "trigger": seq["trigger"],
            "motherDate": win[seq["mother"]]["d"],
            "insideDate": win[seq["inside"]]["d"],
            "triggerDate": win[seq["trigger"]]["d"],
            "motherHigh": win[seq["mother"]]["h"],
            "insideLow": win[seq["inside"]]["l"],
        },
        "trade": {**trade, "tpBar": tp_bar, "tpDate": win[tp_bar]["d"] if tp_bar else None},
        "baseRate": rate,
        "split": split,
        "july": july,
        "aftermath": {
            "peakDate": peak["d"],
            "peakHigh": peak["h"],
            "troughDate": trough_after["d"],
            "troughLow": trough_after["l"],
            "lastDate": win[-1]["d"],
            "lastClose": win[-1]["c"],
        },
        "provenance": {
            "source": raw["source"],
            "endpoint": raw["endpoint"],
            "source_class": raw["source_class"],
            "bars_retrieved_at": raw["retrieved_at"],
            "built_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "notes": SOURCES,
        },
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(fixture, open(OUT, "w"), indent=1)

    s, p, t = fixture["shock"], fixture["pattern"], fixture["trade"]
    print(f"window   {win[0]['d']} .. {win[-1]['d']}  ({len(win)} bars)")
    print(f"shock    {s['date']} ({s['weekday']}) -> first session {s['firstSession']}")
    print(f"         gap {s['gapPts']:+.2f} ({s['gapPct']:+.1f}%), spiked to {s['spikeHigh']}, "
          f"gave back {s['spikeGiveback']}")
    print(f"pattern  {p['name']}  {p['motherDate']} / {p['insideDate']} / {p['triggerDate']}")
    print(f"trade    entry {t['entry']}  stop {t['stop']}  target {t['target']}  "
          f"-> {t['outcome'].upper()}" + (f" on {t['tpDate']}" if t["tpDate"] else ""))
    print(f"base     {rate['wins']}/{rate['n']} = {rate['pct']}% over the full 2y series")
    print(f"split    quiet {split['quiet']['wins']}/{split['quiet']['n']}  "
          f"crisis {split['crisis']['wins']}/{split['crisis']['n']}")
    if july:
        print(f"july     shock {july['shockDate']} ({july['shockPct']:+.1f}%) -> "
              f"trigger {july['triggerDate']} (+{july['sessionsAfter']} sessions) "
              f"-> {july['outcome'].upper()}"
              + (f" on {july['tpDate']}" if july["tpDate"] else ""))
    else:
        print("july     NO confirming conditioned fire in the window")
    print(f"after    peak {fixture['aftermath']['peakHigh']} on {fixture['aftermath']['peakDate']}"
          f" -> {fixture['aftermath']['troughLow']} on {fixture['aftermath']['troughDate']}")
    print(f"-> {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
