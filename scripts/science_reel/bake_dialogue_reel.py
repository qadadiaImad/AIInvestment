"""Bake the science reel with Maya SPEAKING it — the standard pipeline.

Owner-approved standard (2026-08-02): Grok native dialogue for lips,
Chatterbox voice conversion to Maya's clone for the canon voice.

Per window (6 windows of consecutive shots/lines):
  1. grok video, 3 identity refs, calm-delivery prompt, "saying exactly: ..."
  2. STT-verify the transcript (normalized token similarity >= 0.85);
     best-of-3 attempts, keep the best score
  3. extract audio; silence-split into spoken chunks; map chunks -> lines
     (direct if counts match, else proportional by word count) -> the shot
     cut grid is derived from where the words ACTUALLY land
  4. Chatterbox VC the window audio to Maya's voice (timing-preserving)

Outputs: remotion/public/science/pip/dlg{k}.mp4 (+manifest),
content/probe/science_dialogue_vo.wav, content/probe/science_dialogue_props.json.

Run with the chatterbox venv (torch + chatterbox + numpy):
  C:/Users/imadq/tools/chatterbox-venv/Scripts/python.exe scripts/science_reel/bake_dialogue_reel.py
"""
import difflib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CLI = os.path.expanduser("~/tools/grok-cli/grok-cli.exe")
PIP_DIR = os.path.join(REPO, "remotion", "public", "science", "pip")
PROBE = os.path.join(REPO, "content", "probe")
MAYA_REF = os.path.join(REPO, "higgs", "persona_lifestyle", "maya_voice_sample.wav")
REFS = [
    os.path.join(REPO, "higgs", "persona_lifestyle", "field_hoodie_selfie.jpeg"),
    os.path.join(REPO, "higgs", "persona_lifestyle", "city_night_selfie.png"),
    os.path.join(REPO, "higgs", "persona_lifestyle", "park_bench.jpeg"),
]

FPS = 30
WINDOW_FRAMES = 181           # 6.04s grok clips
LEAD_S = 0.12                 # cut lands a breath before the line
MIN_SHOT_FRAMES = 24
SRC_FRAMES = {0: 181, 8: 181, 14: 91, 15: 91}  # bg video sources (loop past end)

SETTING = (
    "The same young woman as in the reference images, shoulder-length dark "
    "wavy hair, sitting at a desk in a dim room at night with a large podcast "
    "microphone on a boom arm, soft cool LED glow behind her, casual vertical "
    "video call framing, facing the camera. She speaks calmly and naturally "
    "into the microphone, saying exactly: "
)
STYLE = (
    " Relaxed natural mouth movements, subtle facial expressions, slight "
    "natural head motion, unhurried delivery. Photorealistic, cinematic soft "
    "light, vertical 9:16. NO readable text, NO logos, NO watermarks."
)

# windows of consecutive shots; each shot has exactly one line
WINDOWS = [
    [(0, "They say trading isn't a real science."),
     (1, "They call it gambling.")],
    [(2, "Pure luck."),
     (3, "Some even call it unethical."),
     (4, "But here's what it actually runs on.")],
    [(5, "Probability."),
     (6, "Statistics."),
     (7, "Stochastic calculus.")],
    [(8, "The same random walks that move particles, move prices.")],
    [(9, "Computer science."),
     (10, "Algorithms."),
     (11, "Game theory."),
     (12, "Machine learning.")],
    [(13, "And the science of human behavior."),
     (14, "It isn't luck. It's mathematics."),
     (15, "Study the science.")],
]


def run(args, timeout=600):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


CONTRACTIONS = {"isn't": "is not", "it's": "it is", "here's": "here is",
                "don't": "do not", "can't": "can not", "that's": "that is"}


def norm(text):
    t = text.lower()
    for k, v in CONTRACTIONS.items():
        t = t.replace(k, v)
    return re.sub(r"[^a-z ]+", " ", t).split()


