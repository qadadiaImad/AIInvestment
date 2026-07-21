import json

import pytest

import comments


def test_add_and_load_for_post():
    s = comments.empty_store()
    s, c = comments.add_comment(s, "2026-06-22_NVDA_reel", "audio", "slow the open",
                                "2026-06-23T09:00:00Z", _id="c_00000001")
    assert c["id"] == "c_00000001"
    assert c["part"] == "audio"
    assert c["resolved"] is False
    got = comments.load_for_post(s, "2026-06-22_NVDA_reel")
    assert len(got) == 1 and got[0]["text"] == "slow the open"


def test_add_rejects_bad_part_and_empty_text():
    s = comments.empty_store()
    with pytest.raises(ValueError):
        comments.add_comment(s, "p", "loudness", "x", "now")
    with pytest.raises(ValueError):
        comments.add_comment(s, "p", "caption", "   ", "now")


def test_resolve_hides_from_open_load():
    s = comments.empty_store()
    s, c = comments.add_comment(s, "p1", "general", "fix", "now", _id="c_aaaa0001")
    s = comments.set_resolved(s, "c_aaaa0001", True)
    assert comments.load_for_post(s, "p1", only_open=True) == []
    assert len(comments.load_for_post(s, "p1", only_open=False)) == 1


def test_edit_and_delete():
    s = comments.empty_store()
    s, c = comments.add_comment(s, "p1", "visual", "old", "now", _id="c_aaaa0002")
    s = comments.edit_comment(s, "c_aaaa0002", "new")
    assert comments.load_for_post(s, "p1")[0]["text"] == "new"
    s = comments.delete_comment(s, "c_aaaa0002")
    assert comments.load_for_post(s, "p1") == []
    with pytest.raises(KeyError):
        comments.set_resolved(s, "c_missing", True)


def test_read_missing_store_is_empty(tmp_path):
    p = tmp_path / "feedback" / "post_comments.json"
    assert comments.read_store(p) == comments.empty_store()


def test_write_then_read_roundtrip(tmp_path):
    p = tmp_path / "feedback" / "post_comments.json"
    s = comments.empty_store()
    s, _ = comments.add_comment(s, "p1", "caption", "hi", "now", _id="c_aaaa0003")
    comments.write_store(p, s)
    assert json.loads(p.read_text("utf-8"))["comments"][0]["text"] == "hi"
    assert comments.read_store(p) == s
