"""Group higgs/ + content/ filenames into post bundles for the review gallery.

Pure: takes filename lists, returns post dicts. Caption/audio_script are added by the
app layer (it reads the caption sheets); this function only does grouping + media + ids.
"""
from __future__ import annotations

import re

_EXCLUDE = re.compile(r"^(hero_|logo_|maya_|_)|voice_.*\.mp3$|_anim\.mp4$|\.json$", re.I)


def _media(rel: str) -> str:
    return f"/media/{rel}"


def _neg_date(date: str) -> str:
    # invert date string ordering so newest sorts first while ticker sorts ascending
    return "".join(chr(255 - ord(c)) for c in date)


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
    posts.sort(key=lambda p: (_neg_date(p["date"]), p["ticker"]))
    return posts
