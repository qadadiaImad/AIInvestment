"""
Render IONQ slide_1.html … slide_5.html → slide_1.png … slide_5.png
at 1080x1350, device_scale_factor=2, waiting for Google Fonts.

Usage (Windows):
    pip install playwright
    python -m playwright install chromium
    python render.py

The script lives next to the slides — it resolves paths relative to itself,
so it works regardless of cwd.
"""
import os, sys, pathlib, time
from playwright.sync_api import sync_playwright

W, H = 1080, 1350
HERE = pathlib.Path(__file__).resolve().parent
SLIDES = [HERE / f"slide_{i}.html" for i in range(1, 6)]

def main():
    missing = [p for p in SLIDES if not p.exists()]
    if missing:
        print("MISSING:", *missing, sep="\n  ")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        ctx = browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=2,
        )
        page = ctx.new_page()
        for src in SLIDES:
            out = src.with_suffix(".png")
            url = src.as_uri()  # file:///C:/.../slide_1.html
            print(f"render {src.name}  ->  {out.name}")
            page.goto(url, wait_until="networkidle")
            # Belt-and-braces font wait — Google Fonts can be slow on a cold cache.
            try:
                page.evaluate("document.fonts && document.fonts.ready")
            except Exception:
                pass
            page.wait_for_timeout(2000)
            page.screenshot(
                path=str(out),
                clip={"x": 0, "y": 0, "width": W, "height": H},
            )
            size = out.stat().st_size
            print(f"  {out.name}  {size/1024:.1f} KB")
        browser.close()
    print("DONE")

if __name__ == "__main__":
    main()
