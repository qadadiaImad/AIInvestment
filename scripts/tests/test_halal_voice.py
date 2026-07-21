import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "higgs"))
import _gen_halal_voice as gv  # noqa: E402

KIT = '''"WULF":{ "kick":"K", "halal_script":"thirty-eight. Educational, not financial or religious advice." }
"NVDA":{ "kick":"K" }'''
VOICE = {"id": "abc-123", "type": "element", "variant": "elevenlabs"}

def test_collect_only_halal_entries():
    assert gv.collect_halal_entries(KIT) == [
        ("WULF", "thirty-eight. Educational, not financial or religious advice.")]

def test_compose_tts_cmd():
    cmd = gv.compose_tts_cmd("hello world", VOICE)
    assert cmd[:3] == ["higgsfield", "generate", "create"]
    assert "text2speech_v2" in cmd
    assert "--voice_id" in cmd and cmd[cmd.index("--voice_id") + 1] == "abc-123"
    assert "--voice_type" in cmd and cmd[cmd.index("--voice_type") + 1] == "element"
    assert "--variant" in cmd and cmd[cmd.index("--variant") + 1] == "elevenlabs"
    assert "--wait" in cmd and "--json" in cmd

def test_compose_refuses_null_voice():
    import pytest
    with pytest.raises(SystemExit):
        gv.compose_tts_cmd("x", {"id": None, "type": "element", "variant": "elevenlabs"})

def test_merge_manifest_updates_existing_and_appends():
    m = {"date": "2026-06-30", "reels": [{"tk": "WULF", "hero": "H", "voice": "OLD"}]}
    out = gv.merge_manifest(m, "2026-07-21", "WULF", "NEW")
    assert out["date"] == "2026-07-21"
    assert out["reels"][0]["voice"] == "NEW" and out["reels"][0]["hero"] == "H"
    out2 = gv.merge_manifest(out, "2026-07-21", "GEV", "V2")
    assert {"tk": "GEV", "hero": "", "voice": "V2", "voice_name": "Karim"} in out2["reels"]
    # IMPORTANT 6: top-level provenance for the Karim voice, additive only —
    # the legacy "voice" field (if any) is left untouched by this function.
    assert out2["voice_karim"] == "Karim (cloned element voice; per-entry voice_name=Karim)"

def test_merge_manifest_does_not_mutate_input():
    m = {"date": "2026-06-30", "reels": [{"tk": "WULF", "hero": "H", "voice": "OLD"}]}
    snapshot = copy.deepcopy(m)
    gv.merge_manifest(m, "2026-07-21", "WULF", "NEW")
    assert m == snapshot


# --- Regression: final-review wave -------------------------------------------

def test_main_dry_run_without_voice_id_does_not_crash(tmp_path, capsys):
    # CRITICAL 2: --dry-run used to call compose_tts_cmd() unconditionally,
    # which raises SystemExit when voice.id is null — aborting the whole
    # batch even though a dry run never needs to actually compose the command.
    kit = tmp_path / "reels_2026-07-21_kit.md"
    kit.write_text(
        '"WULF":{ "kick":"K", '
        '"halal_script":"thirty-eight. Educational, not financial or religious advice." }',
        encoding="utf-8")

    halal_json = tmp_path / "halal.json"
    halal_json.write_text(json.dumps({
        "generated_at": "2026-07-21T13:07:37Z",
        "verdicts": {
            "WULF": {
                "overall": "questionable",
                "standards": {"AAOIFI": {"status": "pass", "tests": [
                    {"id": "debt_mcap", "label": "debt / market cap", "ratio": 0.21,
                     "threshold": 0.30, "margin": 0.09, "status": "pass"}]}},
                "business": {"status": "questionable", "categories": ["crypto-mining"],
                    "impermissible_revenue_pct": {"value": 38.2, "basis": "Q1-2026 revenue mix"}},
                "purification": {"status": "computed", "per_share": 0.13},
                "inputs_asof": "2026-07-21T13:07:36Z",
            }
        }
    }), encoding="utf-8")

    ids_json = tmp_path / "higgsfield-ids.json"
    ids_json.write_text(json.dumps(
        {"voice": {"id": None, "type": "element", "variant": "elevenlabs"}}), encoding="utf-8")

    rc = gv.main(["--dry-run", "--kit", str(kit),
                  "--halal-json", str(halal_json), "--ids", str(ids_json)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "DRY WULF" in out
    assert "voice.id not set" in out
