"""Word-level timestamps for a rendered VO WAV, via faster-whisper.

    <chatterbox-venv-python> scripts/voice/whisper_align.py <wav> --out words.json

Runs faster-whisper's `small.en` model with `compute_type="int8"` and
`word_timestamps=True`, then dumps a flat JSON array of
`[{"word": str, "start": float, "end": float}, ...]` (seconds) — exactly the
shape `aiinvest.align_beats.apply_timing` consumes to derive per-beat
`durationInFrames` and caption spans from the actual rendered narration.

Run this with the **chatterbox venv** python (it has `faster-whisper`
installed alongside torch/chatterbox-tts for `karim_tts.py`), NOT the main
repo venv:

    C:/Users/Amsegt/.venvs/chatterbox/Scripts/python.exe scripts/voice/whisper_align.py <wav> --out words.json

`faster_whisper` is imported lazily inside `main()` (not at module scope) so
this module stays importable — e.g. from `daily_post.py` for its docstring/
CLI wiring, or from tests — without the dependency installed in whichever
venv is doing the importing.

Educational/research only — not financial advice.
"""
from __future__ import annotations

import argparse
import json
import pathlib

MODEL_SIZE = "small.en"
COMPUTE_TYPE = "int8"


def transcribe_words(wav_path: str, model_size: str = MODEL_SIZE) -> list[dict]:
    """Run faster-whisper on `wav_path`, return a flat word-timestamp list.
    Imports faster_whisper lazily — see module docstring."""
    from faster_whisper import WhisperModel  # noqa: E402  (lazy, by design)

    model = WhisperModel(model_size, compute_type=COMPUTE_TYPE)
    segments, _info = model.transcribe(wav_path, word_timestamps=True)

    words: list[dict] = []
    for segment in segments:
        for w in (segment.words or []):
            words.append({"word": w.word, "start": w.start, "end": w.end})
    return words


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("wav", help="path to the rendered VO .wav")
    ap.add_argument("--out", required=True, help="path to write the words JSON")
    ap.add_argument("--model", default=MODEL_SIZE, help=f"faster-whisper model size (default {MODEL_SIZE})")
    args = ap.parse_args(argv)

    words = transcribe_words(args.wav, model_size=args.model)

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(words, indent=2), encoding="utf-8")
    print(f"OK {out_path}  {len(words)} word(s)")


if __name__ == "__main__":
    main()
