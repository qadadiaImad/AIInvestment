"""VO for the debt/bonds explainer using Chatterbox (Resemble AI, MIT) — an expressive,
natural TTS that doesn't sound like flat parametric "AI slop". Runs from an isolated package
dir (C:/Users/Amsegt/chatterbox_env) so ComfyUI's env is untouched. CPU by default.

Writes public/debt_*.wav + debt_captions.json (word timings estimated proportionally, since
Chatterbox doesn't emit word boundaries).

Run with the ComfyUI embedded python (has a compatible interpreter):
  /c/Users/Amsegt/comfy/ComfyUI_windows_portable/python_embeded/python.exe gen_debt_chatterbox.py
"""
import json
import os
import pathlib
import sys

# We run under ComfyUI's embedded python (compatible interpreter) but must NOT use its
# site-packages (torch 2.13/cu130 + torchvision) — they clash with our isolated CPU torch.
# Drop every site-packages entry, keep stdlib, then prepend the isolated Chatterbox env.
TARGET = r"C:\Users\Amsegt\chatterbox_env"
sys.path = [p for p in sys.path if "site-packages" not in p.replace("\\", "/").lower()]
sys.path.insert(0, TARGET)

import torch  # noqa: E402  (resolved from the isolated env)
import torchaudio as ta  # noqa: E402
from chatterbox.tts import ChatterboxTTS  # noqa: E402

PUB = pathlib.Path(__file__).resolve().parent / "public"
DEVICE = "cuda" if torch.cuda.is_available() and os.environ.get("CB_CPU") != "1" else "cpu"
# expressive but composed: some emotion, natural (not rushed) pacing
EXAG, CFG = 0.6, 0.5

LINES = {
    "d1": "The entire world is in debt. Not one country. Not one company. The whole planet. Three hundred and forty-eight trillion dollars. Which raises a strange little question… in debt to whom?",
    "d2": "Because this isn't one giant loan. It's all of us. Households owe sixty-four trillion. Companies, a hundred. Governments, another hundred and seven. Stack it all up, and you get three hundred and forty-eight.",
    "d3": "But here's the strange thing about debt. Every dollar owed is a dollar someone else is owed. So if the entire planet is in the red… who on Earth is in the black?",
    "d4": "The answer hides inside a single piece of paper. A bond. A government needs money today, so it writes a promise. Lend me a hundred, and I'll pay you back, with interest, later. Print millions of those promises, and that pile of paper becomes the national debt.",
    "d5": "So who holds all these promises? Some are foreign. Japan, Britain, China, together about a third. But the biggest lender of all… is you. Your pension. Your bank. Your savings. The world doesn't owe some distant stranger. Mostly, it owes itself.",
    "d6": "And yet, there's a catch. Last year, the interest alone on America's debt hit nine hundred and seventy billion dollars. More than it spends on its entire military. That isn't shrinking the debt. That's just… renting it.",
    "d7": "A planet that owes itself trillions, and borrows just to pay the interest. Brilliant design? Or a slow motion time bomb? Tell me what you think, below.",
}


def word_times(text, dur):
    toks = text.split()
    wts = [len(w) + 1 for w in toks]
    total = sum(wts) or 1
    start, end = 0.06, max(0.2, dur - 0.06)
    t, out = start, []
    for w, wt in zip(toks, wts):
        seg = (end - start) * wt / total
        out.append({"w": w, "t0": round(t, 3), "t1": round(t + seg, 3)})
        t += seg
    return out


def main():
    PUB.mkdir(parents=True, exist_ok=True)
    print(f"loading Chatterbox on {DEVICE} …")
    model = ChatterboxTTS.from_pretrained(device=DEVICE)
    sr = model.sr
    caps = {}
    for lid, text in LINES.items():
        wav = model.generate(text, exaggeration=EXAG, cfg_weight=CFG)
        ta.save(str(PUB / f"debt_{lid}.wav"), wav, sr)
        dur = wav.shape[-1] / sr
        caps[lid] = {"text": text, "words": word_times(text, dur), "dur": round(dur + 0.1, 3), "frames": round(dur * 30)}
        print(f"  debt_{lid}.wav  {dur:.2f}s ({round(dur*30)}f)")
    (PUB / "debt_captions.json").write_text(json.dumps(caps, indent=1), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
