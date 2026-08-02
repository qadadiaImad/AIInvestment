"""Generate WhyReel assets: 12 vector-comic word backgrounds + the anchor base.

Word cards: flat vector comic illustrations, one per word, each SHOWING the
word's meaning — faceless silhouette figures, warm gold/brown/tan palette so
the gold serif overlay stays native. NO text/numbers in the art (house rule
10.1 — the word itself is our overlay, and AI-painted glyphs are gibberish).

Anchor base: Maya from behind at a realistic desk with the monitors OFF
(plain dark screens) — real charts are composited onto them afterwards by
scripts/why_cards/composite_anchor.py, because AI-painted "charts" are
fiction and the owner called them out as looking artificial.

    python scripts/why_cards/gen_assets.py
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "remotion", "public", "why")
CLI = os.path.expanduser("~/tools/grok-cli/grok-cli.exe")
ANCHOR_REF = os.path.join(REPO, "remotion", "public", "grind", "maya_anchor.png")
MANIFEST = os.path.join(OUT, "manifest.json")

STYLE = (
    " Flat vector comic cartoon illustration, bold clean outlines, minimal "
    "composition, warm limited palette of gold, amber, brown, tan and black, "
    "high contrast, faceless silhouette figures, vertical 9:16. NO text, NO "
    "letters, NO numbers, NO logos, NO watermarks."
)

CARDS = [
    ("growth", "A tiny seedling growing into a tall golden tree along an "
               "ascending staircase of steps, upward sweeping motion."),
    ("skill", "An archer silhouette hitting the exact center of a target, "
              "clean confident arrow line across the frame."),
    ("discipline", "A figure doing pushups before dawn beside a ringing "
                   "alarm clock and a neatly made bed, first light in the window."),
    ("creativity", "A head silhouette opening like a door with a glowing "
                   "lightbulb, gears and paint splashes flowing out."),
    ("opportunity", "A single glowing open door in a long dark wall, warm "
                    "light pouring through onto the floor."),
    ("identity", "A small figure looking into a tall mirror that reflects a "
                 "larger, straighter version of the same silhouette."),
    ("challenge", "A climber silhouette scaling a steep jagged mountain "
                  "face toward a golden summit."),
    ("independence", "A figure walking alone down an open road at sunrise, "
                     "broken chain links on the ground behind."),
    ("mastery", "A hand holding a chess king aloft above a scattered board, "
                "rays of gold light."),
    ("control", "A steady hand on a ship's wheel amid stylized storm waves, "
                "the ship cutting a straight line through."),
    ("purpose", "A figure holding a glowing compass, a path lit ahead "
                "toward a north star."),
    ("freedom", "A figure standing on a cliff edge with arms spread wide, "
                "birds rising into a golden sunrise sky."),
]

ANCHOR_PROMPT = (
    "A young woman seen strictly from behind, back to camera, long dark hair, "
    "dark hoodie, sitting at a realistic modern home trading desk: two "
    "ordinary flat monitors side by side, both screens completely OFF, plain "
    "dark blank glass with faint window reflections, a laptop to the side, "
    "keyboard, mouse, coffee mug, notebook and pen, cables, golden sunset "
    "light through a large window, city skyline outside, warm amber tones, "
    "photorealistic, shot on 35mm film, shallow depth of field, vertical 9:16."
    " NO readable text, NO numbers, NO logos, NO watermarks, her face is "
    "never visible."
)


def run(args, timeout=300):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def gen_img(prompt, dest, ref=None):
    args = [CLI, "image", "--json", "--aspect-ratio", "9:16",
            "--response-format", "b64_json", "--output-file", dest,
            "--prompt", prompt]
    rc, out, err = run(args)
    if rc != 0:
        return f"rc={rc} {err[-300:]} {out[-300:]}"
    if not (os.path.exists(dest) and os.path.getsize(dest) > 30_000):
        return f"file missing/small: {out[-200:]}"
    return None


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {"assets": []}
    jobs = [(f"card_{name}", prompt + STYLE) for name, prompt in CARDS]
    jobs.append(("anchor_base", ANCHOR_PROMPT))

    for name, prompt in jobs:
        dest = os.path.join(OUT, f"{name}.png")
        if os.path.exists(dest) and os.path.getsize(dest) > 30_000:
            print(f"[{name}] cached", flush=True)
            continue
        err = gen_img(prompt, dest)
        manifest["assets"] = [a for a in manifest["assets"] if a.get("name") != name]
        manifest["assets"].append({
            "name": name, "file_ok": err is None,
            "source": "grok-cli imagine image",
            "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **({"error": err} if err else {}),
        })
        json.dump(manifest, open(MANIFEST, "w"), indent=1)
        print(f"[{name}] {'FAILED: ' + err if err else 'ok'}", flush=True)
        time.sleep(3)  # polite pacing on the subscription

    n_ok = sum(1 for a in manifest["assets"] if a.get("file_ok"))
    print(f"DONE: {n_ok}/{len(jobs)}", flush=True)
    sys.exit(0 if n_ok == len(jobs) else 1)


if __name__ == "__main__":
    main()
