"""Re-usable capture script: pulls fresh, LEGIBLE, high-res screenshots of the
live AI Stack Terminal site (highreturnethicalscreen.vercel.app) for the
platform showcase carousel builder (_build_platform_carousel.py).

v2 (2026-07-23): the original version took full-desktop-page screenshots at
3456x2160 and the builder then cropped a thin strip out of them -- key
content (ticker symbols, node labels, card names) was cut off or too small
to read. This version captures each page TIGHTLY ZOOMED on its key content
(narrower viewport + CSS zoom + a clip region, or a scroll+clip for tall
static pages, or a wheel-zoom + density-based autocrop for the force-graph
map) so the important data is large enough to read at carousel size and the
whole capture is meant to be shown uncropped (object-fit: contain) in the
slide.

    python higgs/_capture_platform_src.py

Writes higgs/_platform_src/{home,map,map_zoom,chokepoints,resiliency,
screener,congress,strategies,halal}.jpg (overwrites existing).

IMPORTANT -- map_zoom is NOT pixel-deterministic: /map renders a force-
directed graph layout that differs slightly each page load, so a fixed
crop box picked for one run may not land on the densest hub cluster next
run. We handle this with a density-based autocrop (counts non-background
pixels in a sliding window over the canvas region and picks the highest-
density window) rather than a hardcoded box, so it self-corrects across
runs. Still: after running this script, VISUALLY VERIFY map_zoom.jpg shows
readable company node labels before using it -- re-run if the simulation
settled into a sparse region.
"""
from __future__ import annotations

import pathlib

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

HIGGS = pathlib.Path(__file__).resolve().parent
OUT = HIGGS / "_platform_src"

BASE_URL = "https://highreturnethicalscreen.vercel.app"
DSF = 2
QUALITY = 92


def _autocrop_densest(src_path, out_path, win_w, win_h, search_box):
    """Pick the win_w x win_h window (in physical px) inside search_box
    (sx0,sy0,sx1,sy1) with the most non-background (bright) pixels -- i.e.
    the busiest cluster of nodes/edges/labels -- and crop to it."""
    sx0, sy0, sx1, sy1 = search_box
    im_gray = Image.open(src_path).convert("L")
    arr = np.asarray(im_gray, dtype=np.float64)
    content = (arr > 35).astype(np.float64)
    integral = np.cumsum(np.cumsum(content, axis=0), axis=1)
    integral = np.pad(integral, ((1, 0), (1, 0)))
    H, W = content.shape
    best = (-1.0, sx0, sy0)
    step = 20
    for y in range(sy0, min(sy1, H - win_h), step):
        for x in range(sx0, min(sx1, W - win_w), step):
            total = (integral[y + win_h, x + win_w] - integral[y, x + win_w]
                     - integral[y + win_h, x] + integral[y, x])
            if total > best[0]:
                best = (total, x, y)
    _, bx, by = best
    Image.open(src_path).crop((bx, by, bx + win_w, by + win_h)).save(out_path, quality=QUALITY)
    print(f"   autocrop window=({bx},{by},{bx+win_w},{by+win_h}) score={best[0]:.0f}")