def similarity(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def gen_window(k, dialogue, attempts=3):
    best = (0.0, None, None)
    for att in range(attempts):
        args = [CLI, "video", "--json", "--aspect-ratio", "9:16",
                "--duration", "6", "--timeout", "480",
                "--prompt", SETTING + f'"{dialogue}"' + STYLE]
        for r in REFS:
            args += ["--reference-image", r]
        rc, out, err = run(args)
        if rc != 0:
            print(f"  [w{k} att{att}] gen failed rc={rc}", flush=True)
            continue
        try:
            url = json.loads(out.splitlines()[-1])["data"]["video"]
        except Exception:  # noqa: BLE001
            continue
        tmp = os.path.join(PIP_DIR, f"dlg{k}_att{att}.mp4")
        urllib.request.urlretrieve(url, tmp)
        awav = tmp.replace(".mp4", ".wav")
        run(["ffmpeg", "-v", "error", "-i", tmp, "-vn", "-ac", "1",
             "-ar", "16000", awav, "-y"])
        rc, sout, _ = run([CLI, "stt", "--json", awav], timeout=240)
        transcript = ""
        try:
            transcript = json.loads(sout.splitlines()[-1])["data"]["transcript"]
        except Exception:  # noqa: BLE001
            m = re.search(r"transcript: (.+)", sout)
            transcript = m.group(1) if m else ""
        score = similarity(dialogue, transcript)
        print(f"  [w{k} att{att}] sim={score:.2f}  \"{transcript[:70]}\"", flush=True)
        if score > best[0]:
            best = (score, tmp, transcript)
        if score >= 0.85:
            break
        time.sleep(2)
    return best


def speech_chunks(wav_path):
    with wave.open(wav_path, "rb") as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    hop = int(0.02 * sr)
    n = len(x) // hop
    rms = np.array([np.sqrt((x[i * hop:(i + 1) * hop] ** 2).mean() + 1e-12) for i in range(n)])
    db = 20 * np.log10(rms + 1e-9)
    thr = max(-42.0, np.percentile(db, 25) + 10)
    on = db > thr
    spans, start = [], None
    for i, v in enumerate(on):
        if v and start is None:
            start = i
        elif not v and start is not None:
            spans.append([start * 0.02, i * 0.02])
            start = None
    if start is not None:
        spans.append([start * 0.02, n * 0.02])
    merged = []
    for s in spans:
        if merged and s[0] - merged[-1][1] < 0.28:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    return [s for s in merged if s[1] - s[0] >= 0.18]


def line_starts_in_window(chunks, lines):
    if len(chunks) == len(lines):
        return [c[0] for c in chunks]
    if not chunks:
        span0, span1 = 0.4, 5.6
    else:
        span0, span1 = chunks[0][0], chunks[-1][1]
    words = [len(t.split()) for _, t in lines]
    total = sum(words)
    starts, acc = [], 0
    for wcount in words:
        starts.append(span0 + (span1 - span0) * acc / total)
        acc += wcount
    return starts


def main():
    sys.stdout.reconfigure(line_buffering=True)
    os.makedirs(PIP_DIR, exist_ok=True)
    manifest = {"windows": [], "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    picked = []
    for k, window in enumerate(WINDOWS):
        dialogue = " ".join(t for _, t in window)
        print(f"[window {k}] {dialogue}", flush=True)
        score, path, transcript = gen_window(k, dialogue)
        if path is None:
            print(f"[window {k}] FAILED all attempts", flush=True)
            sys.exit(1)
        final = os.path.join(PIP_DIR, f"dlg{k}.mp4")
        os.replace(path, final)
        os.replace(path.replace(".mp4", ".wav"), os.path.join(PIP_DIR, f"dlg{k}.wav"))
        picked.append((k, window, score, transcript))
        manifest["windows"].append({
            "k": k, "dialogue": dialogue, "transcript": transcript,
            "similarity": round(score, 3),
            "source": "grok-cli imagine video 6s native dialogue, 3 identity refs",
        })
        json.dump(manifest, open(os.path.join(PIP_DIR, "dialogue_manifest.json"), "w"), indent=1)

    # cut grid from measured speech + VC to Maya's voice
    from chatterbox.vc import ChatterboxVC
    import torchaudio
    vc = ChatterboxVC.from_pretrained(device="cuda")

    cut_starts = [0] * 16
    vo_parts = []
    for k, window, score, transcript in picked:
        wav16 = os.path.join(PIP_DIR, f"dlg{k}.wav")
        chunks = speech_chunks(wav16)
        starts = line_starts_in_window(chunks, window)
        w_start = k * WINDOW_FRAMES / FPS
        for (shot, _), s in zip(window, starts):
            cut_starts[shot] = int(round((w_start + max(0.0, s - LEAD_S)) * FPS))
        wav = vc.generate(audio=wav16, target_voice_path=MAYA_REF)
        out = os.path.join(PIP_DIR, f"dlg{k}_vc.wav")
        torchaudio.save(out, wav, vc.sr, encoding="PCM_S", bits_per_sample=16)
        vo_parts.append(out)
        print(f"[window {k}] chunks={len(chunks)} vc ok", flush=True)

    cut_starts[0] = 0
    for i in range(1, 16):
        cut_starts[i] = max(cut_starts[i], cut_starts[i - 1] + MIN_SHOT_FRAMES)
    total = len(WINDOWS) * WINDOW_FRAMES
    total = min(total, cut_starts[15] + SRC_FRAMES[15])
    assert cut_starts[15] < total

    RATE = 48000
    buf = np.zeros(int(total / FPS * RATE) + RATE)
    for k, part in enumerate(vo_parts):
        with wave.open(part, "rb") as w:
            sr = w.getframerate()
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
        n48 = int(len(x) * RATE / sr)
        x = np.interp(np.linspace(0, len(x) - 1, n48), np.arange(len(x)), x)
        i = int(k * WINDOW_FRAMES / FPS * RATE)
        buf[i:i + len(x)] += x[: max(0, len(buf) - i)]
    buf = buf[: int(total / FPS * RATE)]
    buf *= (10 ** (-1.5 / 20)) / (np.max(np.abs(buf)) + 1e-9)
    inter = np.repeat((buf * 32767).astype(np.int16), 2)
    vo_path = os.path.join(PROBE, "science_dialogue_vo.wav")
    with wave.open(vo_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(inter.tobytes())

    props = {"cutStarts": cut_starts, "totalFrames": total,
             "pipClips": [f"science/pip/dlg{k}.mp4" for k in range(len(WINDOWS))]}
    json.dump(props, open(os.path.join(PROBE, "science_dialogue_props.json"), "w"), indent=1)
    print("cutStarts:", cut_starts)
    print(f"OK total {total} frames = {total / FPS:.2f}s; vo -> {vo_path}")


if __name__ == "__main__":
    main()
