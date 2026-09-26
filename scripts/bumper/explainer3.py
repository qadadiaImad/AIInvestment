"""Explainer 2, presenter cut: Maya opens each scene on camera, then the data scene plays under her voice-over.

    cd scripts && python -m bumper.presenter gen ; <chatterbox python> -m bumper.presenter vc
    cd scripts && python -m bumper.explainer3 [ids...] [--force]   # -> references/bumper-report/fig/bumper_screen_presenter.mp4

Per scene timeline:  [hook: presenter large, left; scene content hidden; hook captions]
                     [voice-over: scene as designed; presenter card small, bottom-left]
Video inputs to ffmpeg: background clip loop (clip scenes) · RGBA overlay stream (this file) ·
presenter clip (trimmed to speech) · anchor still (card). Audio: hook_vc + gap + rest_vc.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import wave

import numpy as np

from . import explainer2 as X
from .explainer import FPS, FF, C, seg, caption_schedule, wrap
from .presenter import PRES, VOICE3, ANCHOR, CLIPS

D = X.D
WORK3 = X.R.ROOT / "data" / "bumper" / "explainer3"
WORK3.mkdir(parents=True, exist_ok=True)
FINAL = X.R.OUT / "bumper_screen_presenter.mp4"
GAP_S = 0.35
PAD_S = 0.9
BIG = dict(h=960, x=60, y=60)        # presenter during the hook (720x1280 clip scaled to 540x960)
CARD = dict(h=340, x=40, y=700)      # presenter card during the voice-over (191x340)
CHAR_CLIPS = {"06_dilution": "06_dilution_chars.mp4", "10_binding": "10_binding_chars.mp4"}


def wav_duration(p):
    with wave.open(str(p), "rb") as w:
        return w.getnframes() / w.getframerate()


def speech_end(p, thresh=0.02, tail=0.45):
    """last loud sample + tail, so the hook phase does not sit on trailing silence."""
    with wave.open(str(p), "rb") as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768
    loud = np.where(np.abs(x) > thresh)[0]
    end = (loud[-1] / sr if len(loud) else len(x) / sr) + tail
    return max(2.0, min(end, len(x) / sr))


def build_audio(hook_wav, rest_wav, out, sr=24000, hook_len=None, lag_frames=0):
    def load(p):
        with wave.open(str(p), "rb") as w:
            s = w.getframerate()
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768
            if w.getnchannels() == 2:
                x = x[::2]
        if s != sr:
            x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * sr / s)), np.arange(len(x)), x)
        return x
    h = load(hook_wav)
    if lag_frames:  # measured audio-trails-mouth offset (frames at 24 fps): advance the audio by that much
        k = int(round(abs(lag_frames) / 24 * sr))
        h = h[k:] if lag_frames > 0 else np.concatenate([np.zeros(k), h])
    if hook_len:
        h = h[: int(hook_len * sr)]
    r = load(rest_wav) if rest_wav and pathlib.Path(rest_wav).exists() else np.zeros(0)
    y = np.concatenate([h, np.zeros(int(GAP_S * sr)), r])
    y *= (10 ** (-1.5 / 20)) / (np.max(np.abs(y)) + 1e-9)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    return len(h) / sr, len(r) / sr


class Presented:
    """Wraps a scene: hides its content during the hook, offsets its clock, swaps captions."""

    def __init__(self, segment, hook_s, rest_s):
        self.hook_s, self.rest_s = hook_s, rest_s
        inner_seg = {**segment, "text": segment["rest"] or " "}
        self.scene = X.SCENES[segment["chart"]](inner_seg, max(rest_s, 0.5))
        self.scene.total = rest_s + PAD_S
        self.total = hook_s + GAP_S + rest_s + PAD_S
        self.hook_caps = caption_schedule(segment["hook"], hook_s)
        fig = self.scene.fig
        if segment["id"] in CHAR_CLIPS and segment["kind"] != "clip":
            fig.patch.set_alpha(0.62)  # opaque chart scene becomes a dimmed window onto the character clip
        self.content = list(fig.axes) + list(fig.patches) + [t for t in fig.texts if t is not self.scene.cap_txt and t.get_fontsize() > 10]
        self.titles = [t for t in fig.texts if t.get_position()[1] > 0.88 and t.get_fontsize() > 12]
        self.title_pos = [(t.get_position(), t.get_ha()) for t in self.titles]
        self.title_size = [t.get_fontsize() for t in self.titles]
        # hook-phase frame: a caption-styled hook line and the moved title
        self.hook_txt = fig.text(0.655, 0.09, "", ha="center", va="center", fontsize=15, color=C["ink"],
                                 bbox=dict(boxstyle="round,pad=0.6", fc="#0e131dee", ec="#1f2937"), zorder=60)

    def frame(self, t):
        sc = self.scene
        in_hook = t < self.hook_s + GAP_S * 0.5
        for a in self.content:
            a.set_visible(not in_hook or a in self.titles)
        for tx, ((x, y), ha), fs in zip(self.titles, self.title_pos, self.title_size):
            tx.set_position(((0.655 if ha == "center" else 0.34), y) if in_hook else (x, y))
            tx.set_fontsize(min(fs, 19) if in_hook else fs)  # a moved title must clear the top-right stamp
        if in_hook:
            sc.cap_txt.set_text("")
            self.hook_txt.set_text(next((wrap(s, 70) for a, b, s in self.hook_caps if a <= t < b), ""))
            sc.fig.canvas.draw()
        else:
            self.hook_txt.set_text("")
            tt = t - self.hook_s - GAP_S
            sc.update(max(tt, 0))
            sc.caption(max(tt, 0))
            # keep captions clear of the presenter card
            sc.cap_txt.set_position((0.57, 0.062))
            sc.fig.canvas.draw()
        return np.asarray(sc.fig.canvas.buffer_rgba())

    def close(self):
        sc = self.scene
        sc.close()


def render_segment(segment, manifest, force=False):
    sid = segment["id"]
    out = WORK3 / f"{sid}.mp4"
    m = manifest.get(sid)
    hook_vc = PRES / f"{sid}_hook_vc.wav"
    hook_raw = (PRES / m["file"]).with_suffix(".wav") if m and m.get("file") else None
    hook_wav = hook_vc if hook_vc.exists() else hook_raw
    rest_vc = VOICE3 / f"{sid}_rest_vc.wav"
    rest_raw = VOICE3 / f"{sid}_rest.wav"
    rest_wav = rest_vc if rest_vc.exists() else (rest_raw if rest_raw.exists() else None)
    if out.exists() and not force:
        return out
    pres_clip = PRES / m["file"]
    hook_s = speech_end(hook_wav)
    audio = WORK3 / f"{sid}_audio.wav"
    lag = m.get("lag", 0) if abs(m.get("lag", 0)) > 2 else 0  # only correct clips that failed the sync gate
    hook_s, rest_s = build_audio(hook_wav, rest_wav, audio, hook_len=hook_s, lag_frames=lag)
    P = Presented(segment, hook_s, rest_s)
    n = int(round(P.total * FPS))
    inputs, fc, vi = [], [], 0
    if segment["kind"] == "clip" or sid in CHAR_CLIPS:
        bg_src = CLIPS / CHAR_CLIPS.get(sid, f"{sid}.mp4")
        if not bg_src.exists():
            bg_src = CLIPS / f"{sid}.mp4"
        bg = X.palindrome(bg_src)
        inputs += ["-stream_loop", "-1", "-t", f"{P.total:.3f}", "-i", str(bg)]
        fc.append(f"[{vi}:v]scale=1920:1080:flags=lanczos,setsar=1[bg]")
        vi += 1
        base = "[bg]"
    else:
        inputs += ["-f", "lavfi", "-t", f"{P.total:.3f}", "-i", f"color=c={C['bg']}:s=1920x1080:r={FPS}"]
        fc.append(f"[{vi}:v]setsar=1[bg]")
        vi += 1
        base = "[bg]"
    inputs += ["-f", "rawvideo", "-pix_fmt", "rgba", "-s", "1920x1080", "-r", str(FPS), "-i", "-"]
    ov = vi
    vi += 1
    inputs += ["-i", str(pres_clip), "-loop", "1", "-t", f"{P.total:.3f}", "-i", str(ANCHOR), "-i", str(audio)]
    pv, av, ai = vi, vi + 1, vi + 2
    H = hook_s + GAP_S * 0.5
    fc += [f"{base}[{ov}:v]overlay=shortest=1:format=auto[o1]",
           f"[{pv}:v]scale=-2:{BIG['h']},drawbox=x=0:y=0:w=iw:h=ih:color=#22e07e@0.9:t=3[pb]",
           f"[o1][pb]overlay={BIG['x']}:{BIG['y']}:enable='lt(t,{H:.3f})'[o2]",
           f"[{av}:v]scale=-2:{CARD['h']},drawbox=x=0:y=0:w=iw:h=ih:color=#22e07e@0.9:t=2[pc]",
           f"[o2][pc]overlay={CARD['x']}:{CARD['y']}:enable='gte(t,{H:.3f})'[v]"]
    cmd = [FF, "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", f"{ai}:a",
           "-af", "apad", "-t", f"{P.total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        p.stdin.write(P.frame(f / FPS).tobytes())
    p.stdin.close()
    p.wait()
    P.close()
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed on {sid}")
    print(f"{sid}: hook {hook_s:.1f}s + rest {rest_s:.1f}s -> {out.name} ({n} frames)", flush=True)
    return out


def main(argv):
    segs = json.load(open(D / "narration3.json", encoding="utf-8"))
    manifest = json.load(open(PRES / "manifest.json", encoding="utf-8"))
    only = [a for a in argv if not a.startswith("-")]
    force = "--force" in argv
    parts = [render_segment(s, manifest, force) for s in segs if (not only or s["id"] in only) and manifest.get(s["id"], {}).get("file")]
    if not only:
        lst = WORK3 / "concat.txt"
        lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
        subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(FINAL)], check=True)
        print("final:", FINAL, f"{FINAL.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1:])
