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

    # line 0: start-anchored to line 1's real start (4.00s) = 120 frames, no pad --
    # the old model added a flat +12 pad here; the new model doesn't, because the
    # real gap to the next line's start IS the beat's duration.
    assert durations[0] == math.ceil(4.00 * FPS) == 120

    # line 1: start-anchored to line 2's real start (4.10s) = 0.10s = 3 frames,
    # clamped up to min_frames (real gap too tight to render as-is)
    assert durations[1] == MIN_FRAMES

    # final beat: own real start (4.10s) to the true audio end (10.00s), + pad --
    # computed directly against audio_end, not as a leftover remainder.
    audio_end = WORDS[-1]["end"]
    assert durations[2] == math.ceil((audio_end - 4.10) * FPS) + PAD

    # zero drift by construction: since line 1's real gap (3 frames) is BELOW
    # min_frames it does clamp -- but line 0's own gap did not, so the Series'
    # cumulative frame position at the start of beat 1 lands exactly on line 1's
    # real (whisper-true) start.
    assert durations[0] == math.ceil(4.00 * FPS)

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

    # the final beat's duration is always computed directly against the TRUE
    # audio end, from ITS OWN real start (4.10s, where line 1's matched span
    # truly ended) -- independent of the fallback line's own (shorter,
    # proportional) caption span, and independent of any min_frames clamping
    # on earlier beats.
    audio_end = WORDS[-1]["end"]
    durations = [b["durationInFrames"] for b in out["beats"]]
    assert durations[-1] == math.ceil((audio_end - 4.10) * FPS) + PAD

    # line 1's real gap to line 2's start (4.00 -> 4.10s = 3 frames) is too tight
    # to render, so it floors at min_frames -- a deliberate, bounded trade-off
    # (see module docstring): the total can now exceed the "ideal" unclamped
    # target by exactly that clamp's overshoot, but the final beat's own end is
    # never affected by it.
    assert durations[1] == MIN_FRAMES
    target = math.ceil(audio_end * FPS) + PAD
    assert sum(durations) == target + (MIN_FRAMES - 3)


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


# ---------------------------------------------------------------------------
# I2 — start-anchored duration model. Real Chatterbox TTS audio has uneven,
# multi-second inter-line pauses (the module's blank-line-joined `_vo_script`),
# not the earlier fixtures' back-to-back zero-gap words. The old span+pad
# model derived each beat's duration from its OWN span length, which silently
# assumed every line started exactly `pad` after the previous one ended --
# real audio drifts the Remotion <Series>'s cumulative (relative) clock away
# from CaptionLayer's absolute (whisper-true) clock as the gaps compound.
# These fixtures insert realistic 1-2s gaps and assert scene boundaries land
# exactly on the next line's real start -- zero drift, by construction.
# ---------------------------------------------------------------------------

GAP_WORDS = [
    {"word": " Hook", "start": 0.0, "end": 0.5},
    {"word": " line", "start": 0.5, "end": 1.0},
    {"word": " one", "start": 1.0, "end": 2.0},
    # 1.5s real pause before line 1 starts (would be smoothed to 0.4s by the old pad model)
    {"word": " Bars", "start": 3.5, "end": 4.0},
    {"word": " beat", "start": 4.0, "end": 4.5},
    {"word": " here", "start": 4.5, "end": 5.5},
    # 2.0s real pause before line 2 (the stamp/verdict beat -- the reel's climactic moment)
    {"word": " Stamp", "start": 7.5, "end": 8.0},
    {"word": " verdict", "start": 8.0, "end": 8.5},
    {"word": " now", "start": 8.5, "end": 9.5},
    # 1.0s real pause before the final (endcard) line
    {"word": " End", "start": 10.5, "end": 11.0},
    {"word": " card", "start": 11.0, "end": 11.5},
    {"word": " thanks", "start": 11.5, "end": 12.5},
]
GAP_LINES = ["Hook line one", "Bars beat here", "Stamp verdict now", "End card thanks"]
GAP_LINE_STARTS = [0.0, 3.5, 7.5, 10.5]
GAP_AUDIO_END = 12.5


def test_gapful_real_audio_scene_boundaries_land_on_next_line_true_start_zero_drift():
    """The I2 regression fixture, reproducing the live wet-run pattern (WKEY
    props_A.json: hook/bars/hook*/stamp/endcard, stamp caption starting ~4.0s
    late under the old model). None of these gaps trip min_frames, so drift
    must be exactly zero: each beat's cumulative Series start frame equals the
    next line's real (whisper-true) start, converted to frames."""
    props = _props(GAP_LINES)
    out = apply_timing(props, GAP_WORDS, fps=FPS, pad=PAD, min_frames=MIN_FRAMES)
    durations = [b["durationInFrames"] for b in out["beats"]]

    assert all(d >= MIN_FRAMES for d in durations), "fixture is designed so nothing clamps"

    cumulative = 0
    for i in range(len(GAP_LINE_STARTS) - 1):
        cumulative += durations[i]
        expected_frame = math.ceil(GAP_LINE_STARTS[i + 1] * FPS)
        assert cumulative == expected_frame, (
            f"beat {i + 1} should start at frame {expected_frame} (line {i + 1}'s real "
            f"start {GAP_LINE_STARTS[i + 1]}s) but Series cumulative position is {cumulative}")

    # final beat: own real start to the true audio end, + pad
    assert durations[-1] == math.ceil((GAP_AUDIO_END - GAP_LINE_STARTS[-1]) * FPS) + PAD

    # nothing clamped, so the total covers exactly the real audio length + pad
    assert sum(durations) == math.ceil(GAP_AUDIO_END * FPS) + PAD


def test_short_real_gap_clamps_without_corrupting_the_next_beats_own_duration():
    """One inter-line real gap (1.05s = 31.5 frames) is too short to render and
    floors at min_frames -- but each beat's duration is derived independently
    from its OWN pair of adjacent span starts, so that clamp must not corrupt
    the NEXT beat's own duration (it only pushes that beat's cumulative Series
    position later -- a deliberate, bounded trade-off; see the module
    docstring's "Duration model" section)."""
    words = [
        {"word": " Hook", "start": 0.0, "end": 1.0},
        {"word": " Tick", "start": 1.05, "end": 1.10},   # gap from line 0's start: 1.05s -> clamps
        {"word": " End", "start": 4.0, "end": 6.0},        # gap from line 1's start: 2.95s -> no clamp
    ]
    props = _props(["Hook", "Tick", "End"])
    out = apply_timing(props, words, fps=FPS, pad=PAD, min_frames=MIN_FRAMES)
    durations = [b["durationInFrames"] for b in out["beats"]]

    assert durations[0] == MIN_FRAMES  # real gap (1.05s = 31.5 frames) too short, floors
    assert durations[1] == math.ceil((4.0 - 1.05) * FPS)  # unaffected by beat 0's clamp
    assert durations[2] == math.ceil((6.0 - 4.0) * FPS) + PAD  # final beat: own start to audio end + pad


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
