# ComfyUI Local Open-Source Gen Backend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing ComfyUI Desktop install a Claude-drivable local backend for open-weight video (Wan 2.2) and fast images (Z-Image-Turbo), per the approved spec `docs/superpowers/specs/2026-08-03-comfyui-local-gen-design.md`.

**Architecture:** A small pure-Python package `scripts/comfy/` (manifest → downloader → template parameterizer → HTTP client → headless launcher) talking to the already-verified local ComfyUI server API at `http://127.0.0.1:8000` (`POST /prompt`, `GET /history/{id}`, `GET /view`). Model files land in `C:\Users\imadq\Documents\ComfyUI\models\`. Workflow templates are authored against the live server's `/object_info` (never from memory) and validated by real renders.

**Tech Stack:** Python 3 (repo `scripts/` env: requests, pytest), Windows `curl.exe` for resumable downloads, ComfyUI Desktop 0.13.0 (core), ComfyUI-GGUF custom node (already installed).

## Global Constraints

- Sub-agents (if subagent-driven): `model: 'sonnet'` always — orchestrator only runs Fable (owner rule, CLAUDE.md §1.7).
- Commit hook forbids AI-attribution trailers ("Co-Authored-By: Claude…") — omit them; conventional-commit format enforced, subject ≤50 chars, body lines ≤72.
- Tests run from `C:\Users\imadq\AIInvestment\scripts`: `python -m pytest tests\test_comfy_*.py -v`.
- Never invent HF filenames or ComfyUI node class names. Filenames resolve live from the HF API (Task 1); node classes come from `GET /object_info` + the bundled native templates (Tasks 6–8). A pattern that doesn't match exactly one file is an error to fix, not to guess around.
- Every generated deliverable gets provenance: model files used, workflow JSON, `generated_at` UTC ISO-8601, `source_class: local-comfyui`.
- Disk: C: had 53 GB free at planning; total planned downloads ≈ 41 GB. Check free space before each download group; abort below 8 GB headroom.
- Licenses: everything in this plan is Apache 2.0 (Wan 2.2, Z-Image-Turbo, umt5 encoder repackages). HunyuanVideo is excluded (EU license territory), LTX-2 deferred — do not add them.
- The ComfyUI Desktop GUI and the headless server share port 8000 and a sqlite DB — never start one while the other runs. `ensure_server()` attaches if something is already listening.

---

### Task 1: Model manifest with live HF resolution

**Files:**
- Create: `scripts/comfy/__init__.py` (empty)
- Create: `scripts/comfy/manifest.py`
- Test: `scripts/tests/test_comfy_manifest.py`

**Interfaces:**
- Produces: `ModelFile(repo, pattern, dest_dir, approx_gb, group)`, `ResolvedFile(repo, rfile, size, dest_dir, group)` with `.url` and `.dest` properties, `resolve(entries=None, tree_fn=hf_tree) -> list[ResolvedFile]`, `ResolveError`, module global `COMFY_MODELS` (Path). Groups: `"video-5b" | "video-14b" | "image"`.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_comfy_manifest.py
import pytest

from comfy.manifest import ModelFile, ResolveError, resolve

FAKE_TREE = {
    "org/repo": [
        {"path": "split_files/vae/ae.safetensors", "size": 335_000_000},
        {"path": "split_files/diffusion_models/model_fp8.safetensors",
         "size": 6_000_000_000},
        {"path": "README.md", "size": 1000},
    ]
}


def fake_tree(repo):
    return FAKE_TREE[repo]


def test_resolve_exact_match():
    entries = [ModelFile("org/repo", r"vae/ae\.safetensors$", "vae", 0.3, "image")]
    got = resolve(entries, tree_fn=fake_tree)
    assert got[0].rfile == "split_files/vae/ae.safetensors"
    assert got[0].size == 335_000_000
    assert got[0].url == ("https://huggingface.co/org/repo/resolve/main/"
                          "split_files/vae/ae.safetensors")
    assert got[0].dest.name == "ae.safetensors"
    assert got[0].dest.parent.name == "vae"


def test_resolve_zero_matches_raises_and_lists_candidates():
    entries = [ModelFile("org/repo", r"nope\.gguf$", "unet", 1.0, "video-14b")]
    with pytest.raises(ResolveError) as e:
        resolve(entries, tree_fn=fake_tree)
    assert "README.md" in str(e.value)


def test_resolve_multi_match_raises():
    entries = [ModelFile("org/repo", r"safetensors$", "vae", 0.3, "image")]
    with pytest.raises(ResolveError):
        resolve(entries, tree_fn=fake_tree)
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `scripts/`): `python -m pytest tests\test_comfy_manifest.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'comfy'`

- [ ] **Step 3: Write the implementation**

Create empty `scripts/comfy/__init__.py`, then:

```python
# scripts/comfy/manifest.py
"""Model manifest for the local ComfyUI open-source gen backend.

Spec: docs/superpowers/specs/2026-08-03-comfyui-local-gen-design.md
approx_gb comes from the 2026-08-03 research sweep and is for reporting
only; real sizes are always fetched live from the HuggingFace API.
"""
from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path

