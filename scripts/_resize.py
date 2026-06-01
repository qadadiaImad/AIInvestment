from PIL import Image
import pathlib
src = r"C:\Users\imadq\.claude\image-cache\e04ae1e7-cd9c-491a-bc72-ef0303253474\1.png"
im = Image.open(src)
w, h = im.size
scale = 1400 / max(w, h)
if scale < 1:
    im = im.resize((int(w * scale), int(h * scale)))
out = r"C:\Users\imadq\AIInvestment\_shot_small.png"
im.convert("RGB").save(out, "PNG")
print(f"orig {w}x{h} -> {im.size} saved {out}")
