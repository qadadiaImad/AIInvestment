"""Generate the 16 Grok assets for the Science reel (12 stills + 4 videos).

Serial by design — one subscription, polite pacing. Dark-phonk aesthetic:
night, deep blacks, LED accents. Prompt-banned from readable text/numbers
(rule 10.1 — equations and code render as unreadable strokes/blur; the words
are our overlays). Faces never visible.

    python scripts/science_reel/gen_assets.py

Writes remotion/public/science/shotNN.{png,mp4} + manifest.json (stamped,
resumable). Spec: docs/superpowers/specs/2026-08-02-science-reel-design.md
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "remotion", "public", "science")
CLI = os.path.expanduser("~/tools/grok-cli/grok-cli.exe")
MANIFEST = os.path.join(OUT, "manifest.json")

BASE = (
    " Cinematic, night, deep blacks, moody LED accent lighting, high "
    "contrast, shot on 35mm film, soft grain, shallow depth of field, "
    "vertical 9:16. NO readable text, NO numbers, NO letters, NO logos, "
    "NO watermarks, faces never visible."
)

# (idx, kind img|vid, video seconds, prompt)
SHOTS = [
    (0, "vid", 6,
     "A dense night city crowd crossing a wide street toward camera, "
     "silhouettes against car headlights and cold blue signage glow, light "
     "haze, slow cinematic push-in." + BASE),
    (1, "img", 0,
     "A casino table in near darkness, scattered poker chips and cards "
     "under a single dim overhead lamp, cigarette smoke curling." + BASE),
    (2, "img", 0,
     "A spinning coin captured mid-air in macro against a pure black void, "
     "motion blur on the edges, one cold rim light." + BASE),
    (3, "img", 0,
     "A dark glass skyscraper looming overhead at night, low angle, smoke "
     "drifting across, single red aircraft warning light." + BASE),
    (4, "img", 0,
     "A dark study desk lit only by LED strip light, open blank notebook, "
     "sleek keyboard, monitor glow spilling cool light, midnight mood." + BASE),
    (5, "img", 0,
     "A glowing Galton board with streams of light-trail beads falling "
     "through pegs and piling into a luminous bell curve shape at the "
     "bottom, dark background, long exposure look." + BASE),
    (6, "img", 0,
     "Luminous abstract data distribution curves and scatter points drawn "
     "in light, floating in a dark room, long exposure light painting." + BASE),
    (7, "img", 0,
     "A blackboard densely covered in soft unreadable chalk mathematical "
     "notation, one warm spotlight cone, chalk dust in the air." + BASE),
    (8, "vid", 6,
     "Thousands of tiny glowing particles drifting and branching in "
     "random walk paths through darkness, long exposure light trails, "
     "slow camera drift, mesmerizing." + BASE),
    (9, "img", 0,
     "A dark server room aisle, tall racks with constellations of blue "
     "and green LED lights, cold haze, one-point perspective." + BASE),
    (10, "img", 0,
     "A dark computer screen with heavily blurred glowing code lines, "
     "bokeh, an RGB backlit mechanical keyboard in the foreground." + BASE),
    (11, "img", 0,
     "A chess board mid-game in dramatic low-key light, pieces casting "
     "long shadows, one knight in a beam of cold light." + BASE),
    (12, "img", 0,
     "A GPU computing rig glowing with LED light inside a dark case, "
     "abstract web of neural light threads floating above it." + BASE),
    (13, "img", 0,
     "A motion-blurred crowd rushing through a dark station, one sharp "
     "still silhouette standing calm in the middle, cold light." + BASE),
    (14, "vid", 3,
     "A night trading desk with LED strip lighting behind twin monitors "
     "showing soft blurred unreadable chart glow, empty chair, slow "
     "cinematic dolly-in, dark phonk mood." + BASE),
    (15, "vid", 3,
     "The same night city street as a crowd crossing, seen from behind, "
     "headlights flaring, the scene settling calm, slow drift." + BASE),
]


def run(args, timeout=600):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def gen_img(prompt, dest):
    rc, out, err = run([CLI, "image", "--json", "--aspect-ratio", "9:16",
                        "--response-format", "b64_json", "--output-file", dest,
                        "--prompt", prompt], timeout=240)
    if rc != 0:
        return f"rc={rc} {err[-300:]} {out[-300:]}"
    if not (os.path.exists(dest) and os.path.getsize(dest) > 30_000):
        return f"file missing/small: {out[-200:]}"
    return None


def gen_vid(prompt, duration, dest):
    def attempt(dur):
        rc, out, err = run([CLI, "video", "--json", "--aspect-ratio", "9:16",
                            "--duration", str(dur), "--timeout", "480",
                            "--prompt", prompt])
        if rc != 0:
            return None, f"rc={rc} {err[-300:]} {out[-300:]}"
        try:
            return json.loads(out.splitlines()[-1])["data"]["video"], None
        except Exception as e:  # noqa: BLE001
            return None, f"parse: {e} :: {out[-300:]}"

    url, err = attempt(duration)
    if url is None and err and ("duration" in err.lower() or "invalid" in err.lower()):
        url, err = attempt(6)
    if url is None:
        return err
    urllib.request.urlretrieve(url, dest)
    if os.path.getsize(dest) < 100_000:
        return "downloaded file too small"
    return None


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {"shots": []}

    for i, kind, dur, prompt in SHOTS:
        ext = "png" if kind == "img" else "mp4"
        dest = os.path.join(OUT, f"shot{i:02d}.{ext}")
        floor = 30_000 if kind == "img" else 100_000
        if os.path.exists(dest) and os.path.getsize(dest) > floor:
            print(f"[{i:02d}] cached", flush=True)
            continue
        err = gen_img(prompt, dest) if kind == "img" else gen_vid(prompt, dur, dest)
        manifest["shots"] = [s for s in manifest["shots"] if s.get("i") != i]
        manifest["shots"].append({
            "i": i, "kind": kind, "file_ok": err is None,
            "source": f"grok-cli imagine {kind}",
            "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **({"error": err} if err else {}),
        })
        json.dump(manifest, open(MANIFEST, "w"), indent=1)
        print(f"[{i:02d}] {'FAILED: ' + err if err else 'ok'}", flush=True)
        time.sleep(3)  # polite pacing on the subscription

    n_ok = sum(1 for s in manifest["shots"] if s.get("file_ok"))
    print(f"DONE: {n_ok}/{len(SHOTS)}", flush=True)
    sys.exit(0 if n_ok == len(SHOTS) else 1)


if __name__ == "__main__":
    main()
