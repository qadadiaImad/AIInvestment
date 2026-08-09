"""Regenerate the lines that start with a stray burst, gated on the probe.

leading_burst.py finds them; this fixes them. The two are deliberately
separate: a detector that also repairs is a detector you stop trusting.

WHAT IT REPAIRS. A line whose head is a short burst, then a gap near
silence, then the speech - the acoustic shape of the owner's complaint
("still hearing some T ... at the start of some sentences"). Removing the
tags that caused most of these took ep.3 from 2/12 tagged lines to 0/7, but
two UNTAGGED lines still show it, so the cause there is the sampler, not
the prompt.

WHY RESAMPLE RATHER THAN CUT. Cutting the head off is tempting and wrong
in the one case that matters: if the burst is genuinely the first consonant
of the first word, cutting it turns "Fifteen years" into "ifteen years",
and the probe cannot tell the two apart - that is exactly why it reports a
GAP rather than a burst. Drawing a different sample keeps a real onset.
The seed moves and nothing else does; delivery, reference clip and text are
untouched, so the voice is the same voice.

Each candidate is post-processed exactly the way the main pipeline does it
(to_pcm16 -> trim_silence) before being judged, because the probe reads the
shipped file, not the raw model output. The first clean take wins. If no
seed in the budget is clean the original is LEFT ALONE and the stem is
reported as unfixed - shipping a known-bad line loudly beats shipping a
silently mangled one.

  chatterbox-venv/Scripts/python.exe scripts/vector/fix_stray_onset.py b b21_rex_crowbar b49_rex_fifteen
"""
from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "vector"))

import make_all_vo_local as V          # noqa: E402  the pipeline itself
from leading_burst import head_env, stray   # noqa: E402  the detector itself

TRIES = 8
REFS = REPO / "remotion/public/audio/voice_refs"


def lines_index(ep: str) -> dict[str, tuple[str, str]]:
    """stem -> (voice, on-screen text), straight from the episode source."""
    return {stem: (voice, text) for stem, voice, text in V.lines_for(ep)}


def post(raw: Path, out: Path, ep: str) -> None:
    """The pipeline's own post-chain, so the probe judges what ships.

    The episode's delivery SPEED has to come along too: without it a repaired
    line on the Shorts cut would come back at 1.00x while its 13 neighbours
    are at 1.30x, and nothing downstream would notice.
    """
    V.to_pcm16(raw, out, V.SPEED.get(ep, 1.0))
    raw.unlink(missing_ok=True)
    with wave.open(str(out)) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64) / 32768.0
    x = V.trim_silence(x, sr)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def main() -> None:
    import torch
    import torchaudio
    from chatterbox.tts import ChatterboxTTS

    ep = sys.argv[1]
    stems = sys.argv[2:]
    if not stems:
        raise SystemExit("give at least one stem")

    idx = lines_index(ep)
    vo_dir = V.VO_DIR[ep]
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTTS.from_pretrained(device=dev)

    fixed, unfixed = [], []
    for stem in stems:
        if stem not in idx:
            print("%-22s NOT IN EPISODE %s" % (stem, ep))
            continue
        voice, text = idx[stem]
        out = vo_dir / (stem + ".wav")
        keep = out.read_bytes()
        prompt = V.perform(stem, V.say(stem, V.say_as(text)))
        print("\n%s  [%s]  %r" % (stem, voice, prompt))

        won = None
        for k in range(1, TRIES + 1):
            seed = V.SEED + k * 101
            torch.manual_seed(seed)
            if dev == "cuda":
                torch.cuda.manual_seed_all(seed)
            np.random.seed(seed)
            wav = model.generate(
                prompt, audio_prompt_path=str(REFS / ("voice_ref_" + voice + ".wav")),
                **V.DELIVERY[voice])
            raw = vo_dir / ("_" + stem + "_try.wav")
            torchaudio.save(str(raw), wav, model.sr)
            post(raw, out, ep)
            bad, why = stray(head_env(out))
            with wave.open(str(out)) as w:
                dur = w.getnframes() / w.getframerate()
            print("   seed %-6d %5.2fs  %s" % (seed, dur, why or "clean"))
            if not bad:
                won = seed
                break

        if won is None:
            out.write_bytes(keep)          # put the original back, untouched
            unfixed.append(stem)
            print("   -> NO CLEAN TAKE in %d tries; original restored" % TRIES)
        else:
            fixed.append((stem, won))
            print("   -> kept seed %d" % won)

    print("\nfixed   : " + (", ".join("%s@%d" % f for f in fixed) or "none"))
    print("unfixed : " + (", ".join(unfixed) or "none"))
    if fixed:
        print("\nDurations moved. Re-run the mouth tracks and the retime:")
        print("  python scripts/vector/mouth_tracks_for.py " + ep)
        print("  EP=" + ep + " python scripts/vector/retime_beats.py --write")


if __name__ == "__main__":
    main()
