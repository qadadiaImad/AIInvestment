"""List the higgs/ pre-creation planning docs (reel scripts, post scripts, kit markdown)
for the Preview page. Pure: takes a filename list, returns sorted entries."""
from __future__ import annotations

import re

_KIND_ORDER = {"kit": 0, "reel-script": 1, "post-script": 2}


def _classify(name: str):
    m = re.match(r"^reels_(\d{4}-\d{2}-\d{2})_kit\.md$", name)
    if m:
        return m.group(1), "kit"
    m = re.match(r"^reels_(\d{4}-\d{2}-\d{2})\.txt$", name)
    if m:
        return m.group(1), "reel-script"
    m = re.match(r"^posts_(\d{4}-\d{2}-\d{2})\.txt$", name)
    if m:
        return m.group(1), "post-script"
    return None


def list_scripts(higgs_files: list[str]) -> list[dict]:
    out = []
    for name in higgs_files:
        c = _classify(name)
        if not c:
            continue
        date, kind = c
        out.append({"name": name, "date": date, "kind": kind,
                    "media": f"/media/higgs/{name}"})
    # newest date first; within a date: kit -> reel-script -> post-script, then name asc.
    out.sort(key=lambda e: e["name"])
    out.sort(key=lambda e: _KIND_ORDER.get(e["kind"], 9))
    out.sort(key=lambda e: e["date"], reverse=True)
    return out
