"""VO for the 3 non-valuation episodes (edge-tts neural, per-episode voice) + karaoke
word timings. Writes public/{loop,tier,casc}_*.mp3 + *_captions.json.

    python gen_reels3_audio.py
"""
import asyncio
import json
import pathlib

import edge_tts

PUB = pathlib.Path(__file__).resolve().parent / "public"

EPISODES = {
    "loop": ("en-US-BrianNeural", "+6%", {
        "l1": "Microsoft puts money into OpenAI. OpenAI spends it on Microsoft's cloud.",
        "l2": "Nvidia puts money into OpenAI. OpenAI spends it on Nvidia's chips.",
        "l3": "The same dollars go out, and come right back. Nobody's lying. It's just a circle.",
        "l4": "It works great, until someone asks whose money it actually was.",
        "l5": "Genius, or a bubble writing its own paycheck? Tell me below.",
    }),
    "tier": ("en-US-ChristopherNeural", "+10%", {
        "t1": "Five layers hold up the entire A.I. trade. Let's rank them by who breaks first.",
        "t2": "Weakest: the apps. Then the power grid. Then the chips.",
        "t3": "Here's the twist. The infrastructure giants rank the healthiest. Not the chip makers.",
        "t4": "Even though one chip company is the single biggest point of failure on the whole map.",
        "t5": "Which layer cracks first? Fight me below.",
    }),
    "casc": ("en-US-EmmaNeural", "-4%", {
        "x1": "Four companies are basically the entire demand side of the A.I. boom.",
        "x2": "Microsoft, Amazon, Google, Meta. If they blink, everyone downstream feels it.",
        "x3": "Model a ten percent budget cut, and it ripples out to sixty-six names. Half the whole A.I. stack.",
        "x4": "That's not a prediction. It's just what downstream means when four buyers are the market.",
        "x5": "Are we four earnings calls away from a cascade? Tell me below.",
    }),
}


async def gen(voice, rate, key, text):
    c = edge_tts.Communicate(text, voice, rate=rate)
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
    for ep, (voice, rate, lines) in EPISODES.items():
        caps = {}
        for lid, text in lines.items():
            words, dur = await gen(voice, rate, f"{ep}_{lid}", text)
            caps[lid] = {"text": text, "words": words, "dur": dur, "frames": round(dur * 30)}
            print(f"  {ep}_{lid}.mp3  {dur:.2f}s ({round(dur*30)}f)")
        (PUB / f"{ep}_captions.json").write_text(json.dumps(caps, indent=1), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    asyncio.run(main())
