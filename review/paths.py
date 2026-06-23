"""Filesystem anchors for the post-review app. review/ -> repo root is one level up."""
from __future__ import annotations

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HIGGS = REPO_ROOT / "higgs"
CONTENT = REPO_ROOT / "content"
FEEDBACK_FILE = REPO_ROOT / "feedback" / "post_comments.json"
