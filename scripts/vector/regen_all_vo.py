"""Regenerate EVERY spoken line for both episodes in a single pass.

WHY THIS EXISTS. grok's TTS is not stable across sessions. Same tool,
same voice-id, different day - measured 2026-08-04, band-limited to the
range both sample rates share:

    EP1 Rex, original session   pitch 180.0 Hz   rolloff85 3331 Hz
    EP1 Rex, regenerated later  pitch 166.4 Hz   rolloff85 4528 Hz
    EP2 Rex, later still        pitch 161.7 Hz   rolloff85 5124 Hz

Sol drifted the same way (200.5 -> 185.3 Hz). That is roughly two
semitones down and half again as bright - clearly audible, and exactly
the "rex voice changed" the owner heard.

It also means episode 1 had become inconsistent WITH ITSELF: an earlier
fix regenerated only the Chatterbox-cloned lines, leaving ep.1 carrying
two different grok vintages side by side. Diagnosing "same engine" was
not enough; the engine has to be the same RUN.

So: every line, both episodes, one invocation. The only way the voices
match is if nothing is left over from a previous session.

The spoken text is read from the COMPOSITIONS, not re-typed here - the
subtitle is the script, so there is one source of truth and no chance of
audio and caption drifting apart.

  python scripts/vector/regen_all_vo.py [--dry]
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
COMPS = {"1": REPO / "remotion/src/compositions/FairMarketEp1.tsx",
         "2": REPO / "remotion/src/compositions/FairMarketEp2.tsx"}
VO_DIR = {"1": REPO / "remotion/public/audio/fairmarket",
          "2": REPO / "remotion/public/audio/fairmarket_ep2"}
TRACKS = {"1": REPO / "remotion/src/fixtures/cast_ep1/mouth_tracks.json",
          "2": REPO / "remotion/src/fixtures/cast_ep1/mouth_tracks_ep2.json"}
GROK = Path(os.path.expanduser("~/tools/grok-cli/grok-cli.exe"))
AUTH = Path(os.path.expanduser("~/.grok-cli/auth.json"))
FFMPEG = (REPO / "remotion/node_modules/@remotion/"
          "compositor-win32-x64-msvc/ffmpeg.exe")
FPS = 30

LINE_RE = re.compile(r'\b(line2?):\s*"((?:[^"\\]|\\.)*)"')


def lines_for(ep: str) -> list[tuple[str, str, str]]:
    src = COMPS[ep].read_text("utf-8")
    i = src.index("= [", src.index("const BEATS: Beat[] = [")) + 2
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "[":
            depth += 1
        elif src[j] == "]":
            depth -= 1
            if depth == 0:
                body = src[i + 1:j]
                break
    body = re.sub(r"//.*", "", body)
    beats, depth, cur = [], 0, ""
    for ch in body:
        if ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        cur += ch
        if depth == 0 and ch == "}":
            beats.append(cur)
            cur = ""
    out = []
    for b in beats:
        texts = {m.group(1): m.group(2) for m in LINE_RE.finditer(b)}
        for vk, sk, lk in (("vo", "speaker", "line"),
                           ("vo2", "speaker2", "line2")):
            vo = re.search(r'\b' + vk + r':\s*"([a-z0-9_]+)"', b)
            sp = re.search(r'\b' + sk + r':\s*"(SOL|REX)"', b)
            if not (vo and sp and lk in texts):
                continue
            t = texts[lk].replace('\\"', '"')
            # TTS reads punctuation literally; normalise the typography
            for a, z in [("—", "-"), ("…", "..."), ("“", ""),
                         ("”", ""), ("’", "'"), ("‘", "'")]:
                t = t.replace(a, z)
            out.append((vo.group(1),
                        "sal" if sp.group(1) == "SOL" else "rex", t))
    return out


def synth(stem: str, voice: str, text: str, vo_dir: Path) -> Path:
    raw = vo_dir / ("_" + stem + "_raw.wav")
    r = subprocess.run([str(GROK), "tts", "--auth-file", str(AUTH),
                        "--voice-id", voice, "--output", str(raw),
                        "--output-format", "wav", text],
                       capture_output=True, text=True)
    if r.returncode != 0 or not raw.exists():
        sys.exit("tts failed for " + stem + ": " + r.stdout + r.stderr)
    out = vo_dir / (stem + ".wav")
    # grok writes a placeholder header reporting 44,739 seconds; decode to
    # real PCM so every downstream duration read is honest. 44.1k mono
    # for ALL of them, so no file is a different rate from its neighbours.
    subprocess.run([str(FFMPEG), "-v", "error", "-i", str(raw),
                    "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1",
                    str(out), "-y"], check=True)
    raw.unlink(missing_ok=True)
    return out


def track(p: Path) -> list[int]:
    with wave.open(str(p)) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float) / 32768
    step = max(1, sr // FPS)
    rms = np.array([float(np.sqrt((x[i:i + step] ** 2).mean()))
                    for i in range(0, len(x), step) if len(x[i:i + step])])
    ref = float(np.percentile(rms, 92)) or 1.0
    return [0 if v / ref < 0.16 else (1 if v / ref < 0.5 else 2) for v in rms]


def main() -> None:
    dry = "--dry" in sys.argv
    grand = 0
    for ep in ("1", "2"):
        lines = lines_for(ep)
        print("\n=== EPISODE " + ep + ": " + str(len(lines)) + " lines ===")
        if dry:
            for stem, v, t in lines:
                print("  " + stem.ljust(22) + v + "  " + t[:64])
            grand += len(lines)
            continue
        tracks = {}
        total = 0.0
        for stem, voice, text in lines:
            p = synth(stem, voice, text, VO_DIR[ep])
            with wave.open(str(p)) as w:
                d = w.getnframes() / w.getframerate()
            tracks[stem] = track(p)
            total += d
            print("  %-22s %-4s %5.2fs %4df  %s"
                  % (stem, voice, d, round(d * FPS), text[:52]), flush=True)
        TRACKS[ep].write_text(json.dumps(tracks), "utf-8")
        print("  episode " + ep + ": %.1fs of speech, %d tracks rebuilt"
              % (total, len(tracks)))
        grand += len(lines)
    print("\n" + str(grand) + " lines total"
          + (" (dry run)" if dry else " - ONE session, one voice each"))
    if not dry:
        print("beat timings must now be recomputed: "
              "EP=1 and EP=2 retime_beats.py --write")


if __name__ == "__main__":
    main()
