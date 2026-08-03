"""Start or attach to the local ComfyUI server, headless.

SERVER_ARGV is exactly what the Desktop app runs — captured live from
GET /system_stats on 2026-08-03 (minus --log-stdout). Never start the
Desktop GUI while a headless server is running: same port, same sqlite.
"""
from __future__ import annotations

import subprocess
import time
import urllib.request
from pathlib import Path

HOME = Path.home()
DOCS = HOME / "Documents" / "ComfyUI"
APP = (HOME / "AppData" / "Local" / "Programs" /
       "@comfyorgcomfyui-electron" / "resources" / "ComfyUI")
BASE = "http://127.0.0.1:8000"

SERVER_ARGV = [
    str(DOCS / ".venv" / "Scripts" / "python.exe"), str(APP / "main.py"),
    "--user-directory", str(DOCS / "user"),
    "--input-directory", str(DOCS / "input"),
    "--output-directory", str(DOCS / "output"),
    "--front-end-root", str(APP / "web_custom_versions" / "desktop_app"),
    "--base-directory", str(DOCS),
    "--database-url",
    "sqlite:///" + str(DOCS / "user" / "comfyui.db").replace("\\", "/"),
    "--extra-model-paths-config",
    str(HOME / "AppData" / "Roaming" / "ComfyUI" /
        "extra_models_config.yaml"),
    "--listen", "127.0.0.1", "--port", "8000", "--enable-manager",
]


def is_up(base: str = BASE, timeout: float = 3) -> bool:
    try:
        with urllib.request.urlopen(f"{base}/system_stats", timeout=timeout):
            return True
    except Exception:
        return False


def _default_spawn(argv):
    return subprocess.Popen(
        argv,
        creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP
                       | subprocess.DETACHED_PROCESS))


def ensure_server(spawn=None, wait_s: float = 240, probe=is_up,
                  _sleep=time.sleep) -> str:
    if probe():
        return "already-running"
    (spawn or _default_spawn)(SERVER_ARGV)
    deadline = time.monotonic() + wait_s
    while time.monotonic() < deadline:
        if probe():
            return "started"
        _sleep(3)
    raise TimeoutError(f"comfyui server not up within {wait_s}s")
