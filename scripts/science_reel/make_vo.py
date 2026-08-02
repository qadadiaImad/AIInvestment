"""Narration for the Science reel — the SPEECH drives the cut grid.

v1 squeezed lines into the fixed 1.7s grid and three lines overlapped the
next line's start (double-voice collisions — the "abrupt transitions").
Now each shot's duration is derived from its measured line:
    dur = max(min_dur, lead_in + line + gap)
so overlaps are impossible by construction, and the reel breathes where the
narration needs room. Emits cutStarts/totalFrames for the composition
(which already accepts a custom grid) plus the assembled VO track with
60 ms edge fades. Video shots are asserted against their source lengths.

    python scripts/science_reel/make_vo.py

Copy rules: accusations attributed ("they say / they call"), no first
person, no income claims.
"""
import json
import os
import subprocess
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(REPO, "content", "probe", "science_vo")
OUT = os.path.join(REPO, "content", "probe", "science_vo.wav")
OUT_PROPS = os.path.join(REPO, "content", "probe", "science_vo_props.json")
CLI = os.path.expanduser("~/tools/grok-cli/grok-cli.exe")

RATE = 48000
FPS = 30
VOICE = "atlas"
LEAD = 0.15   # cut -> voice onset
GAP = 0.45    # voice end -> next cut

# one entry per shot 0..15: (text or None, min_dur_s, max_dur_s or None)
# max_dur guards video shots against their 6.04s / 3.04s sources.
SHOT_LINES = [
    ("They say trading isn't a real science.", 3.2, 6.0),   # hook (vid)
    ("They call it gambling.", 1.6, None),
    ("Pure luck.", 1.4, None),
    ("Some even call it unethical.", 1.6, None),
    ("But here's what it actually runs on.", 1.6, None),    # pivot + flash
    ("Probability.", 1.4, None),
    ("Statistics.", 1.4, None),
    ("Stochastic calculus.", 1.4, None),
    ("The same random walks that move particles... move prices.", 3.0, 6.0),  # vid
    ("Computer science.", 1.4, None),
    ("Algorithms.", 1.4, None),
    ("Game theory.", 1.4, None),
    ("Machine learning.", 1.4, None),
    ("And the science of human behavior.", 1.6, None),
    ("It isn't luck. It's mathematics.", 1.8, 3.0),          # closer (vid)
    ("Study the science.", 1.8, 3.0),                        # ender (vid)
]


def tts(text, dest):
    p = subprocess.run(
        [CLI, "tts", "--voice-id", VOICE, "--output-format", "wav",
         "--sample-rate", str(RATE), "--output", dest, "--text", text],
        capture_output=True, text=True, timeout=180,
    )
    if p.returncode != 0 or not os.path.exists(dest):
        raise RuntimeError(f"tts failed: {p.stderr[-300:]} {p.stdout[-300:]}")


def load_trim(path):
    with wave.open(path, "rb") as w:
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        ch, sr = w.getnchannels(), w.getframerate()
    x = raw.astype(np.float64).reshape(-1, ch).mean(axis=1) / 32768.0
    if sr != RATE:
        n = int(len(x) * RATE / sr)
        x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)
    loud = np.where(np.abs(x) > 0.005)[0]
    if len(loud):
        x = x[max(0, loud[0] - 240): loud[-1] + 1200]
    f = int(0.06 * RATE)  # 60 ms edge fades kill clicks at line joins
    x[:f] *= np.linspace(0, 1, f)
    x[-f:] *= np.linspace(1, 0, f)
    return x


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    clips, durs = [], []
    for k, (text, _, _) in enumerate(SHOT_LINES):
        dest = os.path.join(OUT_DIR, f"s{k:02d}.wav")
        if not os.path.exists(dest):
            tts(text, dest)
        x = load_trim(dest)
        clips.append(x)
        durs.append(len(x) / RATE)

    starts_s, t = [], 0.0
    for k, (text, min_dur, max_dur) in enumerate(SHOT_LINES):
        starts_s.append(t)
        need = LEAD + durs[k] + GAP
        dur = max(min_dur, need)
        if max_dur is not None:
            assert dur <= max_dur, f"shot {k} needs {dur:.2f}s > source {max_dur}s"
        print(f"[{k:02d}] cut {t:6.2f}s  line {durs[k]:4.2f}s  shot {dur:4.2f}s  {text}")
        t += dur
    total_s = t

    cut_starts = [int(round(s * FPS)) for s in starts_s]
    total_frames = int(round(total_s * FPS))
    json.dump({"cutStarts": cut_starts, "totalFrames": total_frames},
              open(OUT_PROPS, "w"), indent=1)

    buf = np.zeros(int(total_s * RATE) + RATE)
    for k, x in enumerate(clips):
        i = int((starts_s[k] + LEAD) * RATE)
        buf[i:i + len(x)] += x
    buf = buf[: int(total_s * RATE)]
    buf *= (10 ** (-1.5 / 20)) / np.max(np.abs(buf))
    inter = np.repeat((buf * 32767).astype(np.int16), 2)
    with wave.open(OUT, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(inter.tobytes())
    print(f"OK {OUT} {total_s:.2f}s + {OUT_PROPS} ({total_frames} frames)")


if __name__ == "__main__":
    main()
