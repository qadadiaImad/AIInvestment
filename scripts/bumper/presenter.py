"""Presenter cut: Maya speaks each scene's hook on camera; the rest is voice-over in her voice.

    cd scripts && python -m bumper.presenter gen        # grok native-dialogue clips + STT gate (system python)
    C:/Users/imadq/tools/chatterbox-venv/Scripts/python.exe -m bumper.presenter vc   # voice-convert to Maya's clone

The on-camera standard (owner-approved 2026-08-02, see memory maya-talking-pipeline):
start-frame mode from the canonical still, calm-delivery prompt, one short line group per
clip, STT-verify with best-of-N, then Chatterbox VC to Maya's cloned voice with the output
resampled to the exact source duration so native lip timing survives.
Extra clips for character scenes (investors at the table, the contract handshake) are
atmosphere only: no text, numbers, charts or logos in the prompt.
"""
from __future__ import annotations

import difflib
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.request
import wave

ROOT = pathlib.Path(__file__).resolve().parents[2]
D = ROOT / "data" / "bumper" / "2026-09-25"
PRES = ROOT / "data" / "bumper" / "presenter"
VOICE3 = ROOT / "data" / "bumper" / "voice3"
CLIPS = ROOT / "data" / "bumper" / "clips"
CLI = pathlib.Path.home() / "tools" / "grok-cli" / "grok-cli.exe"
ANCHOR = ROOT / "higgs" / "persona_lifestyle" / "maya_podcast_anchor.png"
MAYA_REF = ROOT / "higgs" / "persona_lifestyle" / "maya_voice_sample.wav"
PRES.mkdir(parents=True, exist_ok=True)

SETTING = ("The woman from the input image stays seated at the same podcast desk in the same dark studio, same framing, "
           "static camera, same lighting. She speaks calmly and naturally into the microphone, saying exactly: ")
STYLE = (" Relaxed natural mouth movements, subtle facial expressions, minimal head motion, unhurried delivery, "
         "she remains in the same position throughout. Photorealistic. NO readable text, NO logos, NO watermarks.")
MIN_SIM = 0.85
MAX_LAG = 2          # frames at 24 fps between audio envelope and mouth motion
ATTEMPTS = 3
VIDEO_MODEL = "grok-imagine-video-1.5"   # the CLI default (grok-imagine-video) lip-syncs 7-10 frames late on ~40% of clips

STYLE_CLIP = ("Isometric 3D illustration, dark navy background, neon green and amber accent lighting, clean minimal corporate style, "
              "cinematic slow camera move, soft volumetric light, high detail. Strictly no text, no numbers, no letters, no charts, no logos, no captions.")
CHARACTER_CLIPS = {
    "06_dilution": STYLE_CLIP + " A boardroom table seen from above: a small founder figurine at the head, six glass investor figurines seated around a glowing green pie in the centre; "
                                "a hand keeps adding new amber investor figurines to the table and with each one the pie is cut into thinner slices.",
    "10_binding": STYLE_CLIP + " Three stylised glass figurines on a dark stage: a founder in the middle shakes hands with a customer figurine over a glowing green scroll, while behind them "
                               "a third figurine holding a bag of coins leans in and drops coins into the founder's pocket; a faint dotted line connects the customer and the coin-holder.",
}

CONTRACTIONS = {"isn't": "is not", "it's": "it is", "here's": "here is", "don't": "do not", "can't": "can not", "that's": "that is"}


def norm(text):
    t = text.lower()
    for k, v in CONTRACTIONS.items():
        t = t.replace(k, v)
    t = t.replace("1,126", "eleven hundred twenty six").replace("u.s.", "us")
    return re.sub(r"[^a-z ]+", " ", t).split()


def similarity(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def spoken_numbers(text):
    """grok reads '1,126' fine but '8-K' and '180' can drift; keep the text, the STT normaliser absorbs it."""
    return text


def grok_video(prompt, out, image=None, duration=10, timeout=600):
    args = [str(CLI), "video", "--json", "--model", VIDEO_MODEL, "--duration", str(duration), "--timeout", str(timeout), "--prompt", prompt]
    if image:
        args += ["--image", str(image)]
    else:
        args += ["--aspect-ratio", "16:9"]
    r = subprocess.run(args, capture_output=True, text=True)
    lines = [l for l in r.stdout.splitlines() if l.startswith('{"ok"')]
    if not lines:
        return None, (r.stderr or r.stdout)[-300:]
    j = json.loads(lines[-1])
    if not j.get("ok"):
        return None, str(j)[:300]
    urllib.request.urlretrieve(j["data"]["video"], out)
    return out, None


def stt(mp4):
    wav = mp4.with_suffix(".wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-vn", "-ac", "1", "-ar", "16000", str(wav)], check=True)
    r = subprocess.run([str(CLI), "stt", "--json", str(wav)], capture_output=True, text=True)
    try:
        j = json.loads(r.stdout.strip().splitlines()[-1])
        return j["data"].get("text") or j["data"].get("transcript") or ""
    except Exception:
        return ""


