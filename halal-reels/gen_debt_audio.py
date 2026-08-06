"""VO for the "World Owes $348T — to WHO?" debt/bonds explainer.

Voice = "In a Nutshell" *style* (not a clone of the real narrator): a warm British male
neural voice (en-GB-RyanNeural), measured pace, slightly lowered pitch, and short wondering
sentences with '…' pause beats — the cadence that keeps it from sounding monotone.
Writes public/debt_*.mp3 + debt_captions.json.

    python gen_debt_audio.py
"""
import asyncio
import json
import pathlib

import edge_tts

PUB = pathlib.Path(__file__).resolve().parent / "public"
VOICE, RATE, PITCH = "en-GB-RyanNeural", "-4%", "-2Hz"

LINES = {
    "d1": "The entire world is in debt. Not one country. Not one company. The whole planet. Three hundred and forty-eight trillion dollars. Which raises a strange little question… in debt to whom?",
    "d2": "Because this isn't one giant loan. It's all of us. Households owe sixty-four trillion. Companies, a hundred. Governments, another hundred and seven. Stack it all up, and you get three hundred and forty-eight.",
    "d3": "But here's the strange thing about debt. Every dollar owed is a dollar someone else is owed. So if the entire planet is in the red… who on Earth is in the black?",
    "d4": "The answer hides inside a single piece of paper. A bond. A government needs money today, so it writes a promise. Lend me a hundred, and I'll pay you back, with interest, later. Print millions of those promises, and that pile of paper becomes the national debt.",
    "d5": "So who holds all these promises? Some are foreign. Japan, Britain, China, together about a third. But the biggest lender of all… is you. Your pension. Your bank. Your savings. The world doesn't owe some distant stranger. Mostly, it owes itself.",
    "d6": "And yet, there's a catch. Last year, the interest alone on America's debt hit nine hundred and seventy billion dollars. More than it spends on its entire military. That isn't shrinking the debt. That's just… renting it.",
    "d7": "A planet that owes itself trillions, and borrows just to pay the interest. Brilliant design? Or a slow motion time bomb? Tell me what you think, below.",
}


async def gen(key, text):
    c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
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
