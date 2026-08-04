"""New dialogue for the 60-second cut of FairMarketEp1.

grok-cli's TTS needs an interactive browser OAuth and its auth state is
absent on this machine, so the voices are cloned locally instead:
Chatterbox zero-shot, conditioned on the EXISTING Sol and Rex lines. That
keeps both voices continuous with the 36-second cut rather than
introducing a second-sounding narrator halfway through.

Every added claim is a matter of public record and stays inside the
episode's rails — no advice, no accusation, no returns claim:
  * the STOCK Act requires disclosure of covered trades, with a
    reporting deadline measured in weeks, not days
  * a second ETF tracks Republican lawmakers' disclosed trades, so the
    "it became a product" point is not one-sided
  * the closing line is about reading the reasoning, not copying a trade

Run with the chatterbox venv:
  C:/Users/imadq/tools/chatterbox-venv/Scripts/python.exe \
      scripts/vector/make_ep1_vo_ext.py
"""
import os
import sys

import torch
import torchaudio

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
VO = os.path.join(REPO, "remotion", "public", "audio", "fairmarket")

# Reference clips: the longest clean line each character already has, so
# the clone hears plenty of their timbre and cadence.
REF = {
    "sol": os.path.join(VO, "v6_sol_exhibit.wav"),
    "rex": os.path.join(VO, "v7_rex_index.wav"),
}

LINES = [
    ("v11_sol_bothsides", "sol",
     "And it is not one party, kid. There is a fund that copies the other side too."),
    ("v12_rex_both", "rex",
     "Both teams have an index?!"),
    ("v13_sol_public", "sol",
     "All of it public. The law says they have to disclose."),
    ("v14_rex_late", "rex",
     "But weeks late..."),
    ("v15_sol_late", "sol",
     "Weeks late. By then the trade is old news."),
]


def main():
    from chatterbox.tts import ChatterboxTTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"loading chatterbox on {device}")
    model = ChatterboxTTS.from_pretrained(device=device)
    for name, who, text in LINES:
        ref = REF[who]
        if not os.path.exists(ref):
            sys.exit(f"missing reference audio: {ref}")
        wav = model.generate(text, audio_prompt_path=ref)
        out = os.path.join(VO, f"{name}.wav")
        torchaudio.save(out, wav, model.sr)
        dur = wav.shape[-1] / model.sr
        print(f"{name:22s} {who}  {dur:5.2f}s  {text}")
    print(f"\n{len(LINES)} lines -> {VO}")


if __name__ == "__main__":
    main()
