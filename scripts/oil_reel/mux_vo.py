"""Place the Hormuz voiceover onto the rendered reel.

Why this is a script and not an ffmpeg one-liner:

1. **Overrun has to be an error, not a shrug.** Each line is written for a
   specific picture beat. If line 5 runs past where line 6 starts, the voice is
   describing the wrong thing on screen and the whole cut reads as dubbed. TTS
   duration is not predictable from word count, so the only honest way to know
   is to generate, measure, and refuse to build if it doesn't fit.

2. **The SFX have to duck.** The reel already has keyswitches, whooshes and a
   sting. At full level under a voice they stop being texture and start being
   interference. A sidechain envelope from the voice track solves it; Remotion's
   bundled ffmpeg is a minimal build with no sidechaincompress, so it is done
   here in plain Python — the same reason scripts/audio/make_tick.py exists.

Usage:
    python scripts/oil_reel/mux_vo.py            # build from lines.json
    python scripts/oil_reel/mux_vo.py --dry-run  # measure + validate only
"""
import argparse
import json
import math
import os
import struct
import subprocess
import sys
import urllib.request
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
WORK = os.path.join(REPO, "content", "probe", "vo")
REEL = os.path.join(REPO, "content", "probe", "hormuz_reel.mp4")
OUT = os.path.join(REPO, "content", "probe", "hormuz_reel_vo.mp4")
FFMPEG = os.path.join(
    REPO, "remotion", "node_modules", "@remotion", "compositor-win32-x64-msvc", "ffmpeg.exe"
)

FPS = 30
RATE = 48000
TOTAL_FRAMES = 2220

# How loud the voice sits, and how far the rest of the mix drops under it.
# Hierarchy at every timestamp (research: broadcast convention): VOICE on top,
# SFX stingers just under it, music bed lowest — and the bed ducks DEEPER than
# the SFX because it is texture, not information.
VOICE_GAIN = 1.0
BED_GAIN = 0.78          # the SFX bed when the voice is silent
DUCK_TO = 0.30           # ...and when it is not
MUSIC_GAIN = 0.60        # the music bed when the voice is silent
MUSIC_DUCK_TO = 0.16     # ...and when it is not (-12..-18dB under VO)
DUCK_ATTACK = 0.06       # seconds to pull down — fast, but not a click
DUCK_RELEASE = 0.55      # ...and to come back slower, or it pumps

# A line may bleed this far past the next line's start before it is an error.
# Some overlap is natural speech; a second of it is two people talking.
BLEED_TOLERANCE = 0.35


def read_wav_mono(path):
    """Decode to mono float at RATE. Handles the 24kHz the TTS returns."""
    with wave.open(path) as w:
        n, ch, sw, sr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        if sw != 2:
            raise SystemExit(f"{path}: expected 16-bit, got {sw*8}-bit")
        raw = struct.unpack("<%dh" % (n * ch), w.readframes(n))
    mono = [raw[i * ch] / 32768.0 for i in range(n)] if ch > 1 else [v / 32768.0 for v in raw]
    if sr == RATE:
        return mono
    # linear resample — inaudible on speech, and avoids a filter dependency
    ratio = RATE / sr
    out = []
    for i in range(int(len(mono) * ratio)):
        pos = i / ratio
        k = int(pos)
        frac = pos - k
        a = mono[k] if k < len(mono) else 0.0
        b = mono[k + 1] if k + 1 < len(mono) else a
        out.append(a + (b - a) * frac)
    return out


def write_wav_stereo(path, samples):
    with wave.open(path, "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(
            b"".join(
                struct.pack("<hh", int(max(-1, min(1, s)) * 32767), int(max(-1, min(1, s)) * 32767))
                for s in samples
            )
        )


def fetch(url, dest):
    """Download a voice take and hand back a WAV path. ElevenLabs returns mp3;
    the wave module can't read it, so anything non-RIFF goes through ffmpeg."""
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return dest
    raw = dest + ".dl"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r, open(raw, "wb") as f:
        f.write(r.read())
    with open(raw, "rb") as f:
        magic = f.read(4)
    if magic == b"RIFF":
        os.replace(raw, dest)
    else:
        subprocess.run(
            [FFMPEG, "-v", "error", "-i", raw, "-ar", str(RATE), "-ac", "1", dest, "-y"],
            check=True,
        )
        os.remove(raw)
    return dest


def envelope(voice, attack_s, release_s):
    """Per-sample 0..1 'voice is speaking' envelope with asymmetric slew."""
    a = 1.0 - math.exp(-1.0 / (RATE * attack_s))
    r = 1.0 - math.exp(-1.0 / (RATE * release_s))
    env, cur = [0.0] * len(voice), 0.0
    for i, v in enumerate(voice):
        target = min(1.0, abs(v) * 6.0)
        cur += (target - cur) * (a if target > cur else r)
        env[i] = cur
    return env


