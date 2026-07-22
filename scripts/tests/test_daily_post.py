# scripts/tests/test_daily_post.py — pure-helper tests for the daily_post.py
# orchestrator (The Daily Screen, task 6). No GPU, no subprocess, no network:
# only the pure assembly/formatting helpers are exercised here. The
# subprocess-driving steps (voice/align/render/carousel) are isolated in
# their own small functions in daily_post.py precisely so they stay OUT of
# this file's import/collection path.
import datetime as dt
import json

import pytest

import daily_post


# --- folder_name -------------------------------------------------------------

def test_folder_name_uppercases_ticker():
    assert daily_post.folder_name("2026-07-22", "wulf") == "2026-07-22_WULF"


def test_folder_name_already_upper():
    assert daily_post.folder_name("2026-07-22", "GEV") == "2026-07-22_GEV"


# --- format_candidates ---------------------------------------------------------

def _candidates():
    return [
        {"symbol": "WULF", "score": 12.5, "reason": "verdict flipped questionable -> not_halal"},
        {"symbol": "GEV", "score": 3.0, "reason": "GEV selected for today's screen."},
        {"symbol": "ETN", "score": 1.0, "reason": "ETN selected to keep rotation fresh."},
    ]


def test_format_candidates_three_lines():
    out = daily_post.format_candidates(_candidates())
    lines = out.splitlines()
    assert len(lines) == 3


def test_format_candidates_numbered_and_carries_symbol_and_reason():
    lines = daily_post.format_candidates(_candidates()).splitlines()
    assert lines[0].startswith("1.") and "WULF" in lines[0] and "flipped" in lines[0]
    assert lines[1].startswith("2.") and "GEV" in lines[1]
    assert lines[2].startswith("3.") and "ETN" in lines[2]


def test_format_candidates_handles_missing_score():
    out = daily_post.format_candidates([{"symbol": "AAA", "score": None, "reason": "r"}])
    assert "AAA" in out and "n/a" in out


# --- build_manifest ------------------------------------------------------------

def _bundle():
    return {
        "generated_at": "2026-07-22T09:48:24Z",
        "verdicts": {"WULF": {"inputs_asof": "2026-07-21T13:07:37Z"}},
    }


def test_build_manifest_field_presence():
    m = daily_post.build_manifest(
        ticker="WULF", reason="verdict flipped", score=12.5, story={"kind": "flip"},
        bundle=_bundle(), date_str="2026-07-22", seeds={"tts_seed": 7},
        files=["daily_A.mp4", "daily_B.mp4", "manifest.json"],
    )
    for key in ("ticker", "date", "reason", "score", "story", "generated_at",
                "inputs_asof", "lint_ok", "seeds", "files", "posting_instructions"):
        assert key in m, f"manifest missing {key!r}"


def test_build_manifest_pulls_generated_at_and_inputs_asof_from_bundle():
    m = daily_post.build_manifest(
        ticker="WULF", reason="r", score=1.0, story=None, bundle=_bundle(),
        date_str="2026-07-22", seeds={}, files=[],
    )
    assert m["generated_at"] == "2026-07-22T09:48:24Z"
    assert m["inputs_asof"] == "2026-07-21T13:07:37Z"
    assert m["ticker"] == "WULF" and m["date"] == "2026-07-22"
    assert m["lint_ok"] is True


def test_build_manifest_posting_instructions_name_b_first_a_main():
    m = daily_post.build_manifest(
        ticker="WULF", reason="r", score=1.0, story=None, bundle=_bundle(),
        date_str="2026-07-22", seeds={}, files=[],
    )
    instr = m["posting_instructions"]
    assert "B" in instr and "Trial Reel" in instr
    assert "A" in instr and "main slot" in instr


def test_build_manifest_missing_verdict_degrades_to_none_inputs_asof():
    m = daily_post.build_manifest(
        ticker="ZZZZ", reason="r", score=1.0, story=None, bundle=_bundle(),
        date_str="2026-07-22", seeds={}, files=[],
    )
    assert m["inputs_asof"] is None


# --- is_stale / read_generated_at ----------------------------------------------

def test_is_stale_missing_generated_at():
    assert daily_post.is_stale(None, dt.datetime(2026, 7, 22, tzinfo=dt.timezone.utc)) is True


def test_is_stale_fresh_within_24h():
    now = dt.datetime(2026, 7, 22, 12, 0, tzinfo=dt.timezone.utc)
    assert daily_post.is_stale("2026-07-22T09:00:00Z", now) is False


