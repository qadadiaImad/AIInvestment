"""daily_post.py — The Daily Screen: one command, one ticker, one day's post.

    python daily_post.py [--auto] [--ticker X] [--dry-run] [--skip-refresh] [--skip-carousel]

Runs the full daily halal-screen content pipeline end to end:

  1. Freshness   — checks `web/public/data/halal.json`'s `generated_at`; refreshes
                    (pull_halal.py -> export_halal.py) if it's >=24h stale, unless
                    `--skip-refresh`.
  2. History      — loads yesterday's verdict snapshot, saves today's
                    (`data/halal_history/YYYY-MM-DD.json`).
  3. Candidates   — ranks today's top-3 stories (`aiinvest.daily_pick.rank_candidates`),
                    prints them, and picks one: `--ticker` forces a symbol, `--auto`
                    takes #1, otherwise an interactive prompt (Enter = 1).
  4. Copy         — builds the A/B hook props + caption (`aiinvest.daily_copy.build_daily`).
                    `--dry-run` stops here, printing both VO scripts + the caption, exit 0.
  5. Voice        — renders VO A/B via the local Chatterbox clone (karim_tts.py, chatterbox venv).
  6. Align        — faster-whisper word timestamps -> per-beat durations + captions
                    (`aiinvest.align_beats.apply_timing`); writes props_A.json/props_B.json,
                    then copies the rendered WAVs to `remotion/public/daily/<folder>/`
                    (Remotion's `voiceSrc` needs them there; `run_render` only asserts
                    they landed).
  7. Render       — `npx remotion render SlideStoryReel ...` for both variants.
  8. Carousel     — a minimal one-ticker kit md + `higgs/_build_v4.py` -> 3 PNGs.
                    Skipped (without failing the run) if `_build_v4.py` errors, or with
                    `--skip-carousel`.
  9. Finalize     — writes `manifest.json` into the temp folder, moves it to
                    `higgs/daily/YYYY-MM-DD_TICKER/` (the move is the last effectful
                    step, so it can't strand a manifest-less folder), then appends to
                    the posted log (a failure there is a warning, not a run failure --
                    the folder is already complete).

Every step prints one progress line. Any failure raises `DailyPostError` with a named
reason, aborts, and removes the temp working dir plus the `remotion/public/daily/<folder>/`
WAV copy if the align step had already created it (steps 1-4 run before any temp dir
exists, so a failure there has nothing to clean up).

`manifest.json` schema (see `build_manifest`):
    {
      "ticker": str, "date": "YYYY-MM-DD", "reason": str, "score": float | None,
      "story": dict | None,                # the halal_stories/daily_pick story dict, if any
      "generated_at": str,                 # halal.json's generated_at this post was built from
      "inputs_asof": str | None,           # this ticker's verdict inputs_asof
      "lint_ok": true,                     # build_daily raises LintError rather than return unvetted copy
      "seeds": {"tts_seed": 7},            # karim_tts.py's fixed Chatterbox seed
      "files": [str, ...],                 # filenames written into the folder
      "posting_instructions": "B = Trial Reel first, A = main slot",
      "carousel_note": str,                # present only if the carousel step was skipped/failed
    }

Educational/research only — not financial or religious advice.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
HIGGS = ROOT / "higgs"
REMOTION = ROOT / "remotion"
DATA = ROOT / "data"
WEB_DATA = ROOT / "web" / "public" / "data"
HALAL_HISTORY = DATA / "halal_history"
POSTED_LOG = HALAL_HISTORY / "posted_log.json"

# faster-whisper / chatterbox-tts live only in this venv, not the main repo venv.
CHATTERBOX_PYTHON = "C:/Users/Amsegt/.venvs/chatterbox/Scripts/python.exe"

# karim_tts.py's fixed generation seed (see scripts/voice/karim_tts.py SEED = 7).
TTS_SEED = 7

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from aiinvest import daily_pick, daily_copy  # noqa: E402
from aiinvest.align_beats import apply_timing  # noqa: E402


class DailyPostError(Exception):
    """Raised to abort the pipeline with a named reason. The caller removes any temp dir."""


# ---------------------------------------------------------------------------
# Pure helpers — no I/O, no subprocess. TDD'd in scripts/tests/test_daily_post.py.
# ---------------------------------------------------------------------------

def folder_name(date_str, ticker):
    """`YYYY-MM-DD_TICKER` — the folder name Studio indexes under higgs/daily/."""
    return f"{date_str}_{ticker.upper()}"


def format_candidates(candidates):
    """Numbered, one-line-per-candidate string for the interactive prompt."""
    lines = []
    for i, c in enumerate(candidates, start=1):
        score = c.get("score")
        score_str = f"{score:.2f}" if isinstance(score, (int, float)) else "n/a"
        lines.append(f"{i}. {c['symbol']}  (score {score_str}) -- {c['reason']}")
    return "\n".join(lines)


def choose_candidate(candidates, ticker=None, auto=False, input_func=input):
    """Pick one of `rank_candidates`'s top-3.

    `ticker` forces a symbol — if it matches an existing candidate that entry is
    returned as-is (keeping its story/score/reason), otherwise a synthetic
    `{"symbol", "score": None, "reason": "manually selected via --ticker",
    "story": None}` is returned so the caller can still build copy for it.
    `auto` takes candidates[0]. Otherwise prompts via `input_func`
    (Enter/blank/unparsable/out-of-range all clamp into range, default = #1).
    """
    if ticker:
        ticker = ticker.upper()
        match = next((c for c in candidates if c["symbol"].upper() == ticker), None)
        if match is not None:
            return match
        return {"symbol": ticker, "score": None,
                "reason": "manually selected via --ticker", "story": None}
    if auto:
        return candidates[0]

    try:
        raw = (input_func("Pick 1-3 [Enter=1]: ") or "").strip()
    except (EOFError, KeyboardInterrupt):
        raise DailyPostError(
            "candidates: no interactive input available (stdin closed) -- "
            "pass --auto or --ticker in non-interactive contexts")
    idx = 0
    if raw:
        try:
            idx = int(raw) - 1
        except ValueError:
            idx = 0
    idx = max(0, min(idx, len(candidates) - 1))
    return candidates[idx]


def read_generated_at(halal_path):
    """halal.json's `generated_at`, or None if the file is missing/unreadable."""
    p = pathlib.Path(halal_path)
    if not p.exists():
        return None
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return doc.get("generated_at") if isinstance(doc, dict) else None


def is_stale(generated_at, now, max_age_hours=24):
    """True if `generated_at` is missing, unparsable, or >= `max_age_hours` old."""
    if not generated_at:
        return True
    try:
        ts = dt.datetime.fromisoformat(str(generated_at).strip().replace("Z", "+00:00"))
    except ValueError:
        return True
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=dt.timezone.utc)
    now_aware = now if now.tzinfo is not None else now.replace(tzinfo=dt.timezone.utc)
    return (now_aware - ts) >= dt.timedelta(hours=max_age_hours)


