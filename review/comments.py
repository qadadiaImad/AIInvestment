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
