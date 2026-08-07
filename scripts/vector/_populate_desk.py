"""Give ep.3-5 the reaction-cut grammar of the confirmed episodes.

WHAT THE CONFIRMED EPISODES ACTUALLY DO. Measuring ep.1 and ep.2 rather
than guessing: ~41% / ~34% of beats stage BOTH characters, and 14 of 16
(ep.1) and 9 of 11 (ep.2) of those gate their shots with `only:` - the
panel is populated, but the camera cuts between talent like a broadcast.
A genuine both-in-frame two-shot is rare on purpose: 13.3% of ep.1's
runtime, 4.7% of ep.2's. The life comes from the CUT (open on the
speaker, cut to the listener reacting), not from parking two heads in
frame.

Ep.3-5 were written as single-speaker beats - 84-89% of beats stage one
drawing - so they never cut to a reaction. Their speaker alternation is
already fine (ep.3/4 swap on 81% of beats vs ep.1's 76%); what is missing
is the second body to cut TO.

So this adds the partner and the cut, matching ep.1's proportions. It does
not touch a line, a VO cue or any timing.

  * skips beats that already stage two actors;
  * skips close-ups (shot punches past k=1.2) - a second head in a
    close-up is worse than an empty seat;
  * leaves two beats per episode ungated as real two-shots, framed
    between the seats, which is what ep.1 does.

Safe because no single-actor beat in any episode gates its shots with
`only:` (measured), and the partner is appended so index 0 stays the
speaker.

  python scripts/vector/_populate_desk.py 3 4 5
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

TOTAL = {"1": 5880, "2": 4500, "3": 5010, "4": 4200, "5": 4260}

# ep.1's proportion of beats staging two actors, applied to each episode
TARGET_SHARE = 0.41
UNGATED = 2          # real two-shots per episode, as ep.1 has

# seats, mirrored from remotion/src/motion/Set.tsx
SEAT_X = {"sol": 760, "rex": 322}
MID_X = (760 + 322) // 2

REX_LISTEN = ["rex_listen", "rex_skeptic"]
SOL_LISTEN = ["sol_smug_v1", "sol_finger"]

# POSE CHOICE MATTERS ONLY IN THE TWO-SHOT. In a reaction cut one actor is
# on screen, so a leaning pose is fine. Both in frame is different:
# rex_listen is drawn leaning in profile, which walks his head under Sol's
# and buries his face. Ep.1's two confirmed two-shots both use an UPRIGHT
# partner (rex_eager @123, rex_skeptic @220), so the two-shot takes those.
REX_TWO = "rex_skeptic"
SOL_TWO = "sol_smug_v1"

ONE_ACTOR = re.compile(r"actors: \[(\{poses: \[[^\]]*\][^{}]*\})\]")
SHOTS = re.compile(r"shots: \[(.*?)\],\n", re.S)


def punchy(chunk: str) -> bool:
    ks = [float(v) for v in re.findall(r"\bk(?:End)?: ([\d.]+)", chunk)]
    return bool(ks) and max(ks) >= 1.2


def populate(ep: str) -> None:
    p = REPO / f"remotion/src/compositions/FairMarketEp{ep}.tsx"
    s = p.read_text("utf-8")
    i = s.index("const BEATS")
    j = s.index("\n];", i)
    head, body, tail = s[:i], s[i:j], s[j:]

    chunks = re.split(r"(?=\n  \{at: \d+,)", body)
    # index the real beats and their durations
    beats = []
    for n, c in enumerate(chunks):
        m = re.match(r"\n  \{at: (\d+),", c)
        if m:
            beats.append((n, int(m.group(1))))
    for k, (n, at) in enumerate(beats):
        end = beats[k + 1][1] if k + 1 < len(beats) else TOTAL[ep]
        chunks[n] = chunks[n]  # no-op, keeps mapping explicit
        beats[k] = (n, at, end - at)

    already = sum(1 for n, _, _ in beats if chunks[n].count("poses:") > 1)
    want = max(0, round(len(beats) * TARGET_SHARE) - already)

    cands = [(n, dur) for n, _, dur in beats
             if chunks[n].count("poses:") == 1 and not punchy(chunks[n])]
    # longest beats have the most room for a cut; then restore story order
    cands.sort(key=lambda t: -t[1])
    chosen = sorted(cands[:want], key=lambda t: t[0])
    # spread the ungated two-shots through the episode
    two_shot = set()
    if chosen and UNGATED:
        for q in range(UNGATED):
            two_shot.add(chosen[min(len(chosen) - 1,
                                    round((q + 1) * len(chosen) / (UNGATED + 1)))][0])

    n_rex = n_sol = 0
    cut_added = 0
    for n, dur in chosen:
        c = chunks[n]
        m = ONE_ACTOR.search(c)
        if not m:
            continue
        who = re.search(r'poses: \["([a-z]+)_', m.group(1))
        if not who:
            continue
        if who.group(1) == "sol":
            pose = REX_TWO if n in two_shot else REX_LISTEN[n_rex % len(REX_LISTEN)]
            n_rex += 1
            partner = f'{{poses: ["{pose}"], kind: "bust", x: 400, y: 1270, h: 820}}'
            px = SEAT_X["rex"]
        else:
            pose = SOL_TWO if n in two_shot else SOL_LISTEN[n_sol % len(SOL_LISTEN)]
            n_sol += 1
            partner = f'{{poses: ["{pose}"], kind: "bust", x: 800, y: 1270, h: 840}}'
            px = SEAT_X["sol"]
        c = (c[:m.start()]
             + f"actors: [{m.group(1)},\n" + " " * 22 + f"{partner}]"
             + c[m.end():])

        sm = SHOTS.search(c)
        if sm:
            if n in two_shot:
                # a real two-shot: frame between the seats, stay wide
                new = (f"shots: [{{from: 0, k: 1.0, kEnd: 1.05, "
                       f"tx: {MID_X}, ty: 1250}}],\n")
            else:
                # open on the speaker, cut to the listener reacting
                cut = max(70, int(dur * 0.62))
                inner = sm.group(1).strip()
                first = inner.split("},")[0].rstrip()
                if not first.endswith("}"):
                    first += "}"
                first = first.replace("{from: 0,", "{from: 0, only: 0,", 1)
                new = (f"shots: [{first},\n" + " " * 11
                       + f"{{from: {cut}, only: 1, k: 1.02, kEnd: 1.1, "
                       f"tx: {px}, ty: 1240}}],\n")
                cut_added += 1
            c = c[:sm.start()] + new + c[sm.end():]
        chunks[n] = c

    p.write_text(head + "".join(chunks) + tail, "utf-8")
    print(f"ep{ep}: staged {len(chosen)} more beats "
          f"({already} already) -> {cut_added} reaction cuts, "
          f"{len(two_shot)} real two-shots")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        populate(a)
