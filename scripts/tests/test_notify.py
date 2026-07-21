"""Tests for the pipeline failure notifier.

Guiding rule: notification is observability, not the job. A broken notifier
must never fail a refresh that actually succeeded, so every failure path
here degrades to a return value rather than an exception.

The toast itself is not asserted (it needs a desktop session); it was
verified live on 2026-07-20 and reported channel='winrt'.
"""
from __future__ import annotations

import json

from aiinvest import notify


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def test_status_file_written_on_failure(tmp_path):
    p = notify.write_status(tmp_path, ok=False, job="J", summary="2 problems",
                            problems=["a", "b"], duration_s=12.5)
    assert p
    d = _read(p)
    assert d["ok"] is False
    assert d["problems"] == ["a", "b"]
    assert d["duration_s"] == 12.5
    assert d["finished_at"].endswith("Z")


def test_status_file_written_on_success_too(tmp_path):
    """Always written -- a stale 'ok' timestamp is itself the signal that
    last night's job never ran."""
    p = notify.write_status(tmp_path, ok=True, job="J", summary="all good")
    assert _read(p)["ok"] is True


def test_status_path_is_stable(tmp_path):
    p = notify.write_status(tmp_path, ok=True, job="J", summary="s")
    assert p.replace("\\", "/").endswith(notify.STATUS_REL)


def test_write_status_creates_missing_directories(tmp_path):
    assert not (tmp_path / "data").exists()
    assert notify.write_status(tmp_path, ok=True, job="J", summary="s")


def test_write_status_returns_none_on_unwritable_root(tmp_path):
    """Must degrade, not raise -- a full disk cannot fail a good refresh."""
    blocker = tmp_path / "data"
    blocker.write_text("not a directory", encoding="utf-8")
    assert notify.write_status(tmp_path, ok=True, job="J", summary="s") is None


# ---------------------------------------------------------------------------
# message construction
# ---------------------------------------------------------------------------

def test_body_lists_problems(tmp_path):
    assert "alpha" in notify._body(["alpha", "beta"])


def test_body_truncates_long_problem_lists(tmp_path):
    body = notify._body([f"p{i}" for i in range(10)], limit=3)
    assert "+7 more" in body
    assert body.count(";") == 2


def test_body_handles_no_problems(tmp_path):
    assert "last_run.json" in notify._body([])


def test_toast_script_escapes_xml_metacharacters():
    """A '&' or '<' in a filename would otherwise break the toast XML."""
    script = notify._ps_toast_script("A & B", "x <bad> & 'quoted'")
    assert "&amp;" in script
    assert "&lt;bad&gt;" in script
    assert "<bad>" not in script.split("LoadXml")[1].split("')")[0]


def test_notify_success_is_silent_by_default(tmp_path):
    """A nightly success toast is noise, and noise is how alerts get ignored."""
    out = notify.notify_success(tmp_path, job="J", summary="ok")
    assert out["channel"] is None
    assert out["ok"] is True
    assert _read(out["status_file"])["ok"] is True
