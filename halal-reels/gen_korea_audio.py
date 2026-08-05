"""Korea 'human-stakes leverage' episode audio — neural anchor voice (edge-tts,
en-US-EmmaNeural, same recurring anchor as Ep2) + word timings for karaoke.
Reuses the newsroom bed. Writes public/korea_k1..k5.mp3 + public/korea_captions.json.

    python gen_korea_audio.py
"""
import asyncio
import json
import pathlib

import edge_tts

PUB = pathlib.Path(__file__).resolve().parent / "public"
VOICE = "en-US-EmmaNeural"
RATE = "-6%"

LINES = {
    "k1": "One point two million Koreans got a margin call in a single week.",
    "k2": "They'd borrowed a record thirty-eight trillion won, much of it against their homes, for two chip stocks.",
    "k3": "Then the index dropped twenty-seven percent. With leverage, you don't lose what you put in. You lose what you borrowed.",
    "k4": "Sixty percent of the wiped-out were in their twenties and thirties.",
    "k5": "Same A.I. memory trade you own. Just with the leverage showing.",
}


async def gen(key: str, text: str):
    c = edge_tts.Communicate(text, VOICE, rate=RATE)
    audio = bytearray()
    bounds = []
    async for ch in c.stream():
        if ch["type"] == "audio":
            audio += ch["data"]
        elif ch["type"] in ("WordBoundary", "SentenceBoundary"):
            bounds.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7))
    (PUB / f"korea_{key}.mp3").write_bytes(bytes(audio))
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
    for key, text in LINES.items():
        words, dur = await gen(key, text)
        caps[key] = {"text": text, "words": words, "dur": dur, "frames": round(dur * 30)}
        print(f"  korea_{key}.mp3  {dur:.2f}s  ({round(dur * 30)}f)  {len(words)} words")
    (PUB / "korea_captions.json").write_text(json.dumps(caps, indent=1), encoding="utf-8")
    print("captions -> public/korea_captions.json")


if __name__ == "__main__":
    asyncio.run(main())
