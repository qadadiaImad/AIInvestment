"""Save fundamental-value series harvested from the MCP browser session.

Input: one or more JSON files shaped { "SYM": {"gf_value":..,"ms":..,"medps":[[date,val],..]}, ... }
(the compact chart payloads captured via the MCP Chrome session). Parses each with the
generic parser and writes data/fundamental/<SYM>.json via the merge-protect save (never
downgrades). Relabels everything generically — no source name stored.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import sys

import fundamental_fetch as ff
from aiinvest import fundamental


def main(argv=None):
    paths = list(argv if argv is not None else sys.argv[1:])
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    saved = 0
    for path in paths:
        data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        for sym, payload in data.items():
            if not isinstance(payload, dict):
                continue
            parsed = fundamental.parse_valuation_chart(payload)
            if not parsed.get("fundamental_value_series"):
                continue
            ff.save(sym.upper(), {
                "symbol": sym.upper(),
                "fundamental_value": parsed.get("fundamental_value"),
                "margin_of_safety_pct": parsed.get("margin_of_safety_pct"),
                "fundamental_value_series": parsed["fundamental_value_series"],
                "retrieved_at": now, "source": "fundamental-model",
            })
            saved += 1
    print(f"saved series for {saved} tickers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
