"""VO for the debt/bonds explainer using Chatterbox (Resemble AI, MIT) — expressive, natural TTS.

Per-SENTENCE generation: each sentence in a line is synthesized separately with its own
inflection (questions rise, number/reveal beats punch, trailing "…" thoughts soften), then
stitched with natural pauses. This gives each phrase its own contour — the way a person varies
their voice while explaining — instead of one flat tone across the whole line. It also yields
accurate per-sentence word timing for the karaoke captions.

Runs from an isolated package dir so ComfyUI's env is untouched. CPU by default.
Writes public/debt_*.wav + debt_captions.json.

  /c/Users/Amsegt/comfy/ComfyUI_windows_portable/python_embeded/python.exe gen_debt_chatterbox.py
"""
import json
import os
import pathlib
import re
import sys

# run under ComfyUI's embedded python but NOT its site-packages (torch 2.13/cu130 + torchvision
# clash with our isolated CPU torch). Drop site-packages, keep stdlib, prepend the isolated env.
TARGET = r"C:\Users\Amsegt\chatterbox_env"
sys.path = [p for p in sys.path if "site-packages" not in p.replace("\\", "/").lower()]
sys.path.insert(0, TARGET)

import torch  # noqa: E402
import torchaudio as ta  # noqa: E402
from chatterbox.tts import ChatterboxTTS  # noqa: E402

PUB = pathlib.Path(__file__).resolve().parent / "public"
DEVICE = "cuda" if torch.cuda.is_available() and os.environ.get("CB_CPU") != "1" else "cpu"

LINES = {
    "d1": "The entire world is in debt. Not one country. Not one company. The whole planet. Three hundred and forty-eight trillion dollars. Which raises a strange little question… in debt to whom?",
    "d2": "Because this isn't one giant loan. It's all of us. Households owe sixty-four trillion. Companies, a hundred. Governments, another hundred and seven. Stack it all up, and you get three hundred and forty-eight.",
    "d3": "But here's the strange thing about debt. Every dollar owed is a dollar someone else is owed. So if the entire planet is in the red… who on Earth is in the black?",
    "d4": "The answer hides inside a single piece of paper. A bond. A government needs money today, so it writes a promise. Lend me a hundred, and I'll pay you back, with interest, later. Print millions of those promises, and that pile of paper becomes the national debt.",
    "d5": "So who holds all these promises? Some are foreign. Japan, Britain, China, together about a third. But the biggest lender of all… is you. Your pension. Your bank. Your savings. The world doesn't owe some distant stranger. Mostly, it owes itself.",
    "d6": "And yet, there's a catch. Last year, the interest alone on America's debt hit nine hundred and seventy billion dollars. More than it spends on its entire military. That isn't shrinking the debt. That's just… renting it.",
    "d7": "A planet that owes itself trillions, and borrows just to pay the interest. Brilliant design? Or a slow motion time bomb? Tell me what you think, below.",
}


def sentences(text):
    # Split ONLY on true sentence enders (. ? !) — never on "…" or "," which are
    # intra-sentence pauses. Keeps a clause like "That's just… renting it." whole so it
    # renders as one continuous, human line instead of two disconnected fragments.
    return [s.strip() for s in re.findall(r"[^.?!]+[.?!]+|[^.?!]+$", text) if s.strip()]


def tts_norm(s):
    # Chatterbox reads a comma as a smooth in-clause pause; the unicode "…" tends to be
    # mishandled or over-clipped. Swap it for a comma for synthesis (captions keep the "…").
    s = s.replace("…", ", ")
    s = re.sub(r"\s*,\s*,", ", ", s)   # collapse doubled commas
    return re.sub(r"\s+", " ", s).strip().strip(",").strip()


def level(wav, peak=0.92):
    # even out per-sentence loudness so stitched clips don't jump in volume
    m = wav.abs().max()
    return wav * (peak / m) if m > 0 else wav


def fade(wav, sr, ms=8):
    # tiny in/out ramps so joins don't click
    k = int(sr * ms / 1000)
    if k > 0 and wav.shape[-1] > 2 * k:
        ramp = torch.linspace(0, 1, k)
        wav[..., :k] = wav[..., :k] * ramp
        wav[..., -k:] = wav[..., -k:] * ramp.flip(0)
    return wav


def style(sentence, i):
    """Per-sentence inflection: (exaggeration, cfg_weight, pause_after_seconds)."""
    end = sentence.strip()[-1:] if sentence.strip() else "."
    wig = ((i * 37) % 7 - 3) * 0.02  # deterministic ±0.06 so no two neighbours match
    if end == "?":
        return min(0.8, 0.70 + wig), 0.40, 0.30            # questions rise, more expressive
    if re.search(r"\d|trillion|billion|hundred|seventy", sentence):
        return min(0.8, 0.64 + wig), 0.45, 0.26            # numbers get a punch
    return max(0.42, 0.52 + wig), 0.50, 0.24               # calm default, varied


def word_times(text, t0, t1):
    toks = text.split()
    wts = [len(w) + 1 for w in toks]
    total = sum(wts) or 1
    t, out = t0, []
    for w, wt in zip(toks, wts):
        seg = (t1 - t0) * wt / total
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
        chunks, words, cur = [], [], 0.0
        sents = sentences(text)
        for i, s in enumerate(sents):
            exag, cfg, pause = style(s, i)
            wav = model.generate(tts_norm(s), exaggeration=exag, cfg_weight=cfg)
            wav = fade(level(wav), sr)
            d = wav.shape[-1] / sr
            words += word_times(s, cur + 0.03, cur + d - 0.03)
            chunks.append(wav)
            cur += d
            if i < len(sents) - 1:
                chunks.append(torch.zeros(1, int(sr * pause)))
                cur += pause
        full = torch.cat(chunks, dim=1)
        ta.save(str(PUB / f"debt_{lid}.wav"), full, sr)
        dur = full.shape[-1] / sr
        caps[lid] = {"text": text, "words": words, "dur": round(dur + 0.1, 3), "frames": round(dur * 30)}
        print(f"  debt_{lid}.wav  {dur:.2f}s ({round(dur*30)}f, {len(sents)} phrases)")
    (PUB / "debt_captions.json").write_text(json.dumps(caps, indent=1), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
