"""Maya video-call PiP clips for the Science reel.

Six 6s clips of Maya at her desk speaking into a podcast mic, identity held
by MULTI-image references (grok Video 1.5: --reference-image is repeatable
in CLI 0.1.6) from higgs/persona_lifestyle/. Same setting described
identically each time; gestures vary per clip so the chained PiP doesn't
read as a loop. Mouth motion is generic speech — no lip sync — which reads
fine at quarter-screen video-call size.

    python scripts/science_reel/gen_maya_pip.py

Writes remotion/public/science/pip/clipN.mp4 + manifest (stamped, resumable).
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "remotion", "public", "science", "pip")
CLI = os.path.expanduser("~/tools/grok-cli/grok-cli.exe")
MANIFEST = os.path.join(OUT, "manifest.json")

REFS = [
    os.path.join(REPO, "higgs", "persona_lifestyle", "field_hoodie_selfie.jpeg"),
    os.path.join(REPO, "higgs", "persona_lifestyle", "city_night_selfie.png"),
    os.path.join(REPO, "higgs", "persona_lifestyle", "park_bench.jpeg"),
]

SETTING = (
    "The same young woman as in the reference images, shoulder-length dark "
    "wavy hair, sitting at a desk in a dim room at night, a large podcast "
    "microphone on a boom arm in front of her, soft cool LED strip glow "
    "behind her, framed like a casual vertical video call, facing the "
    "camera, speaking energetically into the mic, "
)
BASE = (
    " Photorealistic, handheld webcam feel, shallow depth of field, vertical "
    "9:16. NO readable text, NO numbers, NO logos, NO watermarks."
)

GESTURES = [
    "making a small dismissive wave as if quoting critics, eyebrows raised.",
    "counting points off on her fingers, nodding.",
    "leaning slightly toward the mic, hands opening outward to explain.",
    "gesturing upward with one hand as if tracing a rising line.",
    "tapping the desk lightly to emphasize a point, confident smile.",
    "finishing a point and settling back with a calm, assured nod.",
]


def run(args, timeout=600):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def gen(prompt, dest):
    args = [CLI, "video", "--json", "--aspect-ratio", "9:16",
            "--duration", "6", "--timeout", "480", "--prompt", prompt]
    for r in REFS:
        args += ["--reference-image", r]
    rc, out, err = run(args)
    if rc != 0:
        return f"rc={rc} {err[-300:]} {out[-300:]}"
    try:
        url = json.loads(out.splitlines()[-1])["data"]["video"]
    except Exception as e:  # noqa: BLE001
        return f"parse: {e} :: {out[-300:]}"
    urllib.request.urlretrieve(url, dest)
    if os.path.getsize(dest) < 100_000:
        return "downloaded file too small"
    return None


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {"clips": []}
    for i, gesture in enumerate(GESTURES):
        dest = os.path.join(OUT, f"clip{i}.mp4")
        if os.path.exists(dest) and os.path.getsize(dest) > 100_000:
            print(f"[{i}] cached", flush=True)
            continue
        err = gen(SETTING + gesture + BASE, dest)
        manifest["clips"] = [c for c in manifest["clips"] if c.get("i") != i]
        manifest["clips"].append({
            "i": i, "file_ok": err is None,
            "source": "grok-cli imagine video 6s, 3 identity reference images",
            "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **({"error": err} if err else {}),
        })
        json.dump(manifest, open(MANIFEST, "w"), indent=1)
        print(f"[{i}] {'FAILED: ' + err if err else 'ok'}", flush=True)
        time.sleep(3)
    n_ok = sum(1 for c in manifest["clips"] if c.get("file_ok"))
    print(f"DONE: {n_ok}/{len(GESTURES)}", flush=True)
    sys.exit(0 if n_ok == len(GESTURES) else 1)


if __name__ == "__main__":
    main()
