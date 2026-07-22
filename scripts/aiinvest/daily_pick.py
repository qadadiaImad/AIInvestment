"""Daily-post picker: verdict snapshots, flip detection, candidate scoring.

Picks which stock gets today's post. Pure logic + small JSON I/O, no network.

Pipeline (see `rank_candidates`):
  1. diff today's verdicts against yesterday's snapshot -> flips (alert-shaped).
  2. hand flips + bundle to `halal_stories.pick_stories` for content-worthy stories.
  3. boost non-flip stories with recent news heat.
  4. demote non-flip stories whose symbol was posted in the last 30 days (flips
     are exempt -- a verdict flip always outranks everything else).
  5. sort, top up to 3 with rotation fillers if stories run dry.

History lives on disk as `data/halal_history/YYYY-MM-DD.json` snapshots plus a
`posted_log.json` list of `{"symbol","date","folder"}` -- see `load_history` /
`save_snapshot` / `load_posted_log` / `append_posted`.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from . import halal_stories

_ROTATION_DAYS = 30
_RECENCY_HOURS = 48
_RECENT_WEIGHT = 1.0
_STALE_WEIGHT = 0.3
_ROTATION_PENALTY = 0.1


def verdict_map(bundle):
    """bundle -> {symbol: overall}."""
    verdicts = (bundle or {}).get("verdicts") or {}
    return {sym: v.get("overall") for sym, v in verdicts.items()}


def detect_flips(prev_map, bundle):
    """Diff prev_map against bundle's current verdicts -> alert-shaped list.

    First run (prev_map is None) never alerts -- it only seeds tomorrow's diff.
    New symbols (absent from prev_map) never flip; symbols dropped from the
    current bundle never flip either (nothing to compare against).
    """
    if prev_map is None:
        return []
    current = verdict_map(bundle)
    flips = []
    for sym, old in (prev_map or {}).items():
        new = current.get(sym)
        if new is not None and new != old:
            flips.append({
                "symbol": sym, "from": old, "to": new,
                "old_value": None, "new_value": None,
            })
    flips.sort(key=lambda f: f["symbol"])
    return flips


def _parse_when(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _word_in(text, symbol):
    if not text or len(symbol) < 3:
        return False
    return re.search(rf"\b{re.escape(symbol)}\b", text, re.IGNORECASE) is not None


def news_heat(news_bundle, symbols, now):
    """count of news items mentioning each symbol, recency-weighted.

    A symbol matches an item if it's in the item's `tickers` list, or appears
    as a whole word in `title`/`summary`. Weight is 1.0 if `published_at` is
    <48h before `now`, else 0.3 (unparsable/missing timestamp -> 0.3 too).
    A missing or unparsable news bundle yields `{}`.
    """
    if not isinstance(news_bundle, dict):
        return {}
    items = news_bundle.get("items")
    if not isinstance(items, list):
        return {}

    symbols = set(symbols or ())
    heat: dict[str, float] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        tickers = item.get("tickers") or []
        title = item.get("title") or ""
        summary = item.get("summary") or ""
        published = _parse_when(item.get("published_at"))
        if published is not None:
            if published.tzinfo is None:
                published = published.replace(tzinfo=dt.timezone.utc)
            now_aware = now if now.tzinfo is not None else now.replace(tzinfo=dt.timezone.utc)
            age = now_aware - published
            weight = _RECENT_WEIGHT if age < dt.timedelta(hours=_RECENCY_HOURS) else _STALE_WEIGHT
        else:
            weight = _STALE_WEIGHT

        for sym in symbols:
            if sym in tickers or _word_in(title, sym) or _word_in(summary, sym):
                heat[sym] = heat.get(sym, 0.0) + weight

    return {sym: round(val, 4) for sym, val in heat.items()}


def _as_date(value):
    if isinstance(value, dt.datetime):
        return value.date()
    return value


def _parse_log_date(value):
    if not isinstance(value, str):
        return None
    try:
        return dt.datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _recently_posted(posted_log, now, days=_ROTATION_DAYS):
    """symbols posted within `days` days of `now` (malformed entries skipped)."""
    now_date = _as_date(now)
    recent = set()
    for entry in posted_log or []:
        if not isinstance(entry, dict):
            continue
        sym = entry.get("symbol")
        posted_date = _parse_log_date(entry.get("date"))
        if not sym or posted_date is None:
            continue
        delta = (now_date - posted_date).days
        if 0 <= delta <= days:
            recent.add(sym)
    return recent


def _last_posted_date(posted_log, symbol):
    dates = [d for d in (
        _parse_log_date(entry.get("date"))
        for entry in (posted_log or []) if isinstance(entry, dict) and entry.get("symbol") == symbol
    ) if d is not None]
    return max(dates) if dates else None


def _rotation_fillers(bundle, used, posted_log):
    """Symbols not already picked, least-recently/never-posted first, then alphabetical."""
    pool = [sym for sym in verdict_map(bundle) if sym not in used]
    return sorted(pool, key=lambda s: (_last_posted_date(posted_log, s) or dt.date.min, s))


def _flip_reason(symbol, alerts, now):
    alert = next((a for a in alerts if a["symbol"] == symbol), None)
    date_str = now.strftime("%Y-%m-%d")
    if alert is None:
        return f"{symbol} verdict flipped on {date_str}."
    return f"verdict flipped {alert['from']} -> {alert['to']} on {date_str}"


def _story_reason(symbol, story):
    if (story or {}).get("kind") == "rotation":
        return f"{symbol} selected to keep rotation fresh — no fresher story today."
    fact = (story or {}).get("headline_fact")
    if fact:
        return fact if fact.rstrip().endswith((".", "!", "?")) else f"{fact}."
    return f"{symbol} selected for today's screen."


def rank_candidates(bundle, prev_map, news_bundle, posted_log, now):
    """Top-3 `{"symbol","score","reason","story"}` candidates for today's post."""
    posted_log = posted_log or []
    alerts = detect_flips(prev_map, bundle)
    stories = halal_stories.pick_stories(bundle, alerts=alerts, top=10)

    story_symbols = {s["symbol"] for s in stories}
    heat = news_heat(news_bundle, story_symbols, now)
    recent = _recently_posted(posted_log, now)

    candidates = []
    for story in stories:
        sym = story["symbol"]
        is_flip = story.get("kind") == "flip"
        score = story.get("score", 0.0)
        if not is_flip:
            score = score + heat.get(sym, 0.0)
            if sym in recent:
                score = score * _ROTATION_PENALTY
        candidates.append({"symbol": sym, "score": score, "story": story, "is_flip": is_flip})

    candidates.sort(key=lambda c: (-c["score"], c["symbol"]))

    # A symbol can earn two story dicts from halal_stories.pick_stories (e.g.
    # it both flips AND independently qualifies for a ratio/business story).
    # Keep only each symbol's highest-scoring entry -- first-seen-wins after
    # the sort above, so flips (score >= 1000) always survive over ratio/
    # business stories for the same symbol.
    seen_symbols = set()
    deduped = []
    for c in candidates:
        if c["symbol"] in seen_symbols:
            continue
        seen_symbols.add(c["symbol"])
        deduped.append(c)
    candidates = deduped

    used = {c["symbol"] for c in candidates}
    for sym in _rotation_fillers(bundle, used, posted_log):
        if len(candidates) >= 3:
            break
        filler_story = {"symbol": sym, "kind": "rotation", "headline_fact": None}
        candidates.append({"symbol": sym, "score": 0.0, "story": filler_story, "is_flip": False})
        used.add(sym)

    out = []
    for c in candidates[:3]:
        reason = _flip_reason(c["symbol"], alerts, now) if c["is_flip"] else _story_reason(c["symbol"], c["story"])
        out.append({"symbol": c["symbol"], "score": c["score"], "reason": reason, "story": c["story"]})
    return out