def load_news_bundle(path):
    """web/public/data/news.json-shaped dict, or None if missing/malformed."""
    p = pathlib.Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def build_manifest(*, ticker, reason, score, story, bundle, date_str, seeds, files):
    """Assemble `manifest.json`'s content for a finished daily-post folder. Pure."""
    verdict = ((bundle or {}).get("verdicts") or {}).get(ticker) or {}
    return {
        "ticker": ticker,
        "date": date_str,
        "reason": reason,
        "score": score,
        "story": story,
        "generated_at": (bundle or {}).get("generated_at"),
        "inputs_asof": verdict.get("inputs_asof"),
        "lint_ok": True,  # build_daily raises LintError rather than return unvetted copy
        "seeds": seeds,
        "files": files,
        "posting_instructions": "B = Trial Reel first, A = main slot",
    }


def write_manifest(tmp_dir, manifest):
    """Write `manifest.json` into `tmp_dir` -- BEFORE the temp-dir-to-`higgs/daily/`
    move, so `finalize` (the move) is the last effectful step in the pipeline. This
    means a failure after this point (e.g. `finalize` itself, or `append_posted`)
    can never strand a manifest-less folder: either the folder doesn't exist yet
    (temp dir, cleaned up by the caller) or it exists complete with its manifest.
    Returns the written path.
    """
    tmp_dir = pathlib.Path(tmp_dir)
    p = tmp_dir / "manifest.json"
    p.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return p


