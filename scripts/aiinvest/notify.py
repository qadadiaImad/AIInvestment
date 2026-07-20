"""Failure notification for unattended pipeline runs.

An unattended 06:00 job is only useful if a failure reaches you. This does
two things, in order of durability:

1. Writes a machine-readable status file (``data/status/last_run.json``).
   Always written, success or failure. Survives reboots, and is the natural
   feed for a pipeline view in the studio app later.
2. Raises a Windows toast. Toasts land in Action Center and persist, so a
   06:00 failure is still waiting at 08:00 -- unlike a console message
   nobody sees.

Best-effort by construction: notification is observability, not the job.
A broken notifier must never fail a refresh that actually succeeded, so
every path here swallows its own errors and reports via the return value.

Verified on this machine 2026-07-20: WinRT toast works; the .NET NotifyIcon
balloon works as a fallback. BurntToast and msg.exe are both absent, so
neither is relied upon.
"""
from __future__ import annotations

import base64
import datetime
import json
import pathlib
import subprocess
import xml.sax.saxutils as _xml

__all__ = ["write_status", "toast", "notify_failure", "notify_success", "STATUS_REL"]

STATUS_REL = "data/status/last_run.json"

_PS = "powershell.exe"
_TOAST_TIMEOUT = 25


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_status(repo_root, *, ok: bool, job: str, summary: str,
                 problems=(), duration_s: float | None = None) -> str | None:
    """Persist the outcome. Returns the path written, or None on failure."""
    try:
        path = pathlib.Path(repo_root) / STATUS_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "job": job,
            "ok": ok,
            "finished_at": _now(),
            "duration_s": duration_s,
            "summary": summary,
            "problems": list(problems),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(path)
    except OSError:
        return None


def _ps_toast_script(title: str, body: str) -> str:
    """WinRT toast, with a .NET balloon fallback if WinRT is unavailable."""
    t, b = _xml.escape(title), _xml.escape(body)
    return f"""
$ErrorActionPreference = 'Stop'
try {{
    $null = [Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime]
    $null = [Windows.Data.Xml.Dom.XmlDocument,Windows.Data.Xml.Dom,ContentType=WindowsRuntime]
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml('<toast><visual><binding template="ToastText02"><text id="1">{t}</text><text id="2">{b}</text></binding></visual></toast>')
    $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Microsoft.WindowsPowerShell').Show($toast)
    Write-Output 'winrt'
}} catch {{
    Add-Type -AssemblyName System.Windows.Forms
    $ni = New-Object System.Windows.Forms.NotifyIcon
    $ni.Icon = [System.Drawing.SystemIcons]::Warning
    $ni.Visible = $true
    $ni.ShowBalloonTip(10000, '{t}', '{b}', [System.Windows.Forms.ToolTipIcon]::Warning)
    Start-Sleep -Milliseconds 1500
    $ni.Dispose()
    Write-Output 'balloon'
}}
""".strip()


def toast(title: str, body: str) -> str | None:
    """Raise a desktop notification. Returns 'winrt' | 'balloon' | None."""
    script = _ps_toast_script(title, body)
    # -EncodedCommand takes UTF-16LE base64, sidestepping every quoting and
    # codepage problem between Python, cmd and PowerShell.
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    try:
        proc = subprocess.run(
            [_PS, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            capture_output=True, text=True, timeout=_TOAST_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return None
    out = (proc.stdout or "").strip().splitlines()
    return out[-1].strip() if out and proc.returncode == 0 else None


def _body(problems, limit=3) -> str:
    if not problems:
        return "See data/status/last_run.json for detail."
    head = "; ".join(str(p) for p in problems[:limit])
    extra = len(problems) - limit
    return head + (f" (+{extra} more)" if extra > 0 else "")


def notify_failure(repo_root, *, job: str, problems, duration_s=None) -> dict:
    """Record and announce a failed run."""
    summary = f"{len(problems)} problem(s)"
    status = write_status(repo_root, ok=False, job=job, summary=summary,
                          problems=problems, duration_s=duration_s)
    channel = toast(f"{job} FAILED", _body(problems))
    return {"status_file": status, "channel": channel, "ok": False}


def notify_success(repo_root, *, job: str, summary: str, duration_s=None,
                   announce: bool = False) -> dict:
    """Record a clean run. Silent unless ``announce`` -- a nightly success
    toast is noise, and noise is how alerts get ignored."""
    status = write_status(repo_root, ok=True, job=job, summary=summary,
                          duration_s=duration_s)
    channel = toast(f"{job} ok", summary) if announce else None
    return {"status_file": status, "channel": channel, "ok": True}
