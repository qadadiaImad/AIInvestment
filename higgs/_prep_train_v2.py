"""Prep the v2 character-LoRA training dataset (retrain fix for the consistency
post-mortem, 2026-08-03).

v1 under-baked because the 14 grasshopper images ALL sat on the same pale-mint
background AND every caption said "teal background" — so the trigger `fablegh`
entangled with that background instead of binding to the character. This script
breaks the entanglement WITHOUT new GPU renders: it masks the flat mint backdrop
(color-distance from the top row) and recolors it to varied tints, writing a
matching caption that names each variant's real background. The character, wings,
eyes, and foreground flowers are preserved (they fall outside the mint tolerance).

The ant set already has varied natural backgrounds, so it's copied as-is.

Output: higgs/fable/train/v2/{grasshopper,ant}/ + fable_lora_dataset_v2.zip.
Upload the zip to Kaggle as `fable_training` (replacing v1) and retrain with the
v2 params in docs/train-character-lora.md (dim32 / alpha16 / 14 epochs).

    python higgs/_prep_train_v2.py
"""
import math
import pathlib
import shutil
import zipfile
from PIL import Image, ImageFilter

TRAIN = pathlib.Path(__file__).resolve().parent / "fable" / "train"
V2 = TRAIN / "v2"
# (name, rgb) tints to scatter the grasshopper across backgrounds
BG_VARIANTS = [("tan", (214, 196, 168)), ("blue", (150, 175, 205)), ("lavender", (203, 188, 214))]


def recolor_bg(src: pathlib.Path, newbg, tol=42) -> Image.Image:
    im = Image.open(src).convert("RGB")
    w, h = im.size
    px = im.load()
    top = [im.getpixel((x, 1)) for x in range(0, w, 20)]
    base = tuple(sum(c) / len(top) for c in zip(*top))
    mask = Image.new("L", (w, h), 0)
    mp = mask.load()
    for y in range(h):
        for x in range(w):
            if math.dist(px[x, y], base) < tol:
                mp[x, y] = 255
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.5))
    return Image.composite(Image.new("RGB", (w, h), newbg), im, mask)


def main():
    if V2.exists():
        shutil.rmtree(V2)
    (V2 / "grasshopper").mkdir(parents=True)
    (V2 / "ant").mkdir(parents=True)

    # --- grasshopper: originals + background-recolored variants ---
    gh_src = sorted((TRAIN / "grasshopper").glob("*.png"))
    gh_n = 0
    for png in gh_src:
        cap = png.with_suffix(".txt").read_text(encoding="utf-8").strip()
        # original (keep)
        shutil.copy(png, V2 / "grasshopper" / png.name)
        (V2 / "grasshopper" / png.with_suffix(".txt").name).write_text(cap, encoding="utf-8")
        gh_n += 1
        # variants (recolor bg + rewrite the background phrase in the caption)
        base_cap = cap.split(", teal background")[0]  # strip the baked-in bg phrase
        for tag, rgb in BG_VARIANTS:
            stem = f"{png.stem}_{tag}"
            recolor_bg(png, rgb).save(V2 / "grasshopper" / f"{stem}.png")
            (V2 / "grasshopper" / f"{stem}.txt").write_text(
                f"{base_cap}, {tag} background with orange flowers", encoding="utf-8")
            gh_n += 1

    # --- ant: already varied natural backgrounds -> copy as-is ---
    ant_n = 0
    for f in sorted((TRAIN / "ant").glob("*")):
        if f.suffix in (".png", ".txt"):
            shutil.copy(f, V2 / "ant" / f.name)
            if f.suffix == ".png":
                ant_n += 1

    # --- zip (grasshopper/ and ant/ at root, matching Kaggle Cell 1's glob) ---
    zpath = TRAIN / "fable_lora_dataset_v2.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for sub in ("grasshopper", "ant"):
            for f in sorted((V2 / sub).glob("*")):
                z.write(f, f"{sub}/{f.name}")
    print(f"grasshopper: {gh_n} images (14 orig + {gh_n-14} bg-variants)")
    print(f"ant: {ant_n} images (as-is, already varied bg)")
    print(f"zip -> {zpath}  ({zpath.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
