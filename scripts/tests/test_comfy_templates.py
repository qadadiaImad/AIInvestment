import pytest

from comfy import templates

WF = {"3": {"class_type": "KSampler", "inputs": {"seed": 1}},
      "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "old"}}}
PMAP = {"prompt": ("6", "text"), "seed": ("3", "seed")}


def test_apply_params_sets_values_without_mutating_original():
    out = templates.apply_params(WF, PMAP, {"prompt": "new", "seed": 42})
    assert out["6"]["inputs"]["text"] == "new"
    assert out["3"]["inputs"]["seed"] == 42
    assert WF["6"]["inputs"]["text"] == "old"


def test_apply_params_partial_params_ok():
    out = templates.apply_params(WF, PMAP, {"seed": 7})
    assert out["6"]["inputs"]["text"] == "old"
    assert out["3"]["inputs"]["seed"] == 7


def test_apply_params_unknown_param_raises():
    with pytest.raises(KeyError, match="unknown params"):
        templates.apply_params(WF, PMAP, {"nope": 1})
