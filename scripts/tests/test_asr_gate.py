"""The ASR gate's comparator, tested against pairs it actually got wrong.

Every case below is a real (intended, transcribed) pair observed while
generating the Shorts cut. The first three were reported as hallucinations
by the first version of the comparator and are perfectly good takes; the
last is the genuine failure the gate exists to catch. A gate that cannot
tell those apart is worse than no gate.

  cd scripts && python -m pytest tests/test_asr_gate.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vector"))

import asr_gate as G


GOOD = [
    ("Same machine. 2008. Down FIFTY-FIVE percent.",
     "Same machine, 2008, down 55%."),
    ("Fifty-five percent - and houses?", "55% and houses?"),
    ("Down TWENTY-SEVEN percent.", "down 27%."),
    ("Dot-com fell SEVENTY-SEVEN percent. Gone.", "Dot-com fell 77%. Gone."),
    ("Thirty-one months to hit bottom.", "31 months to hit bottom."),
    ("Eleven and a half TRILLION in household wealth.",
     "eleven and a half trillion in household wealth."),
    ("The last bubble took fifteen years to get back to even.",
     "The last bubble took 15 years to get back to even."),
]

BAD = [
    ("Gone. Watch the machine, not the number.",
     "W. W. W. S. R. W. S. R. W. 5. W. S. R. Not the number."),
    ("No villain. Just a machine. Four parts.", "Nope. Villain."),
]


def test_good_takes_pass():
    for ref, hyp in GOOD:
        e = G.wer(ref, hyp)
        assert e <= G.FAIL, "false reject %.2f: %r vs %r" % (e, ref, hyp)


def test_the_hallucination_fails():
    for ref, hyp in BAD:
        e = G.wer(ref, hyp)
        assert e > G.FAIL, "false accept %.2f: %r vs %r" % (e, ref, hyp)


def test_compound_numbers_combine():
    assert G.words("fifty-five percent") == ["55", "%"]
    assert G.words("twenty seven percent") == ["27", "%"]
    assert G.words("55%") == ["55", "%"]
    assert G.words("Thirty-one months") == ["31", "months"]


def test_scale_words_survive():
    assert G.words("eleven and a half trillion") == ["11", "trillion", "half"] \
        or G.words("eleven and a half trillion") == ["11", "half", "trillion"]


def test_identical_text_is_zero():
    for ref, _ in GOOD:
        assert G.wer(ref, ref) == 0.0