# --- carousel kit-md assembly (pure) -------------------------------------------

_KIT_FIELD_ORDER = [
    "hero", "logo", "ex", "kick", "head", "sub",
    "data_kick", "data_title", "data_cap", "data_foot", "mode",
    "screen_head", "screen_body", "screen_body2",
    "tk_kick", "big", "unit", "tk_label", "tk_body",
    "src", "halal_script",
]


def carousel_fields(ticker, kit_fields, copy_result, reason, date_str):
    """The `_KIT_FIELD_ORDER` CFG fields for a minimal one-ticker carousel kit.

    Pulls the specific-number hook (headline + sub) from `props_a`'s beat 0 and the
    screen-card copy from `daily_copy.build_daily`'s `kit_fields`. Hero/logo point at
    filenames that likely don't exist for an ad-hoc daily ticker -- `_build_v4.py`
    already degrades that to a solid-background fallback with a WARN, so this is
    intentional, not a bug.
    """
    hook = copy_result["props_a"]["beats"][0]
    return {
        "hero": f"hero_{ticker.lower()}_{date_str}.png",
        "logo": f"logo_{ticker.upper()}.png",
        "ex": "",
        "kick": "THE DAILY SCREEN",
        "head": hook.get("headline") or "",
        "sub": hook.get("sub") or "",
        "data_kick": "", "data_title": "", "data_cap": "", "data_foot": "", "mode": "disc",
        "screen_head": kit_fields["screen_head"],
        "screen_body": kit_fields["screen_body"],
        "screen_body2": kit_fields["screen_body2"],
        "tk_kick": "THE VERDICT",
        "big": "", "unit": "",
        "tk_label": "AAOIFI SCREEN VERDICT",
        "tk_body": reason or "",
        "src": "site",
        "halal_script": kit_fields["halal_script"],
    }


def _escape_kit_value(s):
    return str(s or "").replace("\\", "\\\\").replace('"', '\\"')


def build_kit_md(ticker, fields, date_str):
    """Minimal one-ticker `reels_<date>_kit.md`-shaped CFG block for `higgs/_build_v4.py`.

    Mirrors `higgs/reels_2026-07-21_kit.md`'s format closely enough for
    `aiinvest.kit_md.parse_cfg` to read it (that's the only contract that matters --
    `_build_v4.py` reads through `parse_cfg`, not the surrounding markdown prose).
    `fields` must carry every key in `_KIT_FIELD_ORDER` (see `carousel_fields`).
    """
    ticker = ticker.upper()
    field_lines = ",\n".join(
        f'   "{k}":"{_escape_kit_value(fields[k])}"' for k in _KIT_FIELD_ORDER)
    cfg = f' "{ticker}":{{\n{field_lines},\n   "rows":[]\n }}'
    return (
        f"# Reel KIT — {date_str} (The Daily Screen, auto-generated single-ticker kit)\n\n"
        f"## REEL 1 — {ticker} (THE DAILY SCREEN)\n\n"
        "**CFG block:**\n```python\n"
        f"{cfg}\n"
        "```\n"
    )


# ---------------------------------------------------------------------------
# Subprocess-driving steps — each isolated in its own small function so the
# pure helpers above stay importable/testable without a GPU or any process spawn.
# ---------------------------------------------------------------------------

def _tee_pipe(pipe, sink, out_stream):
    """Read `pipe` line-by-line until EOF, appending each line to `sink` (a list)
    and writing it straight to `out_stream` as it arrives. Runs in its own thread
    (one per stream) so stdout and stderr can be drained -- and echoed live -- at
    the same time without either one blocking on the other's OS pipe buffer.

    Wrapped in a broad try/except: if the reader itself ever throws (e.g. a
    decoding error slipping past the parent's `errors="replace"`, or a write
    failure on `out_stream`), a crash here must NOT leave `pipe` undrained --
    an undrained OS pipe fills its buffer and deadlocks the child process
    (this is exactly what happened with tqdm progress bytes from Chatterbox
    TTS before the parent `Popen` call was given an explicit UTF-8 decode).
    On any reader error we record the error into `sink` and fall back to a
    binary-blind drain of whatever remains on the pipe, so the child can
    always finish writing and exit.
    """
    try:
        for line in iter(pipe.readline, ""):
            sink.append(line)
            out_stream.write(line)
            out_stream.flush()
    except Exception as e:
        sink.append(f"\n[_tee_pipe reader error: {e!r} -- draining remainder binary-blind]\n")
        try:
            raw = getattr(pipe, "buffer", pipe)
            while True:
                chunk = raw.read(65536)
                if not chunk:
                    break
        except Exception:
            pass
    finally:
        try:
            pipe.close()
        except Exception:
            pass