COMFY_MODELS = Path.home() / "Documents" / "ComfyUI" / "models"
HF_TREE_URL = "https://huggingface.co/api/models/{repo}/tree/main?recursive=true"
UA = {"User-Agent": "AIInvestment-comfy-setup/1.0"}


@dataclass(frozen=True)
class ModelFile:
    repo: str        # HF repo id
    pattern: str     # regex against the full path inside the repo
    dest_dir: str    # subfolder of COMFY_MODELS
    approx_gb: float
    group: str       # "video-5b" | "video-14b" | "image"


@dataclass(frozen=True)
class ResolvedFile:
    repo: str
    rfile: str
    size: int        # exact bytes per HF API
    dest_dir: str
    group: str

    @property
    def url(self) -> str:
        return f"https://huggingface.co/{self.repo}/resolve/main/{self.rfile}"

    @property
    def dest(self) -> Path:
        import comfy.manifest as m  # late lookup so tests can monkeypatch
        return m.COMFY_MODELS / self.dest_dir / Path(self.rfile).name


MANIFEST: list[ModelFile] = [
    # --- video-5b: Wan 2.2 TI2V-5B + shared encoder/VAEs (Apache 2.0)
    ModelFile("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
              r"split_files/diffusion_models/wan2\.2_ti2v_5B_fp16\.safetensors$",
              "diffusion_models", 10.0, "video-5b"),
    ModelFile("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
              r"split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled\.safetensors$",
              "text_encoders", 6.74, "video-5b"),
    ModelFile("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
              r"split_files/vae/wan2\.2_vae\.safetensors$",
              "vae", 1.41, "video-5b"),
    ModelFile("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
              r"split_files/vae/wan_2\.1_vae\.safetensors$",
              "vae", 0.25, "video-5b"),
    # --- video-14b: Wan 2.2 I2V-A14B GGUF Q4_K_M + lightx2v 4-step LoRAs
    ModelFile("QuantStack/Wan2.2-I2V-A14B-GGUF",
              r"(?i)high[-_]?noise.*Q4_K_M\.gguf$",
              "unet", 9.65, "video-14b"),
    ModelFile("QuantStack/Wan2.2-I2V-A14B-GGUF",
              r"(?i)low[-_]?noise.*Q4_K_M\.gguf$",
              "unet", 9.65, "video-14b"),
    ModelFile("lightx2v/Wan2.2-Distill-Loras",
              r"wan2\.2_i2v_A14b_high_noise_lora_rank64_lightx2v_4step.*\.safetensors$",
              "loras", 0.64, "video-14b"),
    ModelFile("lightx2v/Wan2.2-Distill-Loras",
              r"wan2\.2_i2v_A14b_low_noise_lora_rank64_lightx2v_4step.*\.safetensors$",
              "loras", 0.74, "video-14b"),
    # --- image: Z-Image-Turbo (Apache 2.0)
    ModelFile("Comfy-Org/z_image_turbo",
              r"(?i)split_files/diffusion_models/.*fp8.*\.safetensors$",
              "diffusion_models", 6.15, "image"),
    ModelFile("Comfy-Org/z_image_turbo",
              r"(?i)split_files/text_encoders/qwen_3_4b.*fp8.*\.safetensors$",
              "text_encoders", 5.63, "image"),
    ModelFile("Comfy-Org/z_image_turbo",
              r"split_files/vae/ae\.safetensors$",
              "vae", 0.34, "image"),
]


class ResolveError(RuntimeError):
    pass


