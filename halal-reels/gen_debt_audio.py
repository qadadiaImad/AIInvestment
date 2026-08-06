"""VO for the "World Owes $348T — to WHO?" debt/bonds explainer (edge-tts, Christopher,
the analyst-detective voice) + karaoke word timings. Writes public/debt_*.mp3 + debt_captions.json.

    python gen_debt_audio.py
"""
import asyncio
import json
import pathlib

import edge_tts

PUB = pathlib.Path(__file__).resolve().parent / "public"
VOICE, RATE = "en-US-ChristopherNeural", "+6%"

LINES = {
    "d1": "The entire world is in debt. Three hundred forty-eight trillion dollars. So, dumb question nobody actually answers: in debt to who?",
    "d2": "It's not one loan, it's everyone. Households owe sixty-four trillion. Companies, a hundred. Governments, another hundred and seven. Add the banks: three hundred forty-eight.",
    "d3": "But every dollar you owe is a dollar someone else is owed. So if the whole planet is in the red, who's in the black?",
    "d4": "The answer is a piece of paper called a bond. A government needs cash now, so it writes an I.O.U. Lend me a hundred, I'll pay you back with interest on a set date. Sell millions of them, and that pile of paper is the national debt.",
    "d5": "So who buys them? Foreign countries, Japan, Britain, China, hold about a third. But the biggest lender to your government is you. Your pension, your bank, your retirement fund. The world doesn't owe some outsider. It mostly owes itself.",
    "d6": "Here's the part that stings. Just the interest on America's debt hit nine hundred seventy billion last year. More than it spends on its entire military. Not paying it down, just renting it.",
    "d7": "A planet that owes itself trillions, paying itself interest it has to borrow to afford. Genius, or a time bomb? Tell me below.",
}


async def gen(key, text):
    c = edge_tts.Communicate(text, VOICE, rate=RATE)
    audio = bytearray()
    bounds = []
    async for ch in c.stream():
        if ch["type"] == "audio":
            audio += ch["data"]
        elif ch["type"] in ("WordBoundary", "SentenceBoundary"):
            bounds.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7))
    (PUB / f"{key}.mp3").write_bytes(bytes(audio))
    start = bounds[0][0] if bounds else 0.05
    end = bounds[-1][1] if bounds else 0.05 + len(text) / 15.0
    toks = text.split()
    wts = [len(w) + 1 for w in toks]
    total = sum(wts) or 1
    t = start
    words = []
    for w, wt in zip(toks, wts):
        seg = (end - start) * wt / total
        words.append({"w": w, "t0": round(t, 3), "t1": round(t + seg, 3)})
        t += seg
    return words, round(end + 0.12, 3)


async def main():
    PUB.mkdir(parents=True, exist_ok=True)
    caps = {}
    for lid, text in LINES.items():
        words, dur = await gen(f"debt_{lid}", text)
        caps[lid] = {"text": text, "words": words, "dur": dur, "frames": round(dur * 30)}
        print(f"  debt_{lid}.mp3  {dur:.2f}s ({round(dur*30)}f)")
    (PUB / "debt_captions.json").write_text(json.dumps(caps, indent=1), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    asyncio.run(main())