def lip_lag(mp4, crop="220:150:250:360", fps=24):
    """frames by which the audio envelope trails mouth-region motion (0 = in sync); plus the correlation."""
    import numpy as np
    wav = mp4.with_suffix(".wav")
    if not wav.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-vn", "-ac", "1", "-ar", "16000", str(wav)], check=True)
    with wave.open(str(wav), "rb") as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768
    hop = 16000 // fps
    env = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a) - hop, hop)])
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vf", f"crop={crop},scale=48:48,format=gray", "-r", str(fps),
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    fr = np.frombuffer(p.stdout, dtype=np.uint8).reshape(-1, 48, 48).astype(float)
    mot = np.concatenate([[0], np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))])
    n = min(len(env), len(mot))
    env, mot = env[:n], mot[:n]
    env = (env - env.mean()) / (env.std() + 1e-9)
    mot = (mot - mot.mean()) / (mot.std() + 1e-9)
    lags = list(range(-15, 16))
    xc = [float(np.mean(env[max(0, l):n + min(0, l)] * mot[max(0, -l):n - max(0, l)])) for l in lags]
    i = int(np.argmax(xc))
    return lags[i], round(xc[i], 2)


def gen():
    segs = json.load(open(D / "narration3.json", encoding="utf-8"))
    manifest_p = PRES / "manifest.json"
    manifest = json.load(open(manifest_p)) if manifest_p.exists() else {}
    # character clips first (short queue), only if missing
    for sid, prompt in CHARACTER_CLIPS.items():
        out = CLIPS / f"{sid}_chars.mp4"
        if out.exists() and out.stat().st_size > 100000:
            continue
        t = time.time()
        f, err = grok_video(prompt, out)
        print(f"clip {sid}: {'ok' if f else 'FAILED ' + str(err)} {time.time() - t:.0f}s", flush=True)
    for s in segs:
        sid = s["id"]
        if manifest.get(sid, {}).get("similarity", 0) >= MIN_SIM and abs(manifest[sid].get("lag", 99)) <= MAX_LAG:
            print(f"{sid}: cached sim {manifest[sid]['similarity']} lag {manifest[sid]['lag']}", flush=True)
            continue
        best = manifest.get(sid, {"similarity": 0, "lag": 99})
        for att in range(ATTEMPTS):
            out = PRES / f"{sid}_b{att}.mp4"
            t = time.time()
            if not (out.exists() and out.stat().st_size > 100000):  # a pre-seeded probe clip is evaluated, not regenerated
                f, err = grok_video(SETTING + spoken_numbers(s["hook"]) + STYLE, out, image=ANCHOR)
                if not f:
                    print(f"{sid} b{att}: FAILED {err}", flush=True)
                    continue
            txt = stt(out)
            sim = round(similarity(s["hook"], txt), 3)
            lag, corr = lip_lag(out)
            print(f"{sid} b{att}: sim {sim} lag {lag:+d}f corr {corr} ({time.time() - t:.0f}s) :: {txt[:80]}", flush=True)
            cand = {"file": out.name, "similarity": sim, "lag": lag, "lip_corr": corr, "transcript": txt, "hook": s["hook"], "attempt": att,
                    "source": f"grok-cli {VIDEO_MODEL} 10s native dialogue, start-frame anchor"}
            better = (sim >= MIN_SIM, -abs(lag), sim) > (best.get("similarity", 0) >= MIN_SIM, -abs(best.get("lag", 99)), best.get("similarity", 0))
            if better:
                best = cand
            if sim >= MIN_SIM and abs(lag) <= MAX_LAG:
                break
        manifest[sid] = best
        json.dump(manifest, open(manifest_p, "w", encoding="utf-8"), indent=1)
    low = [k for k, v in manifest.items() if v.get("similarity", 0) < MIN_SIM or abs(v.get("lag", 99)) > MAX_LAG]
    print("done. below gate:", low or "none")


def vc():
    """Chatterbox VC: presenter clip audio + VO remainders -> Maya's voice; presenter output resampled to source length."""
    import numpy as np
    import torch
    import torchaudio
    from chatterbox.vc import ChatterboxVC
    model = ChatterboxVC.from_pretrained(device="cuda")
    manifest = json.load(open(PRES / "manifest.json", encoding="utf-8"))
    segs = json.load(open(D / "narration3.json", encoding="utf-8"))

    def convert(src_wav, dst_wav, keep_duration=True):
        wav = model.generate(audio=str(src_wav), target_voice_path=str(MAYA_REF))
        x = wav.squeeze(0).cpu().numpy()
        if keep_duration:
            with wave.open(str(src_wav), "rb") as w_in:
                src_s = w_in.getnframes() / w_in.getframerate()
            want = int(round(src_s * model.sr))
            if abs(len(x) - want) > model.sr * 0.01:
                x = np.interp(np.linspace(0, len(x) - 1, want), np.arange(len(x)), x)
        x = np.asarray(x, dtype=np.float32) * (0.85 / (np.max(np.abs(x)) + 1e-9))  # VC output peaks at full scale; leave headroom
        torchaudio.save(str(dst_wav), torch.from_numpy(x).unsqueeze(0), model.sr, encoding="PCM_S", bits_per_sample=16)

    for s in segs:
        sid = s["id"]
        m = manifest.get(sid)
        if m and m.get("file"):
            src = (PRES / m["file"]).with_suffix(".wav")  # 16 kHz mono from stt()
            dst = PRES / f"{sid}_hook_vc.wav"
            if not dst.exists():
                convert(src, dst, keep_duration=True)
                print(f"{sid}: hook vc ok", flush=True)
        rest_mp3 = VOICE3 / f"{sid}_rest.mp3"
        if rest_mp3.exists():
            rest_wav = VOICE3 / f"{sid}_rest.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(rest_mp3), "-ac", "1", "-ar", "16000", str(rest_wav)], check=True)
            dst = VOICE3 / f"{sid}_rest_vc.wav"
            if not dst.exists():
                convert(rest_wav, dst, keep_duration=False)
                print(f"{sid}: rest vc ok", flush=True)
    print("vc done")


if __name__ == "__main__":
    {"gen": gen, "vc": vc}[sys.argv[1]]()
