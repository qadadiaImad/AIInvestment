import pytest

from comfy.manifest import ModelFile, ResolveError, resolve

FAKE_TREE = {
    "org/repo": [
        {"path": "split_files/vae/ae.safetensors", "size": 335_000_000},
        {"path": "split_files/diffusion_models/model_fp8.safetensors",
         "size": 6_000_000_000},
        {"path": "README.md", "size": 1000},
    ]
}


def fake_tree(repo):
    return FAKE_TREE[repo]


def test_resolve_exact_match():
    entries = [ModelFile("org/repo", r"vae/ae\.safetensors$", "vae", 0.3, "image")]
    got = resolve(entries, tree_fn=fake_tree)
    assert got[0].rfile == "split_files/vae/ae.safetensors"
    assert got[0].size == 335_000_000
    assert got[0].url == ("https://huggingface.co/org/repo/resolve/main/"
                          "split_files/vae/ae.safetensors")
    assert got[0].dest.name == "ae.safetensors"
    assert got[0].dest.parent.name == "vae"


def test_resolve_zero_matches_raises_and_lists_candidates():
    entries = [ModelFile("org/repo", r"nope\.gguf$", "unet", 1.0, "video-14b")]
    with pytest.raises(ResolveError) as e:
        resolve(entries, tree_fn=fake_tree)
    assert "README.md" in str(e.value)


def test_resolve_multi_match_raises():
    entries = [ModelFile("org/repo", r"safetensors$", "vae", 0.3, "image")]
    with pytest.raises(ResolveError):
        resolve(entries, tree_fn=fake_tree)
