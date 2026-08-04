"""New dialogue for the TWO-MINUTE cut of FairMarketEp1.

WHY THESE LINES EXIST. In the 60s cut Rex blurted "They made it an
INDEX?!" out of nowhere — he announced a fact he had no way of knowing,
which is narration captioning itself. These lines are the ramp that makes
that reaction EARNED: Sol goes one filing -> people track these
portfolios like a leaderboard -> here are the ones they watch -> somebody
wrapped it in a fund. Only then does Rex react.

ACCURACY RAIL. Periodic-transaction reporting under the STOCK Act is a
CONGRESSIONAL mechanism. A president is not a member of Congress, so
whenever the second caricature is on screen the wording is "politicians
whose trades people track", never "congress investors". Nothing here
asserts a return, an accusation, or a recommendation; the beating-the-
market line is explicitly attributed to trackers and hedged to "some
years", which is how it is actually reported.

Voices are cloned locally with Chatterbox zero-shot, conditioned on the
existing Sol and Rex lines, so the new dialogue is continuous with the
lines already in the cut rather than introducing a second narrator
halfway through.

Run with the chatterbox venv:
  C:/Users/imadq/tools/chatterbox-venv/Scripts/python.exe \
      scripts/vector/make_ep1_vo_2min.py
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
    # --- ACT 3: the leaderboard (the ramp to "INDEX?!") ---
    ("a3_rex_onetrade", "rex",
     "Okay... but that is one trade. One person."),
    ("a3_sol_leaderboard", "sol",
     "One? People track these disclosures like a leaderboard."),
    ("a3_sol_portfolios", "sol",
     "Whole portfolios. Filing by filing. Year by year."),
    ("a3_sol_speaker", "sol",
     "The Speaker's household. Technology, mostly. Big positions, disclosed late."),
    ("a3_sol_others", "sol",
     "And it is not one person, or one party. Other politicians get tracked exactly the same way."),
    ("a3_rex_score", "rex",
     "People are keeping SCORE?"),
    ("a3_sol_beating", "sol",
     "Some years, the trackers reported those portfolios beating the market. That is why people watch."),
    ("a3_sol_obvious", "sol",
     "And then somebody did the obvious thing."),
    # --- ACT 5: the payoff ---
    ("a5_rex_dowhat", "rex",
     "So what do I actually do with it?"),
    ("a5_sol_homework", "sol",
     "Watch what they sit near. Committees. Hearings. Then do your own homework."),
    ("a5_sol_fair", "sol",
     "Fair? No. But now you can read it."),
]


def main():
    from chatterbox.tts import ChatterboxTTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"loading chatterbox on {device}")
    model = ChatterboxTTS.from_pretrained(device=device)
    total = 0.0
    for name, who, text in LINES:
        ref = REF[who]
        if not os.path.exists(ref):
            sys.exit(f"missing reference audio: {ref}")
        wav = model.generate(text, audio_prompt_path=ref)
        out = os.path.join(VO, f"{name}.wav")
        torchaudio.save(out, wav, model.sr)
        dur = wav.shape[-1] / model.sr
        total += dur
        print(f"{name:22s} {who}  {dur:5.2f}s  {text}", flush=True)
    print(f"\n{len(LINES)} lines, {total:.1f}s of new dialogue -> {VO}")


if __name__ == "__main__":
    main()
