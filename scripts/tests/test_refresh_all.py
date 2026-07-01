"""Unit tests for the full-refresh orchestrator plan builders (pure, no subprocess).

refresh_all chains, in strict order:
  1. fair-value backfill (GuruFocus scalar, headless) -> data/fundamental/  [MUST precede export]
  2. refresh_daily.py   (pulls + merges + export_site folds in the fresh fair values + news)
  3. refresh_congress.py --years ... --keep-going

Also covers fundamental_backfill.resolve_universe (bare-symbol universe resolution).
"""
import sys
import pathlib

_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import refresh_all  # noqa: E402
import fundamental_backfill as fb  # noqa: E402


def _ns(**kw):
    return type("NS", (), kw)()


def _scripts(steps):
    # cmd[0] is the python exe; cmd[1] is the script name
    return [s["cmd"][1] for s in steps]


def test_full_plan_order_fundamentals_then_daily_then_congress():
    steps = refresh_all.build_plan(_ns(fundamentals="all", years=[2026], keep_going=True, deploy=False))
    scr = _scripts(steps)
    assert scr == ["fundamental_backfill.py", "refresh_daily.py", "refresh_congress.py"]
    assert scr.index("fundamental_backfill.py") < scr.index("refresh_daily.py") < scr.index("refresh_congress.py")


def test_fundamentals_step_targets_the_universe():
    steps = refresh_all.build_plan(_ns(fundamentals="all", years=[2026], keep_going=True, deploy=False))
    cmd = steps[0]["cmd"]
    assert "--universe" in cmd and "all" in cmd


def test_congress_step_is_current_year_and_keep_going():
    steps = refresh_all.build_plan(_ns(fundamentals="all", years=[2026], keep_going=True, deploy=False))
    cg = steps[-1]["cmd"]
    assert "--keep-going" in cg
    assert "2026" in cg


def test_skip_fundamentals_omits_the_backfill():
    steps = refresh_all.build_plan(_ns(fundamentals="none", years=[2026], keep_going=True, deploy=False))
    scr = _scripts(steps)
    assert "fundamental_backfill.py" not in scr
    assert scr[0] == "refresh_daily.py"


def test_resolve_universe_all_returns_bare_symbols():
    syms = fb.resolve_universe("all")
    assert syms, "universe should be non-empty"
    assert all(":" not in s for s in syms), "symbols must be bare (no EXCHANGE: prefix)"
    assert "NVDA" in syms
    assert len(syms) == len(set(syms)), "deduplicated"


def test_resolve_universe_all_is_union_of_ai_and_quantum():
    ai = set(fb.resolve_universe("ai"))
    q = set(fb.resolve_universe("quantum"))
    allu = set(fb.resolve_universe("all"))
    assert ai and q
    assert allu == ai | q
