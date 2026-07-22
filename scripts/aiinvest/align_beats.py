"""Whisper word-span -> beat durations + caption spans (The Daily Screen,
docs/superpowers/plans/2026-07-22-daily-screen-production-line.md Task 4).

Pure `apply_timing(props, words, fps=30, pad=12, min_frames=60) -> dict`.
Consumes the props dict produced by `aiinvest.daily_copy.build_daily`
(`{"beats": [...], "vo": [...], ...}`, beats/vo index-aligned 1:1) and a
faster-whisper word-timestamp list (`[{"word": str, "start": float, "end":
float}, ...]`, seconds), and returns a new props dict (deepcopy — the input
is never mutated) where:

  - each beat's `durationInFrames` is **start-anchored**: beat *i*'s
    duration is the real gap from its own VO line's matched-span START to
    the NEXT line's matched-span START (real inter-line pauses are absorbed
    into the owning beat, not smoothed away by a flat pad), clamped to >=
    `min_frames`. The final beat has no "next start" to anchor to, so it
    runs from its own start to the true audio end, plus `pad` frames for a
    trailing breath. (See "Duration model" below for why — I2.)
  - `captions` is filled with one `{"text", "fromMs", "toMs"}` entry per
    VO line, in milliseconds, for Task 5's caption track.

Matching (per VO line, in beat order): normalize both VO tokens and
whisper words (`lower()`, strip non-alphanumerics) and walk the word list
**once** with a single forward-only pointer — each line consumes its
matched words greedily, in order, without ever re-using a word claimed by
an earlier line. A token may only match a word within `_LOOKAHEAD_WINDOW`
(15) words of the last CONFIRMED match — beyond that it is counted
unmatched rather than letting a stray hit drag the shared pointer arbitrarily
far ahead (see `_LOOKAHEAD_WINDOW`'s docstring). Low-information stopwords
(`_STOPWORDS` — "the", "a", "of", ...) are trusted only within
`_STOPWORD_WINDOW` (3) words of the last confirmed match; they never serve as
a long-range anchor on their own. A line's span is `first_matched_word.start
.. last_matched_word.end`. If fewer than 60% of a line's tokens matched, that
line falls back to *proportional allocation*: its share of the total VO
character count (across all lines in this reel) times the audio time
remaining after the previous line's span, laid down starting where the
previous line ended.

Because a fallback span is computed purely from a proportional share of the
*remaining* audio, it knows nothing about a later line's real (matched)
span — it can run past the very next line's true start, which would
otherwise produce overlapping caption pills at render. A second pass fixes
this: after every line has a span, each **fallback-derived** span's end
(and, if that collapses it below its own start, its start too) is clamped
so the full caption list stays non-decreasing — `captions[i]["toMs"] <=
captions[i + 1]["fromMs"]` for every `i`, and the last line's span never
runs past the true audio length. Matched lines carry real whisper
timestamps and are **never** altered by this clamp, even if that leaves a
gap before them.

Duration model (I2 — start-anchored boundaries): the Remotion `<Series>` lays
out beats **cumulatively** by summing each beat's *relative* `durationInFrames`,
while `captions[i].fromMs/toMs` are *absolute* whisper-true timestamps that
`CaptionLayer` reads straight off the render clock. Those two clocks only
agree if `durationInFrames` is derived from the gap between consecutive
lines' real starts — deriving it from each line's OWN span length (`end -
start`) plus a flat `pad` (the old model) implicitly assumes every line is
followed immediately (exactly `pad` later) by the next, which real TTS
audio does not honor (uneven inter-line pauses accumulate into growing
drift — up to several seconds by the final beat on real Chatterbox output).
Anchoring each beat's duration to `next_start - this_start` instead makes
the cumulative relative-duration sum telescope back to the true absolute
timeline: `sum(durationInFrames[:i]) == frames(spans[i][0] - spans[0][0])`
for any beat *i* with no `min_frames` clamp upstream, so scene boundaries
land exactly on the next line's real (whisper-true) start — zero drift by
construction. The final beat has no next line to anchor to, so it instead
runs from its own start to the true audio end (`audio_end - start`) plus
`pad` frames for a trailing breath; `sum(durationInFrames) ==
ceil(audio_end * fps) + pad` again follows naturally from that telescoping,
*provided* no beat needed the `min_frames` floor (see below) — the total
still always ends when the narration ends, never early, because the last
beat's own end is computed directly against `audio_end`, not as a leftover
remainder of the earlier beats.

`min_frames` still floors any beat whose real gap (or trailing span) would
be too short to render sensibly (e.g. a fast one-word matched line, or the
degenerate all-fallback case with zero audio) — when that clamp fires for a
non-final beat, later scene boundaries necessarily slip later than their
true starts by the clamped amount (a deliberate, bounded trade-off: a
beat is never shorter than `min_frames`, but a pathologically tiny real gap
can no longer be represented exactly). This is the same trade-off the old
model made; only the *unclamped* case's accuracy improved.

Raises `ValueError` if `len(props["beats"]) != len(props["vo"])`.

---

`scripts/voice/whisper_align.py` is the thin CLI that produces the `words`
list this module consumes, via faster-whisper. Run it with the chatterbox
venv python (it has `faster-whisper` installed; the main repo venv does
not):

    C:/Users/Amsegt/.venvs/chatterbox/Scripts/python.exe scripts/voice/whisper_align.py <wav> --out words.json

Educational/research only — not financial advice.
"""
from __future__ import annotations

