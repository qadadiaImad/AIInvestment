"""Attach the generated caricature plates, and the real SFX, to ep.1 beats.

Keyed by VO stem rather than beat index so a retime cannot silently move a
plate onto the wrong line.

The SFX names are the WAV copies of the downloaded meme sounds
(v_whoosh / v_riser / v_boom / v_core / v_reveal), levelled at 0.55 on
conversion and then again per placement, because these files are mastered
loud for phone speakers and land about 10 dB over the VO if dropped in raw.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COMP = REPO / "remotion/src/compositions/FairMarketEp1.tsx"

# vo stem -> (exhibit, callout | None, [(sfx name, at, vol)])
PLAN = {
    "v1_sol_intro": ("capitol_ticker", None, [("v_whoosh", 0, 0.30)]),
    "v4_sol_politics": ("deal_handshake",
                        {"x": 0.46, "y": 0.55, "at": 30, "label": "THE DEAL"},
                        [("v_whoosh", 0, 0.32), ("v_core", 28, 0.34)]),
    "a3_sol_leaderboard": ("leaderboard_suits", None, [("v_whoosh", 0, 0.28)]),
    "a3_sol_others": ("committee_room", None, [("v_whoosh", 0, 0.26)]),
    "v7_rex_index": ("index_basket", None, [("v_reveal", 0, 0.26)]),
    "v11_sol_bothsides": ("two_podiums", None, [("v_whoosh", 0, 0.28)]),
    "v8_sol_legal": ("calendar_late",
                     {"x": 0.52, "y": 0.60, "at": 34, "label": "45 DAYS"},
                     [("v_whoosh", 0, 0.28), ("v_core", 32, 0.30)]),
    "a2_rex_copy": ("copy_homework", None, [("v_boom", 4, 0.30)]),
    "a6_sol_leverage": ("options_leverage", None, [("v_riser", 0, 0.24)]),
    "a5_sol_homework": ("watching_chart", None, [("v_whoosh", 0, 0.26)]),
    "a7_rex_oilthing": ("oil_tanker_strait", None, [("v_riser", 0, 0.26)]),
}


def main() -> None:
    s = COMP.read_text("utf-8")
    i = s.index("const BEATS")
    j = s.index("\n];", i)
    head, body, tail = s[:i], s[i:j], s[j:]
    chunks = re.split(r"(?=\n  \{at: \d+,)", body)
    done, seen = 0, set()

    for ci, c in enumerate(chunks):
        m = re.search(r'\bvo2?:\s*"([a-z0-9_]+)"', c)
        if not m or m.group(1) not in PLAN:
            continue
        stem = m.group(1)
        if "exhibit:" in c:
            continue
        ex, cal, sfx = PLAN[stem]
        add = '\n   exhibit: "%s",' % ex
        if cal:
            add += ('\n   callout: {x: %s, y: %s, at: %d, label: "%s"},'
                    % (cal["x"], cal["y"], cal["at"], cal["label"]))
        if sfx and "sfx:" not in c:
            items = ", ".join('{at: %d, name: "%s", vol: %.2f}' % (a, nm, v)
                              for nm, a, v in sfx)
            add += "\n   sfx: [%s]," % items
        mm = re.match(r"(\n  \{at: \d+,)", c)
        if not mm:
            continue
        chunks[ci] = c[:mm.end()] + add + c[mm.end():]
        done += 1
        seen.add(stem)

    COMP.write_text(head + "".join(chunks) + tail, "utf-8")
    missed = set(PLAN) - seen
    print("beats wired: %d" % done)
    if missed:
        print("NOT FOUND (check the stem): " + ", ".join(sorted(missed)))


if __name__ == "__main__":
    main()
