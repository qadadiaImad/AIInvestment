"""Minimal client for the local ComfyUI server.

Canonical API (docs.comfy.org/development/comfyui-server/comms_routes):
POST /prompt, GET /history/{id}, GET /view. Server verified live on
127.0.0.1:8000 (ComfyUI Desktop, no auth) on 2026-08-03.
"""
from __future__ import annotations

import json
import shutil
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode

import requests

BASE = "http://127.0.0.1:8000"
COMFY_INPUT = Path.home() / "Documents" / "ComfyUI" / "input"


class ComfyError(RuntimeError):
    pass


class ComfyClient:
    def __init__(self, base: str = BASE, http=None):
        self.base = base
        self.http = http or requests.Session()
        self.client_id = uuid.uuid4().hex
        self._last_family = None

    def submit(self, workflow: dict) -> str:
        r = self.http.post(f"{self.base}/prompt",
                           json={"prompt": workflow,
                                 "client_id": self.client_id})
        if r.status_code != 200:
            raise ComfyError(f"/prompt HTTP {r.status_code}: {r.text[:2000]}")
        return r.json()["prompt_id"]

    def wait(self, prompt_id: str, timeout: float = 3600,
             poll: float = 2.0) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            r = self.http.get(f"{self.base}/history/{prompt_id}")
            entry = r.json().get(prompt_id) if r.status_code == 200 else None
            if entry:
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    raise ComfyError(json.dumps(status)[:3000])
                if status.get("completed"):
                    return entry
            time.sleep(poll)
        raise TimeoutError(f"prompt {prompt_id} not done after {timeout}s")

    @staticmethod
    def outputs(entry: dict) -> list[dict]:
        found: list[dict] = []
        for out in entry.get("outputs", {}).values():
            for key in ("images", "videos", "gifs", "audio"):
                found.extend(out.get(key, []))
        return found

    def fetch(self, item: dict, dest_dir) -> Path:
        q = urlencode({"filename": item["filename"],
                       "subfolder": item.get("subfolder", ""),
                       "type": item.get("type", "output")})
        r = self.http.get(f"{self.base}/view?{q}")
        if r.status_code != 200:
            raise ComfyError(f"/view HTTP {r.status_code} for {item}")
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        p = dest_dir / item["filename"]
        p.write_bytes(r.content)
        return p

    @staticmethod
    def stage_input(src) -> str:
        src = Path(src)
        if not src.exists():
            raise ComfyError(f"input file not found: {src}")
        COMFY_INPUT.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, COMFY_INPUT / src.name)
        return src.name

    def generate(self, template: str, out_dir, timeout: float = 3600,
                 **params) -> list[Path]:
        from .templates import load_template
        family = template.split("_", 1)[0]
        if self._last_family is not None and family != self._last_family:
            print(
                "WARNING: ComfyUI model family switch "
                f"({self._last_family} -> {family}) in one server process "
                "is a known VRAM-eviction corruption risk (static/black "
                "output, see task-8-report.md / references/comfyui-local.md) "
                "-- restart the ComfyUI server before this render."
            )
        self._last_family = family
        entry = self.wait(self.submit(load_template(template, **params)),
                          timeout=timeout)
        return [self.fetch(i, out_dir) for i in self.outputs(entry)]
