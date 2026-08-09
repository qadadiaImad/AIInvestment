"""Generate every line for both episodes LOCALLY, then pin it to canon.

This replaces the hosted TTS entirely. The chain is:

    Chatterbox (local weights + a committed reference clip, fixed seed)
      -> pcm16 44.1k
      -> pitch-corrected onto the owner-approved canon
      -> mouth tracks rebuilt from the FINAL audio

WHY LOCAL. grok's voice drifted roughly two semitones between sessions -
measured, twice - and no downstream correction can fix identity because
pitch is not identity: timbre and formants carry it and normalisation
touches neither. With the weights and the reference both on disk and the
seed fixed, the same text yields the same voice a year from now, offline,
for nothing. Verified: line-to-line spread 2.7 Hz (Rex), 1.7 Hz (Sol),
against grok's 18 Hz.

WHY STILL PITCH-CORRECT. The local clone reads lower than the takes the
owner picked by ear (Rex ~128 Hz vs 151, Sol ~144 vs 151). Correcting a
CONSISTENT source onto a fixed target is a safe, one-way job; correcting
a drifting one - which is what was attempted before - is not.

The spoken text is read out of the COMPOSITIONS so the audio can never
drift from the subtitles.

Run in the chatterbox venv:
  C:/Users/imadq/tools/chatterbox-venv/Scripts/python.exe \
      scripts/vector/make_all_vo_local.py [--only ep1|ep2] [--limit N]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

import asr_gate

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "vector"))

COMPS = {"s": REPO / "remotion/src/compositions/BubblesShort.tsx",
         "b": REPO / "remotion/src/compositions/Bubbles.tsx",
         "1": REPO / "remotion/src/compositions/FairMarketEp1.tsx",
         "2": REPO / "remotion/src/compositions/FairMarketEp2.tsx",
         "3": REPO / "remotion/src/compositions/FairMarketEp3.tsx",
         "4": REPO / "remotion/src/compositions/FairMarketEp4.tsx",
         "5": REPO / "remotion/src/compositions/FairMarketEp5.tsx"}
VO_DIR = {"s": REPO / "remotion/public/audio/fairmarket_bshort",
          "b": REPO / "remotion/public/audio/fairmarket_bubbles",
          "1": REPO / "remotion/public/audio/fairmarket",
          "2": REPO / "remotion/public/audio/fairmarket_ep2",
          "3": REPO / "remotion/public/audio/fairmarket_ep3",
          "4": REPO / "remotion/public/audio/fairmarket_ep4",
          "5": REPO / "remotion/public/audio/fairmarket_ep5"}
TRACKS = {"s": REPO / "remotion/src/fixtures/cast_ep1/mouth_tracks_bshort.json",
          "b": REPO / "remotion/src/fixtures/cast_ep1/mouth_tracks_bubbles.json",
          "1": REPO / "remotion/src/fixtures/cast_ep1/mouth_tracks.json",
          "2": REPO / "remotion/src/fixtures/cast_ep1/mouth_tracks_ep2.json",
          "3": REPO / "remotion/src/fixtures/cast_ep1/mouth_tracks_ep3.json",
          "4": REPO / "remotion/src/fixtures/cast_ep1/mouth_tracks_ep4.json",
          "5": REPO / "remotion/src/fixtures/cast_ep1/mouth_tracks_ep5.json"}
REFS = REPO / "remotion/public/audio/voice_refs"
CANON_F = REPO / "remotion/src/fixtures/cast_ep1/voice_canon.json"
FFMPEG = (REPO / "remotion/node_modules/@remotion/"
          "compositor-win32-x64-msvc/ffmpeg.exe")
FPS = 30
SEED = 1234

LINE_RE = re.compile(r'\b(line2?):\s*"((?:[^"\\]|\\.)*)"')


def lines_for(ep: str):
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
            for a, z in [("—", "-"), ("…", "..."), ("“", ""), ("”", ""),
                         ("’", "'"), ("‘", "'")]:
                t = t.replace(a, z)
            out.append((vo.group(1),
                        "rex" if sp.group(1) == "REX" else "sol", t))
    return out


# Words the TTS mishandles, and how to spell them FOR THE TTS ONLY.
# The subtitle keeps the written form; only what is spoken is respelled.
SAY_AS = [
    # ALL-CAPS reads as emphasis-shouting or gets spelled letter by letter.
    # Sentence case with an exclamation mark gets the same read, correctly.
    #
    # THIS TABLE IS EXACT-STRING MATCHES ON EPISODE 1'S SENTENCES, and that
    # is exactly how episode 3 broke. Ep.3 wrote new lines, matched none of
    # these, and shipped with "HA!" spelled out as "aitch-ay" - measured at
    # 0.555 s/syllable against a 0.302 median. The entries stay so ep.1 and
    # ep.2 regenerate byte-identically, but they are no longer the defence:
    # `say()` below applies the same protection as a RULE, to any line.
    ("HA! ...Fundamentals.", "Hah! ... Fundamentals."),
    ("POLITICS", "politics"),
    ("WHAT?!", "What?!"),
    ("INDEX?!", "index?!"),
    ("SCORE", "score"),
    ("Six weeks?", "Six... weeks?"),
]


# ── DELIVERY, PER VOICE ────────────────────────────────────────────────
# Until now every line shipped at Chatterbox's defaults (exaggeration 0.5,
# cfg_weight 0.5, temperature 0.8) because generate() was called with text
# and a reference and nothing else.
#
# The owner hears Rex as "too high, like a child - make him a teenager".
# Measured, that is NOT pitch: his reference clip is 112.8 Hz against Sol's
# 132.2, so he is already the deeper of the two, and their brightness is
# within 3%. What differs is delivery - his lines average 1.9-2.8s against
# Sol's 4.3s and mostly end in "!" or "?!", and on short exclamatory text
# the default intensity reads as yelping. Confirmed by rex_voice_probe:
# calming the delivery also drops his pitch (120.7 -> 112.9 Hz avg), which
# is what you would expect if the shouting was pushing it up.
#
# Setting "B" chosen by the owner from a four-way A/B. Sol stays at the
# defaults he was approved on - changing him was never asked for.
DELIVERY = {
    "rex": dict(exaggeration=0.35, cfg_weight=0.4, temperature=0.7),
    "sol": dict(exaggeration=0.5, cfg_weight=0.5, temperature=0.8),
}

# ── PERFORMANCE TAGS ───────────────────────────────────────────────────
# Chatterbox's tokenizer carries bracket tokens that had never been used
# here. vo_tag_probe generated each one twice, with and without, same seed:
#
#   [sigh] +0.7s   [clear_throat] +1.2s   [whisper] +1.3s   renders
#   [gasp] -0.5s   changes the delivery
#   [laughter] +0.2s   [UM] -0.1s   no audible change - NOT USED
#
# Keyed by VO stem so each placement is deliberate and auditable, and
# applied only to the text fed to the model. The subtitle is read from the
# composition separately, so a tag can never appear on screen.
# MEASURED 2026-08-09, controlled A/B at fixed seed (scripts/vector/tag_ab.py):
# [gasp] and [whisper] render as a clean single onset straight into the
# speech. [sigh] and [clear_throat] render as a short burst, then a GAP,
# then the line - a vocalised artefact sitting in FRONT of the words, which
# is what the owner heard as a stray "T" at the start of sentences.
# [clear_throat] alone adds a full second of it. Both are therefore unused
# on ep.3; ep.1 and ep.2 keep theirs so their approved audio is unchanged.
PERFORM = {
    # ep.1 - Sol is the weary one; the tag does the work the caps used to
    "v1_sol_intro": "[sigh] ",
    "v8_sol_legal": "[clear_throat] ",
    "a4_sol_thin": "[sigh] ",
    "a6_sol_thesis": "[whisper] ",
    "a5_sol_fair": "[sigh] ",
    "a7_sol_ownepisode": "[clear_throat] ",
    "v5_rex_what": "[gasp] ",
    "v7_rex_index": "[gasp] ",
    # ep.2
    "e14_sol_nope": "[sigh] ",
    "e15_sol_sitwith": "[clear_throat] ",
    "e23_sol_clock": "[whisper] ",
    "e28_sol_fair": "[sigh] ",
    "e7_rex_coincidence": "[gasp] ",
    # ep.3 "The Machine". v1 shipped with ZERO tags across 41 lines and
    # the owner heard it immediately: "boring, not funny, something is
    # missing". Every line was generated flat. These are placed per beat.
    # ep.3 - gasp/whisper only, see beats_v2.PERFORM_TAGS
    "b05_rex_what": "[gasp] ",
    "b14_rex_free": "[gasp] ",
    "b27_rex_banks": "[gasp] ",
    "b47_rex_what2": "[gasp] ",
    "b44_sol_runback": "[whisper] ",
    "b52_sol_time": "[whisper] ",
    # Shorts cut v2 - v1's stems (s2_rex_fifteen, s7_sol_nobody) no longer
    # exist; a tag keyed to a stem that is gone is silently a no-op, which is
    # how ep.3 shipped its first cut with zero tags.
    "s4_rex_villain": "[gasp] ",
    "s12_rex_comesback": "[gasp] ",
    "s13_sol_watch": "[whisper] ",
}


# ── SPOKEN-TEXT OVERRIDES ──────────────────────────────────────────────
# The subtitle is read from the composition and the spoken text is derived
# from it, so normally they are the same string. These break that link for
# specific lines, in the same one-way direction as PERFORM: the screen
# keeps what the writer wrote, the model gets something it can pronounce.
#
# WHY. The owner: "still get HA! pronounced letter by letter - disgusting
# audio". Measured: ep.1 says "HA! ...Fundamentals." - five syllables - in
# 1.22s; ep.3 said "HA! ...Bad banks." - three syllables - in 1.67s. Longer
# audio for fewer syllables is what an initialism sounds like, because
# "aitch-ay" is three syllables where "hah" is one.
#
# Chatterbox reads a short ALL-CAPS token as an initialism, which in written
# English it usually is (US, CEO, FBI). Ep.1 survived on luck: it had only
# four capitalised words and all were long real words. The v2 voice pass
# took capitals from 4 to 19 - which fixed the flatness and walked straight
# into this.
SPOKEN = {
    "b03_sol_ha": "Hah! ...Bad banks.",
    "s3_sol_ha": "Hah! ...Fifteen years.",
}

# EVERY remaining ALL-CAPS token is title-cased for the model, not just the
# short ones. That is what ep.1 actually does - look at the table above:
# POLITICS -> politics, INDEX?! -> index?!, SCORE -> score. The capitals are
# for the WRITER and the screen; the model has never been given them and
# has never needed them. Emphasis in the delivery comes from the sentence
# shape, the ellipses and the DELIVERY settings, not from shouting.
#
# "I" and "A" are left alone - ordinary sentence words, not emphasis.
CAPS_TOKEN = re.compile(r"\b([A-Z]{2,})\b")
_KEEP = {"I", "A", "OK"}


def say(stem: str, text: str) -> str:
    """The text the MODEL hears. Never what the viewer reads."""
    if stem in SPOKEN:
        return SPOKEN[stem]
    return CAPS_TOKEN.sub(
        lambda m: m.group(1) if m.group(1) in _KEEP else m.group(1).title(),
        text)


def perform(stem: str, text: str) -> str:
    """Prefix the spoken text with its performance tag, if it has one."""
    return PERFORM.get(stem, "") + text


def say_as(text: str) -> str:
    """Rewrite a line the way it should be SPOKEN.

    Chatterbox reads shouted capitals as spelled-out letters or as a
    strained bark, and bare ellipses become ragged pauses. The written
    line stays as-is on screen - this only changes what is fed to the
    model, so the subtitle and the audio can differ in spelling while
    saying the same thing.
    """
    for a, z in SAY_AS:
        text = text.replace(a, z)
    return text


def trim_silence(x: np.ndarray, sr: int, thresh: float = 0.015) -> np.ndarray:
    """Strip leading/trailing silence.

    Chatterbox pads roughly a third of a second of silence onto the front
    of every file. Measured on the v30 render: speech landed a median 8
    frames after the subtitle and the mouth animation, on 30 of 38 beats.
    The <Audio> starts on time; the VOICE does not. Trimming makes the
    first sound land where the composition already expects it.
    """
    idx = np.nonzero(np.abs(x) > thresh)[0]
    if len(idx) == 0:
        return x
    head = max(0, idx[0] - int(sr * 0.02))       # keep 20ms of air
    tail = min(len(x), idx[-1] + int(sr * 0.06))
    return x[head:tail]


# ── DELIVERY SPEED, PER EPISODE ────────────────────────────────────────
# The owner, on the Shorts cut: "stack more information and maybe speed up
# prononciation". Chatterbox has NO speed control - generate() takes
# repetition_penalty, min_p, top_p, audio_prompt_path, exaggeration,
# cfg_weight and temperature, and sweeping cfg_weight 0.20-0.50 moved the
# rate between 2.85 and 3.11 syllables/sec, which is noise
# (scripts/vector/pace_ab.py). So the speed-up is a tempo change afterwards.
#
# This repo had a standing grudge against that - make_all_vo_local's own
# comment says WSOLA "smears speech and leaves a metallic edge" - so it was
# measured rather than assumed (scripts/vector/tempo_ab.py). Transcribing
# every rate back with faster-whisper and scoring against the input text:
# word-error DAMAGE relative to the untouched control is +0.000 at every
# rate up to 1.38x. The intelligibility cost of speeding this voice up is,
# as far as an ASR model can tell, zero.
#
# The choice of FILTER is where the grudge was right. Nominally rubberband
# is the better time-stretcher; on this material it drifts the share of
# energy above 4kHz by 20.6% at 1.30x where plain atempo drifts it 3.6% -
# that drift IS the metallic edge. So: atempo.
#
# 1.30 SHIPPED AND WAS WRONG. The owner heard it and said "artificial", and
# he was right - the WER gate had answered a different question. An ASR model
# does not care whether speech sounds synthetic, only whether it is
# decodable, so "+0.000 word-error damage at 1.38x" was true and irrelevant.
#
# scripts/vector/stretch_artefact.py asks the question that was actually
# being complained about, by measuring spectral flux on voiced frames - the
# accumulating splice discontinuities that overlap-add leaves on sustained
# sound, which is what "processed" sounds like. Against an unstretched
# baseline: +1.9% at 1.08x, +6.6% at 1.15x, +13.7% at 1.30x. The knee is
# just above 1.08.
#
# 1.10 also lands the cut on the rate the owner has ALREADY approved: the
# short's natural rate is 3.57 syl/s, ep.1 (which he called perfect) sits at
# 3.89, and 1.10x puts the short at 3.93. Still faster than the full episode
# (3.52), which is what "speed up prononciation" asked for - just not faster
# than anything he has ever signed off, which is what 1.30x was.
#
# Applied inside the generation chain, so it can never compound: a rerun
# always starts from fresh model output, never from an already-stretched
# file.
SPEED = {"s": 1.10}

# Lines that are NOT generated at the default seed, and why. fix_stray_onset.py
# resamples a line until the burst-then-gap probe calls it clean and keeps the
# winning seed - but it only wrote the WAV. A later full regeneration at SEED
# would have silently reinstated the take the probe rejected, with nothing to
# notice it. The seed is part of the recipe, so it lives here.
ASR_TRIES = 5        # resamples allowed before a line is reported broken
SEED_OVERRIDE = {
    "b21_rex_crowbar": 1335,     # stray onset: burst 100ms, gap 80ms
    "b49_rex_fifteen": 1436,     # stray onset: burst 90ms, gap 360ms
    "s12_rex_comesback": 1537,   # stray onset: burst 110ms, gap 60ms
    "s13_sol_watch": 2211,       # seed 1234 hallucinates letters, reproducibly
    "s6_rex_which": 1537,        # stray onset
    "s9_rex_houses": 1537,       # stray onset
}


def to_pcm16(src: Path, dst: Path, speed: float = 1.0) -> None:
    """Chatterbox writes float32 wav, which the stdlib wave module and
    several downstream tools refuse outright."""
    filt = ["-filter:a", "atempo=%.4f" % speed] if speed and speed != 1.0 else []
    subprocess.run([str(FFMPEG), "-v", "error", "-i", str(src)] + filt +
                   ["-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1",
                    str(dst), "-y"], check=True)


def amp_track(p: Path):
    with wave.open(str(p)) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float) / 32768
    step = max(1, sr // FPS)
    rms = np.array([float(np.sqrt((x[i:i + step] ** 2).mean()))
                    for i in range(0, len(x), step) if len(x[i:i + step])])
    ref = float(np.percentile(rms, 92)) or 1.0
    return [0 if v / ref < 0.16 else (1 if v / ref < 0.5 else 2) for v in rms]


def main() -> None:
    import torch
    import torchaudio
    from chatterbox.tts import ChatterboxTTS
    from voice_canon import read, write, measure, shift_pitch, tilt

    canon = json.loads(CANON_F.read_text("utf-8"))
    # canon keys the rest of the repo uses are rex / sal
    tgt = {"rex": canon["rex"], "sol": canon["sal"]}

    eps = ["1", "2"]
    if "--only" in sys.argv:
        eps = [sys.argv[sys.argv.index("--only") + 1].replace("ep", "")]
    limit = (int(sys.argv[sys.argv.index("--limit") + 1])
             if "--limit" in sys.argv else None)
    only_stems = (set(sys.argv[sys.argv.index("--stems") + 1].split(","))
                  if "--stems" in sys.argv else None)

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print("device " + dev + ", seed " + str(SEED))
    model = ChatterboxTTS.from_pretrained(device=dev)

    for ep in eps:
        lines = lines_for(ep)
        if limit:
            lines = lines[:limit]
        if only_stems:
            lines = [l for l in lines if l[0] in only_stems]
        print("\n=== EPISODE " + ep + ": " + str(len(lines)) + " lines ===")
        tracks = {}
        keep_tracks = json.loads(TRACKS[ep].read_text("utf-8")) if (
            only_stems and TRACKS[ep].exists()) else {}
        for k, (stem, voice, text) in enumerate(lines, 1):
            seed = SEED_OVERRIDE.get(stem, SEED)
            torch.manual_seed(seed)
            if dev == "cuda":
                torch.cuda.manual_seed_all(seed)
            np.random.seed(seed)
            prompt = perform(stem, say(stem, say_as(text)))
            out = VO_DIR[ep] / (stem + ".wav")
            raw = VO_DIR[ep] / ("_" + stem + "_raw.wav")

            # THE ASR GATE. Chatterbox does not always say what it was given.
            # This episode's closing line came back as "W. W. W. S. R. W. S.
            # R. W. 5. W. S. R. Not the number." - 6.37 seconds of letters,
            # on the last beat of the Shorts cut - and nothing else in the
            # pipeline could see it. Durations only know it is long; the
            # mouth tracks are built FROM the audio so they matched the
            # garbage perfectly. So every line is transcribed back and
            # resampled at a fresh seed until it IS the line.
            asr = ""
            for attempt in range(ASR_TRIES):
                if attempt:
                    torch.manual_seed(seed + attempt * 977)
                    if dev == "cuda":
                        torch.cuda.manual_seed_all(seed + attempt * 977)
                    np.random.seed(seed + attempt * 977)
                wav = model.generate(
                    prompt,
                    audio_prompt_path=str(REFS / ("voice_ref_" + voice + ".wav")),
                    **DELIVERY[voice])
                torchaudio.save(str(raw), wav, model.sr)
                to_pcm16(raw, out, SPEED.get(ep, 1.0))
                raw.unlink(missing_ok=True)
                e, hyp, ok = asr_gate.check(out, text)
                if ok:
                    asr = "" if attempt == 0 else "  [reseeded x%d]" % attempt
                    break
                print("      ASR REJECT (wer %.2f) seed %d: %r"
                      % (e, seed + attempt * 977, hyp[:60]), flush=True)
                asr = "  [ASR FAILED %d tries]" % ASR_TRIES
            # strip the leading pad so the voice lands on the beat
            with wave.open(str(out)) as w:
                sr0, n0 = w.getframerate(), w.getnframes()
                xx = (np.frombuffer(w.readframes(n0), dtype=np.int16)
                      .astype(np.float64) / 32768.0)
            xx = trim_silence(xx, sr0)
            with wave.open(str(out), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(sr0)
                w.writeframes((np.clip(xx, -1, 1) * 32767).astype(np.int16).tobytes())

            # PITCH CORRECTION IS OFF BY DEFAULT.
            # It existed to compensate for grok drifting between sessions.
            # Local generation removes that drift at the source, so the
            # correction now buys nothing and costs quality: WSOLA
            # time-stretching smears speech and leaves a metallic edge,
            # and it was being applied to every single line. Pass
            # --canon to re-enable it.
            if "--canon" not in sys.argv:
                with wave.open(str(out)) as w:
                    dur = w.getnframes() / w.getframerate()
                tracks[stem] = amp_track(out)
                print("  [%2d/%d] %-22s %-3s %5.2fs  raw     %s%s"
                      % (k, len(lines), stem, voice, dur, text[:38], asr),
                      flush=True)
                continue
            x, sr = read(out)
            m = measure(x, sr)
            note = ""
            if m:
                f0, roll = m
                semis = 12 * np.log2(tgt[voice]["f0"] / f0)
                if abs(semis) <= 5.0:
                    db = float(np.clip(20 * np.log10(
                        tgt[voice]["rolloff"] / max(roll, 1.0)) * 0.5, -6, 6))
                    y = tilt(shift_pitch(x, sr, tgt[voice]["f0"] / f0), sr, db)
                    pk = np.abs(y).max()
                    if pk > 0.99:
                        y *= 0.99 / pk
                    write(out, y, sr)
                    note = "%6.1f->%5.1fHz" % (f0, tgt[voice]["f0"])
                else:
                    note = "SKIP %+.1fst" % semis
            with wave.open(str(out)) as w:
                dur = w.getnframes() / w.getframerate()
            tracks[stem] = amp_track(out)
            print("  [%2d/%d] %-22s %-3s %5.2fs %s  %s"
                  % (k, len(lines), stem, voice, dur, note, text[:38]),
                  flush=True)
        # A --stems run rebuilds tracks for the stems it touched and MERGES
        # them over the rest. Writing `tracks` straight out would leave the
        # episode with a mouth-track file describing one line, which is the
        # same class of bug as importing the wrong episode's tracks - the
        # viseme machinery would keep working perfectly on data that does not
        # describe the episode, and every other mouth would stay shut.
        merged = {**keep_tracks, **tracks}
        TRACKS[ep].write_text(json.dumps(merged), "utf-8")
        print("  episode %s: %d tracks rebuilt%s"
              % (ep, len(tracks),
                 " (merged into %d)" % len(merged) if keep_tracks else ""))

    print("\nnow: EP=1 and EP=2 retime_beats.py --write, then render")


if __name__ == "__main__":
    main()
