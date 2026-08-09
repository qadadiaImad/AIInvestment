"""Pin each character's voice to a CANON, so the TTS may drift and the
show does not.

THE PROBLEM. grok's TTS is not stable across sessions. Same tool, same
voice-id, different day - measured 2026-08-04, band-limited to the range
both sample rates share:

    Rex, original session   pitch 180.0 Hz   rolloff85 3331 Hz
    Rex, a later session    pitch 166.4 Hz   rolloff85 4528 Hz
    Rex, later still        pitch 161.7 Hz   rolloff85 5124 Hz

Two semitones down and half again as bright. Clearly audible.

WHY "JUST REGENERATE EVERYTHING IN ONE PASS" IS THE WRONG FIX, and the
owner is right to reject it: it does not scale. Episode 12 would require
regenerating episodes 1 through 11 to match, every time, forever. The
back catalogue cannot be a dependency of the next episode.

THE FIX. The voice identity stops living on someone else's server. A
canonical profile per character is stored in this repo - measured once,
from the take everyone agreed sounded right - and every line generated
on any future day is corrected onto it. The TTS becomes a source of
PERFORMANCE (words, timing, delivery); the canon owns IDENTITY (pitch,
brightness).

Two corrections, both deterministic, both pure numpy so they do not
depend on Remotion's minimal ffmpeg build (which ships no equalizer and
no rubberband):

  * PITCH - resample the waveform by the ratio canon_f0 / measured_f0,
    then restore the original duration by resampling back in time. Net
    effect is a pitch shift with the running time preserved, which
    matters because beat timings are derived from these durations.
  * BRIGHTNESS - a gentle first-order shelf that tilts the spectrum onto
    the canon's 85% rolloff. Bounded hard, because a big tilt sounds
    like a broken filter rather than a different microphone.

  python scripts/vector/voice_canon.py --measure   # print the profiles
  python scripts/vector/voice_canon.py --set-canon # freeze the canon
  python scripts/vector/voice_canon.py --apply     # correct every line
"""
from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
CANON = REPO / "remotion" / "src" / "fixtures" / "cast_ep1" / "voice_canon.json"
VO_DIRS = [REPO / "remotion" / "public" / "audio" / "fairmarket",
           REPO / "remotion" / "public" / "audio" / "fairmarket_ep2"]

# The canon is measured from these - the take the owner signed off on as
# sounding right. Episode 1's original session.
CANON_SOURCE = {
    "rex": ["v2_rex_fundamentals", "v5_rex_what", "v7_rex_index",
            "v9_rex_filings", "a2_rex_copy", "a2_rex_useless"],
    "sal": ["v1_sol_intro", "v3_sol_ha", "v4_sol_politics",
            "v6_sol_exhibit", "v8_sol_legal", "v10_sol_learning"],
}
BAND = 11000.0          # compare inside the range every sample rate shares
MAX_SEMITONES = 3.0     # refuse to "fix" more than this; something else is wrong
MAX_TILT_DB = 6.0


def read(p: Path):
    with wave.open(str(p)) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64)
    return x / 32768.0, sr


def write(p: Path, x: np.ndarray, sr: int) -> None:
    x = np.clip(x, -1.0, 1.0)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def measure(x: np.ndarray, sr: int):
    """Median pitch over voiced frames, and the 85% spectral rolloff.

    The first version of this sampled only the first four seconds with
    non-overlapping windows and no voicing gate, and it read the SAME
    line as 190.7 Hz once and 156.9 Hz another time — noise big enough
    to have shifted the whole cast by three semitones in the wrong
    direction. It now walks the entire file with 50% overlap and rejects
    frames whose autocorrelation peak is weak, which is the difference
    between measuring a voice and measuring a consonant.
    """
    v = x[np.abs(x) > 0.015]
    if len(v) < sr // 4:
        return None
    f0s = []
    win = int(sr * 0.045)
    hop = win // 2
    for i in range(0, len(v) - win, hop):
        f = v[i:i + win] - v[i:i + win].mean()
        if np.sqrt((f ** 2).mean()) < 0.04:
            continue
        f = f * np.hanning(len(f))
        ac = np.correlate(f, f, "full")[len(f) - 1:]
        lo, hi = int(sr / 320), int(sr / 70)
        if hi >= len(ac):
            continue
        seg = ac[lo:hi]
        if seg.max() <= 0.25 * ac[0]:      # weak periodicity: not voiced
            continue
        f0s.append(sr / (lo + int(np.argmax(seg))))
    if len(f0s) < 4:
        return None
    seg = v[:sr * 3] * np.hanning(len(v[:sr * 3]))
    S = np.abs(np.fft.rfft(seg))
    fr = np.fft.rfftfreq(len(seg), 1.0 / sr)
    m = fr <= BAND
    c = np.cumsum(S[m])
    roll = float(fr[m][np.searchsorted(c, 0.85 * c[-1])])
    return float(np.median(f0s)), roll


