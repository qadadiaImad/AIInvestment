"""Rank halal verdicts into content-worthy stories (carousels/reels). Pure, no I/O.

Scoring: verdict flips (from alerts) 1000 + |delta| (always outrank non-flip stories);
extreme ratios 10x the threshold-multiple; business-vs-ratio surprises 40;
near-threshold squeezes 20.
Copy rails live with the RENDERERS (higgs), not here — this module only emits
facts and numbers.
"""
from __future__ import annotations


def _fmt_ratio(r):
    if r is None:
        return "—"
    return f"{r * 100:.1f}%" if r < 2 else f"{r:.1f}x"


def pick_stories(bundle, alerts=None, top=3):
    stories = []
    verdicts = (bundle or {}).get("verdicts", {})

    for a in (alerts or []):
        stories.append({
            "symbol": a["symbol"], "kind": "flip",
            "score": 1000.0 + abs((a.get("new_value") or 0) - (a.get("old_value") or 0)),
            "headline_fact": f"{a['symbol']} flipped {a['from']} -> {a['to']}",
            "numbers": [{"label": "was", "value": _fmt_ratio(a.get("old_value"))},
                        {"label": "now", "value": _fmt_ratio(a.get("new_value"))}],
            "verdict": a["to"],
        })

    for sym, v in verdicts.items():
        tests = [t for std in v.get("standards", {}).values() for t in std.get("tests", [])]
        failing = [t for t in tests if t.get("status") == "fail" and t.get("ratio") is not None]
        biz = v.get("business", {}).get("status")

        if biz == "prohibited" and tests and all(
                t.get("status") == "pass" for t in tests if t.get("status") != "unknown"):
            worst = min(tests, key=lambda t: t.get("ratio") or 9e9)
            stories.append({"symbol": sym, "kind": "business_override", "score": 40.0,
                            "headline_fact": f"{sym}: every ratio passes — the business itself is the reason",
                            "numbers": [{"label": worst.get("label", "best ratio"),
                                         "value": _fmt_ratio(worst.get("ratio"))}],
                            "verdict": v.get("overall")})
        elif failing:
            worst = max(failing, key=lambda t: (t["ratio"] or 0) / (t.get("threshold") or 1))
            multiple = (worst["ratio"] or 0) / (worst.get("threshold") or 1)
            if multiple >= 2:
                stories.append({"symbol": sym, "kind": "extreme_ratio", "score": 10.0 * multiple,
                                "headline_fact": f"{sym}: {worst.get('label')} at {_fmt_ratio(worst['ratio'])} vs a {_fmt_ratio(worst.get('threshold'))} limit",
                                "numbers": [{"label": worst.get("label", "ratio"), "value": _fmt_ratio(worst["ratio"])},
                                            {"label": "limit", "value": _fmt_ratio(worst.get("threshold"))}],
                                "verdict": v.get("overall")})
            elif 0 < (worst["ratio"] or 0) - (worst.get("threshold") or 0) < 0.05:
                stories.append({"symbol": sym, "kind": "margin_squeeze", "score": 20.0,
                                "headline_fact": f"{sym} misses by a whisker: {_fmt_ratio(worst['ratio'])} vs {_fmt_ratio(worst.get('threshold'))}",
                                "numbers": [{"label": worst.get("label", "ratio"), "value": _fmt_ratio(worst["ratio"])},
                                            {"label": "limit", "value": _fmt_ratio(worst.get("threshold"))}],
                                "verdict": v.get("overall")})

    stories.sort(key=lambda s: (-s["score"], s["symbol"]))
    return stories[:top]
