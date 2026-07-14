"""Light unit tests for the refresh orchestrators' pure plan builders.

These import build_plan() directly and assert on the ordered command list — no
subprocess is ever executed, so the tests are fast and side-effect-free.
"""
import sys
import pathlib

import pytest

_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import refresh_daily  # noqa: E402
import refresh_congress  # noqa: E402
import refresh_ta  # noqa: E402


def _ns(**kw):
    return type("NS", (), kw)()


def _labels(steps):
    return [s["label"] for s in steps]


def _cmd_str(step):
    return " ".join(step["cmd"])


# --------------------------------------------------------------------------- daily


def test_daily_plan_order_default():
    """Default daily plan is in the documented order and OMITS the backtest."""
    steps = refresh_daily.build_plan(_ns(with_backtest=False, deploy=False, keep_going=False))
    cmds = [s["cmd"][1] if len(s["cmd"]) > 1 else s["cmd"][0] for s in steps]
    # the core AI pipeline order is preserved (quantum steps slot in after export_site)
    assert cmds[:6] == [
        "pull_ai_stack.py",
        "pull_prices.py",
        "merge_enriched.py",
        "build_capital_web.py",
        "run_graph_analysis.py",
        "export_site.py",
    ]
    assert "build_screener.py" in cmds
    # graph analysis must come before site export (site reads graph artifacts/order matters)
    assert cmds.index("run_graph_analysis.py") < cmds.index("export_site.py")
    # the AI export still precedes the screener rebuild
    assert cmds.index("export_site.py") < cmds.index("build_screener.py")


def test_daily_plan_includes_news_after_screener():
    """pull_news.py runs after build_screener.py (guarded; present here)."""
    steps = refresh_daily.build_plan(_ns(with_backtest=False, deploy=False, keep_going=False))
    cmds = [s["cmd"][1] if len(s["cmd"]) > 1 else s["cmd"][0] for s in steps]
    assert "pull_news.py" in cmds
    assert cmds.index("build_screener.py") < cmds.index("pull_news.py")


def test_daily_news_step_is_guarded(monkeypatch):
    """The news step appears IFF pull_news.py exists on disk."""
    monkeypatch.setattr(refresh_daily.os.path, "exists", lambda p: False)
    steps_absent = refresh_daily.build_plan(
        _ns(with_backtest=False, deploy=False, keep_going=False))
    assert not any("pull_news.py" in _cmd_str(s) for s in steps_absent)

    monkeypatch.setattr(refresh_daily.os.path, "exists", lambda p: True)
    steps_present = refresh_daily.build_plan(
        _ns(with_backtest=False, deploy=False, keep_going=False))
    assert any("pull_news.py" in _cmd_str(s) for s in steps_present)


def test_daily_skip_backtest_default_omits_backtest():
    steps = refresh_daily.build_plan(_ns(with_backtest=False, deploy=False, keep_going=False))
    assert not any("run_backtest.py" in _cmd_str(s) for s in steps)


def test_daily_with_backtest_includes_and_positions_backtest():
    steps = refresh_daily.build_plan(_ns(with_backtest=True, deploy=False, keep_going=False))
    cmds = [s["cmd"][1] for s in steps]
    assert "run_backtest.py" in cmds
    # backtest runs after graph analysis and before the site export
    assert cmds.index("run_graph_analysis.py") < cmds.index("run_backtest.py")
    assert cmds.index("run_backtest.py") < cmds.index("export_site.py")


def test_daily_deploy_appends_vercel_in_web():
    steps = refresh_daily.build_plan(_ns(with_backtest=False, deploy=True, keep_going=False))
    last = steps[-1]
    assert last["cmd"][0] == "vercel"
    assert "--prod" in last["cmd"] and "--yes" in last["cmd"]
    assert last["cwd"].endswith("web")
    # no deploy step when --deploy is off
    off = refresh_daily.build_plan(_ns(with_backtest=False, deploy=False, keep_going=False))
    assert not any(s["cmd"][0] == "vercel" for s in off)


# --------------------------------------------------------------------------- quantum


def test_daily_includes_quantum_steps_after_ai_export():
    """The quantum pull + export run AFTER export_site.py (AI path stays byte-identical),
    pull_quantum before export_quantum, and both before build_screener."""
    steps = refresh_daily.build_plan(_ns(with_backtest=False, deploy=False, keep_going=False))
    cmds = [s["cmd"][1] if len(s["cmd"]) > 1 else s["cmd"][0] for s in steps]
    assert "pull_quantum.py" in cmds
    assert "export_quantum.py" in cmds
    # AI export precedes both quantum steps
    assert cmds.index("export_site.py") < cmds.index("pull_quantum.py")
    assert cmds.index("export_site.py") < cmds.index("export_quantum.py")
    # pull before export
    assert cmds.index("pull_quantum.py") < cmds.index("export_quantum.py")
    # both before the screener rebuild
    assert cmds.index("export_quantum.py") < cmds.index("build_screener.py")