def _run_and_echo(cmd, cwd, env, shell=False):
    """Run `cmd` via `Popen`, streaming stdout and stderr to the console *live*
    (line-by-line, as each stream produces output) while also buffering both so
    the result exposes `.returncode`/`.stdout`/`.stderr` like `subprocess.run`'s
    `CompletedProcess` -- which is what `_stderr_tail` and the failure-message
    callers here rely on. Two reader threads (one per stream) drain stdout/stderr
    concurrently so a chatty stderr can't stall stdout's echo (or vice versa)
    behind the OS pipe buffer.

    `encoding="utf-8", errors="replace"` (instead of the platform default --
    cp1252 on Windows) is load-bearing: tqdm progress bars (e.g. Chatterbox
    TTS) emit multi-byte UTF-8 (box-drawing/block characters) on stdout that
    isn't valid cp1252. Without an explicit encoding, decoding that raises
    inside the reader thread, the thread dies uncaught, its pipe is never
    drained again, the OS pipe buffer fills, and the GPU child deadlocks
    writing to a full pipe. UTF-8 decodes those bytes cleanly; `errors="replace"`
    is a second line of defense for anything still undecodable.
    """
    proc = subprocess.Popen(
        cmd, cwd=str(cwd), env=env, shell=shell,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", bufsize=1,
    )
    stdout_lines = []
    stderr_lines = []
    t_out = threading.Thread(target=_tee_pipe, args=(proc.stdout, stdout_lines, sys.stdout))
    t_err = threading.Thread(target=_tee_pipe, args=(proc.stderr, stderr_lines, sys.stderr))
    t_out.start()
    t_err.start()
    t_out.join()
    t_err.join()
    proc.wait()
    return subprocess.CompletedProcess(
        cmd, proc.returncode, "".join(stdout_lines), "".join(stderr_lines))


def _stderr_tail(proc, n=400):
    """Last `n` chars of `proc`'s stderr (falls back to stdout), for error messages."""
    tail = (proc.stderr or proc.stdout or "").strip()
    return tail[-n:]


def run_refresh(python_exe=None, cwd=SCRIPTS):
    """pull_halal.py then export_halal.py, cwd=scripts, PYTHONIOENCODING=utf-8."""
    python_exe = python_exe or sys.executable
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for script in ("pull_halal.py", "export_halal.py"):
        proc = _run_and_echo([python_exe, script], cwd=cwd, env=env)
        if proc.returncode != 0:
            raise DailyPostError(
                f"refresh: {script} failed (exit {proc.returncode}): {_stderr_tail(proc)}")


def _vo_script(vo_lines):
    """All VO lines joined with blank lines, per the task-6 brief."""
    return "\n\n".join(vo_lines)


def run_tts(tmp_dir, copy_result, python_exe=CHATTERBOX_PYTHON):
    """Write daily_a.txt/daily_b.txt, run karim_tts.py --text-file per variant.

    Returns {"daily_a": Path, "daily_b": Path} to the rendered WAVs
    (karim_tts.py writes `voice_<name-lower>.wav` into --out).
    """
    karim_tts = ROOT / "scripts" / "voice" / "karim_tts.py"
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    wavs = {}
    for name, props_key in (("daily_a", "props_a"), ("daily_b", "props_b")):
        txt_path = tmp_dir / f"{name}.txt"
        txt_path.write_text(_vo_script(copy_result[props_key]["vo"]), encoding="utf-8")
        cmd = [python_exe, str(karim_tts), "--text-file", name, str(txt_path), "--out", str(tmp_dir)]
        proc = _run_and_echo(cmd, cwd=ROOT, env=env)
        if proc.returncode != 0:
            raise DailyPostError(
                f"voice: karim_tts.py failed for {name} (exit {proc.returncode}): {_stderr_tail(proc)}")
        wav_path = tmp_dir / f"voice_{name}.wav"
        if not wav_path.exists():
            raise DailyPostError(f"voice: expected {wav_path} was not written")
        wavs[name] = wav_path
    return wavs


