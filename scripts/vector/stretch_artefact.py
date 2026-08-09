"""Where does a tempo change start SOUNDING processed?

tempo_ab.py answered a different question. It asked whether the words
survive - transcribe the stretched audio, compare to the input - and the
answer was that they survive perfectly to 1.38x. The owner then listened to
1.30x and said "artificial". Both are true: an ASR model does not care
whether speech sounds synthetic, only whether it is decodable. Word error
rate was the wrong instrument for this complaint.

atempo is overlap-add. It keeps pitch by splicing the waveform, and every
splice on a sustained voiced sound is a small discontinuity in the harmonic
structure. Individually inaudible; at a high enough rate they accumulate
into the warble people describe as "processed". That is measurable as
SPECTRAL FLUX - how much the spectrum jumps frame to frame - restricted to
the voiced parts, where the true spectrum should be changing slowly.

So: flux at 1.00x is the floor set by the speech itself, and the rate to
ship is the one before flux starts climbing away from it.

  <chatterbox-venv-python> scripts/vector/stretch_artefact.py
"""
from __future__ import annotations

import subprocess
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
FF = "C:/ffmpeg/bin/ffmpeg"
# The FULL episode's lines, because those are UNSTRETCHED. The Shorts cut on
# disk is already at 1.30x, so measuring further stretching from it would
# give a curve with no true baseline - the first thing this probe needed was
# a control that had not already had the treatment applied.
SRC = REPO / "remotion/public/audio/fairmarket_bubbles"
OUT = REPO / "content/probe/stretch_artefact"
RATES = [1.00, 1.08, 1.15, 1.22, 1.30, 1.40]
WIN, HOP = 1024, 256


def rd(p: Path):
    with wave.open(str(p)) as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64) / 32768.0
    if ch == 2:
        x = x.reshape(-1, 2).mean(1)
    return x, sr


def voiced_flux(x: np.ndarray, sr: int) -> float:
    """Mean normalised spectral flux over the LOUD frames only.

    Silence and breath have high relative flux for uninteresting reasons, so
    they are excluded - the artefact lives in sustained voiced sound.
    """
    if len(x) < WIN * 4:
        return 0.0
    w = np.hanning(WIN)
    mags, energy = [], []
    for i in range(0, len(x) - WIN, HOP):
        f = x[i:i + WIN] * w
        m = np.abs(np.fft.rfft(f))
        mags.append(m)
        energy.append(float(np.sqrt((f ** 2).mean())))
    mags = np.array(mags)
    energy = np.array(energy)
    if not len(energy):
        return 0.0
    loud = energy > np.percentile(energy, 60)
    fl = []
    for i in range(1, len(mags)):
        if not (loud[i] and loud[i - 1]):
            continue
        a, b = mags[i - 1], mags[i]
        d = np.linalg.norm(b - a) / (np.linalg.norm(a) + 1e-9)
        fl.append(d)
    return float(np.mean(fl)) if fl else 0.0


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # the longest, most sustained lines - where a splice artefact shows
    stems = ["b01_sol_bubble", "b09_sol_nomame", "b15_sol_parttwo",
             "b17_sol_only", "b31_sol_broker", "b45_sol_internet",
             "b21_rex_crowbar", "b16_rex_true"]
    have = [s for s in stems if (SRC / (s + ".wav")).exists()]
    if not have:
        raise SystemExit("no source lines - generate the short's VO first")

    print("source: the FULL episode's lines, which are unstretched, so
"
          "1.00x here is the true floor - the flux of the speech itself.
")
    print("%-6s %10s %9s" % ("rate", "flux", "vs 1.00x"))
    base = None
    for r in RATES:
        vals = []
        for s in have:
            src = SRC / (s + ".wav")
            if r == 1.00:
                x, sr = rd(src)
            else:
                dst = OUT / ("%s_%03d.wav" % (s, int(r * 100)))
                subprocess.run([FF, "-v", "error", "-i", str(src), "-filter:a",
                                "atempo=%.4f" % r, "-ar", "44100", str(dst), "-y"],
                               check=True)
                x, sr = rd(dst)
            vals.append(voiced_flux(x, sr))
        f = float(np.mean(vals))
        if base is None:
            base = f
        print("%-6.2f %10.4f %8.1f%%" % (r, f, 100 * (f / base - 1)))


if __name__ == "__main__":
    main()