def test_daily_quantum_steps_are_guarded(monkeypatch):
    """The quantum steps appear IFF the quantum CLIs exist on disk."""
    monkeypatch.setattr(refresh_daily.os.path, "exists", lambda p: False)
    steps_absent = refresh_daily.build_plan(
        _ns(with_backtest=False, deploy=False, keep_going=False))
    assert not any("pull_quantum.py" in _cmd_str(s) for s in steps_absent)
    assert not any("export_quantum.py" in _cmd_str(s) for s in steps_absent)

    monkeypatch.setattr(refresh_daily.os.path, "exists", lambda p: True)
    steps_present = refresh_daily.build_plan(
        _ns(with_backtest=False, deploy=False, keep_going=False))
    assert any("pull_quantum.py" in _cmd_str(s) for s in steps_present)
    assert any("export_quantum.py" in _cmd_str(s) for s in steps_present)


# --------------------------------------------------------------------------- congress


def test_congress_plan_includes_both_years_and_export():
    steps = refresh_congress.build_plan(
        _ns(years=[2025, 2026], delay=0.4, deploy=False, keep_going=False))
    joined = [_cmd_str(s) for s in steps]
    assert any("pull_congress.py --year 2025" in c and "--limit 99999" in c for c in joined)
    assert any("pull_congress.py --year 2026" in c and "--limit 99999" in c for c in joined)
    # export_congress.py is the terminal data step (last when not deploying)
    assert steps[-1]["cmd"][1] == "export_congress.py"


def test_congress_conflict_step_is_guarded(monkeypatch):
    """The conflict step appears IFF pull_conflict.py exists on disk."""
    # Force "absent": no conflict step.
    monkeypatch.setattr(refresh_congress.os.path, "exists", lambda p: False)
    steps_absent = refresh_congress.build_plan(
        _ns(years=[2025], delay=0.4, deploy=False, keep_going=False))
    assert not any("pull_conflict.py" in _cmd_str(s) for s in steps_absent)

    # Force "present": conflict step inserted before export.
    monkeypatch.setattr(refresh_congress.os.path, "exists", lambda p: True)
    steps_present = refresh_congress.build_plan(
        _ns(years=[2025], delay=0.4, deploy=False, keep_going=False))
    cmds = [s["cmd"][1] for s in steps_present]
    assert "pull_conflict.py" in cmds
    assert cmds.index("pull_conflict.py") < cmds.index("export_congress.py")


def test_congress_member_profiles_step_is_guarded(monkeypatch):
    """The member-profiles step appears IFF pull_member_profiles.py exists, and
    sits AFTER the conflict step and BEFORE export_congress.py."""
    # Force "absent": no member-profiles step.
    monkeypatch.setattr(refresh_congress.os.path, "exists", lambda p: False)
    steps_absent = refresh_congress.build_plan(
        _ns(years=[2025], delay=0.4, deploy=False, keep_going=False))
    assert not any("pull_member_profiles.py" in _cmd_str(s) for s in steps_absent)

    # Force "present": member-profiles step inserted after conflict, before export.
    monkeypatch.setattr(refresh_congress.os.path, "exists", lambda p: True)
    steps_present = refresh_congress.build_plan(
        _ns(years=[2025], delay=0.4, deploy=False, keep_going=False))
    cmds = [s["cmd"][1] for s in steps_present]
    assert "pull_member_profiles.py" in cmds
    assert cmds.index("pull_conflict.py") < cmds.index("pull_member_profiles.py")
    assert cmds.index("pull_member_profiles.py") < cmds.index("export_congress.py")


def test_congress_delay_threaded_into_pull_commands():
    steps = refresh_congress.build_plan(
        _ns(years=[2025, 2026], delay=1.5, deploy=False, keep_going=False))
    pulls = [s for s in steps if s["cmd"][1] == "pull_congress.py"]
    assert pulls and all("1.5" in s["cmd"] for s in pulls)


# --------------------------------------------------------------------------- ta desk


def test_ta_plan_has_one_pull_step_by_default():
    steps = refresh_ta.build_plan(_ns(deploy=False, keep_going=False))
    cmds = [s["cmd"][1] for s in steps]
    assert cmds == ["pull_ta.py"]


def test_ta_deploy_appends_vercel_in_web():
    steps = refresh_ta.build_plan(_ns(deploy=True, keep_going=False))
    last = steps[-1]
    assert last["cmd"][0] == "vercel"
    assert "--prod" in last["cmd"] and "--yes" in last["cmd"]
    assert last["cwd"].endswith("web")
    off = refresh_ta.build_plan(_ns(deploy=False, keep_going=False))
    assert not any(s["cmd"][0] == "vercel" for s in off)


def test_ta_plan_pull_step_runs_in_scripts_dir():
    steps = refresh_ta.build_plan(_ns(deploy=False, keep_going=False))
    assert steps[0]["cwd"].endswith("scripts")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