def test_is_stale_older_than_24h():
    now = dt.datetime(2026, 7, 23, 12, 0, tzinfo=dt.timezone.utc)
    assert daily_post.is_stale("2026-07-22T09:00:00Z", now) is True


def test_is_stale_unparsable_value_is_stale():
    now = dt.datetime(2026, 7, 22, 12, 0, tzinfo=dt.timezone.utc)
    assert daily_post.is_stale("not-a-date", now) is True


def test_read_generated_at_missing_file(tmp_path):
    assert daily_post.read_generated_at(tmp_path / "nope.json") is None


def test_read_generated_at_reads_field(tmp_path):
    p = tmp_path / "halal.json"
    p.write_text('{"generated_at": "2026-07-22T09:48:24Z"}', encoding="utf-8")
    assert daily_post.read_generated_at(p) == "2026-07-22T09:48:24Z"


# --- choose_candidate -----------------------------------------------------------

def _plain_candidates():
    return [
        {"symbol": "A", "score": 2, "reason": "x", "story": None},
        {"symbol": "B", "score": 1, "reason": "y", "story": None},
        {"symbol": "C", "score": 0, "reason": "z", "story": None},
    ]


def test_choose_candidate_auto_picks_first():
    picked = daily_post.choose_candidate(_plain_candidates(), ticker=None, auto=True)
    assert picked["symbol"] == "A"


def test_choose_candidate_ticker_override_matches_existing_candidate():
    picked = daily_post.choose_candidate(_plain_candidates(), ticker="b", auto=False)
    assert picked["symbol"] == "B" and picked["reason"] == "y"


def test_choose_candidate_ticker_override_not_in_list_synthesizes_entry():
    picked = daily_post.choose_candidate(_plain_candidates(), ticker="ZZZZ", auto=False)
    assert picked["symbol"] == "ZZZZ"
    assert picked["score"] is None
    assert picked["story"] is None


def test_choose_candidate_interactive_enter_defaults_to_first():
    picked = daily_post.choose_candidate(
        _plain_candidates(), ticker=None, auto=False, input_func=lambda prompt="": "")
    assert picked["symbol"] == "A"


def test_choose_candidate_interactive_explicit_pick():
    picked = daily_post.choose_candidate(
        _plain_candidates(), ticker=None, auto=False, input_func=lambda prompt="": "2")
    assert picked["symbol"] == "B"


def test_choose_candidate_interactive_out_of_range_clamps():
    picked = daily_post.choose_candidate(
        _plain_candidates(), ticker=None, auto=False, input_func=lambda prompt="": "99")
    assert picked["symbol"] == "C"


def test_choose_candidate_eof_on_closed_stdin_aborts_via_daily_post_error():
    def _closed_stdin(prompt=""):
        raise EOFError()

    with pytest.raises(daily_post.DailyPostError) as exc:
        daily_post.choose_candidate(
            _plain_candidates(), ticker=None, auto=False, input_func=_closed_stdin)
    msg = str(exc.value)
    assert "--auto" in msg and "--ticker" in msg


def test_choose_candidate_keyboard_interrupt_aborts_via_daily_post_error():
    def _ctrl_c(prompt=""):
        raise KeyboardInterrupt()

    with pytest.raises(daily_post.DailyPostError):
        daily_post.choose_candidate(
            _plain_candidates(), ticker=None, auto=False, input_func=_ctrl_c)


def test_choose_candidate_auto_never_touches_input_func():
    def _boom(prompt=""):
        raise EOFError()

    # --auto short-circuits before input_func is ever called, so a closed stdin
    # must not matter in that path.
    picked = daily_post.choose_candidate(_plain_candidates(), ticker=None, auto=True, input_func=_boom)
    assert picked["symbol"] == "A"


# --- carousel_fields / build_kit_md --------------------------------------------

def _fake_copy_result():
    return {
        "props_a": {"beats": [
            {"kind": "hook", "headline": "$57 of every $100 here is borrowed money.",
             "sub": "Muslim investors run a halal screen — watch it work."},
        ]},
        "kit_fields": {
            "screen_head": "WULF: the halal screen, plain-English.",
            "screen_body": "$57 of every $100 here sits in interest-bearing debt.",
            "screen_body2": "Three independent rulebooks each ran the same numbers.",
            "halal_script": "TeraWulf runs A-I datacenters now. Educational, not financial or religious advice.",
        },
    }


def test_carousel_fields_carries_kit_fields_through():
    fields = daily_post.carousel_fields(
        "WULF", _fake_copy_result()["kit_fields"], _fake_copy_result(), "reason text", "2026-07-22")
    assert fields["screen_head"] == "WULF: the halal screen, plain-English."
    assert fields["halal_script"].startswith("TeraWulf")
    assert fields["head"] == "$57 of every $100 here is borrowed money."


