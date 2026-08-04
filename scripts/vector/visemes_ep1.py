"""FairMarketEp1 viseme production: masked mouth/eye inpainting per talking pose.

Proven technique (commit 03eb2fb): sdxl_lora_inpaint (SetLatentNoiseMask,
denoise 0.8, ana_cast_v1 LoRA) regenerates ONLY an elliptical mouth/eye
region of the cropped pose drawing, giving native-style visemes. Production
hardening applied here:
  * bases are the cropped `_<pose>_rgba.png` canvases (same dims as the
    shipped SVGs), padded to multiples of 8 before staging -- ComfyUI's
    VAEEncode floor-crops otherwise (846x1101 came back 840x1096 in the
    proof) and alignment would be guesswork;
  * every result is composited back onto its base (VAE round-trip drifts
    ~8.6% of outside-mask pixels), silhouette locked to the base alpha;
  * explicit viseme phrasings, 2-3 phrasings/seeds per target (soft
    phrasings lose to the mustache/expression prior);
  * everything goes through a vision gate before wiring.

Phases (run from scripts/: python -m vector.visemes_ep1 <phase>):
  anchors    detect faces; calibrate Rex mouth anchors off Sol's known ones;
             eye bands for all poses; write anchors_ep1.json + debug sheet
  gen        run the inpaint plan on the local ComfyUI queue (resumable)
  composite  paste masked regions back onto bases (exact identity outside)
  sheets     per-pose audit sheets (base + zoomed labeled candidates)
  vectorize  vtracer the gate survivors + write the comp's viseme manifest
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

REPO = Path(__file__).resolve().parents[2]
EP = REPO / "content" / "vector_char" / "cast" / "ep_fairmarket"
RENDERS = EP / "renders"
VIS = EP / "visemes"
FIX = REPO / "remotion" / "src" / "fixtures" / "cast_ep1"
PUB = REPO / "remotion" / "public" / "characters" / "cast_ep1"

# Proven proof-mask geometry, measured from the committed _inpaint_mask.png:
# ellipse centered on the mouth anchor, 4.42 x 3.53 mouth-widths.
MASK_RX = 2.21
MASK_RY = 1.77

SOL_POSES = ["sol_point", "sol_finger", "sol_armswide", "sol_point_v1",
             "sol_smug", "sol_wink", "sol_smug_v1", "sol_smug_v2",
             "sol_wink_v1", "sol_laugh"]
REX_POSES = ["rex_eager", "rex_eager_v1", "rex_shock", "rex_shock_v1",
             "rex_determined"]

SOL_LOCK = ("solquant, 1boy, solo, old man, gray hair, thick mustache, "
            "burgundy cardigan, yellow bow tie, plump")
REX_LOCK = ("rexquant, 1boy, solo, orange hair, spiky hair, glasses, "
            "gray vest, white shirt")
SUFFIX = ("masterpiece, best quality, flat color, simple background, "
          "white background")
NEG = "worst quality, low quality"
NEG_EXTRA = {"closed": ", open mouth, teeth", "blink": ", open eyes"}

PHRASES = {
    "closed": ["closed mouth, lips pressed together, neutral expression",
               "mouth firmly closed, calm face",
               "closed mouth, small frown"],
    "half": ["half open mouth, parted lips, mid speech",
             "slightly open mouth, talking"],
    "open": ["wide open mouth, shouting, mouth fully open",
             "open mouth wide, yelling loudly"],
    "oh": ["round open o mouth, o shaped mouth",
           "round o shaped open mouth, surprised",
           "puckered round open mouth, saying oh"],
    "blink": ["closed eyes, both eyes shut, blinking",
              "eyes closed, peaceful expression",
              "closed eyes, mid blink"],
}
# poses whose base drawing already IS a viseme, so that slot points at
# the base SVG instead of a regenerated one
BASE_IS = {"sol_laugh": "open"}

# candidates per (character, viseme); Sol has no 'closed' (mustache IS closed)
COUNTS = {"sol": {"half": 2, "open": 2, "oh": 3, "blink": 2},
          "rex": {"closed": 3, "half": 2, "open": 2, "oh": 3, "blink": 3}}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ----------------------------------------------------------------- geometry

def ellipse_mask(w: int, h: int, cx: float, cy: float,
                 rx: float, ry: float) -> np.ndarray:
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).ellipse(
        [cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    return np.asarray(im)


def pad8(arr: np.ndarray):
    """Pad H,W up to multiples of 8 (right/bottom, edge-replicate).
    Returns (padded, (H, W)) with the original dims for unpad8."""
    h, w = arr.shape[:2]
    ph, pw = (-h) % 8, (-w) % 8
    if ph == 0 and pw == 0:
        return arr, (h, w)
    pad = [(0, ph), (0, pw)] + [(0, 0)] * (arr.ndim - 2)
    return np.pad(arr, pad, mode="edge"), (h, w)


def unpad8(arr: np.ndarray, box) -> np.ndarray:
    h, w = box
    return arr[:h, :w]


def composite_rgb(base: np.ndarray, gen: np.ndarray,
                  mask: np.ndarray) -> np.ndarray:
    """gen inside mask, base outside -- identity outside is exact by
    construction (the whole point vs. the VAE round-trip)."""
    m = (mask > 128)[..., None]
    return np.where(m, gen, base).astype(np.uint8)


# ------------------------------------------------------------ face detection

def skin_mask(rgba: np.ndarray) -> np.ndarray:
    r = rgba[..., 0].astype(int)
    g = rgba[..., 1].astype(int)
    b = rgba[..., 2].astype(int)
    a = rgba[..., 3]
    # flat-style skin: warm, light, r>g>b. g floor kills Rex's orange hair,
    # g ceiling + (r-b) floor kill the white shirt / near-white highlights.
    return ((a > 0) & (r >= 230) & (g >= 185) & (g <= 238)
            & (b >= 150) & (b <= 218) & (r > g) & (g > b) & ((r - b) >= 25))


def detect_face(rgba: np.ndarray) -> tuple[int, int, int, int]:
    """Largest skin blob in the top 45% of the ink bbox = the face."""
    h = rgba.shape[0]
    ys = np.nonzero(rgba[..., 3] > 0)[0]
    y_top, y_bot = int(ys.min()), int(ys.max())
    cut = y_top + int((y_bot - y_top) * 0.45)
    m = skin_mask(rgba)
    m[cut:] = False
    m = ndimage.binary_closing(m, iterations=2)
    labels, n = ndimage.label(m)
    if n == 0:
        raise ValueError("no skin blob found")
    sizes = ndimage.sum(m, labels, range(1, n + 1))
    sl = ndimage.find_objects(labels == (int(np.argmax(sizes)) + 1))[0]
    return (sl[1].start, sl[0].start, sl[1].stop, sl[0].stop)


def mouth_ratios_from_face(face, mouth) -> dict:
    x0, y0, x1, y1 = face
    fw, fh = x1 - x0, y1 - y0
    fcx = (x0 + x1) / 2
    return {"dx": (mouth["cx"] - fcx) / fw,
            "my": (mouth["cy"] - y0) / fh,
            "mw": mouth["w"] / fw}


def apply_ratios(face, r) -> dict:
    x0, y0, x1, y1 = face
    fw, fh = x1 - x0, y1 - y0
    return {"cx": (x0 + x1) / 2 + r["dx"] * fw,
            "cy": y0 + r["my"] * fh,
            "w": r["mw"] * fw}


# ------------------------------------------------------------------ the plan

def plan_jobs() -> list[dict]:
    jobs = []
    for pi, pose in enumerate(SOL_POSES + REX_POSES):
        char = "sol" if pose.startswith("sol") else "rex"
        lock = SOL_LOCK if char == "sol" else REX_LOCK
        for vi, (viseme, n) in enumerate(COUNTS[char].items()):
            for i in range(n):
                phrase = PHRASES[viseme][i % len(PHRASES[viseme])]
                jobs.append({
                    "pose": pose, "viseme": viseme,
                    "mask": "eyes" if viseme == "blink" else "mouth",
                    "phrase": phrase,
                    "prompt": f"{lock}, {phrase}, {SUFFIX}",
                    "negative": NEG + NEG_EXTRA.get(viseme, ""),
                    "seed": 71000 + pi * 100 + vi * 10 + i,
                    "out": f"{pose}__{viseme}__c{i}",
                })
    return jobs


# ------------------------------------------------------------------- phases

def load_base(pose: str) -> np.ndarray:
    p = RENDERS / f"_{pose}_rgba.png"
    return np.asarray(Image.open(p).convert("RGBA"))


def flatten_white(rgba: np.ndarray) -> np.ndarray:
    a = rgba[..., 3:4].astype(float) / 255.0
    rgb = rgba[..., :3].astype(float) * a + 255.0 * (1 - a)
    return rgb.astype(np.uint8)


def load_anchors() -> dict:
    return json.loads((VIS / "anchors_ep1.json").read_text("utf-8"))


def mask_for(pose: str, kind: str, anchors: dict) -> np.ndarray:
    a = anchors[pose]
    W, H = a["canvas"]
    e = a[kind if kind == "eyes" else "mouth"]
    return ellipse_mask(W, H, e["cx"], e["cy"], e["rx"], e["ry"])


def phase_anchors() -> None:
    """Hand-placed ellipses (anchor_overrides.json, normalized) -> pixel
    ellipses per pose. Auto skin-blob detection proved unreliable on the
    bust closeups and most Rex poses, and even the shipped fixture mouth
    anchors sat on the bow tie for three busts -- every mask is placed by
    eye off the grid overlays instead, then re-verified on the debug
    sheet."""
    VIS.mkdir(parents=True, exist_ok=True)
    overrides = json.loads(
        (VIS / "anchor_overrides.json").read_text("utf-8"))
    out = {}
    for pose in SOL_POSES + REX_POSES:
        rgba = load_base(pose)
        H, W = rgba.shape[:2]
        o = overrides[pose]
        out[pose] = {
            "canvas": [W, H],
            "mouth": {"cx": o["mouth"]["cx"] * W, "cy": o["mouth"]["cy"] * H,
                      "rx": o["mouth"]["rx"] * W, "ry": o["mouth"]["ry"] * H},
            "eyes": {"cx": o["eyes"]["cx"] * W, "cy": o["eyes"]["cy"] * H,
                     "rx": o["eyes"]["rx"] * W, "ry": o["eyes"]["ry"] * H},
            "source": f"renders/_{pose}_rgba.png + anchor_overrides.json",
            "retrieved_at": now_utc(),
        }
    (VIS / "anchors_ep1.json").write_text(
        json.dumps(out, indent=1), "utf-8")
    _debug_sheet(out)
    print(f"wrote {VIS / 'anchors_ep1.json'} + anchor_debug.png "
          f"({len(out)} poses, hand-placed)")


def _debug_sheet(anchors: dict, cell_h=420) -> None:
    tiles = []
    for pose, a in anchors.items():
        rgba = load_base(pose)
        im = Image.fromarray(flatten_white(rgba)).convert("RGB")
        d = ImageDraw.Draw(im)
        for kind, col in (("mouth", (230, 30, 30)), ("eyes", (20, 170, 60))):
            e = a[kind]
            d.ellipse([e["cx"] - e["rx"], e["cy"] - e["ry"],
                       e["cx"] + e["rx"], e["cy"] + e["ry"]],
                      outline=col, width=4)
        s = cell_h / im.height
        im = im.resize((int(im.width * s), cell_h))
        tile = Image.new("RGB", (im.width, cell_h + 34), "white")
        tile.paste(im, (0, 34))
        ImageDraw.Draw(tile).text((6, 6), pose, fill="black",
                                  font=_font(22))
        tiles.append(tile)
    _grid(tiles, VIS / "anchor_debug.png", cols=7)


def _font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _grid(tiles, path: Path, cols: int) -> None:
    rows = (len(tiles) + cols - 1) // cols
    cw = max(t.width for t in tiles)
    ch = max(t.height for t in tiles)
    sheet = Image.new("RGB", (cw * min(cols, len(tiles)), ch * rows), "white")
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * cw, (i // cols) * ch))
    sheet.save(path)


def phase_gen(jobs: list[dict] | None = None, denoise=0.8) -> None:
    from comfy.client import ComfyClient
    from comfy.launch import ensure_server
    ensure_server()
    anchors = load_anchors()
    client = ComfyClient()
    client._last_family = "sdxl"          # proof ran sdxl last; no switch
    jobs = jobs if jobs is not None else plan_jobs()
    jobs = [j for j in jobs
            if not (VIS / "raw" / f"{j['out']}.png").exists()]
    (VIS / "raw").mkdir(parents=True, exist_ok=True)
    (VIS / "staged").mkdir(exist_ok=True)
    staged: set[str] = set()
    manifest_p = VIS / "gen_manifest.json"
    manifest = (json.loads(manifest_p.read_text("utf-8"))
                if manifest_p.exists() else [])
    print(f"{len(jobs)} jobs to run")
    for n, j in enumerate(jobs, 1):
        pose, kind = j["pose"], j["mask"]
        base_name = f"vis_{pose}_base.png"
        mask_name = f"vis_{pose}_{kind}.png"
        if base_name not in staged:
            base, box = pad8(flatten_white(load_base(pose)))
            Image.fromarray(base).save(VIS / "staged" / base_name)
            ComfyClient.stage_input(VIS / "staged" / base_name)
            staged.add(base_name)
        if mask_name not in staged:
            mk, _ = pad8(mask_for(pose, kind, anchors))
            Image.fromarray(mk).convert("RGB").save(
                VIS / "staged" / mask_name)
            ComfyClient.stage_input(VIS / "staged" / mask_name)
            staged.add(mask_name)
        t0 = time.monotonic()
        dn = j.get("denoise", denoise)
        paths = client.generate(
            "sdxl_lora_inpaint", VIS / "raw", timeout=300,
            image=base_name, mask=mask_name,
            prompt=j["prompt"], negative=j["negative"],
            seed=j["seed"], denoise=dn)
        raw = np.asarray(Image.open(paths[0]).convert("RGB"))
        H, W = load_base(pose).shape[:2]
        Image.fromarray(unpad8(raw, (H, W))).save(
            VIS / "raw" / f"{j['out']}.png")
        paths[0].unlink()                 # drop the comfy-named duplicate
        manifest.append({**j, "denoise": dn,
                         "seconds": round(time.monotonic() - t0, 1),
                         "source": "local ComfyUI sdxl_lora_inpaint "
                                   "Illustrious-XL-v0.1 + ana_cast_v1@0.9",
                         "source_class": "local-gen",
                         "retrieved_at": now_utc()})
        manifest_p.write_text(json.dumps(manifest, indent=1), "utf-8")
        print(f"[{n}/{len(jobs)}] {j['out']} "
              f"{manifest[-1]['seconds']}s", flush=True)


def phase_composite() -> None:
    anchors = load_anchors()
    (VIS / "comp").mkdir(exist_ok=True)
    drifts = []
    for raw_p in sorted((VIS / "raw").glob("*.png")):
        pose = raw_p.stem.split("__")[0]
        kind = "eyes" if "__blink__" in raw_p.name else "mouth"
        rgba = load_base(pose)
        base_rgb = flatten_white(rgba)
        gen = np.asarray(Image.open(raw_p).convert("RGB"))
        mask = mask_for(pose, kind, anchors)
        comp = composite_rgb(base_rgb, gen, mask)
        out = np.dstack([comp, rgba[..., 3]])   # silhouette lock
        Image.fromarray(out).save(VIS / "comp" / raw_p.name)
        outside = mask <= 128
        drift = (np.abs(gen.astype(int) - base_rgb.astype(int))
                 .max(axis=2)[outside] > 8).mean()
        drifts.append(drift)
    print(f"composited {len(drifts)} images; VAE outside-mask drift "
          f"median {np.median(drifts):.1%} (killed by composite)")


def phase_sheets(comp_dir="comp", suffix="") -> None:
    anchors = load_anchors()
    (VIS / "sheets").mkdir(exist_ok=True)
    by_pose: dict[str, list[Path]] = {}
    for p in sorted((VIS / comp_dir).glob("*.png")):
        by_pose.setdefault(p.stem.split("__")[0], []).append(p)
    for pose, files in by_pose.items():
        a = anchors[pose]
        tiles = [_sheet_tile(flatten_white(load_base(pose)), "BASE", a)]
        for p in files:
            label = "__".join(p.stem.split("__")[1:])
            rgba = np.asarray(Image.open(p).convert("RGBA"))
            tiles.append(_sheet_tile(flatten_white(rgba), label, a))
        _grid(tiles, VIS / "sheets" / f"{pose}{suffix}_sheet.png",
              cols=min(7, len(tiles)))
    print(f"wrote {len(by_pose)} sheets to {VIS / 'sheets'}")


def _sheet_tile(rgb: np.ndarray, label: str, a: dict, fig_h=360,
                zoom_h=240) -> Image.Image:
    im = Image.fromarray(rgb)
    s = fig_h / im.height
    fig = im.resize((int(im.width * s), fig_h))
    # zoom on the mouth+eyes ellipse union so the gate agent can judge
    m, e = a["mouth"], a["eyes"]
    x0 = int(min(m["cx"] - m["rx"], e["cx"] - e["rx"]))
    x1 = int(max(m["cx"] + m["rx"], e["cx"] + e["rx"]))
    y0 = int(min(m["cy"] - m["ry"], e["cy"] - e["ry"]))
    y1 = int(max(m["cy"] + m["ry"], e["cy"] + e["ry"]))
    pad = int((x1 - x0) * 0.15)
    crop = im.crop((max(0, x0 - pad), max(0, y0 - pad),
                    min(im.width, x1 + pad), min(im.height, y1 + pad)))
    zs = zoom_h / crop.height
    zoom = crop.resize((int(crop.width * zs), zoom_h))
    w = max(fig.width, zoom.width) + 8
    tile = Image.new("RGB", (w, fig_h + zoom_h + 42), "white")
    tile.paste(fig, (4, 38))
    tile.paste(zoom, (4, 38 + fig_h))
    d = ImageDraw.Draw(tile)
    d.text((6, 6), label, fill=(180, 20, 20) if label != "BASE" else "black",
           font=_font(24))
    d.rectangle([0, 0, w - 1, fig_h + zoom_h + 41], outline=(200, 200, 200))
    return tile


def phase_vectorize(picks_path: Path) -> None:
    from vector.cells import vectorize
    picks = json.loads(Path(picks_path).read_text("utf-8"))
    pose_anchors = json.loads((FIX / "pose_anchors.json").read_text("utf-8"))
    (PUB / "visemes").mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict[str, str]] = {}
    for pose, vis in picks.items():
        for viseme, cand in vis.items():
            src = VIS / "comp" / f"{cand}.png"
            rgba = np.asarray(Image.open(src).convert("RGBA"))
            H, W = rgba.shape[:2]
            assert [W, H] == [pose_anchors[pose]["w"],
                              pose_anchors[pose]["h"]], \
                f"{cand}: {W}x{H} != base SVG canvas"
            svg = PUB / "visemes" / f"{pose}__{viseme}.svg"
            vectorize(src, svg)
            manifest.setdefault(pose, {})[viseme] = \
                f"characters/cast_ep1/visemes/{pose}__{viseme}.svg"
            print(f"{pose}.{viseme} <- {cand}")
    # A pose whose BASE drawing already is one of the visemes maps that
    # slot straight to the base SVG — sol_laugh is drawn mid-laugh, so
    # its wide-open mouth is the 'open' shape and regenerating one would
    # only risk drift.
    for pose, slot in BASE_IS.items():
        if pose in manifest:
            manifest[pose][slot] = f"characters/cast_ep1/{pose}.svg"
            print(f"{pose}.{slot} <- base drawing")
    (FIX / "visemes.json").write_text(json.dumps(manifest, indent=1),
                                      "utf-8")
    print(f"wrote {FIX / 'visemes.json'} "
          f"({sum(len(v) for v in manifest.values())} visemes)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("phase", choices=["anchors", "gen", "composite",
                                      "sheets", "vectorize"])
    ap.add_argument("--jobs-file", help="gen: JSON job list (regen loop)")
    ap.add_argument("--picks", help="vectorize: pose->viseme->candidate")
    ap.add_argument("--comp-dir", default="comp")
    ap.add_argument("--suffix", default="")
    args = ap.parse_args()
    if args.phase == "anchors":
        phase_anchors()
    elif args.phase == "gen":
        jobs = (json.loads(Path(args.jobs_file).read_text("utf-8"))
                if args.jobs_file else None)
        phase_gen(jobs)
    elif args.phase == "composite":
        phase_composite()
    elif args.phase == "sheets":
        phase_sheets(args.comp_dir, args.suffix)
    elif args.phase == "vectorize":
        phase_vectorize(Path(args.picks))


if __name__ == "__main__":
    main()