# ---------------------------------------------------------------------------
# History I/O: data/halal_history/YYYY-MM-DD.json snapshots + posted_log.json
# ---------------------------------------------------------------------------

_POSTED_LOG_NAME = "posted_log.json"


def load_history(dir_path):
    """-> (prev_verdict_map|None, prev_date_str|None) from the newest snapshot."""
    d = Path(dir_path)
    if not d.exists() or not d.is_dir():
        return None, None
    files = sorted(p for p in d.glob("*.json") if p.name != _POSTED_LOG_NAME)
    if not files:
        return None, None
    try:
        payload = json.loads(files[-1].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, None
    if not isinstance(payload, dict):
        return None, None
    return payload.get("verdicts"), payload.get("date")


def save_snapshot(dir_path, date_str, vmap):
    """Write `{dir_path}/{date_str}.json` = `{"date": date_str, "verdicts": vmap}`."""
    d = Path(dir_path)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{date_str}.json"
    path.write_text(json.dumps({"date": date_str, "verdicts": vmap}, indent=2), encoding="utf-8")
    return str(path)


def load_posted_log(path):
    """-> list of `{"symbol","date","folder"}` (missing/malformed file -> [])."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def append_posted(path, entry):
    """Append `entry` to the posted log at `path`, creating it if needed."""
    p = Path(path)
    log = load_posted_log(p)
    log.append(entry)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(log, indent=2), encoding="utf-8")
    return log
