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
        m = re.search(r"—\s*([A-Z]{1,16})\b", head)
        if not m:
            continue
        body = (blocks[i + 1] if i + 1 < len(blocks) else "").strip()
        if body:
            out[m.group(1)] = body
    return out
