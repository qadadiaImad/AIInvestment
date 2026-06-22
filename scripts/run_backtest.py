"""Backtest named strategies over our own data; write web/public/data/backtests.json.

Strategies: momentum (12-1, point-in-time), fundamental (price vs PIT fundamental value),
ai_synthesis (a current composite conviction applied retroactively — ILLUSTRATIVE only).
Monthly long top-N equal-weight vs an equal-weight benchmark, via vectorbt.

HARD RULES: point-in-time only (fundamentals lagged + projected points excluded by
backtest.pit_fundamental_value); survivorship is NOT corrected (today's AI names) and is
flagged loudly. Educational/research — not financial advice.
"""
from __future__ import annotations

import datetime
import glob
import json
import pathlib

import numpy as np
import pandas as pd
import vectorbt as vbt

from aiinvest import ai_stack, backtest as core

REPO = pathlib.Path(__file__).resolve().parent.parent
PRICES = REPO / "web" / "public" / "data" / "prices"
FUND = REPO / "data" / "fundamental"
TOP_N, FEES, LAG_D, MOM_LB = 10, 0.001, 45, 231


def load_prices():
    cols = {}
    for f in glob.glob(str(PRICES / "*.json")):
        d = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        s = d.get("series") or []
        if len(s) < 300:
            continue
        cols[d["symbol"]] = pd.Series({p["date"]: p["close"] for p in s})
    df = pd.DataFrame(cols)
    df.index = pd.to_datetime(df.index)
    return df.sort_index().ffill()


def load_fundamentals():
    out = {}
    for f in glob.glob(str(FUND / "*.json")):
        d = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        if d.get("fundamental_value_series"):
            out[d["symbol"]] = d["fundamental_value_series"]
    return out


def month_end_dates(idx):
    s = pd.Series(idx, index=idx)
    return list(s.groupby([idx.year, idx.month]).last().values)


def topn_weights(score, close, rebs, n=TOP_N):
    w = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    for dt in rebs:
        if dt not in score.index:
            continue
        row = score.loc[dt].dropna()
        price = close.loc[dt].dropna()
        row = row[row.index.isin(price.index)]
        if len(row) == 0:
            continue
        top = row.sort_values(ascending=False).head(n)
        w.loc[dt] = 0.0
        w.loc[dt, top.index] = 1.0 / len(top)
    return w


def equal_weights(close, rebs):
    w = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    for dt in rebs:
        price = close.loc[dt].dropna()
        if len(price) == 0:
            continue
        w.loc[dt] = 0.0
        w.loc[dt, price.index] = 1.0 / len(price)
    return w


def fundamental_score(close, fund, rebs):
    sc = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    for dt in rebs:
        asof = pd.Timestamp(dt).date().isoformat()
        for sym in close.columns:
            series = fund.get(sym)
            if not series:
                continue
            pv = core.pit_fundamental_value(series, asof, LAG_D)
            price = close.at[dt, sym]
            if pv and pd.notna(price) and price > 0:
                sc.at[dt, sym] = (pv - price) / price  # higher = cheaper vs value
    return sc


def _rf_mom(s, r):
    return f"12-1 momentum {s * 100:+.0f}% · rank {r}" if s is not None else f"rank {r}"


def _rf_fnd(s, r):
    return f"{s * 100:+.0f}% vs fundamental value · rank {r}" if s is not None else f"rank {r}"


def _rf_ai(s, r):
    return f"conviction {s * 100:.0f}th pct · rank {r}" if s is not None else f"rank {r}"


def holdings_detail(weights, score, rebs, reason_fn):
    """Current portfolio with each name's ENTRY date (start of current holding streak) and WHY."""
    last = rebs[-1]
    if last not in weights.index:
        return []
    srow = score.loc[last] if last in score.index else None
    held = [s for s in weights.columns if pd.notna(weights.at[last, s]) and weights.at[last, s] > 0]
    if srow is not None:
        held = list(srow[held].sort_values(ascending=False).index)  # rank order
    out = []
    for rank, sym in enumerate(held, 1):
        entered = last
        for d in reversed(rebs):
            if d > last:
                continue
            wv = weights.at[d, sym] if d in weights.index else None
            if pd.notna(wv) and wv and wv > 0:
                entered = d
            else:
                break
        sc = float(srow[sym]) if (srow is not None and pd.notna(srow.get(sym))) else None
        out.append({"symbol": sym, "rank": rank,
                    "entered": pd.Timestamp(entered).strftime("%Y-%m-%d"),
                    "reason": reason_fn(sc, rank)})
    return out