def capture():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])

        # ---- home & map: unchanged full-desktop overview captures. -------
        # home.jpg backs the CTA slide (top-of-page already reads fine at
        # cover-fit); map.jpg backs the blurred cover-slide background only
        # (never shown sharp/uncropped, so the full overview is fine there).
        pg = browser.new_page(viewport={"width": 1728, "height": 1080}, device_scale_factor=DSF)
        print("-> home")
        pg.goto(BASE_URL + "/", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(2500)
        pg.screenshot(path=str(OUT / "home.jpg"), type="jpeg", quality=QUALITY)

        print("-> map (overview, for cover bg)")
        pg.goto(BASE_URL + "/map", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(6000)
        pg.screenshot(path=str(OUT / "map.jpg"), type="jpeg", quality=QUALITY)
        pg.close()

        # ---- map_zoom: wheel-zoom into the graph, then autocrop the ------
        # densest labeled cluster. Target aspect ~1.30 (952x731 @2x slide box).
        print("-> map_zoom")
        pg = browser.new_page(viewport={"width": 1400, "height": 1000}, device_scale_factor=DSF)
        pg.goto(BASE_URL + "/map", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(6000)
        canvas = pg.evaluate("""() => {
          const c = document.querySelector('canvas');
          const r = c.getBoundingClientRect();
          return {x:r.x,y:r.y,w:r.width,h:r.height};
        }""")
        cx = canvas["x"] + canvas["w"] * 0.56
        cy = canvas["y"] + canvas["h"] * 0.62
        pg.mouse.move(cx, cy)
        for _ in range(11):
            pg.mouse.wheel(0, -220)
            pg.wait_for_timeout(150)
        # move off the canvas so a hover tooltip/citation popup isn't left
        # open over the graph when we screenshot (it happened -- vis-network's
        # edge-hover tooltip, class .vis-tooltip, can stick open after the
        # wheel-zoom sequence and its bright white box dominates the density
        # autocrop). Belt-and-suspenders: also force-hide it via JS.
        pg.mouse.move(10, 10)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(600)
        pg.evaluate("""() => {
          document.querySelectorAll('.vis-tooltip').forEach(el => {
            el.style.display = 'none';
            el.style.visibility = 'hidden';
          });
        }""")
        pg.wait_for_timeout(400)
        raw_path = OUT / "_map_raw.jpg"
        pg.screenshot(path=str(raw_path), type="jpeg", quality=QUALITY)
        search_box = (
            int(canvas["x"] * DSF), int(canvas["y"] * DSF),
            int((canvas["x"] + canvas["w"]) * DSF), int((canvas["y"] + canvas["h"]) * DSF),
        )
        _autocrop_densest(raw_path, OUT / "map_zoom.jpg", win_w=1250, win_h=960, search_box=search_box)
        raw_path.unlink(missing_ok=True)
        pg.close()

        # ---- chokepoints / resiliency / strategies: static content, ------
        # direct viewport clip (no scroll needed -- key content is at the
        # top of each page). Clip coords are CSS px (viewport space).
        print("-> chokepoints")
        pg = browser.new_page(viewport={"width": 1300, "height": 1010}, device_scale_factor=DSF)
        pg.goto(BASE_URL + "/chokepoints", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(3000)
        pg.screenshot(path=str(OUT / "chokepoints.jpg"), type="jpeg", quality=QUALITY,
                       clip={"x": 0, "y": 245, "width": 1300, "height": 760})
        pg.close()

        print("-> resiliency")
        pg = browser.new_page(viewport={"width": 1300, "height": 1100}, device_scale_factor=DSF)
        pg.goto(BASE_URL + "/resiliency", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(4000)
        pg.screenshot(path=str(OUT / "resiliency.jpg"), type="jpeg", quality=QUALITY,
                       clip={"x": 0, "y": 97, "width": 1300, "height": 953})
        pg.close()

        print("-> strategies")
        pg = browser.new_page(viewport={"width": 1300, "height": 1000}, device_scale_factor=DSF)
        pg.goto(BASE_URL + "/strategies", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(3000)
        pg.screenshot(path=str(OUT / "strategies.jpg"), type="jpeg", quality=QUALITY,
                       clip={"x": 0, "y": 240, "width": 1300, "height": 640})
        pg.close()

        # ---- screener / congress: narrow viewport + CSS zoom on the ------
        # table so ticker/price/etc text renders big, then clip the header
        # + first N rows (table doesn't reflow with viewport -- it just
        # overflows -- so the narrow viewport naturally shows only the
        # left, most-important columns).
        print("-> screener")
        pg = browser.new_page(viewport={"width": 980, "height": 760}, device_scale_factor=DSF)
        pg.goto(BASE_URL + "/screener", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(2500)
        pg.evaluate("document.documentElement.style.zoom = '1.35'")
        pg.wait_for_timeout(400)
        thead_y = pg.evaluate("document.querySelector('table thead').getBoundingClientRect().y")
        pg.screenshot(path=str(OUT / "screener.jpg"), type="jpeg", quality=QUALITY,
                       clip={"x": 0, "y": max(thead_y - 4, 0), "width": 980, "height": 590})
        pg.close()

        print("-> congress")
        pg = browser.new_page(viewport={"width": 1120, "height": 900}, device_scale_factor=DSF)
        pg.goto(BASE_URL + "/congress", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(2500)
        pg.evaluate("document.documentElement.style.zoom = '1.15'")
        pg.wait_for_timeout(400)
        thead_y = pg.evaluate("document.querySelector('table thead').getBoundingClientRect().y")
        pg.screenshot(path=str(OUT / "congress.jpg"), type="jpeg", quality=QUALITY,
                       clip={"x": 0, "y": max(thead_y, 0), "width": 1120, "height": 595})
        pg.close()

        # ---- halal: the SECOND table on the page is the per-company ------
        # verdict table (the first is the 5-standards comparison legend) --
        # scroll to it, zoom, clip.
        print("-> halal")
        pg = browser.new_page(viewport={"width": 1100, "height": 900}, device_scale_factor=DSF)
        pg.goto(BASE_URL + "/halal", wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(2500)
        pg.evaluate("document.documentElement.style.zoom = '1.2'")
        pg.wait_for_timeout(400)
        verdict_y = pg.evaluate("""() => {
          const tables = [...document.querySelectorAll('table')];
          return tables[1].getBoundingClientRect().y;
        }""")
        pg.evaluate(f"window.scrollTo(0, {verdict_y / 1.2 - 20})")
        pg.wait_for_timeout(300)
        verdict_y2 = pg.evaluate("""() => {
          const tables = [...document.querySelectorAll('table')];
          return tables[1].getBoundingClientRect().y;
        }""")
        pg.screenshot(path=str(OUT / "halal.jpg"), type="jpeg", quality=QUALITY,
                       clip={"x": 0, "y": max(verdict_y2, 0), "width": 1100, "height": 585})
        pg.close()

        browser.close()
    print(f"DONE -> {OUT}")


if __name__ == "__main__":
    capture()
