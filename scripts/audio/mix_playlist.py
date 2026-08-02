"""Fit the Habits reel's cut grid to a real track's beat grid.

Instead of forcing music onto the reel's fixed 1.7s grid, this measures the
track (BPM, beat phase, drop location) and emits:
  - content/probe/playlist_mix.wav   the aligned 18-bar segment, faded tail,
                                     sample 0 = reel frame 0
  - content/probe/playlist_props.json  {cutStarts, totalFrames} for the
                                     HabitsReel composition (fps 30)

Mapping: one reel cut unit = one 4/4 bar of the track. The reel's shot
structure in units is fixed (2,2,1,1,1,1,1,1,2,1,1,1,1,1,1); the track's
drop is pinned to unit 2 — the "TALENT LOSES TO ROUTINE" hook — so the two
sparse intro bars carry the Maya doubt shot, exactly like a montagem build.

Analysis is plain numpy/scipy (no librosa): spectral-flux onset envelope,
autocorrelation tempo in 60-200 BPM, comb search for beat phase, and the
drop = the beat with the biggest sustained jump in <150 Hz energy.

Usage:
    python scripts/audio/mix_playlist.py content/probe/playlist/andromeda.wav
"""
import json
import os
import sys
import wave

import numpy as np
from scipy.signal import butter, lfilter, stft

RATE = 48000
FPS = 30
UNITS = [2, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1]  # shots 00..14
BEATS_PER_UNIT = 4
DROP_UNIT = 2  # hook shot index in units — the drop lands here

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_WAV = os.path.join(REPO, "content", "probe", "playlist_mix.wav")
OUT_PROPS = os.path.join(REPO, "content", "probe", "playlist_props.json")


def load_wav(path):
    with wave.open(path, "rb") as w:
        assert w.getframerate() == RATE and w.getsampwidth() == 2, "expect 48k s16"
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        ch = w.getnchannels()
    x = raw.astype(np.float64).reshape(-1, ch) / 32768.0
    return x  # (n, ch)


def onset_envelope(mono):
    f, tt, z = stft(mono, RATE, nperseg=2048, noverlap=2048 - 512)
    mag = np.abs(z)
    flux = np.maximum(mag[:, 1:] - mag[:, :-1], 0).sum(axis=0)
    env_rate = RATE / 512
    return flux / (flux.max() + 1e-12), env_rate