def run_portfolio(close, weights):
    pf = vbt.Portfolio.from_orders(
        close=close, size=weights, size_type="targetpercent",
        group_by=True, cash_sharing=True, call_seq="auto", freq="1D", fees=FEES)
    eq = pf.value()
    eq = eq / eq.iloc[0]  # normalize to 1.0
    rets = eq.pct_change().dropna().tolist()
    curve = [[d.strftime("%Y-%m-%d"), round(float(v), 4)] for d, v in eq.items()]
    return {
        "equity": curve[:: max(1, len(curve) // 400)],  # downsample for payload
        "metrics": {
            "total_return": round(float(eq.iloc[-1] - 1) * 100, 1),
            "cagr": round(core.cagr(eq.tolist()) * 100, 1),
            "sharpe": round(core.sharpe(rets), 2),
            "max_drawdown": round(core.max_drawdown(eq.tolist()) * 100, 1),
        },
    }


LAYER_LABELS = {
    "all": "All layers", "L0-energy": "L0 · Energy", "L1-chips": "L1 · Chips",
    "L2-infra": "L2 · Infra", "L4-application": "L4 · Application",
}


def _defs(n):
    return {
        "momentum": (f"Each month, hold the {n} names with the strongest trailing ~12-month return "
                     f"(most recent month skipped), equal-weight. Classic price-momentum; point-in-time."),
        "fundamental": (f"Each month, hold the {n} names at the largest discount of price to their "
                        f"POINT-IN-TIME fundamental value (value lagged ~{LAG_D}d; projected points "
                        f"excluded), equal-weight."),
        "ai_synthesis": (f"Each month, hold the {n} highest-conviction names by a composite of momentum "
                         f"+ value percentiles (stand-in 'AI judge'). ILLUSTRATIVE: current signal "
                         f"applied retroactively (lookahead)."),
    }


def _method(u, n):
    return (f"Universe: {u} names with >=1y price history. Monthly rebalance to equal-weight top {n}, "
            f"{FEES * 100:g}%/trade, simulated with vectorbt. SURVIVORSHIP-BIASED (today's names) — "
            f"educational illustration, not a trading system, not financial advice.")


def run_scope(close, rebs, scope_syms, specs, top_n):
    """Run all strategies + benchmark restricted to scope_syms (a layer or 'all')."""
    cols = [s for s in scope_syms if s in close.columns]
    if len(cols) < 3:
        return None
    n = min(top_n, max(2, len(cols) // 2))
    close_sub = close[cols].ffill()
    dd = pd.Timestamp(rebs[-1]).strftime("%Y-%m-%d")
    defs, method = _defs(n), _method(len(cols), n)
    strats = []
    for key, (label, score, rf) in specs.items():
        sc = score[cols]
        w = topn_weights(sc, close_sub, rebs, n)
        res = run_portfolio(close_sub, w)
        holdings = holdings_detail(w, sc, rebs, rf)
        strats.append({"key": key, "name": label, "definition": defs[key], "methodology": method,
                       "decision_date": dd, "holdings": holdings,
                       "current_holdings": [h["symbol"] for h in holdings], **res})
    bench = run_portfolio(close_sub, equal_weights(close_sub, rebs))
    return {"top_n": n, "universe": len(cols),
            "benchmark": {"name": f"Equal-weight ({len(cols)} names)", **bench},
            "strategies": strats}


def main():
    df = load_prices()
    fund = load_fundamentals()
    start = df.index[252]                      # need 1y lookback for momentum
    universe = [c for c in df.columns if pd.notna(df.at[start, c])]
    close = df[universe].loc[start:].ffill()
    rebs = month_end_dates(close.index)

    mom_full = df[universe].pct_change(MOM_LB).reindex(close.index)
    fnd = fundamental_score(close, fund, rebs)
    # ai_synthesis: current composite conviction (momentum + fundamental discount percentiles),
    # broadcast as a STATIC score -> illustrative/lookahead, labeled as such.
    cur = pd.DataFrame({"mom": mom_full.iloc[-1], "fnd": fnd.loc[rebs[-1]] if rebs[-1] in fnd.index else np.nan})
    conv = cur.rank(pct=True).mean(axis=1)
    ai = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    for dt in rebs:
        ai.loc[dt] = conv

    specs = {
        "momentum": ("Momentum (12-1)", mom_full, _rf_mom),
        "fundamental": ("Fundamental (price vs value, point-in-time)", fnd, _rf_fnd),
        "ai_synthesis": ("AI-Synthesis conviction (illustrative, current signal)", ai, _rf_ai),
    }
    scope_defs = [("all", universe, TOP_N)]
    for layer in ("L0-energy", "L1-chips", "L2-infra", "L4-application"):
        bare = [t.split(":")[-1] for t in ai_stack.LAYERS.get(layer, [])]
        scope_defs.append((layer, [s for s in bare if s in universe], 5))

    scopes = {}
    for skey, syms, n in scope_defs:
        r = run_scope(close, rebs, syms, specs, n)
        if r:
            scopes[skey] = {"label": LAYER_LABELS[skey], **r}

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bundle = {
        "generated_at": now,
        "window": {"start": close.index[0].strftime("%Y-%m-%d"),
                   "end": close.index[-1].strftime("%Y-%m-%d"), "universe": len(universe)},
        "params": {"rebalance": "monthly", "fees_pct": FEES * 100, "fundamental_lag_days": LAG_D},
        "survivorship_warning": ("Backtests run on TODAY'S AI-stack names — SURVIVORSHIP-BIASED, "
                                 "overstating achievable returns. ai_synthesis is a current composite "
                                 "applied retroactively (lookahead). Educational only — NOT financial advice."),
        "scopes": scopes,
    }
    out = REPO / "web" / "public" / "data" / "backtests.json"
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"Wrote {out}  ({bundle['window']['start']}..{bundle['window']['end']})")
    for skey, sc in scopes.items():
        print(f"  [{skey}] universe={sc['universe']} top_n={sc['top_n']}")
        for s in sc["strategies"]:
            m = s["metrics"]
            print(f"     {s['key']:14} CAGR={m['cagr']:>6}% Sharpe={m['sharpe']:>5} maxDD={m['max_drawdown']}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
