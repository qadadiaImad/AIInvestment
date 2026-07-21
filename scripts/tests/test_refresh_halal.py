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


def test_pull_xbrl_facts_between_pull_halal_inputs_and_export_halal():
    """'pull xbrl facts' step must appear between 'pull halal inputs' and 'export halal.json'."""
    labels = [s["label"] for s in refresh_daily.build_plan(_args())]
    assert "pull xbrl facts" in labels, "missing 'pull xbrl facts' step in daily plan"
    hi = labels.index("pull halal inputs")
    xf = labels.index("pull xbrl facts")
    eh = labels.index("export halal.json")
    assert hi < xf < eh, (
        f"ordering violation: pull halal inputs={hi}, pull xbrl facts={xf}, "
        f"export halal.json={eh}"
    )
