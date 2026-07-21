"""Halal steps appear in the daily plan (pure build_plan, no subprocess)."""
import argparse

import refresh_daily


def _args(**kw):
    ns = argparse.Namespace(dry_run=False, with_backtest=False,
                            deploy=False, keep_going=False)
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def test_halal_steps_in_plan_between_quantum_and_screener():
    labels = [s["label"] for s in refresh_daily.build_plan(_args())]
    assert "pull halal inputs" in labels
    assert "export halal.json" in labels
    assert labels.index("export halal.json") < labels.index("build screener")
    assert labels.index("pull halal inputs") < labels.index("export halal.json")
