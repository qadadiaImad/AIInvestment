"""Synthesise the narration, measure it, and size the reel to fit.

The first narrated cut was written to a timeline that already existed: acts were
sized by eye, then lines were written to fill them. That produced 74.7 seconds of
speech for a 36 second reel - ten of thirteen segments talking over the next cue.

So the dependency is inverted here. The script is synthesised first, every
segment is measured, and each act is sized to what was ACTUALLY said plus a
breath. The composition reads those beats from the fixture, so the picture
follows the voice rather than the voice being asked to fit the picture.

Usage:
    python scripts/ta_quiz/build_narrated_cut.py            # measure + write beats
    python scripts/ta_quiz/build_narrated_cut.py --tts      # re-synthesise first
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
VO = os.path.join(REPO, "content", "probe", "vo")
SCRIPT = os.path.join(REPO, "content", "probe", "vo_script.json")
FIXTURE = os.path.join(REPO, "remotion", "src", "fixtures", "trading_quiz_spy_cup_zoom.json")
GROK = os.path.expanduser("~/tools/grok-cli/grok-cli.exe")
FFPROBE = r"C:\ffmpeg\bin\ffprobe.exe"

FPS = 30
# Breath after each line before the next act may start. Below ~0.25s the cuts
# tread on the tail of the previous word.
PAD = {
    "tape": 0.5, "widen": 0.35, "deep": 0.3, "justify": 0.5, "countdown": 0.4,
    "entry": 0.35, "stop": 0.45, "target": 0.45, "zones": 0.3,
    "reveal": 0.4, "hit": 0.4, "rule": 0.5, "end": 0.4,
}


def load():
    return json.load(io.open(SCRIPT, encoding="utf-8"))


def synth(d):
    for s in d["segments"]:
        out = os.path.join(VO, s["id"] + ".mp3")
        r = subprocess.run(
            [GROK, "tts", "--voice-id", d["voice"], "--output-format", "mp3",
             "--output", out, "--text", s["text"]],
            capture_output=True, text=True)
        print(("  ok   " if r.returncode == 0 else "  FAIL ") + s["id"])
        if r.returncode != 0:
            print(r.stderr[:300], file=sys.stderr)
            return False
    return True


def dur(path):
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True).stdout.strip()
    return float(out)


def frames(sec):
    return int(round(sec * FPS))


def main(argv):
    d = load()
    os.makedirs(VO, exist_ok=True)
    if "--tts" in argv:
        print("synthesising:")
        if not synth(d):
            return 1

    seg = {s["act"]: dur(os.path.join(VO, s["id"] + ".mp3")) for s in d["segments"]}
    missing = [a for a in PAD if a not in seg]
    if missing:
        print("no audio for acts: " + ", ".join(missing), file=sys.stderr)
        return 1

    def need(act):
        return frames(seg[act] + PAD[act])

    # ---- lay the reel out in order, each act as long as its line needs -------
    t = 40                                   # boot + hook, before any speech
    tape = t;        t += need("tape")
    fastFrom = t;    t += need("widen")
    fastTo = t;      t += need("deep")
    deepTo = t;      t += need("justify")
    justifyTo = t;   t += frames(0.9)        # camera returns, no line over it
    count = t;       t += 150                # the countdown is exactly 5s
    answer = t;      t += frames(0.9)        # badge lands before the trade talk
    rr = t;          t += need("entry")
    rrStop = t;      t += need("stop")
    rrTarget = t;    t += need("target")
    rrZones = t;     t += need("zones")
    reveal = t
    # The reveal must outlast its own line AND leave the winning bar somewhere
    # sensible: the check fires when that bar prints, so the span is sized so the
    # bar lands with room for the "target hit" line to finish before the rule.
    revealSpan = max(frames(seg["reveal"] + seg["hit"] + PAD["hit"] + 0.5), 110)
    t += revealSpan
    rule = t;        t += need("rule")
    endcard = t;     t += need("end")
    total = t

    beats = {
        "LEVEL": max(0, fastTo - 20), "PATTERN": deepTo - 10, "ARROWS": justifyTo + 6,
        "COUNT": count, "ANSWER": answer,
        "RR": rr, "RR_STOP": rrStop, "RR_TARGET": rrTarget, "RR_ZONES": rrZones,
        "REVEAL": reveal, "REVEAL_SPAN": revealSpan,
        "RULE": rule, "ENDCARD": endcard, "TOTAL": total,
        "tape": tape, "fastFrom": fastFrom, "fastTo": fastTo,
        "deepTo": deepTo, "justifyTo": justifyTo,
        "touchIn": deepTo + 4, "touchStep": max(3, (justifyTo - deepTo - 16) // 10),
    }

    fx = json.load(io.open(FIXTURE, encoding="utf-8"))
    fx["zoom"]["beats"] = beats
    fx["durationInFrames"] = total
    with io.open(FIXTURE, "w", encoding="utf-8") as f:
        json.dump(fx, f, indent=2, ensure_ascii=False)

    # ---- the cue sheet, for muxing and for reading ---------------------------
    cues = []
    order = [("tape", tape), ("widen", fastFrom), ("deep", fastTo), ("justify", deepTo),
             ("countdown", count + 5), ("entry", rr), ("stop", rrStop),
             ("target", rrTarget), ("zones", rrZones), ("reveal", reveal + 6),
             ("hit", reveal + revealSpan - frames(seg["hit"] + 0.45)),
             ("rule", rule), ("end", endcard + 4)]
    ids = {s["act"]: s["id"] for s in d["segments"]}
    for act, at in order:
        cues.append({"id": ids[act], "act": act, "at": at,
                     "start_s": round(at / FPS, 3), "dur_s": round(seg[act], 3)})
    json.dump({"fps": FPS, "total": total, "cues": cues},
              io.open(os.path.join(VO, "cues.json"), "w", encoding="utf-8"), indent=2)

    print("%-11s %8s %8s %8s" % ("act", "start_s", "line_s", "act_s"))
    for i, (act, at) in enumerate(order):
        nxt = order[i + 1][1] if i + 1 < len(order) else total
        print("%-11s %8.2f %8.2f %8.2f%s" % (
            act, at / FPS, seg[act], (nxt - at) / FPS,
            "   OVERRUNS" if seg[act] > (nxt - at) / FPS + 0.05 else ""))
    print("\nnarration %.1fs   reel %d frames / %.1fs" %
          (sum(seg.values()), total, total / FPS))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