def hf_tree(repo: str) -> list[dict]:
    """Full file listing of a HF repo: [{'path':…, 'size':…}, …]."""
    req = urllib.request.Request(HF_TREE_URL.format(repo=repo), headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def resolve(entries=None, tree_fn=hf_tree) -> list[ResolvedFile]:
    """Match every manifest pattern against the live repo listing.

    Raises ResolveError (listing candidates) on 0 or >1 matches — fix
    the pattern from the candidate list; never guess a filename.
    """
    entries = MANIFEST if entries is None else entries
    trees: dict[str, list[dict]] = {}
    out: list[ResolvedFile] = []
    for e in entries:
        if e.repo not in trees:
            trees[e.repo] = [f for f in tree_fn(e.repo) if f.get("size")]
        hits = [f for f in trees[e.repo] if re.search(e.pattern, f["path"])]
        if len(hits) != 1:
            names = sorted(f["path"] for f in trees[e.repo])
            raise ResolveError(
                f"{e.repo}: pattern {e.pattern!r} matched "
                f"{[h['path'] for h in hits]}; repo files: {names}")
        out.append(ResolvedFile(e.repo, hits[0]["path"], hits[0]["size"],
                                e.dest_dir, e.group))
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests\test_comfy_manifest.py -v` — Expected: 3 PASS

- [ ] **Step 5: Live resolution check (real HF API, prints the actual plan)**

Run from `scripts/`:
`python -c "from comfy.manifest import resolve; [print(f'{r.group:9s} {r.size/1e9:6.2f}GB {r.rfile}') for r in resolve()]"`

Expected: 11 lines, each group's sizes within ~15% of `approx_gb`. If any pattern raises `ResolveError`, read the candidate list in the message and fix the pattern in `MANIFEST` (e.g. the Z-Image diffusion file may live in a sibling repo — research fallbacks: `drbaph/Z-Image-Turbo-FP8` or `Kijai/Z-Image_comfy_fp8_scaled`; if Comfy-Org's repo lacks an fp8 diffusion file, change that entry's `repo` to one of those and re-run). Re-run Step 4 after any edit.

- [ ] **Step 6: Commit**

```bash
git add scripts/comfy scripts/tests/test_comfy_manifest.py
git commit -m "feat(comfy): model manifest with live HF resolution"
```
(Body: what the manifest covers and why patterns resolve live.)

---

### Task 2: Resumable downloader + start the downloads

**Files:**
- Create: `scripts/comfy/download.py`
- Test: `scripts/tests/test_comfy_download.py`

**Interfaces:**
- Consumes: `comfy.manifest.resolve`, `ResolvedFile`.
- Produces: `fetch(rf, runner=run_curl) -> "present"|"downloaded"`, CLI `python -m comfy.download [--group G] [--list]`.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_comfy_download.py
from pathlib import Path

import pytest

import comfy.manifest as manifest
from comfy import download


def _rf(size):
    return manifest.ResolvedFile("o/r", "vae/x.safetensors", size, "vae", "image")


def test_fetch_skips_existing_exact_size(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "COMFY_MODELS", tmp_path)
    rf = _rf(4)
    rf.dest.parent.mkdir(parents=True)
    rf.dest.write_bytes(b"abcd")
    assert download.fetch(
        rf, runner=lambda u, p: pytest.fail("must not download")) == "present"


def test_fetch_downloads_verifies_and_renames(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "COMFY_MODELS", tmp_path)
    rf = _rf(4)

    def fake_curl(url, part):
        assert url == rf.url
        Path(part).write_bytes(b"abcd")
        return 0

    assert download.fetch(rf, runner=fake_curl) == "downloaded"
    assert rf.dest.read_bytes() == b"abcd"
    assert not rf.dest.with_suffix(rf.dest.suffix + ".part").exists()


def test_fetch_size_mismatch_raises_and_keeps_part(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "COMFY_MODELS", tmp_path)
    rf = _rf(9)

    def fake_curl(url, part):
        Path(part).write_bytes(b"abcd")
        return 0

    with pytest.raises(RuntimeError, match="size mismatch"):
        download.fetch(rf, runner=fake_curl)
    assert rf.dest.with_suffix(rf.dest.suffix + ".part").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests\test_comfy_download.py -v`
Expected: FAIL — `No module named 'comfy.download'`

- [ ] **Step 3: Write the implementation**

```python
# scripts/comfy/download.py
"""Resumable downloader for the model manifest.

Windows' bundled curl.exe with -C - (resume). Sequential on purpose:
polite to HF, and disk/net is the bottleneck anyway.

CLI (run from scripts/):
    python -m comfy.download --list
    python -m comfy.download --group video-5b
    python -m comfy.download                # everything
"""
from __future__ import annotations

import argparse
import subprocess
import sys

from .manifest import ResolvedFile, resolve


def run_curl(url: str, part) -> int:
    cmd = ["curl.exe", "-L", "--fail", "--retry", "3", "-C", "-",
           "-o", str(part), url]
    return subprocess.call(cmd)


def fetch(rf: ResolvedFile, runner=run_curl) -> str:
    dest = rf.dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size == rf.size:
        return "present"
    part = dest.with_suffix(dest.suffix + ".part")
    rc = runner(rf.url, part)
    if rc != 0:
        raise RuntimeError(f"curl exited {rc} for {rf.url}")
    got = part.stat().st_size
    if got != rf.size:
        raise RuntimeError(
            f"size mismatch for {dest.name}: got {got}, HF says {rf.size} "
            f"(.part kept; rerun to resume)")
    part.replace(dest)
    return "downloaded"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default=None)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    files = [f for f in resolve() if args.group in (None, f.group)]
    print(f"{len(files)} files, {sum(f.size for f in files)/1e9:.1f} GB total")
    if args.list:
        for f in files:
            print(f"  [{f.group}] {f.size/1e9:6.2f} GB  {f.dest}")
        return 0
    for f in files:
        print(f"-> {f.dest.name}", flush=True)
        print(f"   {fetch(f)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests\test_comfy_download.py tests\test_comfy_manifest.py -v` — Expected: 6 PASS

- [ ] **Step 5: Check disk, then start real downloads in the background**

`Get-PSDrive C` → free must be ≥ (total from `--list`) + 8 GB. Then launch **in background** (harness background facility), from `scripts/`:
1. `python -m comfy.download --group image` (~12 GB, finishes first — unblocks Task 6)
2. then `python -m comfy.download --group video-5b` (~18 GB)
3. then `python -m comfy.download --group video-14b` (~21 GB)

Sequential (one command chained with `;`) is fine and politer than parallel. Do not wait for completion — continue with Task 3; Tasks 6–8 each begin by confirming their group reports all `present`.

- [ ] **Step 6: Commit**

```bash
git add scripts/comfy/download.py scripts/tests/test_comfy_download.py
git commit -m "feat(comfy): resumable size-verified model downloader"
```

---

### Task 3: Template parameterizer

**Files:**
- Create: `scripts/comfy/templates.py`
- Create: `scripts/comfy/templates/` (dir; populated by Tasks 6–8)
- Test: `scripts/tests/test_comfy_templates.py`

**Interfaces:**
- Produces: `apply_params(workflow: dict, param_map: dict[str, tuple[str, str]], params: dict) -> dict` (pure, deep-copies), `load_template(name: str, **params) -> dict`, registry `PARAM_MAPS: dict[str, dict[str, tuple[str, str]]]` (Tasks 6–8 add entries), `TEMPLATES_DIR: Path`.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_comfy_templates.py
import pytest

from comfy import templates

WF = {"3": {"class_type": "KSampler", "inputs": {"seed": 1}},
      "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "old"}}}
PMAP = {"prompt": ("6", "text"), "seed": ("3", "seed")}


def test_apply_params_sets_values_without_mutating_original():
    out = templates.apply_params(WF, PMAP, {"prompt": "new", "seed": 42})
    assert out["6"]["inputs"]["text"] == "new"
    assert out["3"]["inputs"]["seed"] == 42
    assert WF["6"]["inputs"]["text"] == "old"


def test_apply_params_partial_params_ok():
    out = templates.apply_params(WF, PMAP, {"seed": 7})
    assert out["6"]["inputs"]["text"] == "old"
    assert out["3"]["inputs"]["seed"] == 7


def test_apply_params_unknown_param_raises():
    with pytest.raises(KeyError, match="unknown params"):
        templates.apply_params(WF, PMAP, {"nope": 1})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests\test_comfy_templates.py -v` — Expected: FAIL (no module)

- [ ] **Step 3: Write the implementation**

```python
# scripts/comfy/templates.py
"""Load and parameterize API-format ComfyUI workflow templates.

Templates are the JSON shape POST /prompt expects:
{node_id: {"class_type": …, "inputs": {…}}, …}. PARAM_MAPS names the
logical knobs a template exposes and where each lands (node_id, input);
entries are added as templates are authored against the live server.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

PARAM_MAPS: dict[str, dict[str, tuple[str, str]]] = {}


def apply_params(workflow: dict, param_map: dict, params: dict) -> dict:
    unknown = set(params) - set(param_map)
    if unknown:
        raise KeyError(f"unknown params {sorted(unknown)}; "
                       f"template exposes {sorted(param_map)}")
    wf = copy.deepcopy(workflow)
    for name, value in params.items():
        node_id, input_name = param_map[name]
        wf[node_id]["inputs"][input_name] = value
    return wf


def load_template(name: str, **params) -> dict:
    wf = json.loads((TEMPLATES_DIR / f"{name}.json").read_text("utf-8"))
    return apply_params(wf, PARAM_MAPS[name], params)
```

- [ ] **Step 4: Run tests** — Expected: 3 PASS

- [ ] **Step 5: Commit** — `feat(comfy): API-workflow template parameterizer`

---

### Task 4: ComfyUI HTTP client

**Files:**
- Create: `scripts/comfy/client.py`
- Test: `scripts/tests/test_comfy_client.py`

**Interfaces:**
- Consumes: `comfy.templates.load_template`.
- Produces: `ComfyClient(base="http://127.0.0.1:8000", http=None)` with `.submit(workflow) -> prompt_id: str`, `.wait(prompt_id, timeout=3600, poll=2.0) -> history_entry: dict`, `ComfyClient.outputs(entry) -> list[dict]`, `.fetch(item, dest_dir) -> Path`, `ComfyClient.stage_input(src) -> str` (copies into ComfyUI's input dir, returns bare name for LoadImage), `.generate(template, out_dir, timeout=3600, **params) -> list[Path]`; `ComfyError`.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_comfy_client.py
import json

import pytest

from comfy import client


class FakeResp:
    def __init__(self, status_code=200, payload=None, content=b""):
        self.status_code = status_code
        self._payload = payload
        self.content = content
        self.text = json.dumps(payload) if payload is not None else ""

    def json(self):
        return self._payload


class FakeHttp:
    def __init__(self):
        self.posts, self.gets = [], []
        self.post_queue, self.get_queue = [], []

    def post(self, url, **kw):
        self.posts.append((url, kw))
        return self.post_queue.pop(0)

    def get(self, url, **kw):
        self.gets.append(url)
        return self.get_queue.pop(0)


def test_submit_posts_prompt_and_returns_id():
    http = FakeHttp()
    http.post_queue = [FakeResp(200, {"prompt_id": "abc", "number": 1})]
    c = client.ComfyClient(http=http)
    assert c.submit({"1": {"class_type": "X", "inputs": {}}}) == "abc"
    url, kw = http.posts[0]
    assert url.endswith("/prompt")
    assert kw["json"]["prompt"] == {"1": {"class_type": "X", "inputs": {}}}


def test_submit_non_200_raises_with_body():
    http = FakeHttp()
    http.post_queue = [FakeResp(400, {"error": "bad node"})]
    with pytest.raises(client.ComfyError, match="bad node"):
        client.ComfyClient(http=http).submit({})


def test_wait_polls_until_completed():
    http = FakeHttp()
    done = {"abc": {"outputs": {},
                    "status": {"status_str": "success", "completed": True}}}
    http.get_queue = [FakeResp(200, {}), FakeResp(200, done)]
    entry = client.ComfyClient(http=http).wait("abc", timeout=5, poll=0.01)
    assert entry["status"]["completed"] is True


def test_wait_error_status_raises():
    http = FakeHttp()
    http.get_queue = [FakeResp(200, {"abc": {"status": {"status_str": "error",
                                                        "completed": False}}})]
    with pytest.raises(client.ComfyError):
        client.ComfyClient(http=http).wait("abc", timeout=5, poll=0.01)


def test_outputs_collects_all_media_kinds():
    entry = {"outputs": {"9": {"images": [{"filename": "a.png"}]},
                         "12": {"videos": [{"filename": "b.mp4"}]}}}
    assert [i["filename"] for i in client.ComfyClient.outputs(entry)] == \
        ["a.png", "b.mp4"]


def test_fetch_writes_file(tmp_path):
    http = FakeHttp()
    http.get_queue = [FakeResp(200, content=b"PNGDATA")]
    c = client.ComfyClient(http=http)
    p = c.fetch({"filename": "a.png", "subfolder": "", "type": "output"},
                tmp_path)
    assert p.read_bytes() == b"PNGDATA"
    assert "filename=a.png" in http.gets[0]
```

- [ ] **Step 2: Run test to verify it fails** — Expected: FAIL (no module)

- [ ] **Step 3: Write the implementation**

```python
# scripts/comfy/client.py
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
        COMFY_INPUT.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, COMFY_INPUT / src.name)
        return src.name

    def generate(self, template: str, out_dir, timeout: float = 3600,
                 **params) -> list[Path]:
        from .templates import load_template
        entry = self.wait(self.submit(load_template(template, **params)),
                          timeout=timeout)
        return [self.fetch(i, out_dir) for i in self.outputs(entry)]
```

- [ ] **Step 4: Run all comfy tests** — Expected: all PASS

- [ ] **Step 5: Live shape-check of the history contract**

The `status.completed` / `status_str` fields come from docs; verify the real server agrees (server must be running — it usually is; else `python -c "from comfy.launch import ensure_server"` after Task 5, or skip until Task 6 which renders for real):
`python -c "import requests; h=requests.get('http://127.0.0.1:8000/history', timeout=5).json(); import json; print(json.dumps(list(h.values())[-1].get('status', 'EMPTY-HISTORY'), indent=2)[:500] if h else 'EMPTY-HISTORY')"`
If the emitted structure differs from what `wait()` reads, fix `wait()` and the fake payloads in the test to match reality, re-run tests.

- [ ] **Step 6: Commit** — `feat(comfy): http client for local comfyui api`

---

### Task 5: Headless launcher

**Files:**
- Create: `scripts/comfy/launch.py`
- Test: `scripts/tests/test_comfy_launch.py`

**Interfaces:**
- Produces: `is_up(base=BASE, timeout=3) -> bool`, `ensure_server(spawn=None, wait_s=240, probe=is_up, _sleep=time.sleep) -> "already-running"|"started"`, `SERVER_ARGV: list[str]`.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_comfy_launch.py
import pytest

from comfy import launch


def test_attaches_when_already_up():
    got = launch.ensure_server(
        spawn=lambda argv: pytest.fail("must not spawn"), probe=lambda: True)
    assert got == "already-running"


def test_spawns_then_waits_until_probe_true():
    probes = iter([False, False, True])
    spawned = []
    got = launch.ensure_server(spawn=spawned.append,
                               probe=lambda: next(probes),
                               wait_s=10, _sleep=lambda s: None)
    assert got == "started"
    assert spawned == [launch.SERVER_ARGV]


def test_raises_when_server_never_comes_up():
    with pytest.raises(TimeoutError):
        launch.ensure_server(spawn=lambda argv: None, probe=lambda: False,
                             wait_s=0.01, _sleep=lambda s: None)
```

- [ ] **Step 2: Run test to verify it fails** — Expected: FAIL (no module)

- [ ] **Step 3: Write the implementation**

```python
# scripts/comfy/launch.py
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
```

- [ ] **Step 4: Run all comfy tests** — Expected: all PASS

- [ ] **Step 5: Live check** (only if the Desktop app is NOT currently running — check `is_up()` first; if up, attach counts as the pass):
`python -c "from comfy.launch import ensure_server; print(ensure_server())"` → `already-running` or `started`; then `python -c "from comfy.launch import is_up; print(is_up())"` → `True`.

- [ ] **Step 6: Commit** — `feat(comfy): headless server launcher with attach`

---

### Task 6: Z-Image-Turbo template + first real render

**Files:**
- Create: `scripts/comfy/templates/zimage_t2i.json`
- Modify: `scripts/comfy/templates.py` (add `PARAM_MAPS["zimage_t2i"]`)
- Test: `scripts/tests/test_comfy_live.py` (new, live-only smoke)

**Interfaces:**
- Consumes: everything from Tasks 1–5.
- Produces: template `zimage_t2i` with params `prompt, negative, seed, width, height`.

**Discovery procedure (do not write node JSON from memory):**

- [ ] **Step 1:** Confirm the image group is fully downloaded: from `scripts/`, `python -m comfy.download --group image` → every line `present`.

- [ ] **Step 2:** Server up (`ensure_server()`), then dump node metadata:
`python -c "import requests, json; oi=requests.get('http://127.0.0.1:8000/object_info', timeout=30).json(); open(r'..\data\object_info.json','w',encoding='utf-8').write(json.dumps(oi)); print(len(oi), 'node classes')"`
Then list candidates: `python -c "import json; oi=json.load(open(r'..\data\object_info.json',encoding='utf-8')); print([k for k in oi if 'image' in k.lower() and 'z' in k.lower() or 'zimage' in k.lower()])"` — and separately grep for `UNETLoader`, `CLIPLoader`, `VAELoader`, `KSampler`, `EmptySD3LatentImage`/`EmptyLatentImage`, `SaveImage`.

- [ ] **Step 3:** Find the bundled native Z-Image template for the exact intended graph and defaults (steps, cfg, sampler, shift):
`Get-ChildItem "$env:USERPROFILE\Documents\ComfyUI\.venv\Lib\site-packages\comfyui_workflow_templates*" -Recurse -Filter *.json | Where-Object Name -match 'z.?image' | Select-Object FullName`
Read the matching JSON (UI format: `nodes` array with `type` and `widgets_values`). For each node, `object_info[type]["input_order"]` gives the widget order → map `widgets_values` to named inputs; `links` give the connections (`[node_id, output_index]` refs in API format).

- [ ] **Step 4:** Hand-translate to API format at `scripts/comfy/templates/zimage_t2i.json` (dict of `node_id -> {class_type, inputs}`; connections as `["<other_node_id>", <output_index>]`). Set width/height 1024, steps/cfg/sampler exactly as the native template's defaults. Model filenames must be the exact basenames Task 1 resolved (check `models/diffusion_models/`, `models/text_encoders/`, `models/vae/`).

- [ ] **Step 5:** Add to `templates.py`:

```python
PARAM_MAPS["zimage_t2i"] = {
    "prompt":   ("<positive CLIPTextEncode node id>", "text"),
    "negative": ("<negative CLIPTextEncode node id>", "text"),
    "seed":     ("<sampler node id>", "seed"),   # or "noise_seed" — per object_info
    "width":    ("<latent node id>", "width"),
    "height":   ("<latent node id>", "height"),
}
```
(Replace ids/names with the real ones from your authored JSON — the unit tests in Task 3 already guard the mechanism.)

- [ ] **Step 6:** Validate by rendering — the server's own validation is the test; `node_errors` in a 400 response names the broken node/input, fix and repeat:
`python -c "from comfy.client import ComfyClient; print(ComfyClient().generate('zimage_t2i', r'..\data\comfy_smoke', prompt='macro photo of a brass telescope on a mahogany desk, window light', seed=7, width=1024, height=1024))"`
Expected: a PNG path in `data\comfy_smoke\` within ~60 s. Open/inspect it — it must actually depict the prompt.

- [ ] **Step 7:** Add the live smoke file:

```python
# scripts/tests/test_comfy_live.py
"""Live smoke tests — auto-skip when no local server is running."""
import pytest

from comfy import launch

pytestmark = pytest.mark.skipif(not launch.is_up(),
                                reason="local ComfyUI server not running")


def test_zimage_renders_a_png(tmp_path):
    from comfy.client import ComfyClient
    outs = ComfyClient().generate("zimage_t2i", tmp_path,
                                  prompt="a red cube on white background",
                                  seed=1, width=512, height=512)
    assert outs and outs[0].suffix == ".png" and outs[0].stat().st_size > 10_000
```

Run: `python -m pytest tests\test_comfy_live.py -v` — Expected: PASS (or SKIP if server down — then it must PASS with the server up before this task closes).

- [ ] **Step 8: Commit** — `feat(comfy): z-image-turbo t2i template, first local render`

---

### Task 7: Wan 2.2 TI2V-5B template (fast video, T2V+I2V)

**Files:**
- Create: `scripts/comfy/templates/wan22_ti2v_5b.json`
- Modify: `scripts/comfy/templates.py` (add `PARAM_MAPS["wan22_ti2v_5b"]`)
- Modify: `scripts/tests/test_comfy_live.py` (add one test)

**Interfaces:**
- Produces: template `wan22_ti2v_5b` with params `prompt, negative, seed, width, height, length` (frames) and optional `image` (staged input name → LoadImage; when set, the graph runs I2V).

- [ ] **Step 1:** `python -m comfy.download --group video-5b` → all `present`.
- [ ] **Step 2:** Locate the bundled native "Wan 2.2 5B" template (same `Get-ChildItem` technique, `-match 'wan.?2.?2'`); note which VAE file it references (**this resolves the 2.1-vs-2.2 VAE question — use exactly what the template uses**), the CLIPLoader type, the latent/video node (`Wan22ImageToVideoLatent` or similar per `object_info`), sampler defaults, shift, fps and the save node (`SaveVideo`/`SaveWEBM`/`CreateVideo` — whatever the template uses).
- [ ] **Step 3:** Translate to API JSON as in Task 6 Step 4. Default size: the template's native default (likely 1280×704); `length` default 49 frames for smoke (native 121).
- [ ] **Step 4:** Register `PARAM_MAPS["wan22_ti2v_5b"]` (ids from your JSON; same five params as Z-Image plus `length` and `image`).
- [ ] **Step 5:** Validate T2V mode with a small render (~640×352, 33 frames):
`python -c "from comfy.client import ComfyClient; print(ComfyClient().generate('wan22_ti2v_5b', r'..\data\comfy_smoke', prompt='steam rising from a coffee cup, slow camera push-in', seed=3, width=640, height=352, length=33, timeout=1800))"`
Expected: a video file; play/inspect frames (ffmpeg frame-dump per CLAUDE.md §10.7). Record wall-clock.
- [ ] **Step 6:** Validate I2V mode: `stage_input()` a real photo, set `image=<name>`, re-render, confirm the clip visibly starts from the photo.
- [ ] **Step 7:** Add live test (mirroring `test_zimage_renders_a_png`, asserting a video-suffix output > 100 KB, `length=17`, 448×256, `timeout=900`). Run: PASS.
- [ ] **Step 8: Commit** — `feat(comfy): wan2.2 ti2v-5b video template (t2v+i2v)`

---

### Task 8: Wan 2.2 I2V-A14B GGUF + lightx2v 4-step template (quality video)

**Files:**
- Create: `scripts/comfy/templates/wan22_i2v_14b.json`
- Modify: `scripts/comfy/templates.py` (add `PARAM_MAPS["wan22_i2v_14b"]`)
- Modify: `scripts/tests/test_comfy_live.py` (add one test)

**Interfaces:**
- Produces: template `wan22_i2v_14b` with params `prompt, negative, seed, width, height, length, image` (required — this is I2V only).

- [ ] **Step 1:** `python -m comfy.download --group video-14b` → all `present`.
- [ ] **Step 2:** Locate the bundled native "Wan 2.2 14B I2V" template. Structure to preserve: **two-expert MoE chain** — high-noise model handles early steps, low-noise handles late steps, chained via two `KSamplerAdvanced` nodes sharing one latent (first: add_noise enable, steps 0→N/2, return_with_leftover_noise enable; second: add_noise disable, steps N/2→N).
- [ ] **Step 3:** Adaptations to the native graph, validated against `object_info`:
  - Replace each diffusion loader with the GGUF loader from the installed ComfyUI-GGUF pack (find its exact class in `object_info` — search keys containing `gguf`, e.g. `UnetLoaderGGUF`), pointing at the two resolved `.gguf` basenames in `models/unet/`.
  - Insert one `LoraLoaderModelOnly` after each expert loader: high-noise LoRA on the high-noise model, low-noise LoRA on the low-noise model (exact basenames from Task 1's resolution), `strength_model` 1.0.
  - Distilled sampling start point (from the lightx2v research; tune by eye later): total steps 8 split 4/4, `cfg` 1.0, sampler `euler`, scheduler `simple`, keep the native template's `ModelSamplingSD3`/shift nodes and values.
  - VAE: whichever VAE file the native 14B template references (per Task 7 Step 2 finding).
- [ ] **Step 4:** Register `PARAM_MAPS["wan22_i2v_14b"]`.
- [ ] **Step 5:** Validate: stage a real still, render 832×480, `length=49`, `timeout=3600`. Inspect frames; record wall-clock and `nvidia-smi` peak VRAM during the run (`nvidia-smi --query-gpu=memory.used --format=csv -l 5` in background). If OOM: drop to 640×368 and note it; if far under VRAM budget, note headroom for Q5_K_M later.
- [ ] **Step 6:** Add live test (I2V with a tiny 33-frame 512×288 run, `timeout=1800`). Run: PASS.
- [ ] **Step 7: Commit** — `feat(comfy): wan2.2 i2v-14b gguf 4-step template`

---

### Task 9: Deliverable renders + benchmark report

**Files:**
- Create: `data/comfy_smoke/benchmark.md` (data/ is gitignored — this is evidence, `git add -f` it)

- [ ] **Step 1:** Three real deliverables at target quality, timing each and polling peak VRAM:
  1. `zimage_t2i` 1024×1024 still — a reel-relevant subject (e.g. "trading terminal glowing in a dark room, cinematic").
  2. `wan22_ti2v_5b` T2V at its native default res, 121 frames.
  3. `wan22_i2v_14b` at 832×480, 81 frames (~5 s), animating an existing project still (e.g. a `content/probe/` frame or `hormuz_cover.png`).
- [ ] **Step 2:** Write `benchmark.md`: per render — template, params, wall-clock, peak VRAM, output size, model files (exact basenames), `generated_at` UTC, `source_class: local-comfyui`. Note explicitly which research timing estimates held and which didn't.
- [ ] **Step 3:** `git add -f data/comfy_smoke/benchmark.md` + commit `docs(comfy): live benchmark of local gen stack`. **Orchestrator (not the task subagent) then uploads the three outputs via the Higgsfield media flow and posts CloudFront URLs to the owner** (house rule: show, don't describe).

---

### Task 10: torch cu130 upgrade (attempt-with-rollback)

**Files:**
- Create: `data/comfy_venv_freeze_pre_cu130.txt` (evidence, `git add -f`)

- [ ] **Step 1:** Snapshot: `& "$env:USERPROFILE\Documents\ComfyUI\.venv\Scripts\python.exe" -m pip freeze > data\comfy_venv_freeze_pre_cu130.txt` — verify it lists `torch==2.7.1+cu128`.
- [ ] **Step 2:** Stop the server cleanly. If the Desktop GUI is running (check for the `ComfyUI.exe` process), the owner must quit it — do not kill; if it's the headless server we spawned, terminate that python process.
- [ ] **Step 3:** `& ...python.exe -m pip install --upgrade torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu130` (≈3–4 GB download; background it).
- [ ] **Step 4:** `ensure_server()`, then check the startup log tail (`%APPDATA%\ComfyUI\logs\comfyui.log` or `Documents\ComfyUI\user\comfyui_8000.log`): the exact line `WARNING: You need pytorch with cu130 or higher` must be GONE, and a `comfy_kitchen backend cuda` line should show `available: True, disabled: False`.
- [ ] **Step 5:** Re-run the three live smokes (`python -m pytest tests\test_comfy_live.py -v`) and eyeball one Z-Image output against the pre-upgrade one (same seed) for gross corruption (the #10389 failure mode is crash-on-start or broken VAE output).
- [ ] **Step 6 (only on failure):** Rollback exactly: `& ...python.exe -m pip install torch==2.7.1+cu128 torchvision==<ver from freeze> torchaudio==<ver from freeze> --extra-index-url https://download.pytorch.org/whl/cu128`, re-run smokes, document the failure in benchmark.md.
- [ ] **Step 7:** Commit evidence + a note in benchmark.md: `chore(comfy): torch cu130 upgrade result`

---

### Task 11: ComfyUI core update (owner-assisted, non-blocking)

- [ ] **Step 1:** Check what the Desktop updater offers: `GET https://api.github.com/repos/Comfy-Org/desktop/releases/latest` (note version + bundled core if stated). The Manage/Update panel in the GUI is the supported path — there is no documented headless core-update command for Desktop.
- [ ] **Step 2:** Message the owner: one GUI action — open ComfyUI Desktop → Manage → Update (Stable). Everything already built keeps working on 0.13; the update unlocks Krea 2 (needs ≥0.26) and newer video templates.
- [ ] **Step 3 (after owner updates):** `GET /system_stats` → record new core version; re-run `python -m pytest tests\test_comfy_*.py -v` (unit + live). If the update moved/renamed anything the templates reference, fix and commit.

---

### Task 12: Documentation + memory

**Files:**
- Create: `references/comfyui-local.md`
- Modify: `CLAUDE.md` (one line in §7 map pointing to the new reference)
- Memory: `comfyui-local-backend.md` + index line in `MEMORY.md`

- [ ] **Step 1:** Write `references/comfyui-local.md`: what the backend is (third gen backend beside Higgsfield/grok); model inventory with licenses (all Apache 2.0) and groups; how to generate (`ComfyClient().generate(...)` examples for all three templates); headless start/attach rules (never race the Desktop GUI); measured benchmarks from Task 9; provenance conventions; what was excluded and why (Hunyuan EU license, LTX-2 VRAM, "Wan 2.7" fakes); torch/core upgrade status.
- [ ] **Step 2:** Add the map line in CLAUDE.md §7 (`references/comfyui-local.md ← local open-source gen backend (ComfyUI)`).
- [ ] **Step 3:** Write the memory file (type: project): ComfyUI Desktop = local OS gen backend; scripts/comfy client; Wan 2.2 + Z-Image installed; port 8000; GUI/headless mutual exclusion; link `[[reel-engine]]` `[[content-non-commercial]]`. Add the MEMORY.md line.
- [ ] **Step 4:** Final commit `docs(comfy): local gen backend reference + claude.md map line`.

---

## Self-review notes

- Spec coverage: Phase 1 → Tasks 1, 2, 6, 7, 8 (+9 verification); Phase 2 → Tasks 3, 4, 5; Phase 3 → Tasks 10, 11; docs/provenance → Task 12; Z-Image add-on → Task 6; disk guard → Task 2 Step 5; VAE question → Task 7 Step 2 (and consumed in Task 8 Step 3).
- Node-graph tasks (6–8) deliberately specify a *discovery procedure* (bundled native template + `/object_info` + server-side validation by real render) instead of literal node JSON — inventing class names from memory is the failure mode the spec forbids; the server's `node_errors` response is the corrective loop.
- Type consistency: `ResolvedFile.dest` late-binds `COMFY_MODELS` for the monkeypatched download tests; `generate()` param names match `PARAM_MAPS` registration; live tests all go through `launch.is_up` skip guard.