def run_align(tmp_dir, folder, copy_result, wavs, python_exe=CHATTERBOX_PYTHON, side_effect_dirs=None):
    """whisper_align.py per WAV -> align_beats.apply_timing per variant.

    Writes props_A.json/props_B.json (with `voiceSrc` set) into `tmp_dir`. Also
    copies the WAVs to `remotion/public/daily/<folder>/` (this is the align step
    per the brief's step numbering; `run_render` only asserts they landed).
    `dest_voice_dir` is appended to `side_effect_dirs` (if given) right after
    it's created, so a caller-owned cleanup handler can remove it on any later
    pipeline failure without orphaning WAV copies outside git's view.
    Returns {"A": props_dict, "B": props_dict}.
    """
    whisper_align = ROOT / "scripts" / "voice" / "whisper_align.py"
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    props_out = {}
    for variant, name, props_key in (("A", "daily_a", "props_a"), ("B", "daily_b", "props_b")):
        wav_path = wavs[name]
        words_path = tmp_dir / f"words_{variant}.json"
        cmd = [python_exe, str(whisper_align), str(wav_path), "--out", str(words_path)]
        proc = _run_and_echo(cmd, cwd=ROOT, env=env)
        if proc.returncode != 0:
            raise DailyPostError(
                f"align: whisper_align.py failed for {variant} (exit {proc.returncode}): {_stderr_tail(proc)}")
        words = json.loads(words_path.read_text(encoding="utf-8"))
        props = apply_timing(copy_result[props_key], words)
        props["voiceSrc"] = f"daily/{folder}/voice_{variant}.wav"
        (tmp_dir / f"props_{variant}.json").write_text(json.dumps(props, indent=2), encoding="utf-8")
        props_out[variant] = props

    dest_voice_dir = REMOTION / "public" / "daily" / folder
    dest_voice_dir.mkdir(parents=True, exist_ok=True)
    if side_effect_dirs is not None:
        side_effect_dirs.append(dest_voice_dir)
    shutil.copy2(wavs["daily_a"], dest_voice_dir / "voice_A.wav")
    shutil.copy2(wavs["daily_b"], dest_voice_dir / "voice_B.wav")
    return props_out


def run_render(tmp_dir, folder, props_out):
    """`npx remotion render` A/B, after asserting `run_align`'s WAV copies landed."""
    dest_voice_dir = REMOTION / "public" / "daily" / folder
    for variant in ("A", "B"):
        wav_path = dest_voice_dir / f"voice_{variant}.wav"
        if not wav_path.exists():
            raise DailyPostError(f"render: expected {wav_path} was not written by the align step")

    outputs = {}
    for variant in ("A", "B"):
        props_path = tmp_dir / f"props_{variant}.json"
        out_mp4 = tmp_dir / f"daily_{variant}.mp4"
        cmd = f'npx remotion render SlideStoryReel "{out_mp4}" --props="{props_path}"'
        proc = _run_and_echo(cmd, cwd=REMOTION, env=os.environ.copy(), shell=True)
        if proc.returncode != 0:
            raise DailyPostError(
                f"render: remotion render failed for {variant} (exit {proc.returncode}): {_stderr_tail(proc)}")
        if not out_mp4.exists():
            raise DailyPostError(f"render: expected {out_mp4} was not written")
        outputs[variant] = out_mp4
    return outputs


