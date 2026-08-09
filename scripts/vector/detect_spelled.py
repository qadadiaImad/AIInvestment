"""Find lines where the TTS spelled a word out letter by letter.

The owner: "still get HA! pronounced letter by letter - disgusting audio".

He is right and it is measurable. Episode 1 says "HA! ...Fundamentals." -
five syllables - in 1.22s. Episode 3 says "HA! ...Bad banks." - three
syllables - in 1.67s. LONGER audio for FEWER syllables. That is what an
initialism sounds like: "aitch-ay" is three syllables where "hah" is one.

The cause is short ALL-CAPS tokens. Chatterbox reads a two- or three-letter
capitalised token as an initialism, because that is what such a token
usually is in written English (US, FBI, CEO). Episode 1 got away with it
because it only had four capitalised words and they were all long real
words. The v2 voice pass took capitals from 4 to 19 - which fixed the
emphasis and simultaneously walked into this.

This flags every line whose measured duration is far longer than its
syllable count predicts, so the fix targets what is actually broken instead
of every capitalised word in the script.

  python scripts/vector/detect_spelled.py [b|s|1|2]
"""
from __future__ import annotations

import json
import re
import sys
import wave
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DIRS = {"b": "fairmarket_bubbles", "s": "fairmarket_bshort",
        "1": "fairmarket", "2": "fairmarket_ep2"}
COMPS = {"b": "Bubbles", "s": "BubblesShort",
         "1": "FairMarketEp1", "2": "FairMarketEp2"}
PAIR = re.compile(
    r'vo: "([a-z_0-9]+)", speaker: "[A-Z]+",\s*\n?\s*line: "((?:[^"\\]|\\.)*)"')

VOWELS = "aeiouy"


def syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    n, prev = 0, False
    for ch in w:
        v = ch in VOWELS
        if v and not prev:
            n += 1
        prev = v
    if w.endswith("e") and n > 1:
        n -= 1
    return max(1, n)


def spoken_syllables(line: str) -> tuple[int, list[str]]:
    """Syllables as a HUMAN would say it, plus the caps tokens at risk."""
    total, risky = 0, []
    for raw in line.split():
        w = raw.strip('.,!?"—-…')
        if not w:
            continue
        if len(w) <= 4 and w.isupper() and w.isalpha():
            risky.append(w)
        total += syllables(w)
    return total, risky


def main() -> None:
    ep = next((a for a in sys.argv[1:] if a in DIRS), "b")
    comp = (REPO / "remotion/src/compositions" / (COMPS[ep] + ".tsx")
            ).read_text("utf-8", errors="replace")
    d = REPO / "remotion/public/audio" / DIRS[ep]

    rows = []
    for vo, line in PAIR.findall(comp):
        p = d / (vo + ".wav")
        if not p.exists():
            continue
        with wave.open(str(p), "rb") as w:
            secs = w.getnframes() / w.getframerate()
        syl, risky = spoken_syllables(line)
        if not syl:
            continue
        rows.append((secs / syl, secs, syl, risky, vo, line))

    rows.sort(reverse=True)
    med = sorted(r[0] for r in rows)[len(rows) // 2]
    print("%s: %d lines, median %.3f s/syllable" % (COMPS[ep], len(rows), med))
    print("flagging > 1.5x median, or any line with a short ALL-CAPS token\n")
    flagged = []
    for rate, secs, syl, risky, vo, line in rows:
        hot = rate > med * 1.5
        if hot or risky:
            mark = "SPELLED?" if hot else "at-risk "
            print("  %s %-22s %.2fs / %2d syl = %.3f  caps=%s"
                  % (mark, vo, secs, syl, rate, risky or "-"))
            print("           %s" % line[:78])
            if hot or risky:
                flagged.append(dict(vo=vo, line=line, rate=round(rate, 3),
                                    caps=risky, spelled=hot))
    out = REPO / "data/bubbles" / ("spelled_%s.json" % ep)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(flagged, indent=1), "utf-8")
    print("\n%d flagged -> %s" % (len(flagged), out.name))


if __name__ == "__main__":
    main()
