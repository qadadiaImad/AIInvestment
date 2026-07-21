"""Karim VO via local Chatterbox (MIT) — clones the canonical voice from
course/persona/voice/karim_sample.wav. Free, offline, reproducible (fixed seed).

    <venv-python> scripts/voice/karim_tts.py --date 2026-07-21 --out halal-reels/public

Reads halal_script entries from higgs/reels_<date>_kit.md, runs the SAME lint gate as
the Higgsfield path (aiinvest.halal_lint), chunks long scripts at sentence boundaries
(Chatterbox is happiest under ~250 chars per generation), and concatenates chunks with
short pauses. Writes voice_<tk>.wav (24kHz mono) into --out.

Run inside the chatterbox venv (torch + chatterbox-tts installed), NOT the repo python.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "higgs"))

from aiinvest.halal_join import load_halal, screen_card_data  # noqa: E402
from aiinvest.halal_lint import lint_halal_script  # noqa: E402
from _gen_halal_voice import collect_halal_entries  # noqa: E402

SAMPLE = ROOT / "course/persona/voice/karim_sample.wav"
SEED = 7
PAUSE_S = 0.35
MAX_CHUNK = 240


def chunks(script: str) -> list[str]:
    """Sentence-boundary chunks of <= MAX_CHUNK chars (Chatterbox sweet spot)."""
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script.replace("\n", " ")) if s.strip()]
    out: list[str] = []
    cur = ""
    for s in sents:
        if cur and len(cur) + len(s) + 1 > MAX_CHUNK:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--out", default=str(ROOT / "halal-reels/public"))
    ap.add_argument("--tickers", nargs="*", help="subset filter, e.g. WULF GEV")
    ap.add_argument("--exaggeration", type=float, default=0.4, help="calm educator < default 0.5")
    ap.add_argument("--cfg-weight", type=float, default=0.5)
    args = ap.parse_args(argv)

    kit = ROOT / f"higgs/reels_{args.date}_kit.md"
    if not kit.exists():
        raise SystemExit(f"kit not found: {kit}")
    if not SAMPLE.exists():
        raise SystemExit(f"canonical sample missing: {SAMPLE}")

    verdicts, warns = load_halal(ROOT / "web/public/data/halal.json")
    for w in warns:
        print("WARN", w)

    entries = collect_halal_entries(kit.read_text(encoding="utf-8"))
    if args.tickers:
        keep = {t.upper() for t in args.tickers}
        entries = [(tk, s) for tk, s in entries if tk in keep]
    if not entries:
        raise SystemExit("no halal_script entries matched")

    # Lint gate BEFORE loading the model — no wasted minutes on a bad script.
    failed = False
    for tk, script in entries:
        card = screen_card_data(verdicts, tk)
        if card is None:
            print(f"SKIP {tk}: not in halal.json")
            continue
        for e in lint_halal_script(script, card):
            failed = True
            print(f"LINT {tk}: {e}")
    if failed:
        raise SystemExit("lint failed — fix the kit scripts first")

    import torch
    import torchaudio

    torch.manual_seed(SEED)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"loading Chatterbox on {device} (first run downloads the model)...")
    from chatterbox.tts import ChatterboxTTS

    model = ChatterboxTTS.from_pretrained(device=device)
    sr = model.sr
    pause = torch.zeros(1, int(PAUSE_S * sr))

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for tk, script in entries:
        if screen_card_data(verdicts, tk) is None:
            continue
        parts = chunks(script)
        print(f"{tk}: {len(parts)} chunk(s), {len(script)} chars")
        waves = []
        for i, part in enumerate(parts):
            torch.manual_seed(SEED + i)  # stable per chunk
            wav = model.generate(
                part,
                audio_prompt_path=str(SAMPLE),
                exaggeration=args.exaggeration,
                cfg_weight=args.cfg_weight,
            )
            waves.append(wav.cpu() if hasattr(wav, "cpu") else wav)
            waves.append(pause)
        audio = torch.cat(waves[:-1], dim=-1)  # drop trailing pause
        dest = out_dir / f"voice_{tk.lower()}.wav"
        torchaudio.save(str(dest), audio, sr)
        print(f"OK {dest}  {audio.shape[-1] / sr:.1f}s")
    print("done")


if __name__ == "__main__":
    main()
