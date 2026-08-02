"""Generate the 15 Grok Imagine clips for the Maya grind reel.

Serial by design — one subscription, polite pacing. Every clip is 9:16 and
prompt-banned from drawing readable text or numbers (the monitors show chart
SILHOUETTES; anything numeric an image model paints is fiction, house rule
10.1). Identity across clips is held by the anchor still: clips that match the
anchor's framing start FROM it (--image), reframed clips reference it
(--reference-image), and pure-scenery clips run free.

    python scripts/grind/gen_clips.py

Writes remotion/public/grind/clipNN.mp4 + manifest.json (URLs, durations,
retrieved_at) so the batch is resumable — already-downloaded clips are skipped.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "remotion", "public", "grind")
ANCHOR = os.path.join(OUT, "maya_anchor.png")
CLI = os.path.expanduser("~/tools/grok-cli/grok-cli.exe")
MANIFEST = os.path.join(OUT, "manifest.json")

BASE = (
    " Cinematic, photorealistic, moody, shallow depth of field, vertical 9:16. "
    "NO readable text, NO numbers, NO logos, NO captions, NO watermarks, "
    "her face is never visible."
)
ROOM = (
    "the dark trading room with a wall of monitors showing soft glowing "
    "candlestick chart silhouettes, deliberately blurred and unreadable, "
    "magenta and teal neon light strips, night. "
)
HER = (
    "The same young woman seen strictly from behind, back to camera, oversized "
    "charcoal hoodie, long dark hair, "
)

# (word or None, mode: start|ref|free, prompt)
CLIPS = [
    ("AMBITION", "start",
     "Slow cinematic push-in toward her back as she studies the charts, the "
     "monitors flickering softly, neon light breathing." + BASE),
    (None, "ref",
     HER + "seen from a three-quarter back angle in " + ROOM +
     "She leans forward toward the screens, one hand on the mouse, intent." + BASE),
    ("STRUGGLE", "ref",
     HER + "hood pulled UP over her head, in " + ROOM +
     "Heavy rain streaking down a tall window beside the desk, she keeps "
     "working, slow drift left." + BASE),
    ("DISCIPLINE", "ref",
     "Over-the-shoulder shot from behind " + HER.lower() + "writing notes in a "
     "paper journal at the desk in " + ROOM +
     "Screen glow on the page, her handwriting is soft unreadable strokes." + BASE),
    (None, "ref",
     HER + "in " + ROOM +
     "She leans back in the chair, stretches, hands behind her head, exhausted "
     "but unbeaten, monitors glowing." + BASE),
    ("FOCUS", "ref",
     "Low angle from behind her chair, " + HER.lower() + "silhhouetted against "
     "the glowing monitor wall in " + ROOM +
     "She rolls her shoulders and settles in, slow rise of the camera." + BASE),
    (None, "ref",
     HER + "standing, holding a steaming mug, silhouetted in front of the "
     "monitor wall in " + ROOM + "Steam curls through the neon light." + BASE),
    ("PATIENCE", "start",
     "Slow orbital drift around her back, the neon shifting hue, she never "
     "looks away from the charts." + BASE),
    ("FREEDOM", "ref",
     HER + "walking slowly away from camera toward floor-to-ceiling penthouse "
     "windows, a vast city skyline at dusk beyond the glass, warm interior "
     "light, marble floor reflections." + BASE),
    (None, "free",
     "A matte black supercar parked in a dark underground garage with magenta "
     "and teal neon strips, slow cinematic dolly along its side, reflections "
     "sliding over the body." + BASE),
    (None, "ref",
     HER + "standing on a penthouse rooftop terrace at night, back to camera, "
     "wind moving her hair, endless city lights below, slow push-in." + BASE),
    (None, "free",
     "Empty private jet cabin interior at golden hour, cream leather seats, "
     "sunlight streaming through oval windows, slow dolly down the aisle." + BASE),
    (None, "free",
     "Night drive: a dark supercar gliding through a city of neon lights, "
     "shot from behind, tail lights glowing, light streaks on wet asphalt, "
     "cinematic tracking shot." + BASE),
    ("PURPOSE", "ref",
     HER + "leaning on a rooftop terrace railing at night, back to camera, "
     "looking out over the glowing city, calm, slow drift upward." + BASE),
    ("WORTH IT", "start",
     "She sits back down at the trading desk, hood up, the monitors waking up "
     "with soft chart glow, slow push-in — back to work." + BASE),
]


def run(args, timeout=600):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def gen(i, word, mode, prompt, duration):
    args = [CLI, "video", "--json", "--aspect-ratio", "9:16",
            "--duration", str(duration), "--timeout", "480", "--prompt", prompt]
    if mode == "start":
        args += ["--image", ANCHOR]
    elif mode == "ref":
        args += ["--reference-image", ANCHOR]
    rc, out, err = run(args)
    if rc != 0:
        return None, f"rc={rc} {err[-300:]} {out[-300:]}"
    try:
        j = json.loads(out.splitlines()[-1])
        return j["data"]["video"], None
    except Exception as e:  # noqa: BLE001
        return None, f"parse: {e} :: {out[-300:]}"


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {"clips": []}
    done = {c["i"]: c for c in manifest["clips"] if c.get("file_ok")}

    for i, (word, mode, prompt) in enumerate(CLIPS, 1):
        dest = os.path.join(OUT, f"clip{i:02d}.mp4")
        if i in done and os.path.exists(dest):
            print(f"[{i:02d}] cached", flush=True)
            continue
        url, err = gen(i, word, mode, prompt, 3)
        if url is None and err and ("duration" in err.lower() or "invalid" in err.lower()):
            print(f"[{i:02d}] 3s rejected ({err[:80]}), trying 6s", flush=True)
            url, err = gen(i, word, mode, prompt, 6)
        if url is None:
            print(f"[{i:02d}] FAILED: {err}", flush=True)
            manifest["clips"].append({"i": i, "word": word, "error": err})
            json.dump(manifest, open(MANIFEST, "w"), indent=1)
            continue
        urllib.request.urlretrieve(url, dest)
        ok = os.path.getsize(dest) > 100_000
        print(f"[{i:02d}] {'ok' if ok else 'SMALL'} {os.path.getsize(dest)/1e6:.1f}MB {word or ''}",
              flush=True)
        manifest["clips"] = [c for c in manifest["clips"] if c.get("i") != i]
        manifest["clips"].append({
            "i": i, "word": word, "mode": mode, "url": url, "file_ok": ok,
            "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        json.dump(manifest, open(MANIFEST, "w"), indent=1)
        time.sleep(3)  # polite pacing on the subscription

    n_ok = sum(1 for c in manifest["clips"] if c.get("file_ok"))
    print(f"DONE: {n_ok}/15 clips", flush=True)
    sys.exit(0 if n_ok == 15 else 1)


if __name__ == "__main__":
    main()
