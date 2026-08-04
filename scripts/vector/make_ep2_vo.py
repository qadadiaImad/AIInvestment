"""All dialogue for episode 2, "Sixteen Minutes".

OPENS WITH A RECAP, per the owner: ep.2 starts with "last time we..."
and then introduces the new story. The recap is not just housekeeping -
it states ep.1's thesis (public, legal, 45 days late) so that ep.2 can
be its exact inverse: what it looks like when somebody is not late at
all. Rex delivers the callback line himself, which is also the joke,
because being late is precisely the mistake he made last episode.

ACCURACY RAILS - these lines were written against sourced reporting and
must not drift:
  * The traders are UNKNOWN. "Somebody" is the subject of every sentence
    about the trades. No official is named, depicted trading, or implied
    to be a suspect - no reporting connects any named official to them.
  * No charges have been filed in the oil case. The episode says so, out
    loud, twice, because that IS the story.
  * The one charged case (a service member indicted for trading a
    prediction market on classified intelligence about a different
    operation) is kept explicitly separate. It proves the mechanism is
    prosecutable; it is not evidence about the oil trades.
  * Every figure is from mainstream reporting or a congressional letter.

  python scripts/vector/make_ep2_vo.py
"""
from __future__ import annotations
import json, os, subprocess, sys, wave
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[2]
VO = REPO/'remotion'/'public'/'audio'/'fairmarket_ep2'
FIX = REPO/'remotion'/'src'/'fixtures'/'cast_ep1'
GROK = Path(os.path.expanduser('~/tools/grok-cli/grok-cli.exe'))
AUTH = Path(os.path.expanduser('~/.grok-cli/auth.json'))
FFMPEG = REPO/'remotion'/'node_modules'/'@remotion'/'compositor-win32-x64-msvc'/'ffmpeg.exe'
FPS = 30

LINES = [
    # ---- COLD OPEN: last time on ------------------------------------
    ("r1_sol_lasttime", "sal",
     "Last time, I showed you a filing. Public. Legal. Forty-five days late."),
    ("r2_rex_useless", "rex",
     "And useless if I tried to copy it."),
    ("r3_sol_otherside", "sal",
     "Late, kid. Not useless. Today I'll show you the other side of that. What it looks like when somebody isn't late at all."),
    # ---- ACT 1: the clock -------------------------------------------
    ("e1_sol_march", "sal",
     "March twenty-third. Six forty-nine in the morning."),
    ("e2_sol_buys", "sal",
     "Somebody buys five hundred and eighty million dollars of oil futures."),
    ("e3_rex_bullish", "rex",
     "Okay. Big trade. Somebody's feeling bullish."),
    ("e4_sol_no", "sal",
     "No. They were betting oil would fall. And stocks would rise."),
    # ---- ACT 2: sixteen minutes -------------------------------------
    ("e5_sol_sixteen", "sal",
     "Sixteen minutes later, the President posts that talks with Iran went well."),
    ("e6_sol_exactly", "sal",
     "Oil falls. Stocks rise. Exactly the way that trade was pointed."),
    ("e7_rex_coincidence", "rex",
     "That's a coincidence. Boss. Tell me that's a coincidence."),
    ("e8_sol_once", "sal",
     "Once is a coincidence, kid."),
    # ---- ACT 3: it happened again -----------------------------------
    ("e9_sol_again", "sal",
     "Two weeks later. Nine hundred and fifty million, betting oil falls. Hours before a ceasefire nobody had announced."),
    ("e10_sol_hormuz", "sal",
     "And another one. Seven hundred and sixty million, minutes before the Hormuz announcement."),
    ("e11_rex_total", "rex",
     "How much is that all together?"),
    ("e12_sol_billions", "sal",
     "The Justice Department and the CFTC are looking at about two point six billion."),
    ("e13_rex_caught", "rex",
     "So they caught them."),
    ("e14_sol_nope", "sal",
     "No."),
    # ---- ACT 4: nobody knows who ------------------------------------
    ("e15_sol_sitwith", "sal",
     "That's the part I need you to sit with. Not one charge. Not one name. The tape knew, and the tape doesn't sign its orders."),
    ("e16_rex_someone", "rex",
     "Somebody has to know something."),
    ("e17_sol_open", "sal",
     "Four members of Congress have written asking exactly that. The investigation is open. That's where it sits."),
    # ---- ACT 5: but they CAN catch you ------------------------------
    ("e18_sol_didcatch", "sal",
     "Now. They did catch one. Different war, same idea."),
    ("e19_sol_soldier", "sal",
     "A special forces soldier bet a prediction market on an operation he had been briefed on. Classified. Indicted."),
    ("e20_rex_provable", "rex",
     "So it is provable."),
    ("e21_sol_whentrail", "sal",
     "When the trail leads somewhere. Yes."),
    ("e22_rex_whennot", "rex",
     "And when it doesn't?"),
    ("e23_sol_clock", "sal",
     "Then all you have is the clock."),
    # ---- ACT 6: the lesson ------------------------------------------
    ("e24_sol_lastweek", "sal",
     "Last week I told you public information isn't enough to find an edge."),
    ("e25_sol_thisweek", "sal",
     "This week? Somebody had an edge sixteen minutes before the public had a headline."),
    ("e26_rex_sowhat", "rex",
     "So what do I do with that?"),
    ("e27_sol_newsfirst", "sal",
     "You stop assuming the news moves the market. Sometimes the market moves first, and the news catches up."),
    ("e28_sol_fair", "sal",
     "Fair? No. But now you know what to watch."),
]


def synth(stem, voice, text):
    raw = VO/f'_{stem}_g.wav'
    r = subprocess.run([str(GROK), 'tts', '--auth-file', str(AUTH),
                        '--voice-id', voice, '--output', str(raw),
                        '--output-format', 'wav', text],
                       capture_output=True, text=True)
    if r.returncode or not raw.exists():
        sys.exit(f'{stem}: {r.stdout}\n{r.stderr}')
    out = VO/f'{stem}.wav'
    subprocess.run([str(FFMPEG), '-v', 'error', '-i', str(raw), '-acodec',
                    'pcm_s16le', '-ar', '44100', '-ac', '1', str(out), '-y'],
                   check=True)
    raw.unlink(missing_ok=True)
    return out


def track(p):
    with wave.open(str(p)) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float)/32768
    step = max(1, sr//FPS)
    rms = np.array([float(np.sqrt((x[i:i+step]**2).mean()))
                    for i in range(0, len(x), step) if len(x[i:i+step])])
    ref = float(np.percentile(rms, 92)) or 1.0
    return [0 if v/ref < 0.16 else (1 if v/ref < 0.5 else 2) for v in rms]


def main():
    VO.mkdir(parents=True, exist_ok=True)
    f = FIX/'mouth_tracks_ep2.json'
    tracks = json.loads(f.read_text('utf-8')) if f.exists() else {}
    total = 0.0
    for stem, voice, text in LINES:
        p = synth(stem, voice, text)
        with wave.open(str(p)) as w:
            d = w.getnframes()/w.getframerate()
        tracks[stem] = track(p)
        total += d
        print(f'{stem:22s} {voice:4s} {d:5.2f}s {int(round(d*FPS)):4d}f  {text[:58]}',
              flush=True)
    f.write_text(json.dumps(tracks), 'utf-8')
    print(f'\n{len(LINES)} lines, {total:.1f}s of speech -> {VO}')
    print(f'with beat gaps that lands near {total*1.25:.0f}s')


if __name__ == '__main__':
    main()
