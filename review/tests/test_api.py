import pytest

import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    # isolate the comment store to a temp file
    monkeypatch.setattr(app_module, "FEEDBACK_FILE", tmp_path / "feedback" / "post_comments.json")
    return app_module.create_app().test_client()


def test_posts_endpoint_returns_list(client):
    r = client.get("/api/posts")
    assert r.status_code == 200
    body = r.get_json()
    assert isinstance(body, list)
    # the repo's real reels should appear (NVDA reel dated 2026-06-22)
    assert any(p["post_id"].endswith("_NVDA_reel") for p in body)
    nvda = next(p for p in body if p["post_id"].endswith("_NVDA_reel"))
    assert nvda["kind"] == "reel"
    assert "audio_script" in nvda and "caption" in nvda
    assert nvda["open_comment_count"] == 0


def test_comment_crud_flow(client):
    r = client.post("/api/comments", json={"post_id": "2026-06-22_NVDA_reel",
                                           "part": "audio", "text": "slow the open"})
    assert r.status_code == 201
    cid = r.get_json()["id"]

    r = client.get("/api/comments?post_id=2026-06-22_NVDA_reel")
    assert len(r.get_json()) == 1

    r = client.patch(f"/api/comments/{cid}", json={"resolved": True})
    assert r.status_code == 200 and r.get_json()["resolved"] is True

    r = client.delete(f"/api/comments/{cid}")
    assert r.status_code == 200
    assert client.get("/api/comments?post_id=2026-06-22_NVDA_reel").get_json() == []


def test_comment_validation(client):
    assert client.post("/api/comments", json={"post_id": "p", "part": "bad", "text": "x"}).status_code == 400
    assert client.post("/api/comments", json={"post_id": "p", "part": "caption", "text": " "}).status_code == 400


def test_media_serves_real_reel_and_blocks_traversal(client):
    r = client.get("/media/higgs/reel_nvda_2026-06-22.mp4")
    assert r.status_code == 200
    bad = client.get("/media/../../etc/passwd")
    assert bad.status_code in (400, 403, 404)


def test_scripts_endpoint_lists_kit_and_reel_script(client):
    r = client.get("/api/scripts")
    assert r.status_code == 200
    names = [e["name"] for e in r.get_json()]
    assert "reels_2026-06-23.txt" in names
    assert "reels_2026-06-23_kit.md" in names
