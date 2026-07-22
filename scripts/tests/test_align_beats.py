"""TDD tests for scripts/aiinvest/align_beats.py — whisper word-span -> beat
durations + caption spans (docs/superpowers/plans/2026-07-22-daily-screen-
production-line.md Task 4).

Synthetic fixture only — no audio, no whisper import here. 12 words across
3 VO lines (4 words each), at hand-picked times chosen so the expected frame
math lands on exact values (see the plan brief's Step 1 case list):

    line 0: 0.00s -> 4.00s   ("Assalamu alaykum WULF flipped.")   -- full match
    line 1: 4.00s -> 4.10s   ("The debt ratio is")                -- full match, TINY span (clamp)
    line 2: 4.10s -> 10.00s  ("Screen shows solid footing")       -- full match (test A)

fps=30, pad=12, min_frames=60 (the module defaults) throughout.
"""
import math

import pytest

from aiinvest.align_beats import apply_timing

FPS = 30
PAD = 12
MIN_FRAMES = 60

WORDS = [
    {"word": " Assalamu", "start": 0.00, "end": 1.00},
    {"word": " alaykum", "start": 1.00, "end": 2.00},
    {"word": " WULF", "start": 2.00, "end": 3.00},
    {"word": " flipped", "start": 3.00, "end": 4.00},
    {"word": " the", "start": 4.00, "end": 4.025},
    {"word": " debt", "start": 4.025, "end": 4.05},
    {"word": " ratio", "start": 4.05, "end": 4.075},
    {"word": " is", "start": 4.075, "end": 4.10},
    {"word": " screen", "start": 4.10, "end": 6.00},
    {"word": " shows", "start": 6.00, "end": 7.50},
    {"word": " solid", "start": 7.50, "end": 9.00},
    {"word": " footing", "start": 9.00, "end": 10.00},
]

VO_LINE_0 = "Assalamu alaykum WULF flipped."
VO_LINE_1 = "The debt ratio is"
VO_LINE_2_MATCHED = "Screen shows solid footing"


def _props(vo_lines):
    return {
        "beats": [{"kind": f"beat{i}", "durationInFrames": 999} for i in range(len(vo_lines))],
        "vo": list(vo_lines),
        "captions": [],
        "bubbleClips": [],
    }


def test_spans_plus_pad_and_final_beat_absorbs_remainder_and_captions_correct():
    props = _props([VO_LINE_0, VO_LINE_1, VO_LINE_2_MATCHED])
    out = apply_timing(props, WORDS, fps=FPS, pad=PAD, min_frames=MIN_FRAMES)

    # original untouched (deepcopy contract)
    assert props["beats"][0]["durationInFrames"] == 999

    durations = [b["durationInFrames"] for b in out["beats"]]

    # line 0: 0.00 -> 4.00s = 120 frames + 12 pad = 132, not clamped
    assert durations[0] == math.ceil(4.00 * FPS) + PAD == 132

    # line 1: 4.00 -> 4.10s = 3 frames + 12 pad = 15, clamped up to min_frames
    assert durations[1] == MIN_FRAMES

    # final beat absorbs the remainder so the total matches ceil(audio_end*fps)+pad
    audio_end = WORDS[-1]["end"]
    target = math.ceil(audio_end * FPS) + PAD
    assert sum(durations) == target
    assert durations[2] == target - durations[0] - durations[1]

    caps = out["captions"]
    assert len(caps) == 3
    assert caps[0] == {"text": VO_LINE_0, "fromMs": 0, "toMs": 4000}
    assert caps[1] == {"text": VO_LINE_1, "fromMs": 4000, "toMs": 4100}
    assert caps[2] == {"text": VO_LINE_2_MATCHED, "fromMs": 4100, "toMs": 10000}


def test_beats_vo_length_mismatch_raises_value_error():
    props = _props([VO_LINE_0, VO_LINE_1, VO_LINE_2_MATCHED])
    props["beats"] = props["beats"][:2]  # 2 beats, 3 vo lines
    with pytest.raises(ValueError):
        apply_timing(props, WORDS, fps=FPS, pad=PAD, min_frames=MIN_FRAMES)


def test_unmatched_line_falls_back_to_proportional_allocation():
    garbage = "Xylophone Quokka Umbrella Zephyr"  # shares no tokens with the remaining words
    props = _props([VO_LINE_0, VO_LINE_1, garbage])
    out = apply_timing(props, WORDS, fps=FPS, pad=PAD, min_frames=MIN_FRAMES)

    caps = out["captions"]
    # lines 0/1 matched normally, so line 2's fallback starts where line 1 ended
    assert caps[1]["toMs"] == 4100
    assert caps[2]["fromMs"] == 4100

    # proportional fallback: line's share of total VO chars x remaining audio duration
    total_vo_chars = len(VO_LINE_0) + len(VO_LINE_1) + len(garbage)
    remaining = WORDS[-1]["end"] - 4.10
    expected_end_s = 4.10 + (len(garbage) / total_vo_chars) * remaining
    assert caps[2]["toMs"] == round(expected_end_s * 1000)
    # sanity: fallback line does NOT reach the true audio end (partial match would have)
    assert caps[2]["toMs"] < round(WORDS[-1]["end"] * 1000)

    # the final beat still absorbs the remainder against the TRUE audio end,
    # regardless of the fallback line's own (shorter) computed span
    audio_end = WORDS[-1]["end"]
    target = math.ceil(audio_end * FPS) + PAD
    durations = [b["durationInFrames"] for b in out["beats"]]
    assert sum(durations) == target


