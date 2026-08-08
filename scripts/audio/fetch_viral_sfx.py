"""Download the ACTUAL trending transition sounds, not lookalikes.

WHY THIS REPLACES THE SYNTHESISED PACK. make_viral_sfx.py generates a
convincing riser and a convincing boom, and the owner's verdict on it was
blunt and correct: a synthesised Vine Boom is not the Vine Boom. These
sounds work precisely BECAUSE the audience has heard them ten thousand
times - recognition is the entire effect, and recognition cannot be
resynthesised. A near-miss is worse than nothing, because it reads as a
cheap imitation of a sound everyone knows.

So these are fetched from myinstants.com, which is where the meme-sound
canon actually lives and which serves plain MP3s at stable URLs.

LICENCE, STATED PLAINLY AND ONCE. These are meme/UGC sounds with no clean
licence chain - "Among Us" is InnerSloth's game audio, "Vine Boom" is a
sampled hit of unclear origin, "Faah" is somebody's recorded voice. They
are ubiquitous on TikTok/Reels/Shorts and the platforms do not police them
in practice, and the owner has declared this content non-commercial. That
is the basis for using them. It is NOT a licence, and they should not ship
in anything sold or in anything that needs a clean rights audit. The
synthesised pack stays in the repo as the rights-clean alternative for
exactly that case.

  python scripts/audio/fetch_viral_sfx.py
Writes remotion/public/audio/viral_real/ + a provenance.json
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "remotion", "public", "audio", "viral_real")
BASE = "https://www.myinstants.com/media/sounds/"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0 Safari/537.36")

# (local name, remote slug, what it is for)
PACK = [
    ("vine_boom", "vine-boom.mp3", "statement · more comedic"),
    ("vine_boom_bass", "vine-boom-bass-boost-sound-effect.mp3",
     "statement · more comedic, heavier"),
    ("among_us", "among-us-role-reveal-sound.mp3", "reveal · unexpected"),
    ("faah", "faahhhhhh.mp3", "vocal accent · punchline"),
    ("riser_metallic", "popular-riser-metallic-sound-effect.mp3",
     "transition · feel smoother"),
    ("riser_suspense", "cinematic-suspense-riser.mp3",
     "transition · build tension"),
    ("whoosh", "whoosh-sfx.mp3", "transition · the cut itself"),
    ("whoosh_fire", "fire-whoosh.mp3", "transition · heavier cut"),
    ("core", "core-sound-effect.mp3", "statement · more important"),
    ("core_tiktok", "tiktok-core-sound-effect.mp3",
     "statement · more important, trending mix"),
]


def probe(path):
    """Duration and bitrate, so a 0-byte or HTML-error file cannot pass."""
    ff = next((p for p in (r"C:\ffmpeg\bin\ffprobe.exe", "ffprobe")
               if os.path.exists(p) or p == "ffprobe"), "ffprobe")
    r = subprocess.run([ff, "-v", "error", "-show_entries",
                        "format=duration,bit_rate", "-of",
                        "default=nw=1:nk=1", path],
                       capture_output=True, text=True)
    vals = [v for v in r.stdout.split() if v.strip()]
    if len(vals) < 1:
        return None, None
    dur = float(vals[0]) if vals[0] not in ("N/A",) else None
    br = int(vals[1]) // 1000 if len(vals) > 1 and vals[1] != "N/A" else None
    return dur, br


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    rows, bad = [], 0
    for name, slug, purpose in PACK:
        dest = os.path.join(OUT, name + ".mp3")
        req = urllib.request.Request(BASE + slug, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
        except Exception as e:
            print(f"  {name:16s} FAILED  {type(e).__name__}")
            bad += 1
            continue
        # an HTML error page is still a 200; verify it is really audio
        if not data[:3] in (b"ID3", b"\xff\xfb\x00") and b"<html" in data[:400]:
            print(f"  {name:16s} FAILED  server returned HTML")
            bad += 1
            continue
        with open(dest, "wb") as f:
            f.write(data)
        dur, br = probe(dest)
        if not dur:
            print(f"  {name:16s} FAILED  unreadable audio")
            bad += 1
            continue
        print(f"  {name:16s} {dur:5.2f}s  {br or '?'}kbps  "
              f"{len(data)//1024:4d}KB   {purpose}")
        rows.append({"name": name, "file": name + ".mp3", "purpose": purpose,
                     "seconds": round(dur, 2), "kbps": br,
                     "source": "https://www.myinstants.com/media/sounds/" + slug,
                     "source_class": "web-download",
                     "licence": "meme/UGC, no clean chain - non-commercial use only"})
    with open(os.path.join(OUT, "provenance.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1)
    print(f"\n{len(rows)} downloaded, {bad} failed -> "
          f"{os.path.relpath(OUT, REPO)}")
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
