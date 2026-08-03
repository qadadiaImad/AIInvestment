from pathlib import Path

import pytest

import comfy.manifest as manifest
from comfy import download


def _rf(size):
    return manifest.ResolvedFile("o/r", "vae/x.safetensors", size, "vae", "image")


def test_fetch_skips_existing_exact_size(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "COMFY_MODELS", tmp_path)
    rf = _rf(4)
    rf.dest.parent.mkdir(parents=True)
    rf.dest.write_bytes(b"abcd")
    assert download.fetch(
        rf, runner=lambda u, p: pytest.fail("must not download")) == "present"


def test_fetch_downloads_verifies_and_renames(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "COMFY_MODELS", tmp_path)
    rf = _rf(4)

    def fake_curl(url, part):
        assert url == rf.url
        Path(part).write_bytes(b"abcd")
        return 0

    assert download.fetch(rf, runner=fake_curl) == "downloaded"
    assert rf.dest.read_bytes() == b"abcd"
    assert not rf.dest.with_suffix(rf.dest.suffix + ".part").exists()


def test_fetch_size_mismatch_raises_and_keeps_part(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "COMFY_MODELS", tmp_path)
    rf = _rf(9)

    def fake_curl(url, part):
        Path(part).write_bytes(b"abcd")
        return 0

    with pytest.raises(RuntimeError, match="size mismatch"):
        download.fetch(rf, runner=fake_curl)
    assert rf.dest.with_suffix(rf.dest.suffix + ".part").exists()