def test_empty_words_list_does_not_crash_and_stays_sane():
    props = _props([VO_LINE_0, VO_LINE_1, VO_LINE_2_MATCHED])
    out = apply_timing(props, [], fps=FPS, pad=PAD, min_frames=MIN_FRAMES)
    durations = [b["durationInFrames"] for b in out["beats"]]
    assert all(d >= 0 for d in durations)
    assert len(out["captions"]) == 3
    for cap in out["captions"]:
        assert cap["fromMs"] <= cap["toMs"]


def test_words_run_out_before_last_vo_line_falls_back_without_crashing():
    # Only enough words for line 0; lines 1 and 2 have nothing left to match.
    short_words = WORDS[:4]
    props = _props([VO_LINE_0, VO_LINE_1, VO_LINE_2_MATCHED])
    out = apply_timing(props, short_words, fps=FPS, pad=PAD, min_frames=MIN_FRAMES)
    durations = [b["durationInFrames"] for b in out["beats"]]
    assert all(d >= MIN_FRAMES for d in durations[:-1])
    caps = out["captions"]
    assert caps[0]["toMs"] == 4000
    # lines 1/2 degenerate to zero-length spans starting where line 0 ended
    assert caps[1]["fromMs"] == 4000


def test_zero_duration_word_does_not_crash():
    words = [{"word": " WULF", "start": 1.0, "end": 1.0}]
    props = _props(["WULF"])
    out = apply_timing(props, words, fps=FPS, pad=PAD, min_frames=MIN_FRAMES)
    assert out["captions"][0]["fromMs"] == 1000
    assert out["captions"][0]["toMs"] == 1000


# ---------------------------------------------------------------------------
# Reviewer finding: proportional-fallback caption spans could overlap the
# NEXT line's real matched span (e.g. fallback line's toMs landing past the
# next line's already-known fromMs), producing overlapping caption pills at
# render. Fix: after all lines get a span, fallback-derived spans are
# clamped (end, and start if needed) so the list stays non-decreasing
# (captions[i].toMs <= captions[i+1].fromMs) without ever touching a
# matched line's real span.
# ---------------------------------------------------------------------------

FALLBACK_OVERLAP_WORDS = [
    {"word": " Hello", "start": 0.0, "end": 1.0},
    {"word": " World", "start": 2.0, "end": 3.0},
]
FALLBACK_OVERLAP_GARBAGE = "Xylophone Quokka Umbrella Zephyr"


def test_fallback_span_clamped_to_not_overlap_next_matched_line():
    # Reviewer-reproduced scenario: 3 lines, line 1 is garbage (falls back
    # to proportional allocation), lines 0 and 2 match real whisper words.
    # Unclamped, line 1's fallback share computes toMs ~= 2524ms, which
    # overshoots line 2's real matched fromMs of 2000ms -> overlap.
    props = _props(["Hello", FALLBACK_OVERLAP_GARBAGE, "World"])
    out = apply_timing(props, FALLBACK_OVERLAP_WORDS, fps=FPS, pad=PAD, min_frames=MIN_FRAMES)
    caps = out["captions"]

    # Global monotonicity across the whole caption list: no span's toMs may
    # exceed the next span's fromMs.
    for i in range(len(caps) - 1):
        assert caps[i]["toMs"] <= caps[i + 1]["fromMs"]
    for cap in caps:
        assert cap["fromMs"] <= cap["toMs"]

    # Line 2's real matched span must be untouched by the clamp.
    assert caps[2] == {"text": "World", "fromMs": 2000, "toMs": 3000}

    # Line 1's fallback span was pulled in to stop exactly at line 2's start.
    assert caps[1]["fromMs"] == 1000
    assert caps[1]["toMs"] == 2000


@pytest.mark.parametrize(
    "vo_lines,words",
    [
        ([VO_LINE_0, VO_LINE_1, VO_LINE_2_MATCHED], WORDS),
        ([VO_LINE_0, VO_LINE_1, "Xylophone Quokka Umbrella Zephyr"], WORDS),
        ([VO_LINE_0, VO_LINE_1, VO_LINE_2_MATCHED], []),
        ([VO_LINE_0, VO_LINE_1, VO_LINE_2_MATCHED], WORDS[:4]),
        (["Hello", FALLBACK_OVERLAP_GARBAGE, "World"], FALLBACK_OVERLAP_WORDS),
    ],
)
def test_captions_globally_non_decreasing_across_fixtures(vo_lines, words):
    props = _props(vo_lines)
    out = apply_timing(props, words, fps=FPS, pad=PAD, min_frames=MIN_FRAMES)
    caps = out["captions"]

    for cap in caps:
        assert cap["fromMs"] <= cap["toMs"]
    for i in range(len(caps) - 1):
        assert caps[i]["toMs"] <= caps[i + 1]["fromMs"]


def test_pathological_many_tiny_beats_floor_at_min_frames_and_sum_exceeds_target():
    """Pin the documented pathological case (align_beats.py's final-beat
    fallback branch): with no audio at all, every line's span degenerates to
    zero length, so every beat -- including the one that would normally
    absorb the remainder -- floors at min_frames instead. The
    sum(durationInFrames) == target invariant is deliberately NOT guaranteed
    here; this test pins that documented outcome so a future change to that
    branch is a deliberate decision, not an accidental regression.
    """
    lines = [f"Line number {i} of five" for i in range(5)]
    props = _props(lines)
    out = apply_timing(props, [], fps=FPS, pad=PAD, min_frames=MIN_FRAMES)
    durations = [b["durationInFrames"] for b in out["beats"]]

    assert durations == [MIN_FRAMES] * len(lines)

    audio_end = 0.0
    target = math.ceil(audio_end * FPS) + PAD
    assert sum(durations) > target
    assert durations[-1] == MIN_FRAMES
