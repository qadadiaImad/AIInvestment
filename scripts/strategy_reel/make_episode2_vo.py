"""Episode 2 voices — reuses episode 1's machinery (synth_lines/oncamera).

  C:/Users/imadq/tools/chatterbox-venv/Scripts/python.exe scripts/strategy_reel/make_episode2_vo.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from make_episode_vo import PROBE, oncamera, synth_lines  # noqa: E402

BRIDGE2 = ("This time, something more complex. The inverse head and shoulders. "
           "Recent, and on oil.")

ACT3 = [
    (0.6, "Three dips. The middle one is the deepest. That's the head."),
    (4.6, "Shoulders left and right. Neckline above."),
    (7.75, "Does the neckline break? Five seconds."),
    (13.0, "It breaks. That's the signal."),
    (16.9, "Entry at the neckline. Stop below the shoulder. Target, the head's depth projected up."),
    (21.4, "Measured move. Hit."),
]

ACT4_SPECS = [
    ("start+0.1", "Not fiction. West Texas oil, this January."),
    ("l1+1.3", "First dip. Left shoulder."),
    ("head+0.3", "Deeper low. The head."),
    ("l2+0.3", "Third dip, shallower. Right shoulder. Now draw the neckline."),
    ("breakout+0.3", "January twenty eighth. The neckline breaks."),
    ("trade_frame+1.6", "Entry sixty two thirty six. Stop under the shoulder. "
                        "Target, sixty seven sixty two. The head's depth, projected."),
    ("tp+0.4", "Target hit. Measured move complete."),
    ("end-2.5", "Real chart. Real dates. Same science."),
]


def main():
    sys.stdout.reconfigure(line_buffering=True)
    print("[bridge2]")
    oncamera("act2b", BRIDGE2)

    from chatterbox.tts import ChatterboxTTS
    tts = ChatterboxTTS.from_pretrained(device="cuda")
    print("[act3b vo]")
    synth_lines(ACT3, 24.0, os.path.join(PROBE, "act3b_vo.wav"), tts)

    ev = json.load(open(os.path.join(PROBE, "strategy_walkthrough2_props.json")))["event_times_s"]
    lines = []
    for spec, text in ACT4_SPECS:
        key, off = (spec.split("+") if "+" in spec else spec.split("-"))
        t = ev[key] + (float(off) if "+" in spec else -float(off))
        lines.append((t, text))
    print("[act4b vo]")
    synth_lines(sorted(lines), ev["end"], os.path.join(PROBE, "act4b_vo.wav"), tts)


if __name__ == "__main__":
    main()
