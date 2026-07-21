"""Unit tests for the manifest-driven reel assembler (scriptable Phase-2).

build_jobs is pure: it turns reels_manifest.json into make_reel.py command lists,
skipping entries whose hero/voice URLs are still placeholders (Phase-1 not done).
No subprocess, no ffmpeg, no network here.
"""
import sys
import pathlib

_HIGGS = pathlib.Path(__file__).resolve().parents[2] / "higgs"
if str(_HIGGS) not in sys.path:
    sys.path.insert(0, str(_HIGGS))

import make_reels_from_manifest as mr  # noqa: E402


VALID = {
    "date": "2026-06-27",
    "reels": [
        {"tk": "team", "hero": "https://cdn/x.mp4", "voice": "https://cdn/x.mp3"},
        {"tk": "QBTS", "hero": "https://cdn/y.mp4", "voice": "https://cdn/y.mp3"},
    ],
}


def test_build_jobs_emits_make_reel_commands_for_valid_entries():
    jobs, skipped = mr.build_jobs(VALID)
    assert skipped == []
    assert len(jobs) == 2
    # each job: [python, <make_reel.py>, TK(upper), hero, voice]
    j = jobs[0]
    assert j[1].endswith("make_reel.py")
    assert j[2] == "TEAM"  # uppercased
    assert j[3] == "https://cdn/x.mp4"
    assert j[4] == "https://cdn/x.mp3"


def test_build_jobs_skips_placeholder_urls():
    m = {"reels": [
        {"tk": "NVDA", "hero": "<hero_url>", "voice": "<voice_url>"},
        {"tk": "AMD", "hero": "https://cdn/a.mp4", "voice": "https://cdn/a.mp3"},
    ]}
    jobs, skipped = mr.build_jobs(m)
    assert [c[2] for c in jobs] == ["AMD"]
    assert [tk for tk, _ in skipped] == ["NVDA"]


def test_build_jobs_skips_missing_url_or_ticker():
    m = {"reels": [
        {"tk": "X", "hero": "https://cdn/x.mp4"},            # no voice
        {"hero": "https://cdn/y.mp4", "voice": "https://cdn/y.mp3"},  # no ticker
    ]}
    jobs, skipped = mr.build_jobs(m)
    assert jobs == []
    assert len(skipped) == 2


def test_build_jobs_accepts_bare_list_and_dict_forms():
    bare = VALID["reels"]
    assert len(mr.build_jobs(bare)[0]) == 2
    assert len(mr.build_jobs(VALID)[0]) == 2


def test_is_placeholder():
    assert mr.is_placeholder("<hero_url>")
    assert mr.is_placeholder("")
    assert mr.is_placeholder(None)
    assert mr.is_placeholder("not-a-url")
    assert not mr.is_placeholder("https://cdn/x.mp4")
