"""Generate the 14 Grok Imagine assets for the Habits reel (10 stills + 4 videos).

Serial by design — one subscription, polite pacing. Every asset is 9:16 and
prompt-banned from readable text/numbers/logos (anything numeric an image
model paints is fiction, house rule 10.1). Aesthetic is real photography —
35mm film, natural light, muted warm tones — NOT the neon sci-fi of the
retired grind reel. Humans appear only as anonymous fragments; faces never.

    python scripts/habits/gen_assets.py

Writes remotion/public/habits/shotNN.{png,mp4} + manifest.json (source,
retrieved_at) so the batch is resumable — existing good files are skipped.
Spec: docs/superpowers/specs/2026-08-02-habits-reel-design.md
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "remotion", "public", "habits")
CLI = os.path.expanduser("~/tools/grok-cli/grok-cli.exe")
MANIFEST = os.path.join(OUT, "manifest.json")

BASE = (
    " Photorealistic candid photography, shot on 35mm film, natural light, "
    "muted warm tones, soft film grain, shallow depth of field, vertical 9:16 "
    "composition. NO readable text, NO numbers, NO logos, NO watermarks, "
    "faces never visible."
)

# (idx, kind img|vid, video seconds (vids only), word or None, prompt)
SHOTS = [
    (1, "vid", 6, "TALENT LOSES TO ROUTINE",
     "A dark home office before dawn, a wooden desk with a closed notebook, a "
     "dormant computer monitor and a cup of coffee, faint blue pre-dawn light "
     "through the window, slow cinematic push-in toward the desk." + BASE),
    (2, "img", 0, "WAKE EARLY",
     "A dark bedroom at dawn, first pale light through the window, a steaming "
     "cup of coffee on the windowsill, soft curtain silhouettes." + BASE),
    (3, "img", 0, "TRAIN",
     "Running shoes on wet pavement at dawn, low angle, soft morning mist, "
     "empty city street out of focus behind." + BASE),
    (4, "img", 0, "STUDY",
     "An open trading journal on a modern desk in warm morning window light, "
     "pages filled with hand-sketched candlestick patterns, support and "
     "resistance trendlines and soft unreadable formula notation, a sleek "
     "matte-black rollerball pen resting on the page, the edge of a "
     "mechanical keyboard and a folded financial newspaper with blurred "
     "columns beside it." + BASE),
    (5, "img", 0, "PLAN",
     "A modern trading desk in morning light: a notepad with hand-drawn "
     "chart pattern sketches and an unreadable checklist, small sticky notes "
     "with soft unreadable strokes on the lower edge of a monitor, a sleek "
     "metal pen, a plain coffee mug." + BASE),
    (6, "img", 0, "EXECUTE",
     "Close-up of hands resting on a keyboard in a dim room, soft "
     "out-of-focus glow from a monitor beyond, cinematic." + BASE),
    (7, "img", 0, "RISK SMALL",
     "A single wooden chess pawn standing on a desk in a beam of window "
     "light, everything else in shadow." + BASE),
    (8, "vid", 6, None,
     "Heavy rain streaking down a window pane at night, blurred warm city "
     "lights beyond the glass, slow gentle drift, meditative." + BASE),
    (9, "img", 0, "JOURNAL EVERYTHING",
     "A desk at night lit by a single warm lamp, an open trading journal "
     "with hand-sketched candlestick charts, trendlines and soft unreadable "
     "annotations, printed chart pages with blurred lines spread around it, "
     "a modern matte-black pen resting on top, faint monitor glow in the "
     "background." + BASE),
    (10, "img", 0, "PATIENCE",
     "An analog wristwatch with a plain numeral-free face lying on a wooden "
     "desk, warm evening light, macro shot, shallow focus." + BASE),
    (11, "img", 0, "IT COMPOUNDS",
     "Sunrise over a city skyline seen from a high window, warm golden light "
     "flooding into a quiet room, silhouetted window frame." + BASE),
    (12, "vid", 3, "FREEDOM",
     "View from inside a car driving on an open highway at golden hour, "
     "sunlight flaring through the windshield, hills in the distance, steady "
     "cinematic motion, no people visible." + BASE),
    (13, "img", 0, "WORTH IT",
     "A person seen from far behind as a small distant silhouette standing "
     "at a floor-to-ceiling window at dusk, city lights far below, vast "
     "quiet room." + BASE),
    (14, "vid", 3, "SAME HABITS. TOMORROW.",
     "The same dark home office before dawn, wooden desk with notebook and "
     "coffee, faint blue pre-dawn light, the scene settles calmly, very slow "
     "drift." + BASE),
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

    for i, kind, dur, word, prompt in SHOTS:
        ext = "png" if kind == "img" else "mp4"
        dest = os.path.join(OUT, f"shot{i:02d}.{ext}")
        floor = 30_000 if kind == "img" else 100_000
        if os.path.exists(dest) and os.path.getsize(dest) > floor:
            print(f"[{i:02d}] cached", flush=True)
            if not any(s.get("i") == i and s.get("file_ok") for s in manifest["shots"]):
                manifest["shots"].append({
                    "i": i, "kind": kind, "word": word, "file_ok": True,
                    "source": "grok-cli imagine (cached probe)",
                    "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })
                json.dump(manifest, open(MANIFEST, "w"), indent=1)
            continue
        err = gen_img(prompt, dest) if kind == "img" else gen_vid(prompt, dur, dest)
        manifest["shots"] = [s for s in manifest["shots"] if s.get("i") != i]
        entry = {
            "i": i, "kind": kind, "word": word, "file_ok": err is None,
            "source": f"grok-cli imagine {kind}",
            "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if err:
            entry["error"] = err
            print(f"[{i:02d}] FAILED: {err}", flush=True)
        else:
            print(f"[{i:02d}] ok {os.path.getsize(dest)/1e6:.1f}MB {word or ''}", flush=True)
        manifest["shots"].append(entry)
        json.dump(manifest, open(MANIFEST, "w"), indent=1)
        time.sleep(3)  # polite pacing on the subscription

    n_ok = sum(1 for s in manifest["shots"] if s.get("file_ok"))
    print(f"DONE: {n_ok}/{len(SHOTS)} assets", flush=True)
    sys.exit(0 if n_ok == len(SHOTS) else 1)


if __name__ == "__main__":
    main()
