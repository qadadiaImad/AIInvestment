"""Act two of FairMarketEp1: the turn where Rex is wrong.

WHY A NEW ACT AND NOT MORE LINES. The 36-second cut is one reveal stated
three ways — politics moves the market, here is a filing, it became a
product, it is legal — and then Rex says "so, read the filings!" having
done nothing to earn it. Adding facts to that makes it longer, not
better.

So Rex ACTS on what he has learned and is wrong: he decides to copy the
trades. Sol punctures it with the disclosure delay, Rex over-corrects to
"then they're useless", and Sol reframes what a filing is actually for.
The existing closer then lands on a character who changed his mind
instead of on a slogan.

It also gives the glint-eyed rex_eager drawing an honest job: Rex is
genuinely excited exactly once, on "I'll just copy them", and wears
ordinary eyes (rex_calm) everywhere else — which is the owner's note
about the eyes, solved by the writing rather than by a rule.

Voices: grok-cli TTS, sal = Sol, rex = Rex, matching the ten existing
lines. grok-cli resolves its auth state relative to the CWD, so
--auth-file is passed explicitly.

Run from the repo root:
    python scripts/vector/make_ep1_act2.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
VO = REPO / "remotion" / "public" / "audio" / "fairmarket"
FIX = REPO / "remotion" / "src" / "fixtures" / "cast_ep1"
GROK = Path(os.environ["USERPROFILE"]) / "tools" / "grok-cli" / "grok-cli.exe"
AUTH = Path(os.environ["USERPROFILE"]) / ".grok-cli" / "auth.json"
FPS = 30

# (file stem, voice, line). Slotted between "All legal." and
# "So — read the filings!".
LINES = [
    ("a2_rex_copy", "rex",
     "Then I'll just copy them! Buy what they buy!"),
    ("a2_sol_sixweeks", "sal",
     "Copy them. With a filing from six weeks ago?"),
    ("a2_rex_six", "rex",
     "Six weeks?"),
    ("a2_sol_edge", "sal",
     "The trade is public. The edge is not. By the time you read it, the move already happened."),
    ("a2_rex_useless", "rex",
     "So the filings are useless."),
    ("a2_sol_map", "sal",
     "No. They're a map of attention. Who is watching what, and when."),
]


def synth(stem: str, voice: str, text: str) -> Path:
    out = VO / f"{stem}.wav"
    cmd = [str(GROK), "tts", "--auth-file", str(AUTH), "--voice-id", voice,
           "--output", str(out), "--output-format", "wav", text]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        sys.exit(f"tts failed for {stem}: {r.stdout}\n{r.stderr}")
    return out


def amplitude_track(path: Path) -> list[int]:
    """Per-frame mouth state 0/1/2 from the speech envelope.

    Same shape as the existing mouth_tracks entries: silence closes the
    mouth, quiet speech half-opens it, loud speech opens it. Thresholds
    are relative to the line's own loud level so a quiet line still
    articulates instead of sitting shut.
    """
    with wave.open(str(path)) as w:
        sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float) / 32768
    if ch == 2:
        x = x.reshape(-1, 2).mean(axis=1)
    step = max(1, sr // FPS)
    frames = [x[i:i + step] for i in range(0, len(x), step)]
    rms = np.array([float(np.sqrt((f ** 2).mean())) if len(f) else 0.0
                    for f in frames])
    ref = float(np.percentile(rms, 92)) or 1.0
    out = []
    for v in rms:
        r = v / ref
        out.append(0 if r < 0.16 else (1 if r < 0.5 else 2))
    return out


def main() -> None:
    tracks = json.loads((FIX / "mouth_tracks.json").read_text("utf-8"))
    total = 0.0
    report = []
    for stem, voice, text in LINES:
        p = synth(stem, voice, text)
        with wave.open(str(p)) as w:
            dur = w.getnframes() / w.getframerate()
        tracks[stem] = amplitude_track(p)
        total += dur
        report.append((stem, voice, dur, len(tracks[stem]), text))
        print(f"{stem:18s} {voice:4s} {dur:5.2f}s  "
              f"{len(tracks[stem])} track frames")
    (FIX / "mouth_tracks.json").write_text(json.dumps(tracks), "utf-8")
    print(f"\nnew dialogue {total:.1f}s across {len(LINES)} lines")
    print(f"episode 36.2s + {total:.1f}s speech + beat gaps "
          f"-> target ~60s")
    print(f"mouth_tracks.json now has {len(tracks)} entries")


if __name__ == "__main__":
    main()
