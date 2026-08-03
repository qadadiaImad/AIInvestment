import json

import pytest

from comfy import client


class FakeResp:
    def __init__(self, status_code=200, payload=None, content=b""):
        self.status_code = status_code
        self._payload = payload
        self.content = content
        self.text = json.dumps(payload) if payload is not None else ""

    def json(self):
        return self._payload


class FakeHttp:
    def __init__(self):
        self.posts, self.gets = [], []
        self.post_queue, self.get_queue = [], []

    def post(self, url, **kw):
        self.posts.append((url, kw))
        return self.post_queue.pop(0)

    def get(self, url, **kw):
        self.gets.append(url)
        return self.get_queue.pop(0)


def test_submit_posts_prompt_and_returns_id():
    http = FakeHttp()
    http.post_queue = [FakeResp(200, {"prompt_id": "abc", "number": 1})]
    c = client.ComfyClient(http=http)
    assert c.submit({"1": {"class_type": "X", "inputs": {}}}) == "abc"
    url, kw = http.posts[0]
    assert url.endswith("/prompt")
    assert kw["json"]["prompt"] == {"1": {"class_type": "X", "inputs": {}}}


def test_submit_non_200_raises_with_body():
    http = FakeHttp()
    http.post_queue = [FakeResp(400, {"error": "bad node"})]
    with pytest.raises(client.ComfyError, match="bad node"):
        client.ComfyClient(http=http).submit({})


def test_wait_polls_until_completed():
    http = FakeHttp()
    done = {"abc": {"outputs": {},
                    "status": {"status_str": "success", "completed": True}}}
    http.get_queue = [FakeResp(200, {}), FakeResp(200, done)]
    entry = client.ComfyClient(http=http).wait("abc", timeout=5, poll=0.01)
    assert entry["status"]["completed"] is True


def test_wait_error_status_raises():
    http = FakeHttp()
    http.get_queue = [FakeResp(200, {"abc": {"status": {"status_str": "error",
                                                        "completed": False}}})]
    with pytest.raises(client.ComfyError):
        client.ComfyClient(http=http).wait("abc", timeout=5, poll=0.01)


def test_outputs_collects_all_media_kinds():
    entry = {"outputs": {"9": {"images": [{"filename": "a.png"}]},
                         "12": {"videos": [{"filename": "b.mp4"}]}}}
    assert [i["filename"] for i in client.ComfyClient.outputs(entry)] == \
        ["a.png", "b.mp4"]


def test_fetch_writes_file(tmp_path):
    http = FakeHttp()
    http.get_queue = [FakeResp(200, content=b"PNGDATA")]
    c = client.ComfyClient(http=http)
    p = c.fetch({"filename": "a.png", "subfolder": "", "type": "output"},
                tmp_path)
    assert p.read_bytes() == b"PNGDATA"
    assert "filename=a.png" in http.gets[0]


def test_stage_input_missing_raises(tmp_path):
    missing = tmp_path / "nope.png"
    with pytest.raises(client.ComfyError, match="not found"):
        client.ComfyClient.stage_input(missing)


def _queue_generate_response(http, prompt_id):
    done = {prompt_id: {"outputs": {},
                        "status": {"status_str": "success",
                                   "completed": True}}}
    http.post_queue.append(FakeResp(200, {"prompt_id": prompt_id}))
    http.get_queue.append(FakeResp(200, done))


def test_generate_warns_on_family_switch(monkeypatch, tmp_path, capsys):
    import comfy.templates as templates_mod
    monkeypatch.setattr(templates_mod, "load_template",
                        lambda name, **params: {})

    http = FakeHttp()
    _queue_generate_response(http, "a")
    _queue_generate_response(http, "b")
    c = client.ComfyClient(http=http)

    c.generate("zimage_t2i", tmp_path)
    assert capsys.readouterr().out == ""

    c.generate("wan22_ti2v_5b", tmp_path)
    out = capsys.readouterr().out
    assert "WARNING" in out
    assert "zimage" in out and "wan22" in out


def test_generate_no_warning_same_family(monkeypatch, tmp_path, capsys):
    import comfy.templates as templates_mod
    monkeypatch.setattr(templates_mod, "load_template",
                        lambda name, **params: {})

    http = FakeHttp()
    _queue_generate_response(http, "a")
    _queue_generate_response(http, "b")
    c = client.ComfyClient(http=http)

    c.generate("wan22_ti2v_5b", tmp_path)
    c.generate("wan22_ti2v_5b_i2v", tmp_path)
    assert capsys.readouterr().out == ""
