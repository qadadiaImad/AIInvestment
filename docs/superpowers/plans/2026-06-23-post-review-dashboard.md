# Post-Review Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A standalone local Flask web app (`review/`) that galleries the generated social posts (reels + carousels), shows each post's caption + audio/narration script, and lets the owner attach per-post tagged comments that persist to a git-tracked store which regeneration later reads.

**Architecture:** A Python Flask backend serves a no-build static frontend. Pure logic (post indexer, caption parser, comment store) is TDD'd with pytest; Flask exposes a small JSON API (`/api/posts`, `/api/comments`) plus a path-guarded `/media/<path>` file server. Comments live in `feedback/post_comments.json`; a `load_for_post()` helper + short doc notes in the generators close the regeneration feedback loop. The dashboard never regenerates.

**Tech Stack:** Python 3.14, Flask 3.x, pytest 8.x. Vanilla HTML/CSS/JS frontend (no bundler). Runs at `http://localhost:5005`.

**Spec:** `docs/superpowers/specs/2026-06-23-post-review-dashboard-design.md`

## Global Constraints

- All app code lives under `review/`; the comment store lives at `feedback/post_comments.json` (repo root). Run commands from the repo root unless a task says `cd review`.
- Repo root is the parent of `review/`. The app only **reads** `higgs/` + `content/`; it **reads/writes** only `feedback/post_comments.json`. Never write to `higgs/`, `content/`, or `web/`.
- `post_id` format is exactly `"<date>_<TICKER>_<kind>"`, e.g. `2026-06-22_NVDA_reel` (date `YYYY-MM-DD`, ticker uppercase, kind ∈ `reel`/`carousel`).
- `part` tag is exactly one of `caption`, `audio`, `visual`, `general`. `kind` is exactly one of `reel`, `carousel`.
- Excluded scratch filenames (never indexed): match `^(hero_|logo_|maya_|_)` or `voice_*.mp3` or `*_anim.mp4` or `*.json`.
- `audio_script` = the post's caption text for `reel` posts; `null` for `carousel` posts.
- Comment id format: `"c_" + 8 lowercase hex chars`. Store file shape: `{"version": 1, "comments": [...]}`. Missing store file is treated as empty (`{"version":1,"comments":[]}`).
- Media URLs in post records are repo-root-relative under the `/media/` prefix, e.g. `/media/higgs/reel_nvda_2026-06-22.mp4`.
- House style colors: background `#0A0D12`, text `#E8EDF2`, accent emerald `#34D399`. Educational/not-financial-advice framing only.
- Tests are pytest, run from `review/` (so imports resolve as `from index import ...`). Frontend has no build step.

---

## Task 0: Scaffold `review/` app + paths + Flask hello

**Files:**
- Create: `review/requirements.txt`
- Create: `review/paths.py`
- Create: `review/app.py`
- Create: `review/.gitignore`
- Create: `review/tests/__init__.py`
- Create: `review/tests/test_paths.py`

**Interfaces:**
- Produces: `paths.REPO_ROOT`, `paths.HIGGS`, `paths.CONTENT`, `paths.FEEDBACK_FILE` (all `pathlib.Path`); `app.create_app() -> flask.Flask` with a `GET /api/health` route returning `{"ok": True}`.

- [ ] **Step 1: Create `review/requirements.txt`**

```
flask==3.1.0
pytest==8.3.4
```

- [ ] **Step 2: Create `review/.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 3: Create `review/paths.py`**

```python
"""Filesystem anchors for the post-review app. review/ -> repo root is one level up."""
from __future__ import annotations

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HIGGS = REPO_ROOT / "higgs"
CONTENT = REPO_ROOT / "content"
FEEDBACK_FILE = REPO_ROOT / "feedback" / "post_comments.json"
```

- [ ] **Step 4: Create `review/tests/__init__.py`** (empty file)

```python
```

- [ ] **Step 5: Write the failing test `review/tests/test_paths.py`**

```python
import paths


def test_repo_root_is_parent_of_review():
    # paths.py lives in review/, so REPO_ROOT must contain a 'higgs' dir name in its tree anchor
    assert paths.HIGGS == paths.REPO_ROOT / "higgs"
    assert paths.CONTENT == paths.REPO_ROOT / "content"
    assert paths.FEEDBACK_FILE == paths.REPO_ROOT / "feedback" / "post_comments.json"
    # review/ is a direct child of REPO_ROOT
    assert (paths.REPO_ROOT / "review" / "paths.py").exists()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd review && python -m pytest tests/test_paths.py -v`
Expected: PASS (paths.py already written). If `flask`/`pytest` missing: `cd review && pip install -r requirements.txt` first.

- [ ] **Step 7: Create `review/app.py` (minimal factory + health route)**

```python
"""Post-review dashboard — Flask app factory and routes."""
from __future__ import annotations

from flask import Flask, jsonify


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", static_url_path="")

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5005, debug=True)
```

- [ ] **Step 8: Smoke test the factory**

Run: `cd review && python -c "from app import create_app; c=create_app().test_client(); r=c.get('/api/health'); print(r.status_code, r.get_json())"`
Expected: `200 {'ok': True}`

- [ ] **Step 9: Commit**

```bash
git add review/requirements.txt review/.gitignore review/paths.py review/app.py review/tests/__init__.py review/tests/test_paths.py
git commit -m "feat(review): scaffold flask post-review app + paths"
```

---

## Task 1: Caption-sheet parser (pure, TDD)

**Files:**
- Create: `review/captions.py`
- Create: `review/tests/test_captions.py`

**Interfaces:**
- Produces: `captions.parse_captions(text: str) -> dict[str, str]` — maps uppercase TICKER → caption/hashtags block. `{}` for empty/blank input.

- [ ] **Step 1: Write the failing test `review/tests/test_captions.py`**

```python
from captions import parse_captions