def main():
    global REEL, OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--reel", default=REEL)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--lines", default=os.path.join(WORK, "lines.json"))
    args = ap.parse_args()
    REEL, OUT = args.reel, args.out

    lines = json.load(open(args.lines))
    os.makedirs(WORK, exist_ok=True)

    # ---- fetch + measure -------------------------------------------------
    for ln in lines:
        ln["path"] = fetch(ln["url"], os.path.join(WORK, f"vo{ln['n']:02d}.wav"))
        ln["samples"] = read_wav_mono(ln["path"])
        ln["dur"] = len(ln["samples"]) / RATE
        ln["start"] = ln["frame"] / FPS
        ln["end"] = ln["start"] + ln["dur"]

    # ---- validate: does every line fit before the next one starts? -------
    total_s = TOTAL_FRAMES / FPS
    problems = []
    print(f"{'#':>2}  {'start':>6} {'dur':>6} {'end':>6}  {'slot':>6}  line")
    for i, ln in enumerate(lines):
        nxt = lines[i + 1]["start"] if i + 1 < len(lines) else total_s
        slot = nxt - ln["start"]
        over = ln["dur"] - slot
        flag = ""
        if over > BLEED_TOLERANCE:
            flag = f"  <-- OVERRUNS by {over:.2f}s"
            problems.append((ln["n"], over, ln["text"]))
        elif over > 0:
            flag = f"  (bleeds {over:.2f}s, ok)"
        print(
            f"{ln['n']:>2}  {ln['start']:6.2f} {ln['dur']:6.2f} {ln['end']:6.2f}  "
            f"{slot:6.2f}  {ln['text'][:44]}{flag}"
        )
    if lines[-1]["end"] > total_s + 0.05:
        problems.append((lines[-1]["n"], lines[-1]["end"] - total_s, "runs past the end of the reel"))

    if problems:
        print("\nREFUSING TO BUILD — the voice would talk over the wrong picture:")
        for n, over, txt in problems:
            print(f"  line {n}: {over:+.2f}s  {txt}")
        print("\nShorten the line, or raise its speech_rate, and regenerate it.")
        sys.exit(1)
    print("\nall lines fit.")
    if args.dry_run:
        return

    # ---- build the voice track ------------------------------------------
    n_total = int(total_s * RATE) + RATE
    voice = [0.0] * n_total
    for ln in lines:
        off = int(ln["start"] * RATE)
        for i, v in enumerate(ln["samples"]):
            if off + i < n_total:
                voice[off + i] += v * VOICE_GAIN

    # ---- pull the existing SFX bed out of the render ---------------------
    bed_wav = os.path.join(WORK, "bed.wav")
    subprocess.run(
        [FFMPEG, "-v", "error", "-i", REEL, "-vn", "-ac", "1", "-ar", str(RATE), bed_wav, "-y"],
        check=True,
    )
    bed = read_wav_mono(bed_wav)
    bed += [0.0] * max(0, n_total - len(bed))

    # ---- the music bed, if one has been synthesized ------------------------
    music_wav = os.path.join(WORK, "bed_music.wav")
    music = read_wav_mono(music_wav) if os.path.exists(music_wav) else []
    music += [0.0] * max(0, n_total - len(music))
    if any(music):
        print("music bed found — mixing three tracks (voice > sfx > music)")

    # ---- duck sfx and music under the voice, music deeper, and mix --------
    env = envelope(voice, DUCK_ATTACK, DUCK_RELEASE)
    mix = []
    for i in range(n_total):
        duck = BED_GAIN + (DUCK_TO - BED_GAIN) * env[i]
        mduck = MUSIC_GAIN + (MUSIC_DUCK_TO - MUSIC_GAIN) * env[i]
        mix.append(voice[i] + bed[i] * duck + music[i] * mduck)

    peak = max(abs(v) for v in mix) or 1.0
    if peak > 0.97:  # normalise only if we would clip
        mix = [v / peak * 0.97 for v in mix]

    mixed = os.path.join(WORK, "mixed.wav")
    write_wav_stereo(mixed, mix)

    # ---- mux ------------------------------------------------------------
    subprocess.run(
        [FFMPEG, "-v", "error", "-i", REEL, "-i", mixed, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT, "-y"],
        check=True,
    )
    print(f"peak before limiting {peak:.3f}")
    print(f"-> {os.path.relpath(OUT, REPO)}  ({os.path.getsize(OUT)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