def stretch(x: np.ndarray, sr: int, rate: float) -> np.ndarray:
    """Time-stretch by `rate` WITHOUT changing pitch — overlap-add with
    cross-correlation alignment (WSOLA).

    This is the piece the first version was missing. It tried to hold the
    duration by resampling back, which exactly undoes the resample that
    shifted the pitch: net effect nothing but interpolation noise. Real
    pitch-shift-at-constant-length is resample (pitch+speed) THEN stretch
    the speed back (pitch untouched), and the stretch has to be a genuine
    overlap-add or the two operations just cancel again.
    """
    if abs(rate - 1.0) < 1e-3:
        return x
    win = int(sr * 0.046)
    hop_out = win // 2
    hop_in = int(round(hop_out * rate))
    seek = max(2, int(sr * 0.004))          # alignment search radius
    w = np.hanning(win)
    out = np.zeros(int(len(x) / rate) + win * 2)
    norm = np.zeros_like(out)
    prev_tail = None
    ip = op = 0
    while ip + win + seek < len(x) and op + win < len(out):
        best = ip
        if prev_tail is not None:
            lo = max(0, ip - seek)
            hi = min(len(x) - win, ip + seek)
            cand = np.arange(lo, hi)
            if len(cand):
                scores = [float(np.dot(prev_tail, x[c:c + len(prev_tail)]))
                          for c in cand]
                best = int(cand[int(np.argmax(scores))])
        seg = x[best:best + win] * w
        out[op:op + win] += seg
        norm[op:op + win] += w
        prev_tail = x[best + hop_out:best + win]
        ip = best + hop_in
        op += hop_out
    norm[norm < 1e-6] = 1.0
    return out[:int(len(x) / rate)] / norm[:int(len(x) / rate)]


def shift_pitch(x: np.ndarray, sr: int, ratio: float) -> np.ndarray:
    """Pitch by `ratio`, duration unchanged.

    Duration must be preserved: every beat boundary in both episodes is
    derived from these file lengths by retime_beats.py.
    """
    if abs(ratio - 1.0) < 1e-3:
        return x
    n = len(x)
    # 1. resample -> pitch * ratio, length / ratio
    idx = np.arange(0, n - 1, ratio)
    y = np.interp(idx, np.arange(n), x)
    # 2. stretch back to n samples, leaving the new pitch alone
    y = stretch(y, sr, len(y) / n)
    if len(y) < n:
        y = np.pad(y, (0, n - len(y)))
    return y[:n]


def tilt(x: np.ndarray, sr: int, db: float) -> np.ndarray:
    """First-order high shelf above 2 kHz, +/- db. FFT domain so it needs
    no filter-design dependency and no ffmpeg equalizer."""
    if abs(db) < 0.3:
        return x
    n = len(x)
    S = np.fft.rfft(x)
    fr = np.fft.rfftfreq(n, 1.0 / sr)
    g = 10 ** (db / 20.0)
    ramp = np.clip((fr - 2000.0) / 6000.0, 0.0, 1.0)
    return np.fft.irfft(S * (1.0 + (g - 1.0) * ramp), n)


def voice_of(stem: str) -> str:
    return "rex" if "_rex_" in stem or stem.endswith("_rex") else "sal"


def collect():
    out = {}
    for d in VO_DIRS:
        for p in sorted(d.glob("*.wav")):
            if p.stem.startswith("_"):
                continue
            out[p.stem] = p
    return out


def main() -> None:
    files = collect()
    if "--measure" in sys.argv or "--set-canon" in sys.argv:
        canon = {}
        for voice, stems in CANON_SOURCE.items():
            vals = []
            for s in stems:
                if s in files:
                    m = measure(*read(files[s]))
                    if m:
                        vals.append(m)
            if not vals:
                sys.exit("no canon source files found for " + voice)
            canon[voice] = {"f0": float(np.median([v[0] for v in vals])),
                            "rolloff": float(np.median([v[1] for v in vals])),
                            "from": stems, "n": len(vals)}
            print("%-4s canon  pitch %6.1f Hz   rolloff85 %6.0f Hz  (n=%d)"
                  % (voice, canon[voice]["f0"], canon[voice]["rolloff"],
                     len(vals)))
        if "--set-canon" in sys.argv:
            CANON.write_text(json.dumps(canon, indent=1), "utf-8")
            print("froze canon -> " + CANON.name)
        return

    if "--apply" not in sys.argv:
        print(__doc__)
        return

    canon = json.loads(CANON.read_text("utf-8"))
    fixed = skipped = 0
    for stem, p in files.items():
        voice = voice_of(stem)
        c = canon.get(voice)
        if not c:
            continue
        x, sr = read(p)
        m = measure(x, sr)
        if not m:
            skipped += 1
            continue
        f0, roll = m
        semis = 12 * np.log2(c["f0"] / f0)
        if abs(semis) > MAX_SEMITONES:
            print("  SKIP %-24s would need %+.1f semitones - too far, "
                  "check the source" % (stem, semis))
            skipped += 1
            continue
        db = float(np.clip(20 * np.log10(c["rolloff"] / max(roll, 1.0))
                           * 0.5, -MAX_TILT_DB, MAX_TILT_DB))
        if abs(semis) < 0.15 and abs(db) < 0.3:
            continue
        y = tilt(shift_pitch(x, sr, c["f0"] / f0), sr, db)
        peak = np.abs(y).max()
        if peak > 0.99:
            y = y * (0.99 / peak)
        write(p, y, sr)
        fixed += 1
        print("  %-24s %6.1f -> %6.1f Hz (%+.2f st)  tilt %+.1f dB"
              % (stem, f0, c["f0"], semis, db))
    print("\ncorrected " + str(fixed) + " files onto canon, "
          + str(skipped) + " skipped")
    print("durations are unchanged, so beat timings still hold")


if __name__ == "__main__":
    main()
