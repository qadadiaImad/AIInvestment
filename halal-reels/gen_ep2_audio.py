"""Episode 2 audio — non-default NEURAL voice via edge-tts (free, online), applying
the viral-voiceover-audio skill: a consistent recurring anchor voice, NOT a default
top-10 TTS preset. edge-tts also returns word-boundary timings, which we save so
Remotion can render word-by-word karaoke captions (short-form-scripting skill).

Reuses the newsroom bed (public/qr_news_bed.wav). Writes public/ep2_e1..e5.mp3 and
public/ep2_captions.json (per-line word timings + durations).

    python gen_ep2_audio.py
"""
import asyncio
import json
import pathlib

import edge_tts

PUB = pathlib.Path(__file__).resolve().parent / "public"
VOICE = "en-US-EmmaNeural"   # non-default, natural; the anchor character's voice
RATE = "-6%"                  # slightly measured = directed deadpan (not monotone)

# Myth-Bust beats (Intel 2.9x OVER a model, 2026-08-03 data)
LINES = {
    "e1": "Everyone's buying the Intel comeback.",                                  # hook
    "e2": "New CEO, new fabs, the stock's ripping.",                                # setup
    "e3": "But a fundamental model says it's worth about a third of the price.",    # turn
    "e4": "You're not buying a turnaround. You're paying triple for the story.",    # button
    "e5": "Overpriced hope? Or am I wrong.",                                        # cta
}


async def gen(key: str, text: str):
    c = edge_tts.Communicate(text, VOICE, rate=RATE)
    audio = bytearray()
    bounds = []  # (offset_s, end_s) from Sentence/Word boundary events
    async for ch in c.stream():
        if ch["type"] == "audio":
            audio += ch["data"]
        elif ch["type"] in ("WordBoundary", "SentenceBoundary"):
            bounds.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7))
    (PUB / f"ep2_{key}.mp3").write_bytes(bytes(audio))
    # This edge-tts build emits SentenceBoundary only -> distribute word timings
    # across the spoken span proportional to word length (approx karaoke).
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
        print(f"  ep2_{key}.mp3  {dur:.2f}s  ({round(dur * 30)}f)  {len(words)} words")
    (PUB / "ep2_captions.json").write_text(json.dumps(caps, indent=1), encoding="utf-8")
    print("captions -> public/ep2_captions.json")


if __name__ == "__main__":
    asyncio.run(main())