import copy
import math
import re

__all__ = ["apply_timing"]

# Matching-loop bounds (see "Matching" section of the module docstring above).
# `_LOOKAHEAD_WINDOW` caps how far ahead of the last CONFIRMED match a token
# may search: without this, a single false hit on a low-information token
# (e.g. a stray "the") can jump the shared forward-only pointer arbitrarily
# far ahead, stranding every word the NEXT line actually needed. Reproduced
# live in higgs/daily/2026-07-22_WKEY: line 0's trailing "the" unbounded-
# matched words_A.json idx 40 (a "the" that really belongs to line 2's
# audio), skipping lines 1-2's real spans entirely.
# `_STOPWORDS` are low-information tokens that appear constantly throughout
# any transcript -- they carry almost no positional signal, so even within
# `_LOOKAHEAD_WINDOW` they're only trusted as a match when they land within
# `_STOPWORD_WINDOW` words of the last confirmed match (i.e. right next to
# content we already know is correct), never as a long-range anchor on their
# own.
_LOOKAHEAD_WINDOW = 15
_STOPWORD_WINDOW = 3
_STOPWORDS = frozenset({
    "the", "a", "an", "of", "is", "to", "and", "in", "it", "that", "this",
})


def _normalize(token: str) -> str:
    return re.sub(r"[^a-z0-9]", "", token.lower())


def _frames(seconds: float, fps: int) -> int:
    """Seconds -> whole frames, rounding UP (never under-cover the audio).
    `round(..., 6)` first absorbs float noise (e.g. 4.10-4.00 == 0.0999...964)
    so it doesn't spuriously push us to the next frame."""
    return math.ceil(round(seconds * fps, 6))


