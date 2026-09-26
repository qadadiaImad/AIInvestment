"""Presenter cut of explainer 2: each scene = a HOOK spoken on camera + the REST as voice-over.

    cd scripts && python -m bumper.narration3

Reads narration2.json (numbers already templated from the screen outputs) and writes
narration3.json with, per scene: hook (<= ~24 words, spoken by the presenter on camera
via grok native dialogue) and rest (voice-over). Both end up in the same voice after
Chatterbox voice conversion to the presenter's clone.
"""
from __future__ import annotations

import json
import pathlib
import re

D = pathlib.Path(__file__).resolve().parents[2] / "data" / "bumper" / "2026-09-25"
MAX_HOOK_WORDS = 26


def split_hook(text: str):
    sents = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
    hook, rest = [], []
    for s in sents:
        if not rest and sum(len(x.split()) for x in hook) + len(s.split()) <= MAX_HOOK_WORDS:
            hook.append(s)
        else:
            rest.append(s)
    if not hook:  # first sentence alone is too long: it is the hook anyway
        hook, rest = sents[:1], sents[1:]
    if sum(len(x.split()) for x in hook) < 10 and rest:  # a six-word hook leaves a 10 s clip half silent
        hook, rest = hook + rest[:1], rest[1:]
    return " ".join(hook), " ".join(rest)


def build():
    scenes = json.load(open(D / "narration2.json", encoding="utf-8"))
    out = []
    # proper nouns defeat the transcript gate (STT spells them its own way); keep names in the voice-over and on the chart
    HOOK_OVERRIDE = {"11_robots": "So, robotics. Five pure plays sit under three billion dollars, and most of them fail on the first gate."}
    for s in scenes:
        hook, rest = split_hook(s["text"])
        if s["id"] in HOOK_OVERRIDE:
            hook, rest = HOOK_OVERRIDE[s["id"]], s["text"]
        out.append({**s, "hook": hook, "rest": rest})
    (D / "narration3.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for s in out:
        print(f"{s['id']}: HOOK({len(s['hook'].split())}w) {s['hook']}\n    REST({len(s['rest'].split())}w)")
    return out


if __name__ == "__main__":
    build()
