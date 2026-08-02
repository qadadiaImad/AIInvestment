"""Voices for the strategy episode.

On-camera (acts 2 & 5): standard maya-talking-pipeline — anchored start
frame, grok native dialogue, STT-verified, VC'd to her clone, drift-locked.
Off-camera (acts 3 & 4): Chatterbox TTS in her cloned voice, lines placed at
the engines' precomputed event times (quiz timeline constants; walkthrough
event_times_s), overlap-checked like make_vo.

Run with the chatterbox venv:
  C:/Users/imadq/tools/chatterbox-venv/Scripts/python.exe scripts/strategy_reel/make_episode_vo.py

Outputs:
  remotion/public/science/pip/act2.mp4 / act5.mp4  (full-frame Maya, muxed VC audio)
  content/probe/act3_vo.wav / act4_vo.wav          (48k stereo, act-length)
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts", "science_reel"))
import bake_dialogue_reel as bake  # noqa: E402  (gen_window, ANCHOR, etc.)

PIP_DIR = os.path.join(REPO, "remotion", "public", "science", "pip")
PROBE = os.path.join(REPO, "content", "probe")
RATE = 48000

BRIDGE = "Let's dive into one medium complexity setup. The breakout and retest. First, on a clean example."
OUTRO = "That's one setup out of dozens. If you want more candlestick strategies like this, like and follow for more."

# Act 3 — quiz engine timeline (frames/30): count 7.73-12.73, answer 12.73,
# reveal to 16.5, trade frame 16.7+, rule card 19.8, total 24.0
ACT3 = [
    (0.6, "Price keeps hitting the same ceiling. Two rejections."),
    (4.3, "Then breakout. And now, the retest."),
    (7.75, "Does it hold? Five seconds."),
    (13.0, "It holds. Buyers defended the level."),
    (16.9, "Entry at the level. Stop below the retest. Target, two R."),
    (21.2, "Take profit. That's the whole idea."),
]
ACT3_LEN_S = 24.0

# Act 4 — from strategy_walkthrough_props.json event_times_s
ACT4_LINES = [
    ("start+0.1", "This is not fiction. Brent crude, summer twenty twenty."),
    ("printing+1.15", "Watch the tape print. Signals appear only when they appear."),
    ("resist+0.2", "Two touches. Now we can draw the resistance."),
    ("breakout+0.2", "July fifteenth. Breakout, close above the level."),
    ("retest+0.1", "The retest."),
    ("trade_frame+0.7", "Entry at the level. Stop under the retest. Target, two R."),
    ("tp+0.4", "Target hit, July twenty third."),
    ("end-3.4", "Real chart. Real dates. Real process."),
]


def synth_lines(lines, total_s, out_path, vc_model):
    import torchaudio
    from chatterbox.tts import ChatterboxTTS
    buf = np.zeros(int(total_s * RATE) + RATE)
    prev_end = 0.0
    for k, (start, text) in enumerate(lines):
        cache = os.path.join(PROBE, "episode_vo",
                             f"{os.path.basename(out_path)}.{k:02d}.wav")
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        if not os.path.exists(cache):
            wav = vc_model.generate(
                text,
                audio_prompt_path=os.path.join(REPO, "higgs", "persona_lifestyle",
                                               "maya_voice_sample.wav"),
                exaggeration=0.55, cfg_weight=0.5)
            torchaudio.save(cache, wav, vc_model.sr, encoding="PCM_S", bits_per_sample=16)
        with wave.open(cache, "rb") as w:
            sr = w.getframerate()
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
        n48 = int(len(x) * RATE / sr)
        x = np.interp(np.linspace(0, len(x) - 1, n48), np.arange(len(x)), x)
        loud = np.where(np.abs(x) > 0.005)[0]
        if len(loud):
            x = x[max(0, loud[0] - 240): loud[-1] + 1200]
        f = int(0.06 * RATE)
        x[:f] *= np.linspace(0, 1, f)
        x[-f:] *= np.linspace(1, 0, f)
        dur = len(x) / RATE
        flag = "OVERLAP!" if start < prev_end - 0.05 else "ok"
        print(f"  [{k}] {start:6.2f}s +{dur:4.2f}s {flag}  {text}")
        i = int(start * RATE)
        buf[i:i + len(x)] += x
        prev_end = start + dur
    buf = buf[: int(total_s * RATE)]
    peak = np.max(np.abs(buf))
    if peak > 0:
        buf *= (10 ** (-2.0 / 20)) / peak
    inter = np.repeat((buf * 32767).astype(np.int16), 2)
    with wave.open(out_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(inter.tobytes())
    print(f"OK {out_path} ({total_s:.1f}s)")


def oncamera(name, text):
    """Anchored dialogue window -> full-frame act clip with VC audio."""
    out_cached = os.path.join(PIP_DIR, f"{name}_final.mp4")
    if os.path.exists(out_cached) and os.path.getsize(out_cached) > 200_000:
        print(f"  [{name}] cached")
        return
    score, path, transcript = bake.gen_window(name, text)
    assert path, f"{name}: generation failed"
    print(f"  [{name}] sim={score:.2f} \"{transcript[:60]}\"")
    vid = os.path.join(PIP_DIR, f"{name}.mp4")
    os.replace(path, vid)
    wav16 = os.path.join(PIP_DIR, f"{name}.wav")
    os.replace(path.replace(".mp4", ".wav"), wav16)

    from chatterbox.vc import ChatterboxVC
    import torchaudio, torch
    vc = ChatterboxVC.from_pretrained(device="cuda")
    wav = vc.generate(audio=wav16, target_voice_path=os.path.join(
        REPO, "higgs", "persona_lifestyle", "maya_voice_sample.wav"))
    with wave.open(wav16, "rb") as w_in:
        src_s = w_in.getnframes() / w_in.getframerate()
    want = int(round(src_s * vc.sr))
    x = wav.squeeze(0).cpu().numpy()
    if abs(len(x) - want) > vc.sr * 0.01:
        x = np.interp(np.linspace(0, len(x) - 1, want), np.arange(len(x)), x)
    wav = torch.from_numpy(np.asarray(x, dtype=np.float32)).unsqueeze(0)
    vcw = os.path.join(PIP_DIR, f"{name}_vc.wav")
    torchaudio.save(vcw, wav, vc.sr, encoding="PCM_S", bits_per_sample=16)
    out = os.path.join(PIP_DIR, f"{name}_final.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-i", vid, "-i", vcw,
                    "-map", "0:v:0", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", out, "-y"], check=True)
    print(f"OK {out}")


def main():
    sys.stdout.reconfigure(line_buffering=True)
    print("[bridge]")
    oncamera("act2", BRIDGE)
    print("[outro]")
    oncamera("act5", OUTRO)

    from chatterbox.tts import ChatterboxTTS
    tts = ChatterboxTTS.from_pretrained(device="cuda")
    print("[act3 vo]")
    synth_lines(ACT3, ACT3_LEN_S, os.path.join(PROBE, "act3_vo.wav"), tts)

    ev = json.load(open(os.path.join(PROBE, "strategy_walkthrough_props.json")))["event_times_s"]
    lines4 = []
    for spec, text in ACT4_LINES:
        key, off = (spec.split("+") if "+" in spec else spec.split("-"))
        t = ev[key] + (float(off) if "+" in spec else -float(off))
        lines4.append((t, text))
    print("[act4 vo]")
    synth_lines(sorted(lines4), ev["end"], os.path.join(PROBE, "act4_vo.wav"), tts)


if __name__ == "__main__":
    main()