SAMPLE = """AI STACK — NARRATED REEL KIT (2026-06-22)
=============== REEL 1 — NVDA (AI CHIPS) ===============
File: reel_nvda_2026-06-22.mp4
Caption:
Every AI chip stock looks expensive except the biggest one.
Hashtags: #nvidia #nvda
=============== REEL 2 — IONQ (QUANTUM) ===============
Caption:
Quantum gets traded like one bet.
Hashtags: #ionq"""


def test_returns_caption_text_per_ticker():
    c = parse_captions(SAMPLE)
    assert "biggest one" in c["NVDA"]
    assert "#nvidia" in c["NVDA"]
    assert "one bet" in c["IONQ"]


def test_empty_input_returns_empty_dict():
    assert parse_captions("") == {}
    assert parse_captions("   \n  ") == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd review && python -m pytest tests/test_captions.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'captions'`

- [ ] **Step 3: Implement `review/captions.py`**

```python
"""Parse reel/post caption sheets: sections headed '=== ... — TICKER (..) ===',
returns { TICKER: 'caption + hashtags block' }."""
from __future__ import annotations

import re


def parse_captions(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if not text.strip():
        return out
    blocks = re.split(r"(?m)^={3,}.*$", text)
    heads = re.findall(r"(?m)^={3,}.*$", text)
    for i, head in enumerate(heads):
        m = re.search(r"—\s*([A-Z]{1,6})\b", head)
        if not m:
            continue
        body = (blocks[i + 1] if i + 1 < len(blocks) else "").strip()
        if body:
            out[m.group(1)] = body
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd review && python -m pytest tests/test_captions.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add review/captions.py review/tests/test_captions.py
git commit -m "feat(review): caption-sheet section parser, TDD"
```

---

## Task 2: Post indexer (pure, TDD)

**Files:**
- Create: `review/index.py`
- Create: `review/tests/test_index.py`

**Interfaces:**
- Consumes: nothing (pure; caption lookup is wired in Task 4's app layer, not here).
- Produces: `index.build_index(higgs_files: list[str], content_files: list[str]) -> list[dict]`. Each post dict: `{"post_id", "date", "ticker", "kind", "media": list[str]}` where `kind` ∈ `reel`/`carousel`, `media` entries are `/media/...` URLs, `post_id` = `"<date>_<TICKER>_<kind>"`. Sorted newest date first, then ticker. (Caption/audio_script are added later by the app layer, not by this function.)

- [ ] **Step 1: Write the failing test `review/tests/test_index.py`**

```python
from index import build_index


def test_groups_reel_with_its_slides_and_assigns_post_id():
    higgs = [
        "reel_nvda_2026-06-22.mp4",
        "reel_nvda_data.png", "reel_nvda_hook.png", "reel_nvda_takeaway.png",
        "v4_crm_1_hook.png", "v4_crm_2_data.png",
        "reels_2026-06-22.txt", "posts_2026-06-21.txt",
        "hero_nvda_2026-06-22.png", "logo_NVDA.png", "voice_nvda_2026-06-22.mp3",
        "_check_anim.png", "reels_manifest.json",  # all excluded
    ]
    content = ["carousel_2026-06-03/CRM/slide_1.html", "carousel_2026-06-03/CRM/brief.md"]
    posts = build_index(higgs, content)

    nvda = next(p for p in posts if p["ticker"] == "NVDA" and p["kind"] == "reel")
    assert nvda["post_id"] == "2026-06-22_NVDA_reel"
    assert nvda["date"] == "2026-06-22"
    assert any(m.endswith("reel_nvda_2026-06-22.mp4") for m in nvda["media"])
    assert any("reel_nvda_data.png" in m for m in nvda["media"])
    assert all(m.startswith("/media/") for m in nvda["media"])
    # scratch excluded
    assert not any(("hero_" in m or "logo_" in m or "voice_" in m or "_check" in m)
                   for m in nvda["media"])

    # v4 image carousel becomes a carousel post for CRM
    assert any(p["ticker"] == "CRM" and p["kind"] == "carousel" for p in posts)
    # content HTML carousel becomes a carousel post for CRM (2026-06-03)
    assert any(p["post_id"] == "2026-06-03_CRM_carousel" for p in posts)


def test_sorted_newest_date_first():
    posts = build_index(["reel_ionq_2026-06-21.mp4", "reel_nvda_2026-06-22.mp4"], [])
    assert posts[0]["date"] >= posts[-1]["date"]


def test_post_id_shape():
    posts = build_index(["reel_adbe_2026-06-22.mp4"], [])
    assert posts[0]["post_id"] == "2026-06-22_ADBE_reel"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd review && python -m pytest tests/test_index.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'index'`

- [ ] **Step 3: Implement `review/index.py`**

```python
"""Group higgs/ + content/ filenames into post bundles for the review gallery.

Pure: takes filename lists, returns post dicts. Caption/audio_script are added by the
app layer (it reads the caption sheets); this function only does grouping + media + ids.
"""
from __future__ import annotations

import re

_EXCLUDE = re.compile(r"^(hero_|logo_|maya_|_)|voice_.*\.mp3$|_anim\.mp4$|\.json$", re.I)


def _media(rel: str) -> str:
    return f"/media/{rel}"


def build_index(higgs_files: list[str], content_files: list[str]) -> list[dict]:
    by_key: dict[str, dict] = {}
    v4_slides: list[tuple[str, str]] = []  # (TICKER, filename) — date unknown until grouped

    def ensure(date: str, ticker: str, kind: str) -> dict:
        key = f"{date}|{ticker}|{kind}"
        if key not in by_key:
            by_key[key] = {
                "post_id": f"{date}_{ticker}_{kind}",
                "date": date, "ticker": ticker, "kind": kind, "media": [],
            }
        return by_key[key]

    for f in higgs_files:
        if _EXCLUDE.search(f):
            continue
        m = re.match(r"^reel_([a-z]+)_(\d{4}-\d{2}-\d{2})\.mp4$", f, re.I)
        if m:
            p = ensure(m.group(2), m.group(1).upper(), "reel")
            p["media"].insert(0, _media(f"higgs/{f}"))
            continue
        m = re.match(r"^v4_([a-z]+)_\d_[a-z]+\.png$", f, re.I)
        if m:
            v4_slides.append((m.group(1).upper(), f))
            continue
        # reel slide frames reel_<tk>_<word>.png (no date) attach to that ticker's reel later
        m = re.match(r"^reel_([a-z]+)_([a-z]+)\.png$", f, re.I)
        if m:
            v4_slides.append((m.group(1).upper(), f))  # reuse the "attach to ticker's newest" path
            continue

    # content/carousel_<date>/<TK>/...  -> one carousel post per (date, ticker)
    seen_content: set[str] = set()
    for f in content_files:
        m = re.match(r"^carousel_(\d{4}-\d{2}-\d{2})/([A-Za-z]+)/", f)
        if not m:
            continue
        date, tk = m.group(1), m.group(2).upper()
        ck = f"{date}|{tk}"
        if ck in seen_content:
            continue
        seen_content.add(ck)
        p = ensure(date, tk, "carousel")
        p["media"].append(_media(f"content/carousel_{date}/{tk}/slide_1.html"))

    # attach v4/reel-slide pngs to that ticker's newest bundle (prefer a reel bundle)
    for ticker, fname in v4_slides:
        candidates = [p for p in by_key.values() if p["ticker"] == ticker]
        if not candidates:
            # no reel/carousel yet for this ticker -> create a carousel post keyed by a
            # synthetic date so v4 image sets still appear; date unknown -> use "0000-00-00"
            # so they sort last but remain visible.
            p = ensure("0000-00-00", ticker, "carousel")
        else:
            p = sorted(candidates, key=lambda x: x["date"], reverse=True)[0]
        p["media"].append(_media(f"higgs/{fname}"))

    posts = list(by_key.values())
    posts.sort(key=lambda p: (p["date"], p["ticker"]), reverse=False)
    posts.reverse()  # newest date first; ties broken by reverse ticker -> fix to ascending ticker
    posts.sort(key=lambda p: (_neg_date(p["date"]), p["ticker"]))
    return posts


def _neg_date(date: str) -> str:
    # invert date string ordering so newest sorts first while ticker sorts ascending
    return "".join(chr(255 - ord(c)) for c in date)
```

> Note: the double-sort above is intentional — the final `posts.sort(key=lambda p: (_neg_date(p["date"]), p["ticker"]))` is the authoritative order (newest date first, ticker ascending). The earlier `sort`/`reverse` lines are dead and MUST be removed. Final form of the return block:
> ```python
>     posts = list(by_key.values())
>     posts.sort(key=lambda p: (_neg_date(p["date"]), p["ticker"]))
>     return posts
> ```
> Apply this corrected version (delete the two stray sort/reverse lines).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd review && python -m pytest tests/test_index.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add review/index.py review/tests/test_index.py
git commit -m "feat(review): post indexer (filenames -> post bundles), TDD"
```

---

## Task 3: Comment store (pure ops + IO, TDD)

**Files:**
- Create: `review/comments.py`
- Create: `review/tests/test_comments.py`

**Interfaces:**
- Produces:
  - `comments.empty_store() -> dict` → `{"version":1,"comments":[]}`
  - `comments.add_comment(store, post_id, part, text, now, *, _id=None) -> tuple[dict, dict]` → `(store, comment)`. Raises `ValueError` on bad `part` or empty `text`. `now` is an ISO8601 string. `_id` is a test seam (default: generated `"c_"+8 hex`).
  - `comments.set_resolved(store, comment_id, resolved) -> dict` (raises `KeyError` if absent)
  - `comments.edit_comment(store, comment_id, text) -> dict` (raises `KeyError`/`ValueError`)
  - `comments.delete_comment(store, comment_id) -> dict` (raises `KeyError`)
  - `comments.load_for_post(store, post_id, only_open=True) -> list[dict]` — **regeneration entry point**
  - `comments.read_store(path) -> dict` (missing file → `empty_store()`); `comments.write_store(path, store) -> None` (atomic; creates parent dir)

- [ ] **Step 1: Write the failing test `review/tests/test_comments.py`**

```python
import json

import pytest

import comments


def test_add_and_load_for_post():
    s = comments.empty_store()
    s, c = comments.add_comment(s, "2026-06-22_NVDA_reel", "audio", "slow the open",
                                "2026-06-23T09:00:00Z", _id="c_00000001")
    assert c["id"] == "c_00000001"
    assert c["part"] == "audio"
    assert c["resolved"] is False
    got = comments.load_for_post(s, "2026-06-22_NVDA_reel")
    assert len(got) == 1 and got[0]["text"] == "slow the open"


def test_add_rejects_bad_part_and_empty_text():
    s = comments.empty_store()
    with pytest.raises(ValueError):
        comments.add_comment(s, "p", "loudness", "x", "now")
    with pytest.raises(ValueError):
        comments.add_comment(s, "p", "caption", "   ", "now")


def test_resolve_hides_from_open_load():
    s = comments.empty_store()
    s, c = comments.add_comment(s, "p1", "general", "fix", "now", _id="c_aaaa0001")
    s = comments.set_resolved(s, "c_aaaa0001", True)
    assert comments.load_for_post(s, "p1", only_open=True) == []
    assert len(comments.load_for_post(s, "p1", only_open=False)) == 1


def test_edit_and_delete():
    s = comments.empty_store()
    s, c = comments.add_comment(s, "p1", "visual", "old", "now", _id="c_aaaa0002")
    s = comments.edit_comment(s, "c_aaaa0002", "new")
    assert comments.load_for_post(s, "p1")[0]["text"] == "new"
    s = comments.delete_comment(s, "c_aaaa0002")
    assert comments.load_for_post(s, "p1") == []
    with pytest.raises(KeyError):
        comments.set_resolved(s, "c_missing", True)


def test_read_missing_store_is_empty(tmp_path):
    p = tmp_path / "feedback" / "post_comments.json"
    assert comments.read_store(p) == comments.empty_store()


def test_write_then_read_roundtrip(tmp_path):
    p = tmp_path / "feedback" / "post_comments.json"
    s = comments.empty_store()
    s, _ = comments.add_comment(s, "p1", "caption", "hi", "now", _id="c_aaaa0003")
    comments.write_store(p, s)
    assert json.loads(p.read_text("utf-8"))["comments"][0]["text"] == "hi"
    assert comments.read_store(p) == s
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd review && python -m pytest tests/test_comments.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'comments'`

- [ ] **Step 3: Implement `review/comments.py`**

```python
"""Comment store for the post-review dashboard.

Pure dict operations (unit-tested) + thin atomic file IO. `load_for_post` is the
reader the regeneration flow uses to fold open comments into a generation prompt.
"""
from __future__ import annotations

import json
import os
import pathlib
import secrets

VALID_PARTS = {"caption", "audio", "visual", "general"}


def empty_store() -> dict:
    return {"version": 1, "comments": []}


def _new_id() -> str:
    return "c_" + secrets.token_hex(4)


def add_comment(store, post_id, part, text, now, *, _id=None):
    if part not in VALID_PARTS:
        raise ValueError(f"bad part {part!r}; must be one of {sorted(VALID_PARTS)}")
    if not text or not text.strip():
        raise ValueError("comment text is empty")
    comment = {
        "id": _id or _new_id(),
        "post_id": post_id,
        "part": part,
        "text": text.strip(),
        "created_at": now,
        "resolved": False,
    }
    store = {**store, "comments": [*store["comments"], comment]}
    return store, comment


def _find(store, comment_id):
    for c in store["comments"]:
        if c["id"] == comment_id:
            return c
    raise KeyError(comment_id)


def set_resolved(store, comment_id, resolved):
    _find(store, comment_id)
    return {**store, "comments": [
        {**c, "resolved": bool(resolved)} if c["id"] == comment_id else c
        for c in store["comments"]
    ]}


def edit_comment(store, comment_id, text):
    _find(store, comment_id)
    if not text or not text.strip():
        raise ValueError("comment text is empty")
    return {**store, "comments": [
        {**c, "text": text.strip()} if c["id"] == comment_id else c
        for c in store["comments"]
    ]}


def delete_comment(store, comment_id):
    _find(store, comment_id)
    return {**store, "comments": [c for c in store["comments"] if c["id"] != comment_id]}


def load_for_post(store, post_id, only_open=True):
    return [c for c in store["comments"]
            if c["post_id"] == post_id and (not only_open or not c["resolved"])]


def read_store(path) -> dict:
    path = pathlib.Path(path)
    if not path.exists():
        return empty_store()
    try:
        data = json.loads(path.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty_store()
    data.setdefault("version", 1)
    data.setdefault("comments", [])
    return data


def write_store(path, store) -> None:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(store, indent=2), encoding="utf-8")
    os.replace(tmp, path)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd review && python -m pytest tests/test_comments.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Add the regeneration CLI to `review/comments.py`** (append at end)

```python
def _cli(argv=None) -> int:
    import sys
    from paths import FEEDBACK_FILE
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python -m comments <post_id>")
        return 2
    store = read_store(FEEDBACK_FILE)
    open_comments = load_for_post(store, args[0], only_open=True)
    if not open_comments:
        print(f"(no open comments for {args[0]})")
        return 0
    print(f"OPEN COMMENTS for {args[0]} (fold these into the regeneration prompt):")
    for c in open_comments:
        print(f"  - [{c['part']}] {c['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
```

- [ ] **Step 6: Verify the CLI runs**

Run: `cd review && python comments.py 2026-06-22_NVDA_reel`
Expected: prints `(no open comments for 2026-06-22_NVDA_reel)` (store is empty/absent), exit 0.

- [ ] **Step 7: Commit**

```bash
git add review/comments.py review/tests/test_comments.py
git commit -m "feat(review): comment store (pure ops + atomic IO) + regen CLI, TDD"
```

---

## Task 4: Wire the API — `/api/posts`, `/api/comments`, `/media`

**Files:**
- Modify: `review/app.py`
- Create: `review/tests/test_api.py`

**Interfaces:**
- Consumes: `index.build_index`, `captions.parse_captions`, `comments.*`, `paths.*`.
- Produces (routes): `GET /api/posts`, `GET /api/comments[?post_id=]`, `POST /api/comments`, `PATCH /api/comments/<id>`, `DELETE /api/comments/<id>`, `GET /media/<path:rel>`. `GET /api/posts` returns post dicts enriched with `caption`, `audio_script`, `comment_count`, `open_comment_count`.

- [ ] **Step 1: Write the failing test `review/tests/test_api.py`**

```python
import pytest

import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    # isolate the comment store to a temp file
    monkeypatch.setattr(app_module, "FEEDBACK_FILE", tmp_path / "feedback" / "post_comments.json")
    return app_module.create_app().test_client()


def test_posts_endpoint_returns_list(client):
    r = client.get("/api/posts")
    assert r.status_code == 200
    body = r.get_json()
    assert isinstance(body, list)
    # the repo's real reels should appear (NVDA reel dated 2026-06-22)
    assert any(p["post_id"].endswith("_NVDA_reel") for p in body)
    nvda = next(p for p in body if p["post_id"].endswith("_NVDA_reel"))
    assert nvda["kind"] == "reel"
    assert "audio_script" in nvda and "caption" in nvda
    assert nvda["open_comment_count"] == 0


def test_comment_crud_flow(client):
    r = client.post("/api/comments", json={"post_id": "2026-06-22_NVDA_reel",
                                           "part": "audio", "text": "slow the open"})
    assert r.status_code == 201
    cid = r.get_json()["id"]

    r = client.get("/api/comments?post_id=2026-06-22_NVDA_reel")
    assert len(r.get_json()) == 1

    r = client.patch(f"/api/comments/{cid}", json={"resolved": True})
    assert r.status_code == 200 and r.get_json()["resolved"] is True

    r = client.delete(f"/api/comments/{cid}")
    assert r.status_code == 200
    assert client.get("/api/comments?post_id=2026-06-22_NVDA_reel").get_json() == []


def test_comment_validation(client):
    assert client.post("/api/comments", json={"post_id": "p", "part": "bad", "text": "x"}).status_code == 400
    assert client.post("/api/comments", json={"post_id": "p", "part": "caption", "text": " "}).status_code == 400


def test_media_serves_real_reel_and_blocks_traversal(client):
    r = client.get("/media/higgs/reel_nvda_2026-06-22.mp4")
    assert r.status_code == 200
    bad = client.get("/media/../../etc/passwd")
    assert bad.status_code in (400, 403, 404)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd review && python -m pytest tests/test_api.py -v`
Expected: FAIL — routes/`FEEDBACK_FILE` not defined on `app` module.

- [ ] **Step 3: Rewrite `review/app.py` with the full API**

```python
"""Post-review dashboard — Flask app factory and routes."""
from __future__ import annotations

import datetime
import os
import pathlib

from flask import Flask, abort, jsonify, request, send_file

import comments
import index
from captions import parse_captions
from paths import CONTENT, FEEDBACK_FILE, HIGGS, REPO_ROOT


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _list_higgs() -> list[str]:
    return [p.name for p in HIGGS.iterdir() if p.is_file()] if HIGGS.exists() else []


def _list_content() -> list[str]:
    out: list[str] = []
    if CONTENT.exists():
        for p in CONTENT.rglob("*"):
            if p.is_file():
                out.append(p.relative_to(CONTENT).as_posix())
    return out


def _caption_for(post: dict) -> str | None:
    date, ticker, kind = post["date"], post["ticker"], post["kind"]
    primary = f"reels_{date}.txt" if kind == "reel" else f"posts_{date}.txt"
    fallback = f"posts_{date}.txt" if kind == "reel" else f"reels_{date}.txt"
    for name in (primary, fallback):
        f = HIGGS / name
        if f.exists():
            parsed = parse_captions(f.read_text("utf-8"))
            if ticker in parsed:
                return parsed[ticker]
    return None


def _build_posts() -> list[dict]:
    posts = index.build_index(_list_higgs(), _list_content())
    store = comments.read_store(FEEDBACK_FILE)
    for p in posts:
        cap = _caption_for(p)
        p["caption"] = cap
        p["audio_script"] = cap if p["kind"] == "reel" else None
        all_c = comments.load_for_post(store, p["post_id"], only_open=False)
        open_c = [c for c in all_c if not c["resolved"]]
        p["comment_count"] = len(all_c)
        p["open_comment_count"] = len(open_c)
    return posts


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", static_url_path="")

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/api/posts")
    def posts():
        return jsonify(_build_posts())

    @app.get("/api/comments")
    def get_comments():
        store = comments.read_store(FEEDBACK_FILE)
        post_id = request.args.get("post_id")
        items = (comments.load_for_post(store, post_id, only_open=False)
                 if post_id else store["comments"])
        return jsonify(items)

    @app.post("/api/comments")
    def post_comment():
        body = request.get_json(silent=True) or {}
        try:
            store = comments.read_store(FEEDBACK_FILE)
            store, c = comments.add_comment(
                store, body.get("post_id", ""), body.get("part", ""),
                body.get("text", ""), _now())
        except (ValueError, KeyError) as e:
            abort(400, str(e))
        comments.write_store(FEEDBACK_FILE, store)
        return jsonify(c), 201

    @app.patch("/api/comments/<cid>")
    def patch_comment(cid):
        body = request.get_json(silent=True) or {}
        store = comments.read_store(FEEDBACK_FILE)
        try:
            if "resolved" in body:
                store = comments.set_resolved(store, cid, body["resolved"])
            if "text" in body:
                store = comments.edit_comment(store, cid, body["text"])
        except KeyError:
            abort(404)
        except ValueError as e:
            abort(400, str(e))
        comments.write_store(FEEDBACK_FILE, store)
        updated = next(c for c in store["comments"] if c["id"] == cid)
        return jsonify(updated)

    @app.delete("/api/comments/<cid>")
    def delete_comment(cid):
        store = comments.read_store(FEEDBACK_FILE)
        try:
            store = comments.delete_comment(store, cid)
        except KeyError:
            abort(404)
        comments.write_store(FEEDBACK_FILE, store)
        return jsonify({"ok": True})

    @app.get("/media/<path:rel>")
    def media(rel):
        root = REPO_ROOT.resolve()
        target = (root / rel).resolve()
        if target != root and root not in target.parents:
            abort(403)
        if not target.is_file():
            abort(404)
        return send_file(target, conditional=True)

    @app.get("/")
    def home():
        return app.send_static_file("index.html")

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5005, debug=True)
```

> Note: `FEEDBACK_FILE` is imported at module scope so the test's `monkeypatch.setattr(app_module, "FEEDBACK_FILE", ...)` rebinds the name the route functions close over. Keep the `from paths import ... FEEDBACK_FILE ...` import (do not access it as `paths.FEEDBACK_FILE` inside routes).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd review && python -m pytest tests/test_api.py -v`
Expected: PASS (4 tests). If `/` static test noise appears, ignore — `index.html` arrives in Task 5.

- [ ] **Step 5: Run the full suite**

Run: `cd review && python -m pytest -v`
Expected: all tests PASS (paths + captions + index + comments + api).

- [ ] **Step 6: Commit**

```bash
git add review/app.py review/tests/test_api.py
git commit -m "feat(review): JSON API — posts/comments CRUD + guarded /media"
```

---

## Task 5: Static frontend (gallery + detail + comments)

**Files:**
- Create: `review/static/index.html`
- Create: `review/static/styles.css`
- Create: `review/static/app.js`

**Interfaces:**
- Consumes: `GET /api/posts`, `GET/POST/PATCH/DELETE /api/comments`, `GET /media/...`.
- Produces: the single-page dashboard UI. No exported JS interface (browser entry only).

- [ ] **Step 1: Create `review/static/index.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Post Review</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <header>
      <span class="brand">POST REVIEW</span>
      <span class="filters">
        <select id="filter-date"></select>
        <select id="filter-ticker"></select>
        <button id="refresh">Refresh</button>
      </span>
    </header>
    <main>
      <section id="gallery"></section>
      <aside id="detail" hidden></aside>
    </main>
    <footer>Educational / market-commentary only — not financial advice.</footer>
    <script src="app.js"></script>
  </body>
</html>
```

- [ ] **Step 2: Create `review/static/styles.css`**

```css
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: #0A0D12; color: #E8EDF2;
  font-family: Inter, system-ui, sans-serif; }
header { height: 56px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 18px; border-bottom: 1px solid rgba(255,255,255,.1); }
.brand { font-family: 'JetBrains Mono', monospace; letter-spacing: .2em; color: #34D399; }
.filters select, .filters button, .add button, .add select, .add textarea {
  background: rgba(255,255,255,.06); color: #E8EDF2; border: 1px solid rgba(255,255,255,.12);
  border-radius: 6px; padding: 6px 10px; font: inherit; }
main { display: flex; height: calc(100vh - 56px - 32px); }
#gallery { flex: 1; overflow: auto; padding: 18px; }
.daygroup > h2 { font-family: 'JetBrains Mono', monospace; font-size: 12px;
  letter-spacing: .2em; color: #34D399; margin: 18px 4px 10px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 14px; }
.tile { text-align: left; cursor: pointer; border: 1px solid rgba(255,255,255,.1);
  border-radius: 12px; overflow: hidden; background: rgba(255,255,255,.04); padding: 0; color: inherit; }
.tile:hover { border-color: rgba(52,211,153,.6); }
.tile .thumb { aspect-ratio: 4/5; background: #000; display: flex; align-items: center;
  justify-content: center; color: rgba(255,255,255,.3); }
.tile .thumb img, .tile .thumb video { width: 100%; height: 100%; object-fit: cover; }
.tile .meta { display: flex; justify-content: space-between; padding: 8px 10px;
  font-family: 'JetBrains Mono', monospace; font-size: 13px; }
.badge { background: #34D399; color: #04130d; border-radius: 999px; padding: 0 7px;
  font-size: 11px; font-weight: 700; }
#detail { width: 440px; border-left: 1px solid rgba(255,255,255,.1); overflow: auto;
  padding: 18px; background: #0B0E14; }
#detail h3 { margin: 0 0 6px; font-family: 'JetBrains Mono', monospace; }
#detail video, #detail img.slide { width: 100%; border-radius: 8px; margin-bottom: 10px; }
.label { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: .18em;
  color: #34D399; margin: 14px 0 6px; }
.block { background: rgba(255,255,255,.05); border-radius: 8px; padding: 10px;
  white-space: pre-wrap; font-size: 13px; line-height: 1.45; }
.comment { border: 1px solid rgba(255,255,255,.1); border-radius: 8px; padding: 8px;
  margin-bottom: 8px; }
.comment.resolved { opacity: .5; }
.comment .row { display: flex; gap: 8px; align-items: center; font-size: 11px;
  color: rgba(255,255,255,.5); font-family: 'JetBrains Mono', monospace; }
.chip { background: rgba(52,211,153,.18); color: #34D399; border-radius: 4px; padding: 0 6px; }
.add { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
.add textarea { min-height: 64px; resize: vertical; }
footer { height: 32px; display: flex; align-items: center; padding: 0 18px;
  font-size: 11px; color: rgba(255,255,255,.4); border-top: 1px solid rgba(255,255,255,.1); }
button { cursor: pointer; }
```

- [ ] **Step 3: Create `review/static/app.js`**

```javascript
const $ = (s, el = document) => el.querySelector(s);
let POSTS = [];
let SELECTED = null;

async function load() {
  POSTS = await (await fetch("/api/posts")).json();
  buildFilters();
  renderGallery();
}

function buildFilters() {
  const dates = ["all", ...new Set(POSTS.map((p) => p.date))];
  const tks = ["all", ...new Set(POSTS.map((p) => p.ticker))];
  $("#filter-date").innerHTML = dates.map((d) => `<option>${d}</option>`).join("");
  $("#filter-ticker").innerHTML = tks.map((t) => `<option>${t}</option>`).join("");
}

function shown() {
  const d = $("#filter-date").value, t = $("#filter-ticker").value;
  return POSTS.filter((p) => (d === "all" || p.date === d) && (t === "all" || p.ticker === t));
}

function thumb(p) {
  const mp4 = p.media.find((m) => m.endsWith(".mp4"));
  const png = p.media.find((m) => m.endsWith(".png"));
  if (mp4) return `<video src="${mp4}" muted preload="metadata"></video>`;
  if (png) return `<img src="${png}" alt="${p.ticker}" />`;
  return `<span>${p.kind}</span>`;
}

function renderGallery() {
  const groups = {};
  for (const p of shown()) (groups[p.date] ??= []).push(p);
  const dates = Object.keys(groups).sort().reverse();
  $("#gallery").innerHTML = dates.map((date) => `
    <div class="daygroup"><h2>${date}</h2><div class="grid">
      ${groups[date].map((p) => `
        <button class="tile" data-id="${p.post_id}">
          <div class="thumb">${thumb(p)}</div>
          <div class="meta"><b>${p.ticker}</b><span>${p.kind}${
            p.open_comment_count ? ` <span class="badge">${p.open_comment_count}</span>` : ""
          }</span></div>
        </button>`).join("")}
    </div></div>`).join("");
  for (const b of document.querySelectorAll(".tile"))
    b.onclick = () => select(b.dataset.id);
}

async function select(postId) {
  SELECTED = POSTS.find((p) => p.post_id === postId);
  await renderDetail();
}

async function renderDetail() {
  const p = SELECTED;
  const det = $("#detail");
  det.hidden = false;
  const mp4 = p.media.find((m) => m.endsWith(".mp4"));
  const slides = p.media.filter((m) => m.endsWith(".png"));
  const cs = await (await fetch(`/api/comments?post_id=${encodeURIComponent(p.post_id)}`)).json();
  det.innerHTML = `
    <h3>${p.ticker} · ${p.kind} <span style="color:#888">${p.date}</span></h3>
    ${mp4 ? `<video src="${mp4}" controls></video>`
          : slides.map((s) => `<img class="slide" src="${s}" />`).join("")}
    <div class="label">CAPTION</div>
    <div class="block">${escapeHtml(p.caption || "(none)")}</div>
    ${p.kind === "reel"
      ? `<div class="label">AUDIO SCRIPT (pushed to Higgsfield)</div>
         <div class="block">${escapeHtml(p.audio_script || "(none)")}</div>`
      : `<div class="label">AUDIO SCRIPT</div><div class="block">no audio for this post</div>`}
    <div class="label">COMMENTS</div>
    <div id="comment-list">${cs.map(commentHtml).join("") || '<div class="block">No comments yet.</div>'}</div>
    <form class="add" id="add-form">
      <select id="add-part">
        <option value="general">general</option>
        <option value="caption">caption</option>
        <option value="audio">audio</option>
        <option value="visual">visual</option>
      </select>
      <textarea id="add-text" placeholder="Add a comment for regeneration…"></textarea>
      <button type="submit">Add comment</button>
    </form>`;
  $("#add-form").onsubmit = addComment;
  for (const el of det.querySelectorAll("[data-resolve]"))
    el.onclick = () => patchComment(el.dataset.resolve, { resolved: el.dataset.next === "true" });
  for (const el of det.querySelectorAll("[data-del]"))
    el.onclick = () => delComment(el.dataset.del);
}

function commentHtml(c) {
  return `<div class="comment ${c.resolved ? "resolved" : ""}">
    <div class="row"><span class="chip">${c.part}</span><span>${c.created_at}</span>
      <span style="margin-left:auto">
        <a href="#" data-resolve="${c.id}" data-next="${!c.resolved}">${c.resolved ? "reopen" : "resolve"}</a>
        · <a href="#" data-del="${c.id}">delete</a></span></div>
    <div>${escapeHtml(c.text)}</div></div>`;
}

async function addComment(e) {
  e.preventDefault();
  const text = $("#add-text").value.trim();
  if (!text) return;
  await fetch("/api/comments", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ post_id: SELECTED.post_id, part: $("#add-part").value, text }),
  });
  await refreshCounts();
  await renderDetail();
}

async function patchComment(id, body) {
  await fetch(`/api/comments/${id}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  await refreshCounts();
  await renderDetail();
}

