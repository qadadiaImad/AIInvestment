"""Generate the caricature exhibits that play on the studio wall.

THE GAP THIS FILLS. The wall has only ever carried charts and text cards.
The owner's note: "no animation to explain what Sol's saying - not only
graph - add caricatures portraying politicians and big corpo shaking hands
and combining political and economic ambitions". A candlestick cannot show
a bargain being struck; a drawing can.

WHY Z-IMAGE AND NOT THE SDXL CAST MODEL. The first pass ran through
sdxl_lora_t2i with the cast LoRA at 0 and SIX OF EIGHT were unusable -
calendar_late came back as blank grey canvas, chip_gavel as an
unrecognisable blob, capitol_ticker with neither dome nor ticker. That is
not a prompt problem: Illustrious-XL is a character/anime checkpoint and it
cannot draw symbolic still life or architecture. Z-Image, already on disk
as a separate UNET, drew all three cleanly on the first attempt at the same
sizes - a real calendar with a circled date and a melting clock, a legible
microchip and gavel, and two suits actually shaking hands.

Z-Image also has no cast LoRA at all, which removes the risk the SDXL route
had to guard against: a generated figure inheriting Sol's face and reading
as Sol himself doing the deal.

WHY NOBODY REAL IS DRAWN. The episodes name real offices ("the Speaker's
household") because those are public record, and the footer carries
"parody · public record · educational, not advice". A recognisable likeness
of a living politician is a different thing entirely and buys nothing the
archetype does not - the point is the TRANSACTION, not the person. So:
generic suit, generic flag pin, no face anyone can name.

Output is sized to the wall (976x740) and rendered dark, so it drops
straight onto the video wall with no keying step.

  python scripts/vector/gen_exhibits.py            # all
  python scripts/vector/gen_exhibits.py deal_handshake
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from comfy.client import ComfyClient          # noqa: E402
from comfy.launch import ensure_server         # noqa: E402

OUT = REPO / "remotion/public/characters/cast_ep1/exhibits"
W, H = 976, 736          # the wall, rounded to /8 for the sampler

# One shared look so twelve separate generations read as one graphics
# package rather than twelve stock illustrations. Z-Image takes plain
# description, not danbooru tags.
STYLE = ("flat vector editorial illustration, bold black outlines, limited "
         "palette of teal amber and cream on a very dark navy background, "
         "clean broadcast news graphic, centered, high contrast, no text")
NEG = ("text, watermark, letters, words, caption, logo, blurry, photo, "
       "3d render, extra fingers, deformed hands, recognisable celebrity, white border, picture frame, matte, letterbox, margin")

EXHIBITS = [
    ("deal_handshake",
     "two men in dark business suits firmly shaking hands across a polished "
     "desk, one wears a small flag pin on his lapel, the other holds a "
     "briefcase, a rising stock chart glows on the wall behind them"),
    ("capitol_ticker",
     "a grand government building with a domed roof and tall columns at "
     "night, a glowing stock ticker tape wrapped around the columns like a "
     "ribbon, gold coins falling gently through the air"),
    ("chip_gavel",
     "a large computer microchip on the left and a wooden judge's gavel on "
     "the right, the gavel striking down, a single beam of light between "
     "them"),
    ("leaderboard_suits",
     "three men in dark suits standing on an olympic winners podium holding "
     "briefcases up like trophies, a glowing scoreboard behind them"),
    ("index_basket",
     "a woven shopping basket filled with tiny government buildings and "
     "glowing gold coins, a price tag hanging from the handle"),
    ("calendar_late",
     "a wall calendar with most days crossed out in red and one date "
     "circled, a melting clock draped over the top corner, an envelope "
     "arriving late"),
    ("committee_room",
     "a long curved committee bench seen from the front with several "
     "silhouetted figures in suits seated behind microphones, an empty "
     "witness chair facing them under a hard overhead light"),
    ("watching_chart",
     "a man in a suit seen from behind, hands clasped, standing small in "
     "front of an enormous glowing line chart on a wall"),
    ("copy_homework",
     "a young man in a vest leaning over to copy from an older man's paper, "
     "but the paper he is copying is dated and yellowed, a clock on the "
     "wall behind them"),
    ("options_leverage",
     "a small stack of coins on the left connected by an arrow to a huge "
     "tower of coins on the right, a lever and fulcrum underneath doing the "
     "lifting, dramatic scale difference"),
    ("two_podiums",
     "two speaking podiums facing each other, one lit red and one lit blue, "
     "a single briefcase sitting exactly between them on the floor"),
    ("oil_tanker_strait",
     "an oil tanker seen from above passing through a very narrow sea "
     "channel between two dark headlands, a barrel icon and a rising price "
     "arrow in the corner of the sky"),
]


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    want = set(sys.argv[1:])
    jobs = [e for e in EXHIBITS if not want or e[0] in want]
    if not jobs:
        sys.exit("no matching exhibit; known: "
                 + ", ".join(n for n, _ in EXHIBITS))
    OUT.mkdir(parents=True, exist_ok=True)
    ensure_server()
    client = ComfyClient()
    client._last_family = "zimage"

    manifest_p = OUT / "provenance.json"
    manifest = (json.loads(manifest_p.read_text("utf-8"))
                if manifest_p.exists() else [])
    manifest = [m for m in manifest if m["name"] not in {n for n, _ in jobs}]

    for i, (name, subject) in enumerate(jobs):
        t0 = time.monotonic()
        paths = client.generate(
            "zimage_t2i", OUT, timeout=600,
            prompt=subject + ", " + STYLE, negative=NEG,
            width=W, height=H, seed=9110 + i * 47)
        dest = OUT / (name + ".png")
        if dest.exists():
            dest.unlink()
        paths[0].replace(dest)
        secs = time.monotonic() - t0
        manifest.append({
            "name": name, "file": name + ".png", "subject": subject,
            "w": W, "h": H, "seed": 7300 + i * 31, "seconds": round(secs, 1),
            "source": "local ComfyUI zimage_t2i z_image_turbo_fp8",
            "source_class": "local-gen", "retrieved_at": now_utc()})
        print(f"  {name:18s} {secs:5.1f}s", flush=True)

    manifest_p.write_text(json.dumps(manifest, indent=1), "utf-8")
    print("-> " + str(OUT))


if __name__ == "__main__":
    main()
