"""Do Chatterbox's emotion/action tags actually render? Tested, not assumed.

THE FIND. Chatterbox 0.1.7's tokenizer carries 49 bracket tokens, and this
project has never used one. The ones that matter for a two-hander at a news
desk:

    [sigh] [gasp] [laughter] [giggle] [guffaw] [groan] [cry]
    [inhale] [exhale] [clear_throat] [whisper] [mumble] [UH] [UM]
    [sniff] [cough] [shhh] [kiss] [humming] [whistle] [singing]

Every VO line in all five episodes was generated as flat text with default
delivery, so none of this was ever reachable.

BUT A TOKEN IN A VOCAB IS NOT A RENDERED SOUND. The tokenizer will happily
encode anything in its vocab; whether the acoustic model produces an actual
sigh is a separate question, and the honest way to answer it is to generate
each line twice - once with the tag, once without, same seed, same settings
- and compare. If the tag does nothing, the two files are near-identical in
length and content.

  python scripts/vector/vo_tag_probe.py
Writes  content/probe/vo_tags/  plus a labelled A/B reel.
"""
from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "content/probe/vo_tags"
REFS = REPO / "remotion/public/audio/voice_refs"
SEED = 20260804

# Calmed delivery, from rex_voice_probe: the tags are being judged on top of
# the settings we would actually ship, not on the shouty defaults.
CALM = dict(exaggeration=0.35, cfg_weight=0.4, temperature=0.7)

# (id, voice, text WITH tag, the same text WITHOUT it)
TESTS = [
    ("sigh_sol", "sol", "[sigh] Read it to me.", "Read it to me."),
    ("laugh_sol", "sol", "[laughter] Fundamentals.", "Fundamentals."),
    ("gasp_rex", "rex", "[gasp] They made it an INDEX?!",
     "They made it an INDEX?!"),
    ("um_rex", "rex", "[UM] So they caught them.", "So they caught them."),
    ("throat_sol", "sol", "[clear_throat] Now. Here is the part people skip.",
     "Now. Here is the part people skip."),
    ("whisper_sol", "sol", "[whisper] Nobody had announced it yet.",
     "Nobody had announced it yet."),
]


def pcm16(path: Path):
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        if w.getnchannels() == 2:
            a = a.reshape(-1, 2).mean(axis=1).astype(np.int16)
    return a, sr


def main() -> None:
    import torch
    import torchaudio
    from chatterbox.tts import ChatterboxTTS

    OUT.mkdir(parents=True, exist_ok=True)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print("loading chatterbox on " + dev)
    model = ChatterboxTTS.from_pretrained(device=dev)

    rows = []
    for tid, voice, tagged, plain in TESTS:
        for kind, text in (("with", tagged), ("without", plain)):
            torch.manual_seed(SEED)
            if dev == "cuda":
                torch.cuda.manual_seed_all(SEED)
            np.random.seed(SEED)
            wav = model.generate(
                text, audio_prompt_path=str(REFS / f"voice_ref_{voice}.wav"),
                **CALM)
            p = OUT / f"{tid}__{kind}.wav"
            torchaudio.save(str(p), wav.cpu(), model.sr,
                            encoding="PCM_S", bits_per_sample=16)
            a, sr = pcm16(p)
            rows.append({"id": tid, "voice": voice, "kind": kind,
                         "text": text, "seconds": round(len(a) / sr, 2)})
        w_, wo = rows[-2]["seconds"], rows[-1]["seconds"]
        # if the tag renders, the tagged take carries extra audio
        print(f"  {tid:12s} with {w_:4.1f}s   without {wo:4.1f}s   "
              f"delta {w_ - wo:+5.1f}s   "
              f"{'RENDERS' if abs(w_ - wo) > 0.25 else 'no audible change'}",
              flush=True)

    (OUT / "probe.json").write_text(json.dumps(rows, indent=1), "utf-8")

    reel, sr0 = [], None
    for tid, _, _, _ in TESTS:
        for kind in ("with", "without"):
            a, sr = pcm16(OUT / f"{tid}__{kind}.wav")
            sr0 = sr0 or sr
            reel.append(a)
            reel.append(np.zeros(int(sr * 0.4), dtype=np.int16))
        reel.append(np.zeros(int(sr0 * 0.9), dtype=np.int16))
    out = np.concatenate(reel).astype(np.int16)
    with wave.open(str(OUT / "ab_reel.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr0)
        w.writeframes(out.tobytes())
    print("-> " + str(OUT / "ab_reel.wav"))


if __name__ == "__main__":
    main()