async function delComment(id) {
  await fetch(`/api/comments/${id}`, { method: "DELETE" });
  await refreshCounts();
  await renderDetail();
}

async function refreshCounts() {
  POSTS = await (await fetch("/api/posts")).json();
  SELECTED = POSTS.find((p) => p.post_id === SELECTED.post_id) || SELECTED;
  renderGallery();
}

function escapeHtml(s) {
  return (s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

$("#refresh").onclick = load;
$("#filter-date").onchange = renderGallery;
$("#filter-ticker").onchange = renderGallery;
load();
```

- [ ] **Step 4: Smoke test — launch and verify the page**

Run (background): `cd review && python app.py` then in another shell:
`curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5005/` → expect `200`;
`curl -s http://127.0.0.1:5005/api/posts | python -c "import sys,json;print(len(json.load(sys.stdin)),'posts')"` → expect ≥ 4 posts.
Then stop the server. (Full visual confirmation — tiles render, video plays, comment add/resolve — is a manual check by the owner at the live window.)

- [ ] **Step 5: Commit**

```bash
git add review/static
git commit -m "feat(review): static gallery + detail + comments UI"
```

---

## Task 6: Regeneration feedback-loop docs + run docs

**Files:**
- Create: `review/README.md`
- Modify: `higgs/README_reels.md` (append a "Feedback loop" section)
- Modify: `.claude/skills/stock-carousel/SKILL.md` (append a "Feedback loop" note)
- Modify: `.claude/agents/higgsfield-ugc.md` (append a "Feedback loop" note)

**Interfaces:**
- Consumes: `comments.load_for_post` / `python comments.py <post_id>` from Task 3.
- Produces: documentation only. No code.

- [ ] **Step 1: Create `review/README.md`**

```markdown
# Post Review dashboard

Local web app to review generated social posts (reels + carousels), read each post's caption +
audio/narration script, and attach comments that regeneration will honor.

## Run
    cd review
    pip install -r requirements.txt
    python app.py            # http://localhost:5005

## What it reads / writes
- Reads (never writes): ../higgs/* and ../content/carousel_*/<TK>/
- Reads/writes: ../feedback/post_comments.json  (the comment store; git-tracked)

## Comments → regeneration
Comments are captured here, not acted on here. When you regenerate a post, the generator reads its
**open** comments and folds them into the prompt:

    cd review && python comments.py <post_id>      # e.g. 2026-06-22_NVDA_reel
    # or, in code:  from comments import read_store, load_for_post

`post_id` = `<date>_<TICKER>_<kind>` (e.g. `2026-06-22_NVDA_reel`). After regenerating, mark the
comments resolved (in the dashboard, or PATCH /api/comments/<id> {"resolved": true}).
```

- [ ] **Step 2: Append a "Feedback loop" section to `higgs/README_reels.md`**

Add at the end of the file:
```markdown

## Feedback loop (review dashboard)

Before **regenerating** a reel, pull its open review comments and fold them into the prompt
(respect the part tag — caption / audio / visual):

    cd review && python comments.py <date>_<TICKER>_reel    # e.g. 2026-06-22_NVDA_reel

Comments live in `feedback/post_comments.json` (written by the `review/` dashboard). After the reel
is regenerated, mark those comments resolved (dashboard, or `PATCH /api/comments/<id> {"resolved":true}`).
```

- [ ] **Step 3: Append a "Feedback loop" note to `.claude/skills/stock-carousel/SKILL.md`**

Add at the end of the file:
```markdown

## Feedback loop (review dashboard)

Before regenerating a carousel, load its open comments from the review dashboard's store and honor
them (respect the part tag — caption / audio / visual):

    cd review && python comments.py <date>_<TICKER>_carousel

Store: `feedback/post_comments.json`. After regenerating, mark those comments resolved.
```

- [ ] **Step 4: Append a "Feedback loop" note to `.claude/agents/higgsfield-ugc.md`**

Add at the end of the file:
```markdown

## Feedback loop (review dashboard)

If regenerating an existing post, first load its open comments — `cd review && python comments.py <post_id>`
(`post_id` = `<date>_<TICKER>_<kind>`) — and fold each into the generation prompt per its part tag
(caption / audio / visual). Mark them resolved after regenerating. Store: `feedback/post_comments.json`.
```

- [ ] **Step 5: Commit**

```bash
git add review/README.md higgs/README_reels.md .claude/skills/stock-carousel/SKILL.md .claude/agents/higgsfield-ugc.md
git commit -m "docs(review): wire the comments->regeneration feedback loop into generators"
```

---

## Task 7: Seed the feedback store + git policy

**Files:**
- Create: `feedback/post_comments.json`
- Modify: `review/README.md` (no-op if already documented — skip if present)

**Interfaces:**
- Produces: a committed empty store so the file is tracked from the start.

- [ ] **Step 1: Create `feedback/post_comments.json`**

```json
{
  "version": 1,
  "comments": []
}
```

- [ ] **Step 2: Verify it is NOT gitignored**

Run: `git check-ignore feedback/post_comments.json || echo "tracked (good)"`
Expected: prints `tracked (good)` (the file is not ignored).

- [ ] **Step 3: Verify the app reads the seeded store**

Run: `cd review && python -c "from comments import read_store; from paths import FEEDBACK_FILE; print(read_store(FEEDBACK_FILE))"`
Expected: `{'version': 1, 'comments': []}`

- [ ] **Step 4: Commit**

```bash
git add feedback/post_comments.json
git commit -m "chore(review): seed git-tracked empty comment store"
```

---

## Self-Review

**Spec coverage:**
- §3 Architecture (Flask + static, `review/` layout, port 5005) → Tasks 0, 4, 5.
- §4 Post model / indexer (post_id, media URLs, exclusions, audio_script rule) → Task 2 (grouping) + Task 4 (`caption`/`audio_script` enrichment).
- §5 Caption parser (kind→sheet selection) → Task 1 (parser) + Task 4 (`_caption_for` sheet selection/fallback).
- §6 Comment store + API (schema, parts, resolved, all routes, `/media` 403 guard) → Task 3 (store) + Task 4 (API).
- §7 Frontend (gallery, detail, caption, audio-script, comments add/resolve/delete, HTML-carousel placeholder) → Task 5.
- §8 Regeneration loop (`load_for_post`, CLI, generator doc notes) → Task 3 (CLI/helper) + Task 6 (docs).
- §9 Testing (pytest pure + Flask client + manual smoke) → Tasks 1-5.
- §10 Git policy (review/ committed, store git-tracked) → Tasks 0, 7.
- §11 Decisions (no in-app regen, per-post + part tag, audio=caption, store tracked, port 5005) → honored across tasks.

**Placeholder scan:** All steps contain concrete code/commands. The one `> Note` in Task 2 (remove the stray sort/reverse lines; use the corrected return block) is a correction to APPLY, not a placeholder. No TBD/TODO remain.

**Type consistency:** `post_id`/`kind`/`part` formats identical across Global Constraints, Tasks 2/3/4. `build_index` return shape (Task 2) matches what Task 4 enriches and Task 5 renders (`media`, `kind`, `ticker`, `date`, `post_id`, plus app-added `caption`/`audio_script`/`*_count`). `comments.*` signatures (Task 3 Interfaces) match the calls in Task 4's routes. `FEEDBACK_FILE` import style (Task 4 Note) matches the test's monkeypatch target.

**Known follow-ups (acceptable):** HTML-carousel tiles show a placeholder (no raster thumbnail) — intentional per spec §7. Reel slide PNGs without a date (`reel_<tk>_data.png`) attach to that ticker's reel bundle via the same path as v4 slides (Task 2) — covered by the indexer test's media assertions.