def run_carousel(tmp_dir, ticker, kit_fields, copy_result, reason, date_str, python_exe=None):
    """Emit a minimal one-ticker kit md and invoke `higgs/_build_v4.py` on it.

    Never raises: `_build_v4.py` failing (missing site/quantum bundles, Playwright
    absent, etc.) or producing fewer than 3 PNGs degrades to a named note + whatever
    was collected, so a carousel problem never fails the whole daily post.
    Returns (note_or_None, [Path, ...] of collected PNGs moved into tmp_dir).
    """
    python_exe = python_exe or sys.executable
    fields = carousel_fields(ticker, kit_fields, copy_result, reason, date_str)
    kit_md = build_kit_md(ticker, fields, date_str)
    kit_path = tmp_dir / f"daily_kit_{ticker.upper()}.md"
    kit_path.write_text(kit_md, encoding="utf-8")

    cmd = [python_exe, str(HIGGS / "_build_v4.py"), "--kit", str(kit_path)]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip()[-500:]
        note = f"carousel skipped: _build_v4.py exited {proc.returncode}: {tail}"
        print(f"  WARN {note}")
        return note, []

    tkl = ticker.lower()
    names = [f"v4_{tkl}_1_hook.png", f"v4_{tkl}_2_data.png", f"v4_{tkl}_3_takeaway.png"]
    collected = []
    for name in names:
        src = HIGGS / name
        if not src.exists():
            continue
        dest = tmp_dir / name
        shutil.move(str(src), str(dest))
        collected.append(dest)
    if len(collected) < 3:
        note = f"carousel skipped: expected 3 PNGs, found {len(collected)}"
        print(f"  WARN {note}")
        return note, collected
    return None, collected


def cleanup_dirs(tmp_dir, side_effect_dirs):
    """Remove `tmp_dir` and every dir in `side_effect_dirs`, best-effort (missing
    or locked paths are ignored, mirroring `shutil.rmtree(..., ignore_errors=True)`).

    Called from `run()`'s cleanup handler on ANY exception that escapes the wet
    steps -- including `KeyboardInterrupt`/`SystemExit` (i.e. `BaseException`, not
    just `Exception`). A Ctrl-C during TTS/whisper/render must not skip cleanup:
    besides orphaning `tmp_dir`, a stranded `remotion/public/daily/<folder>/` would
    still hold the WAVs `run_align` copied there, and those stale files would
    silently satisfy `run_render`'s existence assert on a same-day retry -- making
    the retry render with yesterday's voice track instead of failing loudly.
    """
    shutil.rmtree(tmp_dir, ignore_errors=True)
    for d in side_effect_dirs:
        shutil.rmtree(d, ignore_errors=True)


