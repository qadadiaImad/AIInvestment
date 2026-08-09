"""Did the model actually say the line? Shared ASR gate.

Chatterbox does not always say what it was given. Generating the Shorts cut
produced this, for "Gone. Watch the machine, not the number.":

    W. W. W. S. R. W. S. R. W. 5. W. S. R. Not the number.

6.37 seconds of it, in a 13-line cut, on the closing beat. Nothing else in
the pipeline could see it: the duration probes only know it is long for its
word count, and a pause explains that; the stray-onset probe looks at the
first 600ms, which is fine; the mouth tracks are built FROM the bad audio so
they match it perfectly. The only thing that catches a hallucination is
listening to it, and the machine version of listening is transcribing it.

WHY THE NUMBER MAP. Whisper writes "fifteen" as "15", so a naive word
comparison scores a perfectly good take as 50% wrong. A gate that fails on
correct audio is worse than no gate: it trains you to ignore it, and then
it is not there on the day something is actually broken.

THE THRESHOLD IS LOOSE ON PURPOSE. Measured on approved audio, small.en
still mis-hears "Hah" as "Ah" and renders a leading ellipsis as "2", which
puts a legitimate short line at 0.25-0.33 WER on its own. This is a
catastrophe detector, not a pronunciation critic - it is meant to catch the
line that came out as letters, not to adjudicate diction.
"""
from __future__ import annotations

import re

FAIL = 0.40          # WER above this means the take is not the line

# Numbers have to be COMBINED, not mapped word by word. The first version
# mapped each word on its own, so "fifty-five" became "50 5" against
# Whisper's "55" and every percentage in the script was reported as a
# hallucination. Three of the four rejects on the first real run were this
# bug, not the model - and a gate crying wolf on correct audio is how you
# end up ignoring it on the line that is genuinely broken.
UNITS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
         "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
         "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
         "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
         "nineteen": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90}
SCALE = {"hundred": 100, "thousand": 1000, "million": 10 ** 6,
         "billion": 10 ** 9, "trillion": 10 ** 12}
# words that carry no information for this comparison
NOISE = {"and", "a", "an", "the"}
_MODEL = None


def words(s: str) -> list[str]:
    raw = re.findall(r"[a-z0-9']+|%", s.lower().replace("-", " "))
    out, num, seen = [], 0, False
    for w in raw:
        if w == "percent":
            w = "%"
        if w in UNITS or w in TENS:
            num += UNITS.get(w, 0) or TENS.get(w, 0)
            seen = True
            continue
        if w in SCALE and seen:
            # "eleven ... trillion" keeps the scale as its own token, which
            # is how Whisper writes it back too
            out.append(str(num))
            out.append(w)
            num, seen = 0, False
            continue
        if seen:
            out.append(str(num))
            num, seen = 0, False
        if w.isdigit():
            out.append(str(int(w)))
        elif w not in NOISE:
            out.append(w)
    if seen:
        out.append(str(num))
    return out


def wer(ref: str, hyp: str) -> float:
    a, b = words(ref), words(hyp)
    if not a:
        return 0.0
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (x != y))
    return d[len(b)] / len(a)


def model():
    """Loaded once per process - it is used per line."""
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel("small.en", compute_type="int8")
    return _MODEL


def heard(path) -> str:
    segs, _ = model().transcribe(str(path), beam_size=5)
    return " ".join(s.text for s in segs).strip()


def check(path, text: str) -> tuple[float, str, bool]:
    """(wer, transcript, ok)."""
    h = heard(path)
    e = wer(text, h)
    return e, h, e <= FAIL