def apply_timing(props: dict, words: list[dict], fps: int = 30, pad: int = 12,
                  min_frames: int = 60) -> dict:
    beats = props.get("beats", [])
    vo = props.get("vo", [])
    if len(beats) != len(vo):
        raise ValueError(
            f"align_beats.apply_timing: beats/vo length mismatch "
            f"({len(beats)} beats vs {len(vo)} vo lines)"
        )

    new_props = copy.deepcopy(props)
    n = len(vo)
    if n == 0:
        new_props["captions"] = []
        return new_props

    total_audio_duration = max((w["end"] for w in words), default=0.0)
    total_vo_chars = sum(len(line) for line in vo)

    spans: list[tuple[float, float]] = []
    is_fallback: list[bool] = []
    pointer = 0
    prev_end = 0.0
    for line in vo:
        tokens = [t for t in (_normalize(tok) for tok in line.split()) if t]

        matched_indices: list[int] = []
        p = pointer
        for tok in tokens:
            # `p` always equals "last confirmed match index + 1" (it only
            # advances on a hit below), so it doubles as both the search
            # start AND the anchor for the stopword/lookahead bounds.
            window = _STOPWORD_WINDOW if tok in _STOPWORDS else _LOOKAHEAD_WINDOW
            limit = min(p + window, len(words))
            found = None
            for j in range(p, limit):
                if _normalize(words[j]["word"]) == tok:
                    found = j
                    break
            if found is not None:
                matched_indices.append(found)
                p = found + 1
        pointer = p

        fraction = (len(matched_indices) / len(tokens)) if tokens else 0.0

        if matched_indices and fraction >= 0.6:
            start = words[matched_indices[0]]["start"]
            end = words[matched_indices[-1]]["end"]
            is_fallback.append(False)
        else:
            remaining = max(total_audio_duration - prev_end, 0.0)
            share = (len(line) / total_vo_chars) if total_vo_chars > 0 else (1.0 / n)
            start = prev_end
            end = start + max(share * remaining, 0.0)
            is_fallback.append(True)

        spans.append((start, end))
        prev_end = end

    # A fallback span's end is a proportional guess at the REMAINING audio
    # and has no idea where a later (possibly matched) line's real span
    # begins. Clamp fallback spans only, walking backward so a run of
    # consecutive fallback lines cascades correctly: each fallback span's
    # end is capped at the next span's (by now possibly already-clamped)
    # start, and its own start is pulled down to match if that would
    # otherwise leave start > end. Matched spans carry real whisper
    # timestamps and are never touched here.
    for i in range(n - 2, -1, -1):
        if not is_fallback[i]:
            continue
        start, end = spans[i]
        next_start = spans[i + 1][0]
        if end > next_start:
            end = next_start
            if start > end:
                start = end
            spans[i] = (start, end)

    # The last line, if itself a fallback, has no "next" span to clamp
    # against — cap it to the true audio length instead.
    if is_fallback[-1]:
        start, end = spans[-1]
        if end > total_audio_duration:
            end = total_audio_duration
            if start > end:
                start = end
            spans[-1] = (start, end)

    # Start-anchored boundaries (I2): beat i's duration is the real gap between
    # THIS line's span start and the NEXT line's span start, not this line's own
    # span length + a flat pad -- see the module docstring's "Duration model"
    # section for why this keeps the Remotion <Series>'s cumulative relative
    # clock aligned with CaptionLayer's absolute whisper-true clock. Spans are
    # non-decreasing by construction (matched spans walk the word list with a
    # forward-only pointer; fallback spans are clamped against their neighbor
    # above), so every non-final gap is >= 0 before the min_frames floor.
    starts = [s for s, _ in spans]
    durations = [
        max(_frames(starts[i + 1] - starts[i], fps), min_frames)
        for i in range(n - 1)
    ]
    # Final beat: no "next start" to anchor to -- runs from its own start to the
    # true audio end, plus a trailing pad. Computed directly against
    # `total_audio_duration` (not as a remainder of the other beats), so it
    # always lands on the real audio end regardless of any upstream clamping.
    durations.append(max(_frames(total_audio_duration - starts[-1], fps) + pad, min_frames))

    for beat, dur in zip(new_props["beats"], durations):
        beat["durationInFrames"] = dur

    new_props["captions"] = [
        {"text": line, "fromMs": round(start * 1000), "toMs": round(end * 1000)}
        for (start, end), line in zip(spans, vo)
    ]

    return new_props
