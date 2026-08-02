"""Two-track mix for the Habits reel: dark bed for doubt/habits, a harder
track taking over at the payoff.

Timeline (18 units, one unit = the hard track's measured bar):
  units 0-12   dark bed (make_phonk.py --mode dark, synthesized AT the hard
               track's bar length so the grid never breaks)
  unit  12     hard track enters with its own 2 pre-drop bars — its natural
               build, fill and pre-drop silence become the transition
  unit  14     the hard track's drop = "IT COMPOUNDS", the narrative turn
  unit  18     end, 1.3 s tail fade

The video is NOT re-rendered: the hard track's kick grid is uniform, so the
cut frames are identical to the single-track render — this only replaces
audio. Emits content/probe/two_track_mix.wav + two_track_props.json (equality
with playlist_props.json is asserted, which is what makes the remux legal).

Usage:
    python scripts/audio/mix_two.py content/probe/dark_bed.wav \
        content/probe/playlist/andromeda.wav
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mix_playlist import FPS, RATE, UNITS, analyze_track, load_wav  # noqa: E402

import wave  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_WAV = os.path.join(REPO, "content", "probe", "two_track_mix.wav")
OUT_PROPS = os.path.join(REPO, "content", "probe", "two_track_props.json")

HANDOFF_UNIT = 12   # dark bed ends here; hard track enters (JOURNAL EVERYTHING)
PREDROP_UNITS = 2   # hard track's own build occupies units 12-14
# => drop lands at unit 14 = "IT COMPOUNDS"


def main():
    dark_path, hard_path = sys.argv[1], sys.argv[2]
    dark = load_wav(dark_path)
    hard = load_wav(hard_path)
    mono = hard.mean(axis=1)
    beat, beat_times, kpu, drop_beat = analyze_track(mono)
    unit_s = kpu * beat
    total_units = sum(UNITS)  # 18

    # the dark bed must have been synthesized at this exact bar length
    dark_units = len(dark) / RATE / unit_s
    assert abs(dark_units - HANDOFF_UNIT) < 0.02, f"dark bed is {dark_units:.3f} units"

    total_frames = int(round(total_units * unit_s * FPS))
    total_samples = int(round(total_frames / FPS * RATE))
    buf = np.zeros((total_samples, 2))

    # dark half, with a 20 ms fade-out at the seam so the splice can't click
    d = dark.copy()
    n_fade = int(0.02 * RATE)
    d[-n_fade:] *= np.linspace(1, 0, n_fade)[:, None]
    buf[: len(d)] += d

    # hard half: enter PREDROP_UNITS before its measured drop
    entry_beat = drop_beat - PREDROP_UNITS * kpu
    assert entry_beat >= 0, "hard track's drop is too early for a 2-bar entry"
    t_entry = beat_times[entry_beat]
    seam = int(round(HANDOFF_UNIT * unit_s * RATE))
    need = total_samples - seam
    seg = hard[int(t_entry * RATE): int(t_entry * RATE) + need].copy()
    assert len(seg) == need, "hard track too short past its drop"
    seg[:n_fade] *= np.linspace(0, 1, n_fade)[:, None]
    seg *= (10 ** (-1.0 / 20)) / np.max(np.abs(seg))  # the drop may run hotter
    fade = int(1.3 * RATE)
    seg[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 1.5
    buf[seam:] += seg

    peak = np.max(np.abs(buf))
    if peak > 10 ** (-1.0 / 20):
        buf *= (10 ** (-1.0 / 20)) / peak
    rms_db = 20 * np.log10(np.sqrt(np.mean(buf.mean(axis=1) ** 2)))

    inter = (buf * 32767).astype(np.int16).reshape(-1)
    with wave.open(OUT_WAV, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(inter.tobytes())

    starts_units = np.cumsum([0] + UNITS)
    cut_starts = [int(round(u * unit_s * FPS)) for u in starts_units]
    props = {"cutStarts": cut_starts[:-1], "totalFrames": cut_starts[-1]}
    json.dump(props, open(OUT_PROPS, "w"), indent=1)

    old = json.load(open(os.path.join(REPO, "content", "probe", "playlist_props.json")))
    same_grid = old == props
    print(f"unit {unit_s:.4f}s; handoff at {HANDOFF_UNIT * unit_s:.2f}s; "
          f"hard drop at {(HANDOFF_UNIT + PREDROP_UNITS) * unit_s:.2f}s (unit {HANDOFF_UNIT + PREDROP_UNITS})")
    print(f"total {props['totalFrames']} frames; grid identical to single-track render: {same_grid}")
    print(f"rms {rms_db:.1f} dBFS  OK {OUT_WAV}")
    if not same_grid:
        print("RE-RENDER REQUIRED with two_track_props.json")


if __name__ == "__main__":
    main()
