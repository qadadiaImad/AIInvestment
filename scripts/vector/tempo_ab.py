"""How far can the VO be sped up before it stops being words?

Established first, by scripts/vector/pace_ab.py: Chatterbox has NO speed
control. `generate()` takes repetition_penalty, min_p, top_p,
audio_prompt_path, exaggeration, cfg_weight and temperature, and sweeping
cfg_weight from 0.20 to 0.50 moved the rate between 2.85 and 3.11 syllables
per second - noise, no trend. So "speed up the pronunciation" has to be done
after generation or not at all.

That leaves a tempo change, which this repo has a documented grudge against:
make_all_vo_local.py turned pitch correction off because "WSOLA
time-stretching smears speech and leaves a metallic edge". True - but that
was resampling for PITCH on every line. Changing tempo alone, by a little,
is a different operation, and the honest way to settle it is to measure
rather than to inherit the grudge.

Two tools, both in the full ffmpeg on this machine (NOT the minimal build
Remotion bundles): `atempo`, and `rubberband` which is the better
time-stretcher. Each rate is transcribed back with faster-whisper and scored
against the text that went in.

THE WER COMPARISON NORMALISES NUMBER WORDS. The first version of this gate
called every take of "Fifteen YEARS?!" a 50% error because Whisper writes it
"15 years" - a correct transcription scored as slurring. A gate that fails
on correct audio is worse than no gate, because it hides the real failures
among its own.

  <chatterbox-venv-python> scripts/vector/tempo_ab.py
"""
from __future__ import annotations

import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
FF = "C:/ffmpeg/bin/ffmpeg"
SRC = REPO / "remotion/public/audio/fairmarket_bshort"
OUT = REPO / "content/probe/tempo_ab"
RATES = [1.00, 1.08, 1.15, 1.22, 1.30, 1.38]

# The gate is RELATIVE to the untouched control, not absolute. The first
# version used an absolute 0.10 and failed the 1.00x control itself, because
# a small Whisper model has its own floor on short exclamatory lines - and a
# gate that fails on audio nobody touched cannot tell you anything about the
# audio you did touch. What matters is DAMAGE: how much worse a rate
# transcribes than the same words at 1.00x.
GATE_DELTA = 0.05    # allowed WER above the control
GATE_HF = 0.35       # allowed relative change in high-frequency energy share,
                     # which is where the "metallic edge" this repo warned
                     # about would show up

NUMWORD = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30",
    "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
    "eighty": "80", "ninety": "90", "hundred": "100", "percent": "%",
}


def norm(s: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z0-9']+", s.lower()):
        out.append(NUMWORD.get(w, w))
    return out


def wer(ref: str, hyp: str) -> float:
    a, b = norm(ref), norm(hyp)
    if not a:
        return 0.0
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (x != y))
    return d[len(b)] / len(a)


def stretch(src: Path, dst: Path, rate: float, filt: str) -> None:
    f = ("atempo=%.4f" % rate) if filt == "atempo" else ("rubberband=tempo=%.4f" % rate)
    subprocess.run([FF, "-v", "error", "-i", str(src), "-filter:a", f,
                    "-ar", "44100", str(dst), "-y"], check=True)


def dur(p: Path) -> float:
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def hf_share(p: Path) -> float:
    """Fraction of energy above 4kHz. A time-stretcher that is smearing
    transients pushes this around; a clean one barely moves it."""
    with wave.open(str(p)) as w:
        sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64)
    if ch == 2:
        x = x.reshape(-1, 2).mean(1)
    if len(x) < 2048:
        return 0.0
    win = 2048
    acc_hi = acc_all = 0.0
    for i in range(0, len(x) - win, win):
        sp = np.abs(np.fft.rfft(x[i:i + win] * np.hanning(win))) ** 2
        f = np.fft.rfftfreq(win, 1.0 / sr)
        acc_hi += sp[f > 4000].sum()
        acc_all += sp.sum()
    return float(acc_hi / (acc_all or 1.0))