def test_build_kit_md_round_trips_through_kit_md_parser():
    from aiinvest.kit_md import parse_cfg

    copy_result = _fake_copy_result()
    fields = daily_post.carousel_fields(
        "WULF", copy_result["kit_fields"], copy_result, "some reason", "2026-07-22")
    md = daily_post.build_kit_md("WULF", fields, "2026-07-22")

    cfg = parse_cfg(md, "WULF")
    assert cfg is not None
    assert cfg["screen_head"] == fields["screen_head"]
    assert cfg["screen_body2"] == fields["screen_body2"]
    assert cfg["halal_script"] == fields["halal_script"]
    assert cfg["hook"]["head"] == fields["head"]


def test_build_kit_md_escapes_embedded_quotes():
    from aiinvest.kit_md import parse_cfg

    copy_result = _fake_copy_result()
    fields = daily_post.carousel_fields(
        "WULF", copy_result["kit_fields"], copy_result, 'a "quoted" reason', "2026-07-22")
    fields["tk_body"] = 'contains a "quote" mid-sentence'
    md = daily_post.build_kit_md("WULF", fields, "2026-07-22")

    cfg = parse_cfg(md, "WULF")
    assert cfg is not None
    assert cfg["takeaway"]["body"] == 'contains a "quote" mid-sentence'


# --- write_manifest / finalize: manifest lands before the move -----------------

def test_write_manifest_writes_into_tmp_dir(tmp_path):
    tmp_dir = tmp_path / "work"
    tmp_dir.mkdir()
    (tmp_dir / "daily_A.mp4").write_bytes(b"x")

    manifest = daily_post.build_manifest(
        ticker="WULF", reason="r", score=1.0, story=None, bundle={},
        date_str="2026-07-22", seeds={"tts_seed": 7}, files=["daily_A.mp4", "manifest.json"])
    path = daily_post.write_manifest(tmp_dir, manifest)

    assert path == tmp_dir / "manifest.json"
    assert path.exists()
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["ticker"] == "WULF"
    assert written["files"] == ["daily_A.mp4", "manifest.json"]


def test_write_manifest_happens_before_finalize_moves_the_folder(tmp_path):
    """The pipeline's real contract: write_manifest(tmp_dir, ...) then finalize(tmp_dir,
    dest) -- manifest.json must already be inside tmp_dir when the move (finalize)
    happens, so a finalize failure can never strand a manifest-less folder and a
    finalize success always yields a folder with the manifest already in it."""
    tmp_dir = tmp_path / "work"
    tmp_dir.mkdir()
    (tmp_dir / "daily_A.mp4").write_bytes(b"x")
    (tmp_dir / "daily_B.mp4").write_bytes(b"x")

    manifest = daily_post.build_manifest(
        ticker="WULF", reason="r", score=1.0, story=None, bundle={},
        date_str="2026-07-22", seeds={"tts_seed": 7},
        files=["daily_A.mp4", "daily_B.mp4", "manifest.json"])
    daily_post.write_manifest(tmp_dir, manifest)

    # manifest.json is inside tmp_dir *before* finalize ever runs.
    assert (tmp_dir / "manifest.json").exists()

    dest = tmp_path / "dest" / "2026-07-22_WULF"
    files = daily_post.finalize(tmp_dir, dest)

    assert not tmp_dir.exists()  # move consumed the temp dir
    assert (dest / "manifest.json").exists()
    assert "manifest.json" in files
    assert "daily_A.mp4" in files and "daily_B.mp4" in files


def test_finalize_raising_leaves_manifest_intact_in_still_present_tmp_dir(tmp_path):
    """If finalize can't move (dest already exists), tmp_dir -- manifest included --
    is untouched, so the caller's cleanup (rmtree of tmp_dir) never has to worry
    about a half-written manifest; it just discards the whole (still-valid) temp dir."""
    tmp_dir = tmp_path / "work"
    tmp_dir.mkdir()
    daily_post.write_manifest(tmp_dir, {"ticker": "WULF"})

    dest = tmp_path / "dest" / "2026-07-22_WULF"
    dest.mkdir(parents=True)  # pre-existing -- forces finalize to raise

    with pytest.raises(daily_post.DailyPostError):
        daily_post.finalize(tmp_dir, dest)

    assert tmp_dir.exists()
    assert (tmp_dir / "manifest.json").exists()
