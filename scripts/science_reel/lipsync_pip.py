"""Lip-sync Maya's PiP windows to her narration — free, local, Wav2Lip GAN.

The PiP chains 6s clips across the reel: window k covers reel frames
[k*181, (k+1)*181). Each clip is re-dubbed against exactly that slice of
science_vo_maya.wav, so when the composition chains them back the mouth
matches the words on screen. Runs in the lipsync venv (see tools/Wav2Lip,
justinjohn0306 fork; checkpoints from the camenduru HF mirror + fork
releases). ~2s of GPU per clip on the RTX 4070.

    C:/Users/imadq/tools/lipsync-venv/Scripts/python.exe scripts/science_reel/lipsync_pip.py
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
W2L = "C:/Users/imadq/tools/Wav2Lip"
PY = "C:/Users/imadq/tools/lipsync-venv/Scripts/python.exe"
PIP_DIR = os.path.join(REPO, "remotion", "public", "science", "pip")
VO = os.path.join(REPO, "content", "probe", "science_vo_maya.wav")
PROPS = os.path.join(REPO, "content", "probe", "science_pip_props.json")

FPS = 30
CLIP_FRAMES = 181  # matches PipCall in ScienceReel.tsx


def main():
    total = json.load(open(PROPS))["totalFrames"]
    n = -(-total // CLIP_FRAMES)  # ceil: number of chained windows
    files = []
    for k in range(n):
        src = os.path.join(PIP_DIR, f"clip{k % 6}.mp4")
        t0 = k * CLIP_FRAMES / FPS
        dur = min(CLIP_FRAMES, total - k * CLIP_FRAMES) / FPS
        aslice = os.path.join(W2L, "temp", f"slice{k}.wav")
        out = os.path.join(PIP_DIR, f"sync{k}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-i", VO, "-ss", f"{t0:.3f}",
                        "-t", f"{dur:.3f}", "-ac", "1", "-ar", "16000",
                        aslice, "-y"], check=True)
        r = subprocess.run(
            [PY, "inference.py", "--checkpoint_path", "checkpoints/wav2lip_gan.pth",
             "--face", src, "--audio", aslice, "--out_height", "1280",
             "--outfile", out],
            cwd=W2L, capture_output=True, text=True, timeout=600,
        )
        ok = r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 50_000
        print(f"[{k}] {'ok' if ok else 'FAILED'} {t0:.2f}s +{dur:.2f}s -> sync{k}.mp4",
              flush=True)
        if not ok:
            print(r.stderr[-400:])
            sys.exit(1)
        files.append(f"science/pip/sync{k}.mp4")

    props = json.load(open(PROPS))
    props["pipClips"] = files
    json.dump(props, open(os.path.join(REPO, "content", "probe",
                                       "science_pip_sync_props.json"), "w"), indent=1)
    print(f"OK {n} synced windows; props -> science_pip_sync_props.json")


if __name__ == "__main__":
    main()