def main() -> None:
    from faster_whisper import WhisperModel
    lines = {}
    import json
    for row in json.loads((REPO / "data/bubbles/short_lines.json").read_text("utf-8")):
        lines[row["vo"]] = row["line"]

    OUT.mkdir(parents=True, exist_ok=True)
    stt = WhisperModel("small.en", compute_type="int8")
    have = [s for s in lines if (SRC / (s + ".wav")).exists()]
    print("%d lines, %.2fs of audio\n" % (len(have), sum(dur(SRC / (s + ".wav")) for s in have)))

    table, per_line = {}, {}
    for filt in ("atempo", "rubberband"):
        for rate in RATES:
            if rate == 1.00 and filt == "rubberband":
                continue                       # identical to the atempo control
            errs, secs, hfs = [], 0.0, []
            for s in have:
                src = SRC / (s + ".wav")
                dst = OUT / ("%s_%s_%03d.wav" % (s, filt, int(rate * 100)))
                stretch(src, dst, rate, filt)
                segs, _ = stt.transcribe(str(dst), beam_size=5)
                hyp = " ".join(x.text for x in segs)
                e = wer(lines[s], hyp)
                errs.append(e)
                per_line[(filt, rate, s)] = (e, hyp.strip())
                hfs.append(hf_share(dst))
                secs += dur(dst)
            table[(filt, rate)] = (secs, float(np.mean(errs)), float(np.max(errs)),
                                   float(np.mean(hfs)))
            print("%-11s %.2fx  %5.2fs total  mean wer %.3f  worst %.3f  hf %.4f"
                  % (filt, rate, secs, np.mean(errs), np.max(errs), np.mean(hfs)))

    base_secs, base_mean, base_worst, base_hf = table[("atempo", 1.00)]
    print("\nCONTROL (1.00x, untouched) mean wer %.3f - this is the FLOOR, not damage."
          % base_mean)
    for s in have:
        e, hyp = per_line[("atempo", 1.00, s)]
        if e > 0:
            print("   %-18s wer %.2f  want %r  got %r" % (s, e, lines[s], hyp))

    print("\n%-11s %6s %9s %11s %10s %9s"
          % ("filter", "rate", "total", "wer damage", "hf drift", "saved"))
    ok = []
    for (filt, rate), (secs, mw, xw, hf) in sorted(table.items()):
        dmg = mw - base_mean
        drift = abs(hf - base_hf) / (base_hf or 1.0)
        bad = dmg > GATE_DELTA or drift > GATE_HF
        print("%-11s %6.2f %8.2fs %+10.3f %9.1f%% %8.2fs%s"
              % (filt, rate, secs, dmg, 100 * drift, base_secs - secs,
                 "   <-- fails" if bad else ""))
        if not bad and rate > 1.0:
            ok.append((rate, filt, secs, dmg, drift))
    if ok:
        # Rank by rate, then by SPECTRAL CLEANLINESS - not by rate alone. Both
        # filters clear the WER gate at every rate (speeding this voice up
        # costs literally nothing measurable in intelligibility), so the
        # decision is entirely about which one damages the timbre least, and
        # there rubberband - nominally the better stretcher - is 3-6x worse
        # than plain atempo on this material.
        top = max(r for r, *_ in ok)
        best = min((o for o in ok if o[0] == top), key=lambda o: o[4])
        r, f, secs, dmg, drift = best
        print("\nfastest clean at %.2fx: %s - %.2fs saved of %.2fs "
              "(wer damage %+.3f, hf drift %.1f%%)"
              % (r, f, base_secs - secs, base_secs, dmg, 100 * drift))
        for rr, ff, ss, dd, kk in sorted(ok):
            print("   %-11s %.2fx  drift %5.1f%%" % (ff, rr, 100 * kk))
    else:
        print("\nnothing beat the gate; leave the delivery alone")


if __name__ == "__main__":
    main()
