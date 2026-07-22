"""Record real browser interactions with the live terminal for the tutorial reel.

Playwright chromium, 1920x1080, records one video per scene into
higgs/tutorial_caps/. Slow, deliberate movements — footage is zoomed/panned
inside the Remotion composition, so calm pacing beats speed.

    python scripts/capture_terminal_tour.py
"""
from __future__ import annotations

import pathlib
import time

from playwright.sync_api import sync_playwright

BASE = "https://highreturnethicalscreen.vercel.app"
OUT = pathlib.Path(__file__).resolve().parents[1] / "higgs" / "tutorial_caps"
VIEWPORT = {"width": 1920, "height": 1080}


def slow_scroll(page, px_total, steps=30, pause=0.12):
    for _ in range(steps):
        page.mouse.wheel(0, px_total / steps)
        time.sleep(pause)


def scene(pw, name, actions):
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(viewport=VIEWPORT,
                              record_video_dir=str(OUT / name),
                              record_video_size=VIEWPORT)
    page = ctx.new_page()
    try:
        actions(page)
    finally:
        ctx.close()
        browser.close()
    # rename the random-named video to <name>.webm
    vids = list((OUT / name).glob("*.webm"))
    if vids:
        target = OUT / f"{name}.webm"
        if target.exists():
            target.unlink()
        vids[0].rename(target)
        print(f"OK {target.name}")


def s_hero(page):
    page.goto(f"{BASE}/halal", wait_until="networkidle")
    time.sleep(3.5)
    slow_scroll(page, 500, steps=20)
    time.sleep(1.5)


def s_table(page):
    page.goto(f"{BASE}/halal", wait_until="networkidle")
    time.sleep(2)
    slow_scroll(page, 2400, steps=45, pause=0.14)
    time.sleep(1.5)


def s_stock_math(page):
    page.goto(f"{BASE}/stocks/DDOG", wait_until="networkidle")
    time.sleep(2)
    slow_scroll(page, 3200, steps=40, pause=0.1)
    time.sleep(1)
    # open the first "show the math" details if present
    try:
        det = page.locator("details summary").first
        det.scroll_into_view_if_needed()
        time.sleep(1)
        det.click()
        time.sleep(3)
        slow_scroll(page, 600, steps=12)
        time.sleep(2)
    except Exception as e:  # noqa: BLE001
        print("details interaction skipped:", e)
        time.sleep(4)


def s_screener(page):
    page.goto(f"{BASE}/screener", wait_until="networkidle")
    time.sleep(2.5)
    slow_scroll(page, 1400, steps=30)
    time.sleep(2)


def s_map(page):
    page.goto(f"{BASE}/map", wait_until="networkidle")
    time.sleep(4)
    slow_scroll(page, 400, steps=10)
    time.sleep(3)


def s_news(page):
    page.goto(f"{BASE}/news", wait_until="networkidle")
    time.sleep(2.5)
    slow_scroll(page, 1600, steps=32)
    time.sleep(2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        for name, fn in [("hero", s_hero), ("table", s_table),
                         ("stock_math", s_stock_math), ("screener", s_screener),
                         ("map", s_map), ("news", s_news)]:
            scene(pw, name, fn)
    print("all scenes captured ->", OUT)


if __name__ == "__main__":
    main()


def s_halal_math(page):
    """Targeted: the halal card's Show-the-math accordion on the stock page."""
    page.goto(f"{BASE}/stocks/DDOG", wait_until="networkidle")
    time.sleep(2)
    try:
        card = page.locator("summary", has_text="AAOIFI").first
        card.scroll_into_view_if_needed()
        time.sleep(1.5)
        card.click()
        time.sleep(2.5)
        slow_scroll(page, 500, steps=14)
        time.sleep(2)
        ftse = page.locator("summary", has_text="FTSE").first
        if ftse.count() if hasattr(ftse, "count") else True:
            try:
                ftse.click()
                time.sleep(2.5)
            except Exception:
                pass
        time.sleep(1.5)
    except Exception as e:  # noqa: BLE001
        print("halal accordion interaction failed:", e)
        slow_scroll(page, 2000, steps=30)
        time.sleep(3)


def rerecord_single(name, fn):
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        scene(pw, name, fn)


if __name__ == "__main__" and "--halal-only" in __import__("sys").argv:
    rerecord_single("stock_math", s_halal_math)
    raise SystemExit(0)
