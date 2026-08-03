"""Load and parameterize API-format ComfyUI workflow templates.

Templates are the JSON shape POST /prompt expects:
{node_id: {"class_type": …, "inputs": {…}}, …}. PARAM_MAPS names the
logical knobs a template exposes and where each lands (node_id, input);
entries are added as templates are authored against the live server.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

PARAM_MAPS: dict[str, dict[str, tuple[str, str]]] = {}

# Z-Image-Turbo text-to-image. Graph reconstructed from the native
# `image_z_image_turbo.json` template shipped in
# comfyui_workflow_templates_media_other (steps=4, cfg=1, res_multistep,
# simple, ModelSamplingAuraFlow shift=3) with one deviation: node "5" is a
# real CLIPTextEncode for the negative prompt instead of the template's
# ConditioningZeroOut(positive), so a "negative" param has somewhere to
# land. At cfg=1 (no CFG) both are equivalent — the sampler output is the
# positive conditioning alone either way.
PARAM_MAPS["zimage_t2i"] = {
    "prompt":   ("4", "text"),
    "negative": ("5", "text"),
    "seed":     ("8", "seed"),
    "width":    ("6", "width"),
    "height":   ("6", "height"),
}

# Wan 2.2 TI2V-5B fast video (Apache 2.0). Graph reconstructed from the
# native `video_wan2_2_5B_ti2v.json` template shipped in
# comfyui_workflow_templates_media_video: UNETLoader(wan2.2_ti2v_5B_fp16)
# -> ModelSamplingSD3(shift=8) -> KSampler(steps=20, cfg=5, uni_pc,
# simple, denoise=1) fed by Wan22ImageToVideoLatent (vae=wan2.2_vae.
# safetensors, umt5_xxl CLIP type="wan") -> VAEDecode -> CreateVideo
# (fps=24) -> SaveVideo. The native template is ONE graph with a LoadImage
# node the user bypasses (UI "mode 4") for T2V and enables for I2V —
# API-format prompts can't ship a bypassed/dangling node, so this is
# shipped as two template files sharing everything except the
# Wan22ImageToVideoLatent.start_image link and its upstream LoadImage:
# "wan22_ti2v_5b" (T2V, no start_image input at all — the input is
# optional per /object_info) and "wan22_ti2v_5b_i2v" (adds node "12"
# LoadImage wired to node "6"'s start_image).
PARAM_MAPS["wan22_ti2v_5b"] = {
    "prompt":   ("4", "text"),
    "negative": ("5", "text"),
    "seed":     ("8", "seed"),
    "width":    ("6", "width"),
    "height":   ("6", "height"),
    "length":   ("6", "length"),
}
PARAM_MAPS["wan22_ti2v_5b_i2v"] = {
    **PARAM_MAPS["wan22_ti2v_5b"],
    "image": ("12", "image"),
}


def apply_params(workflow: dict, param_map: dict, params: dict) -> dict:
    unknown = set(params) - set(param_map)
    if unknown:
        raise KeyError(f"unknown params {sorted(unknown)}; "
                       f"template exposes {sorted(param_map)}")
    wf = copy.deepcopy(workflow)
    for name, value in params.items():
        node_id, input_name = param_map[name]
        wf[node_id]["inputs"][input_name] = value
    return wf


def load_template(name: str, **params) -> dict:
    wf = json.loads((TEMPLATES_DIR / f"{name}.json").read_text("utf-8"))
    return apply_params(wf, PARAM_MAPS[name], params)
