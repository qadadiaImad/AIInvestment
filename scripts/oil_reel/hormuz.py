"""Pattern + trade maths for the Hormuz oil reel.

Every number the reel shows comes from this module, and the module never sees
the story it is being used to tell. The scanner FINDS a bar that already
satisfies the definition; it never nudges a definition to fit a chart that
looked good. A window with no qualifying sequence returns None and the reel
has to find another window.

The pattern: **inside-bar breakout.**

    mother    a wide bar. In a shock it is the bar that prints the panic range.
    inside    the next bar's whole range sits inside the mother's. Buyers and
              sellers have stopped disagreeing about the range. Compression.
    trigger   a bar that CLOSES above the mother's high. Not a wick through it
              -- a close. The wick-through is the trap, not the signal.

Stop goes under the inside bar's low, because that is the pattern's own
invalidation: if price is back inside the coil, the coil didn't resolve up.
Chosen from the setup, before looking at what happened next (CLAUDE.md 10.5).
"""

# The inside bar's low, padded slightly below, is the stop. 0.2% keeps the
# stop off the exact tick that a thousand other stops sit on.
STOP_PAD = 0.002

# Below this, the stop is so close to entry that any slippage dominates the
# trade and the R multiple is fiction.
MIN_RISK_FRAC = 0.003


def _is_inside(inner, outer):
    return inner["h"] <= outer["h"] and inner["l"] >= outer["l"]


def iter_inside_bar_breakouts(bars):
    """Every non-overlapping (mother, inside, trigger) in `bars`, in order.

    Non-overlapping because two trades sharing a trigger bar are one trade
    counted twice, which flatters a base rate.
    """
    i = 0
    while i + 2 < len(bars):
        mother, inside, trigger = bars[i], bars[i + 1], bars[i + 2]
        if _is_inside(inside, mother) and trigger["c"] > mother["h"]:
            yield {"mother": i, "inside": i + 1, "trigger": i + 2}
            i += 2  # next candidate mother is the trigger bar itself
        else:
            i += 1


def find_inside_bar_breakout(bars):
    """The FIRST qualifying sequence, or None.

    First, deliberately -- not the biggest or the prettiest. Shopping the
    window for the best-looking instance is how a scanner starts lying.
    """
    return next(iter_inside_bar_breakouts(bars), None)


def resolve_trade(bars, mother, inside, trigger, rr=2.0, horizon=12):
    """Resolve the trade this pattern defines. None if it isn't tradeable.

    One rule, so the number on screen and the number in the base rate cannot
    drift apart. Returns entry/stop/target/outcome together -- a target
    without a stop shows the upside and hides what being wrong cost.
    """
    entry = bars[trigger]["c"]
    stop = bars[inside]["l"] * (1 - STOP_PAD)
    risk = entry - stop
    if risk < entry * MIN_RISK_FRAC:
        return None
    target = entry + rr * risk

    outcome, tp_at = "open", None
    for k in range(trigger + 1, min(trigger + 1 + horizon, len(bars))):
        hit_sl = bars[k]["l"] <= stop
        hit_tp = bars[k]["h"] >= target
        # A bar holding both: daily bars can't order two intrabar touches, so
        # take the bad one. Assuming the good one is how a backtest lies.
        if hit_sl:
            outcome = "loss"
            break
        if hit_tp:
            outcome, tp_at = "win", k - trigger
            break

    return {
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "risk": round(risk, 2),
        "rr": rr,
        "outcome": outcome,
        "tpAt": tp_at,
    }


def base_rate(bars, rr=2.0, horizon=12):
    """How often this pattern actually paid, on this series.

    Counts every occurrence the scanner can find -- including the ones that
    lost and the ones that never resolved. Open trades stay in the
    denominator: dropping them turns "didn't work yet" into "didn't happen".
    """
    tally = {"win": 0, "loss": 0, "open": 0}
    for seq in iter_inside_bar_breakouts(bars):
        t = resolve_trade(bars, seq["mother"], seq["inside"], seq["trigger"], rr, horizon)
        if t is not None:
            tally[t["outcome"]] += 1
    n = sum(tally.values())
    return {
        "n": n,
        "wins": tally["win"],
        "losses": tally["loss"],
        "open": tally["open"],
        "pct": round(tally["win"] / n * 100) if n else None,
    }
