"""Regenerate every Chatterbox-cloned line on grok TTS, and punch up Rex.

WHY. Rex's voice "starts fine but then deviates" — because it is two
different engines playing one character. His opening lines (v2, v5, v7,
v9) and all of act four came from grok-cli TTS; the act-three lines added
for the two-minute cut were Chatterbox zero-shot clones, made when grok
auth was unavailable on this machine. Zero-shot cloning also drifts
WITHIN a line, which is the wobble in the middle of a sentence.

grok auth is present now (~/.grok-cli/auth.json), so every cloned line is
regenerated on the same two voices as the originals: sal = Sol, rex =
Rex. One engine, one voice per character, start to finish.

SECOND JOB: Rex's writing. He was the straight man asking flat setup
questions. He is the over-eager junior — the comedy is that he
over-commits, jumps to the wrong conclusion, and gets deflated. Each of
his lines now also PICKS UP Sol's last idea instead of starting cold,
which is what "fluidity" means here.

grok-cli resolves auth relative to the CWD, so --auth-file is explicit.

Run from the repo root:
    python scripts/vector/make_ep1_vo_grok.py
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
GROK = Path(os.path.expanduser("~/tools/grok-cli/grok-cli.exe"))
AUTH = Path(os.path.expanduser("~/.grok-cli/auth.json"))
FFMPEG = (REPO / "remotion" / "node_modules" / "@remotion"
          / "compositor-win32-x64-msvc" / "ffmpeg.exe")
FPS = 30

# (stem, voice, text).  REWRITTEN lines are marked in the comment.
LINES = [
    # ---- ACT 3: the leaderboard -------------------------------------
    # REWRITTEN. Was "Okay... but that is one trade. One person." — a flat
    # concession. Now he pushes back with a joke, which gives Sol
    # something to demolish.
    ("a3_rex_onetrade", "rex",
     "One trade. One person. That's a coincidence, boss, not a strategy."),
    ("a3_sol_leaderboard", "sal",
     "One? People track these disclosures like a leaderboard."),
    ("a3_sol_portfolios", "sal",
     "Whole portfolios. Filing by filing. Year by year."),
    ("a3_sol_speaker", "sal",
     "The Speaker's household. Technology, mostly. Big positions, disclosed late."),
    ("a3_sol_others", "sal",
     "And it's not one person, or one party. Other politicians get tracked exactly the same way."),
    # REWRITTEN. Was "People are keeping SCORE?" Picks up "leaderboard"
    # and lands the joke on how absurdly normal this has become.
    ("a3_rex_score", "rex",
     "Somebody's keeping score? Like a fantasy league?"),
    ("a3_sol_beating", "sal",
     "Some years, the trackers reported those portfolios beating the market. That's why people watch."),
    ("a3_sol_obvious", "sal",
     "And then somebody did the obvious thing."),
    ("v11_sol_bothsides", "sal",
     "And it's not one party, kid. There's a fund that copies the other side too."),
    # REWRITTEN. Was "Both teams have an index?!" — now he misses the
    # point in character, which is funnier and sets up Sol's correction.
    ("v12_rex_both", "rex",
     "Both sides have one? Okay — who's winning?"),
    # ---- ACT 5: the payoff ------------------------------------------
    # REWRITTEN. Was "So what do I actually do with it?" The tag makes it
    # Rex admitting it is entirely for himself.
    ("a5_rex_dowhat", "rex",
     "So what do I actually do with it? Asking for me."),
    ("a5_sol_homework", "sal",
     "Watch what they sit near. Committees. Hearings. Then do your own homework."),
    ("a5_sol_fair", "sal",
     "Fair? No. But now you can read it."),
]


def synth(stem: str, voice: str, text: str) -> Path:
    raw = VO / f"_{stem}_grok.wav"
    r = subprocess.run(
        [str(GROK), "tts", "--auth-file", str(AUTH), "--voice-id", voice,
         "--output", str(raw), "--output-format", "wav", text],
        capture_output=True, text=True)
    if r.returncode != 0 or not raw.exists():
        sys.exit(f"tts failed for {stem}: {r.stdout}\n{r.stderr}")
    # grok writes a placeholder header that reports 44,739 seconds; decode
    # to real PCM so every downstream duration read is honest.
    out = VO / f"{stem}.wav"
    subprocess.run([str(FFMPEG), "-v", "error", "-i", str(raw),
                    "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1",
                    str(out), "-y"], check=True)
    raw.unlink(missing_ok=True)
    return out


def amplitude_track(path: Path) -> list[int]:
    with wave.open(str(path)) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float) / 32768
    step = max(1, sr // FPS)
    rms = np.array([float(np.sqrt((x[i:i + step] ** 2).mean()))
                    for i in range(0, len(x), step) if len(x[i:i + step])])
    ref = float(np.percentile(rms, 92)) or 1.0
    return [0 if v / ref < 0.16 else (1 if v / ref < 0.5 else 2) for v in rms]


def main() -> None:
    tracks = json.loads((FIX / "mouth_tracks.json").read_text("utf-8"))
    total = 0.0
    for stem, voice, text in LINES:
        p = synth(stem, voice, text)
        with wave.open(str(p)) as w:
            dur = w.getnframes() / w.getframerate()
        tracks[stem] = amplitude_track(p)
        total += dur
        print(f"{stem:22s} {voice:4s} {dur:5.2f}s {int(round(dur*FPS)):4d}f  {text}",
              flush=True)
    (FIX / "mouth_tracks.json").write_text(json.dumps(tracks), "utf-8")
    print(f"\n{len(LINES)} lines regenerated on grok, {total:.1f}s total")
    print("mouth tracks rebuilt for each; beat timings MUST be recomputed")


if __name__ == "__main__":
    main()
