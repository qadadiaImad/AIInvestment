import copy
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

def test_merge_manifest_does_not_mutate_input():
    m = {"date": "2026-06-30", "reels": [{"tk": "WULF", "hero": "H", "voice": "OLD"}]}
    snapshot = copy.deepcopy(m)
    gv.merge_manifest(m, "2026-07-21", "WULF", "NEW")
    assert m == snapshot
