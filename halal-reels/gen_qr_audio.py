"""Generate all audio for the QuarterlyReport reel — 100% offline/free.

Voice: Windows SAPI (Microsoft David) synthesizes each line, then numpy pitches
it up ~1.16x — the classic "South Park" recipe (a normal voice pitched up). Music:
a numpy-synthesized minor-key newsroom bed (bass ostinato + kick pulse + ticker
hats + tense lead motif). Writes public/qr_l1..l5.wav and public/qr_news_bed.wav.

    python gen_qr_audio.py

Re-run after editing LINES to regenerate the VO; the printed per-line frame counts
feed the CUE/beat timing in src/QuarterlyReport.tsx.
"""
import pathlib
import subprocess
import tempfile
import wave

import numpy as np

PUB = pathlib.Path(__file__).resolve().parent / "public"
SR = 22050
PITCH = 1.16  # ~ +2.5 semitones — deadpan-cartoon, still intelligible

LINES = {
    "l1": "Welcome to the quarterly report.",
    "l2": "This quarter, the market called Nvidia a bubble.",
    "l3": "A model says it's worth one point eight times the price. So, half off.",
    "l4": "So naturally, everyone sold it.",
    "l5": "Great job, everyone.",
}


def sapi_synth(tmp: pathlib.Path):
    """Drive Windows SAPI via PowerShell to write one raw wav per line."""
    items = ";".join(f"'{k}'='{v.replace(chr(39), chr(39) * 2)}'" for k, v in LINES.items())
    ps = f"""
Add-Type -AssemblyName System.Speech
$v = New-Object System.Speech.Synthesis.SpeechSynthesizer
$v.SelectVoice('Microsoft David Desktop'); $v.Rate = -1
$lines = @{{{items}}}
foreach ($k in $lines.Keys) {{
 $p = Join-Path '{tmp}' ($k + '_raw.wav')
 $v.SetOutputToWaveFile($p); $v.Speak($lines[$k]); $v.SetOutputToNull()
}}
$v.Dispose()
"""
    subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps], check=True, capture_output=True)


def read_wav(p):
    w = wave.open(str(p), "rb")
    n, sr, ch = w.getnframes(), w.getframerate(), w.getnchannels()
    d = np.frombuffer(w.readframes(n), dtype=np.int16)
    w.close()
    if ch == 2:
        d = d.reshape(-1, 2).mean(1).astype(np.int16)
    return d.astype(np.float32) / 32768.0, sr


def write_wav(p, sig, sr=SR):
    PUB.mkdir(parents=True, exist_ok=True)
    w = wave.open(str(p), "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(sig, -1, 1) * 32767).astype(np.int16).tobytes())
    w.close()


def trim(sig, sr, thr=0.012):
    idx = np.where(np.abs(sig) > thr)[0]
    if not len(idx):
        return sig
    return sig[max(0, idx[0] - int(0.02 * sr)):min(len(sig), idx[-1] + int(0.06 * sr))]


def pitch_up(sig, p):
    n = len(sig); m = int(n / p)
    return np.interp(np.linspace(0, n - 1, m), np.arange(n), sig).astype(np.float32)


def gen_voice():
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        sapi_synth(tmp)
        for k in LINES:
            sig, sr = read_wav(tmp / f"{k}_raw.wav")
            sig = trim(sig, sr); sig = pitch_up(sig, PITCH); sig = trim(sig, sr)
            f = int(0.01 * sr); sig[:f] *= np.linspace(0, 1, f); sig[-f:] *= np.linspace(1, 0, f)
            sig = sig / (np.max(np.abs(sig)) or 1) * 0.92
            write_wav(PUB / f"qr_{k}.wav", sig, sr)
            print(f"  qr_{k}.wav  {len(sig)/sr:.2f}s  ({round(len(sig)/sr*30)} frames)")


def _note(f, dur, kind="tri", dec=6.0):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    if kind == "sine":
        w = np.sin(2 * np.pi * f * t)
    elif kind == "lead":
        w = 0.7 * np.sin(2 * np.pi * f * t) + 0.3 * (2 * (t * f - np.floor(t * f + 0.5)))
    else:  # tri
        w = 2 * np.abs(2 * (t * f - np.floor(t * f + 0.5))) - 1
    return w * np.exp(-dec * t)


def gen_music():
    def kick(dur=0.28):
        t = np.linspace(0, dur, int(SR * dur), endpoint=False)
        return np.sin(2 * np.pi * (110 * np.exp(-18 * t) + 45) * t) * np.exp(-9 * t)

    def hat(dur=0.05):
        n = np.random.RandomState(3).randn(int(SR * dur))
        return n * np.exp(-60 * np.linspace(0, dur, len(n)))

    NN = {"A1": 55, "A2": 110, "F2": 87.31, "G2": 98, "A4": 440, "C5": 523.25, "E5": 659.25, "D5": 587.33}
    beat = 0.6; SPB = int(SR * beat)
    bass_seq = ["A2", "A2", "F2", "G2"]
    lead_seq = ["A4", "C5", "E5", "C5", "D5", "C5", "A4", "A4"]
    bar = np.zeros(SPB * 4)
    dr = _note(NN["A1"], beat * 4, "sine", 0.15) * 0.22 + _note(NN["A2"], beat * 4, "sine", 0.12) * 0.12
    bar[:len(dr)] += dr
    for i, b in enumerate(bass_seq):
        s = i * SPB
        seg = _note(NN[b], beat, "tri", 3.2) * 0.5; bar[s:s + len(seg)] += seg[:len(bar) - s]
        k = kick(); bar[s:s + len(k)] += k[:len(bar) - s] * 0.6
    for i in range(8):
        s = int(i * SPB / 2)
        if i % 2 == 1:
            h = hat(); bar[s:s + len(h)] += h[:len(bar) - s] * 0.08
        ln = _note(NN[lead_seq[i]], beat / 2, "lead", 5.0) * 0.2; bar[s:s + len(ln)] += ln[:len(bar) - s]
    song = np.tile(bar, 7)[:int(SR * 16.8)]
    fi, fo = int(SR * 0.5), int(SR * 1.2)
    song[:fi] *= np.linspace(0, 1, fi); song[-fo:] *= np.linspace(1, 0, fo)
    song = song / (np.max(np.abs(song)) or 1) * 0.85
    write_wav(PUB / "qr_news_bed.wav", song)
    print(f"  qr_news_bed.wav  {len(song)/SR:.1f}s")


if __name__ == "__main__":
    print("voice (SAPI David, pitched %.2fx):" % PITCH)
    gen_voice()
    print("music (numpy newsroom bed):")
    gen_music()
    print("done -> halal-reels/public/")
