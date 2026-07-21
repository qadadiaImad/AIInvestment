"""Beat-level Karim VO — same canon as karim_tts.py (sample, seed 7, calm-educator
params), for PER-BEAT bubble clips where the reel-level rails live in the closing
beat + the on-screen disclaimer footer. Deliberately skips lint_concept_script
(that gate is for complete standalone scripts); the reel assembly is responsible
for ending on the spoken disclaimer beat.

    <chatterbox-venv-python> scripts/voice/karim_tts_beats.py NAME1 PATH1 [NAME2 PATH2 ...] --out higgs
"""
from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from voice.karim_tts import SAMPLE, SEED, chunks, PAUSE_S  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs", nargs="+", help="NAME PATH pairs")
    ap.add_argument("--out", default="higgs")
    ap.add_argument("--exaggeration", type=float, default=0.4)
    ap.add_argument("--cfg-weight", type=float, default=0.5)
    args = ap.parse_args()
    if len(args.pairs) % 2:
        raise SystemExit("pairs must be NAME PATH ...")

    import torch
    import torchaudio

    torch.manual_seed(SEED)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from chatterbox.tts import ChatterboxTTS

    model = ChatterboxTTS.from_pretrained(device=device)
    sr = model.sr
    pause = torch.zeros(1, int(PAUSE_S * sr))
    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i in range(0, len(args.pairs), 2):
        name, path = args.pairs[i], args.pairs[i + 1]
        script = pathlib.Path(path).read_text(encoding="utf-8").strip()
        waves = []
        for j, part in enumerate(chunks(script)):
            torch.manual_seed(SEED + j)
            wav = model.generate(part, audio_prompt_path=str(SAMPLE),
                                 exaggeration=args.exaggeration,
                                 cfg_weight=args.cfg_weight)
            waves.extend([wav, pause])
        full = torch.cat(waves[:-1], dim=1)
        out = out_dir / f"voice_{name}.wav"
        torchaudio.save(str(out), full, sr)
        print(f"OK {out}  {full.shape[1] / sr:.1f}s")


if __name__ == "__main__":
    main()