def kick_grid(mono):
    """Measure the KICK grid directly — cuts must land on kicks, and the
    nominal BPM label is irrelevant. (A spectral-flux comb mislabeled this
    track 120 when its kick pattern is half-time on a ~150 grid.)

    Returns (period_s, phase_s, onset_env, env_rate) where period is the
    inter-kick interval found by autocorrelation of the <150 Hz onset
    envelope over 0.3-1.0 s lags, and phase maximizes the on-kick comb."""
    b, a = butter(2, 150 / (RATE / 2), btype="low")
    low = lfilter(b, a, mono) ** 2
    hop = 512
    frames = low[: len(low) // hop * hop].reshape(-1, hop).mean(axis=1)
    onset = np.maximum(np.diff(frames), 0)
    onset /= onset.max() + 1e-12
    er = RATE / hop
    e = onset - onset.mean()
    ac = np.correlate(e, e, "full")[len(e) - 1:]
    lo, hi = int(er * 0.30), int(er * 1.00)
    lag = lo + int(np.argmax(ac[lo:hi]))
    # prefer the smallest strong sub-multiple: kicks every p, ac also peaks at 2p
    for div in (4, 3, 2):
        sub = lag // div
        if sub >= lo and ac[sub] > 0.5 * ac[lag]:
            lag = sub
            break
    period = lag / er
    n = int(len(onset) / lag) - 2
    best = (-1e9, 0.0)
    for ph in np.linspace(0, lag, 64, endpoint=False):
        idx = (ph + lag * np.arange(n)).astype(int)
        score = onset[idx].mean()
        off = np.minimum(idx + lag // 2, len(onset) - 1)
        score -= onset[off].mean()
        if score > best[0]:
            best = (score, ph / er)
    return period, best[1]


def analyze_track(mono):
    """Measured kick grid + musically-sane unit + drop kick, shared by the
    single-track and two-track mixers. Returns (beat, beat_times, kpu,
    drop_beat)."""
    beat, phase = kick_grid(mono)
    n_beats = int((len(mono) / RATE - phase) / beat) - 1
    beat_times = phase + beat * np.arange(n_beats)

    # kicks per cut unit: prefer whole bars/half-bars (4, 2, 8) so cuts land
    # on downbeats, not cycling bar positions; only then nearest-to-1.7s
    for k in (4, 2, 8, 3, 6):
        if 1.4 <= k * beat <= 2.1:
            kpu = k
            break
    else:
        kpu = min((2, 3, 4, 6, 8), key=lambda k_: abs(k_ * beat - 1.7))

    # drop = FIRST kick that is itself loud (>=60% of max low-band) AND whose
    # next 2 units sustain >=85% of the loudest rolling level — the full slam,
    # not the half-weight bass entry (a 4-unit window picked 1 bar early once)
    b, a = butter(2, 150 / (RATE / 2), btype="low")
    low = lfilter(b, a, mono) ** 2
    per_beat = np.array([
        low[int(t0 * RATE):int((t0 + beat) * RATE)].mean() for t0 in beat_times
    ])
    w = 2 * kpu
    roll = np.array([per_beat[i:i + w].mean() for i in range(len(per_beat) - w)])
    ok = (roll >= 0.85 * roll.max()) & (per_beat[: len(roll)] >= 0.6 * per_beat.max())
    drop_beat = int(np.argmax(ok))
    return beat, beat_times, kpu, drop_beat


def main():
    src = sys.argv[1]
    x = load_wav(src)
    mono = x.mean(axis=1)
    beat, beat_times, kpu, drop_beat = analyze_track(mono)
    n_beats = len(beat_times)
    unit_s = kpu * beat

    total_beats = sum(UNITS) * kpu
    start_beat = drop_beat - DROP_UNIT * kpu  # 2 units of build before the drop
    if start_beat < 0:
        print(f"WARN drop at kick {drop_beat} too early; clamping")
        start_beat = 0
    if start_beat + total_beats > n_beats:
        start_beat = n_beats - total_beats
        print(f"WARN track short past drop; start shifted to kick {start_beat}")
    t_start = beat_times[start_beat]

    # cut starts (frames) from the REAL kick grid — drift never exceeds 1/2 frame
    starts_units = np.cumsum([0] + UNITS)  # 16 boundaries incl. end
    cut_starts = []
    for u in starts_units:
        k = u * kpu
        tb = beat_times[start_beat + k] - t_start if k < total_beats else total_beats * beat
        cut_starts.append(int(round(tb * FPS)))
    total_frames = cut_starts[-1]

    seg = x[int(t_start * RATE):int(t_start * RATE) + int(round(total_frames / FPS * RATE))].copy()
    fade = int(1.3 * RATE)  # tail fade so the loop point doesn't slam
    seg[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 1.5
    peak = np.max(np.abs(seg))
    seg *= (10 ** (-1.5 / 20)) / peak  # normalize to -1.5 dBFS

    inter = (seg * 32767).astype(np.int16).reshape(-1)
    with wave.open(OUT_WAV, "wb") as w_:
        w_.setnchannels(2)
        w_.setsampwidth(2)
        w_.setframerate(RATE)
        w_.writeframes(inter.tobytes())

    props = {"cutStarts": cut_starts[:-1], "totalFrames": total_frames}
    json.dump(props, open(OUT_PROPS, "w"), indent=1)

    print(f"kick period {beat:.4f}s ({60 / beat:.1f} kicks/min)  unit = {kpu} kicks = {unit_s:.3f}s")
    print(f"drop at kick {drop_beat} = {beat_times[drop_beat]:.2f}s; segment starts {t_start:.2f}s")
    print(f"total {total_frames} frames = {total_frames / FPS:.2f}s; cuts at {cut_starts[:-1]}")
    print(f"OK {OUT_WAV} + {OUT_PROPS}")


if __name__ == "__main__":
    main()