def finalize(tmp_dir, dest_dir):
    """Move `tmp_dir`'s contents into `dest_dir` (must not already exist). Returns
    the sorted list of filenames now in `dest_dir`."""
    dest_dir = pathlib.Path(dest_dir)
    if dest_dir.exists():
        raise DailyPostError(f"finalize: destination already exists: {dest_dir}")
    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(tmp_dir), str(dest_dir))
    return sorted(p.name for p in dest_dir.iterdir())


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run(args, now=None, input_func=input):
    now = now or dt.datetime.now(dt.timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    halal_path = WEB_DATA / "halal.json"

    print("[1/9] freshness: checking web/public/data/halal.json ...")
    generated_at = read_generated_at(halal_path)
    if is_stale(generated_at, now) and not args.skip_refresh:
        print(f"  stale (generated_at={generated_at!r}) -- refreshing (pull_halal.py + export_halal.py) ...")
        run_refresh()
        generated_at = read_generated_at(halal_path)
        if is_stale(generated_at, now):
            raise DailyPostError(f"halal.json still stale after refresh (generated_at={generated_at!r})")
    if generated_at is None:
        raise DailyPostError(f"halal.json missing or unreadable at {halal_path}")
    bundle = json.loads(halal_path.read_text(encoding="utf-8"))
    print(f"  OK generated_at={generated_at}")

    print("[2/9] history: loading yesterday's snapshot, saving today's ...")
    prev_map, prev_date = daily_pick.load_history(HALAL_HISTORY)
    daily_pick.save_snapshot(HALAL_HISTORY, date_str, daily_pick.verdict_map(bundle))
    print(f"  OK prev_date={prev_date}")

    print("[3/9] candidates: ranking today's top-3 ...")
    news_bundle = load_news_bundle(WEB_DATA / "news.json")
    posted_log = daily_pick.load_posted_log(POSTED_LOG)
    candidates = daily_pick.rank_candidates(bundle, prev_map, news_bundle, posted_log, now)
    if not candidates:
        raise DailyPostError("no candidates ranked -- nothing to post today")
    print(format_candidates(candidates))
    chosen = choose_candidate(candidates, ticker=args.ticker, auto=args.auto, input_func=input_func)
    ticker = chosen["symbol"].upper()
    print(f"  picked {ticker}")

    print("[4/9] copy: building A/B hook props + caption ...")
    try:
        copy_result = daily_copy.build_daily(ticker, bundle, chosen.get("story"), date_str)
    except daily_copy.InsufficientDataError as e:
        raise DailyPostError(f"copy: insufficient data for {ticker}: {e}")
    except daily_copy.LintError as e:
        raise DailyPostError(f"copy: lint failed for {ticker}: {'; '.join(e.violations)}")
    print("  --- VO A ---\n" + "\n".join(copy_result["props_a"]["vo"]))
    print("  --- VO B ---\n" + "\n".join(copy_result["props_b"]["vo"]))
    print("  --- caption ---\n" + copy_result["caption"])

    if args.dry_run:
        print("[dry-run] stopping after copy build.")
        return 0

    folder = folder_name(date_str, ticker)
    tmp_dir = pathlib.Path(tempfile.mkdtemp(prefix="daily_post_"))
    # Side-effect dirs created outside tmp_dir (currently just the WAV copies under
    # remotion/public/daily/<folder>/, written by run_align) -- tracked here so any
    # failure past that point cleans them up too, instead of orphaning them (that
    # path isn't gitignored, so a leftover dir would pollute git status).
    side_effect_dirs = []
    try:
        print("[5/9] voice: rendering VO A/B via Chatterbox (karim_tts.py) ...")
        wavs = run_tts(tmp_dir, copy_result)

        print("[6/9] align: whisper word-timestamps -> beat timing (+ WAV copy to remotion/public/) ...")
        props_out = run_align(tmp_dir, folder, copy_result, wavs, side_effect_dirs=side_effect_dirs)

        print("[7/9] render: SlideStoryReel A/B via remotion ...")
        run_render(tmp_dir, folder, props_out)

        carousel_note = None
        if args.skip_carousel:
            print("[8/9] carousel: skipped (--skip-carousel)")
        else:
            print("[8/9] carousel: building 3 PNGs via higgs/_build_v4.py ...")
            carousel_note, _pngs = run_carousel(
                tmp_dir, ticker, copy_result["kit_fields"], copy_result, chosen["reason"], date_str)

        print("[9/9] finalize: writing manifest, moving folder, updating posted log ...")
        files = sorted(p.name for p in tmp_dir.iterdir())
        manifest = build_manifest(
            ticker=ticker, reason=chosen["reason"], score=chosen.get("score"),
            story=chosen.get("story"), bundle=bundle, date_str=date_str,
            seeds={"tts_seed": TTS_SEED}, files=files + ["manifest.json"])
        if carousel_note:
            manifest["carousel_note"] = carousel_note
        write_manifest(tmp_dir, manifest)  # written pre-move: the move below is now the last effectful step

        dest = HIGGS / "daily" / folder
        finalize(tmp_dir, dest)

        try:
            daily_pick.append_posted(POSTED_LOG, {"symbol": ticker, "date": date_str, "folder": folder})
        except Exception as e:
            # The folder itself (dest) is already complete and valid -- manifest.json
            # was written before the move above -- so a posted-log write failure here
            # is a warning, not a run failure.
            print(f"  WARN append_posted failed (folder is complete and valid): {e}")

        print(f"  OK wrote {dest}")
        return 0
    except BaseException:
        # BaseException (not just Exception): KeyboardInterrupt/SystemExit during
        # the long wet steps (TTS/whisper/render) must still trigger cleanup --
        # see cleanup_dirs's docstring for why an orphaned side-effect dir is
        # actively dangerous, not just untidy.
        cleanup_dirs(tmp_dir, side_effect_dirs)
        raise


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--auto", action="store_true", help="pick the top-ranked candidate, no prompt")
    ap.add_argument("--ticker", help="force a specific ticker (bypasses ranking/prompt)")
    ap.add_argument("--dry-run", action="store_true",
                    help="stop after building copy; print VO+caption; exit 0 (no GPU touched)")
    ap.add_argument("--skip-refresh", action="store_true",
                    help="skip the pull_halal.py/export_halal.py refresh even if halal.json is stale")
    ap.add_argument("--skip-carousel", action="store_true", help="skip the carousel PNG build step")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        return run(args)
    except DailyPostError as e:
        print(f"ABORT: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
