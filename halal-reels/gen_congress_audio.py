"""'917 Days Late' episode audio — a distinct MALE neural voice (edge-tts Christopher,
measured/deadpan) for the HOST_ANALYST 'detective' character (differentiated from the
Emma anchor). Word timings for karaoke. Reuses the newsroom bed.
Writes public/congress_c1..c5.mp3 + public/congress_captions.json.

Facts (verified from web/public/data/congress.json, 2026-08-05, perishable):
  McCormick (GA-06)  MSFT buy 03/15/2023 -> filed 09/17/2025  = 917-day lag
  McClain  (MI-09)   NVDA/AMD/TSM 03/11/2024 -> filed 08/13/2025 = 520-day lag
  STOCK Act requires disclosure within 45 days.

    python gen_congress_audio.py
"""
import asyncio
import json
import pathlib

import edge_tts

PUB = pathlib.Path(__file__).resolve().parent / "public"
VOICE = "en-US-ChristopherNeural"
RATE = "+12%"

LINES = {
    "c1": "The law says forty-five days to report a stock trade. This congressman took nine hundred seventeen.",
    "c2": "He bought Microsoft in March 2023. Voters didn't find out until September 2025.",
    "c3": "And he's not alone. Another member bought Nvidia, A.M.D., and T.S.M. the same day, then filed five hundred twenty days late.",
    "c4": "All of it disclosed. All of it legal. Just, in no particular hurry.",
    "c5": "Forty-five days is the rule. Should being late cost something? Tell me below.",
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
    (PUB / f"congress_{key}.mp3").write_bytes(bytes(audio))
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
        print(f"  congress_{key}.mp3  {dur:.2f}s  ({round(dur * 30)}f)  {len(words)} words")
    (PUB / "congress_captions.json").write_text(json.dumps(caps, indent=1), encoding="utf-8")
    print("captions -> public/congress_captions.json")


if __name__ == "__main__":
    asyncio.run(main())
